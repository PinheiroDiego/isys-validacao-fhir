"""Build V6 candidate once from preregistered source fixtures with frozen converter V1.1.
No benchmark scoring, no external validation, no clinical inference.
"""
from __future__ import annotations
import sys,json,hashlib,copy,os,platform
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
sys.path.insert(0,str(ROOT/'src'))
from isys_converter.schema import verify_base, SyntheticGraph
from isys_converter.transform import convert,decimal_json
from overlay_components import write_overlay

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observations(b):return [x for x in b.get('entry',[]) if x.get('resource',{}).get('resourceType')=='Observation']

def mutate(b,op,case):
 b=copy.deepcopy(b);oo=observations(b); r=oo[0]['resource']
 if op=='numeric_near':r['valueQuantity']['value']+=Decimal('0.01')
 elif op=='invent_date':r['effectiveDateTime']='2026-02-05'
 elif op=='change_unit':r['valueQuantity']['unit']='outra-unidade'
 elif op=='flip_negation':r['valueString']='com achados' if r['valueString']=='sem alterações' else 'com crescimento'
 elif op=='missing_status':r.pop('status',None)
 elif op=='missing_code':r.pop('code',None)
 elif op=='invalid_status':r['status']='not-a-fhir-status'
 elif op=='duplicate_new_identity':
  d=copy.deepcopy(oo[0]);d['resource']['id']='extra-'+hashlib.sha256(case.encode()).hexdigest()[:16]
  d['fullUrl']='https://example.org/fhir/Observation/'+d['resource']['id'];b['entry'].append(d)
 elif op=='wrong_existing_patient':
  all_ids=[p['resource']['id'] for p in b['entry'] if p['resource']['resourceType']=='Patient']
  cur=r['subject']['reference'].removeprefix('Patient/');other=[z for z in all_ids if z!=cur]
  assert len(other)==1;r['subject']['reference']='Patient/'+other[0]
 elif op=='swap_numeric_values':
  assert len(oo)==2
  oo[0]['resource']['valueQuantity'],oo[1]['resource']['valueQuantity']=copy.deepcopy(oo[1]['resource']['valueQuantity']),copy.deepcopy(oo[0]['resource']['valueQuantity'])
 elif op=='remove_second_occurrence':assert len(oo)==2;b['entry'].remove(oo[1])
 elif op=='reduce_date_precision':r['effectiveDateTime']=r['effectiveDateTime'][:4]
 elif op=='invent_numeric_value':
  r.pop('dataAbsentReason',None) # obs-6: intentional semantic mutation must stay structurally valid
  r['valueQuantity']={'value':Decimal('42')}
 elif op=='change_orphan_unit_note':
  assert 'valueQuantity' not in r and 'dataAbsentReason' in r
  for n in r['note']:
   n['text']=n['text'].replace("'mg/dL'","'g/L'")
 elif op=='increase_date_precision':r['effectiveDateTime']=r['effectiveDateTime']+'-11'
 elif op=='shift_day':r['effectiveDateTime']='2026-07-11'
 elif op=='rename_exam':r['code']['text']='Neutrófilos'
 elif op=='invent_unit':r['valueQuantity']['unit']='mEq/L'
 elif op=='swap_dates':
  assert len(oo)==2
  oo[0]['resource']['effectiveDateTime'],oo[1]['resource']['effectiveDateTime']=oo[1]['resource']['effectiveDateTime'],oo[0]['resource']['effectiveDateTime']
 elif op=='invalid_numeric_lexeme':r['valueQuantity']['value']='not-a-number'
 elif op=='unknown_element':r['isysUnexpectedElement']='does-not-exist'
 elif op=='duplicate_fullurl':b['entry'].append(copy.deepcopy(oo[0]))
 elif op=='invalid_resource_type':r['resourceType']='InvalidObservationType'
 elif op=='invalid_fhir_date':r['effectiveDateTime']='2026-99-99'
 elif op=='duplicate_value_choice':r['valueString']='additional-conflicting-value'
 elif op=='empty_status':r['status']=''
 else:raise ValueError(op)
 return b

def neutral(b,index):
 b=copy.deepcopy(b)
 if index%3==0:b['entry']=list(reversed(b['entry']))
 elif index%3==1:b['meta']={'versionId':'control-'+str(index)}
 else:b['id']='synthetic-control-'+str(index)
 return b

def main():
 import argparse
 ap=argparse.ArgumentParser()
 ap.add_argument('--original',type=Path,required=True,help='Original ontology ZIP, used locally only')
 ap.add_argument('--rebuild-unreviewed-candidate',action='store_true',help='Only for creating a NEW, explicitly versioned candidate; overwrites V6 files')
 a=ap.parse_args()
 if (ROOT/'benchmark/manifest_v6.json').exists() and not a.rebuild_unreviewed_candidate:
  raise RuntimeError('Candidate frozen. Never overwrite V6.1; create a new version if correction is required.')
 original=a.original
 if not original.exists():raise RuntimeError('Original file missing, required only locally for checking scheme')
 original_hash=sha(original)
 declarations=verify_base(original)['declared_uris']
 families=json.loads((ROOT/'benchmark/gold/families.json').read_text(encoding='utf8'))['families']
 assert len(families)==36 and sum(f['expected_decision']=='emit' for f in families)==31
 metrics=[];variants=[]
 for index,f in enumerate(families,1):
  fid=f['id'];overlay=ROOT/'benchmark/fixtures/overlays'/f'{fid}.owx';write_overlay(f,overlay)
  graph=SyntheticGraph(overlay,declarations)
  b,trace,rejected,stats=convert(graph)
  if f['expected_decision']=='reject':
   actual=set(k for x in rejected for k in x['reasons'])
   assert set(f['expected_rejection_reasons']).issubset(actual),(fid,actual,f['expected_rejection_reasons'])
   assert len(rejected)==len(f['exams']) and not trace,(fid,rejected)
  else:assert len(rejected)==0 and len(trace)==len(f['exams']),(fid,rejected)
  root=ROOT/'benchmark/inputs'/fid;root.mkdir(parents=True,exist_ok=True)
  (root/'baseline.json').write_text(decimal_json(b),encoding='utf8')
  variants.append(dict(id=fid+'_baseline',family=fid,split=f['split'],variant='baseline',expected_class='correct_conversion' if not rejected else 'expected_refusal',path=str((root/'baseline.json').relative_to(ROOT))))
  if not rejected:
   m=mutate(b,f['mutation']['operation'],fid);n=neutral(b,index)
   (root/'mutation.json').write_text(decimal_json(m),encoding='utf8')
   (root/'neutral.json').write_text(decimal_json(n),encoding='utf8')
   variants.extend([
    dict(id=fid+'_mutation',family=fid,split=f['split'],variant='mutation',operation=f['mutation']['operation'],expected_class=f['mutation']['kind']+'_fault',path=str((root/'mutation.json').relative_to(ROOT))),
    dict(id=fid+'_neutral',family=fid,split=f['split'],variant='neutral',operation=['reorder','meta.versionId','bundle.id'][index%3],expected_class='semantic_equivalent_control',path=str((root/'neutral.json').relative_to(ROOT)))])
  metrics.append({'family':fid,'split':f['split'],'source_occurrences':len(f['exams']),'emitted':len(trace),'refused':len(rejected),'rejection_reasons':rejected})
 assert len(variants)==98,(len(variants))
 assert len([v for v in variants if v['split']=='development'])==26
 assert len([v for v in variants if v['split']=='confirmatory'])==72
 assert original_hash==sha(original),'Original was modified'
 historical={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'historical').glob('*.zip')}
 manifest={
  'benchmark_id':'ISYS-V6.1-ADJUDICATED-CANDIDATE-2026-10-25','status':'EXPERT_ADJUDICATION_RECEIVED_NEW_VARIANTS_AWAIT_RATIFICATION_NOT_OFFICIALLY_VALIDATED',
  'version':'6.1-adjudicated-candidate-1','fhir_version':'4.0.1','fhir_core':'hl7.fhir.r4.core#4.0.1',
  'validator_cli_version':'7.0.3','validator_cli_sha256':'57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b',
  'profile':'http://hl7.org/fhir/StructureDefinition/Bundle','terminology':'-tx n/a',
  'source_ontology_original_sha256':original_hash,'source_ontology_original_unchanged':True,
  'original_ontology_NOT_distributed':True,'historical_archives_sha256':historical,
  'gold_sha256':sha(ROOT/'benchmark/gold/families.json'),
  'overlays_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'benchmark/fixtures/overlays').glob('*.owx'))},
  'file_sha256':{v['path']:sha(ROOT/v['path']) for v in variants},
  'variants':variants,'families':metrics,
  'analysis_unit':'family (cluster) and not derived variant','heldout_no_scoring_before_review':True,
  'expert_review_status':'EXPERT_G35_POLICY_DECIDED__FINAL_RATIFICATION_PENDING',
  'privacy':'No clinical records or ontology original included',
 }
 (ROOT/'benchmark/manifest_v6.json').write_text(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'families':len(families),'convertible':31,'refusals':5,'official_inputs_prepared':len(variants),'development_variants':26,'confirmatory_variants':72,'hash_original_unchanged':True,'expected_review':'FINAL_DELTA_RATIFICATION_PENDING'},ensure_ascii=False))

if __name__=='__main__':main()

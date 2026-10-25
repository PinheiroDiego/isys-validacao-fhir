"""Standalone evaluation reference derived from preregistered gold fixtures, not converter.
Purpose: compare clinical meaning, not OWL inference, FHIR profile, or clinical validity.
Does not import any converter code or its trace file.
"""
from __future__ import annotations
import json,hashlib,time
from pathlib import Path
from decimal import Decimal,InvalidOperation
ROOT=Path(__file__).resolve().parents[1]
TEST='https://example.org/isys/fhir-semantic-test/2026/v1#'

def deterministic_id(family,source_local,kind):
 return kind+'-'+hashlib.sha256((TEST+family+'-'+source_local).encode('utf-8')).hexdigest()[:24]

def expected(f):
 parent={e['id']:e['patients'] for e in f['evolutions']}
 out={};patients=set()
 if f['expected_decision']=='reject':return out,patients
 for x in f['exams']:
  owners=parent[x['evolution']]
  if len(owners)!=1:raise ValueError('Expected accepted fixture needs one patient')
  pid=deterministic_id(f['id'],owners[0],'p');oid=deterministic_id(f['id'],x['id'],'o')
  patients.add(pid)
  exp={'id':oid,'patient':'Patient/'+pid,'name':x['name'],'date':x.get('date'),
       'value_type':x.get('datatype'),'value':x.get('value'),'unit':x.get('unit')}
  out[oid]=exp
 return out,patients

def _value_actual(obs):
 present=[k for k in ('valueQuantity','valueString','valueCodeableConcept','valueBoolean','valueInteger','valueDateTime') if k in obs]
 if not present:return (None,None,None)
 if len(present)>1:return ('INVALID_MULTIPLE',None,None)
 key=present[0]
 if key=='valueQuantity':
  q=obs[key];return ('numeric',q.get('value'),q.get('unit'))
 if key=='valueString':return ('text',obs[key],None)
 return ('UNEXPECTED_TYPE',key,None)

def compare(f,bundle):
 mismatches=[]
 expected_obs,expected_patients=expected(f)
 entries=bundle.get('entry',[])
 actual_obs={}; actual_patients=set();seen=[]
 for e in entries:
  res=e.get('resource',{})
  if res.get('resourceType')=='Observation':
   oid=res.get('id');seen.append(oid)
   if oid in actual_obs:mismatches.append({'field':'duplicated_resource_id','id':oid})
   actual_obs[oid]=res
  elif res.get('resourceType')=='Patient':actual_patients.add(res.get('id'))
  else:mismatches.append({'field':'unexpected_resource_type','resource':res.get('resourceType')})
 for oid in sorted(set(actual_obs)-set(expected_obs)):
  mismatches.append({'field':'invented_observation','id':oid})
 for oid in sorted(set(expected_obs)-set(actual_obs)):
  mismatches.append({'field':'missing_observation','id':oid})
 if actual_patients != expected_patients:
  mismatches.append({'field':'patient_resource_set','expected_count':len(expected_patients),'actual_count':len(actual_patients)})
 for oid,exp in expected_obs.items():
  if oid not in actual_obs:continue
  a=actual_obs[oid]
  if a.get('subject',{}).get('reference')!=exp['patient']:mismatches.append({'field':'patient_association','id':oid})
  if a.get('code',{}).get('text')!=exp['name']:mismatches.append({'field':'exam_identity','id':oid})
  if a.get('effectiveDateTime')!=exp['date']:mismatches.append({'field':'date_or_precision','id':oid})
  dtype=exp['value_type'];value=exp['value'];actual_type,actual_value,actual_unit=_value_actual(a)
  if value is None:
   if actual_type is not None:mismatches.append({'field':'invented_value','id':oid})
  elif dtype in ('decimal','integer','int'):
   if actual_type!='numeric':mismatches.append({'field':'numeric_value_missing_or_wrong_type','id':oid})
   else:
    try:
     if Decimal(str(actual_value))!=Decimal(value):mismatches.append({'field':'numeric_value_changed','id':oid})
    except (InvalidOperation,TypeError):mismatches.append({'field':'invalid_numeric_value','id':oid})
    if actual_unit!=exp['unit']:mismatches.append({'field':'unit_changed','id':oid})
  elif dtype=='string':
   if actual_type!='text' or actual_value!=value:mismatches.append({'field':'text_result_changed','id':oid})
  else:mismatches.append({'field':'gold_datatype_out_of_scope','id':oid})
 return mismatches

def score_variants(split):
 gold=json.loads((ROOT/'benchmark/gold/families.json').read_text(encoding='utf8'))
 manifest=json.loads((ROOT/'benchmark/manifest_v6.json').read_text(encoding='utf8'))
 fs={f['id']:f for f in gold['families']}
 data=[]
 for v in manifest['variants']:
  if split!='all' and v['split']!=split:continue
  start=time.perf_counter()
  actual=json.loads((ROOT/v['path']).read_text(encoding='utf8'),parse_float=Decimal)
  diffs=compare(fs[v['family']],actual)
  elapsed=time.perf_counter()-start
  wanted=(v['expected_class']=='semantic_fault')
  data.append({'id':v['id'],'family':v['family'],'class':v['expected_class'],
               'oracle_flags':len(diffs)>0,'expected_semantic_fault':wanted,'findings':diffs,'oracle_wallclock_seconds':elapsed})
 return data

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['development','evaluation','all'],default='development')
 opts=p.parse_args()
 data=score_variants(opts.split)
 result={'scope':opts.split,'official_HL7_executed':False,'independence_limitation':'Gold scenario fixtures AI-assisted and not externally adjudicated',
         'total':len(data),'oracle_semantic_faults_flagged':sum(d['oracle_flags'] for d in data),
         'failures':[d for d in data if d['oracle_flags']!=d['expected_semantic_fault']],
         'cases':data}
 out=ROOT/'outputs'/('oracle_'+opts.split+'.json');out.parent.mkdir(exist_ok=True)
 out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in result.items() if k not in ('cases','failures')}|{'unexpected':len(result['failures'])},ensure_ascii=False))

"""Build independent OWL/XML synthetic families, convert using frozen V1.1,
and apply declared target perturbations. Never modify ontology original.
Oracle expectations are not derived from converter outputs.
"""
from __future__ import annotations
import json,sys,hashlib,copy,csv,random
from pathlib import Path
from decimal import Decimal
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from isys_converter.schema import verify_base,SyntheticGraph,BASE,TEST,EXAM,PATIENT,EVOLUTION,NAME,RESULT,HAS_EVOLUTION,HAS_EXAM,EXAM_DATE,EXAM_UNIT,XSD,OWL
from isys_converter.transform import convert,decimal_json

N=lambda name:'{'+OWL+'}'+name

def node(root,kind,iri): return ET.SubElement(root,N(kind),{'IRI':iri})
def elements(root,axiom,args):
 p=ET.SubElement(root,N(axiom))
 for kind,uri in args:node(p,kind,uri)
 return p

def write_overlay(family,path):
 root=ET.Element(N('Ontology'),{'ontologyIRI':TEST.rstrip('#')})
 for ax,args in [('Declaration',[('ObjectProperty',HAS_EXAM)]),
                 ('ObjectPropertyDomain',[('ObjectProperty',HAS_EXAM),('Class',EVOLUTION)]),
                 ('ObjectPropertyRange',[('ObjectProperty',HAS_EXAM),('Class',EXAM)])]:
  elements(root,ax,args)
 for u in [EXAM_DATE,EXAM_UNIT]:
  elements(root,'Declaration',[('DataProperty',u)])
  elements(root,'DataPropertyDomain',[('DataProperty',u),('Class',EXAM)])
  elements(root,'DataPropertyRange',[('DataProperty',u),('Datatype',XSD+'string')])
 key=family['id']+'-'
 def uri(i):return TEST+key+i
 for ident,klass in [(p,PATIENT) for p in family['patients']]+[(e['id'],EVOLUTION) for e in family['evolutions']]+[(e['id'],EXAM) for e in family['exams']]:
  elements(root,'Declaration',[('NamedIndividual',uri(ident))])
  elements(root,'ClassAssertion',[('Class',klass),('NamedIndividual',uri(ident))])
 for evo in family['evolutions']:
  for p in evo['patients']:
   elements(root,'ObjectPropertyAssertion',[('ObjectProperty',HAS_EVOLUTION),('NamedIndividual',uri(p)),('NamedIndividual',uri(evo['id']))])
 for ex in family['exams']:
  elements(root,'ObjectPropertyAssertion',[('ObjectProperty',HAS_EXAM),('NamedIndividual',uri(ex['evolution'])),('NamedIndividual',uri(ex['id']))])
  def data(prop,text,dtype='string'):
   a=elements(root,'DataPropertyAssertion',[('DataProperty',prop),('NamedIndividual',uri(ex['id']))])
   l=ET.SubElement(a,N('Literal'),{'datatypeIRI':XSD+dtype});l.text=str(text)
  if ex.get('name') is not None:data(NAME,ex['name'])
  if 'value' in ex:data(RESULT,ex['value'],ex['datatype'])
  for extra in ex.get('extra_results',[]):data(RESULT,extra['value'],extra['datatype'])
  if 'date' in ex:data(EXAM_DATE,ex['date'])
  if 'unit' in ex:data(EXAM_UNIT,ex['unit'])
 path.parent.mkdir(parents=True,exist_ok=True)
 ET.ElementTree(root).write(path,encoding='UTF-8',xml_declaration=True)

def obs_list(b):return [e for e in b['entry'] if e['resource'].get('resourceType')=='Observation']

def mutate(bundle,operation,marker):
 b=copy.deepcopy(bundle);obs=obs_list(b)
 if not obs:raise ValueError('Mutation requires accepted exam')
 r=obs[0]['resource']
 if operation=='change_numeric_value':r['valueQuantity']['value']+=Decimal('1.25')
 elif operation=='change_text_result':r['valueString']='achados inespecíficos'
 elif operation=='invent_result':r['valueString']='suposto sem referência'
 elif operation=='change_exam_date':r['effectiveDateTime']='2025'
 elif operation=='change_unit':r['valueQuantity']['unit']='mmol/L'
 elif operation=='swap_values':
  if len(obs)<2:raise ValueError('Two observations needed to swap')
  a0,a1=obs[0]['resource'],obs[1]['resource'];v0=copy.deepcopy(a0.get('valueQuantity') or a0.get('valueString'));v1=copy.deepcopy(a1.get('valueQuantity') or a1.get('valueString'))
  # both numeric in authored fixtures
  a0['valueQuantity'],a1['valueQuantity']=v1,v0
 elif operation=='drop_observation':b['entry'].remove(obs[1] if len(obs)>1 else obs[0])
 elif operation=='invent_exam_date':r['effectiveDateTime']='2026-01-15'
 elif operation=='reassign_patient':
  current=r['subject']['reference'];patients=['Patient/'+e['resource']['id'] for e in b['entry'] if e['resource']['resourceType']=='Patient']; others=[p for p in patients if p!=current]
  if not others:raise ValueError('reassignment target missing')
  r['subject']['reference']=others[0]
 elif operation=='duplicate_new_identity':
  dup=copy.deepcopy(obs[0]);dup['resource']['id']='extra-'+hashlib.sha256(marker.encode()).hexdigest()[:16]
  dup['fullUrl']='https://example.org/fhir/Observation/'+dup['resource']['id'];b['entry'].append(dup)
 elif operation=='change_exam_name':r['code']['text']='Mamografia alterada'
 elif operation=='increase_date_precision':r['effectiveDateTime']=r['effectiveDateTime']+'-14'
 elif operation=='drop_result':r.pop('valueQuantity',None);r.pop('valueString',None)
 elif operation=='remove_status':r.pop('status',None)
 elif operation=='duplicate_same_fullurl':b['entry'].append(copy.deepcopy(obs[0]))
 elif operation=='remove_code':r.pop('code',None)
 elif operation=='invalid_status':r['status']='not-a-valid-status'
 else:raise ValueError('Unknown mutation '+operation)
 return b

def neutral(bundle,idx):
 b=copy.deepcopy(bundle)
 if idx%2==0:
  b['entry']=list(reversed(b['entry']))
 else:
  # Marker on Bundle, not clinical content and not modifying source data
  b['meta']={'tag':[{'system':'https://example.org/isys/benchmark/metadata','code':'control'}]}
 return b

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--original',type=Path,default=Path('/mnt/data/ontologia-cbms-ontologies.owx.zip'));opts=a.parse_args()
 pre=hashlib.sha256(opts.original.read_bytes()).hexdigest()
 declaration=verify_base(opts.original)['declared_uris']
 families=json.loads((ROOT/'benchmark/gold/families.json').read_text(encoding='utf8'))['families']
 variants=[]; source_metrics=[]
 for i,f in enumerate(families):
  fid=f['id'];ov=ROOT/'benchmark/fixtures/overlays'/f'{fid}.owx'
  write_overlay(f,ov)
  graph=SyntheticGraph(ov,declaration)
  bundle,trace,refusals,stats=convert(graph)
  output=ROOT/'benchmark/inputs'/fid;output.mkdir(parents=True,exist_ok=True)
  (output/'baseline.json').write_text(decimal_json(bundle),encoding='utf8')
  source_metrics.append({'family':fid,'split':f['split'],'topic':f['topic'],
       'source_exam_count':len(f['exams']),'actual_emitted':len(trace),'actual_rejected':len(refusals),
       'rejection_reasons':refusals,'overlay_sha256':hashlib.sha256(ov.read_bytes()).hexdigest(),
       'decision_as_designed':(len(refusals)==len(f['exams']) if f['expected_decision']=='reject' else len(refusals)==0)})
  variants.append({'id':fid+'_baseline','family':fid,'split':f['split'],'variant':'baseline',
                   'expected_class':'correct_conversion' if f['expected_decision']=='emit' else 'expected_refusal',
                   'path':str((output/'baseline.json').relative_to(ROOT))})
  if f['expected_decision']=='emit':
   m=mutate(bundle,f['variant_mutation']['operation'],fid)
   (output/'mutation.json').write_text(decimal_json(m),encoding='utf8')
   variants.append({'id':fid+'_mutation','family':fid,'split':f['split'],'variant':'mutation',
                    'operation':f['variant_mutation']['operation'],'expected_class':f['variant_mutation']['kind']+'_fault',
                    'path':str((output/'mutation.json').relative_to(ROOT))})
   n=neutral(bundle,i)
   (output/'neutral.json').write_text(decimal_json(n),encoding='utf8')
   variants.append({'id':fid+'_neutral','family':fid,'split':f['split'],'variant':'neutral',
                    'operation':'reorder_entries' if i%2==0 else 'metadata_only', 'expected_class':'semantic_equivalent_control',
                    'path':str((output/'neutral.json').relative_to(ROOT))})
 assert len(families)==26 and len(variants)==66,(len(families),len(variants))
 assert all(x['decision_as_designed'] for x in source_metrics),[x for x in source_metrics if not x['decision_as_designed']]
 artifact={'benchmark_id':'ISYS-V4-2026-10-25','seed':20261025,'source_original_sha256_before':pre,
    'source_original_sha256_after':hashlib.sha256(opts.original.read_bytes()).hexdigest(),
    'fhir_version':'4.0.1','validator_cli_version':'7.0.3','fhir_package':'hl7.fhir.r4.core#4.0.1',
    'profile':'http://hl7.org/fhir/StructureDefinition/Bundle',
    'design':'26 purposively constructed source families, 20 convertible and 6 intended refusals; 66 bundles',
    'families':source_metrics,'variants':variants,
    'file_hashes':{x['path']:hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest() for x in variants},
    'overlay_hashes':{str((ROOT/'benchmark/fixtures/overlays'/f'{f["id"]}.owx').relative_to(ROOT)):hashlib.sha256((ROOT/'benchmark/fixtures/overlays'/f'{f["id"]}.owx').read_bytes()).hexdigest() for f in families},
    'gold_sha256':hashlib.sha256((ROOT/'benchmark/gold/families.json').read_bytes()).hexdigest(),
    'uncertainty':'Not scientifically independently adjudicated. GitHub official results for V4 not run.'}
 assert pre==artifact['source_original_sha256_after']
 path=ROOT/'benchmark/manifest_v4.json';path.write_text(json.dumps(artifact,sort_keys=True,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print(json.dumps({'source_families':len(families),'variants':len(variants),'accepted_families':sum(f['expected_decision']=='emit' for f in families),
   'refused_families':sum(f['expected_decision']=='reject' for f in families),'source_original_unchanged':True,'development_variants':sum(v['split']=='development' for v in variants), 'evaluation_variants':sum(v['split']=='evaluation' for v in variants)},ensure_ascii=False))

if __name__=='__main__':main()

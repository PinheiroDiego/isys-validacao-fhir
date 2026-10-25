"""Q01-Q06 comparison on OWL/XML assertions and FHIR Bundle, separate query code.
This module does not import converter/trace and does not inspect its logs.
Date intervals use three-valued classification; missing date is unknown, not false.
"""
from __future__ import annotations
from xml.etree import ElementTree as ET
from pathlib import Path
from datetime import date
from decimal import Decimal
from collections import Counter
import json,calendar,hashlib
ROOT=Path(__file__).resolve().parents[1]
TEST='https://example.org/isys/fhir-semantic-test/2026/v1#'
BASE='http://www.semanticweb.org/marco/ontologies/2018/11/marco'
HAS_EVOLUTION=BASE+'#possui';HAS_EXAM=TEST+'tem_ocorrencia_exame'
EXAM_NAME='http://webprotege.stanford.edu/R8Ln57NZOBVImw2EqPktO3f'
RESULT='http://webprotege.stanford.edu/RsGwsc6uggNZDQtrRF1fAg'
EXAM_DATE=TEST+'data_exame';EXAM_UNIT=TEST+'unidade_textual'

def typ(e):return e.tag.split('}')[-1]
def iri(e):return e.get('IRI')
def local(uri):return uri.split('#')[-1] if uri else None

def parse_overlay(path):
 root=ET.parse(path).getroot();relations=[];data={}
 for ax in root:
  k=typ(ax)
  if k=='ObjectPropertyAssertion' and len(ax)==3:
   relations.append((iri(ax[0]),local(iri(ax[1])),local(iri(ax[2]))))
  elif k=='DataPropertyAssertion' and len(ax)==3:
   data.setdefault((local(iri(ax[1])),iri(ax[0])),[]).append((ax[2].text,ax[2].get('datatypeIRI','').split('#')[-1]))
 return relations,data

def normalize_value(val,datatype):
 if val is None:return None
 if datatype in ('decimal','integer','int'):
  return ('numeric',str(Decimal(str(val)).normalize()))
 return ('text',str(val))

def source_rows(f):
 rel,data=parse_overlay(ROOT/'benchmark/fixtures/overlays'/(f['id']+'.owx'))
 p_of_e={}
 for prop,sub,obj in rel:
  if prop==HAS_EVOLUTION:p_of_e.setdefault(obj,set()).add(sub)
 rows=[]
 for prop,evo,ex in rel:
  if prop!=HAS_EXAM:continue
  owner=p_of_e.get(evo,set())
  if len(owner)!=1:continue
  def get(prop):
   vals=data.get((ex,prop),[])
   return vals[0] if len(vals)==1 else (None,None)
  name,_=get(EXAM_NAME); value,dtype=get(RESULT);dt,_=get(EXAM_DATE);unit,_=get(EXAM_UNIT)
  rows.append({'patient':next(iter(owner)),'exam':ex,'name':name,'result':normalize_value(value,dtype),
               'date':dt,'unit':unit})
 return rows

def expected_id(local_name,kind):return kind+'-'+hashlib.sha256((TEST+local_name).encode()).hexdigest()[:24]

def target_rows(f,b):
 reverse_exam={expected_id(f['id']+'-'+ex['id'],'o'):f['id']+'-'+ex['id'] for ex in f['exams']}
 reverse_pt={expected_id(f['id']+'-'+p,'p'):f['id']+'-'+p for p in f['patients']}
 rows=[]
 for ent in b.get('entry',[]):
  o=ent.get('resource',{})
  if o.get('resourceType')!='Observation':continue
  oid=o.get('id')
  ex=reverse_exam.get(oid,'EXTRA/'+str(oid))
  ref=o.get('subject',{}).get('reference','')
  patient=reverse_pt.get(ref.removeprefix('Patient/'),'UNMAPPED/'+ref)
  typ0=None;val=None;unit=None
  if 'valueQuantity' in o:
   typ0='numeric';val=o['valueQuantity'].get('value');unit=o['valueQuantity'].get('unit')
  elif 'valueString' in o:typ0='text';val=o['valueString']
  rows.append({'patient':patient,'exam':ex,'name':o.get('code',{}).get('text'),
               'result':normalize_value(val,'decimal') if typ0=='numeric' else normalize_value(val,'string'),
               'date':o.get('effectiveDateTime'),'unit':unit})
 return rows

def interval(d):
 if not d:return 'UNKNOWN_DATE'
 try:
  if len(d)==4:lo=date(int(d),1,1);hi=date(int(d),12,31)
  elif len(d)==7:
   yy,mm=map(int,d.split('-'));lo=date(yy,mm,1);hi=date(yy,mm,calendar.monthrange(yy,mm)[1])
  else:lo=hi=date.fromisoformat(d)
 except (ValueError,TypeError):return 'INVALID_DATE'
 start,end=date(2026,3,1),date(2026,3,31)
 if lo>=start and hi<=end:return 'IN'
 if hi<start or lo>end:return 'OUT'
 return 'INDETERMINATE'

def questions(rows):
 def clean(items):return sorted([repr(x) for x in items]) # canonical multiset retains duplicates
 return {
  'Q01':clean([(r['patient'],r['exam'],r['name']) for r in rows]),
  'Q02':clean([(r['exam'],r['result']) for r in rows if r['result'] is not None]),
  'Q03':clean([(r['exam'],r['date']) for r in rows if r['date'] is not None]),
  'Q04':clean([(r['exam'],r['result'],r['unit']) for r in rows if r['result'] is not None]),
  'Q05':clean([(r['exam'],interval(r['date'])) for r in rows]),
 }

def compare_queries(f,b,refusals=None):
 if f['expected_decision']=='reject':
  return {'family':f['id'],'status':'SOURCE_REFUSED','Q06':{'nonrepresented_occurrences':len(f['exams']),
    'expected_refusal_reasons':f['expected_rejection_reasons']}}
 qa=questions(source_rows(f));qb=questions(target_rows(f,b))
 results={q:{'equivalent':qa[q]==qb[q], 'source_answers':len(qa[q]),'destination_answers':len(qb[q]),
            'source_only':list((Counter(qa[q])-Counter(qb[q])).elements()),
            'destination_only':list((Counter(qb[q])-Counter(qa[q])).elements())} for q in qa}
 mismatches=[q for q in qa if not results[q]['equivalent']]
 return {'family':f['id'],'status':'COMPARED','questions':results,
         'Q06':{'mismatched_queries':mismatches,'count':len(mismatches)}}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['development','evaluation','all'],default='development');arg=p.parse_args()
 fs=json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']
 manifest=json.loads((ROOT/'benchmark/manifest_v4.json').read_text())
 byf={x['id']:x for x in fs}
 rec=[]
 for v in manifest['variants']:
  if arg.split!='all' and v['split']!=arg.split:continue
  b=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
  row=compare_queries(byf[v['family']],b);row['variant']=v['variant'];rec.append(row)
 report={'scope':arg.split,'results':rec,'source_queries':'explicit OWL/XML synthetic assertions',
         'target_queries':'FHIR JSON resources, no converter trace',
         'fully_equivalent_on_accepted':sum(v.get('status')=='COMPARED' and v['Q06']['count']==0 for v in rec),
         'non_equivalent_on_accepted':sum(v.get('status')=='COMPARED' and v['Q06']['count']>0 for v in rec),
         'refused':sum(v.get('status')=='SOURCE_REFUSED' for v in rec)}
 path=ROOT/'outputs'/('competency_'+arg.split+'.json');path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False))

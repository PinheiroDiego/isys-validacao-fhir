"""Score a COMPLETED official run, with family-level units and separate source refusals."""
from __future__ import annotations
import json,hashlib,sys,random,statistics
from pathlib import Path
from decimal import Decimal
from collections import Counter
from verify_v6 import verify
from semantic_oracle import compare
from competency_v4 import compare_queries
from review_gate import check as check_review
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def confusion(rows,flag):
 c=Counter(('TP' if r['fault'] else 'FP') if r[flag] else ('FN' if r['fault'] else 'TN') for r in rows)
 tp,fp,fn,tn=(c[x] for x in ('TP','FP','FN','TN'))
 return {'TP':tp,'FP':fp,'FN':fn,'TN':tn,
   'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,
   'false_alarm_rate':fp/(fp+tn) if fp+tn else None,'denominator':len(rows)}
def cluster_descriptives(families,iterations=2000,seed=160627):
 """Bootstrap dependent variants BY FAMILY for within-benchmark descriptive variability only."""
 pairs=[(a['B_detect_mutation'],a['C_detect_mutation']) for a in families]
 if not pairs:return None
 rng=random.Random(seed);gains=[];n=len(pairs)
 for _ in range(iterations):
  sample=[pairs[rng.randrange(n)] for __ in range(n)]
  gains.append(sum(c-b for b,c in sample)/n)
 gains.sort()
 return {'paired_recall_gain':sum(c-b for b,c in pairs)/n,'descriptive_cluster_bootstrap_2p5_97p5':[gains[int(.025*(iterations-1))],gains[int(.975*(iterations-1))]],
  'family_clusters':n,'resamples':iterations,'seed':seed,'inference_limit':'Designed synthetic cases; interval describes corpus variation, not population uncertainty'}
def analyze(scope):
 verify()
 if scope=='confirmatory':check_review()
 manifest=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
 gold={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 root=ROOT/'outputs/official_v6'/scope
 official=json.loads((root/'execution-summary.json').read_text())
 vars=[v for v in manifest['variants'] if v['split']==scope]
 if official.get('state') not in ('COMPLETED',) or len(official['results'])!=len(vars):raise RuntimeError('HL7 official data not complete')
 byid={r['id']:r for r in official['results']}
 if len(byid)!=len(vars):raise RuntimeError('duplicate ids')
 for v in vars:
  o=byid[v['id']]
  if o.get('state')!='VALIDATED' or o.get('input_sha256')!=manifest['file_sha256'][v['path']]:raise RuntimeError('not validated/hash drift '+v['id'])
  if sha(root/(v['id']+'.outcome.json'))!=o['outcome_sha256']:raise RuntimeError('outcome digest drift '+v['id'])
 family_valid={}
 for v in vars:
  if v['variant']=='baseline' and v['expected_class']!='expected_refusal':family_valid[v['family']]=byid[v['id']]['errors']==0
 eligible=[];noninterpretable=[];refusals=[];per_family={}
 for v in vars:
  o=byid[v['id']]
  if v['expected_class']=='expected_refusal':
   refusals.append({'family':v['family'],'A_refused':True,'official_bundle_errors':o['errors'],'not_scored_B_C':True});continue
  if not family_valid.get(v['family'],False):
   noninterpretable.append({'id':v['id'],'family':v['family'],'reason':'NONCONFORMANT_BASELINE','baseline_errors':byid[v['family']+'_baseline']['errors']});continue
  b=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
  findings=compare(gold[v['family']],b)
  q=compare_queries(gold[v['family']],b)
  b_alert=o['errors']>0;c_alert=b_alert or bool(findings) or bool(q['Q06']['mismatched_queries'])
  row={'id':v['id'],'family':v['family'],'variant':v['variant'],
    'expected_class':v['expected_class'],'fault':v['expected_class'] in ('semantic_fault','structural_fault'),
    'B_alert':b_alert,'C_alert':c_alert,'oracle_alert':bool(findings),
    'Q01_Q05_mismatches':q['Q06']['mismatched_queries'],'finding_codes':[x['field'] for x in findings],
    'official_errors':o['errors'],'official_warnings':o['warnings'],'official_seconds':o['duration_seconds']}
  eligible.append(row)
  per_family.setdefault(v['family'],{})[v['variant']]=row
 family_pairs=[]
 for fid,group in sorted(per_family.items()):
  if 'mutation' not in group or 'baseline' not in group or 'neutral' not in group:raise RuntimeError('Missing triplet '+fid)
  fm=group['mutation'];fb=group['baseline'];fn=group['neutral']
  family_pairs.append({'family':fid,'mutation_kind':fm['expected_class'],'B_detect_mutation':int(fm['B_alert']),
    'C_detect_mutation':int(fm['C_alert']),'B_false_alarms':int(fb['B_alert'])+int(fn['B_alert']),
    'C_false_alarms':int(fb['C_alert'])+int(fn['C_alert'])})
 mm=[x for x in eligible if x['variant']=='mutation']
 sem=[x for x in mm if x['expected_class']=='semantic_fault']
 src=[r for r in manifest['families'] if r['split']==scope]
 n_src=sum(x['source_occurrences'] for x in src);n_emit=sum(x['emitted'] for x in src)
 out={'benchmark_id':manifest['benchmark_id'],'scope':scope,'official_hl7_executed':True,
  'review_status':'DOCUMENTED_EXTERNAL_APPROVAL' if scope=='confirmatory' else 'DEVELOPMENT_ONLY',
  'A':{'source_occurrences':n_src,'emitted':n_emit,'refused':n_src-n_emit,'coverage':n_emit/n_src if n_src else None},
  'B':confusion(eligible,'B_alert'),'C':confusion(eligible,'C_alert'),
  'semantics_only':{'count':len(sem),'B_detected':sum(x['B_alert'] for x in sem),'C_detected':sum(x['C_alert'] for x in sem)},
  'families_valid':len(per_family),'family_cluster_results':family_pairs,
  'paired_family_descriptive_bootstrap':cluster_descriptives(family_pairs),
  'excluded_due_to_baseline':noninterpretable,'source_refusals_separate':refusals,
  'official_duration_seconds_total':sum(x['duration_seconds'] for x in eligible),
  'notes':['No population inference from purposive synthetic samples','One family is the analysis cluster; no independence assigned to variants','B detects official errors/fatals only, not warnings','C checks source value/relationships and competency queries in addition to B','A source refusals excluded from B/C confusion matrix but included in A coverage'],
  'cases':eligible}
 return out
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--scope',choices=['development','confirmatory'],required=True);a=p.parse_args()
 print(json.dumps(analyze(a.scope),indent=2,ensure_ascii=False))

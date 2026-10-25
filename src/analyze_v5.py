"""Corrective V5 scoring. Preserves all raw outcomes and limitations."""
import json
from pathlib import Path
from decimal import Decimal
from collections import Counter
from semantic_oracle import compare
from competency_v4 import compare_queries
ROOT=Path(__file__).resolve().parents[1]
def counts(rows,field):
 tp=sum(x['is_fault'] and x[field] for x in rows)
 fp=sum(not x['is_fault'] and x[field] for x in rows)
 fn=sum(x['is_fault'] and not x[field] for x in rows)
 tn=sum(not x['is_fault'] and not x[field] for x in rows)
 return {'TP':tp,'FP':fp,'FN':fn,'TN':tn,'precision':tp/(tp+fp) if (tp+fp) else None,'recall':tp/(tp+fn) if (tp+fn) else None,'false_positive_fraction':fp/(fp+tn) if (fp+tn) else None}
def analyze():
 m=json.loads((ROOT/'benchmark/manifest_v5.json').read_text())
 run=json.loads((ROOT/'outputs/official_v5/evaluation/execution-summary.json').read_text())
 if run['state']!='COMPLETED' or len(run['results'])!=42:raise RuntimeError('Official V5 run incomplete')
 byid={r['id']:r for r in run['results']}
 gold={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 accepted=[]; refused=[]; baseline_clean={}
 for v in m['variants']:
  if v['variant']=='baseline' and v['expected_class']!='expected_refusal':baseline_clean[v['family']]=(byid[v['id']]['errors']==0)
 for v in m['variants']:
  official=byid[v['id']]
  bundle=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
  differences=compare(gold[v['family']],bundle)
  cq=compare_queries(gold[v['family']],bundle)
  row={'id':v['id'],'family':v['family'],'variant':v['variant'],'expected_class':v['expected_class'],
       'errors':official['errors'],'warnings':official['warnings'],'B_alert':official['errors']>0,
       'semantic_alert':bool(differences),'C_alert':official['errors']>0 or bool(differences),
       'semantic_findings':differences,'Q01_Q05_mismatches':cq.get('Q06',{}).get('mismatched_queries',[]),
       'official_seconds':official['seconds'],'input_sha256':official['input_sha256']}
  if v['expected_class']=='expected_refusal':
   row['interpretation']='source_refusal_not_scored_BC';refused.append(row)
  else:
   row['is_fault']=v['expected_class'] in ('semantic_fault','structural_fault')
   row['baseline_conformant']=baseline_clean[v['family']]
   accepted.append(row)
 valid=[r for r in accepted if r['baseline_conformant']]
 return {'benchmark_id':m['benchmark_id'],'origin':'post-inspection corrective replication; not blinded',
  'complete_official_operations':len(run['results']),'accepted_family_count':12,
  'A':{'converted':15,'source_occurrences':21,'refused':6,'rate':15/21},
  'B':counts(valid,'B_alert'),'C_combined':counts(valid,'C_alert'),
  'semantic_fault_detection':{'B':sum(x['B_alert'] for x in valid if x['expected_class']=='semantic_fault'), 'C':sum(x['C_alert'] for x in valid if x['expected_class']=='semantic_fault'),'denominator':sum(x['expected_class']=='semantic_fault' for x in valid)},
  'structural_fault_detection':{'B':sum(x['B_alert'] for x in valid if x['expected_class']=='structural_fault'), 'denominator':sum(x['expected_class']=='structural_fault' for x in valid)},
  'controls_negative':sum(not x['is_fault'] for x in valid),
  'invalid_baseline_families':sorted({r['family'] for r in accepted if not r['baseline_conformant']}),
  'not_scored_expected_refusals':refused,
  'sum_warnings':sum(x['warnings'] for x in run['results']),
  'sum_errors':sum(x['errors'] for x in run['results']),
  'official_seconds_total':sum(x['seconds'] for x in run['results']),
  'clinical_adjudication':'PENDING','holdout_independence':'NOT_BLINDED_AFTER_V4',
  'rows':accepted}

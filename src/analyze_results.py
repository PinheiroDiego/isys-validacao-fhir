"""Score A/B/C from official OperationOutcome + a separate semantic gold oracle.
Never substitute structural local checker for B.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from semantic_oracle import score_variants,ROOT
from competency_v4 import compare_queries
from decimal import Decimal

def ratio(n,d):return {'numerator':n,'denominator':d,'fraction':n/d if d else None}
def confusion(rows,field):
 # positive expected fault=semantic or structural; negatives are baseline and neutral of accepted cases.
 tp=sum(r['fault'] and r[field] for r in rows)
 fn=sum(r['fault'] and not r[field] for r in rows)
 fp=sum(not r['fault'] and r[field] for r in rows)
 tn=sum(not r['fault'] and not r[field] for r in rows)
 return {'TP':tp,'FN':fn,'FP':fp,'TN':tn,'recall':ratio(tp,tp+fn),'precision':ratio(tp,tp+fp),
         'false_alarm_rate':ratio(fp,fp+tn)}
def analyze(scope):
 m=json.loads((ROOT/'benchmark/manifest_v4.json').read_text(encoding='utf8'))
 g=json.loads((ROOT/'benchmark/gold/families.json').read_text(encoding='utf8'))
 scope_root=ROOT/'outputs/official_v4'/scope
 run=json.loads((scope_root/'execution-summary.json').read_text(encoding='utf8'))
 if run.get('state')!='COMPLETED':raise ValueError('Cannot score incomplete official run')
 byid={x['id']:x for x in run['results'] if x.get('status')=='VALIDATED'}
 expected_variants=[v for v in m['variants'] if scope=='all' or v['split']==scope]
 if len(byid)!=len(expected_variants):raise ValueError('Incomplete official dataset')
 semantic={x['id']:x for x in score_variants(scope)}
 # Gate entire family when baseline is not clean.
 baseline_clean={v['family']:byid[v['id']]['errors']==0
                 for v in expected_variants if v['variant']=='baseline'}
 rows=[];uninferable=[];refused=[]
 for v in expected_variants:
  hl7=byid[v['id']];sem=semantic[v['id']]
  rec={'id':v['id'],'family':v['family'],'split':v['split'],'expected_class':v['expected_class'],
       'family_baseline_clean':baseline_clean[v['family']], 'official_errors':hl7['errors'],
       'official_warnings':hl7['warnings'],'B_detected':hl7['errors']>0,
       'semantic_detected':sem['oracle_flags'],'C_detected':hl7['errors']>0 or sem['oracle_flags'],
       'semantic_findings':sem['findings'],'C_semantic_check_seconds':sem['oracle_wallclock_seconds'], 'B_official_elapsed_seconds':hl7['seconds'],'input_sha256':hl7['input_sha256']}
  from_fhir=json.loads((ROOT/v['path']).read_text(encoding='utf8'),parse_float=Decimal)
  fam_gold=next(f for f in g['families'] if f['id']==v['family'])
  cq=compare_queries(fam_gold,from_fhir)
  rec['competency_questions']=cq
  if v['expected_class']=='expected_refusal':refused.append(rec);continue
  if not baseline_clean[v['family']]:uninferable.append(rec);continue
  rec['fault']=v['expected_class'] in ('semantic_fault','structural_fault')
  rows.append(rec)
 semantic_faults=[x for x in rows if x['expected_class']=='semantic_fault']
 structural_faults=[x for x in rows if x['expected_class']=='structural_fault']
 accepted_normal=[x for x in rows if x['expected_class'] in ('correct_conversion','semantic_equivalent_control')]
 f={i['id']:i for i in g['families']}
 actual={i['family']:i for i in m['families']}
 relevant=[f[v['family']] for v in expected_variants if v['variant']=='baseline']
 seen={x['id']:x for x in relevant};relevant=list(seen.values())
 source_count=sum(len(x['exams']) for x in relevant)
 converted=sum(actual[x['id']]['actual_emitted'] for x in relevant)
 rejected=sum(actual[x['id']]['actual_rejected'] for x in relevant)
 return {'scope':scope,'origin':'V4 purposefully designed, synthetic, related variants',
    'no_independent_clinical_validation':True,'family_count':len(relevant),'official_completed':len(byid),
    'A':{'source_occurrences':source_count,'converted':converted,'refused':rejected,
         'conversion_coverage':ratio(converted,source_count),
         'refusal_reasons_match_design':all(actual[x['id']]['decision_as_designed'] for x in relevant)},
    'B':confusion(rows,'B_detected'),'C_combined':confusion(rows,'C_detected'),
    'semantic_fault_detection':{'B':ratio(sum(x['B_detected'] for x in semantic_faults),len(semantic_faults)),
       'C_semantic':ratio(sum(x['semantic_detected'] for x in semantic_faults),len(semantic_faults))},
    'structural_negative_controls':{'B':ratio(sum(x['B_detected'] for x in structural_faults),len(structural_faults)),
       'C_combined':ratio(sum(x['C_detected'] for x in structural_faults),len(structural_faults))},
    'no_fault_controls':{'B_false_alarms':ratio(sum(x['B_detected'] for x in accepted_normal),len(accepted_normal)),
       'C_false_alarms':ratio(sum(x['C_detected'] for x in accepted_normal),len(accepted_normal))},
    'uninterpretable_due_to_invalid_reference':uninferable,
    'expected_refusals_reported_separately':refused,
    'issues_total':{'error':sum(x['errors'] for x in byid.values()),'warning':sum(x['warnings'] for x in byid.values())},
    'execution_costs':{'official_validation_seconds_total':sum(x.get('seconds',0) for x in byid.values()),
      'semantic_oracle_seconds_total':sum(x['C_semantic_check_seconds'] for x in rows),
      'note':'Non-comparable environments/IO; report separate totals; not an isolated overhead causal estimate'},
    'competency':{'baselines_equivalent':ratio(sum(r['expected_class']=='correct_conversion' and not r['competency_questions']['Q06']['mismatched_queries'] for r in rows),sum(r['expected_class']=='correct_conversion' for r in rows)),
      'neutral_equivalent':ratio(sum(r['expected_class']=='semantic_equivalent_control' and not r['competency_questions']['Q06']['mismatched_queries'] for r in rows),sum(r['expected_class']=='semantic_equivalent_control' for r in rows)),
      'mutations_changing_answers':ratio(sum(r['fault'] and r['competency_questions']['Q06']['mismatched_queries']!=[] for r in rows),sum(r['fault'] for r in rows))},
    'family_cluster_count_for_detection':len({r['family'] for r in rows}),
    'note':'No CI calculated; family is unit, not individual mutation; not a probability sample; pre-adjudication evidence',
    'rows':rows}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scope',choices=['development','evaluation','all'],default='evaluation');args=p.parse_args()
 print(json.dumps(analyze(args.scope),indent=2,ensure_ascii=False))

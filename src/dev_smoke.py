"""Only examine preregistered DEVELOPMENT cases, never the confirmatory partition."""
import json
from pathlib import Path
from decimal import Decimal
from verify_v6 import verify
from semantic_oracle import compare
from competency_v4 import compare_queries
ROOT=Path(__file__).resolve().parents[1]
def main():
 verify()
 m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
 fs={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 report={'scope':'development ONLY','official_HL7_execution':False,'expert_review':'PENDING','expected_structural_detection':'NOT TESTED',
         'records':[]}
 for v in m['variants']:
  if v['split']!='development':continue
  if v['expected_class']=='expected_refusal':continue
  b=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
  diffs=compare(fs[v['family']],b);q=compare_queries(fs[v['family']],b)
  row={'id':v['id'],'expected_class':v['expected_class'],'semantic_comparison_alert':bool(diffs),'questions_non_equivalent':q['Q06']['mismatched_queries']}
  report['records'].append(row)
 report['baselines_no_semantic_alert']=sum(not x['semantic_comparison_alert'] for x in report['records'] if x['expected_class']=='correct_conversion')
 report['neutrals_no_semantic_alert']=sum(not x['semantic_comparison_alert'] for x in report['records'] if x['expected_class']=='semantic_equivalent_control')
 report['semantic_mutations_alerted']=sum(x['semantic_comparison_alert'] for x in report['records'] if x['expected_class']=='semantic_fault')
 p=ROOT/'outputs/development-only/smoke.json';p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()

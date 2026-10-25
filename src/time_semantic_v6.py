"""Independent INCREMENTAL C timing, excluding Java validator startup.
Warm caches, separate I/O, paired family reporting. Synthetic data only.
"""
from __future__ import annotations
import argparse,json,time,statistics,random,sys,platform,os
from decimal import Decimal
from pathlib import Path
from collections import defaultdict
from verify_v6 import verify
from review_gate import check as review_check
from semantic_oracle import compare
from competency_v4 import compare_queries
ROOT=Path(__file__).resolve().parents[1]
def ns_median(x):return statistics.median(x)/1e6

def main():
 p=argparse.ArgumentParser();p.add_argument('--scope',choices=['development','confirmatory'],required=True)
 p.add_argument('--warmups',type=int,default=12);p.add_argument('--repetitions',type=int,default=45);a=p.parse_args()
 verify()
 if a.scope=='confirmatory':review_check()
 m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
 gold={x['id']:x for x in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 cases=[v for v in m['variants'] if v['split']==a.scope and v['expected_class']!='expected_refusal']
 prepared=[]
 for v in cases:
  tic=time.perf_counter_ns();bundle=json.loads((ROOT/v['path']).read_text(encoding='utf8'),parse_float=Decimal)
  parse_ns=time.perf_counter_ns()-tic
  prepared.append((v,gold[v['family']],bundle,parse_ns))
 rng=random.Random(28106)
 timings=defaultdict(list)
 # Precondition warmup is intentionally excluded from measured workload.
 for _ in range(a.warmups):
  for v,f,b,_ in prepared:compare(f,b);compare_queries(f,b)
 for _ in range(a.repetitions):
  for i in rng.sample(range(len(prepared)),len(prepared)):
   v,f,b,_=prepared[i]
   st=time.perf_counter_ns()
   findings=compare(f,b)
   queries=compare_queries(f,b)
   ns=time.perf_counter_ns()-st
   timings[v['id']].append(ns)
 detail=[]
 for v,f,b,parse_ns in prepared:
  numbers=timings[v['id']]
  detail.append({'id':v['id'],'family':v['family'],'split':a.scope,'variant':v['variant'],
   'C_incremental_median_ms':ns_median(numbers),'C_incremental_p90_ms':sorted(numbers)[int(.9*(len(numbers)-1))]/1e6,
   'input_parse_once_ms':parse_ns/1e6,'repetitions':len(numbers)})
 clusters=defaultdict(list)
 for row in detail:clusters[row['family']].append(row['C_incremental_median_ms'])
 per_family={k:statistics.median(vals) for k,vals in clusters.items()}
 values=list(per_family.values())
 report={'scope':a.scope,'timing_kind':'C incremental only, from already parsed FHIR Bundle to semantic/origin-competency decision',
 'exclude':'Java validator invocation, Java startup and loading HL7 packages; these are recorded separately in official results',
 'warmup_rounds':a.warmups,'repetitions_per_variant':a.repetitions,'seed':28106,
 'python':sys.version.split()[0],'platform':platform.platform(),'families':len(per_family),'variants':len(detail),
 'unit':'milliseconds','cluster_median_ms':statistics.median(values) if values else None,
 'cluster_p90_ms':sorted(values)[int(.9*(len(values)-1))] if values else None,
 'family_medians_ms':per_family,'records':detail,
 'limits':['Execution speed depends on hardware, CPU scheduling, caches and Python runtime',
           'This measures the local check independently, not the end-to-end C pipeline',
           'Values are descriptive only and repeated iterations do not increase the independent family sample size']}
 output=ROOT/'outputs/metrics_v6'/a.scope/'incremental_C_timing.json';output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
 print(json.dumps({'status':'MEASURED_LOCAL_INCREMENTAL_C','scope':a.scope,'variants':len(detail),'families':len(per_family),
  'cluster_median_ms':report['cluster_median_ms'],'not_HL7_latency':True},ensure_ascii=False))
if __name__=='__main__':main()

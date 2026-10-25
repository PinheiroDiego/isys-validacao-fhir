#!/usr/bin/env python3
"""Official pinned validator execution for V5 corrective inputs; never rewrite V4."""
from pathlib import Path
import json,hashlib,subprocess,sys,time,zipfile
from verify_v5 import check
from run_hl7_v4 import parse_outcome,save,JAR_HASH,PROFILE
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'outputs/official_v5/evaluation'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--jar',required=True,type=Path);a=p.parse_args()
 gate=check()
 m=json.loads((ROOT/'benchmark/manifest_v5.json').read_text())
 run={'benchmark_id':m['benchmark_id'],'scope':'evaluation','fhir_version':'4.0.1','core':'hl7.fhir.r4.core#4.0.1',
      'validator_version':'7.0.3','validator_expected_sha256':JAR_HASH,'profile':PROFILE,'terminology':'-tx n/a',
      'planned':42,'completed':0,'state':'STARTED','results':[],
      'qualification':'V5 corrective replication on previously exposed V4 evaluation cases; not blind'}
 TARGET.mkdir(parents=True,exist_ok=True)
 logs=TARGET/'logs';logs.mkdir(exist_ok=True)
 if not a.jar.exists() or not zipfile.is_zipfile(a.jar) or h(a.jar)!=JAR_HASH:
  run['state']='BLOCKED';run['reason']='Validator JAR unavailable or SHA mismatch';save(TARGET/'execution-summary.json',run);return 3
 run['java']=subprocess.run(['java','-version'],capture_output=True,text=True,timeout=15).stderr.splitlines()[0]
 for v in m['variants']:
  source=ROOT/v['path'];dest=TARGET/(v['id']+'.outcome.json')
  if h(source)!=m['hashes'][v['path']]:raise RuntimeError('Case digest changed: '+v['id'])
  cmd=['java','-jar',str(a.jar),str(source),'-version','4.0.1','-tx','n/a','-profile',PROFILE,'-output',str(dest)]
  record={'id':v['id'],'family':v['family'],'variant':v['variant'],'expected_class':v['expected_class'],'input':v['path'],'input_sha256':h(source),'command':cmd}
  start=time.monotonic()
  try:
   cp=subprocess.run(cmd,capture_output=True,timeout=240,cwd=ROOT)
   (logs/(v['id']+'.stdout.txt')).write_bytes(cp.stdout)
   (logs/(v['id']+'.stderr.txt')).write_bytes(cp.stderr)
   record['exit_code']=cp.returncode
   outcome=parse_outcome(dest)
   if outcome:
    record.update(outcome);record['status']='VALIDATED';run['completed']+=1
   else:record['status']='OUTCOME_PARSE_FAILED'
  except subprocess.TimeoutExpired as e:
   record['status']='TIMEOUT';(logs/(v['id']+'.timeout.txt')).write_text(str(e),encoding='utf8')
  record['seconds']=round(time.monotonic()-start,3)
  run['results'].append(record)
  save(TARGET/'execution-summary.json',run)
  print(v['id'],record['status'],flush=True)
 run['state']='COMPLETED' if run['completed']==42 else 'PARTIAL'
 save(TARGET/'execution-summary.json',run)
 if run['state']=='COMPLETED':
  from analyze_v5 import analyze
  save(TARGET/'comparison_abc.json',analyze())
 return 0 if run['state']=='COMPLETED' else 4
if __name__=='__main__':sys.exit(main())

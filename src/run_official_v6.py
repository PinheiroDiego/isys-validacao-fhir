#!/usr/bin/env python3
"""Official HL7 validator only. Captures raw outcomes and evidence; no local substitute."""
from __future__ import annotations
import argparse,sys,subprocess,json,time,hashlib,zipfile,platform
from collections import Counter
from pathlib import Path
from verify_v6 import verify
from review_gate import check as review_check
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
def parse_outcome(path):
 try:
  a=json.loads(path.read_text(encoding='utf8'))
  if a.get('resourceType')!='OperationOutcome' or not isinstance(a.get('issue'),list):return None
  counts=Counter(x.get('severity') for x in a['issue'])
  return {'errors':counts.get('error',0)+counts.get('fatal',0),'warnings':counts.get('warning',0),
    'information':counts.get('information',0),'outcome_sha256':sha(path),
    'issues':[{'severity':x.get('severity'),'code':x.get('code'),'details':x.get('details',{}).get('text'),
              'diagnostics':x.get('diagnostics'),'expression':x.get('expression')} for x in a['issue']]}
 except (ValueError,OSError):return None

def main():
 p=argparse.ArgumentParser();p.add_argument('--jar',type=Path,required=True);p.add_argument('--scope',choices=['development','confirmatory'],required=True);p.add_argument('--timeout',type=int,default=240);a=p.parse_args()
 verify()
 review=review_check() if a.scope=='confirmatory' else {'state':'NOT_REQUIRED_FOR_TECHNICAL_DEVELOPMENT'}
 m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
 cases=[v for v in m['variants'] if v['split']==a.scope]
 target=ROOT/'outputs/official_v6'/a.scope;logs=target/'logs';logs.mkdir(parents=True,exist_ok=True)
 run={'benchmark_id':m['benchmark_id'],'scope':a.scope,'state':'STARTED','planned':len(cases),'completed':0,
 'validator_cli_version':m['validator_cli_version'],'fhir_version':m['fhir_version'],'fhir_core':m['fhir_core'],
 'validator_cli_sha256_expected':m['validator_cli_sha256'],'profile':m['profile'],'terminology':'-tx n/a',
 'review_gate':review,'results':[],'measurement':'Each invocation includes separate Java startup; not C incremental cost'}
 if not a.jar.is_file() or not zipfile.is_zipfile(a.jar) or sha(a.jar)!=m['validator_cli_sha256']:
  run.update(state='BLOCKED',reason='Pinned HL7 validator 7.0.3 JAR absent or digest mismatch');dump(target/'execution-summary.json',run);return 3
 cmd=['java','-version'];cp=subprocess.run(cmd,capture_output=True,timeout=15)
 run['java']=(cp.stderr or cp.stdout).decode('utf8','replace').splitlines()[0]
 for i,v in enumerate(cases):
  infile=ROOT/v['path'];out=target/(v['id']+'.outcome.json')
  if sha(infile)!=m['file_sha256'][v['path']]:raise RuntimeError('Input changed '+v['id'])
  command=['java','-jar',str(a.jar),str(infile),'-version',m['fhir_version'],'-tx','n/a', '-profile',m['profile'],'-output',str(out)]
  record={'id':v['id'],'family':v['family'],'variant':v['variant'],'expected_class':v['expected_class'],
    'input':v['path'],'input_sha256':sha(infile),'command':command,'state':'NOT_RUN'}
  start=time.monotonic()
  try:
   cp=subprocess.run(command,capture_output=True,timeout=a.timeout,cwd=ROOT)
   (logs/(v['id']+'.stdout.log')).write_bytes(cp.stdout);(logs/(v['id']+'.stderr.log')).write_bytes(cp.stderr)
   record['exit_code']=cp.returncode
   outcome=parse_outcome(out)
   if outcome:record.update(outcome);record['state']='VALIDATED';run['completed']+=1
   else:record['state']='INVALID_OR_MISSING_OUTCOME'
  except subprocess.TimeoutExpired as e:
   record['state']='TIMEOUT';(logs/(v['id']+'.timeout.txt')).write_text(str(e),encoding='utf8')
  record['duration_seconds']=round(time.monotonic()-start,6)
  run['results'].append(record);dump(target/'execution-summary.json',run)
  print(f'{i+1}/{len(cases)} {v["id"]}: {record["state"]}',flush=True)
 run['state']='COMPLETED' if run['completed']==len(cases) else 'PARTIAL';dump(target/'execution-summary.json',run)
 if run['state']=='COMPLETED':
  from analyze_v6 import analyze
  dump(target/'comparison_abc.json',analyze(a.scope))
 return 0 if run['state']=='COMPLETED' else 4
if __name__=='__main__':sys.exit(main())

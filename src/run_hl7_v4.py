#!/usr/bin/env python3
"""Run pinned official HL7 validator on V4 cases; preserve verbatim outcomes/logs.
No replacement with a local JSON checker. Each case is one Bundle validation.
"""
from __future__ import annotations
import argparse,json,hashlib,subprocess,platform,time,sys,zipfile
from pathlib import Path
from collections import Counter
from verify_freeze import verify
ROOT=Path(__file__).resolve().parents[1]
JAR_HASH='57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b'
PROFILE='http://hl7.org/fhir/StructureDefinition/Bundle'

def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf8')
def parse_outcome(path):
 try:
  j=json.loads(path.read_text(encoding='utf8'))
  if j.get('resourceType')!='OperationOutcome' or not isinstance(j.get('issue'),list):return None
  counts=Counter(e.get('severity') for e in j['issue'])
  return {'errors':counts.get('error',0)+counts.get('fatal',0), 'warnings':counts.get('warning',0),
          'information':counts.get('information',0), 'outcome_sha256':h(path),
          'issues':[{'severity':x.get('severity'),'code':x.get('code'),'details':x.get('details',{}).get('text'),
                    'expression':x.get('expression'),'diagnostics':x.get('diagnostics')} for x in j['issue']]}
 except (OSError,ValueError):return None

def main():
 p=argparse.ArgumentParser();p.add_argument('--jar',type=Path,required=True);p.add_argument('--scope',choices=['development','evaluation','all'],default='evaluation');p.add_argument('--timeout',type=int,default=240)
 a=p.parse_args();verify()
 m=json.loads((ROOT/'benchmark/manifest_v4.json').read_text(encoding='utf8'))
 selected=[x for x in m['variants'] if a.scope=='all' or x['split']==a.scope]
 target=ROOT/'outputs/official_v4'/a.scope
 logs=target/'logs';logs.mkdir(parents=True,exist_ok=True)
 run={'benchmark_id':m['benchmark_id'],'scope':a.scope,'version':'HL7-validator-cli#7.0.3','jar_sha256_expected':JAR_HASH,
      'fhir_version':'4.0.1','fhir_core_package':'hl7.fhir.r4.core#4.0.1','profiles':{'Bundle':PROFILE},
      'terminology':'-tx n/a (terminology service disabled)','planned':len(selected), 'completed':0,'state':'STARTED',
      'results':[],'date':'2026-10-25 baseline design; execution date in runtime logs',
      'scientific_qualification':'Synthetic purposive pilot. Source/gold review by an external domain expert remains pending.'}
 if not a.jar.is_file() or not zipfile.is_zipfile(a.jar) or h(a.jar)!=JAR_HASH:
  run.update(state='BLOCKED',reason='Pinned official JAR absent/invalid/wrong SHA-256')
  save(target/'execution-summary.json',run);print(run['reason'],file=sys.stderr);return 3
 java=subprocess.run(['java','-version'],capture_output=True,text=True,timeout=15)
 run['java']=(java.stderr or java.stdout).splitlines()[0]
 for i,v in enumerate(selected):
  inp=ROOT/v['path'];id=v['id']
  if h(inp)!=m['file_hashes'][v['path']]:
   run['results'].append({'id':id,'state':'HASH_MISMATCH'});continue
  out=target/(id+'.outcome.json')
  cmd=['java','-jar',str(a.jar),str(inp),'-version','4.0.1','-tx','n/a','-profile',PROFILE,'-output',str(out)]
  record={'id':id,'family':v['family'],'split':v['split'],'variant':v['variant'],'expected_class':v['expected_class'],
          'input':v['path'],'input_sha256':h(inp),'command':cmd, 'status':'NOT_RUN'}
  ts=time.monotonic()
  try:
   cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=a.timeout,cwd=ROOT)
   (logs/(id+'.stdout.txt')).write_bytes(cp.stdout)
   (logs/(id+'.stderr.txt')).write_bytes(cp.stderr)
   record['exit_code']=cp.returncode
   result=parse_outcome(out)
   if result is not None:
    record.update(result);record['status']='VALIDATED';run['completed']+=1
   else:record.update(status='FAILED_OUTCOME_PARSE')
  except subprocess.TimeoutExpired as e:
   (logs/(id+'.timeout.txt')).write_text(str(e),encoding='utf8');record.update(status='TIMEOUT')
  except Exception as e:record.update(status='FAILED_EXCEPTION',error=str(e))
  record['seconds']=round(time.monotonic()-ts,3)
  run['results'].append(record)
  save(target/'execution-summary.json',run) # checkpoint per case
  print(f'{i+1}/{len(selected)} {id} {record["status"]}',flush=True)
 run['state']='COMPLETED' if run['completed']==len(selected) else 'PARTIAL'
 save(target/'execution-summary.json',run)
 if run['state']=='COMPLETED':
  from analyze_results import analyze
  report=analyze(a.scope)
  save(target/'comparison_abc.json',report)
 return 0 if run['state']=='COMPLETED' else 4
if __name__=='__main__':sys.exit(main())

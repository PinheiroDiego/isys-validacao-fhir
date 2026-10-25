#!/usr/bin/env python3
"""Reproducible official HL7 CLI runner. Does NOT substitute local checks for HL7 evidence."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time, zipfile
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
VALIDATOR_VERSION='7.0.3'
FHIR_VERSION='4.0.1'
CORE='hl7.fhir.r4.core#4.0.1'
URL=f'https://github.com/hapifhir/org.hl7.fhir.core/releases/download/{VALIDATOR_VERSION}/validator_cli.jar'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def json_file(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')


def parse_outcome(path):
    if not path.is_file():return None,'operationoutcome_missing'
    try: obj=json.loads(path.read_text(encoding='utf-8'))
    except Exception as ex:return None,f'invalid_outcome_json:{type(ex).__name__}'
    if obj.get('resourceType')!='OperationOutcome' or not isinstance(obj.get('issue'),list):
        return None,'not_an_operation_outcome'
    issues=[{'severity':i.get('severity'),'code':i.get('code'),'diagnostics':i.get('diagnostics'),
             'details_text':i.get('details',{}).get('text'), 'expression':i.get('expression'),
             'location':i.get('location')} for i in obj['issue']]
    sev=dict(Counter(x['severity'] for x in issues))
    return {'severity_counts':sev, 'errors':sev.get('error',0)+sev.get('fatal',0),
            'warnings':sev.get('warning',0),'issues':issues,'conforms_base_profile':(sev.get('error',0)+sev.get('fatal',0)==0)},None


def main():
 p=argparse.ArgumentParser(description='Official HL7 validator runner; logs failures without fabricating results')
 p.add_argument('--jar',type=Path,default=ROOT/'tools'/f'validator_cli_{VALIDATOR_VERSION}.jar')
 p.add_argument('--root',type=Path,default=ROOT)
 p.add_argument('--timeout',type=int,default=240)
 a=p.parse_args();root=a.root
 output=root/'outputs/official';logs=root/'logs'; output.mkdir(parents=True,exist_ok=True);logs.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/'outputs/engineering/manifest_inputs.json').read_text(encoding='utf-8'))
 items=manifest['requests'];jar=a.jar
 run={'official_validator_version_requested':VALIDATOR_VERSION,'fhir_version':FHIR_VERSION,'fhir_core_package_expected':CORE,
      'profiles':manifest['profiles'], 'terminology_server':'n/a (explicitly disabled)',
      'source_file_sha256':manifest['ontology_zip_sha256_before'],
      'planned_requests':len(items),'attempted_requests':0,'completed_requests':0,
      'unrun_requests':len(items),'validator_executable_available':False,
      'status':'BLOCKED','jar_sha256':None,'java_version':None, 'results':[],
      'qualifier':'Do not interpret null rates as zero error rate; official validation not accomplished.'}
 try:
    jv=subprocess.run(['java','-version'],text=True,capture_output=True,timeout=15)
    run['java_version']=(jv.stderr or jv.stdout).splitlines()[0]
 except Exception as ex:run['java_version_error']=str(ex)
 if not jar.is_file():
    run['reason']='validator_cli.jar unavailable in execution environment; binary download blocked (DNS/network).'
    run['release_url']=URL
    run['results']=[{'id':req['id'],'status':'NOT_RUN','profile':manifest['profiles'][req['resourceType']]} for req in items]
    json_file(output/'execution-summary.json',run)
    json_file(output/'coverage-metrics.json',metrics(manifest,run))
    print(json.dumps({'status':run['status'],'reason':run['reason'],'official_completed':0,'planned':len(items)}))
    return 2
 if not zipfile.is_zipfile(jar):
    run['reason']='Supplied validator JAR is not a valid ZIP/JAR archive.'
    json_file(output/'execution-summary.json',run); json_file(output/'coverage-metrics.json',metrics(manifest,run))
    return 3
 run['validator_executable_available']=True;run['jar_sha256']=sha(jar)
 run['status']='RUNNING';run['reason']=None
 for req in items:
    inp=root/req['path']
    if sha(inp)!=manifest['input_file_hashes'][req['path']]:
        run['results'].append({'id':req['id'],'status':'INPUT_HASH_MISMATCH'})
        continue
    profile=manifest['profiles'][req['resourceType']]
    dest=output/(req['id']+'.outcome.json')
    cmd=['java','-jar',str(jar),str(inp),'-version',FHIR_VERSION,'-tx','n/a','-profile',profile,'-output',str(dest)]
    # No external terminology service in this phase. Core package is selected by -version 4.0.1.
    start=time.monotonic()
    try:
        run['attempted_requests']+=1
        cp=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=a.timeout)
        (logs/(req['id']+'.stdout.txt')).write_text(cp.stdout,encoding='utf-8')
        (logs/(req['id']+'.stderr.txt')).write_text(cp.stderr,encoding='utf-8')
        report,parseerr=parse_outcome(dest)
        detail={'id':req['id'],'resourceType':req['resourceType'],'cohort':req['cohort'],
                'profile':profile,'input':req['path'],'input_sha256':sha(inp),
                'command':cmd,'return_code':cp.returncode,'elapsed_seconds':round(time.monotonic()-start,3),
                'stdout_log':str((logs/(req['id']+'.stdout.txt')).relative_to(root)),
                'stderr_log':str((logs/(req['id']+'.stderr.txt')).relative_to(root))}
        if report is not None:
            detail.update(report);detail['status']='VALIDATED';run['completed_requests']+=1
            detail['outcome_sha256']=sha(dest)
        else:
            detail['status']='EXECUTION_FAILED';detail['error']=parseerr
        run['results'].append(detail)
    except subprocess.TimeoutExpired as err:
        detail={'id':req['id'],'status':'TIMEOUT','timeout_seconds':a.timeout}
        (logs/(req['id']+'.timeout.txt')).write_text(str(err),encoding='utf8')
        run['results'].append(detail)
    except OSError as err:
        run['results'].append({'id':req['id'],'status':'EXECUTION_FAILED','error':str(err)})
    # Save checkpoint after every attempt
    run['unrun_requests']=len(items)-len(run['results'])
    json_file(output/'execution-summary.json',run)
    json_file(output/'coverage-metrics.json',metrics(manifest,run))
 run['unrun_requests']=len(items)-len(run['results'])
 run['status']='COMPLETED' if run['completed_requests']==len(items) else 'PARTIAL'
 json_file(output/'execution-summary.json',run)
 json_file(output/'coverage-metrics.json',metrics(manifest,run))
 print(json.dumps({'status':run['status'],'completed':run['completed_requests'],'planned':len(items)}))
 return 0 if run['status']=='COMPLETED' else 4


def metrics(m,run):
    completed=[r for r in run['results'] if r['status']=='VALIDATED']
    baseline=[r for r in completed if r['cohort']=='baseline']
    obs=[r for r in baseline if r['resourceType']=='Observation']
    passed=[r for r in obs if r['conforms_base_profile']]
    mutations=[r for r in completed if r['cohort']=='mutation']
    mutation_count=len(m['mutations'])
    # Return none for rates with denominator of 0 validated tests: evidence not present.
    return {
      'official_validation_status':run['status'],
      'planned_validation_requests':len(m['requests']),
      'official_validation_requests_attempted':run['attempted_requests'],
      'official_validation_requests_completed':len(completed),
      'official_validation_request_coverage':len(completed)/len(m['requests']),
      'official_baseline_resource_coverage':len([r for r in baseline if r['resourceType']!='Bundle'])/7,
      'official_observation_validation_coverage':len(obs)/m['mapped_observations'],
      'official_observation_profile_pass_rate':len(passed)/len(obs) if obs else None,
      'source_occurrences_total':m['source_observation_occurrences'],
      'converted_observations':m['mapped_observations'],
      'source_to_fhir_mapping_coverage':m['mapped_observations']/m['source_observation_occurrences'],
      'source_refusals':m['refused_observations'],
      'refusal_rate':m['refused_observations']/m['source_observation_occurrences'],
      'end_to_end_source_conformant_coverage':len(passed)/m['source_observation_occurrences'] if len(obs)==m['mapped_observations'] else None,
      'official_mutation_requests_completed':len(mutations),
      'official_mutation_detection_rate':sum(not r['conforms_base_profile'] for r in mutations)/len(mutations) if len(mutations)==mutation_count else None,
      'official_error_issue_count':sum(r['errors'] for r in completed),
      'official_warning_issue_count':sum(r['warnings'] for r in completed),
      'condition_A':'EXECUTED_SYNTHETIC_CONVERSION',
      'condition_B':'OFFICIAL_VALIDATION_COMPLETE' if len(completed)==len(m['requests']) else 'NOT_YET_EVALUABLE',
      'condition_C':'SEMANTIC_ENGINEERING_TESTS_COMPLETED; COMBINED_C_NOT_YET_EVALUABLE' if len(completed)!=len(m['requests']) else 'COMBINE_WITH_SEMANTIC_ORACLE',
      'scientific_inference_allowed':False,
      'note':'Rates based on 11 artificial occurrences. CLI coverage and conformance remain null when not run; offline terminology restrictions apply.'
    }

if __name__=='__main__':sys.exit(main())

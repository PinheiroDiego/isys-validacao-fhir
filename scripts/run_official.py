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


def differential_summary(m, run):
    """Controlled mutation detection is interpretable only if the reference Bundle passes."""
    byid={r['id']:r for r in run['results'] if r.get('status')=='VALIDATED'}
    baseline=byid.get('base_bundle')
    good=baseline is not None and baseline['errors']==0
    summary={'baseline_bundle_valid':good if baseline else None,
             'baseline_bundle_errors':baseline['errors'] if baseline else None,
             'comparisons_interpretable':good, 'mutations':[]}
    def sig(i):
        return (i.get('severity'),i.get('code'),i.get('details_text'),
                tuple(i.get('expression') or ()))
    errs_base=Counter(sig(i) for i in (baseline or {}).get('issues',[])
                     if i.get('severity') in ('error','fatal'))
    for mut in m['mutations']:
        r=byid.get('mutation_'+mut['id'])
        if not r:
            summary['mutations'].append({'id':mut['id'],'kind':mut['kind'],
                                        'completed':False,'official_detected':None})
            continue
        errs=Counter(sig(i) for i in r['issues']
                     if i.get('severity') in ('error','fatal'))
        delta=list((errs-errs_base).elements())
        summary['mutations'].append({'id':mut['id'],'kind':mut['kind'],
          'completed':True,'total_errors':r['errors'],
          'additional_errors_vs_baseline':len(delta),
          'additional_error_details':[{'code':v[1], 'details':v[2], 'expression':list(v[3])} for v in delta],
          'official_detected':(r['errors']>0) if good else None,
          'oracle_detected_previous_engineering_test':mut.get('semantic_detected')})
    return summary


def metrics(m,run):
    completed=[r for r in run['results'] if r.get('status')=='VALIDATED']
    baseline=[r for r in completed if r['cohort']=='baseline']
    observations=[r for r in baseline if r['resourceType']=='Observation']
    conforming_obs=[r for r in observations if r['conforms_base_profile']]
    bundle=next((r for r in baseline if r['id']=='base_bundle'),None)
    bundle_clean=(bundle['errors']==0) if bundle else None
    differential=differential_summary(m,run)
    mutants=differential['mutations']
    mut_complete=len(mutants)==len(m['mutations']) and all(r['completed'] for r in mutants)
    detected=[r for r in mutants if r.get('official_detected') is True]
    kinds={k:[r for r in mutants if r['kind']==k] for k in ('SEMANTIC','FHIR_NEGATIVE_CONTROL')}
    return {
      'official_validation_status':run['status'],
      'planned_validation_requests':len(m['requests']),
      'official_validation_requests_attempted':run['attempted_requests'],
      'official_validation_requests_completed':len(completed),
      'official_validation_request_coverage':len(completed)/len(m['requests']),
      'baseline_bundle_conforms_base_profile':bundle_clean,
      'official_baseline_resource_coverage':sum(r['resourceType']!='Bundle' for r in baseline)/7,
      'official_observation_profile_pass_rate':len(conforming_obs)/len(observations) if observations else None,
      'source_occurrences_total':m['source_observation_occurrences'],
      'converted_observations':m['mapped_observations'],
      'source_to_fhir_mapping_coverage':m['mapped_observations']/m['source_observation_occurrences'],
      'source_refusals':m['refused_observations'],
      'refusal_rate':m['refused_observations']/m['source_observation_occurrences'],
      'end_to_end_source_conformant_coverage':(len(conforming_obs)/m['source_observation_occurrences']
        if bundle_clean and len(observations)==m['mapped_observations'] else None),
      'official_mutation_requests_completed':sum(r['completed'] for r in mutants),
      'official_mutation_detection_rate':(len(detected)/len(mutants) if bundle_clean and mut_complete else None),
      'official_semantic_mutation_detection_rate':(sum(r.get('official_detected') is True for r in kinds['SEMANTIC'])/len(kinds['SEMANTIC'])
        if bundle_clean and mut_complete and kinds['SEMANTIC'] else None),
      'official_negative_control_detected':(kinds['FHIR_NEGATIVE_CONTROL'][0].get('official_detected')
        if bundle_clean and mut_complete and len(kinds['FHIR_NEGATIVE_CONTROL'])==1 else None),
      'official_error_issue_count':sum(r['errors'] for r in completed),
      'official_warning_issue_count':sum(r['warnings'] for r in completed),
      'condition_A':'EXECUTED_SYNTHETIC_CONVERSION',
      'condition_B':('OFFICIAL_BASELINE_CONFORMANT' if bundle_clean else 'BASELINE_INVALID' if bundle is not None else 'NOT_YET_EVALUABLE'),
      'condition_C':'ENGINEERING_ORACLE_AVAILABLE; SCIENTIFIC_BENCHMARK_NOT_EXECUTED',
      'scientific_inference_allowed':False,
      'note':'Differential mutation detection is NULL until clean baseline and every mutation evaluated; rates describe synthetic pilot, no clinical/semantic inference from profile pass.'}

if __name__=='__main__':sys.exit(main())

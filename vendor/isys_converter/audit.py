"""Independent, hand-authored expected-case comparator for this synthetic pilot.
Input oracle is deliberately separate from mapping code.
"""
from __future__ import annotations
from collections import Counter
from decimal import Decimal
import json,copy
from .transform import date_check


def local_structure_check(bundle):
    """Small local sanity check; NOT the official HL7 validator or profile checking."""
    errors=[]
    if bundle.get('resourceType')!='Bundle' or bundle.get('type')!='collection':errors.append('INVALID_BUNDLE')
    resources=[e.get('resource',{}) for e in bundle.get('entry',[])]
    refs={'Patient/'+r.get('id','') for r in resources if r.get('resourceType')=='Patient'}
    IDs=[(r.get('resourceType'),r.get('id')) for r in resources]
    if len(IDs)!=len(set(IDs)):errors.append('DUPLICATE_RESOURCE_IDS')
    allowed={'registered','preliminary','final','amended','corrected','cancelled','entered-in-error','unknown'}
    for r in resources:
        if r.get('resourceType')=='Observation':
            if r.get('status') not in allowed:errors.append('INVALID_STATUS')
            if not r.get('code',{}).get('text'):errors.append('MISSING_CODE')
            if r.get('subject',{}).get('reference') not in refs:errors.append('INVALID_PATIENT_REFERENCE')
            if 'effectiveDateTime' in r and not date_check(r['effectiveDateTime']):errors.append('INVALID_EFFECTIVE_DATE')
            if 'valueQuantity' in r and 'valueString' in r:errors.append('MULTIPLE_VALUE_TYPES')
    return sorted(set(errors))


def compare_oracle(bundle,trace,rejected,oracle):
    """Check factual-preservation promises, refusals, and duplicates against separate oracle."""
    by_target={e['resource'].get('id'):e['resource'] for e in bundle['entry'] if e['resource'].get('resourceType')=='Observation'}
    by_source={t['source_exam']:(by_target.get(t['target_observation']),t) for t in trace}
    refused={x['synthetic_exam']:set(x['reasons']) for x in rejected}
    findings=[]
    observed=set(by_source)|set(refused)
    expected=set(oracle['cases'])
    for e in sorted(observed^expected): findings.append({'case':e,'problem':'MISSING_OR_UNKNOWN_CASE'})
    seen_ids=[t['target_observation'] for t in trace]
    if len(set(seen_ids))!=len(seen_ids):findings.append({'case':'bundle','problem':'DUPLICATE_OBSERVATION_TRACE'})
    for ex,exp in sorted(oracle['cases'].items()):
        if exp['decision']=='reject':
            if ex in by_source:findings.append({'case':ex,'problem':'SHOULD_HAVE_REJECTED'})
            elif not set(exp['reasons']).issubset(refused.get(ex,set())):
                findings.append({'case':ex,'problem':'REJECTION_REASON_MISMATCH'})
            continue
        if ex not in by_source:
            findings.append({'case':ex,'problem':'EXPECTED_OBSERVATION_MISSING'});continue
        ob,t=by_source[ex]
        if t['source_patient']!=exp['patient'] or t['source_evolution']!=exp['evolution']:
            findings.append({'case':ex,'problem':'SOURCE_RELATION_CHANGED'})
        if ob['subject']['reference'] != 'Patient/'+t['target_patient']:
            findings.append({'case':ex,'problem':'TARGET_PATIENT_MISMATCH'})
        if ob['status'] != 'unknown':findings.append({'case':ex,'problem':'STATUS_NOT_SUPPORTED_BY_SOURCE'})
        if ob.get('code',{}).get('text')!=exp['code']:
            findings.append({'case':ex,'problem':'EXAM_CODE_CHANGED'})
        if ob.get('effectiveDateTime')!=exp.get('date'):
            findings.append({'case':ex,'problem':'EXAM_DATE_CHANGED'})
        value=exp.get('value')
        if value is None:
            if any(k in ob for k in ['valueQuantity','valueString','dataAbsentReason']):
                findings.append({'case':ex,'problem':'UNSUPPORTED_VALUE_OR_ABSENCE_REASON'})
        elif value['kind']=='decimal':
            actual=ob.get('valueQuantity',{})
            if ('valueQuantity' not in ob or Decimal(str(actual.get('value'))) != Decimal(value['number'])
                or actual.get('unit')!=value.get('unit') or 'code' in actual or 'system' in actual):
                findings.append({'case':ex,'problem':'NUMERIC_OR_UNIT_CHANGED'})
            if 'valueString' in ob:findings.append({'case':ex,'problem':'MULTIPLE_VALUE_TYPES'})
        elif value['kind']=='text':
            if ob.get('valueString')!=value['text'] or 'valueQuantity' in ob:
                findings.append({'case':ex,'problem':'TEXT_RESULT_CHANGED'})
    # Detect inserted observations without provenance. An unchanged copy at a second entry is also counted.
    observed_obs_count=len([e for e in bundle['entry'] if e['resource'].get('resourceType')=='Observation'])
    if observed_obs_count!=sum(c['decision']=='emit' for c in oracle['cases'].values()):
        findings.append({'case':'bundle','problem':'OBSERVATION_OCCURRENCE_COUNT_CHANGED'})
    for ob_id in by_target:
        if ob_id not in set(seen_ids):findings.append({'case':'bundle','problem':'OBSERVATION_WITHOUT_TRACE'})
    return findings


def mutations_and_checks(bundle,trace,rejections,oracle):
    observations=[e['resource'] for e in bundle['entry'] if e['resource']['resourceType']=='Observation']
    lookup={t['source_exam']:t['target_observation'] for t in trace}
    def find_ob(b, case):
        return next(x['resource'] for x in b['entry'] if x['resource'].get('id')==lookup[case])
    def make(tag,change):
        b=copy.deepcopy(bundle);change(b)
        return {'mutation':tag,'local_structure_findings':local_structure_check(b),
                'independent_semantic_findings':compare_oracle(b,trace,rejections,oracle)}
    other_patient=next(x['resource']['id'] for x in bundle['entry'] if x['resource']['resourceType']=='Patient' and x['resource']['id']!=find_ob(bundle,'ex01')['subject']['reference'][8:])
    cases=[
        make('change_numeric_value',lambda b:find_ob(b,'ex01')['valueQuantity'].update(value=Decimal('26.20'))),
        make('swap_result_between_occurrences',lambda b:(find_ob(b,'ex01')['valueQuantity'].update(value=Decimal('8')),find_ob(b,'ex05')['valueQuantity'].update(value=Decimal('25.20')))),
        make('change_exam_date',lambda b:find_ob(b,'ex01').update(effectiveDateTime='2026-03-13')),
        make('reassign_existing_patient',lambda b:find_ob(b,'ex01')['subject'].update(reference='Patient/'+other_patient)),
        make('drop_result',lambda b:find_ob(b,'ex01').pop('valueQuantity',None)),
        make('add_unjustified_value',lambda b:find_ob(b,'ex03').update(valueString='presumido')),
        make('duplicate_observation_entry',lambda b:b['entry'].append(copy.deepcopy(next(x for x in b['entry'] if x['resource'].get('id')==lookup['ex01'])))),
    ]
    return {'scenario_type':'CONTROLLED SYNTHETIC ENGINEERING CHECK - NOT INDEPENDENT EMPIRICAL STUDY',
            'local_checker':'Subset-only local structural sanity check, not HL7 FHIR validator',
            'baseline_local_structure':local_structure_check(bundle),
            'baseline_oracle_discrepancies':compare_oracle(bundle,trace,rejections,oracle),
            'mutations':[{'mutation':r['mutation'],'local_check_flags':bool(r['local_structure_findings']),
                          'semantic_check_flags':bool(r['independent_semantic_findings']),
                          'local_details':r['local_structure_findings'],
                          'semantic_details':r['independent_semantic_findings']} for r in cases]}

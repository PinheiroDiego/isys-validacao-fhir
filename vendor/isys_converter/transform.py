"""Deterministic OWL/XML synthetic-extension to HL7 FHIR R4 (4.0.1) converter.
No clinical inferences and no copying the original ontology's individual data.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from collections import defaultdict, Counter
from hashlib import sha256
from datetime import date
import json, re
from .schema import PATIENT,EVOLUTION,EXAM,NAME,RESULT,HAS_EVOLUTION,HAS_EXAM,EXAM_DATE,EXAM_UNIT,XSD,TEST

FHIR_VERSION = '4.0.1'
DATE_RE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')


def fid(uri, kind):
    return kind + '-' + sha256(uri.encode('utf8')).hexdigest()[:24]


def date_check(s):
    m=DATE_RE.fullmatch(s)
    if not m: return False
    try:
        y=int(m[1]); mo=int(m[2] or 1); day=int(m[3] or 1)
        if y==0: return False
        date(y,mo,day)
        return True
    except ValueError: return False


def lone(values, field, errors, required=False):
    if len(values)>1: errors.append('MULTIPLE_'+field.upper());return None
    if len(values)==0:
        if required: errors.append('MISSING_'+field.upper())
        return None
    return values[0]


def fhir_value(value, errors):
    if not value: return {}
    if value.datatype in (XSD+'integer', XSD+'int',XSD+'decimal'):
        try:
            n=Decimal(value.text)
            if not n.is_finite():raise InvalidOperation
            if value.datatype in (XSD+'integer',XSD+'int') and n!=n.to_integral_value():
                raise InvalidOperation
            return {'valueQuantity':{'value':n}}
        except (InvalidOperation, ValueError):
            errors.append('INVALID_NUMERIC_RESULT'); return {}
    if value.datatype==XSD+'string':
        if not value.text.strip(): errors.append('EMPTY_TEXT_RESULT');return {}
        return {'valueString':value.text}
    errors.append('UNSUPPORTED_RESULT_DATATYPE')
    return {}


def convert(graph):
    patients = graph.nodes(PATIENT)
    evolutions= graph.nodes(EVOLUTION)
    exams=graph.nodes(EXAM)
    patient_of_evolution=defaultdict(set)
    for p in patients:
        for evo in graph.target(HAS_EVOLUTION,p):
            if evo in evolutions: patient_of_evolution[evo].add(p)
    evolution_of_exam=defaultdict(set)
    for evo in evolutions:
        for ex in graph.target(HAS_EXAM,evo):
            if ex in exams: evolution_of_exam[ex].add(evo)
    converted=[]; rejected=[]; resource_patients={}; trace=[]
    for ex in sorted(exams):
        errs=[]
        evo=evolution_of_exam[ex]
        if len(evo)==0:errs.append('NO_EVOLUTION_LINK')
        elif len(evo)!=1:errs.append('MULTIPLE_EVOLUTION_LINKS')
        pt=set()
        for e in evo:pt.update(patient_of_evolution[e])
        if len(pt)==0:errs.append('NO_PATIENT_LINK')
        elif len(pt)!=1:errs.append('MULTIPLE_PATIENT_LINKS')
        name=lone(graph.values(NAME,ex),'exam_name',errs,True)
        result=lone(graph.values(RESULT,ex),'result',errs)
        dt=lone(graph.values(EXAM_DATE,ex),'exam_date',errs)
        unit=lone(graph.values(EXAM_UNIT,ex),'exam_unit',errs)
        vals=fhir_value(result,errs)
        if name and (name.datatype!=XSD+'string' or not name.text.strip()): errs.append('INVALID_EXAM_NAME')
        if dt and (dt.datatype!=XSD+'string' or not date_check(dt.text)):
            errs.append('AMBIGUOUS_OR_INVALID_DATE')
        if unit and (unit.datatype!=XSD+'string' or not unit.text.strip()):
            errs.append('INVALID_UNIT')
        if unit and 'valueQuantity' not in vals:
            errs.append('UNIT_WITHOUT_NUMERIC_VALUE')
        if errs:
            rejected.append({'synthetic_exam':ex.removeprefix(TEST),'reasons':sorted(set(errs))})
            continue
        patient=next(iter(pt)); evol=next(iter(evo))
        patient_id=fid(patient,'p')
        obs={
            'resourceType':'Observation',
            'id':fid(ex,'o'),
            'status':'unknown',
            'code':{'text':name.text},
            'subject':{'reference':'Patient/'+patient_id},
        }
        if dt:obs['effectiveDateTime']=dt.text
        obs.update(vals)
        if unit:obs['valueQuantity']['unit']=unit.text # RAW display text; deliberately NO UCUM code/system
        converted.append(obs)
        resource_patients[patient_id]={'resourceType':'Patient','id':patient_id}
        trace.append({
            'source_exam':ex.removeprefix(TEST), 'source_evolution':evol.removeprefix(TEST),
            'source_patient':patient.removeprefix(TEST), 'target_observation':obs['id'],
            'target_patient':patient_id, 'source_value_datatype':result.datatype if result else None,
            'source_date_precision':len(dt.text) if dt else None,
            'status_rule':'Required FHIR status=unknown because source has no observation lifecycle status',
            'unit_rule':'Literal unit copied verbatim; no assumed UCUM code' if unit else None
        })
    resources=list(sorted(resource_patients.values(),key=lambda r:r['id'])) + sorted(converted,key=lambda r:r['id'])
    # Use stable, non-operational resource identities. Relative Observation.subject
    # references resolve against the common fullUrl base within this collection.
    # A duplicate occurrence MUST reuse the same fullUrl, triggering bdl-7.
    bundle={'resourceType':'Bundle','type':'collection','entry':[
        {'fullUrl':f'https://example.org/fhir/{r["resourceType"]}/{r["id"]}', 'resource':r}
        for r in resources]}
    counts=dict(Counter(reason for rec in rejected for reason in rec['reasons']))
    report={
        'scope':'SYNTHETIC TEST DATA ONLY; ORIGINAL INDIVIDUALS NEVER CONVERTED',
        'fhir_version':FHIR_VERSION,'patients_in_overlay':len(patients),
        'exams_in_overlay':len(exams),'emitted_observations':len(converted),
        'rejected_exams':len(rejected),'rejection_reasons':counts,
        'notes':['No semantic inference, no official HL7 validator, no terminology profile validation',
                 'Explicit refusals remain in denominator; incomplete exams may be emitted without value or effectiveDateTime',
                 'Only synthetic individuals identified by overlay namespace are processed',
                 'No DiagnosticReport or Encounter resource was generated']
    }
    return bundle,trace,rejected,report


def decimal_json(obj):
    """Serialize exact Decimal as JSON numeric lexeme, preserving significant decimal digits."""
    marker='ISYS_DECIMAL_MARKER_'
    numerics=[]
    def convert_dec(o):
        if isinstance(o,Decimal):
            numerics.append(o)
            return marker+str(len(numerics)-1)+'_END'
        if isinstance(o,dict):return {k:convert_dec(v) for k,v in o.items()}
        if isinstance(o,list):return [convert_dec(v) for v in o]
        return o
    serialized=json.dumps(convert_dec(obj),ensure_ascii=False,indent=2,sort_keys=True)
    for i,n in enumerate(numerics):
        num=format(n,'f')
        serialized=serialized.replace('"'+marker+str(i)+'_END"',num)
    return serialized+'\n'

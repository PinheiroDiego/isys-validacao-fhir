"""Q01-Q06 proof-of-concept: source and target are queried with DIFFERENT functions.
Comparisons are limited to successfully mapped *synthetic* occurrences. Original remains private.
"""
from datetime import date
import calendar
from decimal import Decimal
from .schema import *


def _scalar(value):
    if not value:return None
    if value.datatype in (XSD+'integer',XSD+'int',XSD+'decimal'):
        return ('number', str(Decimal(value.text).normalize()))
    return ('text',value.text)

def _item(g,p,exam):
    result=g.values(RESULT,exam)
    date0=g.values(EXAM_DATE,exam)
    unit=g.values(EXAM_UNIT,exam)
    name=g.values(NAME,exam)
    return {'patient':p.removeprefix(TEST),'exam':exam.removeprefix(TEST),
            'name':name[0].text if name else None,
            'result':_scalar(result[0]) if result else None,
            'date':date0[0].text if date0 else None,
            'unit':unit[0].text if unit else None}

def _source_items(graph,trace):
    # Compute source values from OWL assertions; only the eligible subset is fixed by trace.
    return [_item(graph,TEST+t['source_patient'],TEST+t['source_exam']) for t in trace]

def _target_items(bundle,trace):
    obs={e['resource']['id']:e['resource'] for e in bundle['entry'] if e['resource'].get('resourceType')=='Observation'}
    arr=[]
    for t in trace:
        r=obs[t['target_observation']]
        if 'valueQuantity' in r: value=('number',str(Decimal(str(r['valueQuantity']['value'])).normalize()))
        elif 'valueString' in r:value=('text',r['valueString'])
        else:value=None
        arr.append({'patient':t['source_patient'],'exam':t['source_exam'],
                    'name':r['code'].get('text'),'result':value,
                    'date':r.get('effectiveDateTime'),'unit':r.get('valueQuantity',{}).get('unit')})
    return arr

def _bounds(precision):
    if not precision:return None
    y=int(precision[:4])
    if len(precision)==4:return date(y,1,1),date(y,12,31)
    m=int(precision[5:7])
    if len(precision)==7:return date(y,m,1),date(y,m,calendar.monthrange(y,m)[1])
    day=date.fromisoformat(precision)
    return day,day

def _interval(date_literal,start,end):
    if not date_literal:return 'UNKNOWN_DATE'
    lo,hi=_bounds(date_literal)
    if start<=lo and hi<=end:return 'IN'
    if hi<start or lo>end:return 'OUT'
    return 'INDETERMINATE'

def queries(graph,bundle,trace,rejected):
    src=_source_items(graph,trace)
    dst=_target_items(bundle,trace)
    def q01(items):return sorted((x['patient'],x['exam']) for x in items)
    def q02(items):return sorted((x['exam'],x['result']) for x in items if x['result'] is not None)
    def q03(items):return sorted((x['exam'],x['date']) for x in items if x['date'] is not None)
    def q04(items):return sorted((x['exam'],x['result'],x['unit']) for x in items if x['result'] is not None)
    def q05(items):return sorted((x['exam'],_interval(x['date'],date(2026,3,1),date(2026,3,31))) for x in items)
    comps=[]
    for code,fn,description in [
        ('Q01',q01,'patient to examination occurrence (multiset)'),
        ('Q02',q02,'result belonging to examination occurrence'),
        ('Q03',q03,'date and explicit precision by occurrence'),
        ('Q04',q04,'explicit results and literal units'),
        ('Q05',q05,'three-valued membership in March 2026 range')]:
        a,b=fn(src),fn(dst)
        comps.append({'question':code,'scope':'accepted synthetic occurrences',
                      'description':description,'source_answer_count':len(a),
                      'target_answer_count':len(b),'exact_normalized_multiset_equivalence':a==b})
    # Q06 is loss inventory, not success rate; refusal acknowledged, not silently ignored.
    comps.append({'question':'Q06','scope':'all synthetic occurrences',
                  'description':'Explicit nonrepresented source occurrences and reasons',
                  'refusal_count':len(rejected),'refusal_reasons':rejected,
                  'unmapped_original_facts':'not evaluated; original individuals deliberately excluded',
                  'out_of_scope_features':['Evolution as Encounter','Clinical terminologies','Inference-generated triples']})
    return {'scope':'synthetic overlay, not study benchmark', 'comparisons':comps}

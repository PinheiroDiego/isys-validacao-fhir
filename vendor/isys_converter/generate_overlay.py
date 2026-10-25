"""Generate purely fictitious OWL/XML test overlay and extension metadata. No PHI."""
from pathlib import Path
from xml.etree import ElementTree as ET
from .schema import *

ET.register_namespace('', OWL)

def n(tag, parent, **attrs):
    return ET.SubElement(parent,'{'+OWL+'}'+tag,attrs)
def entity(kind,iri0,parent):n(kind,parent,IRI=iri0)
def axiom(root,kind,items):
    a=n(kind,root)
    for k,u in items:entity(k,u,a)
    return a

def generate(path):
    root=ET.Element('{'+OWL+'}Ontology',{'ontologyIRI':TEST.rstrip('#')})
    # The only extensions to the authentic ontology: three versioned properties.
    axiom(root,'Declaration',[('ObjectProperty',HAS_EXAM)])
    axiom(root,'ObjectPropertyDomain',[('ObjectProperty',HAS_EXAM),('Class',EVOLUTION)])
    axiom(root,'ObjectPropertyRange',[('ObjectProperty',HAS_EXAM),('Class',EXAM)])
    for prop in (EXAM_DATE,EXAM_UNIT):
        axiom(root,'Declaration',[('DataProperty',prop)])
        axiom(root,'DataPropertyDomain',[('DataProperty',prop),('Class',EXAM)])
        axiom(root,'DataPropertyRange',[('DataProperty',prop),('Datatype',XSD+'string')])
    pts=['p01','p02','p03','p04','p05','p06']
    evos=['ev01','ev02','ev_orphan','ev_multi','ev05','ev06']
    exs=['ex%02d'%i for i in range(1,12)]
    node=lambda id0: TEST+id0
    for id0,cls in [(x,PATIENT) for x in pts]+[(x,EVOLUTION) for x in evos]+[(x,EXAM) for x in exs]:
        axiom(root,'Declaration',[('NamedIndividual',node(id0))])
        axiom(root,'ClassAssertion',[('Class',cls),('NamedIndividual',node(id0))])
    for p,e in [('p01','ev01'),('p02','ev02'),('p03','ev_multi'),('p04','ev_multi'),('p05','ev05'),('p06','ev06')]:
        axiom(root,'ObjectPropertyAssertion',[('ObjectProperty',HAS_EVOLUTION),('NamedIndividual',node(p)),('NamedIndividual',node(e))])
    for e,ex in [('ev01','ex01'),('ev01','ex02'),('ev01','ex03'),('ev01','ex04'),('ev02','ex05'),('ev_orphan','ex06'),('ev_multi','ex07'),('ev05','ex08'),('ev06','ex09'),('ev06','ex10'),('ev06','ex11')]:
        axiom(root,'ObjectPropertyAssertion',[('ObjectProperty',HAS_EXAM),('NamedIndividual',node(e)),('NamedIndividual',node(ex))])
    def dp(prop, exam, value, datatype=XSD+'string'):
        a=axiom(root,'DataPropertyAssertion',[('DataProperty',prop),('NamedIndividual',node(exam))])
        v=n('Literal',a,datatypeIRI=datatype);v.text=str(value)
    for ex,name in [('ex01','CEA'),('ex02','Ultrassom'),('ex03','PSA'),('ex04','CEA'),('ex05','Hemograma'),('ex06','TSH'),('ex07','CEA'),('ex09','CEA'),('ex10','TSH'),('ex11','Glicemia')]:dp(NAME,ex,name)
    for ex,value,type0 in [('ex01','25.20','decimal'),('ex02','sem achados','string'),('ex04','25.20','decimal'),('ex05','8','integer'),('ex06','3','integer'),('ex07','1','integer'),('ex08','8','integer'),('ex09','1','integer'),('ex10','true','boolean'),('ex11','3','integer'),('ex11','4','integer')]:dp(RESULT,ex,value,XSD+type0)
    for ex,date in [('ex01','2026-03-12'),('ex02','2026-03'),('ex04','2026-03-15'),('ex05','2026'),('ex06','2026-03-15'),('ex07','2026-03-16'),('ex09','10/11/2026'),('ex10','2026-03-18'),('ex11','2026-03-19')]:dp(EXAM_DATE,ex,date)
    dp(EXAM_UNIT,'ex01','ng/mL')
    data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return path

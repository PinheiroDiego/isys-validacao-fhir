"""Load the original schema strictly read-only and a purely synthetic OWL/XML overlay.
No external entity resolution, imports, internet, reasoner, or original patient export.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from dataclasses import dataclass
import hashlib
import zipfile

BASE = 'http://www.semanticweb.org/marco/ontologies/2018/11/marco'
TEST = 'https://example.org/isys/fhir-semantic-test/2026/v1#'
EXAM = 'http://webprotege.stanford.edu/R95jloB4mXQPNYJr4PxDfL0'
NAME = 'http://webprotege.stanford.edu/R8Ln57NZOBVImw2EqPktO3f'
RESULT = 'http://webprotege.stanford.edu/RsGwsc6uggNZDQtrRF1fAg'
PATIENT = BASE + '#Paciente'
EVOLUTION = BASE + '#Evolução'
HAS_EVOLUTION = BASE + '#possui'
HAS_EXAM = TEST + 'tem_ocorrencia_exame'
EXAM_DATE = TEST + 'data_exame'
EXAM_UNIT = TEST + 'unidade_textual'
XSD = 'http://www.w3.org/2001/XMLSchema#'
OWL = 'http://www.w3.org/2002/07/owl#'
BASE_HASH = '54fde32e281df37b79773ca56128ad2526125bc3174717cbb04871750cfd8558'


def typ(el): return el.tag.rsplit('}', 1)[-1]


def iri(el, base=BASE):
    key = el.get('IRI') or el.get('abbreviatedIRI')
    if key is None: return None
    if key.startswith('#'): return base + key
    return key


def get_xml_bytes_from_zip(path):
    with zipfile.ZipFile(path) as archive:
        files = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith('.owx')]
        if len(files) != 1 or files[0].file_size > 4_000_000 or files[0].file_size < 1:
            raise ValueError('ZIP must contain one OWX no larger than 4 MB')
        if sum(i.file_size for i in archive.infolist()) > 10_000_000:
            raise ValueError('ZIP size cap exceeded')
        return archive.read(files[0])


def verify_base(path):
    raw = get_xml_bytes_from_zip(path)
    if hashlib.sha256(raw).hexdigest() != BASE_HASH:
        raise ValueError('Original OWX hash does not match verified schema; refusing conversion')
    r = ET.fromstring(raw)
    if typ(r) != 'Ontology' or r.get('ontologyIRI') != BASE:
        raise ValueError('Unexpected ontology IRI')
    decl = defaultdict(set)
    for a in r:
        if typ(a) == 'Declaration' and len(a) == 1:
            decl[typ(a[0])].add(iri(a[0]))
    for expected, kind in [(EXAM,'Class'),(PATIENT,'Class'),(EVOLUTION,'Class'),
                          (NAME,'DataProperty'),(RESULT,'DataProperty'),(HAS_EVOLUTION,'ObjectProperty')]:
        if expected not in decl[kind]: raise ValueError(f'Missing expected schema symbol: {expected}')
    return {'sha256': BASE_HASH, 'declarations': {k:len(v) for k,v in decl.items()}, 'declared_uris': decl}


@dataclass(frozen=True)
class Value:
    text: str
    datatype: str

class SyntheticGraph:
    def __init__(self, path: Path, base_declarations):
        raw = path.read_bytes()
        if len(raw) > 1_000_000: raise ValueError('Synthetic overlay file too large')
        root = ET.fromstring(raw)
        if typ(root) != 'Ontology' or root.get('ontologyIRI') != TEST.rstrip('#'):
            raise ValueError('Invalid test-only ontology IRI')
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.classes = defaultdict(set)
        self.objects = defaultdict(lambda: defaultdict(set))
        self.data = defaultdict(lambda: defaultdict(list))
        self.individuals = set()
        extension_objects = set()
        extension_data = set()
        for a in root:
            kind = typ(a)
            if kind == 'Import': raise ValueError('No remote imports allowed in overlay')
            if kind == 'Declaration' and len(a) == 1:
                tag = typ(a[0]); symbol = iri(a[0]);
                if tag == 'ObjectProperty' and symbol.startswith(TEST): extension_objects.add(symbol)
                if tag == 'DataProperty' and symbol.startswith(TEST): extension_data.add(symbol)
                if tag == 'NamedIndividual':
                    if not symbol.startswith(TEST): raise ValueError('All overlay individuals must be synthetic')
                    self.individuals.add(symbol)
            elif kind == 'ClassAssertion' and len(a) == 2:
                klass, ind = iri(a[0]), iri(a[1]); self._synthetic(ind)
                self.classes[ind].add(klass)
            elif kind == 'ObjectPropertyAssertion' and len(a) == 3:
                p,s,o = map(iri,a); self._synthetic(s); self._synthetic(o)
                self.objects[p][s].add(o)
            elif kind == 'DataPropertyAssertion' and len(a) == 3:
                p,s = iri(a[0]),iri(a[1]);self._synthetic(s)
                self.data[p][s].append(Value(a[2].text or '', a[2].get('datatypeIRI', XSD+'string')))
            elif kind in {'NegativeObjectPropertyAssertion','NegativeDataPropertyAssertion'}:
                raise ValueError('Negative property assertions are not in the pilot scope')
        if extension_objects != {HAS_EXAM} or extension_data != {EXAM_DATE,EXAM_UNIT}:
            raise ValueError('Unexpected or missing extension properties')
        # Forbid undeclared original predicates or classes. Original stays unmodified.
        for p in self.objects:
            if p not in extension_objects and p not in base_declarations['ObjectProperty']:
                raise ValueError('Unknown object property in extension')
        for p in self.data:
            if p not in extension_data and p not in base_declarations['DataProperty']:
                raise ValueError('Unknown data property in extension')
        for classes in self.classes.values():
            if not classes.issubset(base_declarations['Class']):
                raise ValueError('Unknown class used by test overlay')
        mentioned = set(self.classes)
        for vals in self.objects.values():
            for s, targets in vals.items(): mentioned.add(s); mentioned.update(targets)
        for vals in self.data.values(): mentioned.update(vals.keys())
        if not mentioned.issubset(self.individuals): raise ValueError('Every synthetic node must be declared')
    @staticmethod
    def _synthetic(uri):
        if not uri or not uri.startswith(TEST): raise ValueError('Overlay cannot assert facts on original individuals')
    def nodes(self, klass): return {s for s,ts in self.classes.items() if klass in ts}
    def values(self, prop, subj): return self.data[prop].get(subj, [])
    def target(self, prop, subj): return self.objects[prop].get(subj, set())

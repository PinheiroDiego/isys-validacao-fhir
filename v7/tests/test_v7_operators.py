"""Testes dos operadores N1–N4 sobre um Bundle de brinquedo escrito à mão.
Não usa casos V7, não chama o HL7 Validator nem o comparador."""
import sys, unittest, unicodedata, copy, re
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import v7_operators as op

def toy():
    return {'resourceType': 'Bundle', 'type': 'collection', 'entry': [
        {'fullUrl': 'https://example.org/fhir/Patient/p-aaa', 'resource': {'resourceType': 'Patient', 'id': 'p-aaa'}},
        {'fullUrl': 'https://example.org/fhir/Patient/p-bbb', 'resource': {'resourceType': 'Patient', 'id': 'p-bbb'}},
        {'fullUrl': 'https://example.org/fhir/Observation/o-111', 'resource': {
            'resourceType': 'Observation', 'id': 'o-111', 'status': 'unknown', 'code': {'text': 'Exame fictício'},
            'subject': {'reference': 'Patient/p-aaa'}, 'effectiveDateTime': '2025-12-01',
            'valueQuantity': {'value': Decimal('1.10'), 'unit': 'µg/L'}}},
        {'fullUrl': 'https://example.org/fhir/Observation/o-222', 'resource': {
            'resourceType': 'Observation', 'id': 'o-222', 'status': 'unknown', 'code': {'text': 'Teste textual'},
            'subject': {'reference': 'Patient/p-bbb'}, 'valueString': 'sem lesão'}},
        {'fullUrl': 'https://example.org/fhir/Observation/o-333', 'resource': {
            'resourceType': 'Observation', 'id': 'o-333', 'status': 'unknown', 'code': {'text': 'Ausente'},
            'subject': {'reference': 'Patient/p-aaa'},
            'dataAbsentReason': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/data-absent-reason', 'code': 'unknown'}]}}},
    ]}

def strip_text(b):
    b = copy.deepcopy(b)
    for e in b['entry']: e['resource'].pop('text', None)
    return b

class T(unittest.TestCase):
    def test_n1_only_adds_generated_narrative(self):
        b = toy(); n = op.n1_narrative(b)
        self.assertEqual(strip_text(n), b)
        for e in n['entry']:
            t = e['resource']['text']
            self.assertEqual(t['status'], 'generated')
            self.assertTrue(t['div'].startswith('<div xmlns="http://www.w3.org/1999/xhtml">'))
        self.assertIn('Resultado: 1.10 µg/L', n['entry'][2]['resource']['text']['div'])
        self.assertIn('ausente (motivo: desconhecido)', n['entry'][4]['resource']['text']['div'])
        self.assertEqual(b, toy())  # entrada não modificada

    def test_n2_consistent_reidentification(self):
        b = toy(); n = op.n2_reidentify(b, 'semente-de-teste')
        old = {e['resource']['id'] for e in b['entry']}
        new = [e['resource']['id'] for e in n['entry']]
        self.assertTrue(old.isdisjoint(new)); self.assertEqual(len(set(new)), len(new))
        for e in n['entry']:
            self.assertRegex(e['resource']['id'], r'^[A-Za-z0-9\-\.]{1,64}$')
            self.assertTrue(e['fullUrl'].endswith('/' + e['resource']['id']))
        pid = {e['resource']['id'] for e in n['entry'] if e['resource']['resourceType'] == 'Patient'}
        for e, eo in zip(n['entry'][2:], b['entry'][2:]):
            ref = e['resource']['subject']['reference']
            self.assertTrue(ref.startswith('Patient/') and ref.removeprefix('Patient/') in pid)
            # mesma associação paciente-ocorrência, a menos da renomeação
            idx_old = [x['resource']['id'] for x in b['entry']].index(eo['resource']['subject']['reference'].removeprefix('Patient/'))
            self.assertEqual(ref.removeprefix('Patient/'), n['entry'][idx_old]['resource']['id'])
        def facts(x):
            return [{k: v for k, v in e['resource'].items() if k not in ('id', 'subject')} for e in x['entry']]
        self.assertEqual(facts(n), facts(b))
        self.assertEqual(op.n2_reidentify(b, 'semente-de-teste'), n)  # determinístico

    def test_n3_absolute_reference_targets_same_patient(self):
        b = toy(); n = op.n3_absolute_reference(b)
        self.assertEqual(n['entry'][2]['resource']['subject']['reference'], 'https://example.org/fhir/Patient/p-aaa')
        self.assertEqual(n['entry'][3]['resource']['subject']['reference'], 'https://example.org/fhir/Patient/p-bbb')
        for e in n['entry'][2:]: e['resource']['subject']['reference'] = None
        bb = toy()
        for e in bb['entry'][2:]: e['resource']['subject']['reference'] = None
        self.assertEqual(n, bb)

    def test_n4_nfd_only_target_fields(self):
        b = toy(); n, k = op.n4_unicode_nfd(b)
        self.assertEqual(k, 2)  # 'fictício' e 'lesão'
        r = n['entry'][2]['resource']
        self.assertNotEqual(r['code']['text'], 'Exame fictício')
        self.assertEqual(unicodedata.normalize('NFC', r['code']['text']), 'Exame fictício')
        self.assertEqual(r['valueQuantity']['unit'], 'µg/L')  # unidade fora do escopo de N4
        self.assertEqual(unicodedata.normalize('NFC', n['entry'][3]['resource']['valueString']), 'sem lesão')
        for e in n['entry']:
            rr = e['resource']
            if 'code' in rr: rr['code']['text'] = unicodedata.normalize('NFC', rr['code']['text'])
            if 'valueString' in rr: rr['valueString'] = unicodedata.normalize('NFC', rr['valueString'])
        self.assertEqual(n, b)

    def test_n4_not_applicable_without_accents(self):
        b = {'resourceType': 'Bundle', 'type': 'collection', 'entry': [{'fullUrl': 'https://example.org/fhir/Observation/o-1',
             'resource': {'resourceType': 'Observation', 'id': 'o-1', 'code': {'text': 'Ferritina'}}}]}
        n, k = op.n4_unicode_nfd(b)
        self.assertEqual((n, k), (b, 0))

    def test_refusal_without_entry(self):
        self.assertEqual(op.serialize_refusal({'resourceType': 'Bundle', 'type': 'collection', 'entry': []}),
                         {'resourceType': 'Bundle', 'type': 'collection'})
        with self.assertRaises(AssertionError):
            op.serialize_refusal(toy())

if __name__ == '__main__':
    unittest.main()

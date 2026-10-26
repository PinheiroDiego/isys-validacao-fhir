"""Teste de fumaça do pipeline com famílias FICTÍCIAS T00/T01 (fora da V7), em diretório temporário.
Exige o ZIP original da ontologia em ISYS_ORIGINAL_ZIP; caso contrário, é ignorado.
Não chama o HL7 Validator nem o comparador."""
import os, sys, json, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

T00 = {'id': 'T00', 'split': 'smoke', 'scenario': 'fumaça', 'patients': ['p1'], 'evolutions': [{'id': 'e1', 'patients': ['p1']}],
       'exams': [{'id': 'x1', 'evolution': 'e1', 'datatype': 'decimal', 'name': 'Exame fictício de fumaça', 'value': '1.1',
                  'unit': 'mg/L', 'date': '2025-12-01'}],
       'expected_decision': 'emit', 'expected_rejection_reasons': [], 'mutation': {'kind': 'semantic', 'operation': 'change_unit'}}
T01 = {'id': 'T01', 'split': 'smoke', 'scenario': 'fumaça recusa', 'patients': ['p1'], 'evolutions': [{'id': 'e1', 'patients': []}],
       'exams': [{'id': 'x1', 'evolution': 'e1', 'datatype': 'decimal', 'name': 'Teste', 'value': '2.2', 'date': '2025-12-02'}],
       'expected_decision': 'reject', 'expected_rejection_reasons': ['NO_PATIENT_LINK'], 'mutation': None}

@unittest.skipUnless(os.environ.get('ISYS_ORIGINAL_ZIP'), 'ontologia original indisponível neste ambiente')
class T(unittest.TestCase):
    def test_smoke(self):
        import build_v7
        with tempfile.TemporaryDirectory() as d:
            regs, ovs, recs = build_v7.generate([T00, T01], Path(d), Path(os.environ['ISYS_ORIGINAL_ZIP']), 'SEMENTE-FUMACA')
            self.assertEqual([r['variant'] for r in regs], ['baseline', 'N1', 'N2', 'N3', 'N4', 'mutation', 'refusal'])
            self.assertNotIn('entry', regs[-1]['bundle'])
            self.assertEqual(regs[4]['expected_class'], 'equivalent_control')
            ordem = build_v7.assign_opaque(regs, 'SEMENTE-FUMACA')
            self.assertEqual(sorted(r['opaque_id'] for r in ordem), [f'V7-{i:03d}' for i in range(1, 8)])
            from isys_converter.transform import decimal_json
            for r in ordem:
                json.loads(decimal_json(r['bundle']))
            self.assertIn('T01', recs)

if __name__ == '__main__':
    unittest.main()

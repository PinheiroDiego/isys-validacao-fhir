"""Verifica as regras de aplicabilidade com SEMENTES ALTERNATIVAS de teste.
Nunca calcula os cenários com SEMENTE_V7 (proibido antes do commit de congelamento)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import v7_spec as s

class T(unittest.TestCase):
    def test_constraints_hold_for_alternative_seeds(self):
        for i in range(300):
            seed = f'TESTE-ALTERNATIVO-{i}'
            self.assertNotEqual(seed, s.SEMENTE_V7)
            F = s.build_families(seed)  # check_constraints é chamado internamente
            self.assertEqual(len(F), 11)
            self.assertEqual(sum(f['expected_decision'] == 'emit' for f in F), 8)

    def test_lists_satisfy_constraints_by_construction(self):
        self.assertNotIn(s.SAIDAS_MUTACAO_V61['rename_exam'], s.EXAMES_NUMERICOS_ACENTUADOS)
        self.assertNotIn(s.SAIDAS_MUTACAO_V61['change_unit'], s.UNIDADES)
        self.assertNotIn(s.SAIDAS_MUTACAO_V61['shift_day'], s.DATAS)
        self.assertTrue(set(s.RESULTADOS_TEXTUAIS).isdisjoint(s.SAIDAS_MUTACAO_V61['flip_negation']))
        self.assertTrue(all(s.tem_acento(x) for x in s.EXAMES_NUMERICOS_ACENTUADOS + s.EXAMES_TEXTUAIS_ACENTUADOS))
        self.assertFalse(any(s.tem_acento(x) for x in s.EXAMES_NUMERICOS_SEM_ACENTO))
        self.assertTrue(all(not v.endswith('0') for v in s.VALORES_DECIMAIS))
        self.assertEqual(len(set(s.VALORES_DECIMAIS)), len(s.VALORES_DECIMAIS))

    def test_pick2_distinct(self):
        for i in range(500):
            a, b = s.pick2(f'x{i}', s.VALORES_DECIMAIS, 'r')
            self.assertNotEqual(a, b)

if __name__ == '__main__':
    unittest.main()

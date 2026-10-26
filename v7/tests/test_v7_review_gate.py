"""B1/B3/R3: gate das fichas da especialista e resumo de sanidade, com dados fictícios."""
import sys, unittest, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import verify_v7 as v
from analyze_v7 import sanity_summary

KEY = [{'pair': f'P{i:02d}'} for i in range(1, 39)] + [{'refusal': f'R{i}'} for i in range(1, 4)]

def sheet(col, ids, verdict, crlf=False, bom=True, extra=None):
    lines = [f'{col},veredito,justificativa'] + [f'{i},{verdict},' for i in ids] + (extra or [])
    nl = '\r\n' if crlf else '\n'
    return (('\ufeff' if bom else '') + nl.join(lines) + nl).encode('utf-8')

PAIRS = [f'P{i:02d}' for i in range(1, 39)]
REFS = ['R1', 'R2', 'R3']

class T(unittest.TestCase):
    def ok(self, praw, rraw):
        return v.check_review_sheets(KEY, v.parse_sheet(praw, 'par'), v.parse_sheet(rraw, 'recusa'))

    def test_complete_sheets_pass_with_crlf_and_bom(self):
        self.assertEqual(self.ok(sheet('par', PAIRS, 'EQUIVALENTE', crlf=True), sheet('recusa', REFS, 'JUSTIFICADA', crlf=True)),
                         {'pairs': 38, 'refusals': 3})

    def test_missing_duplicate_extra_swapped_blank(self):
        r = sheet('recusa', REFS, 'JUSTIFICADA')
        for bad in (PAIRS[:-1], PAIRS + ['P38'], PAIRS + ['P39'], PAIRS[:-1] + ['P39']):
            with self.assertRaises(AssertionError):
                self.ok(sheet('par', bad, 'EQUIVALENTE'), r)
        with self.assertRaises(AssertionError):
            self.ok(sheet('par', PAIRS, ''), r)
        with self.assertRaises(AssertionError):
            self.ok(sheet('par', PAIRS, 'TALVEZ'), r)
        with self.assertRaises(AssertionError):
            self.ok(sheet('par', PAIRS, 'EQUIVALENTE'), sheet('recusa', REFS[:2], 'JUSTIFICADA'))

    def test_justification_required_for_non_equivalent(self):
        with self.assertRaises(AssertionError):
            self.ok(sheet('par', PAIRS, 'NAO_EQUIVALENTE'), sheet('recusa', REFS, 'JUSTIFICADA'))
        lines = ['par,veredito,justificativa'] + [f'{p},INCERTO,motivo registrado' for p in PAIRS]
        self.ok(('\n'.join(lines) + '\n').encode(), sheet('recusa', REFS, 'JUSTIFICADA'))

    def test_wrong_header_rejected(self):
        with self.assertRaises(AssertionError):
            v.parse_sheet(b'id,veredito,justificativa\nP01,EQUIVALENTE,\n', 'par')

    def test_hash_is_on_raw_bytes(self):
        a = sheet('par', PAIRS, 'EQUIVALENTE', crlf=True); b = sheet('par', PAIRS, 'EQUIVALENTE', crlf=False)
        self.assertNotEqual(hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest())

    def test_sanity_analysis_error_not_counted_as_miss(self):
        base = {'formalmente_valida': True, 'interpretavel': True, 'B_alert': False, 'C_alert': True, 'analysis_state': 'OK'}
        m = [dict(base, family='H01'), dict(base, family='H02', C_alert=None, analysis_state='ANALYSIS_ERROR: X'),
             dict(base, family='H03', formalmente_valida=False, B_alert=True)]
        s = sanity_summary(m)
        self.assertEqual((s['denominador_semantico_computado'], s['C_detectou'], s['erro_de_analise'], s['mutacao_formalmente_invalida']),
                         (1, 1, ['H02'], ['H03']))

if __name__ == '__main__':
    unittest.main()

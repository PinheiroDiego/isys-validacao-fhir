"""CI regression: Git may store the same CSV using LF instead of CRLF."""
import unittest,sys,hashlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from review_gate import attested_csv_matches_checkout,check
class TestCheckoutEol(unittest.TestCase):
 def test_git_lf_reproduction_for_both_attested_csvs(self):
  for rel in ('review/decisions.csv','review/evidence/FICHA_RESPONDER_RECEBIDA.csv'):
   raw=(ROOT/rel).read_bytes()
   # Source archives are frozen using CRLF. Github blob is the same text with LF.
   original=raw.replace(b'\n',b'\r\n') if b'\r' not in raw else raw
   lf=original.replace(b'\r\n',b'\n')
   original_digest=hashlib.sha256(original).hexdigest()
   with tempfile.TemporaryDirectory() as d:
    f=Path(d)/'evidence.csv'
    f.write_bytes(original)
    self.assertTrue(attested_csv_matches_checkout(f,original_digest),rel+' original')
    f.write_bytes(lf)
    self.assertTrue(attested_csv_matches_checkout(f,original_digest),rel+' Git LF')
    f.write_bytes(lf[:-1] + (b'X' if lf[-1:] != b'X' else b'Y'))
    self.assertFalse(attested_csv_matches_checkout(f,original_digest),rel+' tampering')
 def test_full_review_gate_with_both_git_normalized_files(self):
  import review_gate
  original_root=review_gate.ROOT
  # root override only for this test; all other files are read from a disposable copy
  import shutil
  with tempfile.TemporaryDirectory() as td:
   copy=Path(td)/'v61'
   shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('__pycache__'))
   for rel in ('review/decisions.csv','review/evidence/FICHA_RESPONDER_RECEBIDA.csv'):
    p=copy/rel
    p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
   try:
    review_gate.ROOT=copy
    self.assertEqual(check()['state'],'RATIFIED_WITH_RESSALVAS')
    # A clinically meaningful tamper must still be rejected.
    p=copy/'review/decisions.csv'
    p.write_bytes(p.read_bytes().replace(b'RATIFIED_WITH_RESSALVAS',b'INVALID_WITH_RESSALVAS',1))
    with self.assertRaises(AssertionError):check()
   finally:review_gate.ROOT=original_root
if __name__=='__main__':unittest.main()

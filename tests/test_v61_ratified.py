"""Post-ratification audit controls. Never runs HL7 validator nor scores holdout."""
import unittest,json,csv,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestRatificationRelease(unittest.TestCase):
 def test_received_source_preserved(self):
  f=ROOT/'review/evidence/FICHA_RESPONDER_RECEBIDA.csv'
  metadata=json.loads((ROOT/'review/evidence/ratification_transcription.json').read_text())
  self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),metadata['raw_csv_sha256'])
  self.assertEqual(metadata['normalizations'][0]['original_family'],'?')
 def test_g35_neutral_only_clinical_identity_unchanged(self):
  with zipfile.ZipFile(ROOT/'historical/v6.1-candidate-unaltered.zip') as z:
   old=json.loads(z.read('benchmark/inputs/G35/neutral.json'))
  new=json.loads((ROOT/'benchmark/inputs/G35/neutral.json').read_text())
  self.assertEqual(old.pop('id'),'synthetic-control-35')
  self.assertEqual(new.pop('id'),'batch-35')
  self.assertEqual(old,new)
 def test_g35_review_release_transcription(self):
  with (ROOT/'review/decisions.csv').open(encoding='utf-8-sig') as fp:
   rows={r['family']:r for r in csv.DictReader(fp)}
  g35=rows['G35'];g15=rows['G15']
  self.assertEqual(g35['expected_decision'],'emit')
  self.assertEqual(g35['mutation_operation'],'change_orphan_unit_note')
  self.assertEqual(g35['verdict'],'RATIFIED_WITH_RESSALVAS')
  self.assertEqual(g15['verdict'],'RATIFIED')
 def test_97_unchanged_inputs(self):
  with zipfile.ZipFile(ROOT/'historical/v6.1-candidate-unaltered.zip') as z:
   names=[x for x in z.namelist() if x.startswith('benchmark/inputs/') and x.endswith('.json')]
   changed=[x for x in names if z.read(x)!=(ROOT/x).read_bytes()]
  self.assertEqual(changed,['benchmark/inputs/G35/neutral.json'])
if __name__=='__main__':unittest.main()

"""DEVELOPMENT-ONLY deterministic engineering assertions.
No holdout semantic scoring before external review.
"""
import unittest,json,sys,hashlib
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from verify_v6 import verify
from review_gate import check
from semantic_oracle import compare
from competency_v4 import compare_queries
from build_v6 import mutate,neutral
class TestV6(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
  cls.fs={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 def get(self,v):return json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
 def test_history_frozen(self):self.assertEqual(verify()['v5_archives_verified'],3)
 def test_distinct_from_v4(self):self.assertFalse(set(self.fs)&{'F%02d'%i for i in range(1,27)})
 def test_counts(self):
  self.assertEqual(len(self.fs),36);self.assertEqual(len(self.m['variants']),96)
  self.assertEqual(sum(x['split']=='confirmatory' for x in self.m['variants']),70)
 def test_gold_locked(self):
  self.assertEqual(self.m['gold_sha256'],hashlib.sha256((ROOT/'benchmark/gold/families.json').read_bytes()).hexdigest())
 def test_review_gate_state_consistent(self):
  a=json.loads((ROOT/'review/attestation.json').read_text())
  if a['status']=='PENDING':
   with self.assertRaises(AssertionError):check()
  elif a['status']=='APPROVED':self.assertEqual(check()['state'],'APPROVED_DOCUMENTED')
  else:self.fail('Unsupported review state')
 def test_dev_references_equivalent(self):
  for v in self.m['variants']:
   if v['split']!='development' or v['variant']!='baseline' or v['expected_class']=='expected_refusal':continue
   self.assertEqual(compare(self.fs[v['family']],self.get(v)),[],v['id'])
 def test_dev_controls_no_oracle_alarm(self):
  for v in self.m['variants']:
   if v['split']=='development' and v['variant']=='neutral':self.assertFalse(compare(self.fs[v['family']],self.get(v)),v['id'])
 def test_dev_semantic_mutations_flagged(self):
  for v in self.m['variants']:
   if v['split']=='development' and v['expected_class']=='semantic_fault':self.assertTrue(compare(self.fs[v['family']],self.get(v)),v['id'])
 def test_dev_queries_base_equivalent(self):
  for v in self.m['variants']:
   if v['split']=='development' and v['variant']=='baseline' and v['expected_class']=='correct_conversion':
    self.assertEqual(compare_queries(self.fs[v['family']],self.get(v))['Q06']['count'],0,v['id'])
 def test_dev_queries_neutral_equivalent(self):
  for v in self.m['variants']:
   if v['split']=='development' and v['variant']=='neutral':
    self.assertEqual(compare_queries(self.fs[v['family']],self.get(v))['Q06']['count'],0,v['id'])
 def test_dev_rejects_are_recorded(self):
  a={x['family']:x for x in self.m['families']}
  for fid in ('G09','G10'):self.assertEqual(a[fid]['refused'],1)
 def test_human_review_state_declared(self):self.assertIn(json.loads((ROOT/'review/attestation.json').read_text())['status'],('PENDING','APPROVED'))
 def test_original_zip_not_in_distribution(self):self.assertFalse((ROOT/'ontologia-cbms-ontologies.owx.zip').exists())
 def test_no_evaluation_files_named_old_F(self):self.assertTrue(all(not x['id'].startswith('F') for x in self.m['variants']))
if __name__=='__main__':unittest.main()

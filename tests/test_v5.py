import unittest,json,hashlib,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from verify_v5 import check
from semantic_oracle import compare
from competency_v4 import compare_queries
class V5Regression(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((ROOT/'benchmark/manifest_v5.json').read_text())
  cls.gold={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
 def test_frozen_version_manifest(self):self.assertEqual(check()['technical_corrections'],12)
 def test_semantic_expected_behavior(self):
  for v in self.m['variants']:
   obj=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
   diff=compare(self.gold[v['family']],obj)
   self.assertEqual(bool(diff),v['expected_class'] in ('semantic_fault',) or v['family']=='F18' and v['variant']=='mutation' or v['family']=='F19' and v['variant']=='mutation',v['id'])
 def test_repaired_neutral_controls_preserve_knowledge(self):
  for v in self.m['variants']:
   if v['expected_class']=='semantic_equivalent_control':
    obj=json.loads((ROOT/v['path']).read_text(),parse_float=Decimal)
    self.assertEqual([],compare(self.gold[v['family']],obj))
    self.assertEqual([],compare_queries(self.gold[v['family']],obj)['Q06']['mismatched_queries'])
    self.assertNotIn('https://example.org/isys/benchmark/metadata',json.dumps(obj,default=str))
 def test_expected_refusals_are_empty_valid_bundle_shape(self):
  for v in self.m['variants']:
   if v['expected_class']=='expected_refusal':
    obj=json.loads((ROOT/v['path']).read_text())
    self.assertNotIn('entry',obj)
    self.assertEqual(obj['type'],'collection')
 def test_v5_official_results_not_claimed(self):
  self.assertFalse((ROOT/'outputs/official_v5/evaluation/execution-summary.json').exists())

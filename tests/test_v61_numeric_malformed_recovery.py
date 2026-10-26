"""Regression for G25 malformed valueQuantity numeric payload."""
import sys,unittest,json
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from competency_v4 import normalize_value,compare_queries

class TestMalformedNumericV61(unittest.TestCase):
 def test_numeric_valid_unchanged(self):
  self.assertEqual(('numeric','1.23'), normalize_value('1.2300','decimal'))
  self.assertEqual(('numeric','0'), normalize_value('0','decimal'))
 def test_nonnumeric_quantity_is_not_coerced_to_zero_or_valid(self):
  self.assertEqual(('invalid_numeric','not-a-number'),normalize_value('not-a-number','decimal'))
  self.assertEqual(('invalid_numeric','NaN'),normalize_value('NaN','decimal'))
  self.assertEqual(('invalid_numeric','Infinity'),normalize_value('Infinity','decimal'))
 def test_g25_mutation_does_not_abort_and_is_not_equivalent(self):
  fs={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
  b=json.loads((ROOT/'benchmark/inputs/G25/mutation.json').read_text(),parse_float=Decimal)
  result=compare_queries(fs['G25'],b)
  self.assertEqual(result['status'],'COMPARED')
  self.assertTrue(result['Q06']['mismatched_queries'])
  self.assertTrue('Q02' in result['Q06']['mismatched_queries'] or 'Q04' in result['Q06']['mismatched_queries'])

if __name__=='__main__':unittest.main()

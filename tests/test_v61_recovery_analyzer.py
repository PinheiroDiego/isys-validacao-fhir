"""Reanalysis should consume immutable already executed official outcomes."""
import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analyze_v6 import analyze
class TestV61RecoveredAnalysis(unittest.TestCase):
 def test_official_replay_works_without_java(self):
  d=analyze('confirmatory')
  self.assertEqual(d['scope'],'confirmatory')
  self.assertTrue(d['official_hl7_executed'])
  self.assertEqual(len(d['cases']) + len(d['source_refusals_separate'])+len(d['excluded_due_to_baseline']),72)
  self.assertGreaterEqual(d['official_duration_seconds_total'],0)
if __name__=='__main__':unittest.main()

import unittest,json,sys,hashlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from verify_freeze import verify
from semantic_oracle import score_variants,compare
from assemble import write_overlay
from run_hl7_v4 import parse_outcome
from competency_v4 import compare_queries

class BenchmarkV4Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.gold=json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']
  cls.manifest=json.loads((ROOT/'benchmark/manifest_v4.json').read_text())
 def test_baseline_archives_and_immutable_hashes(self):self.assertEqual(verify()['status'],'PASS')
 def test_counts_and_splits(self):
  self.assertEqual(len(self.gold),26)
  self.assertEqual(len(self.manifest['variants']),66)
  self.assertEqual(sum(f['split']=='development' for f in self.gold),8)
  self.assertEqual(sum(f['split']=='evaluation' for f in self.gold),18)
 def test_no_real_original_individuals_in_overlays(self):
  for f in self.gold:
   xml=(ROOT/'benchmark/fixtures/overlays'/f'{f["id"]}.owx').read_text()
   self.assertNotIn('NamedIndividual IRI="http://www.semanticweb.org/marco/',xml)
 def test_development_gold_matching(self):
  rows=score_variants('development')
  self.assertEqual(len(rows),24)
  self.assertFalse([r for r in rows if r['oracle_flags']!=r['expected_semantic_fault']])
 def test_controls_are_nontrivial_and_equivalent(self):
  fs={f['id']:f for f in self.gold}
  for f in self.gold[:8]:
   fid=f['id'];base=json.loads((ROOT/'benchmark/inputs'/fid/'baseline.json').read_text());ctl=json.loads((ROOT/'benchmark/inputs'/fid/'neutral.json').read_text())
   self.assertNotEqual(base,ctl)
   self.assertEqual([],compare(fs[fid],ctl))
 def test_semantic_mutations_have_differences_in_development(self):
  fs={f['id']:f for f in self.gold}
  for f in self.gold[:8]:
   fid=f['id'];mut=json.loads((ROOT/'benchmark/inputs'/fid/'mutation.json').read_text())
   self.assertTrue(compare(fs[fid],mut))
 def test_all_source_refusals_are_recorded_with_reasons(self):
  metric={x['family']:x for x in self.manifest['families']}
  for f in self.gold:
   if f['expected_decision']=='reject':
    self.assertEqual(len(f['exams']),metric[f['id']]['actual_rejected'])
    reasons={r for record in metric[f['id']]['rejection_reasons'] for r in record['reasons']}
    self.assertEqual(set(f['expected_rejection_reasons']),reasons)
 def test_original_zip_unchanged(self):
  self.assertEqual(self.manifest['source_original_sha256_before'],self.manifest['source_original_sha256_after'])
 def test_all_fhir_bundles_reference_resolve_for_normal_baselines(self):
  for v in self.manifest['variants']:
   if v['variant']!='baseline':continue
   b=json.loads((ROOT/v['path']).read_text())
   self.assertEqual('collection',b['type'])
   urls={x['fullUrl'] for x in b['entry']}
   for e in b['entry']:
    r=e['resource']
    if r['resourceType']=='Observation':
     self.assertIn('https://example.org/fhir/'+r['subject']['reference'],urls)
 def test_structural_negative_cases_are_fixtures_not_official_results(self):
  for fid in ['F17','F18','F19','F20']:
   b=json.loads((ROOT/'benchmark/inputs'/fid/'mutation.json').read_text())
   res=[x['resource'] for x in b['entry'] if x['resource']['resourceType']=='Observation'][0]
   if fid=='F17':self.assertNotIn('status',res)
   if fid=='F18':self.assertNotEqual(len(b['entry']),len(set(x['fullUrl'] for x in b['entry'])))
   if fid=='F19':self.assertNotIn('code',res)
   if fid=='F20':self.assertEqual('not-a-valid-status',res['status'])
 def test_overlay_reproducible(self):
  with tempfile.TemporaryDirectory() as tmp:
   for f in self.gold[:8]:
    p=Path(tmp)/(f['id']+'.owx');write_overlay(f,p)
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.manifest['overlay_hashes']['benchmark/fixtures/overlays/'+f['id']+'.owx'])
 def test_official_outcome_parser(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'outcome.json';p.write_text(json.dumps({'resourceType':'OperationOutcome','issue':[{'severity':'warning','code':'invariant'},{'severity':'error','code':'required'}]}))
   s=parse_outcome(p);self.assertEqual(s['errors'],1);self.assertEqual(s['warnings'],1)
 def test_no_v4_official_results_are_fabricated(self):
  self.assertFalse((ROOT/'outputs/official_v4/evaluation/execution-summary.json').exists())
 def test_development_q01_to_q05_equivalence_and_controls(self):
  fs={f['id']:f for f in self.gold}
  for f in self.gold[:8]:
   for v in ('baseline','neutral'):
    b=json.loads((ROOT/'benchmark/inputs'/f['id']/(v+'.json')).read_text())
    result=compare_queries(fs[f['id']],b)
    self.assertFalse(result['Q06']['mismatched_queries'])
 def test_development_mutated_competency_queries_detect_change(self):
  fs={f['id']:f for f in self.gold}
  for f in self.gold[:8]:
   b=json.loads((ROOT/'benchmark/inputs'/f['id']/'mutation.json').read_text())
   result=compare_queries(fs[f['id']],b)
   self.assertTrue(result['Q06']['mismatched_queries'])
 def test_gold_is_not_implemented_in_converter(self):
  converter=' '.join(p.read_text() for p in (ROOT/'vendor/isys_converter').glob('*.py'))
  self.assertNotIn('benchmark/gold/families.json',converter)

if __name__=='__main__':unittest.main()

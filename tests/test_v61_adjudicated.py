"""Engineering invariants for adjudicated patterns, not blind holdout efficacy scoring."""
import unittest,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from semantic_oracle import compare
from competency_v4 import compare_queries
G={f['id']:f for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']}
def obs(fid,variant):
 b=json.loads((ROOT/f'benchmark/inputs/{fid}/{variant}.json').read_text())
 return b,next(e['resource'] for e in b['entry'] if e['resource'].get('resourceType')=='Observation')
class TestAdjudication(unittest.TestCase):
 def test_g15_g35_reference_absence_policy(self):
  for fid in ('G15','G35'):
   for var in ('baseline','neutral'):
    b,o=obs(fid,var)
    self.assertNotIn('valueQuantity',o);self.assertNotIn('valueString',o)
    self.assertEqual(o['dataAbsentReason']['coding'][0]['code'],'unknown')
    self.assertEqual(o['status'],'unknown')
 def test_g35_unit_stays_in_note(self):
  for var in ('baseline','neutral'):
   _,o=obs('G35',var)
   self.assertEqual(o['note'][0]['text'],"Origem informa unidade_textual 'mg/dL' sem resultado associado (G35-x1).")
 def test_g35_semantic_mutation_changes_note_only(self):
  _,o=obs('G35','mutation')
  self.assertEqual(o['note'][0]['text'],"Origem informa unidade_textual 'g/L' sem resultado associado (G35-x1).")
  self.assertNotIn('valueQuantity',o)
 def test_g15_mutation_keeps_obs6_valid_by_construction(self):
  _,o=obs('G15','mutation');self.assertEqual(o['valueQuantity']['value'],42)
  self.assertNotIn('dataAbsentReason',o)
 def test_q04_preserves_orphan_unit(self):
  for v in ('baseline','neutral'):
   b,_=obs('G35',v);self.assertEqual(compare_queries(G['G35'],b)['Q06']['count'],0)
 def test_oracle_rejects_orphan_unit_change(self):
  b,_=obs('G35','mutation');self.assertIn('orphan_unit_provenance',[x['field'] for x in compare(G['G35'],b)])
 def test_oracle_handles_invented_numeric_value(self):
  b,_=obs('G15','mutation');self.assertIn('invented_value',[x['field'] for x in compare(G['G15'],b)])
 def test_only_six_fhir_files_modified(self):
  old=Path('/mnt/data/isys-benchmark-v6')
  if not old.exists():self.skipTest('Original V6 not mounted; cross-version check recorded in delta report')
  m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
  changed={v['path'] for v in m['variants'] if not (old/v['path']).exists() or (ROOT/v['path']).read_bytes() != (old/v['path']).read_bytes()}
  want={f'benchmark/inputs/{f}/{k}.json' for f in ('G15','G35') for k in ('baseline','mutation','neutral') if not (f=='G15' and k=='mutation')}
  self.assertEqual(changed,want)
if __name__=='__main__':unittest.main()

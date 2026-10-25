import unittest,json,hashlib,copy,sys
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_official import metrics

class TestRevalidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/'outputs/engineering/manifest_inputs.json').read_text())
        cls.ref=json.loads((ROOT/'inputs/baseline/bundle.json').read_text(),parse_float=Decimal)

    def test_fixed_versions_and_request_count(self):
        self.assertEqual(self.manifest['fhir_release'],'4.0.1')
        self.assertEqual(self.manifest['validator_pinned_release'],'7.0.3')
        self.assertEqual(len(self.manifest['requests']),16)

    def test_manifest_hashes(self):
        for rel,h in self.manifest['input_file_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h)

    def test_fullurls_and_references_resolve(self):
        self.assertEqual(len(self.ref['entry']),7)
        seen={}
        for entry in self.ref['entry']:
            r=entry['resource'];url=entry['fullUrl']
            self.assertEqual(url,f'https://example.org/fhir/{r["resourceType"]}/{r["id"]}')
            self.assertNotIn(url,seen);seen[url]=r
        for entry in self.ref['entry']:
            r=entry['resource']
            if r['resourceType']=='Observation':
                self.assertIn('https://example.org/fhir/'+r['subject']['reference'],seen)

    def test_duplicate_control_reuses_fullurl(self):
        control=json.loads((ROOT/'inputs/mutations/duplicate_observation_entry.json').read_text())
        urls=[e['fullUrl'] for e in control['entry']]
        self.assertEqual(len(urls),8)
        self.assertEqual(len(set(urls)),7)

    def test_required_status_control(self):
        control=json.loads((ROOT/'inputs/mutations/remove_required_status.json').read_text())
        self.assertEqual(1,sum(e['resource']['resourceType']=='Observation' and 'status' not in e['resource'] for e in control['entry']))

    def test_numeric_lexeme_preserved(self):
        self.assertIn('25.20', (ROOT/'inputs/baseline/bundle.json').read_text())

    def test_no_fake_mutation_detection_when_baseline_invalid(self):
        run={'status':'COMPLETED','results':[],'attempted_requests':16}
        base={'id':'base_bundle','cohort':'baseline','resourceType':'Bundle','status':'VALIDATED',
              'errors':17,'warnings':0,'issues':[{'severity':'error','code':'required','details_text':'Bundle entry missing fullUrl','expression':['Bundle.entry[0]']}],'conforms_base_profile':False}
        run['results'].append(base)
        for r in self.manifest['requests'][1:]:
            record={'id':r['id'],'cohort':r['cohort'],'resourceType':r['resourceType'],'status':'VALIDATED',
                  'errors':17 if r['cohort']=='mutation' else 0,'warnings':0,
                  'issues':copy.deepcopy(base['issues']) if r['cohort']=='mutation' else [],
                  'conforms_base_profile':r['cohort']!='mutation'}
            run['results'].append(record)
        m=metrics(self.manifest,run)
        self.assertIsNone(m['official_mutation_detection_rate'])
        self.assertIsNone(m['end_to_end_source_conformant_coverage'])
        self.assertEqual(m['condition_B'],'BASELINE_INVALID')

if __name__=='__main__':unittest.main()

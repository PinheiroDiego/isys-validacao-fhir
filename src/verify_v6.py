"""Fail closed on any silent change to V6 gold, candidate inputs, source or V5 archives."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 m=json.loads((ROOT/'benchmark/manifest_v6.json').read_text(encoding='utf8'))
 assert m['gold_sha256']==sha(ROOT/'benchmark/gold/families.json'),'gold changed'
 for name,dig in m['historical_archives_sha256'].items():assert sha(ROOT/name)==dig,'V5 altered '+name
 for name,dig in m['file_sha256'].items():assert sha(ROOT/name)==dig,'FHIR input altered '+name
 for name,dig in m['overlays_sha256'].items():assert sha(ROOT/name)==dig,'OWL overlay altered '+name
 fs=json.loads((ROOT/'benchmark/gold/families.json').read_text(encoding='utf8'))['families']
 assert len(fs)==36 and len(m['variants'])==98
 assert len(set(f['id'] for f in fs))==36
 assert {f['split'] for f in fs}=={'development','confirmatory'}
 assert {f['id'] for f in fs}.isdisjoint({f'F{i:02d}' for i in range(1,27)})
 assert len([v for v in m['variants'] if v['split']=='development'])==26
 assert len([v for v in m['variants'] if v['split']=='confirmatory'])==72
 assert 31==sum(f['expected_decision']=='emit' for f in fs)
 assert 5==sum(f['expected_decision']=='reject' for f in fs)
 expected={r['family']:r for r in m['families']}
 for f in fs:
  r=expected[f['id']];assert r['source_occurrences']==len(f['exams'])
  assert (r['emitted'] == len(f['exams'])) if f['expected_decision']=='emit' else (r['refused']==len(f['exams']))
 return {'state':'PASS','families':len(fs),'historical_archives_verified':len(m['historical_archives_sha256']),
  'owl_overlays_verified':len(m['overlays_sha256']),'fhir_inputs_verified':len(m['file_sha256']),
  'gold_hash':m['gold_sha256'],'original_ontology_hash_recorded':m['source_ontology_original_sha256'],
  'ontology_original_bytes_distributed':False}
if __name__=='__main__':
 try:print(json.dumps(verify(),ensure_ascii=False))
 except Exception as exc:print('FAIL',str(exc),file=sys.stderr);sys.exit(2)

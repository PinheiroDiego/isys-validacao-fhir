"""Integrity gate for V4 frozen sources and V5 corrective follow-up."""
from pathlib import Path
import json,hashlib,zipfile
from decimal import Decimal
from verify_freeze import verify
ROOT=Path(__file__).resolve().parents[1]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 original=verify()
 m=json.loads((ROOT/'benchmark/manifest_v5.json').read_text())
 old=json.loads((ROOT/'benchmark/manifest_v4.json').read_text())
 assert m['gold_sha256']==old['gold_sha256']
 assert m['v4_manifest_sha256']==h(ROOT/'benchmark/manifest_v4.json')
 assert m['v4_evaluation_artifact_sha256']==h(ROOT/'provenance/isys-benchmark-v4-evaluation-original.zip')
 assert len(m['variants'])==42 and len(m['fixed_changes'])==12
 assert len({v['id'] for v in m['variants']})==42
 updates={x['id']:x for x in m['fixed_changes']}
 for v in m['variants']:
  before=ROOT/v['v4_path']; after=ROOT/v['path']
  assert h(after)==m['hashes'][v['path']]
  old_json=json.loads(before.read_text(encoding='utf8'),parse_float=Decimal)
  new_json=json.loads(after.read_text(encoding='utf8'),parse_float=Decimal)
  if v['id'] in updates:
   assert h(before)==updates[v['id']]['v4_input_sha256']
   assert h(after)==updates[v['id']]['v5_input_sha256']
   if v['expected_class']=='expected_refusal':
    assert old_json.pop('entry')==[]
    assert new_json==old_json
   else:
    assert v['expected_class']=='semantic_equivalent_control'
    assert v['operation']=='metadata_only'
    assert old_json.pop('meta')['tag'][0]['system']=='https://example.org/isys/benchmark/metadata'
    assert new_json.pop('meta')=={'versionId':'synthetic-control-v5'}
    assert old_json==new_json
  else:
   assert before.read_bytes()==after.read_bytes(),v['id']
 assert original['status']=='PASS'
 return {'v4_frozen':True,'v5_cases':len(m['variants']),'technical_corrections':len(updates),'source_gold_unchanged':True,'manifest_sha256':h(ROOT/'benchmark/manifest_v5.json'),'v4_official_zip_sha256':m['v4_evaluation_artifact_sha256']}
if __name__=='__main__':print(json.dumps(check(),indent=2))

#!/usr/bin/env python3
import json,hashlib,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'outputs/engineering/manifest_inputs.json').read_text())
for rel,want in manifest['input_file_hashes'].items():
    content=(ROOT/rel).read_bytes()
    assert hashlib.sha256(content).hexdigest()==want, f'hash mismatch: {rel}'
reqs=manifest['requests']; assert len(reqs)==16 and len(manifest['mutations'])==8
ref=json.loads((ROOT/'inputs/baseline/bundle.json').read_text())
assert ref['type']=='collection' and len(ref['entry'])==7
urls={}
for e in ref['entry']:
    r=e['resource'];u=e['fullUrl']
    assert u==f'https://example.org/fhir/{r["resourceType"]}/{r["id"]}'
    assert u not in urls, 'duplicate baseline fullUrl'
    urls[u]=r
for e in ref['entry']:
    r=e['resource']
    if r['resourceType']=='Observation':
        assert 'https://example.org/fhir/'+r['subject']['reference'] in urls
        assert r['status']=='unknown'
for e in (ROOT/'inputs/mutations').glob('*.json'):
    m=json.loads(e.read_text())
    assert m['type']=='collection'
    for x in m['entry']:
        r=x['resource']; assert x['fullUrl']==f'https://example.org/fhir/{r["resourceType"]}/{r["id"]}'
ctrl=json.loads((ROOT/'inputs/mutations/remove_required_status.json').read_text())
assert any(e['resource'].get('resourceType')=='Observation' and 'status' not in e['resource'] for e in ctrl['entry'])
print('PREFLIGHT_OK; 16 hashes verified; baseline fullUrls unique and references resolvable; intentional mutations unchanged')

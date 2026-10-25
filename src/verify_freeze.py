"""Fail closed when inputs, original V3 result ZIP or frozen gold change."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PINNED_V3_ARCHIVE_SHA256='d4012e5bbfdf0a010b659b447037dee8a7d30e51c3f7fc72a9cea00ba6bc125f'
PINNED_V4_GOLD_SHA256='dec62b7e8e479270d447229946e8bbfd785e269a705be69b204b05766715ba94'
PINNED_V4_MANIFEST_SHA256='88d47da29e20f7e23ee1ef22a44d78c304f8ba233269493be129ac239a61a318'
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify():
 frozen=json.loads((ROOT/'baseline_v3/frozen_manifest.json').read_text(encoding='utf8'))
 assert h(ROOT/'baseline_v3/hl7_official_v3.zip')==PINNED_V3_ARCHIVE_SHA256, 'V3 pinned hash mismatch'
 assert h(ROOT/'benchmark/gold/families.json')==PINNED_V4_GOLD_SHA256,'V4 pinned gold mismatch'
 assert h(ROOT/'benchmark/manifest_v4.json')==PINNED_V4_MANIFEST_SHA256,'V4 pinned manifest mismatch'
 for name,meta in frozen['sources'].items():
  assert h(ROOT/'baseline_v3'/name)==meta['sha256'],f'V3 archive modified: {name}'
 manifest=json.loads((ROOT/'benchmark/manifest_v4.json').read_text(encoding='utf8'))
 assert manifest['gold_sha256']==h(ROOT/'benchmark/gold/families.json'),'Gold was modified after freeze'
 for p,value in manifest['file_hashes'].items():
  assert h(ROOT/p)==value,f'Input was modified: {p}'
 for p,value in manifest['overlay_hashes'].items():
  assert h(ROOT/p)==value,f'OWL/XML overlay was modified: {p}'
 assert manifest['source_original_sha256_before']==manifest['source_original_sha256_after'],'Original ontology was modified'
 # Frozen vendor source code must match V1.1 archive on disk (not build-generated outputs).
 from zipfile import ZipFile
 with ZipFile(ROOT/'baseline_v3/converter_v1_1.zip') as z:
  for p in (ROOT/'vendor/isys_converter').glob('*.py'):
   candidates=[n for n in z.namelist() if n.endswith('src/isys_converter/'+p.name)]
   assert len(candidates)==1,p.name
   assert hashlib.sha256(z.read(candidates[0])).hexdigest()==h(p),'Converter vendor modified '+p.name
 return {'frozen_v3_zip_sha256':frozen['sources']['hl7_official_v3.zip']['sha256'], 'v4_gold_sha256':manifest['gold_sha256'],
         'verified_variants':len(manifest['variants']), 'verified_overlays':len(manifest['overlay_hashes']),
         'original_owl_sha256':frozen['original_owl_sha256'], 'status':'PASS'}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False))

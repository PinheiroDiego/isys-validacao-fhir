"""Gates confirmatory execution on documented external FHIR expert adjudication.
This verifies the integrity/completeness of declarations, not the human's identity.
"""
import csv,hashlib,json,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 att=json.loads((ROOT/'review/attestation.json').read_text(encoding='utf8'))
 man=json.loads((ROOT/'benchmark/manifest_v6.json').read_text(encoding='utf8'))
 assert att.get('status')=='APPROVED','expert approval not received'
 assert att.get('gold_sha256')==man['gold_sha256'],'gold hash not attested'
 assert att.get('decisions_sha256')==sha(ROOT/'review/decisions.csv'),'review CSV edited after attestation'
 assert len(str(att.get('reviewer_id','')))>3 and att['reviewer_id']!='PENDING','reviewer id unavailable'
 assert len(str(att.get('qualification_summary','')))>15 and att['qualification_summary']!='PENDING','reviewer expertise not documented'
 assert str(att.get('independent_of_authoring'))=='YES','independence not attested'
 assert str(att.get('review_date')) not in ('PENDING','None',''), 'review date missing'
 with (ROOT/'review/decisions.csv').open(encoding='utf-8-sig',newline='') as fh:rows=list(csv.DictReader(fh))
 confirm={f['id'] for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families'] if f['split']=='confirmatory'}
 got={r['family'] for r in rows if r['family'] in confirm}
 assert got==confirm,'missing families in review sheet'
 for r in rows:
  if r['family'] not in confirm:continue
  assert r['verdict']=='APPROVE',f"not approved {r['family']}"
  assert r['semantic_gold_correct']=='YES',f"semantic gold not approved {r['family']}"
  assert r['fhir_structural_expectation_correct']=='YES',f"FHIR expectation not approved {r['family']}"
  assert r['refusal_correct'] in (('YES',) if r['expected_decision']=='reject' else ('N/A',)),f"refusal mismatch {r['family']}"
 return {'state':'APPROVED_DOCUMENTED','confirmatory_families':len(confirm),'reviewer_id':att['reviewer_id'],
   'limitation':'Declared expert review; identity and credentials must be separately verified by authors'}
if __name__=='__main__':
 try:print(json.dumps(check(),ensure_ascii=False))
 except Exception as exc:print('BLOCKED:',str(exc),file=sys.stderr);sys.exit(3)

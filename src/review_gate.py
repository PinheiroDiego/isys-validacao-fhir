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
 assert att.get('status')=='APPROVED_WITH_RESSALVAS','ratification with documented reservations not complete'
 assert att.get('gold_sha256')==man['gold_sha256'],'gold hash not attested'
 assert att.get('decisions_sha256')==sha(ROOT/'review/decisions.csv'),'review CSV edited after attestation'
 assert len(str(att.get('reviewer_id','')))>3 and att['reviewer_id']!='PENDING','reviewer id unavailable'
 assert len(str(att.get('qualification_summary','')))>15 and att['qualification_summary']!='PENDING','reviewer expertise not documented'
 assert att.get('independent_of_authoring')=='EXTERNAL_SPECIALIST_REVIEW_REPORTED_BY_RESEARCHER','external reviewer confirmation/provenance absent'
 assert att.get('consent_to_use_pseudonym_in_paper') is True,'anonymized use consent absent'
 assert att.get('expert_reply_sha256')==sha(ROOT/'review/evidence/FICHA_RESPONDER_RECEBIDA.csv'),'received ratification CSV changed'
 assert str(att.get('review_date')) not in ('PENDING','None',''), 'review date missing'
 with (ROOT/'review/decisions.csv').open(encoding='utf-8-sig',newline='') as fh:rows=list(csv.DictReader(fh))
 prior=json.loads((ROOT/'review/prior_V6_external_review_evidence.json').read_text(encoding='utf8'))
 assert prior.get('global_conclusion')=='APROVO_COM_RESSALVAS' and prior.get('variants_reviewed')==66 and prior.get('refusal_cases_reviewed')==4, 'original external review evidence incomplete'
 assert set(prior.get('not_carried_due_to_changed_inputs',[]))=={'G15','G35'}, 'delta scope drift'
 import zipfile
 with zipfile.ZipFile(ROOT/'historical/v6-candidate-unaltered.zip') as orig:
  manifest=json.loads((ROOT/'benchmark/manifest_v6.json').read_text())
  for v in manifest['variants']:
   if v['split']=='confirmatory' and v['family'] not in ('G15','G35'):
    assert sha(ROOT/v['path'])==hashlib.sha256(orig.read(v['path'])).hexdigest(), 'old reviewer case changed: '+v['path']
 confirm={f['id'] for f in json.loads((ROOT/'benchmark/gold/families.json').read_text())['families'] if f['split']=='confirmatory'}
 got={r['family'] for r in rows if r['family'] in confirm}
 assert got==confirm,'missing families in review sheet'
 for r in rows:
  if r['family'] not in confirm:continue
  if r['family'] in ('G15','G35'):
   expected_v='RATIFIED' if r['family']=='G15' else 'RATIFIED_WITH_RESSALVAS'
   assert r['verdict']==expected_v,f"delta not ratified with original judgment {r['family']}"
  else:
   assert r['verdict']=='PRIOR_REVIEWED_WITH_RESSALVAS',f"prior review proof missing {r['family']}"
  assert r['semantic_gold_correct']=='YES',f"semantic gold not approved {r['family']}"
  assert r['fhir_structural_expectation_correct']=='YES',f"FHIR expectation not approved {r['family']}"
  assert r['refusal_correct'] in (('YES',) if r['expected_decision']=='reject' else ('N/A',)),f"refusal mismatch {r['family']}"
 assert (ROOT/'benchmark/inputs/G35/neutral.json').read_text(encoding='utf8').find('synthetic-control-35')==-1,'G35 marker still present'
 assert {r['family'] for r in rows if r['split']=='confirmatory' and r['expected_decision']=='reject'}=={'G33','G34','G36'},'outdated refusal classification'
 return {'state':'RATIFIED_WITH_RESSALVAS','confirmatory_families':len(confirm),'reviewer_id':att['reviewer_id'],
   'limitation':'Partially unblinded original review; qualifications/independence based on researcher report, not independent certification. G35 neutral post-review metadata-only correction; not expert-resigned.'}
if __name__=='__main__':
 try:print(json.dumps(check(),ensure_ascii=False))
 except Exception as exc:print('BLOCKED:',str(exc),file=sys.stderr);sys.exit(3)

"""Create the expert review form. Never grant approvals automatically."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
families=json.loads((ROOT/'benchmark/gold/families.json').read_text())['families']
cols=['family','split','scenario','source_occurrences','expected_decision','expected_reasons','mutation_kind','mutation_operation','semantic_gold_correct','fhir_structural_expectation_correct','refusal_correct','verdict','reviewer_notes']
with (ROOT/'review/decisions.csv').open('w',newline='',encoding='utf-8-sig') as fh:
 w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
 for f in families:
  mutation=f['mutation'] or {}
  w.writerow(dict(family=f['id'],split=f['split'],scenario=f['scenario'],source_occurrences=len(f['exams']),
   expected_decision=f['expected_decision'],expected_reasons=';'.join(f['expected_rejection_reasons']),
   mutation_kind=mutation.get('kind','n/a'),mutation_operation=mutation.get('operation','n/a'),
   semantic_gold_correct='PENDING',fhir_structural_expectation_correct='PENDING',
   refusal_correct='PENDING' if f['expected_decision']=='reject' else 'N/A',
   verdict='PENDING',reviewer_notes=''))
(ROOT/'review/attestation.json').write_text(json.dumps({'status':'PENDING','reviewer_id':'PENDING','qualification_summary':'PENDING',
 'review_date':'PENDING','gold_sha256':'PENDING','decisions_sha256':'PENDING','independent_of_authoring':'PENDING',
 'adjudication_notes':'PENDING','consent_to_use_pseudonym_in_paper':False},indent=2,ensure_ascii=False)+'\n')
print('Created 36 review forms. Nothing approved.')

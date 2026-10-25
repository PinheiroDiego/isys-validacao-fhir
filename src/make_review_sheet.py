import csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
entries=json.loads((root/'benchmark/gold/families.json').read_text())['families']
path=root/'benchmark/gold/review_protocol.csv'
with path.open('w',newline='',encoding='utf-8-sig') as out:
 wr=csv.writer(out,delimiter=';')
 wr.writerow(['familia','particao','situacao','exames','mutacao','julgamento_A_corretude','julgamento_semantico_mutacao','evidencia/axioma FHIR','parecer_revisor','adjudicacao'])
 for f in entries:
  wr.writerow([f['id'],f['split'],f['topic'],len(f['exams']), (f.get('variant_mutation') or {}).get('operation',''), 'PENDENTE','PENDENTE','PENDENTE','PENDENTE','PENDENTE'])
print(path)

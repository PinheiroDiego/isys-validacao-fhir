"""Pre-specified synthetic source families. NOT sampled from patients.
Each case is deliberately authored as one cluster. No V4/V5 Fxx family is imported.
No statistics on held-out G11-G36 are generated during preparation.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def E(name,value=None,datatype=None,date=None,unit=None,id='x1',evolution='e1',**kw):
 x={'id':id,'evolution':evolution,'name':name}
 if value is not None:x.update(value=str(value),datatype=datatype or 'string')
 if date is not None:x['date']=date
 if unit is not None:x['unit']=unit
 x.update(kw);return x

def C(n,label,exams,kind=None,op=None,patients=None,evolutions=None,reasons=None):
 assert ((kind is None and reasons) or (kind in ('semantic','structural') and op))
 return {'id':f'G{n:02d}', 'split':'development' if n<=10 else 'confirmatory',
  'scenario':label,'patients':patients if patients is not None else ['p1'],
  'evolutions':evolutions if evolutions is not None else [{'id':'e1','patients':['p1']}],
  'exams':exams,'expected_decision':'reject' if reasons else 'emit',
  'expected_rejection_reasons':reasons or [],
  'mutation':None if reasons else {'kind':kind,'operation':op}}

FAMILIES=[
 C(1,'LDH: diferença numérica pequena',[E('LDH','184','integer','2026-04-18','U/L')],'semantic','numeric_near'),
 C(2,'Fosfatase alcalina: ausência de data não significa data presumida',[E('Fosfatase alcalina','95','integer')],'semantic','invent_date'),
 C(3,'Albumina: unidade literal explícita',[E('Albumina','3.75','decimal','2026-05-08','g/dL')],'semantic','change_unit'),
 C(4,'Radiografia: alteração de texto por negação',[E('Radiografia de tórax','sem alterações','string','2026-04')],'semantic','flip_negation'),
 C(5,'Amilase: status obrigatório',[E('Amilase','76','integer','2026-01-09')],'structural','missing_status'),
 C(6,'AST: código de observação obrigatório',[E('AST','48','integer','2026-02-12')],'structural','missing_code'),
 C(7,'Cálcio: status inválido',[E('Cálcio total','9.1','decimal','2026-04-10','mg/dL')],'structural','invalid_status'),
 C(8,'Urina: duplicação com nova identidade FHIR',[E('Urina tipo I','sem anormalidades','string','2026-06')],'semantic','duplicate_new_identity'),
 C(9,'Recusa: evolução sem paciente',[E('Potássio','4.3','decimal')],reasons=['NO_PATIENT_LINK'],evolutions=[{'id':'e1','patients':[]}]),
 C(10,'Recusa: dois resultados para o mesmo exame',[E('Sódio','140','integer',extra_results=[{'value':'141','datatype':'integer'}])],reasons=['MULTIPLE_RESULT']),
 C(11,'Dois pacientes: troca de referência válida',[E('ALT','41','integer','2026-01-23',id='x1',evolution='e1'),E('GGT','33','integer','2026-01-23',id='x2',evolution='e2')],'semantic','wrong_existing_patient',patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1']},{'id':'e2','patients':['p2']}]),
 C(12,'Troca de valores entre exames do mesmo paciente',[E('Ferro sérico','69','integer','2026-02-07',id='x1'),E('Transferrina','203','integer','2026-02-07',id='x2')],'semantic','swap_numeric_values'),
 C(13,'Exames repetidos: perda da segunda ocorrência',[E('Troponina','0.13','decimal','2026-01-14',id='x1'),E('Troponina','0.19','decimal','2026-01-15',id='x2')],'semantic','remove_second_occurrence'),
 C(14,'Data completa convertida para ano sem fundamento',[E('Lactato','1.4','decimal','2026-07-07','mmol/L')],'semantic','reduce_date_precision'),
 C(15,'Exame sem resultado: resultado alucinado',[E('Proteína total',date='2026-03-11')],'semantic','invent_numeric_value'),
 C(16,'Urocultura: polaridade do texto',[E('Urocultura','sem crescimento','string','2026-05-12')],'semantic','flip_negation'),
 C(17,'Duplicação válida de conteúdo clínico com novo id e fullUrl',[E('Creatina quinase','148','integer','2026-03-09','U/L')],'semantic','duplicate_new_identity'),
 C(18,'Proteína C reativa: troca apenas da unidade',[E('Proteína C reativa','4.2','decimal','2026-05-06','mg/L')],'semantic','change_unit'),
 C(19,'Data apenas mensal: enriquecimento indevido de precisão',[E('CA 125','37','integer','2026-02')],'semantic','increase_date_precision'),
 C(20,'Data conhecida: deslocamento por um dia',[E('Procalcitonina','0.25','decimal','2026-07-10','ng/mL')],'semantic','shift_day'),
 C(21,'Identidade do exame alterada, preservando valor',[E('Leucócitos','5400','integer','2026-03-25','/mm3')],'semantic','rename_exam'),
 C(22,'Unidade ausente: unidade indevidamente acrescentada',[E('Ferritina','128','integer','2026-01-12')],'semantic','invent_unit'),
 C(23,'Pacientes distintos, mesmo nome de exame',[E('Glicose','89','integer','2026-06-19',id='x1',evolution='e1'),E('Glicose','111','integer','2026-06-19',id='x2',evolution='e2')],'semantic','wrong_existing_patient',patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1']},{'id':'e2','patients':['p2']}]),
 C(24,'Troca de datas de duas ocorrências de exame',[E('CA 19-9','12','integer','2026-01-03',id='x1'),E('CA 19-9','19','integer','2026-02-14',id='x2')],'semantic','swap_dates'),
 C(25,'Valor numérico tem tipo inválido',[E('Ureia','21','integer','2026-04-16')],'structural','invalid_numeric_lexeme'),
 C(26,'Elemento desconhecido em Observation',[E('Plaquetas','215000','integer','2026-04-17')],'structural','unknown_element'),
 C(27,'fullUrl duplicado em Bundle',[E('Hemoglobina glicada','6.2','decimal','2026-02-20','%')],'structural','duplicate_fullurl'),
 C(28,'Recurso com resourceType inválido',[E('Velocidade de hemossedimentação','21','integer','2026-05-04')],'structural','invalid_resource_type'),
 C(29,'Remoção de code obrigatório',[E('CK-MB','2.5','decimal','2026-05-08')],'structural','missing_code'),
 C(30,'Data calendário inválida em FHIR',[E('Cortisol','8.4','decimal','2026-01-19')],'structural','invalid_fhir_date'),
 C(31,'Múltiplos value[x] simultâneos',[E('Ácido úrico','4.8','decimal','2026-05-28','mg/dL')],'structural','duplicate_value_choice'),
 C(32,'Status vazio',[E('Reticulócitos','1.2','decimal','2026-03-07','%')],'structural','empty_status'),
 C(33,'Recusa: evolução ligada a dois pacientes',[E('Bilirrubina','1.8','decimal')],reasons=['MULTIPLE_PATIENT_LINKS'],patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1','p2']}]),
 C(34,'Recusa: data impossível de calendário na origem',[E('Vitamina B12','420','integer','2026-02-31')],reasons=['AMBIGUOUS_OR_INVALID_DATE']),
 C(35,'Recusa: unidade informada sem valor numérico',[E('Fósforo',date='2026-05-03',unit='mg/dL')],reasons=['UNIT_WITHOUT_NUMERIC_VALUE']),
 C(36,'Recusa: nome do exame ausente',[E(None,'3','integer','2026-02')],reasons=['MISSING_EXAM_NAME']),
]
assert len(FAMILIES)==36 and len({f['id'] for f in FAMILIES})==36
if __name__=='__main__':
 out=ROOT/'benchmark/gold/families.json'
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({'spec':'ISYS-V6-CANDIDATE-GOLD-1','status':'UNREVIEWED_EXTERNALLY','authoring':'AI-assisted design, manually specified independent of converter output','family_unit':'one synthetically authored scenario and all its variants','holdout':'G11-G36; do not run confirmatory scores before specialist adjudication', 'families':FAMILIES},ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 print(out,len(FAMILIES))

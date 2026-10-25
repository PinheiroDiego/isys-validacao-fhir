"""Design-time fixtures authored as explicit templates; NOT a statistical sample.
Run only to reproduce golden cases; definitions frozen in gold/families.json.
"""
import json
from pathlib import Path

def E(name, value=None, datatype=None, date=None, unit=None, eid='x1', evolution='e1', **extras):
 d={'id':eid,'evolution':evolution,'name':name}
 if value is not None:d.update(value=str(value),datatype=datatype or 'string')
 if date is not None:d['date']=date
 if unit is not None:d['unit']=unit
 d.update(extras);return d

def C(i,topic,exams,mutation=None,patients=None,evolutions=None,expected_reasons=None):
 return {'id':f'F{i:02d}','split':'development' if i<=8 else 'evaluation','topic':topic,
         'patients':patients or ['p1'], 'evolutions':evolutions or [{'id':'e1','patients':['p1']}],
         'exams':exams,'variant_mutation':mutation,
         'expected_decision':'reject' if expected_reasons else 'emit',
         'expected_rejection_reasons':expected_reasons or []}

families=[
 C(1,'decimal com escala e unidade explícita',[E('CEA','25.20','decimal','2026-03-12','ng/mL')],{'kind':'semantic','operation':'change_numeric_value'}),
 C(2,'resultado textual e data mensal',[E('Ultrassom','sem achados','string','2026-03')],{'kind':'semantic','operation':'change_text_result'}),
 C(3,'ausência de resultado não é resultado negativo',[E('PSA',date='2026-03-15')],{'kind':'semantic','operation':'invent_result'}),
 C(4,'data anual e precisão preservada',[E('Hemograma','8','integer','2026')],{'kind':'semantic','operation':'change_exam_date'}),
 C(5,'unidade textual sem inferência UCUM',[E('Hemoglobina','11.40','decimal','2026-02-28','g/dL')],{'kind':'semantic','operation':'change_unit'}),
 C(6,'resultados de exames distintos',[E('PSA','2.1','decimal','2026-04-05',eid='x1'),E('TSH','6.8','decimal','2026-04-05',eid='x2')],{'kind':'semantic','operation':'swap_values'}),
 C(7,'repetição legítima do mesmo nome de exame',[E('CEA','1.2','decimal','2026-02-01',eid='x1'),E('CEA','2.4','decimal','2026-03-01',eid='x2')],{'kind':'semantic','operation':'drop_observation'}),
 C(8,'exame sem data informada',[E('Ferritina','128','integer')],{'kind':'semantic','operation':'invent_exam_date'}),
 C(9,'relação paciente trocada por paciente existente',[E('Glicemia','92','integer','2026-03-19',eid='x1',evolution='e1'),E('Ureia','25','integer','2026-03-19',eid='x2',evolution='e2')],{'kind':'semantic','operation':'reassign_patient'},patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1']},{'id':'e2','patients':['p2']}]),
 C(10,'ocorrência extra com nova identidade formal',[E('Calcitonina','3.4','decimal','2026-03-20')],{'kind':'semantic','operation':'duplicate_new_identity'}),
 C(11,'nome do exame alterado mantendo valor',[E('Mamografia','sem alterações','string','2026-05')],{'kind':'semantic','operation':'change_exam_name'}),
 C(12,'precisão do mês artificialmente aumentada',[E('Vitamina D','28.0','decimal','2026-02','ng/mL')],{'kind':'semantic','operation':'increase_date_precision'}),
 C(13,'resultado omitido num registro que o informava',[E('Hemoglobina','12','integer','2026-01-21','g/dL')],{'kind':'semantic','operation':'drop_result'}),
 C(14,'resultados trocados dentro do mesmo paciente',[E('CEA','4.5','decimal','2026-06-01',eid='x1'),E('TSH','0.7','decimal','2026-06-01',eid='x2')],{'kind':'semantic','operation':'swap_values'}),
 C(15,'pacientes distintos com resultados textuais',[E('Biópsia','negativo','string','2026-01-09',eid='x1',evolution='e1'),E('Biópsia','positivo','string','2026-01-10',eid='x2',evolution='e2')],{'kind':'semantic','operation':'reassign_patient'},patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1']},{'id':'e2','patients':['p2']}]),
 C(16,'valor com precisão decimal e data de dia',[E('Creatinina','0.85','decimal','2026-03-11','mg/dL')],{'kind':'semantic','operation':'change_numeric_value'}),
 C(17,'controle negativo: status ausente',[E('TSH','3','integer','2026-03-18')],{'kind':'structural','operation':'remove_status'}),
 C(18,'controle negativo: fullUrl repetido',[E('Ferritina','27','integer','2026-03-19')],{'kind':'structural','operation':'duplicate_same_fullurl'}),
 C(19,'controle negativo: code ausente',[E('Ultrassom','normal','string','2026-03-20')],{'kind':'structural','operation':'remove_code'}),
 C(20,'controle negativo: status fora do conjunto de valores',[E('CEA','8','integer','2026-03-21')],{'kind':'structural','operation':'invalid_status'}),
 C(21,'recusa por ausência do vínculo evolucao-paciente',[E('TSH','4','integer','2026-03-10')],patients=['p1'],evolutions=[{'id':'e1','patients':[]}],expected_reasons=['NO_PATIENT_LINK']),
 C(22,'recusa por múltiplos pacientes possíveis',[E('CEA','3','integer','2026-03-10')],patients=['p1','p2'],evolutions=[{'id':'e1','patients':['p1','p2']}],expected_reasons=['MULTIPLE_PATIENT_LINKS']),
 C(23,'recusa por ausência de identificação do exame',[E(None,'5','integer','2026-03-10')],expected_reasons=['MISSING_EXAM_NAME']),
 C(24,'recusa por data do calendário impossível',[E('PSA','3','integer','2026-02-30')],expected_reasons=['AMBIGUOUS_OR_INVALID_DATE']),
 C(25,'recusa por datatype não suportado',[E('Hemoglobina','true','boolean','2026-03-10')],expected_reasons=['UNSUPPORTED_RESULT_DATATYPE']),
 C(26,'recusa por múltiplos valores de resultado',[E('CEA','4','integer','2026-03-10',extra_results=[{'value':'5','datatype':'integer'}])],expected_reasons=['MULTIPLE_RESULT']),
]

if __name__=='__main__':
 root=Path(__file__).resolve().parents[1]
 path=root/'benchmark/gold/families.json';path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({'spec':'ISYS-V4-GOLD-1','design':'purposefully selected scenarios; not random independent samples',
 'author':'AI-assisted synthetic design; external subject-matter review pending',
 'holdout_policy':'F09-F26 not used to revise converter after freeze; no holdout score until independent review',
 'families':families},ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 print('Wrote',path, len(families))

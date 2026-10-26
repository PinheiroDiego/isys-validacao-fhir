"""V7 — especificação determinística dos cenários (apêndice A do pré-registro).

Nenhuma função deste módulo é executada com a SEMENTE_V7 antes do commit de
congelamento. Os testes usam sementes alternativas apenas para verificar as
restrições de aplicabilidade, sem calcular os valores da V7.

Algoritmo de seleção: SHA-256 em modo contador (sem PRNG da biblioteca padrão),
independente de versão do Python. Para uma lista L e rótulos r1..rk:
    h = int(SHA256(UTF-8(semente + '|' + r1 + '|' + ... + '|' + rk)), 16)
    escolha = L[h mod len(L)]
Para dois elementos distintos (pick2):
    i = h('a') mod n ; j = (i + 1 + (h('b') mod (n-1))) mod n
"""
from __future__ import annotations
import hashlib, unicodedata

SEMENTE_V7 = 'ISYS-V7-2026-10-25-PREREGISTRO'
SPLIT = 'v7'

# Listas fixadas antes da geração. Nomes acentuados garantem que N4 (NFD) altere
# os bytes de code.text; nomes sem acento são usados onde N4 é não aplicável.
EXAMES_NUMERICOS_ACENTUADOS = [
    'Ácido úrico', 'Ácido fólico', 'Cálcio iônico', 'Fósforo', 'Potássio',
    'Sódio', 'Magnésio', 'Ferro sérico', 'Albumina sérica', 'Proteína total',
]
EXAMES_NUMERICOS_SEM_ACENTO = [
    'Ferritina', 'Creatinina', 'Ureia', 'Hemoglobina', 'Plaquetas', 'TSH', 'CEA', 'PSA',
]
EXAMES_TEXTUAIS_ACENTUADOS = [
    'Citologia oncótica', 'Biópsia de pele', 'Pesquisa de células neoplásicas',
]
# Nenhum valor coincide com as saídas do operador flip_negation da V6.1
# ('com achados' / 'com crescimento'), garantindo que a mutação altere o fato.
RESULTADOS_TEXTUAIS = ['sem alterações', 'sem crescimento', 'negativo para malignidade']
# Decimais sem zeros finais (precisão inequívoca em FHIR).
VALORES_DECIMAIS = ['3.4', '4.2', '5.7', '6.1', '7.3', '8.8', '9.4', '12.6']
# Nenhuma unidade coincide com a saída de change_unit ('outra-unidade').
UNIDADES = ['mg/dL', 'mmol/L', 'g/dL', 'U/L', 'ng/mL']
# Datas completas de 2026-01 a 2026-06; nenhuma coincide com a saída de shift_day ('2026-07-11').
DATAS = [
    '2026-01-14', '2026-01-27', '2026-02-09', '2026-02-23', '2026-03-10', '2026-03-24',
    '2026-04-07', '2026-04-21', '2026-05-05', '2026-05-19', '2026-06-02', '2026-06-16',
]
DATA_INVALIDA_H11 = '2026-02-30'  # fixa, não sorteada: data de calendário impossível

# Saídas fixas dos operadores de mutação da V6.1 (src/build_v6.py, congelado).
SAIDAS_MUTACAO_V61 = {
    'change_unit': 'outra-unidade', 'shift_day': '2026-07-11', 'rename_exam': 'Neutrófilos',
    'flip_negation': ('com achados', 'com crescimento'),
}


def _h(seed: str, *labels: str) -> int:
    return int(hashlib.sha256('|'.join((seed,) + labels).encode('utf-8')).hexdigest(), 16)


def pick(seed, lst, *labels):
    return lst[_h(seed, *labels) % len(lst)]


def pick2(seed, lst, *labels):
    n = len(lst)
    i = _h(seed, *labels, 'a') % n
    j = (i + 1 + (_h(seed, *labels, 'b') % (n - 1))) % n
    return lst[i], lst[j]


def tem_acento(s: str) -> bool:
    return unicodedata.normalize('NFD', s) != s


def build_families(seed: str = SEMENTE_V7):
    """Retorna as 11 famílias H01–H11 no formato do gold V6.1 (mesmos campos)."""
    def num(fid, x, name_list, with_unit=False):
        e = {'id': x, 'evolution': 'e1', 'datatype': 'decimal',
             'name': pick(seed, name_list, fid, x, 'nome'),
             'value': pick(seed, VALORES_DECIMAIS, fid, x, 'valor'),
             'date': pick(seed, DATAS, fid, x, 'data')}
        if with_unit:
            e['unit'] = pick(seed, UNIDADES, fid, x, 'unidade')
        return e

    def fam(fid, scenario, patients, evolutions, exams, op=None, reject=None):
        return {'id': fid, 'split': SPLIT, 'scenario': scenario, 'patients': patients,
                'evolutions': evolutions, 'exams': exams,
                'expected_decision': 'reject' if reject else 'emit',
                'expected_rejection_reasons': [reject] if reject else [],
                'mutation': {'kind': 'semantic', 'operation': op} if op else None}

    one = [{'id': 'e1', 'patients': ['p1']}]
    F = []
    # H01 — dois pacientes, um exame numérico cada
    n1, n2 = pick2(seed, EXAMES_NUMERICOS_ACENTUADOS, 'H01', 'nomes')
    x1 = num('H01', 'x1', EXAMES_NUMERICOS_ACENTUADOS); x1['name'] = n1
    x2 = num('H01', 'x2', EXAMES_NUMERICOS_ACENTUADOS); x2['name'] = n2; x2['evolution'] = 'e2'
    F.append(fam('H01', 'Dois pacientes, um exame numérico cada', ['p1', 'p2'],
                 [{'id': 'e1', 'patients': ['p1']}, {'id': 'e2', 'patients': ['p2']}],
                 [x1, x2], 'wrong_existing_patient'))
    # H02 — mesmo paciente, dois exames, nomes e valores distintos
    n1, n2 = pick2(seed, EXAMES_NUMERICOS_ACENTUADOS, 'H02', 'nomes')
    v1, v2 = pick2(seed, VALORES_DECIMAIS, 'H02', 'valores')
    x1 = num('H02', 'x1', EXAMES_NUMERICOS_ACENTUADOS); x1.update(name=n1, value=v1)
    x2 = num('H02', 'x2', EXAMES_NUMERICOS_ACENTUADOS); x2.update(name=n2, value=v2)
    F.append(fam('H02', 'Mesmo paciente, dois exames numéricos', ['p1'], one, [x1, x2], 'swap_numeric_values'))
    F.append(fam('H03', 'Exame numérico com unidade', ['p1'], one,
                 [num('H03', 'x1', EXAMES_NUMERICOS_ACENTUADOS, with_unit=True)], 'change_unit'))
    F.append(fam('H04', 'Exame numérico com data completa (sem acento)', ['p1'], one,
                 [num('H04', 'x1', EXAMES_NUMERICOS_SEM_ACENTO)], 'shift_day'))
    F.append(fam('H05', 'Exame com nome acentuado', ['p1'], one,
                 [num('H05', 'x1', EXAMES_NUMERICOS_ACENTUADOS)], 'rename_exam'))
    x = num('H06', 'x1', EXAMES_NUMERICOS_ACENTUADOS)
    for k in ('value', 'datatype'):
        x.pop(k)
    F.append(fam('H06', 'Exame sem resultado (dataAbsentReason=unknown)', ['p1'], one, [x], 'invent_numeric_value'))
    F.append(fam('H07', 'Exame numérico (sem acento)', ['p1'], one,
                 [num('H07', 'x1', EXAMES_NUMERICOS_SEM_ACENTO)], 'duplicate_new_identity'))
    F.append(fam('H08', 'Resultado textual', ['p1'], one,
                 [{'id': 'x1', 'evolution': 'e1', 'datatype': 'string',
                   'name': pick(seed, EXAMES_TEXTUAIS_ACENTUADOS, 'H08', 'x1', 'nome'),
                   'value': pick(seed, RESULTADOS_TEXTUAIS, 'H08', 'x1', 'valor'),
                   'date': pick(seed, DATAS, 'H08', 'x1', 'data')}], 'flip_negation'))
    # Recusas
    F.append(fam('H09', 'Recusa: evolução sem vínculo com paciente', ['p1'],
                 [{'id': 'e1', 'patients': []}], [num('H09', 'x1', EXAMES_NUMERICOS_ACENTUADOS)],
                 reject='NO_PATIENT_LINK'))
    x = num('H10', 'x1', EXAMES_NUMERICOS_ACENTUADOS)
    v1, v2 = pick2(seed, VALORES_DECIMAIS, 'H10', 'valores')
    x.update(value=v1, extra_results=[{'datatype': 'decimal', 'value': v2}])
    F.append(fam('H10', 'Recusa: dois resultados para a mesma ocorrência', ['p1'], one, [x],
                 reject='MULTIPLE_RESULT'))
    x = num('H11', 'x1', EXAMES_NUMERICOS_ACENTUADOS); x['date'] = DATA_INVALIDA_H11
    F.append(fam('H11', 'Recusa: data de calendário impossível', ['p1'], one, [x],
                 reject='AMBIGUOUS_OR_INVALID_DATE'))
    check_constraints(F)
    return F


N4_APLICAVEL_PREVISTO = {'H01', 'H02', 'H03', 'H05', 'H06', 'H08'}


def check_constraints(F):
    """Regras de aplicabilidade (seção 4 do pré-registro). Falha fechada."""
    by = {f['id']: f for f in F}
    assert [f['id'] for f in F] == [f'H{i:02d}' for i in range(1, 12)]
    assert len(by['H01']['patients']) == 2 and by['H01']['exams'][0]['name'] != by['H01']['exams'][1]['name']
    a, b = by['H02']['exams']
    assert a['value'] != b['value'] and a['name'] != b['name']
    assert by['H03']['exams'][0]['unit'] != SAIDAS_MUTACAO_V61['change_unit']
    assert by['H04']['exams'][0]['date'] != SAIDAS_MUTACAO_V61['shift_day']
    assert by['H05']['exams'][0]['name'] != SAIDAS_MUTACAO_V61['rename_exam']
    assert 'value' not in by['H06']['exams'][0] and 'unit' not in by['H06']['exams'][0]
    assert by['H08']['exams'][0]['value'] not in SAIDAS_MUTACAO_V61['flip_negation']
    v = by['H10']['exams'][0]
    assert v['value'] != v['extra_results'][0]['value']
    for fid in N4_APLICAVEL_PREVISTO:
        assert any(tem_acento(x['name']) for x in by[fid]['exams']), fid
    for fid in ('H04', 'H07'):
        assert not any(tem_acento(x['name']) for x in by[fid]['exams']), fid
    return True

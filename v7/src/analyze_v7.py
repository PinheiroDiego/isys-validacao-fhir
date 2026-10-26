"""V7 — análise conforme o pré-registro (apêndice E).

Usa SEM MODIFICAÇÃO o comparador da V6.1: semantic_oracle.compare e
competency_v4.compare_queries. C = B OU oráculo OU Q01–Q05 (definição V6.1);
o componente que disparou cada alarme é registrado separadamente.
Unidade de análise: família. Sem percentuais agregados, sem reamostragem, sem inferência.
"""
from __future__ import annotations
import sys, json, csv, hashlib
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_oracle import compare            # congelado (V6.1)
from competency_v4 import compare_queries      # congelado (V6.1)
from verify_v7 import verify

PREVISAO_C = {'N1': 'SEM_ALARME', 'N2': 'ALARME', 'N3': 'ALARME', 'N4': 'ALARME'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads((ROOT / p).read_text(encoding='utf8'))


def read_csv(p):
    with (ROOT / p).open(encoding='utf-8-sig', newline='') as fh:
        return {r[next(iter(r))]: r for r in csv.DictReader(fh)}


def sanity_summary(mutacoes):
    """R3: erros de análise formam categoria própria; nunca são contados como ausência de detecção."""
    erro = [x['family'] for x in mutacoes if x['analysis_state'] != 'OK']
    invalidas = [x['family'] for x in mutacoes if x['analysis_state'] == 'OK' and not x['formalmente_valida']]
    nao_interp = [x['family'] for x in mutacoes if x['analysis_state'] == 'OK' and x['formalmente_valida'] and not x['interpretavel']]
    elegiveis = [x for x in mutacoes if x['analysis_state'] == 'OK' and x['formalmente_valida'] and x['interpretavel']]
    return {'casos': mutacoes, 'denominador_semantico_computado': len(elegiveis),
            'B_detectou': sum(bool(x['B_alert']) for x in elegiveis), 'C_detectou': sum(bool(x['C_alert']) for x in elegiveis),
            'erro_de_analise': erro, 'mutacao_formalmente_invalida': invalidas, 'nao_interpretavel_baseline': nao_interp}


def analyze():
    review_state = verify('reviewed')
    m = load('v7/benchmark/manifest_v7.json')
    off = load('v7/outputs/official/execution-summary.json')
    if off.get('state') != 'COMPLETED' or len(off['results']) != 51:
        raise RuntimeError('Execução HL7 oficial V7 incompleta')
    byid = {r['id']: r for r in off['results']}
    for oid, v in m['inputs'].items():
        o = byid[oid]
        assert o['state'] == 'VALIDATED' and o['input_sha256'] == v['sha256']
        assert sha(ROOT / f'v7/outputs/official/{oid}.outcome.json') == o['outcome_sha256'], 'outcome alterado ' + oid
    mapa = {r['opaque_id']: r for r in load('v7/private/opaque_map.json')}
    gold = {f['id']: f for f in load('v7/private/gold_v7.json')['families']}
    recusas = load('v7/private/refusal_records.json')
    att = load('v7/review/attestation_v7.json')
    verdict_ctrl, verdict_ref, decoys = {}, {}, []
    if att['status'] == 'REVIEW_RECEIVED':
        pares = read_csv('v7/review/FICHA_PARES_V7_RESPOSTA.csv')
        rec = read_csv('v7/review/FICHA_RECUSAS_V7_RESPOSTA.csv')
        for k in load('v7/private/review_key.json'):
            if 'pair' in k:
                ver = pares[k['pair']]['veredito'].strip()
                if k['category'] == 'mutation':
                    decoys.append({'pair': k['pair'], 'family': k['family'], 'veredito': ver})
                else:
                    verdict_ctrl[(k['family'], k['category'])] = ver
            else:
                verdict_ref[k['family']] = rec[k['refusal']]['veredito'].strip()

    rows = []
    for oid, r in sorted(mapa.items()):
        o = byid[oid]
        row = {'opaque_id': oid, 'family': r['family'], 'variant': r['variant'], 'expected_class': r['expected_class'],
               'operation': r.get('operation'), 'n4_fields_changed': r.get('n4_fields_changed'),
               'B_errors': o['errors'], 'B_warnings': o['warnings'], 'B_alert': o['errors'] > 0}
        if r['variant'] != 'refusal':
            b = json.loads((ROOT / m['inputs'][oid]['path']).read_text(encoding='utf8'), parse_float=Decimal)
            try:
                findings = compare(gold[r['family']], b)
                q = compare_queries(gold[r['family']], b)['Q06']['mismatched_queries']
                row.update(oracle_codes=[x['field'] for x in findings], Q_mismatches=q,
                           oracle_alert=bool(findings), Q_alert=bool(q), analysis_state='OK')
            except Exception as exc:  # registrado, nunca silenciado
                row.update(oracle_codes=None, Q_mismatches=None, oracle_alert=None, Q_alert=None,
                           analysis_state='ANALYSIS_ERROR: ' + type(exc).__name__ + ': ' + str(exc))
            row['C_alert'] = (row['B_alert'] or bool(row['oracle_alert']) or bool(row['Q_alert'])
                              if row['analysis_state'] == 'OK' else None)
        rows.append(row)

    fam = {}
    for row in rows:
        fam.setdefault(row['family'], {})[row['variant']] = row
    baseline_ok = {f: v['baseline']['B_errors'] == 0 for f, v in fam.items() if 'baseline' in v}

    controles = {}
    for t in ('N1', 'N2', 'N3', 'N4'):
        res = {'previsao_C': PREVISAO_C[t], 'familias': [], 'nao_aplicavel': [], 'nao_interpretavel_baseline': [],
               'controle_invalido_HL7': [], 'excluido_pela_revisao': [], 'erro_de_analise': []}
        for f, v in sorted(fam.items()):
            if t not in v:
                continue
            row = v[t]
            if row['expected_class'] == 'n4_not_applicable':
                res['nao_aplicavel'].append({'family': f, 'B_alert': row['B_alert'], 'C_alert': row['C_alert']}); continue
            if not baseline_ok[f]:
                res['nao_interpretavel_baseline'].append(f); continue
            if row['B_alert']:
                res['controle_invalido_HL7'].append({'family': f, 'B_errors': row['B_errors']}); continue
            ver = verdict_ctrl.get((f, t), 'SEM_REVISAO')
            if att['status'] == 'REVIEW_RECEIVED' and ver != 'EQUIVALENTE':
                res['excluido_pela_revisao'].append({'family': f, 'veredito': ver, 'C_alert': row['C_alert']}); continue
            if row['analysis_state'] != 'OK':
                res['erro_de_analise'].append({'family': f, 'estado': row['analysis_state']}); continue
            res['familias'].append({'family': f, 'C_alert': row['C_alert'], 'oracle_alert': row['oracle_alert'],
                                    'Q_alert': row['Q_alert'], 'Q_mismatches': row['Q_mismatches'],
                                    'oracle_codes': row['oracle_codes'], 'veredito_revisao': ver})
        d = len(res['familias']); c = sum(x['C_alert'] for x in res['familias'])
        res['denominador_valido'] = d
        res['alarmes_C'] = c
        res['alarmes_somente_oraculo'] = sum(x['oracle_alert'] and not x['Q_alert'] for x in res['familias'])
        res['alarmes_somente_Q'] = sum(x['Q_alert'] and not x['oracle_alert'] for x in res['familias'])
        if d == 0:
            res['interpretacao'] = 'SEM_CONTROLES_VALIDOS'
        elif PREVISAO_C[t] == 'ALARME':
            res['interpretacao'] = 'PREVISAO_CONFIRMADA' if c == d else ('PREVISAO_NAO_CONFIRMADA' if c == 0 else 'CONFIRMACAO_PARCIAL')
        else:
            res['interpretacao'] = 'PREVISAO_CONFIRMADA' if c == 0 else ('PREVISAO_NAO_CONFIRMADA' if c == d else 'CONFIRMACAO_PARCIAL')
        controles[t] = res

    referencias = [{'family': f, 'B_errors': v['baseline']['B_errors'], 'C_alert': v['baseline']['C_alert'],
                    'analysis_state': v['baseline']['analysis_state']}
                   for f, v in sorted(fam.items()) if 'baseline' in v]
    mutacoes = []
    for f, v in sorted(fam.items()):
        if 'mutation' not in v:
            continue
        mrow = v['mutation']
        mutacoes.append({'family': f, 'operation': mrow['operation'], 'formalmente_valida': not mrow['B_alert'],
                         'B_alert': mrow['B_alert'], 'C_alert': mrow['C_alert'], 'oracle_alert': mrow['oracle_alert'],
                         'Q_alert': mrow['Q_alert'], 'interpretavel': baseline_ok[f],
                         'analysis_state': mrow['analysis_state']})
    sanidade = sanity_summary(mutacoes)
    recs = []
    for f, v in sorted(fam.items()):
        if 'refusal' in v:
            rr = v['refusal']
            recs.append({'family': f, 'B_errors': rr['B_errors'], 'B_warnings': rr['B_warnings'],
                         'motivos_registrados': sorted({m_ for x in recusas[f]['converter_rejections'] for m_ in x['reasons']}),
                         'veredito_revisao': verdict_ref.get(f, 'SEM_REVISAO')})
    out = {
        'benchmark_id': m['benchmark_id'], 'protocol_commit': m['protocol_commit'], 'review': review_state,
        'definicao_C': 'B OU oraculo(gold) OU Q01-Q05 (instrumento V6.1 congelado)',
        'H1_controles': controles,
        'referencias': referencias,
        'sanidade_mutacoes': sanidade,
        'H2_recusas': {'casos': recs, 'interpretacao': 'CONFIRMADA' if all(x['B_errors'] == 0 for x in recs) else 'NAO_CONFIRMADA'},
        'revisao_chamarizes_mutacao': decoys,
        'limites': ['Casos sintéticos direcionados a acoplamentos identificados previamente no código',
                    'Variantes dependentes dentro da família; sem inferência populacional',
                    'Perfil-base FHIR R4, -tx n/a', 'H3 transferida para V7.1'],
        'variantes': rows,
    }
    return out


if __name__ == '__main__':
    res = analyze()
    dst = ROOT / 'v7/outputs/analysis_v7.json'
    dst.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf8')
    print(json.dumps({k: res[k] for k in ('H2_recusas',)} | {'H1': {t: {k: v[k] for k in ('denominador_valido', 'alarmes_C', 'interpretacao')}
                                                                       for t, v in res['H1_controles'].items()}}, ensure_ascii=False))

"""V7 — operadores metamórficos N1–N4 e serialização de recusa (apêndice B).

Todos os operadores recebem um Bundle FHIR já produzido pelo conversor da V6.1
e devolvem uma cópia transformada. Nenhum operador acrescenta fatos clínicos,
códigos, terminologias ou proveniência que não estejam no Bundle de referência.
"""
from __future__ import annotations
import copy, hashlib, html, re, unicodedata

XHTML_NS = 'http://www.w3.org/1999/xhtml'
FHIR_ID_RE = re.compile(r'[A-Za-z0-9\-\.]{1,64}')
# N4 atua somente nestes campos de Observation (emenda 3): a nota de unidade
# sem resultado fica excluída porque o verificador a lê por padrão textual fixo.
N4_CAMPOS = ('code.text', 'valueString')


def _res(b, rtype):
    return [e for e in b.get('entry', []) if e.get('resource', {}).get('resourceType') == rtype]


def _fmt_value(o):
    if 'valueQuantity' in o:
        q = o['valueQuantity']
        return str(q.get('value')) + (' ' + q['unit'] if q.get('unit') else '')
    if 'valueString' in o:
        return o['valueString']
    if 'dataAbsentReason' in o:
        return 'ausente (motivo: desconhecido)'
    return 'não informado'


def n1_narrative(bundle):
    """N1: narrativa gerada (text.status=generated) a partir apenas dos campos estruturados."""
    b = copy.deepcopy(bundle)
    for e in b.get('entry', []):
        r = e['resource']
        if r['resourceType'] == 'Patient':
            linhas = [f"Paciente (identificador lógico: {r['id']})"]
        elif r['resourceType'] == 'Observation':
            linhas = [f"Exame: {r.get('code', {}).get('text', 'não informado')}",
                      f"Resultado: {_fmt_value(r)}"]
            if 'effectiveDateTime' in r:
                linhas.append(f"Data: {r['effectiveDateTime']}")
            linhas.append(f"Status: {r.get('status', 'não informado')}")
        else:
            raise ValueError('Tipo de recurso fora do escopo V7: ' + r['resourceType'])
        div = f'<div xmlns="{XHTML_NS}">' + ''.join(f'<p>{html.escape(x)}</p>' for x in linhas) + '</div>'
        r['text'] = {'status': 'generated', 'div': div}
    return b


def _novo_id(seed, rtype, old):
    nid = 'r' + hashlib.sha256(f'{seed}|N2|{rtype}|{old}'.encode('utf-8')).hexdigest()[:31]
    assert FHIR_ID_RE.fullmatch(nid)
    return nid


def n2_reidentify(bundle, seed):
    """N2: IDs lógicos opacos para Patient/Observation, com fullUrl e referências reconstruídos."""
    b = copy.deepcopy(bundle)
    mapa = {}
    for e in b.get('entry', []):
        r = e['resource']
        old = r['id']
        new = _novo_id(seed, r['resourceType'], old)
        mapa[(r['resourceType'], old)] = new
        r['id'] = new
        base, sep, tail = e['fullUrl'].rpartition('/')
        assert sep and tail == old, 'fullUrl não termina no id do recurso'
        e['fullUrl'] = base + '/' + new
    for e in _res(b, 'Observation'):
        ref = e['resource']['subject']['reference']
        assert ref.startswith('Patient/')
        e['resource']['subject']['reference'] = 'Patient/' + mapa[('Patient', ref.removeprefix('Patient/'))]
    assert len(set(mapa.values())) == len(mapa), 'colisão de ids'
    return b


def n3_absolute_reference(bundle):
    """N3: Observation.subject.reference passa a ser o fullUrl exato do Patient no Bundle."""
    b = copy.deepcopy(bundle)
    full = {e['resource']['id']: e['fullUrl'] for e in _res(b, 'Patient')}
    for e in _res(b, 'Observation'):
        ref = e['resource']['subject']['reference']
        pid = ref.removeprefix('Patient/')
        assert ref.startswith('Patient/') and pid in full, 'referência sem Patient correspondente'
        e['resource']['subject']['reference'] = full[pid]
    return b


def n4_unicode_nfd(bundle):
    """N4: NFC→NFD em Observation.code.text e Observation.valueString. Retorna (bundle, nº de campos alterados)."""
    b = copy.deepcopy(bundle)
    alterados = 0
    for e in _res(b, 'Observation'):
        r = e['resource']
        if 'text' in r.get('code', {}):
            novo = unicodedata.normalize('NFD', r['code']['text'])
            alterados += novo != r['code']['text']
            r['code']['text'] = novo
        if 'valueString' in r:
            novo = unicodedata.normalize('NFD', r['valueString'])
            alterados += novo != r['valueString']
            r['valueString'] = novo
    return b, alterados


def serialize_refusal(bundle):
    """Recusa: Bundle 'collection' sem a propriedade entry (forma da V5), nunca entry=[]."""
    b = copy.deepcopy(bundle)
    assert b.get('resourceType') == 'Bundle' and b.get('type') == 'collection'
    assert not b.get('entry'), 'Bundle de recusa não pode conter recursos'
    b.pop('entry', None)
    return b

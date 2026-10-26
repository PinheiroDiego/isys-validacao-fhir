"""V7 — verificação de integridade por fase (falha fechada). Revisão A1 (auditoria pré-commit).

protocol : pré-registro, apêndice, políticas Git e módulos congelados da V6.1 conferem com FREEZE_V7.json
generated: + manifesto V7, 51 entradas e kit de revisão (diretório e ZIP de entrega) conferem
reviewed : + arquivos privados, overlays e ZIP do kit obrigatórios; parecer completo e congelado (B1, B2)
Hashes sempre calculados sobre os bytes do arquivo, sem normalização de fim de linha (B3).
"""
from __future__ import annotations
import json, hashlib, sys, csv, io, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VEREDITOS_PAR = {'EQUIVALENTE', 'NAO_EQUIVALENTE', 'INCERTO'}
VEREDITOS_RECUSA = {'JUSTIFICADA', 'NAO_JUSTIFICADA', 'INCERTO'}
EXIGE_JUSTIFICATIVA = {'NAO_EQUIVALENTE', 'INCERTO', 'NAO_JUSTIFICADA'}
PARES_ESPERADOS, RECUSAS_ESPERADAS = 38, 3   # 30 controles aplicáveis + 8 chamarizes; H09–H11
KIT_ZIP = 'v7/review_kit_V7.zip'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _check(mapping, label, root=None):
    root = root or ROOT
    for name, dig in mapping.items():
        p = root / name
        assert p.is_file(), f'{label}: ausente {name}'
        assert sha(p) == dig, f'{label}: alterado {name}'


def parse_sheet(raw: bytes, id_col: str):
    """Lê a ficha a partir dos bytes recebidos (aceita BOM e CRLF sem alterar o arquivo)."""
    text = raw.decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(text, newline='')))
    assert rows, 'ficha vazia'
    assert list(rows[0].keys()) == [id_col, 'veredito', 'justificativa'], f'cabeçalho inválido: {list(rows[0].keys())}'
    return rows


def check_review_sheets(key, pair_rows, refusal_rows):
    """B1: completude e consistência das fichas da especialista contra a chave do kit."""
    exp_pairs = [k['pair'] for k in key if 'pair' in k]
    exp_refs = [k['refusal'] for k in key if 'refusal' in k]
    assert len(exp_pairs) == PARES_ESPERADOS and len(set(exp_pairs)) == PARES_ESPERADOS, 'chave do kit: pares'
    assert len(exp_refs) == RECUSAS_ESPERADAS and len(set(exp_refs)) == RECUSAS_ESPERADAS, 'chave do kit: recusas'
    for rows, col, expected, allowed, ok in ((pair_rows, 'par', exp_pairs, VEREDITOS_PAR, 'EQUIVALENTE'),
                                            (refusal_rows, 'recusa', exp_refs, VEREDITOS_RECUSA, 'JUSTIFICADA')):
        ids = [r[col].strip() for r in rows]
        assert len(ids) == len(set(ids)), f'IDs duplicados na ficha ({col})'
        assert set(ids) == set(expected), f'IDs divergentes ({col}): faltam {sorted(set(expected) - set(ids))}, sobram {sorted(set(ids) - set(expected))}'
        for r in rows:
            v = (r['veredito'] or '').strip()
            assert v in allowed, f'veredito inválido em {r[col]}: {v!r}'
            if v in EXIGE_JUSTIFICATIVA:
                assert (r['justificativa'] or '').strip(), f'justificativa obrigatória em {r[col]} ({v})'
    return {'pairs': len(pair_rows), 'refusals': len(refusal_rows)}


def check_kit_zip(zip_path, manifest):
    """B2: o ZIP entregue tem o hash registrado na geração e os membros conferem com os hashes do kit."""
    assert sha(zip_path) == manifest['review_kit_zip_sha256'], 'ZIP do kit diverge do registrado na geração'
    expected = {k.removeprefix('v7/review_kit/'): v for k, v in manifest['review_kit_sha256'].items()}
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if not n.endswith('/')]
        assert sorted(names) == sorted(expected), 'membros do ZIP do kit divergem do manifesto'
        for n in names:
            assert hashlib.sha256(z.read(n)).hexdigest() == expected[n], 'membro do kit alterado: ' + n
    return len(names)


def verify(phase='protocol', root=None):
    root = root or ROOT
    assert phase in ('protocol', 'generated', 'reviewed')
    fz = json.loads((root / 'v7/FREEZE_V7.json').read_text(encoding='utf8'))
    _check(fz['protocol_files'], 'protocolo', root)
    _check(fz['frozen_v61_modules'], 'módulo V6.1', root)
    out = {'phase': phase, 'protocol_files': len(fz['protocol_files']), 'frozen_v61_modules': len(fz['frozen_v61_modules'])}
    if phase == 'protocol':
        return out | {'state': 'PASS'}
    m = json.loads((root / 'v7/benchmark/manifest_v7.json').read_text(encoding='utf8'))
    assert m['freeze_sha256'] == sha(root / 'v7/FREEZE_V7.json'), 'FREEZE alterado após geração'
    assert m['source_ontology_original_sha256'] == fz['source_ontology_zip_sha256'], 'ontologia de origem divergente'
    assert len(m['inputs']) == 51
    _check({v['path']: v['sha256'] for v in m['inputs'].values()}, 'entrada V7', root)
    priv = {**m['private_sha256'], **m['overlays_sha256']}
    presentes = {k: v for k, v in priv.items() if (root / k).exists()}
    _check(presentes, 'privado/overlay', root)
    kit_presente = {k: v for k, v in m['review_kit_sha256'].items() if (root / k).exists()}
    _check(kit_presente, 'kit de revisão', root)
    if (root / KIT_ZIP).exists():
        check_kit_zip(root / KIT_ZIP, m)
    if phase == 'generated':
        return out | {'state': 'PASS', 'inputs': 51, 'private_present': len(presentes), 'kit_files_present': len(kit_presente)}
    _check(priv, 'privado/overlay (obrigatório após revisão)', root)
    assert (root / KIT_ZIP).exists(), 'ZIP do kit efetivamente entregue é obrigatório após a revisão'
    att = json.loads((root / 'v7/review/attestation_v7.json').read_text(encoding='utf8'))
    assert att['status'] in ('REVIEW_RECEIVED', 'NOT_PERFORMED'), 'estado do parecer inválido'
    assert att['manifest_v7_sha256'] == sha(root / 'v7/benchmark/manifest_v7.json'), 'parecer não referencia o manifesto gerado'
    assert att['generation_commit'] and att['generation_commit'] != m['protocol_commit'], 'commit de geração ausente'
    assert att['reviewer_saw_predictions_or_results'] is False
    if att['status'] == 'REVIEW_RECEIVED':
        assert att['kit_zip_sha256'] == m['review_kit_zip_sha256'], 'parecer não se refere ao kit gerado'
        assert att.get('kit_sent_date') and att.get('review_received_date'), 'datas de envio/recebimento ausentes'
        raws = {}
        for key, fname in (('pairs_csv_sha256', 'v7/review/FICHA_PARES_V7_RESPOSTA.csv'),
                           ('refusals_csv_sha256', 'v7/review/FICHA_RECUSAS_V7_RESPOSTA.csv')):
            raws[key] = (root / fname).read_bytes()
            assert hashlib.sha256(raws[key]).hexdigest() == att[key], f'ficha diverge do hash atestado: {fname}'
        review_key = json.loads((root / 'v7/private/review_key.json').read_text(encoding='utf8'))
        check_review_sheets(review_key, parse_sheet(raws['pairs_csv_sha256'], 'par'),
                            parse_sheet(raws['refusals_csv_sha256'], 'recusa'))
    return out | {'state': 'PASS', 'review': att['status']}


if __name__ == '__main__':
    phase = sys.argv[sys.argv.index('--phase') + 1] if '--phase' in sys.argv else 'protocol'
    try:
        print(json.dumps(verify(phase), ensure_ascii=False))
    except Exception as exc:
        print('FAIL', str(exc), file=sys.stderr)
        sys.exit(2)

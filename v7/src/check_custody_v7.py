"""V7 — controle de custódia pela história Git (R2). Executado no workflow antes do HL7 e do comparador.

Exige a sequência pré-registrada:
  commit de congelamento (protocol_commit) < commit de geração (adiciona manifest_v7.json)
  < commit do parecer (adiciona attestation_v7.json) <= HEAD,
com gold/mapa/chave/overlays/kit adicionados somente no commit do parecer ou depois,
e nenhuma saída oficial V7 versionada antes da execução.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVADOS = ('v7/private/gold_v7.json', 'v7/private/opaque_map.json', 'v7/private/review_key.json',
            'v7/private/refusal_records.json', 'v7/review_kit_V7.zip')


def git(root, *args, check=True):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=check)


def first_add(root, path):
    out = git(root, 'log', '--diff-filter=A', '--format=%H', '--', path).stdout.split()
    assert out, f'arquivo nunca commitado: {path}'
    return out[-1]


def is_ancestor(root, a, b):
    return git(root, 'merge-base', '--is-ancestor', a, b, check=False).returncode == 0


def strictly_before(root, a, b):
    return a != b and is_ancestor(root, a, b)


def check(root=None):
    root = Path(root or ROOT)
    assert not git(root, 'status', '--porcelain', '--untracked-files=no').stdout.strip(), 'arquivos versionados modificados localmente'
    head = git(root, 'rev-parse', 'HEAD').stdout.strip()
    m = json.loads((root / 'v7/benchmark/manifest_v7.json').read_text(encoding='utf8'))
    att = json.loads((root / 'v7/review/attestation_v7.json').read_text(encoding='utf8'))
    proto = m['protocol_commit']
    gen = first_add(root, 'v7/benchmark/manifest_v7.json')
    rev = first_add(root, 'v7/review/attestation_v7.json')
    fz = first_add(root, 'v7/FREEZE_V7.json')
    assert fz == proto or is_ancestor(root, fz, proto), 'FREEZE posterior ao commit de protocolo'
    assert strictly_before(root, proto, gen), 'geração não é posterior ao congelamento do protocolo'
    assert strictly_before(root, gen, rev), 'parecer não é posterior à geração'
    assert is_ancestor(root, rev, head), 'parecer não está na história do commit executado'
    assert att['generation_commit'] == gen, 'attestation_v7.generation_commit diverge do commit que adicionou o manifesto'
    for p in PRIVADOS + tuple(m['overlays_sha256']):
        c = first_add(root, p)
        assert c == rev or strictly_before(root, rev, c), f'material privado publicado antes do parecer congelado: {p}'
    tracked_outputs = git(root, 'ls-files', 'v7/outputs').stdout.strip()
    assert not tracked_outputs, 'saídas V7 já versionadas antes da execução oficial'
    return {'state': 'PASS', 'protocol_commit': proto, 'generation_commit': gen, 'review_commit': rev, 'head': head}


if __name__ == '__main__':
    try:
        res = check()
        out = ROOT / 'v7/outputs/ci/custody_v7.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2) + '\n', encoding='utf8')
        print(json.dumps(res))
    except Exception as exc:
        print('FAIL', str(exc), file=sys.stderr)
        sys.exit(2)

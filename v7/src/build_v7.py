"""V7 — geração única dos 51 arquivos experimentais (apêndice C).

Pré-condições (falha fechada):
  1. verify_v7 --phase protocol aprovado (hashes do FREEZE_V7.json conferem);
  2. árvore git limpa e FREEZE_V7.json já commitado (registra o commit no manifesto);
  3. nenhum arquivo V7 gerado anteriormente (nunca sobrescreve).
Não executa o HL7 Validator nem o comparador. Não lê resultados de nenhuma versão.
"""
from __future__ import annotations
import sys, json, hashlib, platform, subprocess, argparse, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vendor'))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from isys_converter.schema import verify_base, SyntheticGraph          # congelado (V6.1)
from isys_converter.transform import convert, decimal_json             # congelado (V6.1)
from overlay_components import write_overlay                            # congelado (V6.1)
from build_v6 import mutate                                             # congelado (V6.1)
import v7_spec, v7_operators as op

VARIANTES_EMIT = ('baseline', 'N1', 'N2', 'N3', 'N4', 'mutation')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _h(seed, *labels):
    return hashlib.sha256('|'.join((seed,) + labels).encode('utf-8')).hexdigest()


def generate(families, root, original, seed):
    """Núcleo determinístico. Retorna (registros, overlays, recusas). Usado também pelo teste de fumaça."""
    declarations = verify_base(original)['declared_uris']
    registros, overlays, recusas = [], {}, {}
    for f in families:
        fid = f['id']
        ov = root / 'benchmark/fixtures/overlays' / f'{fid}.owx'
        if ov.exists():
            raise RuntimeError('Overlay já existe; nunca sobrescrever: ' + str(ov))
        write_overlay(f, ov)
        overlays[fid] = ov
        bundle, trace, rejected, _ = convert(SyntheticGraph(ov, declarations))
        if f['expected_decision'] == 'reject':
            reasons = sorted({r for x in rejected for r in x['reasons']})
            assert set(f['expected_rejection_reasons']).issubset(reasons), (fid, reasons)
            assert len(rejected) == len(f['exams']) and not trace, (fid, rejected)
            recusas[fid] = {'family': fid, 'decision': 'REFUSED', 'converter_rejections': rejected,
                            'expected_reasons': f['expected_rejection_reasons']}
            registros.append({'family': fid, 'variant': 'refusal', 'expected_class': 'expected_refusal',
                              'operation': 'serialize_refusal_without_entry',
                              'bundle': op.serialize_refusal(bundle)})
            continue
        assert not rejected and len(trace) == len(f['exams']), (fid, rejected)
        n4, alterados = op.n4_unicode_nfd(bundle)
        var = {
            'baseline': (bundle, 'correct_conversion', None),
            'N1': (op.n1_narrative(bundle), 'equivalent_control', 'n1_narrative'),
            'N2': (op.n2_reidentify(bundle, seed), 'equivalent_control', 'n2_reidentify'),
            'N3': (op.n3_absolute_reference(bundle), 'equivalent_control', 'n3_absolute_reference'),
            'N4': (n4, 'equivalent_control' if alterados else 'n4_not_applicable', 'n4_unicode_nfd'),
            'mutation': (mutate(bundle, f['mutation']['operation'], fid), 'semantic_fault', f['mutation']['operation']),
        }
        for v in VARIANTES_EMIT:
            b, cls, operation = var[v]
            registros.append({'family': fid, 'variant': v, 'expected_class': cls, 'operation': operation,
                              'n4_fields_changed': alterados if v == 'N4' else None, 'bundle': b})
    return registros, overlays, recusas


def assign_opaque(registros, seed):
    ordem = sorted(registros, key=lambda r: _h(seed, 'ordem', r['family'], r['variant']))
    for i, r in enumerate(ordem, 1):
        r['opaque_id'] = f'V7-{i:03d}'
    return ordem


def write_review_kit(ordem, overlays, recusas, kit, seed):
    """Kit cego: pares (A/B) sem rótulo de condição, incluindo pares-chamariz com mutação."""
    pares_dir = kit / 'pares'; pares_dir.mkdir(parents=True)
    rec_dir = kit / 'recusas'; rec_dir.mkdir(parents=True)
    base = {r['family']: r for r in ordem if r['variant'] == 'baseline'}
    itens = [r for r in ordem if r['variant'] in ('N1', 'N2', 'N3', 'N4', 'mutation')
             and r['expected_class'] != 'n4_not_applicable']
    itens.sort(key=lambda r: _h(seed, 'par', r['family'], r['variant']))
    chave, linhas = [], ['par,veredito,justificativa']
    for i, r in enumerate(itens, 1):
        pid = f'P{i:02d}'
        b0 = base[r['family']]
        primeiro_ref = int(_h(seed, 'lado', r['family'], r['variant']), 16) % 2 == 0
        a, b = (b0, r) if primeiro_ref else (r, b0)
        (pares_dir / f'{pid}_A.json').write_text(decimal_json(a['bundle']), encoding='utf8')
        (pares_dir / f'{pid}_B.json').write_text(decimal_json(b['bundle']), encoding='utf8')
        chave.append({'pair': pid, 'A': a['opaque_id'], 'B': b['opaque_id'], 'family': r['family'],
                      'category': r['variant'], 'reference_side': 'A' if primeiro_ref else 'B'})
        linhas.append(f'{pid},,')
    (kit / 'FICHA_PARES_V7.csv').write_text('\n'.join(linhas) + '\n', encoding='utf-8-sig')
    rec_ids = sorted(recusas, key=lambda fid: _h(seed, 'recusa', fid))
    linhas_r = ['recusa,veredito,justificativa']
    for i, fid in enumerate(rec_ids, 1):
        rid = f'R{i}'
        shutil.copyfile(overlays[fid], rec_dir / f'{rid}_origem.owx')
        motivo = sorted({m for x in recusas[fid]['converter_rejections'] for m in x['reasons']})
        (rec_dir / f'{rid}_motivo.json').write_text(json.dumps({'recusa': rid, 'motivos': motivo},
                                                                ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        chave.append({'refusal': rid, 'family': fid})
        linhas_r.append(f'{rid},,')
    (kit / 'FICHA_RECUSAS_V7.csv').write_text('\n'.join(linhas_r) + '\n', encoding='utf-8-sig')
    return chave


def write_kit_zip(kit, dest):
    """B2: ZIP de entrega determinístico (ordem, datas e permissões fixas) para custódia do material enviado."""
    with zipfile.ZipFile(dest, 'w') as z:
        for p in sorted(x for x in kit.rglob('*') if x.is_file()):
            info = zipfile.ZipInfo(str(p.relative_to(kit)), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    return sha(dest)


def check_original(original, freeze):
    """B4: a ontologia de origem deve ser exatamente o ZIP histórico fixado no FREEZE, antes de qualquer geração."""
    assert Path(original).is_file(), 'ZIP original ausente'
    assert sha(original) == freeze['source_ontology_zip_sha256'], 'ZIP da ontologia diverge do fixado no pré-registro'
    with zipfile.ZipFile(original) as z:
        owx = [i for i in z.infolist() if i.filename.lower().endswith('.owx')]
        assert len(owx) == 1 and hashlib.sha256(z.read(owx[0])).hexdigest() == freeze['source_ontology_owx_sha256'], 'marco.owx divergente'
    return True


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', type=Path, required=True, help='ZIP original da ontologia (uso local, não distribuído)')
    a = ap.parse_args()
    from verify_v7 import verify
    verify('protocol')
    freeze = json.loads((ROOT / 'v7/FREEZE_V7.json').read_text(encoding='utf8'))
    check_original(a.original, freeze)
    if git('status', '--porcelain'):
        raise RuntimeError('Árvore git com alterações: commit do protocolo obrigatório antes da geração')
    git('ls-files', '--error-unmatch', 'v7/FREEZE_V7.json')
    commit = git('rev-parse', 'HEAD')
    out_inputs = ROOT / 'v7/benchmark/inputs'
    if (ROOT / 'v7/benchmark/manifest_v7.json').exists() or out_inputs.exists():
        raise RuntimeError('V7 já gerada; nunca regenerar. Correções exigem nova versão.')
    families = v7_spec.build_families(v7_spec.SEMENTE_V7)
    registros, overlays, recusas = generate(families, ROOT, a.original, v7_spec.SEMENTE_V7)
    ordem = assign_opaque(registros, v7_spec.SEMENTE_V7)
    assert len(ordem) == 51, len(ordem)
    out_inputs.mkdir(parents=True)
    for r in ordem:
        (out_inputs / f"{r['opaque_id']}.json").write_text(decimal_json(r['bundle']), encoding='utf8')
    priv = ROOT / 'v7/private'; priv.mkdir(parents=True)
    (priv / 'gold_v7.json').write_text(json.dumps({'spec': 'ISYS-V7', 'seed': v7_spec.SEMENTE_V7,
                                                   'families': families}, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf8')
    mapa = [{k: r[k] for k in ('opaque_id', 'family', 'variant', 'expected_class', 'operation', 'n4_fields_changed') if k in r}
            for r in ordem]
    (priv / 'opaque_map.json').write_text(json.dumps(mapa, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (priv / 'refusal_records.json').write_text(json.dumps(recusas, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf8')
    kit = ROOT / 'v7/review_kit'
    chave = write_review_kit(ordem, overlays, recusas, kit, v7_spec.SEMENTE_V7)
    (priv / 'review_key.json').write_text(json.dumps(chave, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    shutil.copyfile(ROOT / 'v7/GUIA_REVISAO_V7.md', kit / 'GUIA_REVISAO_V7.md')
    kit_zip_sha = write_kit_zip(kit, ROOT / 'v7/review_kit_V7.zip')
    manifest = {
        'benchmark_id': 'ISYS-V7-2026', 'status': 'GENERATED__REVIEW_PENDING__HL7_NOT_EXECUTED',
        'protocol_commit': commit, 'freeze_sha256': sha(ROOT / 'v7/FREEZE_V7.json'),
        'seed': v7_spec.SEMENTE_V7, 'frozen_v61_modules': freeze['frozen_v61_modules'],
        'validator_cli_version': '7.0.3', 'validator_cli_sha256': '57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b',
        'fhir_version': '4.0.1', 'fhir_core': 'hl7.fhir.r4.core#4.0.1',
        'profile': 'http://hl7.org/fhir/StructureDefinition/Bundle', 'terminology': '-tx n/a',
        'source_ontology_original_sha256': sha(a.original), 'original_ontology_NOT_distributed': True,
        'environment': {'python': platform.python_version(), 'platform': platform.platform()},
        'inputs': {r['opaque_id']: {'path': f"v7/benchmark/inputs/{r['opaque_id']}.json",
                                    'sha256': sha(out_inputs / f"{r['opaque_id']}.json")} for r in ordem},
        'overlays_sha256': {f'benchmark/fixtures/overlays/{fid}.owx': sha(p) for fid, p in overlays.items()},
        'private_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(priv.glob('*.json'))},
        'review_kit_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(kit.rglob('*')) if p.is_file()},
        'review_kit_zip_sha256': kit_zip_sha,
        'counts': {'files_for_hl7': len(ordem), 'convertible_families': 8, 'refusal_families': 3,
                   'n4_not_applicable': sum(r['expected_class'] == 'n4_not_applicable' for r in ordem)},
        'blinding_rule': 'v7/private, overlays H01–H11, review_kit/ and review_kit_V7.zip are git-ignored and committed (git add -f) only together with the frozen review verdict',
    }
    (ROOT / 'v7/benchmark/manifest_v7.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf8')
    print(json.dumps({'state': 'GENERATED', 'files': len(ordem), 'protocol_commit': commit,
                      'manifest_sha256': sha(ROOT / 'v7/benchmark/manifest_v7.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

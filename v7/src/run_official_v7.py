"""V7 — execução oficial do HL7 Validator CLI 7.0.3 nas 51 entradas opacas (apêndice D).

Somente após verify_v7 --phase reviewed. Mesmos parâmetros da V6.1. Preserva saídas brutas.
Não executa o comparador: a análise é etapa separada (analyze_v7.py).
"""
from __future__ import annotations
import argparse, sys, subprocess, json, time, hashlib, zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_v7 import verify


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf8')


def parse_outcome(path):
    try:
        a = json.loads(path.read_text(encoding='utf8'))
        if a.get('resourceType') != 'OperationOutcome' or not isinstance(a.get('issue'), list):
            return None
        c = Counter(x.get('severity') for x in a['issue'])
        return {'errors': c.get('error', 0) + c.get('fatal', 0), 'warnings': c.get('warning', 0),
                'information': c.get('information', 0), 'outcome_sha256': sha(path)}
    except (ValueError, OSError):
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jar', type=Path, required=True)
    p.add_argument('--timeout', type=int, default=240)
    a = p.parse_args()
    review = verify('reviewed')
    m = json.loads((ROOT / 'v7/benchmark/manifest_v7.json').read_text(encoding='utf8'))
    target = ROOT / 'v7/outputs/official'
    if (target / 'execution-summary.json').exists():
        raise RuntimeError('Execução oficial V7 já existe; nunca sobrescrever')
    logs = target / 'logs'; logs.mkdir(parents=True)
    run = {'benchmark_id': m['benchmark_id'], 'state': 'STARTED', 'planned': len(m['inputs']), 'completed': 0,
           'validator_cli_version': m['validator_cli_version'], 'fhir_version': m['fhir_version'],
           'profile': m['profile'], 'terminology': '-tx n/a', 'review_gate': review, 'results': [],
           'measurement': 'Duration includes Java startup per invocation; not an algorithmic cost; not analysed in V7'}
    if not a.jar.is_file() or not zipfile.is_zipfile(a.jar) or sha(a.jar) != m['validator_cli_sha256']:
        run.update(state='BLOCKED', reason='JAR 7.0.3 ausente ou digest divergente')
        dump(target / 'execution-summary.json', run)
        return 3
    cp = subprocess.run(['java', '-version'], capture_output=True, timeout=15)
    run['java'] = (cp.stderr or cp.stdout).decode('utf8', 'replace').splitlines()[0]
    for i, (oid, v) in enumerate(sorted(m['inputs'].items()), 1):
        infile = ROOT / v['path']
        if sha(infile) != v['sha256']:
            raise RuntimeError('Entrada alterada ' + oid)
        out = target / f'{oid}.outcome.json'
        cmd = ['java', '-jar', str(a.jar), str(infile), '-version', m['fhir_version'], '-tx', 'n/a',
               '-profile', m['profile'], '-output', str(out)]
        rec = {'id': oid, 'input': v['path'], 'input_sha256': v['sha256'], 'command': cmd, 'state': 'NOT_RUN'}
        t0 = time.monotonic()
        try:
            cp = subprocess.run(cmd, capture_output=True, timeout=a.timeout, cwd=ROOT)
            (logs / f'{oid}.stdout.log').write_bytes(cp.stdout)
            (logs / f'{oid}.stderr.log').write_bytes(cp.stderr)
            rec['exit_code'] = cp.returncode
            o = parse_outcome(out)
            if o:
                rec.update(o); rec['state'] = 'VALIDATED'; run['completed'] += 1
            else:
                rec['state'] = 'INVALID_OR_MISSING_OUTCOME'
        except subprocess.TimeoutExpired as e:
            rec['state'] = 'TIMEOUT'
            (logs / f'{oid}.timeout.txt').write_text(str(e), encoding='utf8')
        rec['duration_seconds'] = round(time.monotonic() - t0, 6)
        run['results'].append(rec)
        dump(target / 'execution-summary.json', run)
        print(f'{i}/{len(m["inputs"])} {oid}: {rec["state"]}', flush=True)
    run['state'] = 'COMPLETED' if run['completed'] == len(m['inputs']) else 'PARTIAL'
    dump(target / 'execution-summary.json', run)
    return 0 if run['state'] == 'COMPLETED' else 4


if __name__ == '__main__':
    sys.exit(main())

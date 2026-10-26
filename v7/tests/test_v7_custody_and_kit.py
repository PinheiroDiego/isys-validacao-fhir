"""B2/B3/B4/R1/R2: ZIP do kit, ontologia de origem, política Git e custódia, com repositórios temporários fictícios."""
import sys, os, json, unittest, tempfile, subprocess, zipfile, hashlib, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'src'))
import verify_v7, check_custody_v7
from build_v7 import write_kit_zip, check_original

def sh(root, *a):
    return subprocess.run(['git', *a], cwd=root, capture_output=True, text=True, check=True).stdout.strip()

def commit(root, msg, *paths, force=False):
    sh(root, 'add', *(['-f'] if force else []), *paths); sh(root, 'commit', '-q', '-m', msg); return sh(root, 'rev-parse', 'HEAD')

def init(root):
    sh(root, 'init', '-q'); sh(root, 'config', 'user.email', 't@t'); sh(root, 'config', 'user.name', 't')
    sh(root, 'config', 'core.autocrlf', 'input')

class Kit(unittest.TestCase):
    def test_kit_zip_deterministic_and_tamper_detected(self):
        with tempfile.TemporaryDirectory() as d:
            kit = Path(d) / 'v7/review_kit'; (kit / 'pares').mkdir(parents=True)
            (kit / 'pares/P01_A.json').write_text('{"a": 1}\n'); (kit / 'GUIA.md').write_text('g\n')
            h1 = write_kit_zip(kit, Path(d) / 'k1.zip'); h2 = write_kit_zip(kit, Path(d) / 'k2.zip')
            self.assertEqual(h1, h2)
            man = {'review_kit_zip_sha256': h1, 'review_kit_sha256': {
                'v7/review_kit/' + str(p.relative_to(kit)): hashlib.sha256(p.read_bytes()).hexdigest() for p in kit.rglob('*') if p.is_file()}}
            self.assertEqual(verify_v7.check_kit_zip(Path(d) / 'k1.zip', man), 2)
            (kit / 'GUIA.md').write_text('alterado\n'); write_kit_zip(kit, Path(d) / 'k3.zip')
            with self.assertRaises(AssertionError):
                verify_v7.check_kit_zip(Path(d) / 'k3.zip', man)

    def test_original_zip_pinned(self):
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / 'o.zip'
            with zipfile.ZipFile(z, 'w') as f: f.writestr('x/marco.owx', b'<Ontology/>')
            inner = hashlib.sha256(b'<Ontology/>').hexdigest(); outer = hashlib.sha256(z.read_bytes()).hexdigest()
            self.assertTrue(check_original(z, {'source_ontology_zip_sha256': outer, 'source_ontology_owx_sha256': inner}))
            with self.assertRaises(AssertionError):
                check_original(z, {'source_ontology_zip_sha256': '0' * 64, 'source_ontology_owx_sha256': inner})

class GitPolicy(unittest.TestCase):
    def test_crlf_preserved_with_policy_and_altered_without(self):
        raw = b'\xef\xbb\xbfpar,veredito,justificativa\r\nP01,EQUIVALENTE,\r\n'
        for with_policy in (True, False):
            with tempfile.TemporaryDirectory() as d:
                r = Path(d) / 'r'; r.mkdir(); init(r); (r / 'v7/review').mkdir(parents=True)
                if with_policy: shutil.copyfile(HERE / '.gitattributes', r / 'v7/.gitattributes')
                (r / 'v7/review/F.csv').write_bytes(raw); commit(r, 'c', '.')
                c = Path(d) / 'c'; subprocess.run(['git', 'clone', '-q', str(r), str(c)], check=True)
                same = (c / 'v7/review/F.csv').read_bytes() == raw
                self.assertEqual(same, with_policy)

    def test_gitignore_blocks_private_material(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d); init(r); (r / 'v7/private').mkdir(parents=True)
            shutil.copyfile(HERE / '.gitignore', r / 'v7/.gitignore')
            (r / 'v7/private/gold_v7.json').write_text('{}'); (r / 'v7/review_kit_V7.zip').write_bytes(b'z')
            sh(r, 'add', '.')
            staged = sh(r, 'diff', '--cached', '--name-only').split()
            self.assertEqual(staged, ['v7/.gitignore'])

class Custody(unittest.TestCase):
    def build(self, d, private_early=False, gen_mismatch=False, outputs_tracked=False):
        r = Path(d); init(r); (r / 'v7/benchmark').mkdir(parents=True); (r / 'v7/review').mkdir(); (r / 'v7/private').mkdir()
        (r / 'benchmark/fixtures/overlays').mkdir(parents=True)
        (r / 'v7/FREEZE_V7.json').write_text('{}'); proto = commit(r, 'protocolo', 'v7/FREEZE_V7.json')
        man = {'protocol_commit': proto, 'overlays_sha256': {'benchmark/fixtures/overlays/H01.owx': 'x'}}
        (r / 'v7/benchmark/manifest_v7.json').write_text(json.dumps(man))
        privs = list(check_custody_v7.PRIVADOS) + ['benchmark/fixtures/overlays/H01.owx']
        for p in privs: (r / p).write_text('p')
        gen = commit(r, 'geracao', 'v7/benchmark/manifest_v7.json', *(privs if private_early else []), force=True)
        att = {'generation_commit': 'f' * 40 if gen_mismatch else gen}
        (r / 'v7/review/attestation_v7.json').write_text(json.dumps(att))
        commit(r, 'parecer', 'v7/review/attestation_v7.json', *([] if private_early else privs), force=True)
        if outputs_tracked:
            (r / 'v7/outputs').mkdir(); (r / 'v7/outputs/x.json').write_text('{}'); commit(r, 'saidas', 'v7/outputs/x.json', force=True)
        return r

    def test_correct_sequence_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(check_custody_v7.check(self.build(d))['state'], 'PASS')

    def test_violations_fail(self):
        for kw in ({'private_early': True}, {'gen_mismatch': True}, {'outputs_tracked': True}):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(AssertionError, msg=str(kw)):
                    check_custody_v7.check(self.build(d, **kw))

if __name__ == '__main__':
    unittest.main()

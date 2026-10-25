"""Run: PYTHONPATH=src python -m isys_converter.cli --base-zip ... --output ..."""
from pathlib import Path
import argparse,json,hashlib
from .schema import verify_base,SyntheticGraph
from .transform import convert,decimal_json
from .audit import local_structure_check,compare_oracle,mutations_and_checks
from .competency import queries


def main():
    p=argparse.ArgumentParser(description='Synthetic overlay OWL/XML to FHIR R4 converter; base file read-only')
    p.add_argument('--base-zip',type=Path,required=True)
    p.add_argument('--overlay',type=Path,default=Path('data/extensao-sintetica-v1.owx'))
    p.add_argument('--oracle',type=Path,default=Path('data/oraculo-independente.json'))
    p.add_argument('--output',type=Path,default=Path('outputs'))
    args=p.parse_args()
    before=hashlib.sha256(args.base_zip.read_bytes()).hexdigest()
    base=verify_base(args.base_zip)
    g=SyntheticGraph(args.overlay,base['declared_uris'])
    bundle,trace,refusals,report=convert(g)
    oracle=json.loads(args.oracle.read_text(encoding='utf8'))
    report['original_owl_sha256_before']=base['sha256']
    report['original_zip_sha256_before']=before
    report['overlay_sha256']=g.sha256
    report['local_structure_checker_findings']=local_structure_check(bundle)
    report['independent_oracle_discrepancies']=compare_oracle(bundle,trace,refusals,oracle)
    exp=mutations_and_checks(bundle,trace,refusals,oracle)
    q=queries(g,bundle,trace,refusals)
    after=hashlib.sha256(args.base_zip.read_bytes()).hexdigest()
    report['original_zip_sha256_after']=after
    report['original_not_modified']=before==after
    if before!=after:raise RuntimeError('Original archive unexpectedly changed')
    if report['local_structure_checker_findings'] or report['independent_oracle_discrepancies']:
        raise RuntimeError('Sanity check or independent test oracle failed: '+str(report))
    args.output.mkdir(parents=True,exist_ok=True)
    for path,content in [
        ('bundle-fhir-r4-sintetico.json',decimal_json(bundle)),
        ('rastreamento-sintetico.json',json.dumps(trace,ensure_ascii=False,indent=2)+'\n'),
        ('recusas-sinteticas.json',json.dumps(refusals,ensure_ascii=False,indent=2)+'\n'),
        ('relatorio-execucao.json',json.dumps(report,ensure_ascii=False,indent=2)+'\n'),
        ('mutacoes-local.json',json.dumps(exp,ensure_ascii=False,indent=2)+'\n'),
        ('perguntas-competencia.json',json.dumps(q,ensure_ascii=False,indent=2)+'\n'),
    ]:
        (args.output/path).write_text(content,encoding='utf8')
    print(json.dumps({'converted':report['emitted_observations'],
                      'refused':report['rejected_exams'],'oracle_discrepancies':len(report['independent_oracle_discrepancies']),
                      'local_structure_flags':len(report['local_structure_checker_findings']),
                      'original_not_modified':report['original_not_modified']},ensure_ascii=False))

if __name__=='__main__':main()

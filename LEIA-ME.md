# iSys V6.1 — correção da execução #6 (seleção de testes)

**Diagnóstico confirmado:** a ratificação externa passou, mas `python3 -m unittest discover -s tests -v` executava também `test_v4.py` e `test_v5.py` contra o gold corrente da V6.1. O resultado foram seis falhas e quatro erros (56 testes no total), encerrando o workflow antes do validador HL7.

## O que muda

Somente `.github/workflows/isys-v6-hl7.yml` é alterado. A etapa de regressão exige a presença dos quatro módulos próprios da V6/V6.1 e executa:

```bash
python3 -m unittest discover -s tests -p 'test_v6*.py' -v
```

Isso inclui `test_v6.py`, `test_v61_adjudicated.py`, `test_v61_checkout_eol.py` e `test_v61_ratified.py`. Não executa os testes históricos da V4/V5 contra os arquivos correntes. Os arquivos históricos seguem congelados e seus hashes continuam verificados na etapa `python3 src/verify_v6.py`, que não foi modificada.

## Verificações realizadas

- `verify_v6.py`: PASS, 98 arquivos FHIR e 36 overlays conferidos.
- `review_gate.py`: RATIFIED_WITH_RESSALVAS, 26 famílias confirmatórias.
- Suíte selecionada V6/V6.1, inclusive na presença dos testes legados V4/V5: **28/28 aprovados**.
- Nenhuma alteração em casos FHIR, gold, oráculo, ontologia, ratificação ou histórico.
- **Validação oficial HL7 V6.1: ainda não executada**. O workflow foi interrompido na etapa de testes antes de baixar o JAR.

## Como aplicar

1. Extraia este ZIP na raiz do repositório privado `PinheiroDiego/isys-validacao-fhir`, substituindo `.github/workflows/isys-v6-hl7.yml`.
2. Commit na branch `main`.
3. Inicie um **novo** `Actions → iSys V6.1 - HL7 Adjudicated Benchmark → Run workflow`, com `scope: confirmatory`.
4. Anexe o artefato `isys-v6.1-confirmatory-hl7` (mesmo se falhar); os logs devem permanecer em `outputs/ci_diagnostics/`.

Não use apenas `Re-run jobs` de um commit anterior; essa opção não adota a correção ainda não publicada na branch.

**Limite científico:** correção operacional de pipeline, sem nova avaliação cega e sem mudança nos dados do benchmark.

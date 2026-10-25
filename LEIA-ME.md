# Diagnóstico de CI – iSys V6.1 / execução #4

A execução #4 enviou apenas `benchmark/manifest_v6.json`, `review/attestation.json` e `review/decisions.csv`, sem resultados oficiais. O código 1 não identifica a etapa exata. A falha anterior da trava CSV (código 3) foi corrigida.

## Alteração

Substitua **somente** `.github/workflows/isys-v6-hl7.yml` pelo arquivo homônimo deste pacote. Este patch não altera nenhum caso, entrada FHIR, ontologia, gold, parecer, script de validação nem regra de liberação.

As etapas mantêm o comportamento de falhar em caso de erro (`set -euo pipefail`), mas registram a saída em `outputs/ci_diagnostics`. O `upload-artifact` em `always()` inclui esses arquivos mesmo com falha.

## Como executar

Faça commit do workflow e inicie uma **nova execução** da ação "iSys V6.1 - HL7 Adjudicated Benchmark", com `scope=confirmatory`. Não use `Re-run jobs` de uma execução antiga.

Baixe `isys-v6.1-confirmatory-hl7` e envie-o novamente; agora o ZIP deve incluir `outputs/ci_diagnostics/01-verify-v6.log` até o último passo executado, identificando o bloqueio exato. Se o validador rodar, também haverá `outputs/official_v6/confirmatory` e `outputs/metrics_v6/confirmatory`.

## Segurança

- A execução confirmatória exige o parecer, sem atalhos.
- `sha256sum -c -` do validador permanece obrigatório, com o mesmo SHA-256 fixado.
- O `unittest` permanece obrigatório; erros continuam interrompendo o fluxo.
- A versão dos dados não foi alterada.
- A instrumentação não serve como resultado científico; registrar no artigo somente a execução oficial bem-sucedida e seus artefatos.

## Integridade deste patch

Workflow original SHA-256: `42ca20c9ab8bec9f8953b86d3355acfff6c63bf4ad27e438ac651642ab141c44`
Workflow instrumentado SHA-256: `9ce186b0b46584a307ed252e852bf8fc7d0fd733f1c2f4d986b8422ae04a1ff9`

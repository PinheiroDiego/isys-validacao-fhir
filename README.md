# iSys — Revalidação oficial HL7 FHIR V3 (Bundle corrigido)

**O ZIP original da ontologia não está incluído, e nenhum dado clínico real foi usado.**

Este pacote corrige a falha encontrada na primeira execução oficial: as 7 entradas do Bundle de referência agora usam `Bundle.entry.fullUrl` absoluta consistente (`https://example.org/fhir/<tipo>/<id>`); `Observation.subject.reference` permanece relativa e resolúvel. Todos os Bundles mutados receberam a mesma correção de empacotamento; nenhuma mutação ou valor clínico sintético foi alterado.

**Importante:** os resultados V3 ainda NÃO foram produzidos pelo validador oficial. O que já foi executado em V2 está documentado em `docs/parecer-v2.md`.

## Execute no mesmo repositório privado do GitHub

1. Descompacte este pacote e envie seu conteúdo ao repositório `isys-validacao-fhir` existente, sobrescrevendo arquivos de mesmos caminhos na branch `main` (não envie o ZIP fechado). A pasta oculta `.github/workflows` deve ser mantida.
2. Em **Actions**, execute `iSys - Validacao FHIR R4 fixa` via **Run workflow**, ou acompanhe a execução automática gerada pelo push.
3. Em **Artifacts**, baixe o novo `isys-hl7-fhir-r4-validation` e anexe-o ao ChatGPT.
4. Não misture os novos resultados com o ZIP antigo. Compare hashes e `execution-summary.json`.

## O que será registrado

- 16 operações: 1 Bundle válido esperado + 7 recursos individuais + 8 Bundles mutados.
- `OperationOutcome` e logs para cada entrada, hashes, versão do Java/validador, tempos e contagem de mensagens.
- `differential-mutation-analysis.json`: compara cada mutação com o baseline; se o Bundle base falhar, as taxas de detecção permanecem **null**, nunca 100% indevido.
- `coverage-metrics.json`: cobertura do conversor e conformidade fim a fim, separadas.
- `scripts/preflight.py`: verificação de integridade e referências antes da validação.

FHIR fixado: R4 4.0.1; HL7 Validator CLI 7.0.3; `-tx n/a`. Não pressupor conformidade de terminologias ou perfis de implementação de terceiros.

O JAR da primeira execução oficial é agora fixado também pelo SHA-256 `57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b`; o workflow aborta se receber outro binário, para impedir deriva silenciosa. Dependências complementares de terminologia devem ser registradas pelos logs e não são tratadas como totalmente congeladas.

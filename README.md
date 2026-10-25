# iSys — Validação HL7 FHIR oficial (piloto sintético)

Este repositório foi preparado para executar o validador **oficial** HL7 FHIR CLI **7.0.3** contra perfis-base FHIR **R4 4.0.1** (`Patient`, `Observation`, `Bundle`). Os dados aqui são **sintéticos**. O esquema e indivíduos da ontologia original NÃO estão incluídos.

## Para executar SEM instalar nada localmente

1. Crie um repositório **privado** no GitHub (com um README inicial, para ter a branch `main`).
2. Baixe e descompacte `isys-github-actions-pronto.zip`.
3. No repositório, escolha **Add file > Upload files**; arraste o **conteúdo** da pasta `isys-github-actions-pronto`, mantendo a estrutura. Faça commit na `main`. Se o GitHub não incluir a pasta `.github` nesse upload, crie o arquivo `.github/workflows/validar-fhir-r4.yml` na interface, copiando o arquivo fornecido no pacote.
4. Abra **Actions > iSys - Validacao FHIR R4 fixa > Run workflow > main > Run workflow**.
5. Abra a execução concluída, seção **Artifacts**, e baixe `isys-hl7-fhir-r4-validation`.
6. Na pasta descompactada de resultados, consulte `outputs/official/coverage-metrics.json`, `outputs/official/execution-summary.json`, e `outputs/official/*.outcome.json`.

O workflow obtém automaticamente o JAR e as definições FHIR R4 pela rede do GitHub Actions. Se houver erro de download, o erro será preservado no log; não equivale a falha de conformidade.

## Interpretação

- **16 requisições**: 1 Bundle base + 7 recursos individuais + 8 Bundles mutados.
- **11 ocorrências de origem**; 5 convertidas, 6 recusadas; cobertura de conversão 5/11.
- `official_validation_requests_completed=16` somente quando os 16 `OperationOutcome` forem obtidos.
- `official_observation_profile_pass_rate` informa conformidade dos `Observation` validados contra **perfis-base**, não contra BR Core/RNDS ou perfil especializado.
- `-tx n/a` desativa um servidor terminológico externo, limitando os testes de terminologias.

Evite divulgar arquivos com dados pessoais ou a ontologia original; este repositório contém somente dados artificiais.

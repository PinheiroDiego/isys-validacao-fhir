# Protocolo científico V4 — pré-registro operacional do benchmark sintético

Data de congelamento: 25/10/2026. Periódico-alvo: iSys (*Journal of Information Systems*). Título provisório: *Beyond Structural Validation: Evaluating Semantic Preservation in Ontology-to-FHIR Transformation*.

## Questões de pesquisa

- RQ1: quais falhas de preservação persistem após uma validação FHIR sem erros?
- RQ2: qual diferença de sinalização das verificações semânticas, com quais falsos alarmes, recusas e custos?
- RQ3: quais classes de consultas mantêm equivalência exata de respostas normalizadas?

**O benchmark V4 foi criado artificialmente para explorar essas questões. Não é uma amostra aleatória e não é validação clínica. A referência foi produzida com assistência de IA, sem adjudicação humana independente até este momento.** Uma revisão independente com experiência em HL7 FHIR e representação de dados de saúde é necessária antes de usar os resultados como evidência científica mais forte.

## Materiais e imutabilidade

A execução V3 original, arquivos de entrada, conversor V1.1 e auditoria V3 estão preservados em `baseline_v3/*.zip`. Os hashes SHA-256 por arquivo estão em `baseline_v3/frozen_manifest.json`. Não há arquivo original da ontologia no pacote. O código-fonte V1.1 foi copiado sem alterações para `vendor/isys_converter` e verificado contra o ZIP original. O Gold e os 66 arquivos de entrada V4 são checados contra `benchmark/manifest_v4.json`. Congelamento é **verificável por hash**, não um repositório WORM nem assinatura externa de terceiros.

O gerador OWL/XML usa o namespace sintético separado `https://example.org/isys/fhir-semantic-test/2026/v1#` e apenas as três propriedades de extensão documentadas: `tem_ocorrencia_exame`, `data_exame`, `unidade_textual`. Instâncias reais da ontologia não são exportadas.

## Desenho experimental e unidade de análise

- 26 famílias de casos independentes **como cenários concebidos**, não observações empíricas independentes; 20 são conversíveis segundo critérios explícitos, 6 requerem recusa.
- As 20 famílias conversíveis produzem três variantes cada: `baseline` (conversão normal), `mutation` (alteração controlada) e `neutral` (controle semanticamente equivalente).
- Seis famílias de recusa possuem somente `baseline` (Bundle vazio). No total, 66 entradas oficiais previstas.
- Oito famílias (F01–F08) integram **desenvolvimento**; 18 (F09–F26), **avaliação**. O conjunto de avaliação é fechado antes de rodar a validação oficial V4; não ajustar as regras depois de ler seus resultados. Qualquer ajuste cria V5 e mantém V4 arquivado.
- F01–F16 têm mutações semânticas, F17–F20 são controles negativos estruturais. F21–F26 são exemplos de recusa pela origem. Cada família possui uma variante manipulada, portanto não contamos múltiplas variantes da mesma família como unidades independentes.
- Os 20 controles semanticamente equivalentes alteram somente ordenação das entradas (em Bundle `collection`) ou metadado sem caráter clínico (`meta.tag`). As verificações não devem sinalizá-los como alteração de conteúdo clínico.

## Referência de verdade (*gold*) e independência

`benchmark/gold/families.json` fixa declarativamente paciente(s), evolução(ões), ocorrência(s), data(s) com precisão, nome(s), valor(es), unidade(s), decisão esperada e mutação. `src/semantic_oracle.py` lê esse documento e compara o resultado FHIR sem importar o conversor ou utilizar o rastreamento emitido por ele. Espera identificadores reprodutíveis de uma convenção explicitamente definida. **Essa separação de código não constitui avaliação independente por um especialista**, nem garante que o gold esteja semanticamente correto. O mesmo documento prescreve as instâncias sintéticas; o risco de erro compartilhado de especificação deve ser controlado por revisão externa.

Não se utilizam terminologias clínicas normalizadas para afirmar equivalência LOINC/SNOMED CT/UCUM. Unidades textuais são preservadas literalmente e datas não recebem precisão adicional. Status obrigatório `unknown` deriva da regra FHIR R4 quando nenhum status da origem existe; não representa conhecimento clínico novo.

## Condições experimentais

- **A**: conversor de referência V1.1, aplicado aos overlays sintéticos, sem validação adicional como critério de aceitação. Relatar saída, recusa e motivos para todas as ocorrências. A ocorrência recusada permanece no denominador de cobertura.
- **B**: mesmas saídas de A submetidas ao HL7 Validator CLI **7.0.3** (`jar SHA-256=57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b`), especificação FHIR R4 **4.0.1**, `hl7.fhir.r4.core#4.0.1`, `Bundle` base profile `http://hl7.org/fhir/StructureDefinition/Bundle`, terminologia externa desabilitada (`-tx n/a`). Para cada variante B sinaliza somente se `OperationOutcome.issue.severity` contiver `error` ou `fatal`.
- **C**: mesma validação B mais o comparador semântico independente do código do conversor. Sinalização combinada `B_erro OR divergência_semântica`.

Os `Bundle` validam os recursos internos por seu contexto no pacote, mas não substituem um futuro teste de conformidade com um perfil clínico/nacional específico. Validação FHIR é uma verificação de conformidade computável, não uma prova de significado clínico. Documentação HL7 R4: https://hl7.org/fhir/R4/validation.html, https://hl7.org/fhir/R4/bundle.html, https://hl7.org/fhir/R4/observation.html.

**Detecção ≠ recusa ≠ reparação.** O benchmark V4 mede sinalização; nenhuma condição corrige a alteração automaticamente. Uma recusa do conversor A não é tratada como falso alarme de B, e Bundle vazio não significa ausência de fatos em um prontuário real.

## Métricas, denominadores, critérios de inclusão

1. Cobertura A: `número de ocorrências convertidas / número de ocorrências sintéticas elegíveis à tentativa` com recusas contadas no denominador; estratificar motivos e família.
2. Validação oficial concluída: `OperationOutcome presente e parseável / solicitações planejadas`; não inferir 0% de conformidade quando a validação não rodou.
3. Conformidade do baseline: erros fatais ou comuns = zero; avisos reportados separadamente, não classificados automaticamente como falha.
4. Detecção nas mutações semânticas: TP / 16 no conjunto completo **somente se todos os baselines e todas as mutações tiverem resultados oficiais**; 8 mutações semânticas estão na partição de avaliação.
5. Controles estruturais: quatro mutações de tipo estrutural são informadas separadamente; não usar a proporção de captura de controles estruturais como evidência de preservação semântica.
6. Falsos alarmes: eventos em baselines corretos e controles semanticamente equivalentes, com a descrição de cada classe e contagem de famílias. No conjunto completo são 40 exemplos sem falha, pareados dentro de 20 famílias.
7. Precisão de sinalização: `TP/(TP+FP)` e recall `TP/(TP+FN)`, estratificados por tipo de alteração, com contagens absolutas. A `especificidade` e taxa de falso alarme só se aplicam aos controles corretamente classificados e aprovados pela revisão do gold.
8. Para RQ3: consultas Q01–Q05 exigem comparação da **multiplicidade** (multiconjuntos), não apenas conjuntos, e comparação por fonte e destino mais gold. Q06 lista ausências e recusas. Consultas de competência V4 ainda não foram executadas contra todas as famílias; não reportar 100% de equivalência V4.
9. Tempo: medir separadamente tempo do JVM/validador por variante (incluindo inicialização) e tempo do comparador Python (incluindo leitura). Não atribuir causalmente a diferença à complexidade sem controlar ambiente e inicialização.

A unidade de análise para qualquer intervalo de confiança ou teste estatístico será **família**. Como as famílias foram propositalmente desenhadas e não sorteadas, resultados devem ser descritivos; não aplicar automaticamente um intervalo de confiança populacional nem testes de significância. Só considerar CI por bootstrap agrupado em um estudo ampliado e com justificativa explícita da população-alvo.

## Gatilhos de interpretação e integridade

Se um baseline de família não for conforme, sua comparação diferencial é **não interpretável** para RQ1/RQ2. Se algum arquivo estiver faltando/alterado, o executor aborta. Se o validador não estiver disponível ou não gerar `OperationOutcome`, registrar como `BLOCKED/PARTIAL` e deixar valores de B/C indefinidos. Controles semanticamente equivalentes sinalizados são falsos alarmes candidatos e exigem revisão da referência. Não remover casos difíceis para elevar as métricas.

## Revisão independente, congelamento final e divulgação

A planilha `benchmark/gold/review_protocol.csv` está em branco para revisão e pode ser preenchida por um segundo avaliador FHIR. Avaliar uma amostra estratificada de cada família, e todos os resultados que contradisserem o esperado, preservando o julgamento inicial e a adjudicação. A autora da transformação não deve fazer sozinha a adjudicação. Se houver revisões de gold, registrar diferenças, criar nova versão de benchmark e refazer ambos os grupos.

Publicar futuramente apenas fixtures sintéticas, protocolo e código cuja divulgação esteja autorizada. Não incluir instâncias reais nem reproduzir dados da empresa parceira sem uma autorização própria de divulgação.

### Implementação de Q01–Q06 no benchmark V4

`src/competency_v4.py` extrai afirmações explícitas diretamente dos overlays OWL/XML (sem raciocínio inferencial) e executa funções distintas sobre FHIR JSON, sem usar as funções nem o trace do conversor. Os multiconjuntos são comparados por ocorrência, identificador normalizado, paciente, nome do exame, valor e unidade. Em Q05, uma data anual/mensal pode gerar `INDETERMINATE`; a ausência gera `UNKNOWN_DATE`; não se trata como falso. Em Q06, recusas são inventariadas e diferenças de resposta são descritas, não convertidas automaticamente em um escore de acurácia. A avaliação integral Q01–Q06 sobre as 18 famílias reservadas depende do fechamento do estudo V4.

# Auditoria independente dos resultados técnicos — iSys V4

**Data:** 25/10/2026. **Natureza:** auditoria de engenharia de um benchmark sintético. Não é adjudicação clínica independente.

## Integridade e origem

- Artefato oficial recebido: SHA-256 `73e01142b5e5ce00051aa33e7515b6ef8725615558d362905be3cf3cc7fa79e9`.
- Gold V4: SHA-256 `dec62b7e8e479270d447229946e8bbfd785e269a705be69b204b05766715ba94`; não alterado.
- 42/42 entradas conferidas contra `benchmark/manifest_v4.json` e 42/42 `OperationOutcome` conferidos por hash e contagem de severidades.
- Oficial: HL7 Validator CLI 7.0.3, FHIR 4.0.1, Bundle base profile, terminologia externa desativada.
- 17 erros e 136 avisos ao longo de 42 validações; duração acumulada do executor de 395.777 s (mediana 9.348 s/execução).

## Resultados confirmados

- 12/12 conversões de referência sem erros HL7.
- 8/8 mutações semânticas não sinalizadas por erros HL7 (0/8). Oráculo semântico previamente definido sinalizou 8/8.
- 4/4 controles negativos estruturais apresentaram erros HL7 (5 erros distintos somados).
- Q01–Q05: equivalência para 12/12 baselines e 12/12 controles pretendidos; 10/12 mutações de qualquer tipo alteraram alguma resposta. **As 8 mutações semânticas alteraram consultas; duas mutações puramente estruturais não precisam alterar perguntas de competência.**
- Conversor: 15 de 21 ocorrências emitidas (71,43%); seis recusas por critérios explícitos, com razões documentadas. Isto não é cobertura clínica real.

## Dois defeitos não previstos nos controles

**1. F10, F12, F14, F16, F18 e F20 (neutral):** `Bundle.meta.tag[0].system` contém `https://example.org/isys/benchmark/metadata`. O HL7 Validator relata `Example URLs are not allowed in this context`. São 6 erros causados pelos metadados artificiais **criados pelo próprio controle**; não são falsos alarmes de detecção de uma estrutura FHIR conforme. A variante não altera as informações clínicas, mas viola uma regra computável. A taxa automática de 6/24 falsos alarmes (25%) não mede confiavelmente falso alarme em controles FHIR válidos. O relatório original deve ser preservado com essa ressalva, não retificado silenciosamente.

**2. F21–F26 (recusas):** conversor recusou as ocorrências, mas o empacotamento serializou `Bundle.entry: []`. HL7 relata `Array cannot be empty - the property should not be present if it has no values` (6 erros). São defeitos de empacotamento de casos sem representação, e **não validações bem-sucedidas das razões clínicas/semânticas de recusa**. Devem ficar fora do cálculo diferencial B/C e presentes no denominador da cobertura A.

A decomposição total dos erros é: 5 em quatro controles estruturais, 6 em controles equivalentes com metadados inválidos e 6 nos Bundles de recusa, somando 17.

## Matriz A/B/C e interpretação

- Relatório automático V4, todos os exemplos: B TP=4, FN=8, FP=6, TN=18; C TP=12, FN=0, FP=6, TN=18. Estes são **escores brutos de software**, afetados por controles malformados.
- Quando apenas controles já confirmados como FHIR válidos são descritos, há 18 negativos válidos sem alerta (12 referências e 6 controles neutros). Excluir os seis defeituosos **após ver o resultado** impede usar 0/18 como taxa confirmatória de falsos alarmes. Este número serve apenas como diagnóstico do defeito.
- Resultado sólido limitado ao piloto: B não identificou 8 mutações semânticas deliberadas; o oráculo C as sinalizou. Isso não implica eficácia clínica, generalização ou adequação do gold.
- RQ3: respostas de origem e destino foram equivalentes nos 12 exemplos de referência; o mecanismo mede equivalência definida pelo próprio benchmark, não validade clínica independente.

## Próxima versão necessária

Criar V5 **separada** corrigindo apenas: (a) neutral com `Bundle.meta.versionId` ou reordenação, sem URL reservada; (b) Bundle sem `entry` quando nenhuma observação foi emitida, com recusa explícita preservada. Manter os mesmos casos e a própria V4 imutável. Como as 18 famílias de avaliação já foram vistas, a V5 será **replicação corretiva pós-inspeção**, não uma nova avaliação cega. Submeter depois uma nova seleção de famílias a auditoria independente de gold, incluindo dados semânticos e FHIR.

## Limitações adicionais

- As famílias são amostra intencional, não amostra probabilística, e variantes de uma família não constituem observações independentes.
- Não há revisão independente humana do gold nem validação clínica.
- Avisos FHIR não são automaticamente erros; `-tx n/a` não verifica terminologias externas.
- Tempo medido na nuvem inclui inicialização de JVM e I/O; não extrapolar como diferença causal de custo entre B e C.
- Discriminar sinalização, recusa e reparação: não houve correção automática de conteúdo semântico.

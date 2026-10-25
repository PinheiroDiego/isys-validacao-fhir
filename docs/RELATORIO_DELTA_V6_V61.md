# Relatório de diferenças V6 → V6.1

Emenda metodológica por adjudicação independente recebida pelo pesquisador em 25/10/2026. A V6 original continua congelada; mudança declarada e pós-revisão, não reinterpretação retroativa.

- Políticas alteradas: G15/G35 sem valor → `dataAbsentReason=unknown`; G35 unidade no `note`, não `valueQuantity`.
- G35 passou de recusa para conversão. Nova mutação `change_orphan_unit_note` modifica apenas unidade textual. G15 mutação inventa valor e remove `dataAbsentReason` para preservar validade estrutural.
- Arquivos FHIR alterados ou criados: **5** (`G15` e `G35` × baseline/neutral/mutation); os outros **93 arquivos FHIR idênticos** ao candidato V6 anterior.
- Confirmatório: **23 famílias convertíveis + 3 recusas**; **72 entradas** (antes 70). Total 31 conversíveis + 5 recusas; **98 entradas** (antes 96). Fonte: **36/41 convertidas**.
- Não executar validadores sobre holdout até ratificação. Nenhum resultado de conformidade oficial da V6.1 foi gerado.
- O componente de teste do conversor foi derivado da V1.1 somente nesta V6.1; o arquivo V1.1 original e os snapshots V5/V6 permanecem preservados.
- Ponto metodológico: a revisão recebida se originou de casos parcialmente descegados; a ratificação não transforma a revisão inicial em estudo cego. Avaliação verdadeiramente confirmatória exigirá nova série não exposta.

## Aproveitamento rastreado da revisão anterior

A planilha original foi lida sem alteração, com 66 julgamentos P/Q/R, quatro recusas e conclusão global `APROVO_COM_RESSALVAS`. Para 24 famílias confirmatórias cujos arquivos foram mantidos exatamente como a V6 original, registrou-se `PRIOR_REVIEWED_WITH_RESSALVAS`; G15 e G35 permanecem `PENDING_DELTA_RATIFICATION`. Os controles de integridade conferem cada arquivo transportado com o ZIP da V6 original. Nenhuma atestação pessoal foi fabricada nem a V6.1 foi liberada automaticamente.

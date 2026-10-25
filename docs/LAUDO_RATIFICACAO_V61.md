# Laudo de ratificação técnica V6.1 — 25/10/2026

## Proveniência

Ficha CSV recebida, preservada integralmente em `review/evidence/FICHA_RESPONDER_RECEBIDA.csv`, **SHA-256 `e855030ed7daf88456ccb1af07dc4ef224f25f1671090c32a5a6dc6072e25934`**. Cabeçalho `Column1..Column6` e valores Latin-1 foram interpretados; original não editado. Na segunda linha a coluna `familia` contém `?`; narrativa cita explicitamente G35, seu controle e unidades `mg/dL`/`g/L`, portanto a adjudicação mapeou **? → G35**, registrando a interpretação separadamente.

## Decisões

- **G15: RATIFICO** — referências e controle omitem `value[x]`, trazem `dataAbsentReason=unknown` e `status=unknown`; mutação inventa 42 e remove `dataAbsentReason` para manter `obs-6`.
- **G35: RATIFICO_COM_RESSALVAS** — conversão parcial aceita, unidade informada só em `note`; mutação troca `mg/dL` para `g/L` como falsa proveniência, sem impacto direto no resultado numérico ausente. O comparador **precisa analisar Annotation.note**; não interpretar a mudança como UCUM.

## Resposta às ressalvas

1. `G35/neutral.json`: `Bundle.id` modificado de `synthetic-control-35` para `batch-35`, apenas metadado não clínico. O especialista não reavaliou esse arquivo **após** essa troca; a correção é ação de engenharia documentada, e **não** nova ratificação individual.
2. Comparação de texto de `Observation.note` é componente explícito de C para essa família (ver `src/semantic_oracle.py`).
3. Na partição confirmatória, 23 famílias convertíveis e três recusas; 72 validações previstas, em 26 famílias; total V6.1 31 convertíveis e 5 recusas.
4. Nomenclaturas do kit de revisão: `P`/`Q`/`R` (identificadores de revisão inicial) vs artefato técnico `baseline`/`neutral`/`mutation`; a ficha de ratificação complementar identifica variantes **por seus nomes técnicos**. Não existe mapa P/Q/R novo para G35 na ficha recebida.

## Integridade

- ZIP da candidata V6.1 congelado: SHA-256 `34caf348ea8f8344b3c8508b9355d71c04467e3d4f5f0fc336478b7da1242934`.
- Dos 98 inputs, somente o arquivo `benchmark/inputs/G35/neutral.json` mudou frente à candidata. Todos os 36 overlays sintéticos, gold e demais 97 arquivos FHIR foram preservados sem alterações.
- A V6 candidata original e os artefatos V5 seguem imutáveis em `historical/`.
- O validador HL7 **ainda não foi executado** para este release.

## Interpretação científica

A revisão foi feita por profissional externo com formação e experiência informadas pelo pesquisador; seu documento não contém assinatura digital e a independência de autoria não foi verificada por fonte autônoma. Parecer com ressalvas, cegamento parcial, mutações intencionalmente construídas. Aprovado para execução técnica confirmatória com tais limitações, **não** para apresentar como nova avaliação duplo-cega ou estimativa populacional de sensibilidade.

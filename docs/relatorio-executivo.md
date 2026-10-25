# Relatório de progresso científico — congelamento V3 / constituição do V4

**Data**: 25 de outubro de 2026.

## Status de execução

| Marco | Estado | Base factual |
|---|---|---|
| Referência experimental V3 | Verificada e congelada por hashes | 16/16 execuções HL7 concluídas; Bundle referência 0 erros; 14 validações sem erros, 2 com erros |
| Integridade do artefato HL7 V3 | Verificada | ZIP SHA-256 `d4012e5bbfdf0a010b659b447037dee8a7d30e51c3f7fc72a9cea00ba6bc125f`; 53 arquivos internos enumerados |
| Ontologia original | Preservada | OWX SHA-256 `54fde32e281df37b79773ca56128ad2526125bc3174717cbb04871750cfd8558`; apenas referências por hash |
| Benchmark sintético V4 | Gerado | 26 famílias, 31 ocorrências de exames, 25 convertidas, 6 recusadas; 66 entradas FHIR |
| Gold V4 | Fixado e versionado | `families.json`, SHA-256 `dec62b7e8e479270d447229946e8bbfd785e269a705be69b204b05766715ba94` |
| Desenvolvimento V4 | Testado | 8 famílias, 24 variantes; 8/8 alterações semânticas sinalizadas e 0/16 falsos alertas de engenharia nos controles/baselines |
| Consultas Q01–Q05 (desenvolvimento) | Executadas | 8/8 baselines e 8/8 controles equivalentes; divergência em 8/8 mutações, em ao menos uma questão |
| Revisão independente do gold | **Pendente** | Avaliador com experiência em FHIR e modelagem clínica |
| Validação HL7 oficial V4 | **Pendente** | Necessário executar workflow ou fornecer CLI JAR com hash correspondente |
| Avaliação reservada V4 | **Pendente** | 18 famílias/42 validações oficiais planejadas (12 conversíveis + 6 recusas) |

## Nota sobre os denominadores

A V4 possui 26 famílias, mas 31 ocorrências de exames nas entradas, pois algumas famílias possuem duas ocorrências. A condição A converteu 25/31 ocorrências sintéticas (80,65%) e recusou 6/31 (19,35%). Esses percentuais descrevem a cobertura de conversão **por construção**, não a qualidade clínica ou a conformidade HL7 das novas saídas. As 20 famílias conversíveis geram 20 baselines, 20 mutações e 20 controles; as seis recusas acrescentam seis baselines. Nas 20 mutações, 16 são semânticas e quatro são controles estruturais.

## Separação de evidências

A execução histórica V3 é evidência oficial HL7. As métricas geradas para V4 até aqui são exclusivamente de engenharia, fonte sintética e checagem própria. O número de validações oficiais V4 é **zero**, e sua taxa de conformidade permanece **indeterminada**, não zero. As regras da avaliação reservada estão fixadas sem analisar seus resultados semânticos neste pacote.

## Próxima ação operacional

Publicar os arquivos do benchmark em repositório privado, executar `.github/workflows/benchmark-v4-hl7.yml` com entrada `scope=evaluation`, preservar o artefato `isys-benchmark-v4-evaluation` e proceder à auditoria de resultados B/C. Um avaliador independente deverá conferir amostras estratificadas e discrepâncias antes da interpretação científica final. A V3 não deve ser substituída por esses resultados.

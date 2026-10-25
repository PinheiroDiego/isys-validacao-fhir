# Errata técnica V4 → V5

Este documento não apaga os resultados V4. V4 permaneceu congelada, e os 12 ajustes sobre a partição F09–F26 geraram hashes novos no manifesto V5.

## Fonte, defeito e tratamento

| Casos | Defeito V4 | Ajuste V5 | Escopo alterado |
|---|---|---|---|
| F10, F12, F14, F16, F18 e F20, variante `neutral` | Validador rejeitou `Bundle.meta.tag.system=https://example.org/isys/benchmark/metadata` (`Example URLs are not allowed...`) | `Bundle.meta.versionId='synthetic-control-v5'`, sem `meta.tag.system` | Apenas metadado administrativo do Bundle |
| F21–F26, variante `baseline` recusada | `Bundle.entry: []` rejeitado como array vazio | Propriedade `entry` omitida | Apenas serialização de ausência, sem emissão de `Patient` ou `Observation` |

Foram preservadas todas as 8 mutações semânticas, 4 negativas estruturais e os 12 Bundles de referência aceitos. A restrição de conformidade computável FHIR permanece independente da correção semântica.

## Antes de atribuir os indicadores ao artigo

1. Executar a V5 oficial e verificar `OperationOutcome` de 42 casos.
2. Registrar os resultados brutos V4, inclusive seis controles formalmente inválidos e seis recusas representadas com Bundle inválido.
3. Interpretar V5 como replicação corretiva **posterior ao acesso aos resultados da avaliação V4** — não é blind holdout.
4. Não confundir avisos de boas práticas com erros do HL7: B sinaliza `error|fatal`, conforme protocolo.
5. Relatar 15/21 de cobertura no A e seis recusas separadamente. Um Bundle vazio pode ser estruturalmente válido sem representar dados de origem.
6. Obter revisão independente das regras e do gold, e definir novas famílias para teste externo antes de inferências de efetividade generalizável.

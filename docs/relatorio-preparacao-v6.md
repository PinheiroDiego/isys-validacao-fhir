# Laudo de preparação — iSys V6 confirmatório candidato

**25/10/2026 — sem execução oficial HL7 V6, sem aprovação humana do gold.**

## Evidências de execução local

- Preparadas **36 famílias novas (G01–G36)**, separadas das famílias V4/V5 F01–F26; 30 conversíveis + 6 de recusa.
- **41** ocorrências de exame; **35** emitidas pelo conversor e **6** recusadas conforme política explícita. São dados de teste sintéticos, não resultados de experimentos clínicos.
- **96** `Bundle` FHIR preparados: 26 de desenvolvimento e **70 confirmatórios reservados**.
- Integridade verificada por SHA-256 para 96 JSON, 36 OWL/XML, o gold e três ZIP históricos V5.
- Hash ZIP da ontologia fonte: `1784b46046ecbb38e3fa9e5259ff04aa50138226396040bfd85a89d42ce3d4e2`.
- Hash do `marco.owx` interno: `54fde32e281df37b79773ca56128ad2526125bc3174717cbb04871750cfd8558`.
- **14 testes automatizados aprovados**.
- Avaliação **restrita ao desenvolvimento**: oito referências e oito controles equivalentes não sinalizados como divergentes; cinco mutações semânticas detectadas pelo comparador. As três mutações estruturais do desenvolvimento **não receberam validação HL7 nesta sessão**.
- Cronometragem preliminar para verificar instrumentação no desenvolvimento: quatro aquecimentos, 12 repetições por variante, 24 variantes conversíveis; mediana descritiva por família disponível em `outputs/metrics_v6/development/incremental_C_timing.json`. O workflow oficial usa 12 aquecimentos e 45 repetições, não sendo adequado comparar seus valores como replicações com o ensaio de instrumentação.
- Gate de revisão humana: `BLOCKED` conforme esperado, sem arquivo de aprovação.

## Fatos ainda não demonstrados

Não foram executados HL7 Validator na V6, avaliação de desempenho do conjunto confirmatório, adjudicação de referência esperada, validação clínica, validação de perfil nacional ou análise populacional. O benchmark foi desenvolvido com assistência de IA, e a revisão independente por especialista FHIR é condição necessária, não presumida.

## Critérios para iniciar confirmação

Obter revisão caso a caso (`review/decisions.csv`) das 26 famílias confirmatórias, validar identidade e expertise do avaliador externamente, registrar parecer assinado/atestado (`review/attestation.json`), não modificar o gold nem as entradas após análise, executar `verify_v6.py` e `review_gate.py`, e só então acionar `scope=confirmatory` no GitHub Actions. Se houver reprovação, gerar uma nova versão candidata antes de executar, sem reescrever V6.

## Interpretação pretendida

Principal: detecção B versus C pareada **por família** das variantes com defeito deliberado, apresentada como frequência descritiva. Secundários: falsos alarmes em `baseline`/`neutral`, recusas e cobertura A, equivalência Q01–Q05, perdas Q06, tempos oficiais separados do custo incremental C. Cargas válidas somente se baseline oficial da própria família apresentar zero erros; bloqueio/exclusões contabilizados, não ocultados.

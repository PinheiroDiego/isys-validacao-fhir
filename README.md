# iSys — V3 congelada + benchmark científico V4

Pacote criado em **25/10/2026**. Não inclui a ontologia original nem dados clínicos reais.

## Conteúdo

- `baseline_v3/hl7_official_v3.zip`: artefato **original e intocado** da segunda execução GitHub Actions; hashes individuais de 53 arquivos em `frozen_manifest.json`.
- `baseline_v3/v3_validation_inputs.zip`, `v3_audit.zip`, `converter_v1_1.zip`: cópias dos insumos históricos, também registradas por hash.
- `vendor/isys_converter`: código V1.1 copiado sem alterações; verificado contra o ZIP.
- `benchmark/gold/families.json`: 26 famílias sintéticas com metadados de desenvolvimento (8) e avaliação (18).
- `benchmark/fixtures/overlays/Fxx.owx`: arquivos OWL/XML puramente fictícios, criados sob namespace separado.
- `benchmark/inputs/Fxx`: Bundle de referência e, quando conversível, uma mutação e um controle equivalente. **66 entradas** para HL7.
- `benchmark/manifest_v4.json`: hashes de todas as entradas, overlays e documento gold.
- `src/semantic_oracle.py`: comparação de valores, contexto paciente–exame, precisão temporal, duplicações e ausências, sem importar o conversor.
- `src/run_hl7_v4.py`: executor oficial e registros integrais de operação, códigos de retorno e stdout/stderr.
- `src/analyze_results.py`: métricas A/B/C com condições de interpretabilidade e falsos alarmes.
- `docs/protocolo-cientifico-v4.md`: protocolo pré-fixado e limites metodológicos.

## Testes locais já realizados

`python3 src/verify_freeze.py` -> **PASS**.

`python3 -m unittest discover -s tests -v` -> **14 testes aprovados**.

`python3 src/semantic_oracle.py --split development` -> **24 variantes avaliadas localmente**; 8 mutações semânticas detectadas, 0 divergências indevidas nas 16 variantes sem falha.

**Nenhum dos 66 arquivos V4 foi validado pelo HL7 oficial neste ambiente.** Não há taxa de conformidade oficial V4. A parte de avaliação (18 famílias/42 entradas) ainda não foi pontuada pelo comparador V4, para evitar ajuste da implementação aos casos reservados.

## Como executar a validação oficial sem instalação local

Crie ou utilize um **repositório privado separado** no GitHub e envie o conteúdo descompactado do ZIP, mantendo `.github/workflows/benchmark-v4-hl7.yml`.

Em **Actions → iSys - Benchmark V4 HL7 oficial → Run workflow**, escolha `evaluation` (**42 validações**), `development` (**24**) ou `all` (**66**). O workflow usa Java 21, baixa o JAR **7.0.3**, verifica seu SHA-256 e roda o core FHIR R4 **4.0.1**, sem serviço remoto de terminologias (`-tx n/a`).

Baixe o artefato chamado `isys-benchmark-v4-evaluation` (ou `...-all`). Ele conterá `OperationOutcome` por caso, logs, sumário da execução e, quando todos os casos forem executados, a matriz A/B/C calculada automaticamente.

**Se um baseline estiver inválido, os resultados diferenciais daquela família serão excluídos das taxas e explicitamente listados como não interpretáveis.** Não corrija o gold nem remova a família depois de ver os resultados; preserve V4 e versão V5 caso sejam necessárias modificações.

## Reprodutibilidade da origem privada

A partir da ontologia original autorizada, é possível reconstruir os overlays e entradas pelo comando `python3 src/assemble.py --original <caminho_para_ontologia_original.zip>`. O arquivo original é verificado por SHA-256 antes do processamento e não entra no pacote final. Os arquivos de entrada já estão prontos para a validação no GitHub; **não é necessário enviar a ontologia original ao GitHub**.

Apenas casos sintéticos são utilizados. A validação oficial produz evidências de **conformidade aos perfis-base**, não de eficácia clínica, terminologia clínica padronizada ou funcionamento em hospital.

## Perguntas de competência

`src/competency_v4.py` implementa consultas Q01–Q05 separadamente sobre as asserções OWL/XML e as instâncias `Bundle` FHIR, além do inventário de perdas e recusas Q06. Sem importar o conversor ou ler seu rastreamento, compara multiconjuntos de pacientes/exames, resultados, datas (com precisão), unidades e pertinência temporal trivalorada. No grupo de **desenvolvimento**, 8/8 baselines e 8/8 controles equivalentes preservaram as respostas Q01–Q05; as 8/8 mutações semânticas causaram ao menos uma divergência. Isso não é uma avaliação independente nem uma taxa de generalização.

Quando a avaliação oficial for concluída, `src/analyze_results.py` incorpora a equivalência das consultas por variante à matriz A/B/C.

# iSys — Benchmark V5: replicação corretiva dos controles V4

**Data:** 25/10/2026. **V5 não substitui a V4 e não é nova avaliação cega.**

Este pacote contém o benchmark V4, seus hashes históricos, sua avaliação oficial recebida (mantida byte a byte em `provenance/isys-benchmark-v4-evaluation-original.zip`), e **42 entradas V5** da partição de avaliação. Só existem **12 correções técnicas nas entradas**:

1. `F10_neutral`, `F12_neutral`, `F14_neutral`, `F16_neutral`, `F18_neutral`, `F20_neutral`: a URI reservada de exemplo em `Bundle.meta.tag.system` foi substituída por `Bundle.meta.versionId` de teste, sem alterar qualquer paciente, exame, resultado ou referência clínica. A URI anterior produzia erros oficiais nos controles pretendidos como equivalentes.
2. `F21_baseline` ... `F26_baseline`: foram omitidas as propriedades `Bundle.entry` que continham arrays vazios; não foi criada nenhuma informação clínica. Essas seis famílias continuam sendo **recusas na etapa A**, e os Bundles vazios não devem contar como casos convertidos nem como observações da etapa B/C.

As outras **30 entradas V5** são cópias byte a byte das entradas originais V4. O gold V4, os overlays OWL/XML, o conversor V1.1 congelado e o baseline V3 permanecem inalterados. O arquivo `benchmark/manifest_v5.json` registra o SHA-256 de cada caso e o hash da execução V4 original, com declaração expressa da limitação pós-inspeção. Os hashes V4 são verificados no início do workflow.

## Executar no GitHub Actions

No mesmo repositório privado da V4, substitua os arquivos pelo conteúdo descompactado deste ZIP (preservando a estrutura e a pasta `.github`). Na aba **Actions**, escolha **iSys - Benchmark V5 corrective rerun FHIR R4**, clique em **Run workflow**. Após a execução, baixe **isys-benchmark-v5-corrective** na seção Artifacts e anexe o ZIP ao ChatGPT.

A execução roda **42 validações oficiais** com HL7 Validator CLI 7.0.3, SHA do JAR fixado, FHIR R4 4.0.1, Bundle base profile e `-tx n/a`. O validador grava todo `OperationOutcome`, stdout/stderr e tempo por caso; `src/analyze_v5.py` compara A/B/C somente quando as referências são conformes. As seis recusas de A aparecem em seção própria. Não há correção automática de semântica.

## Conferência local realizada

- `python3 src/verify_v5.py` — **PASS**; 42 hashes, 12 alterações explicitadas; verifica congelamento V4.
- `python3 -m unittest discover -s tests -q` — **21 testes aprovados**.
- Comparador de significado local — 8 mutações semânticas sinalizadas; 12 controles equivalentes e 12 baselines sem divergências (não substitui HL7).

**A execução HL7 oficial da V5 ainda não ocorreu.** Os problemas de validade formal dos metadados e do Bundle vazio só serão considerados resolvidos quando a V5 for revalidada pelo HL7 oficial. A repetição usa famílias de avaliação V4 já analisadas, por isso é uma **replicação técnica de correção de artefatos**, não resultado de avaliação independente nova.

## Limites para publicação

O estudo é sintético e construído intencionalmente. O gold foi preparado com apoio de IA, sem adjudicação humana independente. A ontologia original não é redistribuída. Não há validação de terminologias externas, perfis brasileiros, eficácia clínica ou ambiente hospitalar. Recomenda-se avaliação adicional com casos inéditos e revisor com experiência em FHIR antes de declarar precisão de detecção generalizável.

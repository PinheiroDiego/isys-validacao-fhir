# iSys — V6: benchmark confirmatório *candidato*, com aprovação externa obrigatória

**Data de preparação:** 25/10/2026. **Status:** artefatos preparados, *gold* não revisado por especialista, execução oficial HL7 V6 **não realizada**. A V5 foi encerrada como replicação corretiva histórica e não é alterada.

## Evidência versus preparação

- **Histórico V5**: `historical/v5-source-unaltered.zip`, `historical/v5-official-artifact-unaltered.zip` e `historical/v5-audit-unaltered.zip`, todos preservados com SHA-256 no `benchmark/manifest_v6.json`. A V5 **não** é tratada como replicação cega independente.
- **Novo V6**: 36 famílias de origem sintética G01–G36, distintas das famílias F01–F26; 30 conversíveis, 6 com recusa esperada; 41 ocorrências de exame (35 convertidas, 6 recusadas); **96 entradas FHIR** em `benchmark/inputs/`.
- **Desenvolvimento**: G01–G10, 8 famílias conversíveis + 2 recusas e 26 entradas. Apenas esta partição foi testada/consultada localmente.
- **Confirmatório reservado**: G11–G36, 22 conversíveis + 4 recusas e **70 entradas**. Elas foram geradas e tiveram integridade de arquivos conferida, mas **não foram pontuadas nem validadas oficialmente** nesta preparação.
- **Fonte**: ontologia original `ontologia-cbms-ontologies.owx.zip` consultada para verificar declarações; não distribuída. Hash SHA-256 ZIP `1784b46046ecbb38e3fa9e5259ff04aa50138226396040bfd85a89d42ce3d4e2`. Hash do `marco.owx` interno `54fde32e281df37b79773ca56128ad2526125bc3174717cbb04871750cfd8558`. Nenhum dos dois foi modificado.
- **FHIR fixado**: versão R4 4.0.1, pacote `hl7.fhir.r4.core#4.0.1`, perfis-base de `Bundle`, `Patient` e `Observation` (validação do Bundle e suas entradas), CLI 7.0.3 com SHA fixado, `-tx n/a`. Não são perfis brasileiros nem validação terminológica completa.

## Novidade e valor metodológico

Famílias novas incluem valores numéricos quase iguais, resultados textuais com negação, pacientes diferentes com exames homônimos, duplicação com **nova identidade FHIR válida**, datas com precisão parcial, informação inventada ou omitida, troca entre valores/datas de exames, escolha `value[x]` duplicada, elemento inesperado e alterações FHIR estruturalmente inválidas. Cada família gera uma referência, um controle equivalente e uma mutação; recusas são avaliadas separadamente. **Não multiplicar variantes como unidades amostrais independentes.**

## Estrutura

- `benchmark/gold/families.json` — casos e referência esperada declarados antes da execução oficial, **AI-assisted, ainda sem revisão externa**.
- `benchmark/fixtures/overlays/Gxx.owx` — extensões sintéticas OWL/XML no namespace de teste, sem modificar a ontologia original.
- `benchmark/inputs/Gxx/` — FHIR `baseline.json`, `neutral.json`, `mutation.json` quando aplicáveis.
- `benchmark/manifest_v6.json` — SHA de gold, arquivos OWL, 96 entradas e 3 arquivos históricos V5.
- `vendor/isys_converter/` — conversor V1.1 congelado, sem retreinamento.
- `src/verify_v6.py`, `src/run_official_v6.py`, `src/analyze_v6.py` — auditoria e executor oficial.
- `src/semantic_oracle.py`, `src/competency_v4.py` — verificações independentes do conversor e consultas Q01–Q05/Q06.
- `src/time_semantic_v6.py` — custo incremental local da condição C, sem confundir com tempo de inicialização do Java.
- `review/decisions.csv`, `review/attestation.json` — revisão humana pendente; o gate de confirmação falha enquanto não aprovada.
- `.github/workflows/isys-v6-hl7.yml` — pipeline GitHub Actions por acionamento manual.

## Status de testes de engenharia desta preparação

`python3 src/verify_v6.py` → PASS: três arquivos históricos, 36 overlays e 96 entradas verificados.

`python3 -m unittest discover -s tests -v` → **14 testes aprovados** (somente indicadores de desenvolvimento).

`python3 src/dev_smoke.py` → oito baselines e oito controles equivalentes sem divergência, cinco mutações semânticas sinalizadas no desenvolvimento. **Não é execução HL7**.

`python3 src/time_semantic_v6.py --scope development` → teste de instrumentação de custos, não medição confirmatória.

`python3 src/review_gate.py` → **BLOCKED (esperado)**: especialista ainda não revisou o *gold*.

## Próxima ação mínima

1. Enviar ao especialista em FHIR **somente** `review/brief_para_especialista.md`, `review/decisions.csv`, o arquivo `benchmark/gold/families.json`, overlays e Bundles correspondentes (todos sintéticos). Preferencialmente revisão cega à saída dos detectores B e C.
2. O especialista preenche sua revisão; divergências exigem adjudicação documentada **em uma nova versão antes da execução confirmatória**, jamais substituir silenciosamente o gold V6 congelado.
3. Após receber a revisão humana, preencher/assinar `review/attestation.json` preservando a identificação do revisor em registro privado. A integridade é conferida por `src/review_gate.py`, mas o software **não autentica a identidade humana**.
4. Executar em repositório privado `Actions → iSys V6 - HL7 Confirmatory Benchmark → Run workflow` com `scope=confirmatory` (**70 validações**). Este modo não roda enquanto a documentação da revisão estiver pendente.
5. Anexar o ZIP de resultado `isys-v6-confirmatory-hl7` para auditoria. Qualquer falha de baseline invalida contraste daquela família em B/C; a família permanece reportada como não interpretável.

Há também modo `development`, para 26 validações técnicas sem a aprovação externa; não converter resultados de desenvolvimento em confirmações.

## Restrições

A V6 não é amostra aleatória, não demonstra eficácia clínica nem generalização a hospitais. Os resultados anteriores da V5 seguem publicados como piloto sintético corretivo. O *gold* inicialmente elaborado com IA **não pode ser apresentado como revisado por profissional** antes da adjudicação real. O custo da condição C é medido separadamente do HL7 oficial; comparar Java por processo com Python aquecido diretamente seria metodologicamente inadequado.

# Pré-registro V7 — versão final consolidada (r1 + emendas 1–6 + emenda A1)

**Estado:** TEXTO FINAL PARA CONGELAMENTO. Só passa a valer como pré-registro depois do commit no repositório que contenha este arquivo e o `v7/FREEZE_V7.json` com o hash correspondente.
**Aprovação:** r1 aprovada pelo pesquisador com as seis emendas; H3 transferida para a V7.1 (decisão de 25/10/2026). Emenda A1 incorpora o parecer de auditoria pré-commit de 25/10/2026 (seção 13), sem alteração de hipóteses, previsões, famílias ou operadores.
**Natureza:** teste de estresse especificado prospectivamente sobre acoplamentos de representação identificados previamente por inspeção de código. Não é descoberta cega nem estimativa de desempenho clínico.
**Histórico:** V3, V5, V6 e V6.1 permanecem imutáveis. A V7 não reestima nenhum resultado anterior.
**Uso de IA:** protocolo, apêndice e código V7 elaborados com assistência do Claude (Anthropic), revisados pelo pesquisador; o texto r1 foi proposto com assistência de outra ferramenta de IA. Ambos devem constar na declaração de uso de IA do artigo.

---

## 1. Motivação

Na V6.1, os 23 controles neutros variavam `Bundle.id` (9), `meta.versionId` (7) ou a ordem de `entry` (7), sem transformar a representação do conteúdo; 15 continham marcador textual "control". A inspeção de `competency_v4.py` indicou dependência de: (i) IDs FHIR determinísticos derivados dos IRIs; (ii) referência relativa `Patient/<id>`; (iii) igualdade textual byte a byte, sem normalização Unicode. As recusas da V6.1 voltaram ao formato `entry: []`, que a V5 havia corrigido.

A V7 testa a resistência do instrumento congelado da V6.1 a transformações que preservam os fatos **sob o contrato Q01–Q05**, embora não preservem necessariamente identidade operacional externa, proveniência persistente ou toda a semântica FHIR. Também testa a correção da serialização de recusas.

## 2. Artefatos e versões (congelados)

| Papel | Arquivo | SHA-256 |
|---|---|---|
| Conversor efetivamente usado na V6.1 (não a V1.1 histórica) | `vendor/isys_converter/transform.py` | `47cc34038867ba6d30d04d39216062b306e670cb72d961e51690d6d60ba9ea71` |
| Esquema/leitura de overlays | `vendor/isys_converter/schema.py` | `97aaa8d60f8ebddbcfc0c36c0b0664e30cb0fc9ca944de976bbcef70f084ec9a` |
| Escritor de overlays | `src/overlay_components.py` | `52a45d5d020825f71d96db96d66df9f88e65fe73b541e08a333550fa76518bac` |
| Operadores de mutação V6.1 (`mutate`) | `src/build_v6.py` | `03b4c145c73cfce041888b801a3721c3f903f7c0ec514e292f687c17bd9efecd` |
| Consultas Q01–Q05 (com patch de recuperação) | `src/competency_v4.py` | `3de19be71c80f11b7d6b822eb1fed01aaeee28673aa7614c1b8a2d702d1eda12` |
| Oráculo orientado pelo gold | `src/semantic_oracle.py` | `5327048130d0867fb280d47e1b66e472d7d89303d53a3039c798695abf364d6b` |
| Análise V6.1 (referência, não executada na V7) | `src/analyze_v6.py` | `75e807c77d81624ba88638185a0db53213188c41ff31f6391593700809b47346` |

A V1.1 histórica (`transform.py` SHA-256 `abdc941d4811dc487a3580f73f03a183abf737652d0eda9390bf7eff122ac420`) não é usada: ela recusa unidade sem resultado e reabriria a adjudicação G15/G35.
Observação de proveniência: `RELEASE-SHA256.json` da entrega V6.1 registra os hashes **anteriores** ao patch de `competency_v4.py` e `analyze_v6.py`; os hashes acima são os das versões com patch, idênticas às do laudo de recuperação.

**Ontologia de origem (B4):** ZIP `1784b46046ecbb38e3fa9e5259ff04aa50138226396040bfd85a89d42ce3d4e2`, com `marco.owx` interno `54fde32e281df37b79773ca56128ad2526125bc3174717cbb04871750cfd8558`. Ambos estão fixados no `FREEZE_V7.json` e são conferidos por `build_v7.py` antes de qualquer cálculo de cenário ou criação de overlay.

**Validação formal:** HL7 Validator CLI 7.0.3 (JAR `57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b`), FHIR R4 4.0.1, `hl7.fhir.r4.core#4.0.1`, Java 21, perfil-base `Bundle`, `-tx n/a`, Python 3.11 no runner.

**Código V7 (apêndice):** os hashes de todos os arquivos V7 estão em `v7/FREEZE_V7.json`, verificado por `v7/src/verify_v7.py` antes de cada etapa.

## 3. Condições

- **B:** alarme se o `OperationOutcome` oficial tiver ao menos um item `error` ou `fatal`. Avisos não contam.
- **C:** alarme se B **ou** o oráculo orientado pelo gold (`semantic_oracle.compare`) **ou** qualquer consulta Q01–Q05 (`competency_v4.compare_queries`) indicar divergência — definição idêntica à da V6.1. O componente que disparou cada alarme é registrado e relatado separadamente.

## 4. Hipóteses e previsões

**H1 — controles equivalentes difíceis.**

| Tipo | Operação (apêndice B) | Fundamento de equivalência sob Q01–Q05 | Previsão B | Previsão C |
|---|---|---|---|---|
| N1 narrativa gerada | `text.status=generated` e `div` XHTML com apenas os campos estruturados já presentes, em Patient e Observation | Não acrescenta fatos | 0 erros | sem alarme |
| N2 reidentificação coerente | IDs lógicos opacos para Patient/Observation; `fullUrl` e referências reconstruídos | Grafo de fatos isomorfo sob renomeação; identidade operacional externa fora do contrato | 0 erros (a verificar) | alarme |
| N3 referência absoluta | `subject.reference` = `fullUrl` exato do Patient no Bundle | Mesmo destino de referência | 0 erros (a verificar) | alarme |
| N4 Unicode | NFC→NFD apenas em `Observation.code.text` e `Observation.valueString` (emenda 3) | Equivalência canônica Unicode | 0 erros | alarme nas famílias com acento |

N4 é desafio efetivo apenas em H01, H02, H03, H05, H06 e H08. Em H04 e H07 (sem acentos), o arquivo N4 é idêntico ao de referência e é relatado como **não aplicável**, fora do denominador.

**Exclusões deliberadas** (não equivalentes sob FHIR ou sob o contrato): data → dateTime com hora/fuso (acrescenta precisão); `5` → `5.0` (em `decimal`, zeros finais expressam precisão); acréscimo de `category`, UCUM ou LOINC (informação sem suporte na origem).

**H2 — serialização de recusas.** As recusas H09–H11 são serializadas como Bundle `collection` **sem a propriedade `entry`** (forma da V5). Previsão: 0 erros HL7 nas 3. O motivo da recusa é registrado à parte (`v7/private/refusal_records.json`, com os motivos emitidos pelo conversor); o Bundle vazio não é tomado como evidência do motivo.

**Controle de sanidade.** Uma mutação semântica por família H01–H08, com operadores da V6.1 congelados. Previsão: B 0/8 e C 8/8, **desde que** a mutação seja formalmente válida; mutante com erro HL7 é relatado como falha de desenho e excluído da subanálise estritamente semântica.

**H3** (alinhamento sem o gold) foi **transferida para a V7.1** e não faz parte desta versão.

## 5. Famílias, volume e regras de aplicabilidade

8 famílias conversíveis (H01–H08) × 6 variantes (referência, N1, N2, N3, N4, mutação) + 3 recusas (H09–H11) = **51 arquivos submetidos ao validador**. Há 32 instâncias de controle e 30 desafios não triviais. Nenhum indivíduo dos conjuntos F ou G é reutilizado.

| Família | Pacientes / exames | Característica | Acento em campo-alvo | Mutação (V6.1) |
|---|---|---|---|---|
| H01 | 2 / 2 | Exame numérico em cada paciente | sim | `wrong_existing_patient` |
| H02 | 1 / 2 | Dois exames, nomes e valores distintos | sim | `swap_numeric_values` |
| H03 | 1 / 1 | Numérico com unidade | sim | `change_unit` |
| H04 | 1 / 1 | Numérico, data completa | não | `shift_day` |
| H05 | 1 / 1 | Nome acentuado | sim | `rename_exam` |
| H06 | 1 / 1 | Sem resultado, `dataAbsentReason=unknown` | sim | `invent_numeric_value` (remove `dataAbsentReason`, respeita `obs-6`) |
| H07 | 1 / 1 | Numérico | não | `duplicate_new_identity` (`id` e `fullUrl` únicos) |
| H08 | 1 / 1 | Resultado textual | sim | `flip_negation` |
| H09 | — | Evolução sem paciente | — | recusa `NO_PATIENT_LINK` |
| H10 | — | Dois resultados na mesma ocorrência | — | recusa `MULTIPLE_RESULT` |
| H11 | — | Data `2026-02-30` (fixa) | — | recusa `AMBIGUOUS_OR_INVALID_DATE` |

Regras de aplicabilidade, verificadas por `v7_spec.check_constraints` (falha fechada): H01 com dois pacientes e nomes distintos; H02 com nomes e valores distintos; unidade de H03 ≠ `outra-unidade`; data de H04 ≠ `2026-07-11`; nome de H05 ≠ `Neutrófilos`; H06 sem valor e sem unidade; resultado de H08 ∉ {`com achados`, `com crescimento`}; dois valores distintos em H10; nomes acentuados nas seis famílias N4 e sem acento em H04/H07.

## 6. Apêndice A — sementes, algoritmo e listas (arquivo `v7/src/v7_spec.py`)

- **Semente:** `ISYS-V7-2026-10-25-PREREGISTRO`.
- **Algoritmo:** SHA-256 em modo contador, sem gerador pseudoaleatório da biblioteca padrão (independente de versão do Python). `h = int(SHA256(UTF-8(semente|r1|…|rk)),16)`; escolha = `L[h mod |L|]`. Para dois distintos: `i = h(…,'a') mod n`; `j = (i + 1 + h(…,'b') mod (n−1)) mod n`. A ordem dos nomes opacos `V7-001…V7-051`, os pares do kit e o lado A/B usam o mesmo esquema com rótulos `ordem`, `par`, `lado`, `recusa`. Os IDs de N2 são `r` + 31 primeiros hexadecimais de `SHA256(semente|N2|tipo|id)`.
- **Listas fixadas:**
  - exames numéricos acentuados: Ácido úrico; Ácido fólico; Cálcio iônico; Fósforo; Potássio; Sódio; Magnésio; Ferro sérico; Albumina sérica; Proteína total;
  - exames numéricos sem acento: Ferritina; Creatinina; Ureia; Hemoglobina; Plaquetas; TSH; CEA; PSA;
  - exames textuais acentuados: Citologia oncótica; Biópsia de pele; Pesquisa de células neoplásicas;
  - resultados textuais: sem alterações; sem crescimento; negativo para malignidade;
  - valores decimais (sem zeros finais): 3.4; 4.2; 5.7; 6.1; 7.3; 8.8; 9.4; 12.6;
  - unidades: mg/dL; mmol/L; g/dL; U/L; ng/mL;
  - datas: 2026-01-14; 2026-01-27; 2026-02-09; 2026-02-23; 2026-03-10; 2026-03-24; 2026-04-07; 2026-04-21; 2026-05-05; 2026-05-19; 2026-06-02; 2026-06-16.
- **Regra de não seleção post hoc:** os valores da V7 são calculados uma única vez, por `build_v7.py`, após o commit de congelamento. Antes disso, `build_families` só foi executada com sementes alternativas de teste (`TESTE-ALTERNATIVO-n`), para verificar as restrições.

## 7. Apêndices B–E — código

- **B** `v7/src/v7_operators.py`: N1–N4 e `serialize_refusal`.
- **C** `v7/src/build_v7.py`: geração única; exige `verify_v7 --phase protocol`, árvore git limpa e `FREEZE_V7.json` commitado; registra o commit no manifesto; nunca sobrescreve; gera entradas opacas, gold, mapa, registros de recusa e kit de revisão.
- **D** `v7/src/run_official_v7.py`: 51 invocações oficiais; exige `verify_v7 --phase reviewed`; preserva saídas brutas; não executa o comparador.
- **E** `v7/src/analyze_v7.py`: análise pré-registrada (seção 9); usa o comparador V6.1 sem modificação; erros de análise são registrados por variante, nunca silenciados.
- `v7/src/verify_v7.py`: verificação de integridade por fase, incluindo completude das fichas (B1) e integridade do kit entregue (B2).
- `v7/src/check_custody_v7.py`: custódia pela história Git, executada no workflow antes do validador e do comparador (R2).
- `v7/.gitattributes`, `v7/.gitignore`, `benchmark/fixtures/overlays/.gitattributes`, `benchmark/fixtures/overlays/.gitignore`: preservação de bytes (B3) e bloqueio de publicação antecipada (R1).
- `v7/tests/`: 22 testes — operadores sobre Bundle de brinquedo; restrições com sementes alternativas; fumaça do pipeline com famílias fictícias T00/T01 (ignorado sem a ontologia original); gate das fichas (ausência, duplicação, ID extra ou trocado, veredito vazio ou fora do domínio, justificativa obrigatória, CRLF/BOM); ZIP do kit determinístico e adulteração; ontologia fixada; preservação de CRLF com e sem a política Git; bloqueio do material privado; custódia correta e três violações; erro de análise fora do denominador. Nenhum teste usa casos V7, o validador ou o comparador.
- `.github/workflows/isys-v7-hl7.yml`: workflow novo; não executa suítes legadas sobre dados V7.

## 8. Sequência obrigatória

0. **Commit de congelamento** deste pré-registro, do apêndice e do `FREEZE_V7.json`. Nenhum caso V7 é gerado, validado ou submetido ao comparador antes desse commit.
1. **Geração** (`build_v7.py --original <ZIP>`, uma única vez) e registro dos hashes no `manifest_v7.json`, inclusive do ZIP de entrega do kit (`v7/review_kit_V7.zip`, determinístico). Commit imediato **apenas** de `v7/benchmark/` (manifesto e 51 entradas opacas). Gold, mapa, chave do kit, registros de recusa, overlays H01–H11, diretório e ZIP do kit são ignorados pelo Git e permanecem fora do repositório até a etapa 3; seus hashes já constam do manifesto.
2. **Envio do kit**: o arquivo `v7/review_kit_V7.zip`, com SHA-256 igual ao do manifesto, é enviado à especialista, com registro da data, sem previsões, resultados, gold ou mapeamento. Nem o comparador nem o validador são executados sobre a V7 antes do congelamento do parecer (emenda 2).
3. **Congelamento do parecer**: fichas recebidas sem edição (bytes preservados) em `v7/review/`; `attestation_v7.json` com hashes das fichas, hash do ZIP do kit entregue, datas e commit de geração. Um único commit adiciona o parecer e, com `git add -f`, os arquivos privados, os overlays e o ZIP do kit. `verify_v7 --phase reviewed` exige 38 pares e 3 recusas, conjunto exato de IDs, sem duplicatas, vereditos no domínio e justificativa nos vereditos não favoráveis. Exclusões decorrem mecanicamente da seção 9.
4. **Execução** do workflow V7: `check_custody_v7.py` exige protocolo < geração < parecer ≤ HEAD, material privado adicionado somente no commit do parecer ou depois, e nenhuma saída V7 versionada; em seguida, HL7 Validator e comparador V6.1 congelado.
5. **Publicação** integral: alarmes indevidos, controles inválidos, exclusões pela revisão, previsões não confirmadas e eventuais falhas do job, com o estado original preservado.

Se a revisão especializada não ocorrer, o `attestation_v7.json` registra `NOT_PERFORMED` **antes** da etapa 4, e o artigo declara a ausência de adjudicação externa da V7.

## 9. Elegibilidade, denominadores e critérios de interpretação

1. **Referência não conforme:** se o arquivo de referência de uma família tiver erro HL7, todas as variantes da família ficam não interpretáveis, registradas com o motivo.
2. **Controle inválido:** controle com erro HL7 próprio é relatado como **controle inválido**, com numerador e denominador, e não entra na contagem de alarmes indevidos. Nenhum arquivo é substituído.
3. **Parecer da especialista (emenda 1):** controle julgado `NAO_EQUIVALENTE` ou `INCERTO` sai do denominador de alarmes indevidos **nos dois sentidos** (um alarme não conta como falso alarme; a ausência de alarme não conta como acerto) e é relatado à parte com o veredito.
4. **Tabela principal, por tipo N1–N4:** controles válidos e interpretáveis (denominador), famílias com alarme C, componente que disparou (oráculo, Q01–Q05 ou ambos), controles inválidos, excluídos pela revisão e não aplicáveis. Para N4, denominador máximo de 6.
5. **Rótulos de interpretação** (calculados por `analyze_v7.py`):
   - tipo com previsão de alarme (N2–N4): `PREVISAO_CONFIRMADA` se C alarmar em todos os controles válidos; `CONFIRMACAO_PARCIAL` se em parte; `PREVISAO_NAO_CONFIRMADA` se em nenhum;
   - tipo com previsão de ausência de alarme (N1): `PREVISAO_CONFIRMADA` se nenhum alarme; `CONFIRMACAO_PARCIAL` se algum; `PREVISAO_NAO_CONFIRMADA` se todos;
   - `SEM_CONTROLES_VALIDOS` se o denominador for zero.
   As contagens reais são sempre relatadas; resultado parcial não é apresentado como confirmação.
6. **H2:** confirmada se as 3 recusas tiverem 0 erros HL7. Avisos e veredito da revisão sobre a justificativa da recusa são relatados à parte; um veredito `NAO_JUSTIFICADA` não altera H2, que trata da serialização.
7. **Referências:** qualquer alarme C em arquivo de referência é relatado como achado.
7a. **Erros de análise (R3):** variante cujo comparador falhar é relatada na categoria `erro_de_analise`, fora dos denominadores; nunca é contada como ausência de alarme ou de detecção.
8. **Dependência:** as seis variantes de uma família são dependentes. Não há testes inferenciais, reamostragem, percentuais agregados entre tipos nem combinação com V3/V5/V6.1.
9. Não se relata "taxa de falso positivo populacional", "robustez clínica" nem "validação cega".
10. Um alarme indevido confirmado é tratado como **achado do artigo** sobre requisitos de um verificador implantável (chave de proveniência, canonicalização), nunca como correção silenciosa. Correções do verificador só podem ser avaliadas em versão posterior, com protocolo e famílias novos.

## 10. Revisão especializada e cegamento

- **Conteúdo do kit:** pares A/B com nomes opacos (`P01`…), ordem e lado definidos pelo algoritmo do apêndice A. O kit inclui os 30 controles aplicáveis e, como **pares-chamariz**, as 8 mutações, para que a especialista não presuma que todos os pares são equivalentes. As 3 recusas vêm com a origem OWL/XML e os motivos registrados. Os vereditos sobre os chamarizes são relatados (sensibilidade da revisão) e não afetam nenhum denominador.
- **Fora do kit:** previsões, resultados, gold, mapa e códigos de operação.
- **Limites:** a revisão não torna a V7 um experimento cego, porque as hipóteses foram orientadas pela leitura do código. Pistas de origem apontadas pela especialista são publicadas como limite do cegamento.
- **Credenciais:** informadas pelo pesquisador, sem certificação independente.

## 11. Custódia e regras de imutabilidade

1. Nenhuma alteração em casos, fonte, gold, operadores ou comparador após qualquer resultado oficial V7.
2. Falha de pós-processamento permite apenas recomputação auditada com código documentado em registro separado, preservando resultados originais e o estado do job.
3. Os hashes e o estado original da V6.1 (inclusive a execução #7 como *Failure*) permanecem inalterados.
4. A V7 não mede tempo de execução nem custo incremental (emenda 5).
5. Todos os arquivos V7 são versionados sem normalização de fim de linha; as fichas da especialista são verificadas pelo hash dos bytes recebidos (B3).

## 12. Limitações pré-especificadas

- Casos sintéticos e direcionados a fragilidades identificadas previamente: estresse de implementação, sem inferência para ambientes reais.
- Equivalência de N2/N3 definida no plano dos fatos Q01–Q05; identidade operacional e proveniência persistente mudam.
- A condição C usa o oráculo baseado no gold; a independência em relação ao gold será estudada na V7.1 (H3).
- Possível invalidade de controles no validador HL7, contada e relatada.
- N4 aplicável a 6 famílias e restrito a dois campos.
- Perfil-base FHIR, `-tx n/a`, sem terminologia externa nem perfis institucionais.
- Oito famílias por tipo sustentam apenas descrição.

## 13. Emenda A1 — auditoria pré-commit (25/10/2026)

Incorporada antes do congelamento. Não altera hipóteses, previsões, famílias, operadores, listas ou semente.

| Item do parecer | Alteração |
|---|---|
| B1 — completude da revisão | `verify_v7.check_review_sheets`: 38 pares e 3 recusas derivados da chave do kit; igualdade exata de IDs; unicidade; domínio de vereditos; justificativa obrigatória em `NAO_EQUIVALENTE`, `INCERTO` e `NAO_JUSTIFICADA`; cabeçalho exato. Executado na fase `reviewed`, antes do validador. |
| B2 — kit efetivamente entregue | ZIP determinístico `v7/review_kit_V7.zip` gerado e registrado no manifesto; `verify_v7` confere o ZIP e cada membro contra os hashes da geração; o atestado deve citar o hash do ZIP enviado e as datas. |
| B3 — CRLF/LF | `v7/.gitattributes` (`* -text`) e `benchmark/fixtures/overlays/.gitattributes` (`H*.owx -text`), ambos congelados; hashes sempre sobre os bytes; teste de ida e volta em repositório com `core.autocrlf=input`, que confirma a alteração sem a política e a preservação com ela. |
| B4 — ontologia de origem | SHA-256 do ZIP e do `marco.owx` fixados no `FREEZE_V7.json` e verificados antes de qualquer geração. Nota: `verify_base` já conferia o hash interno do `marco.owx`; a emenda acrescenta o hash do ZIP e antecipa a verificação. |
| R1 — custódia | `.gitignore` em `v7/` e em `benchmark/fixtures/overlays/` bloqueia gold, mapa, chave, kit e overlays H; publicação apenas com `git add -f` no commit do parecer. **Parcialmente não adotado:** os overlays H permanecem em `benchmark/fixtures/overlays/`, porque o comparador congelado (`competency_v4.source_rows`) lê esse caminho fixo; movê-los exigiria alterar o instrumento ou redirecionar seu caminho em tempo de execução, o que comprometeria o congelamento. A separação é garantida pela política Git e pela verificação de custódia. |
| R2 — ordem dos commits | `check_custody_v7.py` no workflow (com `fetch-depth: 0`), gravando os SHAs de protocolo, geração, parecer e HEAD em `v7/outputs/ci/custody_v7.json`. |
| R3 — erros de análise | `sanity_summary` e tabela de controles tratam `ANALYSIS_ERROR` como categoria própria, fora dos denominadores. |
| R4 — testes | 12 testes novos com dados fictícios (seção 7). |

# Laudo de recuperação da execução oficial V6.1 — GitHub Actions #7

**Data de análise:** 25/10/2026. **Estado:** validação oficial concluída, pós-processamento recuperado localmente. O job do GitHub permanece marcado como *Failure* e não deve ser apresentado como *Success*.

## Rastreabilidade

- Repositório: `PinheiroDiego/isys-validacao-fhir`; run GitHub Actions: `40240924783`, execução **#7**, commit `52188459da74f681d0271990eb646dbcdc6b8bc8`.
- Arquivo **oficial original** baixado diretamente da execução #7: `isys-v6.1-run7-official-outcomes.zip`, SHA-256 `c93b8411e3219a5cde7b4674e392c1b6b0dced8bcd80052a35516ce1670a31fa`. Preservado sem modificação.
- Manifesto de entradas V6.1: `bb3d876536b8e20112890a537c4bb5d5e8e1e6ef33ec4241e461eec27b892c00`.
- Gold V6.1: `32cc09a9b1a5d390cb807859ad83d42829e4fdd854c5e2a385020a33c693189d`.
- Verificação independente: **72/72 identificadores**, **72/72 hashes de entradas**, **72/72 hashes de OperationOutcome**, contagens de erro/aviso consistentes com os documentos brutos.
- Validador oficial: HL7 Validator CLI **7.0.3**, `hl7.fhir.r4.core#4.0.1`, Java **21.0.12.1**, perfil-base Bundle, `-tx n/a`, digest esperado do JAR `57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b`.
- O pacote de resultados oficial foi produzido pelo GitHub Actions; a análise A/B/C desta pasta foi recalculada **localmente** após correções de pós-processamento, nunca apresentada como saída bem-sucedida do job original.

## Resultado formal (sem contabilizar avisos como erros)

| Tipo de variante | Quantidade | Erro HL7 | Sem erro HL7 |
|---|---:|---:|---:|
| Referência correta | 23 | 0 | 23 |
| Controle equivalente | 23 | 0 | 23 |
| Mutação semântica | 15 | 0 | 15 |
| Mutação estrutural deliberada | 8 | 8 | 0 |
| Representação de recusa | 3 | 3 | 0 |
| **Total** | **72** | **11** | **61** |

- **17 erros**, **243 avisos**, tempo acumulado das 72 invocações **639.479 s** (inclui inicialização do Java/HL7 e cache/carga de pacotes; não representa a duração exclusiva de algoritmo).
- 3 representações de recusa (G33, G34, G36) foram rejeitadas porque `Bundle.entry=[]` não atende a regra do FHIR. Este é um **defeito de serialização da saída de recusa**, não a presença de uma observação rejeitada nem um falso alarme contra uma conversão correta. Resultados preservados; corrigir posteriormente sem modificar a V6.1.

## Condições A/B/C (69 variantes das 23 famílias conversíveis)

| Métrica | B: HL7 oficial | C: HL7 + comparação semântica |
|---|---:|---:|
| TP | 8 | 23 |
| FP | 0 | 0 |
| FN | 15 | 0 |
| TN | 46 | 46 |
| Recall observado | 34,78% | 100% |
| Precisão observada | 100% | 100% |
| Taxa de falso alarme observada | 0% | 0% |

- Das 15 mutações semânticas, **0/15** sinalizadas por erros HL7, **15/15** sinalizadas pelo verificador semântico (oráculo e consultas Q01–Q05). As 8 estruturais foram capturadas pelo HL7.
- Em **46/46** referências/controles conformes não houve alarme em B nem C.
- A converteu **28/31** ocorrências (90,32%); 3 recusas relatadas à parte, **não incorporadas à matriz B/C**.
- 23 famílias são a unidade de agrupamento: não tratar 69 variantes correlacionadas como 69 observações independentes. Bootstrap por famílias (**2.000 reamostragens, seed 160627**) descreve ganho pareado médio de **65,22 pontos percentuais**, intervalo descritivo **43,48–82,61 p.p.**, **sem inferência populacional**.
- Sem famílias excluídas por referência FHIR inválida entre as 23 conversíveis.

## Custo incremental independente de C

- Cronometrado **neste ambiente local** depois do resgate dos resultados oficiais, não no runner GitHub: 69 variantes (23 famílias), 12 rodadas de aquecimento e 45 repetições por variante.
- Mediana dos tempos medianos por família: **0.131002 ms**; percentil 90: **0.161437 ms**.
- A medida inclui verificador semântico e consultas Q01–Q05 sobre bundles FHIR já carregados; **a implementação atual relê e interpreta o overlay OWL/XML em cada chamada de competência**. Portanto, inclui parte do I/O e parsing da origem; exclui apenas parsing inicial dos JSON FHIR, subprocesso Java e validação oficial HL7. Não deve ser descrita como custo estritamente em memória.
- Esta é uma estimativa descritiva de custo local; não deve ser misturada com tempos das invocações oficiais em máquinas diferentes ou interpretada como custo de ponta a ponta.

## Defeitos operacionais recuperados sem alterar dados

1. A mutação estrutural G25 continha `valueQuantity.value="not-a-number"` intencionalmente; `competency_v4.normalize_value()` fazia `Decimal(...)` sem tratar lexema inválido. Correção: representar como sentinela `('invalid_numeric', 'not-a-number')`, preservando o desvio, sem forçar coerção numérica.
2. `analyze_v6.py` somava `r['duration_seconds']` sobre linhas de análise que contêm `official_seconds`. Correção de referência apenas para soma do tempo.
3. Foram aprovados **30 testes V6/V6.1**, incluindo testes novos para G25 e reprodução analítica sem Java.
4. Arquivos de entrada FHIR **98/98** inalterados, overlays **36/36** inalterados, gold original, decisões da especialista e artefato da execução #7 inalterados. O GitHub Actions #7 permanece historicamente falho; o laudo representa recuperação reproduzível da análise, não sua alteração retroativa.

## Limitações para o manuscrito

- Amostras propositalmente sintéticas. Valores percentuais **não** estimam desempenho em prontuários reais, outros perfis, serviços de terminologia ou contextos de interoperabilidade nacionais.
- Oráculo baseado em cenários planejados; revisão especializada documentada com ressalvas e cegamento parcial; não alegar avaliação totalmente cega.
- `-tx n/a` significa que **não houve validação externa de terminologias**.
- Os avisos HL7 não são tratados como erros na condição B; essa regra foi fixada no protocolo.
- Falhas de serialização dos Bundles de recusa precisam ser documentadas e corrigidas em nova versão, sem alteração retroativa das estatísticas.
- A análise local foi posterior ao acesso aos resultados, portanto é **reprocessamento de pós-análise** e não novo experimento confirmatório independente. A V6.1 já teve revisão externa parcial anteriormente.

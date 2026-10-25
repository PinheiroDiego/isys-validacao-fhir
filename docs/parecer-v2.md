# Laudo técnico — primeira execução oficial HL7 FHIR (V2)

**Data da análise:** 25/10/2026. **Origem:** `isys-hl7-fhir-r4-validation.zip` fornecido pelo usuário. Resultados não inventados; checados em `execution-summary.json`, `OperationOutcome` e `logs`.

## Identificação

- HL7 Validator CLI **7.0.3** (Git 28e9fac6d79d); Java Temurin 21.0.12.1; `hl7.fhir.r4.core#4.0.1`; `-tx n/a` (sem servidor de terminologias).
- JAR SHA-256: `57aa43fb40cec5de41def81c927725fd85908eeb71509b7f9313e04d9b8ec79b`.
- **16/16** solicitações oficiais executadas com OperationOutcome; **7/7** recursos individuais (2 Patient, 5 Observation) sem errors/fatal.
- Bundle base: **17 errors**, 13 warnings, portanto **não conforme** como pacote.
- As 17 mensagens são: 7 por `Bundle.entry.fullUrl` ausente; 5 por referências relativas em entradas sem fullUrl; 5 por `Bundle.entry.fullUrl` ausente com regra de identidade específica. Todos são aspectos do mesmo defeito de empacotamento.
- Foram registrados **157 erros** e **132 avisos** no conjunto completo de validações. Contagens são de ocorrências de `issue`, repetidas através dos 9 Bundles; não representam erros distintos independentes.

## Mutações (comparação correta)

| Mutação | Erros oficiais V2 | Novos erros vs. base | Interpretação |
|---|---:|---:|---|
| Alterar valor numérico | 17 | 0 | Não detectada diferencialmente |
| Trocar resultados entre exames | 17 | 0 | Não detectada diferencialmente |
| Alterar data do exame | 17 | 0 | Não detectada diferencialmente |
| Reatribuir paciente existente | 17 | 0 | Não detectada diferencialmente |
| Remover resultado | 17 | 0 | Não detectada diferencialmente |
| Acrescentar valor não sustentado | 17 | 0 | Não detectada diferencialmente |
| Duplicar entrada Observation | 20 | 3 | Apenas novos erros de fullUrl na entrada adicional; não comprova detecção da duplicação em baseline válida |
| Remover `Observation.status` | 18 | 1 | Detectou ausência de campo obrigatório específico |

O indicador automático `official_mutation_detection_rate=1.0` em V2 é **inválido como medida de detecção diferencial**: o baseline com 17 erros já falhava. Manter o resultado bruto para auditoria, mas tratá-lo como **não estimável** até executar referência válida.

## Cobertura e interpretação

- Fonte: 11 ocorrências fictícias; 5 convertidas (45,45%), 6 recusadas (54,55%).
- 5/5 Observation e 2/2 Patient passam nos perfis-base em validação isolada, com avisos de boas práticas, não erros.
- Cobertura de conformidade fim a fim (origem → Bundle validado) não estabelecida em V2, pois Bundle base falhou.
- A: conversão sintética realizada. B: validação oficial realizada, baseline inválido. C: comparação semântica da V1 detecta 7/7 mutações artificiais, mas ainda não há benchmark científico independente.

## Limites

Sem validação contra perfis brasileiros específicos, alinhamento terminológico externo ou dados clínicos reais; sem avaliação clínica. As mutações derivam de uma única base sintética, com dependência entre variantes.

## Próxima etapa

Executar V3 com fullUrl consistente no Bundle e avaliar de novo os OperationOutcome. Separar de forma explícita a detecção pelo HL7 Validator (B), a detecção semântica adicional (C) e a cobertura/recusa de A.

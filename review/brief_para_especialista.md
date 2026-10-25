# Protocolo de revisão independente do benchmark iSys V6

## Objetivo

Revisar se os dados de origem sintéticos, as transformações de referência, as decisões de recusa e os rótulos de alteração deliberada estão corretos segundo **FHIR R4 (4.0.1)** e o recorte clínico informacional *exame–resultado–paciente–data*. Não se está validando capacidade diagnóstica nem sugerindo implantação clínica.

## Materiais

- `benchmark/gold/families.json`: 36 famílias intencionalmente projetadas;
- `benchmark/fixtures/overlays/Gxx.owx`: asserções explícitas OWL/XML;
- `benchmark/inputs/Gxx/*.json`: estruturas `Bundle`, `Patient` e `Observation`;
- `review/decisions.csv`: ficha para parecer caso a caso.

**Não são fornecidas saídas de detectores B/C** durante revisão, para minimizar viés de confirmação. A autoria do gold não equivale a validação por especialista.

## Verificações exigidas

1. `Observation` é recurso apropriado para o conteúdo específico? Se for laudo ou procedimento, apontar casos em que seria necessário outro recurso e explicitar o motivo.
2. Existe associação inequívoca a Patient? Os `subject.reference` representam o vínculo informado ou há enriquecimento indevido?
3. Os dados de exame, resultado, unidade e data/precisão estão corretamente preservados? Campo não informado deve ficar ausente, não preenchido por inferência.
4. `Observation.status = unknown` é aceitável no contrato do caso? Não marcar `final` sem proveniência.
5. A mutação rotulada semantic_fault realmente altera o significado/recuperabilidade, independentemente de validade estrutural? O controle neutral não altera a informação relevante?
6. A mutação structural_fault viola uma regra efetivamente verificável em R4/perfil-base? Documentar eventual exceção ou aviso apenas.
7. A recusa esperada está alinhada ao contrato do conversor? Ausência de dados, ambiguidade ou múltiplos valores precisam de tratamento explícito.
8. Se qualquer caso depender de terminologia clínica, codificação LOINC/UCUM ou contexto externo ausente, sinalizar como fora de escopo/não adjudicável.

## Resultado solicitado

Em `decisions.csv`, preencher para as famílias G11–G36 (recomendado revisar também desenvolvimento G01–G10):

- `semantic_gold_correct`: `YES` ou `NO`;
- `fhir_structural_expectation_correct`: `YES` ou `NO`;
- `refusal_correct`: `YES` ou `NO` quando recusa, `N/A` nos demais;
- `verdict`: `APPROVE` ou `REJECT`;
- `reviewer_notes`: divergências técnicas, orientações e axiomas/perfis relevantes.

Acompanhar uma confirmação de autoria com pseudônimo/identificação interna, formação/experiência FHIR, data e conflitos declarados. Não compartilhar dados pessoais do revisor desnecessariamente no artefato público.

**Se existir uma rejeição, nenhuma validação confirmatória deve começar.** A equipe deve documentar a alteração e produzir **V6.1 nova**, preservando a V6 candidata com hashes, e solicitar reavaliação dos itens alterados antes de executar.

## Fontes fixadas

- HL7 R4 Bundle: https://hl7.org/fhir/R4/bundle.html
- HL7 R4 Observation: https://hl7.org/fhir/R4/observation.html
- HL7 Validator: https://hl7.org/fhir/validator/

# Protocolo V6 — pré-especificação anterior à validação oficial

**Estado:** design candidato e travado por SHA, pendente de revisão externa. **V5 encerrada** como replicação corretiva pós-inspeção, preservada integralmente. Não há execução oficial V6 nem adjudicação por especialista até esta data.

## Perguntas RQ

- RQ1: quais erros de preservação sobrevivem à validação estrutural FHIR?
- RQ2: qual detecção adicional e quais alarmes/recusas/custos introduz a condição C?
- RQ3: quais consultas Q01–Q05 sobre ocorrências apresentam respostas equivalentes e quais perdas Q06 existem?

## Delineamento, unidade e viés

36 famílias intencionais novas, derivadas de padrões de representação, **não de prontuários**. G01–G10 = desenvolvimento, G11–G36 = confirmação reservada. 30 famílias conversíveis e seis de recusa, 41 ocorrências de exames no total, 96 variantes FHIR. As famílias G11–G36 não são as famílias previamente utilizadas nas versões V4 e V5, embora algumas classes de defeitos se repitam. A mesma equipe preparou o gold e o avaliador; isso é ameaça à independência. A execução só ocorre após revisão de um especialista real em FHIR, com identidade documentada separadamente. A partição não deve ser pontuada para ajuste do algoritmo após o congelamento.

Uma família equivale a um cluster. Seus baseline, neutral e mutation **não são observações estatísticas independentes**. A estimativa descritiva principal será a diferença pareada da detecção da mutação por família B versus C. Pode-se apresentar bootstrap por família como variabilidade interna **não** intervalo de confiança representativo de população clínica. Sem teste de significância ou cálculo amostral de poder inventado.

## Grupos experimentais

A = conversor determinístico OWL/XML → Patient/Observation e Bundle, com registro explícito de recusa. Cobertura: `emitted / all_source_exam_occurrences`, recusas integradas no denominador e classificadas por motivos. Um Bundle vazio de recusa não significa conversão bem-sucedida.

B = A + HL7 Validator CLI 7.0.3, base FHIR R4 4.0.1, core `hl7.fhir.r4.core#4.0.1`, perfil `http://hl7.org/fhir/StructureDefinition/Bundle`, `-tx n/a`. Resultado positivo de detecção **somente** quando existe issue severity error/fatal no `OperationOutcome`. Warnings separados e avaliados em análise de sensibilidade.

C = B + oráculo semântico e equivalência das questões Q01–Q05; **positivo** caso B rejeite ou comparação semântica encontre divergência. Não há correção automática, somente detecção e registro. Esperados definidos a partir de asserções sintéticas, não produzidos a partir das saídas do conversor. O oráculo ainda exige revisão externa.

## Construção dos controles

- Referência: conversor V1.1 sobre overlay OWL/XML válido, sem inferência nem FHIR profile customizado permissivo.
- Controle equivalente: reorganização das entries, `Bundle.meta.versionId` ou `Bundle.id`, sem alteração clínica.
- Mutação semântica: relação, valor, unidade, data e precisão, identidade do exame ou ocorrência introduzida/removida, mantendo quando possível o formato FHIR. Estes alvos são **hipóteses de comportamento**, não resultados do validador antes de executar.
- Mutação estrutural: remoção de obrigatório, código inválido, tipo de recurso inesperado, data impossível, valor de tipo incorreto, `value[x]` duplicado ou `fullUrl` repetido.
- Recusa: identificação ausente, ambiguidade de associação, erro de calendário, dois resultados e unidade sem valor.

## Desfechos pré-especificados

Primário (nas famílias conversíveis confirmatórias com **baseline conforme**): proporção de famílias cujas mutações com falha intencional foram sinalizadas por B vs C; diferença **pareada** por família, com subgrupo de mutações semânticas. Reportar bruto `(detectadas)/(elegíveis)` por categoria.

Secundários: TP, FP, FN, TN e seus denominadores; taxa de alarmes em controles equivalentes e baseline; equivalência exata de Q01–Q05; perdas Q06; cobertura e recusas em A; warnings; tempo de execução por caso da validação oficial; custo adicional de C.

**Validade:** se o baseline de uma família tiver erro HL7, sua mutação e controle não entram no contraste B/C e a família é reportada como não interpretável; nunca contabilizar falha pré-existente como uma mutação detectada. Se um arquivo ou OperationOutcome não puder ser verificado por SHA, bloquear a análise. Não remover famílias desfavoráveis silenciosamente.

**Falsos alarmes:** se um controle supostamente equivalente apresentar erro, verificar se o próprio controle introduziu uma violação legítima (como V4). Preservar ocorrência e classificar o controle como inválido/comprometido; não apagar ou reclassificar retroativamente. Propor revisão V6.1 se necessário.

**Semântica:** comparações conservadoras de identidade, multiplicidades, valores decimais exatos, unidade literal, precisão temporal (ano/mês/dia), ausência e relações paciente–exame. Não inferir UCUM, LOINC, status clínico final ou equivalência terminológica não suportada.

## Medição de custo

1. Tempo total da condição B é obtido por processo Java oficial e contém inicialização/carregamento; reportar como latência de execução do fluxo oficial, sem interpretar como custo de análise da instância isolada.
2. C é cronometrado **separadamente** após parse dos Bundles: `semantic_oracle.compare` + `competency_v4.compare_queries`, com 12 rodadas de aquecimento e 45 repetições intercaladas por variante em ordem pseudoaleatória fixa; mediana por variante e mediana por família. Arquivo I/O registrado à parte e excluído do tempo incremental C. Não tratar as 45 repetições como replicatas independentes do caso.
3. Metadados de Python, plataforma, seed, número de repetições, resultados brutos agregados em `incremental_C_timing.json`. Relatar que soma ingênua de B (Java) e C (Python) não é um sistema implantado medido end-to-end.

## Pré-condições de confirmação

- Hashes conferidos em `verify_v6.py` e 14 testes de engenharia aprovados;
- Especialista aprova gold, rotulagem, representações e recusas; revisão `decisions.csv` com `APPROVE` em todas as famílias confirmatórias e `attestation.json` com hash do CSV e do gold;
- Se especialista rejeitar qualquer item, suspender confirmação e versionar novo conjunto, sem sobrescrever candidato;
- Após revisão, executar workflow GitHub Actions confirmatory e arquivar `OperationOutcome` e saídas brutas.

## Limitações pré-especificadas

Dados totalmente fictícios, conjunto de conveniência, cobertura restrita à representação de exames, referências em FHIR R4 base sem guias regionais, desativação de terminologia remota, ausência de julgamento clínico, números resultantes não generalizáveis e possíveis erros de interpretação do gold apesar da revisão. Nada permite inferir sucesso em prontuários reais ou sistemas hospitalares.

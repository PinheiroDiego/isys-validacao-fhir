# Guia de revisão — V7

Obrigado por avaliar este material. Ele contém apenas dados sintéticos; nenhum dado de paciente real.

## O que é avaliado

**Pares (`pares/Pnn_A.json` e `pares/Pnn_B.json`).** Cada par contém duas representações FHIR R4 (Bundle `collection`). Para cada par, indique se A e B representam **os mesmos fatos clínicos** segundo o contrato abaixo. Alguns pares podem ser equivalentes e outros não; a proporção não é informada.

Contrato de fatos (consultas Q01–Q05):

- **Q01** — qual paciente está associado a cada ocorrência de exame e qual é a identidade (nome) do exame;
- **Q02** — o resultado de cada ocorrência (valor e tipo: numérico ou textual), ou a sua ausência;
- **Q03** — a data de cada ocorrência, com a mesma precisão (ano, mês ou dia);
- **Q04** — valor e unidade do resultado;
- **Q05** — classificação temporal da ocorrência a partir da data e de sua precisão.

Diferenças que **não** alteram esses fatos (por exemplo, forma de serialização, identificadores técnicos, forma de referência que aponta para o mesmo recurso, narrativa gerada a partir dos dados, forma de codificação de caracteres) devem ser julgadas pelo critério acima, e não pela igualdade literal dos arquivos. Se uma diferença técnica tornar a interpretação dos fatos duvidosa, use **INCERTO** e explique.

**Recusas (`recusas/Rn_origem.owx` e `recusas/Rn_motivo.json`).** Para cada recusa, indique se a decisão de não converter a ocorrência em FHIR é justificada pela fonte e pelo motivo registrado.

## Como responder

Preencha `FICHA_PARES_V7.csv` (veredito: `EQUIVALENTE`, `NAO_EQUIVALENTE` ou `INCERTO`) e `FICHA_RECUSAS_V7.csv` (veredito: `JUSTIFICADA`, `NAO_JUSTIFICADA` ou `INCERTO`), com justificativa breve. Não é necessário executar validadores nem ferramentas.

## Cegamento

Os arquivos têm nomes opacos e não indicam como foram produzidos. Você não recebe previsões, resultados de validadores ou do comparador, nem o mapeamento dos arquivos. Se algum conteúdo permitir inferir a origem de um par, por favor registre isso na justificativa: essa informação será publicada como limite do cegamento.

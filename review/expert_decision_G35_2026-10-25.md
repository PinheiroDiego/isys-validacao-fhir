# Adjudicação técnica recebida — G35 e G15

**Origem da decisão:** texto fornecido pelo pesquisador, atribuído à especialista que preencheu o parecer V6; autoria confirmada pelo pesquisador. Não é assinatura digital nem comprovação de cegamento.

**Decisão:** Alternativa A. Converter `G35` parcialmente: `Observation.status=unknown`; `dataAbsentReason.coding` sistema `http://terminology.hl7.org/CodeSystem/data-absent-reason`, código `unknown`; sem `value[x]`; a unidade de origem `mg/dL` vai em `Observation.note`, com referência à ocorrência G35-x1. Não inferir realização, cancelamento ou falha de processo.

**Harmonização:** G15 sem resultado terá igualmente `dataAbsentReason=unknown`; variantes sem razão de ausência são atualizadas. A mutação `invent_numeric_value` remove a razão de ausência ao inventar o resultado, mantendo a mutação semanticamente errada mas estruturalmente válida.

**Impacto:** G35 deixa de ser recusa e ganha três variantes; a V6 original permanece intacta. G35/P,Q,R e G15/P,Q,R modificadas necessitam ratificação pontual das saídas novas antes da validação confirmatória. Demais ressalvas: 1) cegamento parcial da revisão anterior; 2) perda de vínculo com evolução em recursos FHIR; 3) granularidade da taxonomia para identidade do exame; 4) relatórios das recusas fora do Bundle, recomendado `OperationOutcome` separado. Autoriza uso acadêmico anonimizado do parecer, segundo texto fornecido.

**Status:** REGRA APROVADA; NOVAS REPRESENTAÇÕES AINDA NÃO RATIFICADAS. Não converter automaticamente aprovação com ressalvas da V6 em aprovação irrestrita da V6.1.

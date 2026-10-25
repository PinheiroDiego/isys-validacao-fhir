# iSys — V6.1 ratificada com ressalvas; pronta para primeira execução HL7 oficial

**Estado:** parecer complementar G15 **RATIFICO**, G35 **RATIFICO_COM_RESSALVAS**, com autoria e experiência informadas e confirmadas pelo pesquisador. Revisor não identificado publicamente; não há assinatura digital no CSV. Primeira revisão parcialmente descegada. **Nenhum resultado oficial V6.1 foi gerado até este release**. A aprovação documental não equivale a conformidade HL7.

## Contagens e limites

- 36 famílias no total (31 conversíveis, 5 recusas), 41 ocorrências (36 aceitas, 5 recusadas), 98 entradas FHIR.
- Partição confirmatória: **26 famílias**, sendo **23 conversíveis x 3 variantes + 3 recusas = 72 arquivos FHIR**. Analisar variantes agrupadas por família.
- G35 anteriormente recusa passa a observação parcial; ausência representada com `dataAbsentReason=unknown`, sem `value[x]`, com unidade `mg/dL` em `note`. G15 harmonizada.
- G35/neutral `Bundle.id` alterado de `synthetic-control-35` para `batch-35` **depois do parecer**, exatamente como ressalva recomendava; **97 das 98 entradas permanecem byte a byte idênticas ao V6.1 candidato**. Gold, OWL e mutações permanecem intocados; snapshot da candidata em `historical/v6.1-candidate-unaltered.zip`.
- Outras variantes contêm marcadores legíveis de controle e nomes de arquivo reveladores. A correção pontual não elimina o cegamento parcial, nem cria avaliação autenticamente cega.
- Algumas saídas corretas podem ter avisos de boas práticas; matriz B conta só erros/fatais HL7 e C adiciona o oráculo semântico e consultas.

## Executar 72 validações FHIR R4 oficiais em GitHub privado

1. Subir **o conteúdo descompactado deste pacote** no repositório privado (raiz do projeto; pasta `.github/workflows/` incluída). Não subir as planilhas de controle privado do pesquisador.
2. GitHub → **Actions** → `iSys V6.1 - HL7 Adjudicated Benchmark` → **Run workflow** → selecionar `confirmatory`.
3. O workflow testa os hashes do gold, overlays e inputs, verifica o parecer ratificado com ressalvas e depois baixa o HL7 Validator CLI **7.0.3** com hash fixo. Invoca o validador **72 vezes** em FHIR R4 **4.0.1** com `-tx n/a`.
4. Baixar o artefato `isys-v6.1-confirmatory-hl7` e anexar à conversa para auditoria de resultados, matriz A/B/C e análise por família. **Não afirmar 72 resultados confirmados antes dessa execução.**

## Reprodutibilidade local (sem execução do HL7)

```bash
python3 src/verify_v6.py
python3 src/review_gate.py
python3 -m unittest discover -s tests -v
```

A origem ontológica original **não está distribuída**. O gold sintético, o desenho das mutações, sua classificação e o comparador compartilham escolhas do projeto; a revisão especialista não elimina risco de viés.

# Correção do controle de integridade do GitHub Actions — V6.1

**Motivo:** a execução `iSys V6.1 - HL7 Adjudicated Benchmark #2` terminou com exit code 3 na etapa `Require external FHIR specialist review for confirmation`, **antes do HL7 Validator**. O artefato anexado inclui apenas manifest/attestation/decisions, e nenhum OperationOutcome.

**Diagnóstico confirmado:** dois CSVs originalmente preservados com CRLF foram convertidos pelo Git para LF. As diferenças de Git blobs foram comparadas com os hashes SHA-256 originais. A versão do GitHub preserva os mesmos bytes após normalizar unicamente CRLF → LF. Os dois arquivos são `review/decisions.csv` e `review/evidence/FICHA_RESPONDER_RECEBIDA.csv`.

**Correção:** `src/review_gate.py` continua comparando contra os SHA-256 originais já assinados na `attestation.json`, mas, na eventualidade de divergência, aceita **somente** a conversão de LF para CRLF quando essa reconstrução reproduzir exatamente o hash anterior. Não permite alterações em valores, identificadores, BOM ou campos do CSV. `tests/test_v61_checkout_eol.py` reproduz uma cópia integral do repositório com ambos os CSVs normalizados e confirma que a porta abre, e que mudanças de conteúdo continuam bloqueadas.

**Escopo e rastreabilidade:** pacote corretivo operacional CI; nenhuma variante FHIR, overlay OWL/XML, gold, oráculo, documento de revisão, entrada confirmatória, hash atestado ou histórico de versões foi alterado. Apenas script de gate, testes do gate e documentação operacional. **Nenhum resultado confirmatório oficial foi produzido por essa correção.**

**Passo seguinte:** substituir os arquivos de código e testes no GitHub (o ZIP também contém o projeto completo), e executar novamente o workflow em `scope=confirmatory` em novo run, não `Re-run jobs` do commit antigo. Os resultados HL7 só podem ser declarados após execução bem-sucedida.

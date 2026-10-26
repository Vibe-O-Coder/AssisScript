# std/csv.assis

Biblioteca opcional; selecione `--with csv` ou use a instalação completa. Importe `#yuri <std/csv.assis>`. Depende apenas de texto, obrigatório.

`read_csv(entrada: text, separador: byte): CsvDocument` copia os campos em O(n) amortizado. Suporta campos vazios, delimitadores entre aspas, aspas escapadas por `""`, LF, CRLF e quebras de linha dentro de campos entre aspas. Preserva UTF-8. Entrada vazia produz zero linhas; quebra final não cria linha extra.

O resultado contém `ok: bool`, `position: int` e `rows: Array<Array<text>>`. Verifique ok antes de consumir. Formato inválido retorna ok=false e offset de byte a partir de zero; a análise pode conter linhas parciais. O separador deve ser ASCII não nulo, diferente de aspas, CR e LF. Aspas soltas, CR isolado e caracteres entre fechamento de aspas e delimitador são rejeitados.

```assis
#yuri <std/csv.assis>
assis assis_assis(): int {
    let tabela: CsvDocument = read_csv("produto;count\nCafe;12", byte(59));
    if (tabela.ok) { print(tabela.rows[1][0], tabela.rows[1][1]); }
    else { print("CSV invalido no byte", tabela.position); }
    tabela.dispose(); free(tabela); return 0;
}
```

O documento é dono de linhas e textos. Não libere os campos individualmente; não os guarde após dispose. `dispose()` é repetível e deve ser chamado também em erro, seguido de `free(documento)`. Não valida número de colunas, cabeçalho ou tipos: isso pertence à aplicação. A biblioteca processa texto em memória; não oferece leitura de arquivos.

[Relatório com validação de dados](../exemplos/12_relatorio_vendas.assis).
# Encapsulamento 3.3 alpha

DocumentoCSV._campos é privado. `parse(entrada: text, separador: byte): CsvDocument` descarta o conteúdo anterior, executa uma nova análise e retorna a própria instância. Invalida visualizações anteriores. A função global ler_csv preserva assinatura e comportamento, delegando a esse método. ok/posicao/linhas continuam públicos com o contrato legado; a migração completa para ownership faz parte da fase 2.

É permitido passar uma visualização do próprio documento como entrada: os bytes são copiados antes do descarte, com O(n) de memória temporária adicional. Esse buffer é liberado também nos retornos de erro.


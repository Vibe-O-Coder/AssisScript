# Diagnósticos e tratamento de erros 3.1

Erros de compilação mostram arquivo, linha, coluna, trecho e uma indicação de correção. `--diagnostics=json` acrescenta `hint`, `severity` e `endColumn` exclusivo, preservando os campos anteriores e os códigos A001 (fonte) e A002 (ambiente/CLI). As colunas são unidades UTF-16 para o VS Code; offsets retornados por bibliotecas são bytes a partir de zero. O editor mostra a ajuda no painel Problemas e destaca o intervalo informado.

Falhas de programação em execução mantêm status 70: índice fora do limite, ponteiro nulo, divisão por zero, deslocamento fora de 0..63 e assert. O diagnóstico identifica linha e, para módulos, arquivo. `assert(condicao, "contexto do problema")` acrescenta uma mensagem de aplicação; essa mensagem só é avaliada quando a condição falha. Verificações de segurança continuam ativas mesmo com otimização.

Para dados externos, use resultados explícitos:

```assis
#yuri <std/convert.assis>
assis assis_assis(): int {
    let count: IntResult = parse_int("12x");
    if (!count.ok) {
        print("Quantidade invalida:", error_message(count.code), count.position);
        free(count); return 1;
    }
    print(count.value); free(count); return 0;
}
```

`Array.try_get(indice, &saida)`, `Array.try_pop(&saida)` e `HashMap.try_get(chave, &saida)` retornam false em ausência/índice inválido/saída nula. Na falha preservam a saída e a coleção. A saída pode guardar qualquer tipo da especialização, incluindo referência. CSV e decodificações também têm ok e posicao.

A linguagem não possui try/catch, propagação automática, destrutores ou liberação por escopo. Resultados e recursos devem ser liberados em cada caminho. Falta de memória continua fatal; ponteiros brutos exigem disciplina de propriedade. Este modelo é explícito e permite recuperar erros de entrada sem abortar o processo.

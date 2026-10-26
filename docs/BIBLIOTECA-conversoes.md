# std/conversoes.assis

**Atualização 3.3.0-alpha.7:** Alpha.7 adiciona formatar_int_buffer(numero, borrow mut destino), sem alocação e sem NUL, incluindo INT64_MIN. Capacidade mínima 20 bytes; retorna comprimento ou -1. [Contrato](IO-E-APLICACAO-A.md).

Biblioteca obrigatória. Importe `#yuri <std/conversoes.assis>`. Inclui erros e texto transitivamente.

`inteiro_de_texto(entrada: text): ResultadoInt` lê decimal estrito, sinal `+`/`-` opcional, sem espaços, `_` ou prefixos. Aceita de -9223372036854775808 a 9223372036854775807. Não transforma entrada inválida em zero: informa código e primeiro offset inválido. Custo O(n), memória auxiliar O(1) além do registro.

`texto_de_inteiro(valor: int): Texto` formata qualquer int64 em decimal, sem separadores ou zero à esquerda. Inclui INT64_MIN. O resultado possui memória própria.

```assis
#yuri <std/conversoes.assis>
assis assis_assis(): int {
    let valor: ResultadoInt = inteiro_de_texto("1250");
    if (!valor.ok) { print(mensagem_erro(valor.codigo), valor.posicao); free(valor); return 1; }
    let formatado: Texto = texto_de_inteiro(valor.valor);
    print(formatado.visualizacao());
    formatado.dispose(); free(formatado); free(valor); return 0;
}
```

Para aceitar espaços de uma interface, primeiro use `aparar_texto`, converta sua visualização e depois libere o Texto temporário. Veja [exemplo de relatório](../exemplos/12_relatorio_vendas.assis).

# std/conversoes.assis

**Atualização 3.3.0-alpha.7:** Alpha.7 adiciona formatar_int_buffer(numero, borrow mut destino), sem alocação e sem NUL, incluindo INT64_MIN. Capacidade mínima 20 bytes; retorna comprimento ou -1. [Contrato](IO-E-APLICACAO-A.md).

Biblioteca obrigatória. Importe `#yuri <std/convert.assis>`. Inclui erros e texto transitivamente.

`parse_int(entrada: text): IntResult` lê decimal estrito, sinal `+`/`-` opcional, sem espaços, `_` ou prefixos. Aceita de -9223372036854775808 a 9223372036854775807. Não transforma entrada inválida em zero: informa código e primeiro offset inválido. Custo O(n), memória auxiliar O(1) além do registro.

`int_to_string(value: int): String` formata qualquer int64 em decimal, sem separadores ou zero à esquerda. Inclui INT64_MIN. O resultado possui memória própria.

```assis
#yuri <std/convert.assis>
assis assis_assis(): int {
    let value: IntResult = parse_int("1250");
    if (!value.ok) { print(error_message(value.code), value.position); free(value); return 1; }
    let formatado: String = int_to_string(value.value);
    print(formatado.view());
    formatado.dispose(); free(formatado); free(value); return 0;
}
```

Para aceitar espaços de uma interface, primeiro use `trim`, converta sua visualização e depois libere o Texto temporário. Veja [exemplo de relatório](../exemplos/12_relatorio_vendas.assis).

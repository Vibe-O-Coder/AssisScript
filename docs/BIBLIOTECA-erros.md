# std/erros.assis

**Atualização 3.3.0-alpha.7:** Alpha.7 adiciona Option<T>/Result<T,E> Copy, option_or, option_map e result_map sem alocação. Tipos precisam admitir layout Copy. [Contratos e matching](VALORES-E-VARIANTES.md). ResultadoInt legado é preservado.

Biblioteca obrigatória. Importe `#yuri <std/errors.assis>`.

`IntResult` contém `ok: bool`, `value: int`, `code: int` e `position: int`. Leia valor apenas se ok. Cada resultado é um registro alocado; libere com `free(resultado)` inclusive em erro.

| Código | Significado |
| --- | --- |
| 0 | Sucesso |
| 1 | Entrada vazia |
| 2 | Formato inválido |
| 3 | Overflow de inteiro com sinal de 64 bits |
| 4 | Divisão por zero |
| 5 | Intervalo inválido |

`result_ok(value)` e `result_error(code, position)` criam resultados. `error_message(code)` retorna texto estático, sem liberação. Posições são offsets de bytes a partir de zero; -1 significa posição indisponível.

`checked_add(a, b)` detecta overflow antes da operação. `checked_div(a, b)` detecta zero e INT64_MIN/-1. Ambos retornam ResultadoInt sem encerrar o programa.

```assis
#yuri <std/errors.assis>
assis assis_assis(): int {
    let resultado: IntResult = checked_div(100, 0);
    if (!resultado.ok) { print(error_message(resultado.code)); }
    else { print(resultado.value); }
    free(resultado); return 0;
}
```

Erros de memória e ponteiros inválidos não se tornam recuperáveis automaticamente. Veja [tratamento de erros](ERROS.md).

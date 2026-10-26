# Evolução alpha.10 — AssisScript 3.3.0-alpha.10 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.10 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| current-heap | 19.332 | 42.909 | 8200 | 270336 |
| current-value | 20.099 | 34.878 | 8200 | 270336 |
| current-heap-sem-opt | 19.624 | 47.534 | 8200 | 270336 |
| current-value-sem-opt | 19.532 | 42.616 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 3.088 | 270336 |
| 100000 | 1100006 | 20.733 | 270336 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| current | 0.510 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 16.966 | 20.206 | 8193 | 15990784 |
| slice-sem-opt | 16.109 | 46.181 | 12289 | 15990784 |
| unicode | 28.404 | 15.301 | 17912 | 270336 |
| unicode-sem-opt | 27.261 | 23.860 | 17920 | 270336 |
| owned | 26.566 | 17.311 | 13920 | 270336 |
| owned-sem-opt | 28.293 | 17.320 | 13928 | 270336 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.9. Os relatórios antigos permanecem históricos.

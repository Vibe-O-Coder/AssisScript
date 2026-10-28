# Evolução alpha.13 — AssisScript 3.3.0-alpha.13 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.13 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha12-heap | 19.506 | 59.682 | 8200 | 270336 |
| current-heap | 22.038 | 54.111 | 8200 | 270336 |
| current-value | 20.228 | 45.510 | 8200 | 270336 |
| alpha12-heap-sem-opt | 20.075 | 53.594 | 8200 | 270336 |
| current-heap-sem-opt | 21.505 | 51.947 | 8200 | 270336 |
| current-value-sem-opt | 19.945 | 51.938 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 23.148 | 270336 |
| 1000000 | 11000006 | 214.901 | 270336 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha12 | 0.552 | 270336 |
| current | 0.682 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 21.394 | 23.167 | 8193 | 15990784 |
| slice-sem-opt | 21.473 | 53.083 | 12289 | 15990784 |
| unicode | 40.297 | 17.745 | 17912 | 270336 |
| unicode-sem-opt | 40.036 | 28.002 | 17920 | 270336 |
| owned | 36.494 | 19.147 | 13920 | 270336 |
| owned-sem-opt | 39.726 | 20.481 | 13928 | 270336 |
| ffi | 24.215 | 9.086 | 12600 | 958464 |
| ffi-sem-opt | 22.651 | 14.576 | 12600 | 958464 |
| c-callback-sort | 23.525 | 2.334 | 20488 | 1413120 |
| c-callback-sort-sem-opt | 22.818 | 2.956 | 20488 | 1413120 |
| closure-call | 21.199 | 11.397 | 8208 | 270336 |
| closure-call-sem-opt | 22.383 | 16.754 | 8208 | 270336 |
| closure-borrow | 24.158 | 16.596 | 12304 | 270336 |
| closure-borrow-sem-opt | 21.718 | 39.975 | 12304 | 270336 |
| move-enum | 22.174 | 13.209 | 8200 | 270336 |
| move-enum-sem-opt | 21.323 | 14.364 | 8200 | 270336 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.12. Os relatórios antigos permanecem históricos.

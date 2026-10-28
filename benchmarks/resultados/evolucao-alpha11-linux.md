# Evolução alpha.11 — AssisScript 3.3.0-alpha.11 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.11 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha10-heap | 19.455 | 44.142 | 8200 | 270336 |
| current-heap | 19.765 | 44.368 | 8200 | 270336 |
| current-value | 20.113 | 35.051 | 8200 | 270336 |
| alpha10-heap-sem-opt | 18.540 | 47.390 | 8200 | 270336 |
| current-heap-sem-opt | 19.908 | 46.523 | 8200 | 270336 |
| current-value-sem-opt | 19.536 | 43.328 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 2.677 | 270336 |
| 100000 | 1100006 | 20.264 | 270336 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha10 | 0.522 | 270336 |
| current | 0.467 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 17.150 | 21.556 | 8193 | 15990784 |
| slice-sem-opt | 17.900 | 47.509 | 12289 | 15990784 |
| unicode | 29.443 | 15.818 | 17912 | 270336 |
| unicode-sem-opt | 29.442 | 25.273 | 17920 | 270336 |
| owned | 28.098 | 17.479 | 13920 | 270336 |
| owned-sem-opt | 29.813 | 17.754 | 13928 | 270336 |
| ffi | 17.994 | 8.526 | 12600 | 958464 |
| ffi-sem-opt | 16.692 | 12.682 | 12600 | 958464 |
| c-callback-sort | 17.488 | 1.955 | 20488 | 1413120 |
| c-callback-sort-sem-opt | 17.595 | 2.103 | 20488 | 1413120 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.10. Os relatórios antigos permanecem históricos.

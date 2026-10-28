# Evolução alpha.12 — AssisScript 3.3.0-alpha.12 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.12 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha11-heap | 26.327 | 44.489 | 8200 | 270336 |
| current-heap | 28.264 | 44.322 | 8200 | 270336 |
| current-value | 26.721 | 35.194 | 8200 | 270336 |
| alpha11-heap-sem-opt | 21.688 | 44.967 | 8200 | 270336 |
| current-heap-sem-opt | 29.289 | 48.126 | 8200 | 270336 |
| current-value-sem-opt | 27.975 | 45.437 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 63.392 | 270336 |
| 1000000 | 11000006 | 536.846 | 270336 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha11 | 0.801 | 270336 |
| current | 0.770 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 44.339 | 53.502 | 8193 | 15990784 |
| slice-sem-opt | 47.533 | 107.013 | 12289 | 15990784 |
| unicode | 73.953 | 44.449 | 17912 | 270336 |
| unicode-sem-opt | 68.970 | 61.840 | 17920 | 270336 |
| owned | 71.478 | 43.792 | 13920 | 270336 |
| owned-sem-opt | 66.176 | 44.692 | 13928 | 270336 |
| ffi | 45.247 | 29.641 | 12600 | 1081344 |
| ffi-sem-opt | 44.448 | 44.621 | 12600 | 958464 |
| c-callback-sort | 39.489 | 4.006 | 20488 | 1413120 |
| c-callback-sort-sem-opt | 53.735 | 4.681 | 20488 | 1413120 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.11. Os relatórios antigos permanecem históricos.

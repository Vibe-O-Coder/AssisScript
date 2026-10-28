# Evolução alpha.13 — AssisScript 3.3.0-alpha.13 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.13 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha12-heap | 14.874 | 61.386 | 102400 | 5328896 |
| current-heap | 14.717 | 60.656 | 102400 | 5328896 |
| current-value | 14.395 | 52.857 | 102400 | 5263360 |
| alpha12-heap-sem-opt | 14.504 | 67.913 | 102400 | 5324800 |
| current-heap-sem-opt | 14.521 | 67.187 | 102400 | 5328896 |
| current-value-sem-opt | 15.041 | 58.041 | 102400 | 5271552 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 35.100 | 5558272 |
| 1000000 | 11000006 | 219.755 | 5554176 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha12 | 13.990 | 5255168 |
| current | 14.662 | 5259264 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 12.305 | 29.262 | 102400 | 20914176 |
| slice-sem-opt | 12.356 | 56.561 | 102912 | 20910080 |
| unicode | 14.994 | 28.879 | 109056 | 5402624 |
| unicode-sem-opt | 15.113 | 39.580 | 110592 | 5406720 |
| owned | 13.559 | 32.445 | 106496 | 5332992 |
| owned-sem-opt | 13.393 | 34.028 | 107008 | 5332992 |
| ffi | 11.878 | 21.653 | 101888 | 5263360 |
| ffi-sem-opt | 12.064 | 29.208 | 102400 | 5267456 |
| c-callback-sort | 12.995 | 15.854 | 103424 | 5275648 |
| c-callback-sort-sem-opt | 13.083 | 15.683 | 103936 | 5271552 |
| closure-call | 11.220 | 26.735 | 102400 | 5332992 |
| closure-call-sem-opt | 12.356 | 29.988 | 102912 | 5332992 |
| closure-borrow | 12.651 | 26.511 | 102912 | 5332992 |
| closure-borrow-sem-opt | 12.227 | 50.429 | 102912 | 5337088 |
| move-enum | 12.602 | 26.922 | 102400 | 5328896 |
| move-enum-sem-opt | 12.806 | 27.035 | 102912 | 5332992 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.12. Os relatórios antigos permanecem históricos.

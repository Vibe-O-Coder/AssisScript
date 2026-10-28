# Evolução alpha.11 — AssisScript 3.3.0-alpha.11 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.11 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha10-heap | 15.190 | 54.624 | 102400 | 5320704 |
| current-heap | 14.544 | 54.222 | 102400 | 5328896 |
| current-value | 14.851 | 47.425 | 102400 | 5259264 |
| alpha10-heap-sem-opt | 14.760 | 60.423 | 102400 | 5332992 |
| current-heap-sem-opt | 14.841 | 60.206 | 102400 | 5324800 |
| current-value-sem-opt | 14.821 | 52.537 | 102400 | 5263360 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 15.731 | 5554176 |
| 100000 | 1100006 | 31.463 | 5554176 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha10 | 13.026 | 5263360 |
| current | 13.193 | 5259264 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 12.077 | 25.991 | 102400 | 20914176 |
| slice-sem-opt | 11.813 | 52.724 | 102912 | 20905984 |
| unicode | 14.003 | 27.417 | 109056 | 5398528 |
| unicode-sem-opt | 13.547 | 35.723 | 110592 | 5394432 |
| owned | 13.008 | 31.227 | 106496 | 5328896 |
| owned-sem-opt | 13.619 | 31.317 | 107008 | 5332992 |
| ffi | 11.613 | 20.414 | 101888 | 5259264 |
| ffi-sem-opt | 12.154 | 24.957 | 102400 | 5263360 |
| c-callback-sort | 11.717 | 14.030 | 103424 | 5271552 |
| c-callback-sort-sem-opt | 11.770 | 14.141 | 103936 | 5275648 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.10. Os relatórios antigos permanecem históricos.

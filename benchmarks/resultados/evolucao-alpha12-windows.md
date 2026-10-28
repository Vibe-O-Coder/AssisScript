# Evolução alpha.12 — AssisScript 3.3.0-alpha.12 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.12 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha11-heap | 15.026 | 53.700 | 102400 | 5308416 |
| current-heap | 16.108 | 56.100 | 102400 | 5308416 |
| current-value | 15.590 | 49.725 | 102400 | 5238784 |
| alpha11-heap-sem-opt | 14.796 | 60.729 | 102400 | 5308416 |
| current-heap-sem-opt | 15.965 | 59.037 | 102400 | 5308416 |
| current-value-sem-opt | 16.059 | 53.961 | 102400 | 5238784 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 34.724 | 5537792 |
| 1000000 | 11000006 | 203.261 | 5533696 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha11 | 30.342 | 5242880 |
| current | 30.020 | 5234688 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 10.728 | 26.889 | 102400 | 20889600 |
| slice-sem-opt | 10.552 | 57.053 | 102912 | 20893696 |
| unicode | 13.805 | 29.269 | 109056 | 5382144 |
| unicode-sem-opt | 13.202 | 41.931 | 110592 | 5386240 |
| owned | 12.213 | 37.256 | 106496 | 5316608 |
| owned-sem-opt | 21.448 | 35.926 | 107008 | 5312512 |
| ffi | 10.540 | 30.502 | 101888 | 5242880 |
| ffi-sem-opt | 10.782 | 30.277 | 102400 | 5242880 |
| c-callback-sort | 11.388 | 14.691 | 103424 | 5251072 |
| c-callback-sort-sem-opt | 14.975 | 14.416 | 103936 | 5251072 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.11. Os relatórios antigos permanecem históricos.

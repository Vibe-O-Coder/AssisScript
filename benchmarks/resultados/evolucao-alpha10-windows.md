# Evolução alpha.10 — AssisScript 3.3.0-alpha.10 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.10 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| current-heap | 14.606 | 52.375 | 102400 | 5332992 |
| current-value | 14.536 | 47.053 | 102400 | 5263360 |
| current-heap-sem-opt | 15.278 | 57.999 | 102400 | 5332992 |
| current-value-sem-opt | 14.681 | 53.051 | 102400 | 5267456 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 16.165 | 5558272 |
| 100000 | 1100006 | 31.300 | 5550080 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| current | 13.370 | 5267456 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 11.926 | 26.564 | 102400 | 20918272 |
| slice-sem-opt | 12.128 | 49.801 | 102912 | 20918272 |
| unicode | 13.488 | 27.724 | 109056 | 5410816 |
| unicode-sem-opt | 13.890 | 34.747 | 110592 | 5410816 |
| owned | 13.011 | 30.300 | 106496 | 5337088 |
| owned-sem-opt | 13.298 | 30.402 | 107008 | 5332992 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.9. Os relatórios antigos permanecem históricos.

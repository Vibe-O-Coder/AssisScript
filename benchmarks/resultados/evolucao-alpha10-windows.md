# Evolução alpha.10 — AssisScript 3.3.0-alpha.10 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.10 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| current-heap | 15.526 | 54.927 | 102400 | 5328896 |
| current-value | 16.101 | 47.924 | 102400 | 5263360 |
| current-heap-sem-opt | 15.266 | 60.793 | 102400 | 5324800 |
| current-value-sem-opt | 15.182 | 53.519 | 102400 | 5259264 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 17.155 | 5566464 |
| 100000 | 1100006 | 32.925 | 5554176 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| current | 14.661 | 5259264 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 12.258 | 27.972 | 102400 | 20918272 |
| slice-sem-opt | 11.999 | 51.915 | 102912 | 20918272 |
| unicode | 13.729 | 28.049 | 109056 | 5406720 |
| unicode-sem-opt | 14.283 | 36.239 | 110592 | 5398528 |
| owned | 13.478 | 31.304 | 106496 | 5337088 |
| owned-sem-opt | 13.536 | 30.995 | 107008 | 5337088 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.9. Os relatórios antigos permanecem históricos.

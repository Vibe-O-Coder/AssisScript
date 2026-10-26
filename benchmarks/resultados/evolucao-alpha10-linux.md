# Evolução alpha.10 — AssisScript 3.3.0-alpha.10 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.10 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| current-heap | 20.081 | 43.246 | 8200 | 270336 |
| current-value | 20.222 | 33.819 | 8200 | 270336 |
| current-heap-sem-opt | 18.459 | 45.477 | 8200 | 270336 |
| current-value-sem-opt | 18.167 | 41.826 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 10000 | 110006 | 2.674 | 270336 |
| 100000 | 1100006 | 19.214 | 270336 |

A CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| current | 0.376 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 16.401 | 20.192 | 8193 | 15990784 |
| slice-sem-opt | 16.137 | 45.972 | 12289 | 15990784 |
| unicode | 28.677 | 14.902 | 17912 | 270336 |
| unicode-sem-opt | 28.911 | 23.506 | 17920 | 270336 |
| owned | 28.151 | 16.817 | 13920 | 270336 |
| owned-sem-opt | 29.457 | 17.141 | 13928 | 270336 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.9. Os relatórios antigos permanecem históricos.

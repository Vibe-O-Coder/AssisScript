# Evolução alpha.8 — AssisScript 3.3.0-alpha.8 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.8 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha7-heap | 19.983 | 53.919 | 8200 | 270336 |
| atual-heap | 18.194 | 53.443 | 8200 | 270336 |
| atual-valor | 17.482 | 41.613 | 8200 | 270336 |
| alpha7-heap-sem-opt | 18.981 | 50.679 | 8200 | 270336 |
| atual-heap-sem-opt | 17.850 | 50.533 | 8200 | 270336 |
| atual-valor-sem-opt | 17.945 | 49.005 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 19.694 | 270336 |
| 1000000 | 11000006 | 190.976 | 270336 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha7 | 0.572 | 270336 |
| atual | 0.603 | 270336 |

## Novos recursos nativos

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| f64 | 19.879 | 16.645 | 8193 | 270336 |
| f64-sem-opt | 18.061 | 16.998 | 8193 | 270336 |
| u32 | 17.607 | 5.693 | 8193 | 270336 |
| u32-sem-opt | 20.029 | 9.630 | 8193 | 270336 |
| json | 59.741 | 23.202 | 72600 | 270336 |
| json-sem-opt | 60.416 | 29.054 | 85040 | 270336 |
| eventos | 34.607 | 50.548 | 36288 | 270336 |
| eventos-sem-opt | 35.781 | 51.030 | 40392 | 270336 |

Saídas conferidas por fórmulas independentes e contratos de JSON/eventos, em debug e nos dois modos. Não há baseline histórico para tipos/APIs que a alpha.7 não admite. Custos de iniciar processo estão incluídos; RAM zero de processo curto significa indisponível. Sem ganho geral prometido.

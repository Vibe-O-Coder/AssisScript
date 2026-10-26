# Evolução alpha.8 — AssisScript 3.3.0-alpha.8 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.8 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha7-heap | 15.857 | 56.895 | 101376 | 5324800 |
| atual-heap | 16.986 | 56.589 | 102400 | 5328896 |
| atual-valor | 16.078 | 45.765 | 102400 | 5263360 |
| alpha7-heap-sem-opt | 15.971 | 61.195 | 101376 | 5324800 |
| atual-heap-sem-opt | 17.129 | 63.029 | 102400 | 5320704 |
| atual-valor-sem-opt | 15.733 | 56.163 | 102400 | 5259264 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 33.085 | 5558272 |
| 1000000 | 11000006 | 173.311 | 5554176 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha7 | 14.624 | 5255168 |
| atual | 14.582 | 5259264 |

## Novos recursos nativos

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| f64 | 15.523 | 29.444 | 102400 | 5259264 |
| f64-sem-opt | 15.548 | 30.362 | 102400 | 5267456 |
| u32 | 15.429 | 19.259 | 101888 | 5259264 |
| u32-sem-opt | 15.476 | 22.817 | 102400 | 5259264 |
| json | 25.230 | 34.684 | 166400 | 5423104 |
| json-sem-opt | 25.291 | 40.354 | 179200 | 5427200 |
| eventos | 20.148 | 17.316 | 128512 | 5431296 |
| eventos-sem-opt | 19.594 | 16.823 | 131584 | 5414912 |

Saídas conferidas por fórmulas independentes e contratos de JSON/eventos, em debug e nos dois modos. Não há baseline histórico para tipos/APIs que a alpha.7 não admite. Custos de iniciar processo estão incluídos; RAM zero de processo curto significa indisponível. Sem ganho geral prometido.

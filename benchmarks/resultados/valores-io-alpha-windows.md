# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.7 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha6-heap | 14.659 | 47.609 | 99840 | 2650112 |
| atual-heap | 16.698 | 55.495 | 101376 | 5320704 |
| atual-valor | 15.299 | 46.940 | 101376 | 5259264 |
| alpha6-heap-sem-opt | 14.912 | 50.270 | 99840 | 2650112 |
| atual-heap-sem-opt | 16.228 | 59.536 | 101376 | 5320704 |
| atual-valor-sem-opt | 14.834 | 53.186 | 101376 | 5255168 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 33.277 | 5545984 |
| 1000000 | 11000006 | 188.406 | 5554176 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha6 | 6.858 | 2584576 |
| atual | 13.841 | 5255168 |

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.7 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha6-heap | 18.877 | 45.873 | 8200 | 270336 |
| atual-heap | 21.066 | 49.422 | 8200 | 270336 |
| atual-valor | 19.874 | 42.245 | 8200 | 270336 |
| alpha6-heap-sem-opt | 21.047 | 51.137 | 8200 | 270336 |
| atual-heap-sem-opt | 19.093 | 49.786 | 8200 | 270336 |
| atual-valor-sem-opt | 19.583 | 45.021 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 17.720 | 270336 |
| 1000000 | 11000006 | 168.001 | 270336 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha6 | 0.489 | 270336 |
| atual | 0.484 | 270336 |

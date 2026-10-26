# Evolução alpha.9 — AssisScript 3.3.0-alpha.9 (nativo, Linux x86_64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.9 (nativo, Linux x86_64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha8-heap | 23.140 | 56.082 | 8200 | 270336 |
| atual-heap | 19.744 | 47.605 | 8200 | 270336 |
| atual-valor | 22.431 | 42.066 | 8200 | 270336 |
| alpha8-heap-sem-opt | 21.673 | 49.885 | 8200 | 270336 |
| atual-heap-sem-opt | 22.316 | 53.395 | 8200 | 270336 |
| atual-valor-sem-opt | 18.380 | 53.683 | 8200 | 270336 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 23.960 | 270336 |
| 1000000 | 11000006 | 179.373 | 270336 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha8 | 0.381 | 270336 |
| atual | 0.405 | 270336 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 16.793 | 42.150 | 8193 | 15990784 |
| slice-sem-opt | 16.946 | 55.564 | 12289 | 15990784 |
| unicode | 29.526 | 22.509 | 17904 | 270336 |
| unicode-sem-opt | 30.175 | 27.680 | 17912 | 270336 |
| proprios | 29.087 | 18.285 | 13992 | 270336 |
| proprios-sem-opt | 29.120 | 18.647 | 14000 | 270336 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.8. Os relatórios antigos permanecem históricos.

## Investigação pareada de variação acima de 5%

21 amostras intercaladas, duas de aquecimento e 10 milhões de iterações por execução; mesma saída N² em debug e emissão normal. As amostras originais acima foram preservadas.

| Variante | Compilar mediana (ms) | Executar mediana (ms) | Mínimo–máximo execução (ms) |
| --- | ---: | ---: | ---: |
| alpha8 | 17.509 | 240.331 | 209.921–314.272 |
| alpha8-sem-opt | 17.614 | 228.092 | 203.623–394.840 |
| atual | 16.220 | 234.290 | 194.286–376.328 |
| atual-sem-opt | 16.550 | 238.488 | 203.039–305.422 |

Início de processo e ASLR permanecem ativos. Diferenças de frequência/agendamento/layout podem afetar resultados; nenhum check foi retirado para melhorar números. Não há promessa de ganho geral.

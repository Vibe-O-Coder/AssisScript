# Evolução alpha.9 — AssisScript 3.3.0-alpha.9 (nativo, Windows x64)

# Valores Copy e IO nativo — AssisScript 3.3.0-alpha.9 (nativo, Windows x64)

7 amostras por variante; 2000000 iterações; início do processo incluído. Saída conferida por N².

| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| alpha8-heap | 15.658 | 56.209 | 102400 | 5328896 |
| atual-heap | 15.488 | 56.382 | 102400 | 5337088 |
| atual-valor | 15.794 | 45.895 | 102400 | 5267456 |
| alpha8-heap-sem-opt | 15.591 | 65.374 | 102400 | 5328896 |
| atual-heap-sem-opt | 16.674 | 62.871 | 102400 | 5328896 |
| atual-valor-sem-opt | 15.728 | 56.907 | 102400 | 5267456 |

A comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.

| CSV (linhas) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: |
| 100000 | 1100006 | 33.722 | 5562368 |
| 1000000 | 11000006 | 195.724 | 5558272 |

A CLI usa buffers fixos, verifica inteiros, erros e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.

| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |
| --- | ---: | ---: |
| alpha8 | 14.541 | 5267456 |
| atual | 14.612 | 5259264 |

## APIs gerenciadas atuais

| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |
| --- | ---: | ---: | ---: | ---: |
| slice | 12.015 | 45.475 | 102912 | 20914176 |
| slice-sem-opt | 12.553 | 51.625 | 102912 | 20922368 |
| unicode | 14.594 | 29.975 | 109568 | 5406720 |
| unicode-sem-opt | 14.668 | 38.320 | 110592 | 5406720 |
| proprios | 14.149 | 31.947 | 106496 | 5341184 |
| proprios-sem-opt | 13.992 | 32.308 | 107008 | 5328896 |

Saídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.8. Os relatórios antigos permanecem históricos.

## Investigação pareada de variação acima de 5%

21 amostras intercaladas, duas de aquecimento e 10 milhões de iterações por execução; mesma saída N² em debug e emissão normal. As amostras originais acima foram preservadas.

| Variante | Compilar mediana (ms) | Executar mediana (ms) | Mínimo–máximo execução (ms) |
| --- | ---: | ---: | ---: |
| alpha8 | 12.464 | 235.876 | 202.703–418.564 |
| alpha8-sem-opt | 18.593 | 268.260 | 237.876–455.075 |
| atual | 12.117 | 244.183 | 203.803–293.352 |
| atual-sem-opt | 22.244 | 277.464 | 242.181–428.312 |

Início de processo e ASLR permanecem ativos. Diferenças de frequência/agendamento/layout podem afetar resultados; nenhum check foi retirado para melhorar números. Não há promessa de ganho geral.

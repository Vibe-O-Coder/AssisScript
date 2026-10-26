# Investigação alpha.8

Onze pares alternados, 40 milhões de itens por processo, uma rodada de aquecimento. N² é conferido independentemente; os checks continuam ativos.

| Variante | Heap (ms) | Version compilador (ms) | Check compilador (ms) |
| --- | ---: | ---: | ---: |
| alpha7 | 861.571 | 8.359 | 8.779 |
| atual | 861.510 | 8.426 | 8.918 |

Version/check medem cinco subprocessos por amostra e apresentam média por subprocesso. Frequência, escalonamento Windows/WSL e antivírus não foram controlados. Dados brutos e hashes no JSON; os resultados iniciais permanecem preservados.

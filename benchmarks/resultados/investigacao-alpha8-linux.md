# Investigação alpha.8

Onze pares alternados, 40 milhões de itens por processo, uma rodada de aquecimento. N² é conferido independentemente; os checks continuam ativos.

| Variante | Heap (ms) | Version compilador (ms) | Check compilador (ms) |
| --- | ---: | ---: | ---: |
| alpha7 | 923.079 | 14.896 | 17.027 |
| atual | 916.276 | 14.032 | 17.157 |

Instruções de funções do usuário iguais após normalizar endereços de saltos/chamadas: True. O layout/endereço do código mudou; essa comparação não prova causalidade das diferenças de tempo.

Version/check medem cinco subprocessos por amostra e apresentam média por subprocesso. Frequência, escalonamento Windows/WSL e antivírus não foram controlados. Dados brutos e hashes no JSON; os resultados iniciais permanecem preservados.

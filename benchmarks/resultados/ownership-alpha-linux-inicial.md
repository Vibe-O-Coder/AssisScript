# Custo de ownership entre funções — alpha.6

AssisScript 3.3.0-alpha.6 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39. 200000 registros/arrays por execução;
7 amostras intercaladas após aquecimento. Saída independente N² = 40000000000.
Inclui início de processo. RAM é pico por processo; não mede retenção prolongada.

| Variante | Mediana ms | Mín–máx ms | Compilação ms | Bytes executável | Mediana pico bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| alpha5-manual | 19.332 | 17.428–24.537 | 20.747 | 16896 | 270336 |
| alpha6-manual | 20.265 | 18.446–24.252 | 20.257 | 16896 | 270336 |
| alpha6-own | 23.086 | 21.236–30.308 | 20.206 | 16896 | 270336 |
| alpha5-manual-sem-opt | 20.770 | 19.669–27.395 | 20.414 | 16896 | 270336 |
| alpha6-manual-sem-opt | 25.804 | 19.513–31.072 | 21.772 | 16896 | 270336 |
| alpha6-own-sem-opt | 25.442 | 22.347–28.746 | 20.382 | 16896 | 270336 |

A variante own faz chamadas adicionais criar/ler e uma chamada de destruição composta. A diferença não isola o custo de análise estática. Não há nova otimização de chamadas. Pico de RAM depende do OS; as métricas Windows/Linux não são diretamente equivalentes. Não demonstra aplicações A/B/C, 24 horas de estabilidade nem paridade com C/C++. Fontes, amostras e hashes no JSON adjacente. --debug terminou sem alocações vivas em todas as variantes.

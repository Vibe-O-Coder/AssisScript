# Custo de ownership entre funções — alpha.6

AssisScript 3.3.0-alpha.6 (nativo, Windows x64); Windows-10-10.0.19045-SP0. 200000 registros/arrays por execução;
7 amostras intercaladas após aquecimento. Saída independente N² = 40000000000.
Inclui início de processo. RAM é pico por processo; não mede retenção prolongada.

| Variante | Mediana ms | Mín–máx ms | Compilação ms | Bytes executável | Mediana pico bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| alpha5-manual | 478.729 | 473.175–494.494 | 15.090 | 107008 | 2719744 |
| alpha6-manual | 478.137 | 472.401–582.288 | 14.406 | 107008 | 2719744 |
| alpha6-own | 473.738 | 469.140–481.902 | 14.663 | 107008 | 2719744 |
| alpha5-manual-sem-opt | 523.516 | 521.374–527.199 | 14.765 | 107520 | 2719744 |
| alpha6-manual-sem-opt | 521.496 | 517.659–526.457 | 14.408 | 107520 | 2719744 |
| alpha6-own-sem-opt | 525.929 | 520.372–582.545 | 14.791 | 108032 | 2719744 |

A variante own faz chamadas adicionais criar/ler e uma chamada de destruição composta. A diferença não isola o custo de análise estática. Não há nova otimização de chamadas. Pico de RAM depende do OS; as métricas Windows/Linux não são diretamente equivalentes. Não demonstra aplicações A/B/C, 24 horas de estabilidade nem paridade com C/C++. Fontes, amostras e hashes no JSON adjacente. --debug terminou sem alocações vivas em todas as variantes.

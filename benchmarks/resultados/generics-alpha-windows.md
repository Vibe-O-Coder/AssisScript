# Custo da especialização escalar — alpha.2

AssisScript 3.3.0-alpha.2 (nativo, Windows x64); Windows-10-10.0.19045-SP0.

10000000 chamadas por execução, 7 amostras intercaladas após aquecimento, com saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Compilação e execução incluem início do processo.

| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |
| --- | ---: | ---: | ---: | ---: |
| manual | 272.007 | 268.128–300.161 | 99328 | 13.091 |
| generico | 286.722 | 275.802–334.791 | 99328 | 13.297 |
| manual-sem-opt | 336.924 | 312.531–352.635 | 99328 | 13.055 |
| generico-sem-opt | 303.463 | 296.967–344.944 | 99328 | 14.075 |

Os fontes e hashes estão no JSON adjacente. Esta carga mede uma especialização int; não mede RAM, explosão de combinações, structs, closures ou aplicações reais. Não sustenta uma conclusão geral de desempenho ou paridade com C/C++.

Binários manual/genérico idênticos: otimizado=True; sem otimização=True. Quando os bytes são iguais, diferenças de tempo refletem variação de execução, não código diferente devido a generics.

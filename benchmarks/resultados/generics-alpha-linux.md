# Custo da especialização escalar — alpha.2

AssisScript 3.3.0-alpha.2 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39.

10000000 chamadas por execução, 7 amostras intercaladas após aquecimento, com saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Compilação e execução incluem início do processo.

| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |
| --- | ---: | ---: | ---: | ---: |
| manual | 53.303 | 46.975–64.574 | 8193 | 20.987 |
| generico | 52.650 | 48.659–63.443 | 8193 | 20.178 |
| manual-sem-opt | 85.810 | 77.365–91.576 | 8193 | 20.720 |
| generico-sem-opt | 84.432 | 81.031–100.906 | 8193 | 20.623 |

Os fontes e hashes estão no JSON adjacente. Esta carga mede uma especialização int; não mede RAM, explosão de combinações, structs, closures ou aplicações reais. Não sustenta uma conclusão geral de desempenho ou paridade com C/C++.

Binários manual/genérico idênticos: otimizado=True; sem otimização=True. Quando os bytes são iguais, diferenças de tempo refletem variação de execução, não código diferente devido a generics.

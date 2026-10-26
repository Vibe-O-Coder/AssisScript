# Custo de funções como valores — alpha.3

AssisScript 3.3.0-alpha.3 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39.

5000000 chamadas, 7 amostras intercaladas após aquecimento. Saída conferida por 3*N*(N-1)/2+7*N. Tempos incluem início do processo.

| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |
| --- | ---: | ---: | ---: | ---: |
| direta | 25.308 | 24.436–26.626 | 8193 | 24.211 |
| indireta | 28.906 | 26.430–32.755 | 8193 | 22.024 |
| ordem-superior | 49.849 | 44.470–52.548 | 8193 | 22.147 |
| direta-sem-opt | 42.100 | 38.840–47.597 | 8193 | 24.049 |
| indireta-sem-opt | 43.711 | 42.390–47.753 | 8193 | 23.247 |
| ordem-superior-sem-opt | 71.247 | 69.162–74.333 | 8193 | 22.547 |

Chamadas indiretas acrescentam uma carga/endereço e salto; ordem superior inclui outra chamada. Não há inlining ou desvirtualização novos. Os fontes, amostras e hashes estão no JSON adjacente. Esta carga não mede RAM, coleções, closures ou aplicações reais, nem estabelece paridade com C/C++.

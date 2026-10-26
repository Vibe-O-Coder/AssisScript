# Custo de funções como valores — alpha.3

AssisScript 3.3.0-alpha.3 (nativo, Windows x64); Windows-10-10.0.19045-SP0.

5000000 chamadas, 7 amostras intercaladas após aquecimento. Saída conferida por 3*N*(N-1)/2+7*N. Tempos incluem início do processo.

| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |
| --- | ---: | ---: | ---: | ---: |
| direta | 237.909 | 233.437–240.708 | 99328 | 12.904 |
| indireta | 270.732 | 265.755–290.200 | 99328 | 13.172 |
| ordem-superior | 304.045 | 298.810–309.824 | 99840 | 13.367 |
| direta-sem-opt | 250.508 | 248.445–278.113 | 99328 | 12.800 |
| indireta-sem-opt | 275.171 | 268.476–285.134 | 99840 | 12.594 |
| ordem-superior-sem-opt | 319.274 | 315.110–323.706 | 99840 | 13.184 |

Chamadas indiretas acrescentam uma carga/endereço e salto; ordem superior inclui outra chamada. Não há inlining ou desvirtualização novos. Os fontes, amostras e hashes estão no JSON adjacente. Esta carga não mede RAM, coleções, closures ou aplicações reais, nem estabelece paridade com C/C++.

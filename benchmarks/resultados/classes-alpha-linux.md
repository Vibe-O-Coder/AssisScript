# Custo de classes especializadas — alpha.4

AssisScript 3.3.0-alpha.4 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39.

1000000 chamadas virtuais por execução, 7 amostras intercaladas após aquecimento. Cada programa aloca/libera 1/8/32/64 objetos de tipos distintos e confere a soma pela fórmula `3*N*(N-1)/2+7*N`. Compilação e execução incluem início do processo.

| Variante | Instâncias | Execução mediana ms | Mín–máx ms | Bytes | Compilação mediana ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| manual | 1 | 6.148 | 5.242–9.279 | 8216 | 17.478 |
| generico | 1 | 6.035 | 5.266–11.686 | 8216 | 17.240 |
| manual-sem-opt | 1 | 8.889 | 8.694–12.063 | 8216 | 17.321 |
| generico-sem-opt | 1 | 9.972 | 8.665–15.778 | 8216 | 19.091 |
| manual | 8 | 6.344 | 5.954–7.195 | 12480 | 19.508 |
| generico | 8 | 6.827 | 5.846–11.227 | 12480 | 19.592 |
| manual-sem-opt | 8 | 9.891 | 9.142–14.596 | 12480 | 20.372 |
| generico-sem-opt | 8 | 9.912 | 8.567–11.934 | 12480 | 19.616 |
| manual | 32 | 6.584 | 6.407–10.830 | 21248 | 21.153 |
| generico | 32 | 6.624 | 6.095–9.440 | 21248 | 22.027 |
| manual-sem-opt | 32 | 9.885 | 9.550–12.468 | 21248 | 21.697 |
| generico-sem-opt | 32 | 10.466 | 8.978–14.102 | 21248 | 21.047 |
| manual | 64 | 7.554 | 6.229–10.267 | 34304 | 23.272 |
| generico | 64 | 7.040 | 6.131–10.300 | 34304 | 28.834 |
| manual-sem-opt | 64 | 8.811 | 8.653–10.771 | 34304 | 22.382 |
| generico-sem-opt | 64 | 9.412 | 8.669–13.730 | 34304 | 25.739 |

Fontes, amostras e hashes estão no JSON adjacente. Esta carga mede especialização nominal e crescimento de código/métodos; o laço usa apenas a primeira classe. As classes manuais têm as mesmas assinaturas concretas, com o mesmo despacho virtual existente. Não há desvirtualização ou novo inlining. Não mede RAM, recursos proprietários, coleções funcionais nem aplicações reais e não sustenta paridade geral com C/C++.

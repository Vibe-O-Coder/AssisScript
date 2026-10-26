# Custo de classes especializadas — alpha.4

AssisScript 3.3.0-alpha.4 (nativo, Windows x64); Windows-10-10.0.19045-SP0.

1000000 chamadas virtuais por execução, 7 amostras intercaladas após aquecimento. Cada programa aloca/libera 1/8/32/64 objetos de tipos distintos e confere a soma pela fórmula `3*N*(N-1)/2+7*N`. Compilação e execução incluem início do processo.

| Variante | Instâncias | Execução mediana ms | Mín–máx ms | Bytes | Compilação mediana ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| manual | 1 | 323.007 | 311.687–324.577 | 99840 | 12.581 |
| generico | 1 | 320.199 | 316.740–331.350 | 99840 | 12.681 |
| manual-sem-opt | 1 | 329.726 | 322.848–347.026 | 99840 | 12.843 |
| generico-sem-opt | 1 | 327.890 | 323.090–333.052 | 99840 | 12.477 |
| manual | 8 | 327.298 | 320.010–343.739 | 102400 | 13.105 |
| generico | 8 | 327.639 | 319.997–365.009 | 102400 | 13.216 |
| manual-sem-opt | 8 | 328.233 | 324.691–352.658 | 102400 | 12.690 |
| generico-sem-opt | 8 | 330.445 | 321.805–352.920 | 102400 | 12.885 |
| manual | 32 | 347.309 | 337.522–374.860 | 112128 | 14.288 |
| generico | 32 | 337.957 | 327.661–415.440 | 112128 | 14.731 |
| manual-sem-opt | 32 | 344.118 | 328.565–504.688 | 111616 | 14.212 |
| generico-sem-opt | 32 | 335.583 | 328.670–432.026 | 111616 | 15.290 |
| manual | 64 | 337.767 | 329.928–397.481 | 124928 | 29.945 |
| generico | 64 | 336.940 | 327.130–361.770 | 124928 | 20.401 |
| manual-sem-opt | 64 | 337.540 | 326.861–342.115 | 123904 | 29.772 |
| generico-sem-opt | 64 | 335.644 | 329.693–341.624 | 123904 | 20.594 |

Fontes, amostras e hashes estão no JSON adjacente. Esta carga mede especialização nominal e crescimento de código/métodos; o laço usa apenas a primeira classe. As classes manuais têm as mesmas assinaturas concretas, com o mesmo despacho virtual existente. Não há desvirtualização ou novo inlining. Não mede RAM, recursos proprietários, coleções funcionais nem aplicações reais e não sustenta paridade geral com C/C++.

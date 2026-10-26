# Custo do primeiro incremento funcional

AssisScript 3.3.0-alpha.1 (nativo, Windows x64); Windows-10-10.0.19045-SP0.

10000000 chamadas escalares, 7 amostras intercaladas após um aquecimento. Todas as saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Tempos incluem início do processo.

| Variante | Mediana ms | Mín–máx ms | Bytes | Compilação ms (uma observação) |
| --- | ---: | ---: | ---: | ---: |
| atual-legado | 50.337 | 49.179–54.779 | 99328 | 44.378 |
| atual-puro | 48.841 | 47.853–52.030 | 99328 | 25.809 |
| atual-puro-sem-opt | 84.839 | 79.076–95.845 | 99328 | 17.743 |
| base-3.2-legado | 50.157 | 48.078–57.825 | 99328 | 16.100 |

Os fontes têm os mesmos vínculos e operações: a variante funcional troca let por val e anota a função com pure. pure/val não ativam otimizações novas. Hashes e amostras estão no JSON adjacente. Não mede generics, closures, RAM ou aplicações completas e não permite concluir paridade com C/C++. Diferenças dentro da faixa de variação exigem repetição antes de atribuir causa.

As variantes otimizadas, incluindo a base quando informada, geraram executáveis idênticos byte a byte neste caso. A diferença entre seus tempos não corresponde a uma diferença de código emitido.

# Custo do primeiro incremento funcional

AssisScript 3.3.0-alpha.1 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39.

10000000 chamadas escalares, 7 amostras intercaladas após um aquecimento. Todas as saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Tempos incluem início do processo.

| Variante | Mediana ms | Mín–máx ms | Bytes | Compilação ms (uma observação) |
| --- | ---: | ---: | ---: | ---: |
| atual-legado | 48.291 | 46.293–56.793 | 8193 | 14.383 |
| atual-puro | 58.518 | 44.242–62.690 | 8193 | 20.393 |
| atual-puro-sem-opt | 84.532 | 80.029–88.955 | 8193 | 17.629 |
| base-3.2-legado | 55.775 | 51.835–66.868 | 8193 | 18.921 |

Os fontes têm os mesmos vínculos e operações: a variante funcional troca let por val e anota a função com pure. pure/val não ativam otimizações novas. Hashes e amostras estão no JSON adjacente. Não mede generics, closures, RAM ou aplicações completas e não permite concluir paridade com C/C++. Diferenças dentro da faixa de variação exigem repetição antes de atribuir causa.

As variantes otimizadas, incluindo a base quando informada, geraram executáveis idênticos byte a byte neste caso. A diferença entre seus tempos não corresponde a uma diferença de código emitido.

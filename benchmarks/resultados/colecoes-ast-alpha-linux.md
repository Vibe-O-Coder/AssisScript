# Migração AST das coleções — alpha.5

AssisScript 3.3.0-alpha.5 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39.

Base: AssisScript 3.3.0-alpha.4 (nativo, Linux x86_64).

Conclusão estimada do plano nesta entrega: **34%**, pela [régua de progresso](../../docs/PROGRESSO.md). A porcentagem mede atendimento do plano e não desempenho.

7 amostras intercaladas após aquecimento, com/sem otimização. Cada tipo nominal acrescenta Array<Tag> e HashMap<int,Tag>; há também Array<int>/HashMap<int,int>. O laço usa 2000 elementos e confere `2*(3*N*(N-1)/2+7*N)`. Compilação e execução incluem início de processo.

| Compilador | Tipos nominais | Modo | Compilação mediana ms | Execução mediana ms | Mín–máx execução ms | Bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| alpha4 | 1 | opt | 29.232 | 1.493 | 1.308–2.224 | 41968 |
| alpha5 | 1 | opt | 19.538 | 1.446 | 1.357–1.759 | 41968 |
| alpha4 | 1 | sem opt | 21.973 | 1.617 | 1.345–2.415 | 46064 |
| alpha5 | 1 | sem opt | 20.642 | 1.580 | 1.398–1.876 | 46064 |
| alpha4 | 8 | opt | 38.180 | 1.654 | 1.458–2.135 | 154072 |
| alpha5 | 8 | opt | 29.174 | 1.592 | 1.336–2.886 | 154072 |
| alpha4 | 8 | sem opt | 36.370 | 1.815 | 1.590–2.861 | 174552 |
| alpha5 | 8 | sem opt | 29.132 | 1.715 | 1.525–2.841 | 174552 |
| alpha4 | 32 | opt | 83.190 | 1.769 | 1.527–2.117 | 544280 |
| alpha5 | 32 | opt | 54.496 | 1.752 | 1.390–2.087 | 544280 |
| alpha4 | 32 | sem opt | 80.242 | 1.746 | 1.629–2.472 | 609816 |
| alpha5 | 32 | sem opt | 52.878 | 1.743 | 1.464–2.088 | 609816 |
| alpha4 | 64 | opt | 163.273 | 1.648 | 1.573–2.040 | 1059096 |
| alpha5 | 64 | opt | 112.418 | 1.820 | 1.538–2.137 | 1059096 |
| alpha4 | 64 | sem opt | 165.093 | 1.784 | 1.678–2.104 | 1190168 |
| alpha5 | 64 | sem opt | 109.892 | 1.822 | 1.718–2.380 | 1190168 |

Fontes, hashes e amostras no JSON adjacente. A carga exercita especializações distintas e crescimento de código, com operações escalares de coleção. Não mede RAM, vidas entre funções, estruturas persistentes, textos grandes ou aplicações reais. Tempos de execução incluem startup e não sustentam uma conclusão de desempenho geral. Layout, hashing, bounds e algoritmos são preservados.

Todos os pares de executáveis são idênticos byte a byte: True. Quando os bytes coincidem, variações no tempo de execução não correspondem a alterações no código emitido.

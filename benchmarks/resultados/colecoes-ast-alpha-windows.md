# Migração AST das coleções — alpha.5

AssisScript 3.3.0-alpha.5 (nativo, Windows x64); Windows-10-10.0.19045-SP0.

Base: AssisScript 3.3.0-alpha.4 (nativo, Windows x64).

Conclusão estimada do plano nesta entrega: **34%**, pela [régua de progresso](../../docs/PROGRESSO.md). A porcentagem mede atendimento do plano e não desempenho.

7 amostras intercaladas após aquecimento, com/sem otimização. Cada tipo nominal acrescenta Array<Tag> e HashMap<int,Tag>; há também Array<int>/HashMap<int,int>. O laço usa 2000 elementos e confere `2*(3*N*(N-1)/2+7*N)`. Compilação e execução incluem início de processo.

| Compilador | Tipos nominais | Modo | Compilação mediana ms | Execução mediana ms | Mín–máx execução ms | Bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| alpha4 | 1 | opt | 17.048 | 102.824 | 96.856–119.520 | 133120 |
| alpha5 | 1 | opt | 16.778 | 98.573 | 95.950–119.652 | 133120 |
| alpha4 | 1 | sem opt | 16.916 | 116.717 | 111.549–128.866 | 137216 |
| alpha5 | 1 | sem opt | 16.724 | 110.674 | 108.226–151.784 | 137216 |
| alpha4 | 8 | opt | 28.710 | 123.865 | 113.546–133.583 | 249856 |
| alpha5 | 8 | opt | 22.391 | 124.384 | 111.223–133.605 | 249856 |
| alpha4 | 8 | sem opt | 27.789 | 142.962 | 128.441–166.050 | 268288 |
| alpha5 | 8 | sem opt | 22.681 | 132.772 | 128.985–158.884 | 268288 |
| alpha4 | 32 | opt | 77.357 | 162.477 | 153.366–207.830 | 651776 |
| alpha5 | 32 | opt | 47.783 | 157.001 | 153.626–173.098 | 651776 |
| alpha4 | 32 | sem opt | 75.749 | 195.638 | 191.521–217.024 | 718848 |
| alpha5 | 32 | sem opt | 47.725 | 203.748 | 195.444–248.236 | 718848 |
| alpha4 | 64 | opt | 174.158 | 226.464 | 216.802–241.639 | 1186304 |
| alpha5 | 64 | opt | 118.906 | 233.607 | 222.479–294.114 | 1186304 |
| alpha4 | 64 | sem opt | 190.676 | 349.778 | 287.567–358.499 | 1317888 |
| alpha5 | 64 | sem opt | 118.541 | 296.849 | 289.866–373.121 | 1317888 |

Fontes, hashes e amostras no JSON adjacente. A carga exercita especializações distintas e crescimento de código, com operações escalares de coleção. Não mede RAM, vidas entre funções, estruturas persistentes, textos grandes ou aplicações reais. Tempos de execução incluem startup e não sustentam uma conclusão de desempenho geral. Layout, hashing, bounds e algoritmos são preservados.

Todos os pares de executáveis são idênticos byte a byte: True. Quando os bytes coincidem, variações no tempo de execução não correspondem a alterações no código emitido.

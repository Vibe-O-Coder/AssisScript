# Medições do AssisScript 3.1

Execução: 2026-10-24T16:11:34.509Z. win32 10.0.19045 x64; Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz; Node v24.17.0.

7 amostras após 1 aquecimento; mediana, incluindo início do processo. Compilação medida em três amostras separadas. Cada saída foi validada.

| Programa | Variante | Execução mediana (ms) | Mín–máx (ms) | Compilação mediana (ms) | Bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| aritmetica | 3.0 anterior | 369.95 | 331.56–388.48 | 50.55 | 98816 |
| aritmetica | 3.1 otimizado | 192.59 | 184.81–209.17 | 52.69 | 98304 |
| aritmetica | 3.1 sem otimização | 323.17 | 312.24–355.36 | 48.47 | 98816 |
| hashmap | 3.0 anterior | 136.81 | 131.31–141.33 | 51.64 | 114176 |
| hashmap | 3.1 otimizado | 98.33 | 94.67–105.77 | 49.69 | 113152 |
| hashmap | 3.1 sem otimização | 108.16 | 105.40–112.69 | 53.89 | 116736 |
| array | 3.0 anterior | 66.90 | 66.62–76.36 | 52.93 | 104960 |
| array | 3.1 otimizado | 62.66 | 61.49–66.68 | 49.94 | 104448 |
| array | 3.1 sem otimização | 67.92 | 66.39–69.56 | 48.45 | 105984 |
| texto-prefixo | 3.0 anterior | 305.67 | 287.11–334.81 | 53.13 | 100864 |
| texto-prefixo | 3.1 otimizado | 47.37 | 44.76–50.60 | 57.37 | 100352 |
| texto-prefixo | 3.1 sem otimização | 47.74 | 43.47–51.83 | 51.88 | 100864 |

O caso texto-prefixo compara o laço da biblioteca anterior (indexação verificada) ao laço da biblioteca nova (bytes limitados por comprimento). As outras cargas usam o mesmo fonte em todas as variantes. Diferenças próximas ao custo de iniciar um processo não são conclusivas. Não há comparação com outras linguagens. Dados brutos: [benchmark.json](benchmark.json).

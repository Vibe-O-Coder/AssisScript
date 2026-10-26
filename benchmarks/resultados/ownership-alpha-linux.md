# Custo de ownership entre funções — alpha.6

AssisScript 3.3.0-alpha.6 (nativo, Linux x86_64); Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39. 2000000 registros/arrays por execução;
7 amostras intercaladas após aquecimento. Saída independente N² = 4000000000000.
Inclui início de processo. RAM é pico por processo; não mede retenção prolongada.

| Variante | Mediana ms | Mín–máx ms | Compilação ms | Bytes executável | Mediana pico bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| alpha5-manual | 166.513 | 163.451–174.714 | 29.506 | 16896 | 270336 |
| alpha6-manual | 168.796 | 164.277–182.781 | 26.483 | 16896 | 270336 |
| alpha6-own | 201.085 | 196.934–218.277 | 26.797 | 16896 | 270336 |
| alpha5-manual-sem-opt | 179.341 | 178.116–200.947 | 30.264 | 16896 | 270336 |
| alpha6-manual-sem-opt | 181.817 | 177.124–237.076 | 26.305 | 16896 | 270336 |
| alpha6-own-sem-opt | 192.183 | 189.827–232.389 | 26.122 | 16896 | 270336 |

A variante own faz chamadas adicionais criar/ler e uma chamada de destruição composta. A diferença não isola o custo de análise estática. Não há nova otimização de chamadas. Pico de RAM depende do OS; as métricas Windows/Linux não são diretamente equivalentes. Não demonstra aplicações A/B/C, 24 horas de estabilidade nem paridade com C/C++. Fontes, amostras e hashes no JSON adjacente. --debug terminou sem alocações vivas em todas as variantes.

Identidade byte a byte das referências manuais alpha.5/alpha.6: {"optimized": true, "-sem-opt": true}. Diferenças entre tempos de arquivos idênticos refletem variação da medição.

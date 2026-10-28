# Validação — 3.3.0-alpha.13

Data: 26/10/2026, contexto do usuário. **92% estimados (91,5/100 pontos)**,
sem alteração dos pesos ou dos estados históricos. [Handoff](HANDOFF-3.3-ALPHA.13.md),
[contrato](CAPTURAS-E-VARIANTES-MOVE.md), [restante](RESTANTE-PARA-100.md).

## Base, reconstrução e fontes

Preservadas as alterações alpha.11/12 recebidas sobre `257e719`. Os binários
alpha.12 e um patch dos arquivos rastreados ficaram em `build/alpha12-baseline`.
Nenhum reset, commit, push ou CI remota foi executado.

Windows GCC MSYS2 15.2.0; Linux GCC Ubuntu 13.3.0/WSL. As reconstruções limpas
copiaram só entradas de fonte, removeram os blobs dessa cópia e regeneraram
os dois runtimes. Os compiladores produzidos são byte a byte idênticos aos
binários que passaram a matriz completa do workspace. As duas novas suítes
(25 casos) também passaram diretamente nas reconstruções limpas. Não se
promete identidade com outra toolchain. Logs em `build/clean-*-alpha13.log`.

| Binário | SHA-256 |
| --- | --- |
| bin/assis.exe | `e992e3b9affc8372aac538844949d8fe1fef74ca3b0e1bc9b25ebf328fc78052` |
| bin/assis-setup.exe | `b33b1f27e185f1eb36665a372612678c43eb1c57a176c6607bc9626ac20ef868` |
| bin/assis | `99ebbcbf457aabf855fcf2afe8d262a019715b49abbdfbca0ac2dcbc530251d6` |

## Gates executados

| Conjunto | Resultado |
| --- | --- |
| Matriz nativa Windows | 29 suítes, 263 testes relatados: 261 aprovados, 2 ignorados |
| Matriz nativa Linux | 29 suítes, 263 testes relatados: 262 aprovados, 1 ignorado |
| Node/editor/LSP/ferramentas Windows | 84 aprovados |
| Corpus nativo Windows/instalador | 130 verificações aprovadas |
| Corpus nativo Linux | 133 verificações, incluindo 256 operações aritméticas |
| Módulos/instalação/remoção Linux | 28 verificações aprovadas |
| Harness PE no Linux | 41 casos com base relocada e ABI Microsoft |
| Replay do corpus 3.1 recém-gerado | 18 verificações Windows, 22 Linux |
| Replay do corpus 3.2 recém-gerado | 73 casos em cada sistema |

Conjuntos sobrepostos não devem ser somados como casos independentes. Os
ignorados são GDB/ELF e criação de symlink indisponível no Windows; alias de
caminho Windows 8.3 no Linux. GDB executou no Linux. A geração específica
do corpus 3.1 repetiu 13 testes que já pertencem aos 84, sem crédito adicional.
Os relatórios `build/native-validation-alpha13-*.json` guardam os resultados
das 29 suítes por sistema. Logs Node, corpus, instalador e replay têm sufixo
alpha13 em `build/`.

Os 25 novos casos cobrem interfaces check/build/run, otimizado/sem otimização,
emissão cruzada e execução nativa PE/ELF. Rejeições mantêm o arquivo de saída
sentinela e não executam o fonte rejeitado. Variantes: payload ativo, recursão,
generics, retornos/argumentos, Copy aninhado, extração, empréstimo, estados após
move e limpeza em return/break/continue. Closures: snapshots, own/borrow,
mutabilidade/exclusividade, generics, campos/OwnedList, ambientes aninhados,
retornos compostos/borrow(self), slices, ordem de destruição, pipeline e
OwnedResult. Foram rejeitadas cópias de recursos, captura borrow que escapa,
movimento parcial de captura, mutação de borrow, chamadas legadas ocultas,
conversão closure→fn e captura aninhada que apagaria a vida emprestada.

## Ensaio curto real de serviços

`tools/soak-native.py --duration 120 --workers 4 --polling` passou nos dois
sistemas sobre fontes/compiladores congelados. Exercita B/C, recuperação,
polling, cancelamento e recursos do OS; não é um ensaio de 24 horas das novas
closures. `qualifies24Hours=false` em ambos os relatórios.

| Sistema | Segundos | Ciclos | Maior RSS por serviço | Handles/descritores |
| --- | ---: | ---: | ---: | --- |
| windows | 120.556 | 7499 | 5734400 bytes | 91→91, 91→91, 91→91, 91→91 |
| linux | 120.525 | 8904 | 1347584 bytes | 4→4, 4→4, 4→4, 4→4 |

[Windows](../benchmarks/resultados/soak-alpha13-windows.json),
[Linux](../benchmarks/resultados/soak-alpha13-linux.json). P4-SOAK permanece parcial.
O heap continua de uma thread; processos isolados não provam segurança multithread.

## Medições, procedência e distribuição

Sete amostras, aquecimento e variantes intercaladas, saídas conferidas contra
resultados independentes, com tempo de compilação/execução, tamanho e pico de RAM.
As 16 variantes de APIs incluem os novos custos de chamadas/capturas e invólucros
Move, com/sem otimização. Os workloads anteriores usam a alpha.12 preservada
como referência. Início de processo está incluído; medidas curtas têm ruído.
Não se conclui equivalência geral com C/C++ ou prontidão de produção.

[Medição Windows](../benchmarks/resultados/evolucao-alpha13-windows.md),
[medição Linux](../benchmarks/resultados/evolucao-alpha13-linux.md),
[otimizações Windows](../benchmarks/resultados/optimization-alpha13-windows.json),
[otimizações Linux](../benchmarks/resultados/optimization-alpha13-linux.json).

Os inventários [Windows](build-audit-windows.json) e [Linux](build-audit-linux.json)
foram regenerados a partir dos mapas reais e reproduziram os três binários
distribuídos. Isso não resolve direitos de imagens ou revisão de redistribuição.

O catálogo mantém 19 bibliotecas e o instalador 236 caminhos obrigatórios.
O lockfile offline foi regenerado: `f23b90d5a7ad08a05b58fc9ac6b92c5680406d301d67d471266e4e7659b2beda`.
ZIP/VSIX incluem fontes, compiladores, documentos, novo exemplo, bibliotecas,
inventários e medições. A verificação executa os compiladores extraídos,
as aplicações A/B/C/polling, FFI e o novo exemplo, confere safe/legacy,
rejeições de ownership/capturas, hashes de medições/fontes e todo o SHA256SUMS.
**Pacotes aprovados nos dois sistemas: 19 bibliotecas e 687 hashes verificados.**
Os compiladores extraídos executaram os exemplos e as rejeições novas. Os
pacotes foram regenerados após consolidar este relatório e conferidos novamente.
Não houve aceite humano independente ou CI remota.

## Custo observado e investigação de variação

| Variante | Windows (ms) | Linux (ms) |
| --- | ---: | ---: |
| closure-call | 26.735 | 11.397 |
| closure-call-sem-opt | 29.988 | 16.754 |
| closure-borrow | 26.511 | 16.596 |
| closure-borrow-sem-opt | 50.429 | 39.975 |
| move-enum | 26.922 | 13.209 |
| move-enum-sem-opt | 27.035 | 14.364 |

Chamadas de closure: dois milhões por processo; enum Move: 249984 construções/extrações, com buffer de dois inteiros. São custos absolutos destas cargas, com startup incluído, sem comparação histórica para APIs ausentes.

- windows: as sete cargas de otimização produziram executáveis SHA-256 idênticos entre alpha.12 e alpha.13. Maior razão entre passos adversos e passo 1: 0.911× (gate 5×).
- linux: as sete cargas de otimização produziram executáveis SHA-256 idênticos entre alpha.12 e alpha.13. Maior razão entre passos adversos e passo 1: 1.079× (gate 5×).

As diferenças acima de 5% observadas em hash passo 1 no Windows e alocação grande no Linux foram investigadas por essa identidade dos bytes. Não são evidência de mudança do código gerado; startup/escalonamento/ruído do host continuam visíveis. Saídas e fontes foram conferidos, sem retirar validações.

## Pendências

24 horas reais; emissão completa por IR e otimizações amplas; ARM64/macOS;
direitos de imagens/revisão de distribuição; aceite humano independente.
As limitações das APIs legadas permanecem; novos contratos não as ampliam
retroativamente. Nenhum critério externo foi encerrado por autorrevisão.

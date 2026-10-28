# Validação — 3.3.0-alpha.12

Data: 26/10/2026, contexto do usuário. **90% estimados (89,5/100 pontos)** pela régua original de 35 critérios, sem alteração de pesos. [Handoff](HANDOFF-3.3-ALPHA.12.md), [progresso](PROGRESSO.md), [safe padrão](SAFE-DEFAULT.md), [rede cooperativa](BIBLIOTECA-net.md).

## Base e reconstrução

Árvore alpha.11 recebida com alterações ainda sem commit sobre `257e719`; preservadas. Os binários recebidos foram copiados para `build/alpha11-baseline` e conferidos contra os hashes da validação alpha.11. Não houve reset, commit, push ou CI remota nesta sessão.

Reconstruções em diretórios temporários copiaram somente fontes de entrada, regeneraram os dois runtimes e reproduziram exatamente os binários do workspace. As 25 suítes anteriores e as duas novas foram executadas sobre reconstruções limpas do mesmo hash final. `validate-clean.py` agora inclui as 27 suítes por padrão; --suite permite repetir somente uma parte. Windows GCC MSYS2 15.2.0; Linux GCC Ubuntu 13.3.0/WSL. Não se promete identidade com outra toolchain.

| Binário | SHA-256 |
| --- | --- |
| bin/assis.exe | `e881083d921aea699205dffd79ea29eda177d0b439e349f7fdb3263b5f55e481` |
| bin/assis-setup.exe | `367c9de6c347c1b8a451476163d11806e0be68d7abd02c9f885fa4639124e25f` |
| bin/assis | `451eafb71f3f30ec91f5df5d0d43d8d4c0609f4df27ca421d61743c7fe634b4e` |

## Gates executados

| Conjunto | Resultado |
| --- | --- |
| Reconstrução limpa Windows | 27 suítes, 238 testes relatados; 2 ignorados (GDB e symlink indisponível) |
| Reconstrução limpa Linux | 27 suítes, 238 testes relatados; 1 ignorado (alias de caminho Windows 8.3) |
| Node/editor/LSP/instalador Windows | 82 aprovados |
| Corpus nativo Windows | 130 verificações aprovadas |
| Corpus nativo Linux | 133 verificações, incluindo 256 operações aritméticas |
| Módulos/instalação/remoção Linux | 27 verificações aprovadas |
| Emissão PE32+ executada no harness Linux | 41 casos com base relocada/ABI Microsoft |
| Corpus Node recém-gerado | 30 testes aprovados; subconjunto dos 82, não somar |
| Replay desse corpus Windows | 18 verificações 3.1 e 73 casos 3.2 |
| Mesmo corpus Linux | 22 verificações 3.1 e 73 casos 3.2 |

As suítes têm sobreposição e não são uma soma de casos independentes. Os ignorados estão identificados por plataforma; GDB executou no Linux. Logs locais em `build/clean-*-alpha12.log`, `build/clean-new-*-alpha12.log`, `build/node-alpha12.log`, `build/windows-alpha12.log`, `build/native-linux-alpha12.log` e `build/portable-*-alpha12.log`. `build/native-validation-alpha12-*.json` consolida os 27 resultados por sistema.

As novas suítes têm 13 casos: segurança padrão (5) e rede (8). Exercitam check/build/run, emissão cruzada e execução nativa com/sem otimização. Rejeições preservam o arquivo de saída e não executam fontes rejeitados. Foram testados opt-out explícito/ordem de flags, fronteiras raw/text, chamadas indiretas/ramos mortos e reentrada de inicializadores. No módulo net: bytes NUL/UTF-8, limite exato/excedido, 404/redirect/desconexão, timeout, duas requisições intercaladas, evento cooperativo durante IO, cancelamento antes/durante/parcial, destruição pendente e aplicação B preservando o arquivo ao cancelar.

TLS local: certificado não confiado recusado, o mesmo certificado aceito somente por CA explícita da requisição e hostname divergente recusado. Nenhum certificado foi instalado no OS. A libcurl usada no Windows foi a existente em Git for Windows; o módulo declara libcurl como dependência opcional e não exige Git. No Linux foi usada a biblioteca do sistema. Uma sessão longa com 64 operações alternando conclusão/cancelamento/destruição confirmou liberação de handles, além dos contadores de heap em debug.

## Ensaio curto real

`tools/soak-native.py --duration 120 --workers 4 --polling` executou aplicação B com polling e quatro serviços C persistentes por sistema. Ciclos conferem estado, bytes, erros HTTP/comandos, cancelamentos e reabertura após reinício. O harness recusa alteração de fontes/compilador durante a medição.

| Sistema | Segundos | Ciclos | Maior RSS por serviço | Handles/descritores |
| --- | ---: | ---: | ---: | --- |
| windows | 120.542 | 7682 | 5697536 bytes | 91→91, 91→91, 91→91, 91→91 |
| linux | 120.523 | 9000 | 1351680 bytes | 4→4, 4→4, 4→4, 4→4 |

[Windows](../benchmarks/resultados/soak-alpha12-windows.json), [Linux](../benchmarks/resultados/soak-alpha12-linux.json). **Nenhuma execução efetiva de 24 horas foi concluída.** `qualifies24Hours=false`; P4-SOAK continua parcial. Processos isolados não demonstram heap multithread.

## Desempenho e procedência

Sete amostras, aquecimento, variantes intercaladas e saídas conferidas. Medições de valores/CSV, compilação, bytes e pico de RAM: [Windows](../benchmarks/resultados/evolucao-alpha12-windows.md), [Linux](../benchmarks/resultados/evolucao-alpha12-linux.md). Dez variantes atuais incluem slices, UTF-8, lista proprietária, dois milhões de chamadas C e callback qsort. Os hashes de todos os fontes src/stdlib foram conferidos com a árvore final.

A comparação de otimizações foi repetida após os ensaios de carga: [Windows](../benchmarks/resultados/optimization-alpha12-windows.json), [Linux](../benchmarks/resultados/optimization-alpha12-linux.json). **Os sete executáveis de cada par alpha.11/alpha.12 têm SHA-256 idênticos**, agora registrados individualmente. Variações maiores que 5% foram investigadas por essa comparação; inclusive a mediana Windows de hash passo 4096 variou cerca de 2,10× entre arquivos com os mesmos bytes. Startup, escalonamento e efeitos do host tornam estes tempos curtos ruidosos; não atribuir ganho ou regressão de código a esses números. O maior quociente entre passos adversos e passo 1 ficou 1,122× no Windows e 1,074× no Linux, abaixo do gate de 5×. Isso não comprova resistência universal a hash adverso nem desempenho de produção.

[Inventário Windows](build-audit-windows.json): 14 entradas de ligação em cada um dos dois binários, com 185 e 135 membros de archives selecionados. [Linux](build-audit-linux.json): 8 entradas e 491 membros. Os relatórios registram também inputs sem membros selecionados (por exemplo winpthreads), objetos de startup, imports, hashes de arquivos/ferramenta/fontes e a identidade da reconstrução. O script falha para arquivos não resolvidos ou grupos técnicos desconhecidos. Avisos GCC/MinGW/winpthreads e LGPL 2.1 acompanham a distribuição. Isso não encerra direitos de imagens ou revisão de termos/fontes de redistribuição; P6-POLICY permanece parcial.

## Distribuição

ZIP e VSIX alpha.12 incluem 19 módulos, fontes, instaladores, contratos, perfis safe/legacy, novo exemplo B, inventários e relatórios. O manifesto Windows contém 221 caminhos obrigatórios. O lockfile offline foi regenerado com a versão corrente e reproduzido nos dois sistemas: `f5025246bc7b41ef152e89eb030633f35dfc1a3419d76de667b67b120ae1dabc`.

A verificação dos pacotes executa os compiladores extraídos, as 19 bibliotecas, aplicações A/B/C/cliente polling, ferramentas, ABI C e rejeições; confere a fronteira safe padrão, modo legado, métricas, inventários e hashes. **Resultado: Windows e Linux aprovados, com 19 bibliotecas e 668 hashes verificados.** Ambos executaram os compiladores extraídos e os exemplos, incluindo o cliente polling, perfil safe padrão/compatibilidade e a ABI C. Os pacotes foram regenerados após consolidar este relatório e conferidos novamente. Não houve aceite humano independente ou CI remota.

## Pendências preservadas

Closures/capturas com vidas e variantes Move; 24 horas reais; emissão integral por IR e otimizações mais amplas; ARM64/macOS; direitos de imagens/revisão de distribuição; aceite humano independente. Sem servidor HTTP, resolvedor DNS público, novas garantias de tempo real, certificação de produção ou isolamento para conteúdo hostil. Os novos contratos não ampliam retroativamente as garantias das APIs legadas.

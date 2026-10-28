# Validação — 3.3.0-alpha.11

Data: 26/10/2026, contexto do usuário. **Conclusão estimada: 85% (85/100 pontos)**
pela mesma régua de 35 critérios. A meta de 90–100% permanece aberta.
[Handoff](HANDOFF-3.3-ALPHA.11.md), [régua](PROGRESSO.md), [ABI C](FFI-C.md),
[HTTP](BIBLIOTECA-http.md), [processos/serviço C](BIBLIOTECA-process.md).

## Reconstrução

Base recebida limpa no commit `257e719`. Binários alpha.10 copiados antes das
alterações para `build/alpha10-baseline`, conferidos contra os hashes publicados
na entrega anterior. Relatórios alpha.10 e anteriores permanecem históricos.

Ambos os runtimes foram regenerados de seus fontes em árvores temporárias que
não copiaram bin/build/dist. O compilador reconstruído passou nas 25 suítes e
reproduziu exatamente o binário do workspace. GCC Windows MSYS2 15.2.0; Linux
GCC 13.3.0/WSL Ubuntu. Isso não garante bytes idênticos com outra toolchain.

| Compilador | SHA-256 final/reconstrução limpa |
| --- | --- |
| Windows x64 | `21d31502fab3e35451aeaf4f1f3e6d96cbb506647918f2d2ff1edbc2993597f4` |
| Linux x86_64 | `b37bb37cc6c709340d684337bc46a33d7a07c57985dc8d696ed351a833d4ae69` |

## Gates executados

| Conjunto | Resultado |
| --- | --- |
| Python nativo, reconstrução limpa Windows | 25 suítes, 225 testes relatados; 1 teste GDB ignorado nessa plataforma |
| Python nativo, reconstrução limpa Linux | 25 suítes, 225 testes aprovados, incluindo GDB |
| Node/editor/LSP/instalador, Windows Node 24 | 82 testes aprovados |
| Corpus nativo Windows | 130 verificações aprovadas |
| Corpus nativo Linux | 133 verificações aprovadas, incluindo 256 operações aritméticas |
| Módulos/instalação/remoção Linux | 26 verificações aprovadas |
| Harness PE32+ em Linux | 41 casos aprovados com base relocada e ABI Microsoft |
| Corpus Node recém-gerado, reproduzido Windows | 18 verificações 3.1 e 73 casos 3.2 aprovados |
| Mesmo corpus reproduzido Linux | 22 verificações 3.1 e 73 casos 3.2 aprovados |

Os conjuntos têm sobreposição e não representam uma soma de casos independentes.
Node não está instalado no WSL local: editor/LSP completos foram executados no
Windows; CI Linux mantém Node e o gate completo, ainda sem execução remota
registrada para esta entrega. Não atribuir a CI alpha.10 ao código alpha.11.

As quatro suítes novas cobrem 21 casos: ABI C com biblioteca compilada
independentemente (9), HTTP local/TLS não confiável (5), processos/pipes (4),
aplicações B/C (3). Há otimização/desativação e emissão cruzada, além de
execução nativa real em cada OS. Testes de rejeição não executam o código
rejeitado. HTTP preserva NUL/UTF-8, diferencia 404 e transporte, recusa redirects
implícitos, excedente e certificado autoassinado; não instala confiança no OS.

## Ensaio prolongado real, delimitado

`tools/soak-native.py --duration 120 --workers 4` passou em cada sistema, com
compiladores de hash acima: quatro serviços nativos persistentes de longa vida
por ensaio e clientes HTTP nativos independentes. Cada ciclo incrementa e lê o
estado, baixa bytes binários e confere conteúdo. Comandos inválidos e HTTP 404
são injetados periodicamente; reinício reabre o estado final de cada serviço.

| Sistema | Duração observada | Ciclos completos | Maior RSS por serviço | Handles/descritores por serviço |
| --- | ---: | ---: | ---: | --- |
| Windows | 120.558 s | 7556 | 5718016 bytes | 91→91, 91→91, 91→91, 91→91 |
| Linux/WSL | 120.504 s | 8548 | 1347584 bytes | 4→4, 4→4, 4→4, 4→4 |

Dados: [Windows](../benchmarks/resultados/soak-alpha11-windows.json),
[Linux](../benchmarks/resultados/soak-alpha11-linux.json). O campo
`qualifies24Hours` é false em ambos. O padrão do harness é 86400 segundos, mas
**nenhuma execução real de 24 horas foi concluída nesta sessão**. Concorrência
significa processos isolados; não se declarou alocador multithread seguro.

As suítes HTTP/aplicações B/C/catálogo foram repetidas nos dois sistemas após
a introdução final de Client reutilizável, incluindo 128 requisições no mesmo
processo e comparação de handles/descritores. Isso amplia a cobertura do
ensaio entre processos sem confundi-lo com 24 horas.

## Correções verificadas durante a implementação

- Callbacks reais de libcurl revelaram que C usa R15 temporariamente: a ponte
  agora salva/restaura R15 e recupera o estado separado do runtime; o oráculo C
  força esse caso e verifica o registrador ao retornar.
- A repetição de sessões WinHTTP mostrou retenção também em um cliente C
  independente. A API Client reutiliza uma sessão para serviços, com teste de
  handles após aquecimento. Curl limpa callbacks/userdata entre requisições.
- EOF do pipe Windows pode anteceder o término do filho. O supervisor aguarda
  o status do processo sem confundir pipe fechado com código de saída válido.
- Linux mantém o PID do líder com WNOWAIT até sinalizar o grupo e só então faz
  reap, evitando sinalizar um PID já reciclado. Timeout encerra grupo/job.
- Segmentos ELF dinâmicos têm tamanhos de arquivo reais, GOT RELRO e estado
  de callback em página separada sem execução; há teste estrutural do formato.
- Classes com drop rejeitam consumo parcial de campos fora do destrutor. A
  destruição é exercitada com contadores C independentes em retornos, ramos,
  loops, composição, movimentos e free.

Não houve atualização de runtime assembly, protocolo criptográfico novo ou
desativação de certificados. Dependências C/WinHTTP/libcurl são explícitas.
Problemas de permissão de diretórios temporários no ambiente restrito foram
repetidos com acesso local apropriado; não foram contados como aprovação.

## Limites que continuam abertos

Capturas/closures com vidas, variantes Move, safe obrigatório e text externo,
rede cancelável/assíncrona, 24 horas, IR/backend integral, otimizações gerais,
ARM64/macOS, procedência completa/direitos de imagens e aceite por terceiro.
C FFI é escalar e síncrona na thread principal; structs C por valor, unwind e
callbacks de outras threads são rejeitados ou estão fora do contrato. O serviço
C não demonstra durabilidade por perda de energia nem recuperação automática
de temporário interrompido durante commit. A estimativa não certifica produção.



## Medições finais

Sete amostras com aquecimento, variantes intercaladas e saídas conferidas por
oráculos independentes. Baseline alpha.10 preservada. Os dados incluem início
de processo e não demonstram desempenho universal ou prontidão para produção.

| Carga | Windows alpha.10 → alpha.11 (ms) | Linux alpha.10 → alpha.11 (ms) |
| --- | ---: | ---: |
| Hash passo 1 | 22.320 → 22.586 | 11.435 → 11.453 |
| Hash passo 65536 | 25.905 → 23.700 | 10.530 → 10.747 |
| Blocos grandes | 20.004 → 20.052 | 7.247 → 6.868 |
| Chamadas escalares | 34.303 → 35.355 | 18.159 → 18.826 |
| fib(35) | 103.940 → 104.311 | 111.795 → 111.390 |

A razão máxima entre passos adversos e passo 1 foi windows: 1.049×, linux: 0.938×, abaixo do gate de 5×. São cargas específicas, não prova de proteção contra hash adverso escolhido.

[Regressão Windows](../benchmarks/resultados/optimization-alpha11-windows.json),
[Linux](../benchmarks/resultados/optimization-alpha11-linux.json).
[Recursos atuais Windows](../benchmarks/resultados/evolucao-alpha11-windows.md),
[Linux](../benchmarks/resultados/evolucao-alpha11-linux.md) incluem compilação,
tamanho, pico de RAM, valores/CSV e dez variantes de recursos atuais. As novas
cargas verificam dois milhões de chamadas C e qsort de dez mil inteiros com
callback AssisScript. Bibliotecas não usadas nas cargas não são comparativos
históricos de rede. O ensaio de serviços é o relatório separado acima.

Hashes de compiladores e todos os fontes src/stdlib nos relatórios foram
conferidos contra a árvore final. Relatórios alpha.10 não foram reescritos.

## Distribuição

Arquivos desta entrega: `dist/AssisScript-3.3.0-alpha.11-windows-linux.zip` e
`dist/assisscript-3.3.0-alpha.11.vsix`, com 18 módulos, instaladores, fontes,
contratos, exemplos B/C, migração, licenças e medições. O manifesto do instalador
Windows contém 203 caminhos obrigatórios, além dos módulos opcionais.
`SHA256SUMS` identifica os arquivos da distribuição. Dependências do sistema
são declaradas no catálogo e nos contratos; libcurl não foi redistribuída.

`tools/verify-release.py` verifica arquivos/hashes, métricas, rejeições,
instalação, ferramentas, exemplos anteriores, ABI C e inicialização B/C sobre
os arquivos extraídos. A verificação final dessa distribuição é o último gate.


**Resultado da verificação dos pacotes:** Windows e Linux aprovados, com 18
bibliotecas e 645 hashes. Ambos executaram os compiladores extraídos e os
exemplos, incluindo a chamada ABI C, rejeições, ferramentas e entradas B/C.
O lockfile do exemplo offline foi regenerado para alpha.11 e produziu os mesmos
bytes nos dois sistemas (SHA-256
`17b40da1c4f632732c15f26e4c7331fb280fb6e9626750e9738dfbc2b4fa3179`).
Os pacotes foram regenerados após consolidar este relatório; não foi feito
push/CI remoto nem aceite independente nesta sessão.

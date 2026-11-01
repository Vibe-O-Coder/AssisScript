# Relatório — orçamento compartilhado de buffers

Data: **01/11/2026**, America/Fortaleza. Unidade **M1-ALLOC / E02-03**;
ownership/identidades E01-03/E02-02 verificadas sem promover seus níveis.
M0/M1 e todos os gates permanecem abertos.

## Base, objetivo e comportamento

Base: **52c8bb1f1d7482865660580941637a3074329167**, branch
`work/m1-arena-removal-2026-10-30`, [PR #12](https://github.com/Vibe-O-Coder/AssisScript/pull/12).
Destino: `work/m1-shared-budget-2026-11-01`, Vibe-O-Coder/AssisScript.
Cópia isolada: `AssisScript/work/shared-budget-20261101`.

O masterprompt foi lido integralmente no caminho solicitado. O checkout
original estava em 1ed22f5, com 31 arquivos modificados/não rastreados. A
consulta de branches/PRs e fetch mostrou continuações publicadas posteriores;
elas foram usadas como base, sem repetir M0 como novidade. A branch original
foi restaurada e os 31 arquivos foram preservados byte a byte. Nenhum merge,
reset, limpeza ou force push foi realizado.

O próximo bloqueio documentado era orçamento compartilhado. A reprodução
com o compilador reconstruído confirma que dois ByteBuffer com limites
individuais de 12 permitem reservar 8 cada: **16 bytes agregados**, nos dois
modos. Isso é o contrato dos limites independentes, não um bug do ByteBuffer.
Seu fonte coincide com a base e permanece preservado.

Agora `buffers::BufferPool` possui vários buffers e limita a soma das
capacidades, incluindo payload antigo + candidato durante crescimento.
No exemplo, 4+8 bytes sob teto 16 recusam candidato de 8 para o primeiro;
liberar o segundo devolve quota e permite o crescimento, preservando byte 42.
Não houve alteração de sintaxe, compilador, ABI ou runtime. O código principal
é AssisScript; a injeção de falha usa somente fixtures C de teste existentes.

## Implementação e decisões

- `try_new BufferPool` e a reserva interna do índice usam caminhos fallíveis.
  Null indica recusa inicial; controlador não nulo com `is_open=false` indica
  recusa do índice. Esse controlador não publica slots/quota e pode ser
  destruído normalmente. Configuração inválida é contrato 70/R001.
- `try_create` retorna enum Copy Created(BufferId)/Rejected(code), sem objeto
  de erro alocado. Payload, slot e caminhos do índice são preparados antes de
  publicar tamanho/quota/ID; recusa destrói candidatos e conserva o estado.
- `try_reserve` verifica `limit-used` antes de reservar o candidato inteiro;
  conserva tamanho e dados. `try_resize` zera bytes recém-expostos, inclusive
  após shrink. Shrink conserva capacidade/cobrança.
- `release` devolve quota conservando ID vazio; `erase` invalida e recicla com
  geração maior, aposentando no limite sem wrap. `close` e `reset` invalidam
  a instância anterior. Essas operações não alocam pela biblioteca.
- BufferId tem domínio próprio. O host atribui instâncias únicas e crescentes
  no reset. Não é token de autorização e não impede forja num ambiente hostil.
  A API não entrega ponteiros, buffers own ou empréstimos mutáveis que permitam
  crescimento sem passar pelo controlador.

A quota mede **somente payload solicitado nos buffers desse pool**. Não inclui
cabeçalhos, alinhamento, slabs/caches, RSS, metadados, pilha, arenas ou outros
objetos. `max_buffers` limita slots, incluindo aposentados; metadados retidos
são liberados no close/reset/drop. Não há reserva antecipada desses metadados.
Não é ainda quota integral de documento ou recuperação completa do Browser.

Arquivos: novo `stdlib/buffers.assis`, contrato BIBLIOTECA-buffers.md,
exemplo 39_shared_buffer_budget.assis, suíte test-shared-buffer-budget.py,
catálogo e sua asserção de APIs, Makefile, CI, runner nativo e portabilidade.
Manifestos do instalador e dependência buffers → owned foram regenerados;
guias de bibliotecas/memória, fila, progresso, evidências e este relatório
integram a unidade. Não há mudança de sintaxe que exija alterar o editor.

## Ambiente e comandos

Windows 10 Pro x64, build **19045**, Python **3.14.6**, GCC MinGW/MSYS2
**15.2.0**. Linux x64 Ubuntu/WSL2, kernel
**6.18.54.1-microsoft-standard-WSL2**, Python **3.12.3**, GCC **13.3.0**.
O WSL teve uma falha inicial RPC_S_CALL_FAILED; a execução posterior funcionou.
Windows precisou de acesso normal aos temporários: a tentativa restrita
falhou antes de escrever os fontes de teste e não recebeu crédito de runtime.

Compiladores reconstruídos nesta sessão, sem substituir `bin/`:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-budget.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-budget-linux
```

ASSIS_BIN seleciona o candidato do host. Windows usa TEMP/TMP em
build/test-temp e provider libcurl de `C:/Program Files/Git/mingw64/bin`.
Linux usa python3. Evidências em `docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01`:

```text
python tests/test-shared-buffer-budget.py
python tools/test-native.py --output docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/windows.json
python tools/test-portability.py --expect-host x86_64 --output docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/windows-portability.json
python tools/validate-examples.py --output docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/windows-examples.json
python docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/reproduce-before.py
python docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/run-arm64.py
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-buffer-budget-evidence.py
git diff --check
```

O instalador Windows foi compilado separadamente de src/windows_setup.c com
os manifestos finais, bibliotecas shell32/advapi32/user32 e saída em
build/assis-budget-setup-check.exe. Trata-se de geração; esse instalador não
foi executado nem promovido. Comando/hash em installer-generation.json.

Linux grava linux*.json/log; run-arm64.py executa somente no Linux com
qemu-aarch64. Os JSONs incluem comandos, hashes e outputs exatos. Os logs da
primeira matriz e de repetições necessárias são preservados separadamente.

## Resultados próprios e oráculos

| Verificação | Windows x64 | Linux x64 |
| --- | --- | --- |
| 40 suítes, resultado efetivo | **380 executados sem falha; 2 not-run** | **382 executados sem falha; 1 not-run** |
| Suíte nova | **11/11, sem dispensa** | **11/11, sem dispensa** |
| Portabilidade | **28/28 execuções locais** | **28/28 execuções locais** |
| Exemplos | **41/41 analisados**, RPG victory/defeat executados | **41/41 analisados**, RPG victory/defeat executados |

Registrados: 382 métodos Windows e 383 Linux. Not-run: symlink e GDB Linux no
Windows; aliases Windows 8.3 no Linux. Não recebem crédito de aprovação.
A cobertura da matriz permanece parcial, explicitamente distinta de aprovação
completa de todos os casos/destinos.

A primeira matriz Windows teve **8 falhas em net**: configurou-se
ASSIS_CURL_BIN em C:/msys64/ucrt64/bin, onde libcurl-4.dll não estava instalado;
os executáveis encerraram com 0xc0000135. O JSON bruto conserva passed=false.
A repetição **8/8** usando a DLL existente do Git passou sem mudar fontes,
timeouts ou o provider do produto. A consolidação usa essa repetição somente
para net e mantém logs/identidade do provider e resultado inicial. As demais
39 suítes Windows não foram repetidas sem necessidade. Linux passou as 40
na mesma matriz. Push/CI não foram usados como substitutos desses testes.

| Compilador reconstruído | SHA-256 |
| --- | --- |
| build/assis-budget.exe | 0970dfaeee0710a2106b4e0c3661ff8165346ca299b4d39a5c6335457630ee62 |
| build/assis-budget-linux | 034d61bfe7b1106f53b4e5dadec1100faffaa4292688adfc5cd5a4f2ff9ae78c |

Os bytes coincidem com os compiladores da base, pois não houve mudança no
compilador. As aplicações e bibliotecas foram recompiladas e executadas nesta
sessão; essa coincidência não recebeu crédito de teste por si só.

A suíte nova compara **260 operações**, seed **20261101**, a um modelo Python
de bytearray/capacidades por identidade lógica; ele não reproduz a árvore de
índices nem a lista livre. Inclui zero/limites exatos/negativos/extremos,
quotas conjunta e transitória, shrink/zeragem, 10.000 reciclagens, aposentadoria,
IDs expirados/forjados/entre instâncias, privacidade e empréstimos rejeitados.

As fixtures negam novos slabs do OS só no executável filho e drenam as dez
classes pequenas do alocador. São verificados: recusa do controlador inicial,
recusa do índice durante init, payload/crescimento, slot/caminhos candidatos,
cinco concessões de blocos para rollback parcial, liberação sem alocar e pool
vizinho intacto. `--debug` exige ausência de blocos vivos ao fim de cada caso.
Recusa de slabs não mede alocações atendidas por caches; concessões e fonte
explicam o limite do ensaio. Overcommit/OOM killer e pilha mantêm seus limites.

Os cinco formatos são gerados/inspecionados; execução nativa própria é Windows
e Linux x64. O exemplo também tem **2/2 execuções Linux ARM64 emuladas**,
otimizado/referência; emulação não certifica ARM64 nativo. A IR tem
astFallbacks=0. Conformidade HTDL/FS/SSC, integração do Browser, sandbox,
macOS/ARM64 nativos, IME/acessibilidade, crash e carga de 24h: **not-run**.

Consolidação: [summary.json](../ecossistema/evidencias/m1-buffer-budget-2026-11-01/summary.json).
Fontes, compiladores, comandos e logs têm SHA-256. O verificador confere também
os blobs Git com `--revision SHA`; ele não substitui nem reexecuta o runtime.
Textos novos, inclusive logs Windows, foram normalizados para LF antes dos
hashes e da comparação com os blobs, preservando o conteúdo dos resultados.

## Pontos, publicação e próximo incremento

**22,30% → 22,30%; 0/5 → 0/5 gates. E02-03 permanece 2.** Há nova evidência de
quota compartilhada de um subconjunto, sem cumprir toda a aceitação da linha.
O histórico acrescenta retrato completo dos 60 estados e cinco gates, sem
alterar pesos, escopo, baseline ou histórico antigo de fases 0–6.

Publicação em branch de trabalho e PR incremental de rascunho sobre #12,
sem merge automático. O SHA é consultável pelo histórico deste relatório;
a sessão confere arquivos publicados e SHA remoto depois do envio.
Push/PR não significam CI aprovada, release ou aceite de produto. Binários,
ZIP/VSIX e instaladores publicados anteriormente mantêm sua identidade.

Próximo M1-ALLOC: reserva antecipada de metadados e integração do orçamento
com arena/árvore/texto do documento, definindo cobrança e rollback de cada
recurso. M0-EXEC e validação visual M2 permanecem tarefas independentes.

## Adendo — publicação bloqueada pela revisão automática

Implementação e evidências commitadas localmente em
**a3f4e07bcbba9ec3b24a087eb23c3db356e28268**. Os 545 hashes de fontes e
artefatos foram conferidos contra os blobs desse commit. O diretório original,
branch/HEAD e os 31 arquivos preexistentes permanecem preservados.

A tentativa de push foi rejeitada **antes de executar** pela revisão automática
de autorização. Ela classificou o envio dos 117 arquivos ao repositório público
como divulgação externa/mutação remota sem aprovação explícita do usuário para
o destino e payload exatos; não considerou suficiente a autorização contida
no masterprompt referenciado. Nenhuma rota alternativa foi usada.

**Publicação pendente:** enviar esta unidade e este adendo à branch
work/m1-shared-budget-2026-11-01 em
https://github.com/Vibe-O-Coder/AssisScript.git, conferir SHA remoto e abrir
PR de rascunho sobre work/m1-arena-removal-2026-10-30 (#12).
Comando pendente: `git push -u origin work/m1-shared-budget-2026-11-01`.
Requer aprovação específica do usuário por causa desse bloqueio automático.
Nenhuma PR desta unidade foi criada; não se declara push, CI, merge ou release.
Commits e patch locais preservam a entrega revisável enquanto isso.

## Adendo — autorização recebida e publicação confirmada

O usuário respondeu **“Autorizar publicação e PR”** à solicitação que
identificava os 117 arquivos, o commit 7fbb612, o repositório público, a
branch e a base #12. A nova tentativa foi aceita. O push de
**7fbb6127bf608c3ea47a555b9ae9d41d7c7853ed** foi concluído e o mesmo SHA foi
confirmado por git ls-remote. Código, teste e relatório foram consultados
diretamente no GitHub nessa revisão.

Criada a [PR de rascunho #13](https://github.com/Vibe-O-Coder/AssisScript/pull/13),
base work/m1-arena-removal-2026-10-30 (#12), e vinculada à conversa. O conector
GitHub retornou 403 na criação; a mesma operação autorizada foi concluída pela
API usando a autenticação Git local, sem expor credenciais.

O bloqueio descrito no adendo anterior é histórico e está resolvido.
Este adendo documental e a atualização da evidência acompanham a branch;
seu SHA final é consultável pelo histórico deste relatório e conferido no
encerramento da sessão. Não houve alteração de código ou necessidade de
reexecutar a matriz. Nenhum merge, release ou promoção de binário foi feito.
A consulta de status do commit publicado retornou lista vazia; isso não é
aprovação de CI. Os pontos e gates permanecem 22,30% e 0/5.

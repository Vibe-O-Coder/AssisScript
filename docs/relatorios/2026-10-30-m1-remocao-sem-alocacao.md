# Relatório — remoção de recursos sem alocar resultado

Data: **30/10/2026**, America/Fortaleza. Unidade **M1-ALLOC / E02-03**;
obrigações de ownership/identidades E01-03 e E02-01/E02-02 verificadas sem
promover seus níveis. M0/M1 e todos os gates continuam abertos.

## Base, problema e resultado

Base real desta unidade: **17ac155b8a7e37f413696ab562063e3d71e61e51**, branch
work/m1-fallible-slots-2026-10-29, [PR #11](https://github.com/Vibe-O-Coder/AssisScript/pull/11).
Destino: **work/m1-arena-removal-2026-10-30**, Vibe-O-Coder/AssisScript.
Cópia isolada: AssisScript/worktrees/ecosystem-20261030.

A pasta inicial estava na revisão documental 1ed22f5, com 31 arquivos
preexistentes modificados/não rastreados. A consulta real de branches/PRs e
git ls-remote revelou as continuações publicadas posteriores. Não se repetiram
as implementações de M0, arena, janela e alocação como trabalho novo. HEAD,
status e SHA-256 dos 31 arquivos originais foram conferidos antes/depois e
preservados. Não houve reset, limpeza, merge automático ou force push.

O bloqueio escolhido era a remoção de recursos durante recuperação de memória.
Arena.remove alocava um enum Move para devolver Missing/Removed. Com slabs
recusados pelo OS e a classe pequena esgotada, a remoção de um handle válido
encerrava o processo com **70/R001, memória insuficiente**, nos dois modos em
Windows e Linux. A reprodução usa o fonte da arena obtido por git show da
base, com o compilador reconstruído nesta sessão, não um binário antigo.

Agora há transferência e descarte sem alocação pela biblioteca. A API antiga
remove mantém seu contrato e seu resultado own fatal em OOM. Nenhuma sintaxe,
regra de ownership, ABI, backend ou runtime de alocação foi alterado.

## Implementação e decisões

- **Arena.take(handle): own T** exige contains verdadeiro, transfere o recurso
  e atualiza ocupação, geração, lista livre e tamanho sem objeto intermediário.
  Identidade inválida é erro de contrato R001/status 70. Um null armazenado
  continua sendo um recurso presente; não serve como sentinela de ausência.
- **Arena.erase(handle): bool** retorna false sem modificar a arena para uma
  identidade inválida; em sucesso remove e destrói o recurso uma vez. Usa take
  depois de validar. O recurso é invalidado antes do drop do usuário.
- Geração esgotada continua aposentada sem wrap; categoria, instância, slot,
  empréstimos e encerramento conservam os contratos existentes. take transfere
  um valor que pode sobreviver ao fechamento da arena.
- **OwnedArray.swap_remove** primeiro retira o último item e depois substitui
  o destino ainda existente. Isso evita liberar e reconstruir o caminho do
  destino por array_put. Conserva ordem por troca, tamanho, posições, retorno
  own e custo O(log capacidade). Não reserva novos nós de índice.
- remove delega a transferência para take, mantendo a validação e os resultados
  públicos. Seu resultado continua alocado; não foi anunciado como recuperável.

A lógica está em AssisScript. A injeção de falha reutiliza apenas fixtures C de
teste existentes; não acrescenta provider, hook de produção ou sandbox.
Não se mede quota total por eliminar essas alocações. Drops do usuário podem
alocar/falhar/fazer I/O; a garantia é da operação da biblioteca, não de código
arbitrário executado por drop, argumentos, chamador ou runtime inicial.

Arquivos de implementação: stdlib/arena.assis e stdlib/owned.assis.
Teste: tests/test-arena-removal.py. Exemplo: 38_allocation_free_removal.assis.
Contratos: BIBLIOTECA-arena.md, BIBLIOTECA-proprios.md, INSERCAO-FALLIVEL.md.
Catálogo, Makefile, CI, runner nativo, portabilidade, manifesto e fila M1
sincronizados. Não há mudança de sintaxe que exija alterar gramática/editor.
Régua JSON/Markdown, evidência e este relatório completam a unidade.

## Ambiente, comandos e candidatos próprios

Windows 10 x64 **19045**, PowerShell, Python **3.14.6**, GCC MinGW/MSYS2
**15.2.0**. Linux x64 Ubuntu/WSL2, kernel
**6.18.54.1-microsoft-standard-WSL2**, Python **3.12.3**, GCC **13.3.0**.
ARM64 complementar usa qemu-aarch64 no Linux x64; é emulação.

Os dois compiladores foram reconstruídos dos fontes desta base:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-base.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-linux
```

Não houve mudança no compilador; os bytes reconstruídos coincidem com os
candidatos da unidade anterior. Essa coincidência não foi usada como substituto
dos novos testes: os fontes std/arena e std/owned são carregados ao compilar
cada aplicação e foram retestados nesta revisão.

| Candidato reconstruído | SHA-256 |
| --- | --- |
| build/assis-base.exe | 0970dfaeee0710a2106b4e0c3661ff8165346ca299b4d39a5c6335457630ee62 |
| build/assis-linux | 034d61bfe7b1106f53b4e5dadec1100faffaa4292688adfc5cd5a4f2ff9ae78c |

ASSIS_BIN aponta para o candidato do host; os comandos abaixo foram executados
na cópia isolada. Linux usa python3. Windows usa temporário em build/tmp com
acesso normal; as primeiras tentativas com permissões restritas impediram
criação/leitura dos temporários antes da validação semântica.

```text
python tests/test-arena-removal.py
python tools/test-native.py --output docs/ecossistema/evidencias/m1-removal-2026-10-30/windows.json
python tools/test-portability.py --expect-host x86_64 --output docs/ecossistema/evidencias/m1-removal-2026-10-30/windows-portability.json
python tools/validate-examples.py --output docs/ecossistema/evidencias/m1-removal-2026-10-30/windows-examples.json
python docs/ecossistema/evidencias/m1-removal-2026-10-30/reproduce-before.py
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-removal-evidence.py
git diff --check
```

Linux grava linux*.json/log na mesma pasta. O roteiro reproduce-before.py
compila a fixture do próprio host e substitui os caminhos do template
before.assis; seus resultados estão em windows-before.json e linux-before.json.
O ensaio ARM64 compila o novo exemplo com --target linux-arm64 --debug,
com/sem --no-opt, e o executa por qemu-aarch64. Comandos/modos, outputs e
identidades estão na evidência; os binários de teste não integram a publicação.

## Resultados e oráculos

| Verificação final | Windows x64 | Linux x64 |
| --- | --- | --- |
| Matriz de 39 suítes | **369 executados, zero falhas; 2 not-run** | **371 executados, zero falhas; 1 not-run** |
| Suíte nova | **10/10, sem dispensa** | **10/10, sem dispensa** |
| Portabilidade | **26/26 execuções locais** | **26/26 execuções locais** |
| Exemplos | **40/40 analisados**, RPG victory/defeat executados | **40/40 analisados**, RPG victory/defeat executados |

Registrados: 371 métodos Windows e 372 Linux. Not-run: symlink e GDB Linux no
Windows; aliases Windows 8.3 no Linux. O runner bruto passed representa retorno
zero das suítes e admite dispensas; summary.json separa executed/not_run e
marca a cobertura da matriz como parcial. Nenhuma dispensa recebe crédito de
aprovação. Os casos novos, ownership, arena e coleções afetados não têm dispensa.

A suíte nova usa um **modelo lógico Python independente, 220 operações**, seed
**20261030**, para inserção/transferência/descarte/reload e verificação dos
recursos vivos/identidades expiradas. Não reproduz o índice binário nem a lista
livre da implementação. Confere também 10.000 reciclagens, aposentadoria com
limite reduzido, domínios forjados, remoção repetida, null presente, recurso
transferido após close, empréstimos rejeitados e drops na ordem esperada.

A recusa de novos slabs é habilitada somente no executável filho. O teste
esgota duas classes pequenas, remove/transfere recursos, reutiliza slot e
verifica a arena vizinha. Oito cenários adicionais exercitam swap_remove em
fronteiras de árvore, inclusive o último índice. Todos executam otimizado e
referência, com debug exigindo ausência de diagnóstico de blocos vivos.
A ausência de alocação dos novos caminhos também é verificável no fonte:
take move o valor, erase só delega e faz drop; swap_remove usa array_take e
array_replace, sem new/try_new/array_put. Recusa do OS isoladamente não conta
alocações satisfeitas pelas listas livres do runtime.

Os cinco formatos são gerados/inspecionados; a execução nativa desta unidade
é Windows/Linux x64. O novo exemplo teve **2/2 execuções ARM64 emuladas**,
com/sem otimização. A IR do exemplo informa astFallbacks=0. Geração cruzada e
emulação não certificam execução nativa macOS/ARM64 nem OOM nessas plataformas.

Evidência consolidada: [summary.json](../ecossistema/evidencias/m1-removal-2026-10-30/summary.json).
Fontes, testes, candidatos, comandos, logs e artefatos têm SHA-256. Os textos
novos foram normalizados para UTF-8/LF antes de calcular hashes, também
conferidos contra os blobs do commit publicado com
tools/verify-removal-evidence.py --revision SHA. Esse verificador confere
identidades/contagens; não executa nem certifica novamente o runtime.

## Progresso, limites e publicação

**22,30% → 22,30%; 0/5 → 0/5 gates.** E02-03 permanece no nível **2**.
Há nova evidência desse subconjunto, sem quota compartilhada, reserva geral,
construção recuperável completa dos controladores ou recuperação de documento.
Foi acrescentado retrato completo dos 60 critérios e cinco gates com níveis
preservados. Pesos, escopo, baseline e histórico das fases antigas não mudaram.

Não executados: macOS/ARM64 nativos, OOM ARM64, visualização gráfica/IME/
acessibilidade, HTDL/FS/SSC, sandbox de página, recuperação de serviços/crash,
quota de documento e carga integrada de 24h. Não se promove binário em bin/,
pacote, instalador, VSIX, release, merge ou aceite de produto. safe continua
sem equivaler a isolamento de autoridade.

Publicação como branch de trabalho e PR incremental de rascunho sobre #11,
sem merge automático. O SHA desta unidade é consultável pelo histórico deste
relatório; a sessão verifica os arquivos e o SHA remoto depois do envio.
Push/PR não significam CI aprovada ou release. A confirmação e a URL final
são entregues no encerramento da sessão, sem hash autorreferente no relatório.

Próximo incremento recomendado: orçamento de memória compartilhado por
documento, com controladores/reserva antecipada, devolução de quota e rollback
sob OOM em cada fronteira. M0-EXEC e experiência visual M2 mantêm suas tarefas
e aceites separados; a remoção desta unidade não os apresenta como concluídos.

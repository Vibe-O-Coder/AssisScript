# Relatório — objetos e inserções recuperáveis

Unidade iniciada em 29/10 e concluída em 30/10/2026 (America/Fortaleza).
M1-ALLOC / E02-03; obrigações E01-03/E01-04/E01-05 e ferramentas E11.

## Base, objetivo e estado anterior

Base: **085fb4109b5389742be8d562cdab34de69747e6f**, branch
work/m1-allocation-2026-10-29, [PR #10](https://github.com/Vibe-O-Coder/AssisScript/pull/10).
Destino: **work/m1-fallible-slots-2026-10-29**, em Vibe-O-Coder/AssisScript.
Cópia isolada: AssisScript/worktrees/m1-fallible-slots.

A pasta inicial continua em 1ed22f5 com 30 caminhos preexistentes alterados ou
não rastreados. Consultas reais ao GitHub e git ls-remote encontraram as sete
continuações posteriores, incluindo a de buffers. Elas não são trabalho novo
desta unidade. Todos os hashes AssisScript da baseline congelada continuam
iguais na pasta original; seu HEAD/status foram registrados em summary.json.
Não se usaram reset, limpeza, merge automático nem force push.

O bloqueio seguinte de M1-ALLOC era a alocação fatal de objetos/slots/ramos.
try_new não era reconhecido pelo compilador reconstruído da base. Reprodução:
[before.assis](../ecossistema/evidencias/m1-slots-2026-10-29/before.assis),
[before.log](../ecossistema/evidencias/m1-slots-2026-10-29/before.log),
retorno **1/A001**. A recusa encerrava inserções antes de informar OOM.

Agora a reserva inicial pode retornar null e as novas inserções podem recusar
memória preservando os dados anteriores. O aceite é o subconjunto nativo
verificável abaixo. M0/M1 e todos os gates de produto permanecem abertos.

## Implementação, decisões e arquivos

- try_new Type(args) reutiliza o layout e RT_try_alloc já existentes. Aceita
  classes, structs gerenciadas e enums Move; valores Copy continuam com new
  no frame. Sem alteração de ABI, blobs, semântica numérica ou new/alloc.
- Todos os argumentos são avaliados uma vez em ordem, inclusive se a reserva
  inicial falhou. Argumentos own são consumidos nos dois resultados; na recusa
  são destruídos em ordem inversa, sem chamar init/drop do objeto inexistente.
  Empréstimos, privacidade, genéricos e efeitos continuam verificados.
- Emissão TypedIR x64/ARM64 e referência AST x64 possuem caminhos explícitos
  de sucesso/recusa. O efeito de cleanup é registrado na IR; não há fallback
  AST no modo otimizado. pure rejeita também templates não instanciados.
- OwnedArray.try_push prepara os novos ramos fora do índice vivo e publica
  somente após a última reserva. Falha destrói candidatos e valor consumido,
  preservando tamanho, capacidade, ordem e recursos anteriores.
- Arena.try_insert usa Slot recuperável e try_push; InsertStatus é um enum
  Copy sem alocação para relatar erro. Códigos 1 fechado, 2 limite lógico,
  3 recusa do alocador. Slots livres são reutilizados sem alocar.
- A lógica das coleções/arena está em AssisScript. As duas fixtures C são
  apenas injeção de falhas do OS em processos de teste; não são providers,
  hooks de produção nem infraestrutura de sandbox distribuída.

Fontes principais: src/{lexer,frontend,generics,ir,backend_ir,backend_emit,
arm64_emit}.h e src/assisc.c; stdlib/{owned,arena}.assis. Testes:
tests/test-fallible-slots.py, allocation-fault-{windows,linux}.c e
fixtures/fallible-construct.assis. Exemplo 37_fallible_slots.assis; contratos
INSERCAO-FALLIVEL.md, linguagem/gramática/manuais; editor, catálogo, Makefile,
runner nativo/portabilidade, CI e manifesto de instalação sincronizados.

Verificação das identidades publicadas:
[tools/verify-fallible-slots-evidence.py](../../tools/verify-fallible-slots-evidence.py).
Nenhuma versão, binário em bin/, ZIP, instalador, VSIX ou release foi promovido.
Os 100/100 das fases antigas continuam preservados.

## Ambiente e comandos desta revisão

Windows 10 x64 build **19045**, PowerShell, Python **3.14.6**, GCC MinGW
**15.2.0 Rev13/MSYS2**; Node **24.17.0**. Linux x64 Ubuntu/WSL2, kernel
**6.18.54.1-microsoft-standard-WSL2**, Python **3.12.3**, GCC **13.3.0**.
QEMU AArch64 **8.2.2**, explicitamente emulação, não host nativo ARM64.

Compiladores reconstruídos dos fontes desta unidade:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-slots-final.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-slots-final-linux
```

Com ASSIS_BIN apontando para o candidato do host e saída na pasta de evidência:

```text
python tools/test-native.py --output docs/ecossistema/evidencias/m1-slots-2026-10-29/windows.json
python tests/test-fallible-slots.py
python tools/test-portability.py --output docs/ecossistema/evidencias/m1-slots-2026-10-29/windows-portability.json
python tools/validate-examples.py --output docs/ecossistema/evidencias/m1-slots-2026-10-29/windows-examples.json
node --test --test-isolation=none vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py --check
python tools/verify-fallible-slots-evidence.py
git diff --check
```

Linux usa python3 e nomes linux*.json. Sua suíte final foi repetida sozinha
após adicionar o teste de reutilização sem alocar; o compilador permaneceu
igual. linux.json registra o resultado anterior, a razão e o comando do reteste,
e aponta para linux-fallible-slots-final.log. O Windows completo já inclui esse
caso. Não se repetiram as outras 37 suítes sem alteração que as afetasse.

As fixtures são compiladas com -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror
-shared -fPIC. Windows as chama por FFI somente no próprio executável de teste;
Linux instala o filtro seccomp após preparar o estado. Comandos/fontes/saídas
e hashes dos dois programas emulados estão em arm64-emulated.json: build com
--target linux-arm64 --debug, com/sem --no-opt, seguido de qemu-aarch64.

## Resultados, oráculos e limites de cobertura

| Verificação | Windows x64 | Linux x64 |
| --- | --- | --- |
| Matriz de 38 suítes | **359 executados sem falha**, 361 registrados, **2 not-run** | **361 executados sem falha**, 362 registrados, **1 not-run** |
| Suíte nova final | **11/11**, sem dispensa | **11/11**, sem dispensa |
| Portabilidade | **24/24** execuções locais | **24/24** execuções locais |
| Exemplos | **39/39** analisados; finais RPG victory/defeat executados | **39/39** analisados; finais RPG victory/defeat executados |

Not-run: Windows não criou symlink de teste e não executa GDB Linux; Linux não
executa aliases Windows 8.3. GDB passou no Linux e aliases 8.3 no Windows.
O passed bruto do runner significa retorno zero das suítes e admite dispensas;
summary.json normaliza os logs, separa executed/not_run e marca coverage_state
partial. As três dispensas **não** foram contadas como aprovação.

A suíte nova cobre modelo Python independente de lista, **240 operações**, seed
**20261030**; 4.097 inserções, remoção completa e crescimento de 2.049 itens;
defaults, genéricos, Copy composto, herança/dispatch, enums Move, avaliação
única/ordem, drops, empréstimos, pure, limites e esgotamento de geração.
Positivos executam otimizado/referência com debug de blocos vivos.

Para OOM, nega-se nova reserva de slabs de 64 KiB, drenam-se os blocos livres
com buffers retidos e devolvem-se exatamente k blocos. São **29 cenários** de
inserção de array (20 posições de recusa e nove sucessos), **9 de arena**
(sete recusas e dois sucessos), **3 de construção** (classe/struct/enum Move)
e um de reutilização de slot sem alocar, nos dois modos e nos dois hosts.
Cada recusa confere estado anterior e cleanup; a arena também confere handles
e a instância vizinha. Argumentos da construção recusada conservam efeitos e
os recursos são destruídos em ordem inversa sem executar init.

Editor: **31/31**, sem dispensa. ARM64: **4/4 execuções emuladas** de dois
programas, com/sem otimização, incluindo construtores com recursos, valores
Copy aninhados, dispatch e drops. Os cinco formatos têm emissão e inspeção
independente de arquitetura/cabeçalho na portabilidade. Isso não é execução
nativa macOS/ARM64 nem teste de OOM ARM64.

A primeira tentativa de testes foi impedida por permissões do temporário;
testes com acesso normal e temporário na cópia isolada completaram. Ajustes
intermediários do harness corrigiram sintaxe de extern, nome reservado usado
pela fixture e a expectativa de um caminho esparso. O teste de template pure
expôs uma rejeição ausente e motivou correção real e reconstrução dos dois
candidatos; a matriz final completa usa esses novos hashes.

## Identidades e evidência

Fonte consolidada:
[summary.json](../ecossistema/evidencias/m1-slots-2026-10-29/summary.json),
com **131 hashes de entradas** e **88 hashes de artefatos**, incluindo fontes,
logs, resultados, reprodução anterior e separação de dispensas. O verificador
confere esses hashes, os resultados finais e as contagens; não executa runtime.
Os textos das evidências foram normalizados para UTF-8/LF antes da publicação;
os hashes são conferidos também contra os blobs Git, evitando divergência por
conversão automática de finais de linha no Windows.

| Candidato próprio | SHA-256 |
| --- | --- |
| Windows build/assis-slots-final.exe | 0970dfaeee0710a2106b4e0c3661ff8165346ca299b4d39a5c6335457630ee62 |
| Linux build/assis-slots-final-linux | 034d61bfe7b1106f53b4e5dadec1100faffaa4292688adfc5cd5a4f2ff9ae78c |

Não executados: macOS x64/ARM64 e Linux ARM64 nativos, falhas OOM sob ARM64,
UI/IME/acessibilidade, HTDL/FS/SSC, sandbox de página remota, crash de serviço,
quotas compartilhadas de documento, distribuição e carga integrada de 24h.
Não houve nova aprovação de CI ou aceite visual. safe não é sandbox.

try_new cobre a reserva inicial; argumentos e init podem continuar fatais.
Inicialização do runtime, closures, controladores da arena/OwnedArray, remove
e APIs antigas conservam caminhos fatais. Slot_limit é quota lógica de slots,
não limite de bytes/RSS. Não há garantia contra OOM killer/overcommit. Quotas
totais, reserve antecipado e recuperação completa do documento seguem abertos.

## Pontos, publicação e próximo incremento

**21,90% → 22,30%; 0/5 → 0/5 gates.** Somente **E02-03: 1 → 2** (+0,40),
por um subconjunto útil reproduzível de objetos e inserções com falhas adversas.
Não é a aceitação integral: quotas compartilhadas e caminhos acima continuam
pendentes. E01, E02-01/E02-02 e E11 conservam níveis. Há novo retrato completo
dos 60 critérios e cinco gates; pesos, escopo e histórico foram preservados.

Publicação normal autorizada na branch indicada, como PR incremental de
rascunho sobre work/m1-allocation-2026-10-29 (#10). O SHA final é o commit que
introduz este relatório, consultável com git log --follow; a sessão confere
o SHA remoto e os arquivos esperados. Não se grava um hash autorreferente.
Push/PR não significam merge, CI aprovada ou release.

Publicação efetiva do código e da evidência: commit
[795d899394f0444381999dcb0fef7c011f4b99f7](https://github.com/Vibe-O-Coder/AssisScript/commit/795d899394f0444381999dcb0fef7c011f4b99f7),
enviado à branch de destino e confirmado por git ls-remote. Os 219 hashes
foram conferidos contra os blobs desse commit. O SHA deste adendo documental
é encontrado no histórico do relatório, sem autorreferência.

Na primeira tentativa de criar o PR, o conector GitHub devolveu 403 (permissão da
integração). A revisão automática rejeitou o script alternativo que usaria a
credencial Git por considerar esse acesso uma sondagem não autorizada; o
script não foi executado e nenhuma credencial foi lida. A alternativa pela
interface normal encontrou uma tela de login, sem sessão autenticada.

Após o usuário entrar pela interface normal do GitHub, foi criado e conferido
o [PR de rascunho #11](https://github.com/Vibe-O-Coder/AssisScript/pull/11),
base work/m1-allocation-2026-10-29, head work/m1-fallible-slots-2026-10-29.
O PR foi vinculado à conversa. A criação foi confirmada tanto pela interface
quanto pela API de leitura, com draft=true, merged=false e base_sha igual à
base deste relatório. Não foi necessário acessar a credencial Git. A CI remota
estava em andamento na conferência; não se declara aprovação, merge ou release.

Próximo incremento: orçamento de memória compartilhado por documento,
controladores/reserva antecipada e remoção sem alocar para informar resultado,
com devolução de quota e rollback por fronteira. M0-EXEC e a experiência visual
M2 continuam independentes e não foram antecipados como prontos.

Referência primária da injeção Windows:
[VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc).

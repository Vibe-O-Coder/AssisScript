# Relatório — compilação de página com orçamento de processo

**02/11/2026, America/Fortaleza. 41,70% → 42,20%; 0/5 → 0/5 gates.**
Meta solicitada de 50% não atingida. Unidade M0-EXEC/M1/M3 parcial; somente
E06-02 passa 2→3 (+0,50), para o perfil escalar comprovado. Demais 59 estados,
pesos, aceites, baseline congelada, histórico e cinco gates preservados.
Easy permanece a última etapa de todo o projeto.

## Base e problema reproduzido

Base publicada **fffd1b8bd3eb4c43eeab535f586a12e2e6719c0d**, branch
`work/m0-page-integration-2026-11-02`; GitHub fetch_commit e git ls-remote
confirmaram publicação/SHA. PR anterior não existia por 403 do conector.
[Base](../ecossistema/evidencias/m0-resource-budget-2026-11-02/published-base.json).
Estado, planos, fila, baseline, 60 critérios e contratos viewer/ABI/ADR lidos.
Histórico real, branches e worktrees conferidos; nenhuma AGENTS.md encontrada.
Sem subagentes. Projetos irmãos e alterações alheias preservados.

Cópia isolada sem hardlinks em
**C:/Users/babus/Desktop/AssisScript/work/resource-budget-20261102**, branch
**work/m0-resource-budget-2026-11-02**, remoto Vibe-O-Coder/AssisScript.
Não houve troca de branch alheia, reset, limpeza, merge ou force push.
O clone precisou execução permitida pelo ambiente Windows, assim como WSL e
testes em pastas temporárias. Isso não alterou os limites do produto.

Antes: VM/worker tinham fuel, memória, frames, concessões e IPC, mas a fonte
era compilada fora de um processo com orçamento. O CLI de autoria também
resolvia imports no disco antes de validar o subconjunto de página. Um build
próprio da revisão exata anterior recusa o comando novo antes de compilar:
[before.json](../ecossistema/evidencias/m0-resource-budget-2026-11-02/before.json).

Objetivo/IDs: E06-02 limita compilação e mantém interrupção; E02-03/E03-02
ampliam evidência de falhas/processos sem promoção; E07-05 mantém ativação
conjunta do Reader/SDK. Aceite: equivalência de bytes nos dois modos, imports
sem autoridade de disco, limites hostis, OOM/CPU reais, cancelamento/close/drop,
respostas falsas e fragmentadas, recursos sem residual e vizinha ativa.

## Implementação e decisões

`page-compile-worker` compila uma fonte por ASC1/1, em streams limitados.
`std/page.assis` é embutido por gerador verificável; somente seu nome canônico
é aceito. O caminho virtual não usa resolução, projeto/pacotes, ASSIS_PATH,
arquivo de saída ou aliases. Frontend/IR/backend ASV2 são os existentes;
safe, efeitos, números, ordem e rejeições do perfil são conservados. O CLI
normal de autoria não muda. O serviço não recebe flags/caminhos da página.

`std/pagecompiler.assis` copia fonte e implementa o supervisor em AssisScript.
Uma escrita e leitura de até 4096 bytes por avanço, resposta até 131088 bytes,
framing e verificação completa pela VM antes de publicar, sem executar código.
Deadline encerra/recolhe o compilador; close/drop cancelam. Resposta parcial,
forjada, inválida ou compilador morto não vira candidato. stderr é descartado,
sem transmitir diagnóstico/conteúdo privado ao shell. Autoria conserva check.

Provider escalar acrescenta abertura de compilador e telemetria, preservando
ABI v1/imports anteriores. Caminho absoluto é do host confiável, nunca download
de página. Ambiente mínimo, herança de três streams e 16 slots compartilhados.
Linux impõe AS/CPU/stack antes de exec; o compilador aplica a mesma política
seccomp default deny do worker antes de ler fonte. O filtro foi extraído sem
ampliar permissões. Windows configura Job antes de resume, limite de commit
privado, CPU usuário e um processo; GetProcessTimes reforça CPU a cada poll.
O sistema verifica Job periodicamente, sem prazo exato; isso foi observado
na prova inicial e motivou a conferência adicional, sem enfraquecer o aceite.

Orçamento: 16..512 MiB/1..10 s CPU; stream direto instala também tetos próprios
de 512 MiB/10 s. Deadline do supervisor é independente do limite de CPU.
RSS atual/pico e memória contabilizada são expostos separadamente. Windows
limitou 16 MiB privados com RSS observado acima de 16 MiB: o contrato não
chama esse teto de quota RSS. Linux limita AS e observa VmRSS/VmHWM.
Contadores podem desaparecer depois de exit. [Contrato e referência primária
dos limites Windows](../BIBLIOTECA-pagecompiler.md).

`pagereader::Session.prepare_source` acrescenta fase de compilação à navegação.
O ativo continua avançando; preparar não executa a página candidata. Depois
de compilar, a transação Reader/worker/concessões existente é reutilizada.
Falha de fonte/HTDL/layout/load, abort e close mantêm ou encerram os owners
corretos. Ações/reflow ficam suspensos durante navegação, como antes. O parser
e layout ainda são síncronos. Commit/publish conserva o contrato anterior.

Exemplo **51_compile_page.assis** compila fonte, ativa Reader/SDK/worker e
produz **PAGE-STATE 42**, executado nos dois hosts com artefatos novos. Catálogo,
dependências opcionais, documentação, Makefile, suíte nativa e instalador foram
sincronizados. A 31ª biblioteca usa o bit 30; o gerador permite até 31 opcionais,
preservando o limite definido da máscara u32 (não permite 32). A instalação
selecionada e completa valida essa fronteira. Sem pacote/release promovido.

## Validação e resultados

Matriz própria final: **194 métodos executados/4 not-run Windows x64**;
**188 executados/10 not-run Linux x64/WSL2**. Contagens de métodos, não de todos
os subcasos internos. Os 13 métodos novos de compilação foram executados nos
dois modos por host; worker e Reader também têm execuções separadas por modo.
Regressões: pagehost, backend, VM, parser HTDL, transações Reader, safe,
ownership e funções. Os not-run são específicos do OS; não viraram pass.
[Windows](../ecossistema/evidencias/m0-resource-budget-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m0-resource-budget-2026-11-02/linux.json).

**53/53 exemplos analisados em cada host**, com vitória/derrota do RPG.
Exemplo novo foi executado separadamente. Corpus de compilação compara bytes
com backend de arquivo otimizado/referência: constante 42, fatorial(8) e SDK.
Verificação VM independente recusa bytes adulterados antes de execução;
Reader/worker observam célula 42 somente após commit. Testes incluem source
NUL/UTF-8 inválido, cabeçalho/flags/tamanho, profundidade, imports/path traversal,
native authority em ramo morto, clock regressivo, EOF, deadline e resposta falsa.

Oráculo C de alocação faz malloc/touch até recusa sob 16 MiB e mantém o processo
vivo para medir. Windows aceitou 15 blocos MiB; Linux, 13, devido às bases
diferentes de contabilização. Valores exatos de RSS/AS/commit e durações de CPU
estão nos logs por modo, sem extrapolação. Loop C ocupa CPU até encerramento
por RLIMIT ou conferência de CPU/Job no provider; pai não mata pelo timeout
do teste. Uma compilação vizinha continua funcionando após recusa de memória.
**128 ciclos de criar/cancelar** por modo/host retornaram ao número original
de handles/fds do processo de teste. Isso não é aceite dos 1.000 ciclos da UI.

Instalador novo é reconstruído e testado em prefixos temporários, sem PATH,
associações, versão de release ou binários rastreados alterados. **23 testes
Node**, incluindo seleção pagecompiler, dependências de pagereader, instalação
completa e execução do serviço embutido instalado. Logs/hashes e comando no
[registro Windows Node](../ecossistema/evidencias/m0-resource-budget-2026-11-02/windows-node.json).

Erros de desenvolvimento foram corrigidos antes da matriz final: tipo byte
explícito, fixture com utf8 duplicado, header stddef, provider gráfico ausente
no teste que importa Reader, assinatura ctypes de HANDLE, confirmação de exit
após EOF Linux e oscilação do limite periódico de CPU Windows. Duas tentativas
em ambiente restrito falharam antes dos testes ao criar DLL em temporário;
a execução permitida completou sem mudar asserções. A tentativa de CPU Windows
com limite apenas periódico passou de 6 s; foi corrigida no provider, mantendo
o teto do teste. Não foram contadas como aprovação. O relatório distingue
esses ensaios de desenvolvimento dos logs finais capturados pelo coletor.

Comandos reproduzíveis (ASSIS_BIN aponta ao candidato novo do respectivo OS):

```text
gcc <flags C11/O2 do host> src/assisc.c -o build/assis[.exe]
python tools/prepare-page-sdk.py --check
python tools/collect-resource-budget-evidence.py
python tools/validate-examples.py --output <host>-examples.json
python tools/run-resource-budget-example.py
python tools/stage-resource-budget-installer.py
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-resource-budget-evidence.py --write
python tools/verify-resource-budget-evidence.py
git diff --check
```

[Resumo, ambiente, hashes e arquivos](../ecossistema/evidencias/m0-resource-budget-2026-11-02/summary.json).
Não houve execução macOS/ARM, screenshot/aceite desktop, leitor auditivo real,
IME/DPI/multimonitor, CI global, 24h ou novo aceite de produto final.

## Limites, pontuação e fila integral

E06-02 **2→3**, +0,50: contrato funcional do perfil escalar local, adversos e
falhas Windows/Linux demonstrados; integração/aceites gerais continuam abertos.
Nenhum nível 4 e nenhum gate aprovado. E02-03/E03-02/E07-05 ficam em 2:
os testes novos ampliam suas evidências, sem demonstrar seus aceites integrais.
Novo retrato dos 60 estados/cinco gates acrescentado; passado não foi editado.

Windows continua **sem sandbox de autoridade** e restricted=true retorna -3;
macOS/ARM ainda sem esse serviço. Não é quota agregada de shell/Reader/RSS,
nem orçamento de todas as futuras bibliotecas/recursos. Parsing/layout podem
bloquear o shell; teardown Windows ainda pode aguardar 5 s. Não se afirma SLA
de UI, limite exato de RSS ou impossibilidade de falha nativa. O parser/SDK
permanecem bootstrap/read-only; os limites da decisão geral ASV2 não mudam.

Próximo: orçamento agregado de conteúdo/Reader e sandbox Windows/macOS, com
aceites nativos próprios; SDK mutável/strings/subscriptions e loader conjunto
HTDL/código/FS/SSC/recursos. Também seguem todas as pendências anteriores:
catálogo/recuperação/editor HTDL; desktop/leitor/DPI/monitores/shaping/bidi/IME;
FS tipado/layout incremental/SSC numérico; URL/TLS/rede/broker/perfis;
persistência, índice multidocumento/crawler/serviço; M4–M9, distribuição,
24h e aceite por terceiro. A meta 50% permanece pendente; Easy por último.

## Publicação

Branch **work/m0-resource-budget-2026-11-02**, remoto autorizado
**Vibe-O-Coder/AssisScript**. SHA publicado, paths/blobs e resultado de PR
ficam no adendo após commit/push/verificação; não são inferidos de commit local.
Hash do relatório obtido pelo histórico, sem referência autorreferente.


## Adendo — publicação confirmada

Implementação **3fb9810d6690b164e899825d62440904fb59373d** publicada em
[work/m0-resource-budget-2026-11-02](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m0-resource-budget-2026-11-02).
Git ls-remote devolveu o mesmo SHA. A árvore Git no conector GitHub não foi
truncada; os **83 paths, blobs, modos e tipos** foram comparados um a um com
git ls-tree local. [Inventário verificável](../ecossistema/evidencias/m0-resource-budget-2026-11-02/published-implementation.json).

**PR não criada:** o conector retornou HTTP 403 Resource not accessible by
integration. Não houve uso de credencial Git pela API. A negativa de PR não
impediu a publicação autorizada da branch. Sem merge/force push/release ou
alegação de CI global. Os 23 testes Node/instalador finais passaram com a lista
de arquivos estabilizada; matriz, exemplos e hashes preservados.

Este inventário e adendo recebem commit documental posterior, identificado
pelo histórico. O masterprompt no caminho original solicitado foi atualizado
com a continuação, preservando integralmente suas entradas anteriores.
**42,20%, 0/5 gates; meta 50% pendente; fila integral preservada, Easy por último.**

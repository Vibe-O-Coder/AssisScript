# Relatório — isolamento Windows do worker e compilador

**02/11/2026, America/Fortaleza. 42,20% → 42,70%; 0/5 → 0/5 gates.**
Meta 50% ainda pendente. Unidade lógica E06-04/M0-EXEC parcial, com integração
Reader/SDK e compilação preservada. E06-04 passa 2→3 (+0,50) para Windows/Linux
x64 demonstrados; macOS/ARM, broker e integração de produto completa continuam
abertos. Nenhum nível 4; pesos, aceites, baseline congelada, demais 59 estados,
histórico e gates preservados. Easy permanece a última etapa do projeto.

## Base e reprodução

Base publicada **f12a1f2a9a7edf97e829d5f7c6e2f29980961414**, branch
`work/m0-resource-budget-2026-11-02`, confirmada por GitHub fetch_commit e
git ls-remote. Estado/planos/fila/60 critérios, baseline e contratos
viewer/ABI/ADR lidos; histórico, branches e worktrees inspecionados.
Nenhuma AGENTS.md encontrada, nenhum subagente usado.

Cópia isolada sem hardlinks:
**C:/Users/babus/Desktop/AssisScript/work/windows-isolation-20261102**,
branch **work/m0-windows-isolation-2026-11-02**, remoto
**https://github.com/Vibe-O-Coder/AssisScript.git**. A cópia original continua
antiga/suja e foi preservada, assim como projetos irmãos. Sem reset, limpeza,
troca de branch de outra sessão, merge, force push ou promoção de release.

Provider da base foi reconstruído das fontes exatas e reproduziu
`restricted=1 → -3, token 0`, mesmo com caminho confiável válido.
[Reprodução e hash](../ecossistema/evidencias/m0-windows-isolation-2026-11-02/before.json).
Objetivo: exigir restrições nativas Windows antes de entrada hostil, testar
tentativas reais de IO/autoridade e manter compilação/VM/Reader/vizinhas.

## Implementação e decisões

O provider Windows cria LPAC sem capability SIDs, identidade aleatória de
128 bits e perfil exclusivo por processo. Não se reutiliza perfil existente.
Só duas cópias fixas de exe/provider confiáveis entram na pasta temporária;
DACL protegida dá leitura/execução à SID e controle ao usuário/System.
Nenhuma ACL de pasta/arquivo existente ou exceção de rede é alterada.

SECURITY_CAPABILITIES, opt-out de ALL_APPLICATION_PACKAGES, restrição de
filhos e mitigations de código dinâmico/extension points são obrigatórios.
Token AppContainer, SID/capabilities e Job são conferidos antes de resume.
Job mantém memória/CPU/um processo/kill-on-close e acrescenta restrições de
clipboard/UI. Erro não autoriza fallback irrestrito. Fonte e código de página
nunca escolhem um executável nativo. Toda lógica de VM, SDK, supervisão,
framing, navegação e transação continua em AssisScript; C adapta o OS.

Worker restrito usa esse perfil; compilador supervisionado sempre o exige.
ABI/assinaturas/imports anteriores conservados. `assw_restrict` verifica o
token real no filho; HELLO sozinho não autentica um executável arbitrário.
Mecanismos de falha/diagnóstico só existem em build ASSIS_WORKER_TESTING.
Builder/Makefile/suíte/documentação/avisos de dependência sincronizados.

Close encerra/recolhe, fecha handles, remove cópias/pasta/perfil e retorna
-4 nativo se a remoção falhar; o wrapper de close existente não propaga esse
retorno. Processo inicia sem console via DETACHED_PROCESS, preservando os
três streams explícitos e sem modificar LowBoxConsoleEnabled do usuário.
Ambiente contém somente SystemRoot/USERPROFILE/LOCALAPPDATA necessários ao OS,
sem PATH ou variável sentinela. Não são concessões de leitura do perfil.

Perfil, ownership/thread/falhas/dependências e referências primárias estão em
[windows-isolation-v1](../ecossistema/PERFIL-WINDOWS-ISOLATION-V1.md).
Windows depende de Advapi32/Userenv/BCrypt do sistema além de Kernel32/UCRT;
nenhum binário Microsoft novo é redistribuído. Ponte original sob LICENSE.

## Validação

**202 métodos executados/4 not-run Windows x64; 188 executados/18 not-run
Linux x64/WSL2**, com 53 exemplos por host e 23 testes Node Windows. São
contagens de métodos, não de todos os subcasos internos. Resultados finais
por host/modo, contagens e hashes ficam no
[resumo verificável](../ecossistema/evidencias/m0-windows-isolation-2026-11-02/summary.json).
Os logs distinguem executados e not-run; nenhum teste Windows é marcado pass
no Linux. Os quatro métodos novos usam um programa C independente, sem helper
de token do produto, além das regressões reais de compilador/worker/Reader.

O oráculo confirma AppContainer, zero capabilities e SID diferente por spawn.
AccessCheck recusa grant ALL_APPLICATION_PACKAGES e aceita
ALL_RESTRICTED_APPLICATION_PACKAGES, comprovando LPAC por efeito. Runtime
próprio é legível, enquanto escrita, sentinela privada, runtime vizinho,
registro do usuário e processo pai retornam acesso negado (5). Handle
sentinela/variável secreta não são herdados; clipboard é recusado (5), filho
nativo é bloqueado (367), memória executável é recusada (1655).
WinSock falha já em WSAStartup (10107), sem chegar ao listener do teste;
isso não é descrito como connect executado e posteriormente negado.

Seis fronteiras de criação, repetidas três vezes por modo, retornam -4/token
zero sem perfil/pasta/handle residual; incluem processo suspenso antes de
retomada e falha após associação ao Job. **64 ciclos de worker por modo**
mantêm contagens de perfis/pastas/handles e recusam token encerrado. Serviço
de compilação passa pelo mesmo oráculo antes de receber fonte.
Testes existentes acrescentam **128 cancelamentos de compilador por modo**,
OOM/CPU reais e vizinha ativa, imports negados, respostas falsas, framing,
epoch/replay, crash/deadline, rollback/abort/reload e grants/revogação.

Exemplo 51 compila fonte e ativa Reader/SDK/worker com isolamento requerido,
sem --trusted-local, observando PAGE-STATE 42. Exemplo 49 também exige
isolamento por padrão; opt-out local explícito continua testado no Windows.
Exemplos são analisados e o RPG tem vitória/derrota por host. Instalador novo
é reconstruído e testado em distribuição/prefixos temporários, sem PATH,
associações ou binários rastreados alterados. Não há pacote promovido.

Ensaios de desenvolvimento não são somados à matriz final: criação inicial
sem perfil/ambiente exigido falhou, CREATE_NO_WINDOW causou DLL init failure,
consulta TokenIsLessPrivilegedAppContainer retornou ERROR_INVALID_PARAMETER,
e o primeiro teste WinSock consultou incorretamente GetLastError em vez do
retorno WSAStartup. Foram corrigidos; AccessCheck verifica LPAC de forma
independente. Uma gravação de fixtures com codificação local foi revertida
para UTF-8 e os conjuntos afetados foram repetidos. A primeira cópia Git
e criação/ACL de DLL temporária exigiram execução permitida pelo ambiente;
isso não enfraqueceu as asserções ou restrições do produto.

Comandos reproduzíveis, ASSIS_BIN apontando ao compilador novo do host:

```text
gcc <flags C11/O2 do host> src/assisc.c -o build/assis[.exe]
python tools/capture-windows-isolation-before.py
python tools/collect-windows-isolation-evidence.py
python tools/validate-examples.py --output <evidencia>/<host>-examples.json
python tools/run-resource-budget-example.py --evidence-dir <evidencia> --stage-dir build/isolation-example --require-isolation
python tools/stage-resource-budget-installer.py --evidence-dir <evidencia> --stage-dir build/isolation-distribution
python tools/prepare-page-sdk.py --check
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-windows-isolation-evidence.py --write
python tools/verify-windows-isolation-evidence.py
git diff --check
```

## Limites e continuidade integral

Windows 10 x64 19045 e Linux x64/WSL2 foram executados; macOS/ARM e outros
builds Windows não foram. Não há Win32k lockdown ou proteção contra kernel/
canais laterais. Recursos de sistema autorizados ao LPAC e armazenamento
próprio existem; não se anuncia negação universal de arquivos nativos.
Perfil tem disco gravável sem quota. Crash do shell não tem coletor de
perfis/pastas órfãos; limpeza com falha do OS também exige recuperação futura.

Criação/cópia/perfil e teardown são síncronos; parsing/layout no shell também.
RSS observado não é commit nem quota agregada shell/Reader. Não há SLA de UI,
sandbox do broker, partição de produto, URL/DNS/TLS/rede geral ou página remota
aceita. SDK segue escalar/read-only e HTDL bootstrap. Nenhum gate aprovado.

Próximo: quota agregada de conteúdo/Reader e recuperação de disco/perfis,
sandbox macOS com execução própria; SDK mutável/strings/subscriptions e loader
HTDL/código/FS/SSC/recursos. Toda fila anterior permanece: catálogo/recuperação/
editor HTDL, desktop/leitor real/DPI/monitores/shaping/bidi/IME, FS tipado/layout
incremental/SSC numérico, rede/broker/perfis, persistência/índice multidocumento/
crawler/serviço, M4–M9, distribuição, 24h e aceite por terceiro. Meta 50%
pendente, Easy por último. Não se muda peso/escopo para atingir a meta.

## Publicação

Branch **work/m0-windows-isolation-2026-11-02**, destino autorizado
**Vibe-O-Coder/AssisScript**. SHA remoto/paths/blobs e resultado da PR serão
registrados no adendo após verificação. Commit local não prova publicação;
push não significa CI, merge, release ou gate. Hash do relatório pelo histórico.


## Adendo — publicação confirmada

Implementação **667d161b4e5476c8e072a848084f3f3d4df20424** publicada em
[work/m0-windows-isolation-2026-11-02](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m0-windows-isolation-2026-11-02).
Git ls-remote confirmou o mesmo SHA. A árvore remota pelo conector GitHub
não foi truncada: **87 paths, blobs, modos e tipos** comparados individualmente
com a árvore local. [Inventário](../ecossistema/evidencias/m0-windows-isolation-2026-11-02/published-implementation.json).

PR não criada: conector retornou **403 Resource not accessible by integration**.
A branch está publicada; não houve uso da credencial Git pela API para criar PR.
Não há merge, force push, release ou alegação de CI global. Os testes finais
foram 202/4 Windows, 188/18 Linux executados/not-run, 53 exemplos por host,
23 Node Windows e exemplo 51 restrito com PAGE-STATE 42 em ambos.
Provider de produção também foi conferido sem símbolos assw_test_*.

Inventário/adendo/continuidade recebem commit documental posterior,
identificado pelo histórico. O masterprompt no caminho original solicitado
foi atualizado, preservando suas entradas e alterações anteriores.
**42,70%, 0/5 gates; meta 50% pendente; fila integral preservada; Easy por último.**

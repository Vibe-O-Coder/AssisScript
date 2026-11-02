# Relatório — decisão escalar e Reader com worker

Data **02/11/2026**, America/Fortaleza. **40,20% → 41,70%; 0/5 → 0/5 gates**.
A meta solicitada de 50% permanece pendente. Unidade verificável M0-EXEC/M3/M4
parcial, com alternativa Wasm comparável e integração local; não encerra marcos
ou o perfil completo do navegador/buscador.

## Base, objetivo e estado anterior

Base **0345d567a7ade632546805fc18eca5ca32749cdb**, branch publicada
`work/m0-page-worker-2026-11-02`. SHA confirmado por GitHub/fetch_commit e
git ls-remote. [Registro da base](../ecossistema/evidencias/m0-page-integration-2026-11-02/published-base.json).
Histórico, branches/worktrees, planos, fila, 60 estados, baseline e contratos
viewer/ABI/ADR foram consultados. Sem AGENTS.md encontrado; sem subagentes.

A pasta original continua antiga/suja e não foi usada como base. Cópia nova
sem hardlinks em **C:/Users/babus/Desktop/AssisScript/work/page-integration-20261102**,
branch **work/m0-page-integration-2026-11-02**. Clone local precisou permissão
de execução por erro Win32 5 de signal pipe. Nenhum reset/limpeza/force push,
troca da branch alheia, merge ou release. Projetos irmãos preservados.

Durante a leitura, a cópia de trabalho anterior exibiu marcadores de conflito
nos arquivos de progresso. Os objetos Git do commit e o clone isolado foram
conferidos depois: estão íntegros. A avaliação não atribui correção ou pontos
a esses marcadores transitórios e não altera a cópia anterior.

O estado anterior já tinha backend ASV2, SDK, supervisor/IPC e worker. Não
foram reimplementados. Faltavam alternativa Wasm com limites comparáveis,
decisão delimitada e ativação conjunta com Reader. A reconstrução da revisão
exata anterior recusa o import novo de pagereader, antes de executar página:
[before.json](../ecossistema/evidencias/m0-page-integration-2026-11-02/before.json).

Objetivo/IDs: E00-03/E06-01, comparar e escolher executor do perfil escalar;
E06-03/E07-04/E07-05, manter concessões e eventos entre Reader/SDK/worker;
E11-04, medir corpus/custos/memória observada sem extrapolar. Aceite: fonte
real vs nativo/VM/Wasm, bytes hostis/fuel/capacidades, teclado/ponteiro/ação
acessível até SDK, navegação/rollback, pressão de retorno, falha e vizinha.

## Resultado e decisões

O candidato Python traduz ASV2 para wasm32 limitado. O harness Node só aceita
bytes canônicos reconstruídos, usa validação V8 e zero imports. Memória fixa
de 128 KiB, regiões separadas, frames lógicos, fuel total/quanta e limites de
calls; MIN/-1, resto e shifts preservam a linguagem. Estado suspenso aceita
resposta somente com identidade/request/call corretos; revoke/close não
reativam. Não é loader Wasm geral, provider de sandbox ou segundo HTDL em JS.

O [ADR-0001](../ecossistema/ADR-0001-EXECUCAO-PAGINA.md) escolhe ASV2 para o
perfil escalar local. Wasm executou loops mais rápido neste protótipo; não foi
descartado por falta de fuel do spike histórico. ASV2 conserva integração e
auditoria em AssisScript sem incluir engine/embedding novo no produto. Executor
geral, objetos/ownership, SDK completo e sandbox por OS continuam abertos.
Não há dependência redistribuída nova; versões/licenças e manutenção constam
do ADR, com referências primárias e inventário do runtime de comparação.

`stdlib/pagereader.assis` coordena Reader e pageworker em AssisScript. Copia
HTDL/código antes da etapa assíncrona; fonte idêntica é validada dos dois lados.
Prepara layout/nomes acessíveis e espera HELLO, LOAD e ACK das concessões.
Nenhum script candidato executa antes de commit. Publicação MSAA falha sem
trocar documento ou worker. Commit local troca ambos e revoga a geração antiga.
Identidade externa por Session não se confunde com documento 1 interno do
worker: processo/epoch/origem delimitam o contexto.

Ativações nativas entram em FIFO de 32. Payload é índice na projeção imutável,
convertido em handle por SDK sob concessão; não é capacidade ou ponteiro.
Hidden/disabled/foco/window/request passam pelo Reader. Evento só sai da FIFO
após ACK=0, com drenagem antes de novos posts e recusa explícita quando cheia.
Os 32 eventos aceitos são observados exatamente uma vez, com o 33º recusado.
Navegação congela novas ações e descarta eventos antigos no commit. Trap/fuel/
falha mantém leitura, encerra worker e permite recuperação por nova preparação;
uma segunda página continua funcionando. Abort/close e destruição own revogam
processos sem callback da página.

Exemplo **50_page_reader.assis** e **pages/reader-counter.assis** oferecem botão
com teclado/ponteiro/ação acessível, contador no painel do shell e saída no
terminal. Biblioteca, catálogo, dependências opcionais, manifestos/instalador,
Makefile e driver de testes nativos foram sincronizados. O painel do contador
adicional ainda não publica valor assistivo. [Contrato e comandos](../BIBLIOTECA-pagereader.md).

## Validação reproduzível

Matriz final própria: **151 execuções de métodos e 2 not-run Windows x64**;
**142 execuções e 11 not-run Linux x64/WSL2**. Não são contagens de todos os
subcasos. Há 19 métodos novos: pagereader 10 (dois modos por host, com um
Windows-only não executado em Linux) e Wasm 9, que comparam fontes nos dois
modos. Regressões: worker 19 (17 executados/2 not-run por host), pagehost 13,
backend 10, VM 10, parser HTDL 16, transações Reader 15, Reader 10, safe 5 e
ownership 26. Esses dois conjuntos Reader têm 4/3 not-run Linux. Todos os
**52 exemplos** passaram na análise por host, com vitória/derrota do RPG.

[Windows](../ecossistema/evidencias/m0-page-integration-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m0-page-integration-2026-11-02/linux.json),
[resumo e hashes](../ecossistema/evidencias/m0-page-integration-2026-11-02/summary.json).
Comandos, duração, SHA-256 de compiladores/providers/workers/logs e resultados
por método estão rastreados. Ambiente/hardware sem identificadores pessoais
em windows-environment.json e linux-environment.json da mesma pasta.

Oráculos: execução nativa otimizada/referência e modelo Python de i64; V8
independente para os bytes Wasm; fórmula sum(range(2000)), factorial(8) e
250 adições; estado esperado 0/1/2/3/32 para o caminho de eventos; protocolos
e testes adversos de supervisor/SDK já existentes reexecutados. MSAA/publicação
é execução Windows, sem inferir leitor real ou screenshot de desktop.

Benchmark: quatro programas, sete amostras de quarenta instâncias por engine/
host (1120 execuções por engine/host, além de aquecimento/validação). Mesmo
resultado e passos, batch sum-2000 34014 passos/instância: VM/Wasm medianas
62/9,451 ms Windows e 75/8,4762 ms Linux. Casos pequenos ficam abaixo da resolução
inteira da VM; não há afirmação de velocidade com zeros. Custos end-to-end,
validador/engine separados, tamanho, RSS amostrado e limites metodológicos nos
dois JSONs de benchmark. RSS não é quota; amostras curtas não substituem 24h.

O teste de instalação Windows usa candidato recém-construído e distribuição
isolada, incluindo seleção `--with pagereader` e suas dependências transitivas.
23 testes Node, incluindo instalação/remoção em prefixos temporários, sem
alterar PATH/associações do usuário ou promover os binários rastreados.
[Registro](../ecossistema/evidencias/m0-page-integration-2026-11-02/windows-node.json).

Tentativa inicial Windows/reference falhou ao regravar host.exe temporário
com Permission denied; o log foi preservado em windows-page-reader-reference-attempt.log.
Fixtures passaram a usar diretório exclusivo por método e os dois modos foram
reexecutados com as mesmas asserções. Ensaios preliminares também identificaram
ajustes das fixtures de bytes/keyup/borrow e do ambiente Node no WSL; não foram
contados como testes aprovados. Nenhuma verificação foi enfraquecida.
Na conferência documental posterior, uma remoção de prefixo temporário também
recebeu Windows 5; log preservado em windows-node-uninstall-attempt.log, com
22/23 nessa tentativa. A suíte completa foi repetida sem alterar instalador
ou asserções. Isso registra uma falha observada de remoção imediata em Windows;
não é garantia de ausência de interferência do ambiente em outras instalações.

Comandos principais (ASSIS_BIN sempre aponta ao candidato próprio do host):

```text
python tools/capture-page-integration-before.py
python tools/benchmark-page-executors.py
python tools/collect-page-integration-evidence.py
python tools/collect-page-integration-evidence.py --only page-reader
python tools/validate-examples.py --output <host>-examples.json
python tools/record-page-integration-environment.py
python tools/stage-page-integration-installer.py
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-page-integration-evidence.py --write
python tools/verify-page-integration-evidence.py
git diff --check
```

## Régua, limitações e fila integral

Promoções: **E00-03 2→3 (+0,20)**, **E06-01 2→3 (+0,50)**,
**E06-03 2→3 (+0,50)**, **E11-04 1→2 (+0,30)**. Total **+1,50**, **41,70%**,
**0/5 gates**. Demais 56 estados, pesos, escopo/aceites, baseline e histórico
preservados; novo retrato completo de 60 níveis/cinco gates acrescentado.
Nível 3 delimita o perfil comprovado, com integração completa/aceite pendentes;
nível 4 não foi concedido. Integração Reader/loader/events amplia evidência,
mas E03-02/E07-04/E07-05 conservam nível 2: faltam os contratos completos.

Windows continua **sem sandbox de autoridade**, restricted=true retorna -3.
Linux restrito conserva tetos de AS/stack/CPU e filtros do provider; não se
amplia sua política. macOS/ARM não foram executados. Preparação/parsing e
teardown são síncronos; Windows pode aguardar até 5 s em kill/reap. Não há
garantia de latência de UI em tempo real. Worker pode morrer após o último
ACK; a transação local detecta a falha no próximo avanço. Copies/FIFOs/Reader
adicionais não entram na quota Store. Exemplo conserva File legado com alocação
fatal de caminho limitado a 4097 bytes. Captura desktop, leitor auditivo real,
DPI/monitores/IME/shaping/bidi e painel assistivo do contador sem aceite.

Próximo incremento: orçamento real de compilação/RSS e sandbox Windows/macOS;
SDK mutável/strings/subscriptions e loader conjunto HTDL/código/FS/SSC/recursos.
Também permanecem catálogo completo/recuperação HTDL/editor, aceites visuais,
FS tipado/layout incremental/SSC numérico, URL/TLS/rede/broker/perfis, persistência,
índice multidocumento/crawler/serviço, M4–M9, 24h/distribuição/terceiro. A decisão
geral VM/Wasm é reaberta ao ampliar valores/ownership. **Easy por último**.
Nenhuma pendência da fila anterior foi retirada; nenhum gate/prontidão remota,
CI global, merge ou release declarado. Meta de 50% não foi atingida.

## Publicação

Branch **work/m0-page-integration-2026-11-02**, destino normal
**Vibe-O-Coder/AssisScript**. Publicação/SHA e inventário são registrados no
adendo após commit/push/verificação. O SHA do relatório é localizado pelo
histórico, evitando hash autorreferente. Nenhum resultado de publicação é
presumido a partir de commit local.

## Adendo — publicação confirmada

Implementação **8fb60cdbd6ad5ff71f7501502c3bc2cd45254e6c** publicada por push
normal em [work/m0-page-integration-2026-11-02](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m0-page-integration-2026-11-02).
SHA remoto igual ao local. Os **72 paths e respectivos blobs Git** foram
conferidos individualmente pelo conector contra git ls-tree. [Inventário](../ecossistema/evidencias/m0-page-integration-2026-11-02/published-implementation.json).
Sem merge, force push, release ou declaração de CI global aprovada.

O parent efetivo é **3069ee801fea2ea0f23b94c985bc7be82722a73c**, atualização
documental que confirmou as PRs #22/#23 durante esta sessão. Comparação das
árvores: somente índices, relatórios/evidências históricos e lista gerada do
instalador, sem fonte de execução, teste ou mudança de nível. Foi preservada
na ancestralidade da nova branch. A referência de antes/reprodução dos testes
continua **0345d56**, e os 60 estados/histórico de partida são idênticos.

**PR desta unidade não criada:** o conector GitHub retornou HTTP 403 Resource
not accessible by integration. Não foi reutilizada credencial Git pela API.
A branch publicada e o inventário estão disponíveis para revisão; a negativa
do conector não impediu o push autorizado. Nenhuma nova aprovação foi pedida.

Este adendo/inventário recebe commit documental posterior, identificado pelo
histórico. Manifesto/evidência/instalador foram novamente conferidos após a
inclusão do inventário; os testes nativos não foram recontados. **41,70%,
0/5 gates; meta 50% pendente e fila integral preservada, Easy por último.**

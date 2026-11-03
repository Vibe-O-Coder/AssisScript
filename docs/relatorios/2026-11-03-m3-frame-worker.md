# Relatório — Frame e worker ASV2 com ativação conjunta

03/11/2026, America/Fortaleza. Base pública
**52ef3ead2e059395dafb17771214126f578ed19c**, confirmada pelo conector GitHub.
Branch **work/m3-frame-worker-2026-11-03**, cópia isolada
**C:/Users/babus/Desktop/AssisScript/work/frame-worker-20261103**.
Original e continuação anterior preservados, sem reset/limpeza/merge/force push
ou subagentes. O clone local exigiu execução fora da restrição inicial de
processos do Git; a cópia foi criada sem alterar as outras branches.

Unidade parcial M0/M3/M5: E00-01/E00-04/E04-05/E07-03/E07-04/E07-05/E11-01.
**47,50% → 47,90%, 0/5 gates.** Apenas E07-04 passa 2→3 (+0,40): células por
página/handlers/eventos ASV2, fila determinística e revogação agora integram o
Frame HTDL/FS/SSC e publicação nativa com falhas adversas. O contrato do perfil
escalar foi exercitado nos alvos aplicáveis; células por nó, inscrições,
valores gerais e mutação SDK continuam abertos. Não há crédito duplicado em
loader, ABI ou plataforma. Pesos, baseline e os 32 retratos anteriores ficam
preservados; o novo histórico contém os 60 estados e cinco gates completos.
**A meta de 50% não foi atingida; nenhum gate recebe aceite.**

## Problema e resultado

O Frame de leitura FS/SSC e o caminho Reader/worker tinham coordenadores
separados. Uma janela com o catálogo novo não podia ativar seu programa ASV2
na mesma transação. `std/frameworker.assis` agora prepara árvore, grafos,
layout, seleção, Packet e worker candidato a partir dos mesmos bytes HTDL.
Compilação de fonte é opcional, em processo descartável com orçamento/deadline.
Concessões são confirmadas antes de ativar; somente ASV2 verificado é executado.

Raster/MSAA são publicados primeiro. Após sucesso, os proprietários preparados
são transferidos sem alocação/callback de página; falha nativa permite retry
ou abort conservando o ativo. Não se promete transação distribuída do OS:
um worker pode morrer depois, caso em que a leitura continua e nova navegação
recupera a execução. O programa anterior segue suas fatias durante o preparo,
com novas ações suspensas até commit/abort. Fechar cancela compilação e ambas
gerações. A fila anterior só é descartada ao ativar o novo documento.

Reflow aumenta a revisão visual sem reiniciar código/estado/documento. Eventos
levam identidade de documento e revisão de Frame distintas. O payload SDK é o
ordinal do preorder semântico completo, não o índice de caixa: head, inline e
hidden também contam. Teclado/ponteiro/MSAA são revalidados no mesmo Frame;
fila de 32 entradas e ACK/backpressure conservam a ordem. Link #id continua
ação local do host, sem ser convertido em evento de botão no SDK.

ASIP/1 ganha LOAD_CATALOG/9 (resposta 137), com o mesmo envelope/limites de LOAD/1.
O worker revalida o catálogo estático antes de expor a projeção imutável.
LOAD/1 permanece bootstrap estrito, comprovado por cliente binário independente.
Worker antigo recusa a nova operação; não há downgrade silencioso. O provider
C/ABI 1, imports SDK 1..8, gramática e compilador não mudam. Scripts HTDL e
recursos referenciados não são executados/carregados. A implementação principal
é AssisScript; os providers existentes apenas adaptam OS/IPC/COM/raster.

## Contratos, arquivos e exemplos

- [API frameworker](../BIBLIOTECA-frameworker.md) e
  [perfil frame-worker-local-1](../ecossistema/PERFIL-FRAME-WORKER-V1.md).
- stdlib/frameworker e pageworker; tools/page-worker; catálogo, manifestos,
  Makefile e CI. Nenhuma dependência ou licença redistribuída nova.
- [Exemplo 64, headless](../../exemplos/64_frame_worker.assis) e
  [65, janela](../../exemplos/65_frame_worker_window.assis), com compilador e
  worker absolutos concedidos pelo shell. O 65 aceita --once/--smoke.
- [Suíte integrada](../../tests/test-frame-worker.py), cliente ASIP independente
  em test-page-worker, coletores, verificadores e perfil worker no preparador
  do pacote de desenvolvimento Windows.

## Validação rastreada

[Resumo/hash/oráculos](../ecossistema/evidencias/m3-frame-worker-2026-11-03/summary.json),
[Windows](../ecossistema/evidencias/m3-frame-worker-2026-11-03/windows.json) e
[Linux](../ecossistema/evidencias/m3-frame-worker-2026-11-03/linux.json).
Cada registro guarda comando, SO/Python, hash do compilador, duração, logs e
contagens executadas/not-run. A tabela separa execução de not-run; entradas omitidas nunca são contadas
como execução.

| Suíte / worker | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| frame-worker / optimized | 14/0 | 12/2 |
| frame-worker / reference | 14/0 | 12/2 |
| page-worker / optimized | 18/2 | 18/2 |
| page-worker / reference | 18/2 | 18/2 |
| page-reader / optimized | 10/0 | 9/1 |
| page-reader / reference | 10/0 | 9/1 |
| page-compiler / optimized | 13/0 | 13/0 |
| page-host / optimized | 13/0 | 13/0 |
| page-backend / optimized | 10/0 | 10/0 |
| pagevm / optimized | 10/0 | 10/0 |
| windows-isolation / optimized | 4/0 | 0/4 |
| framehost / optimized | 12/0 | 10/2 |
| catalog-frame / optimized | 21/0 | 18/3 |
| install-mask / optimized | 2/0 | 2/0 |
| **Total** | **169/4** | **154/19** |

Host otimizado/referência é executado dentro da suíte frame-worker; o coletor
repete-a com workers otimizados e de referência. Page-worker e page-reader
também têm registros dos dois modos. Outros testes preservam sua comparação
interna otimizado/referência. Há geração de cinco formatos do exemplo 64;
somente Windows/Linux x64 têm execução nativa. Linux gráfico/macOS/ARM não
recebem aceite. Windows-isolation no Linux permanece integralmente not-run.

**67/67 exemplos por host**, finais vitória/derrota do RPG, instalação/execução/
remoção isoladas e seleção transitiva de frameworker verificadas por hash.
Windows executa também **4 testes de locks e 23 Node** de distribuição.
A seleção transitiva fecha **23 bibliotecas** em ambos os hosts.
Linux usa runtime explicitamente construído/concedido em pasta temporária
separada: o instalador shell instala as bibliotecas e o compilador, sem anunciar
instalação automática do provider/worker. Nenhum PATH, associação ou prefixo
global foi alterado. Quantidades exatas e hashes estão nos JSONs de instalação.

O pacote Windows de desenvolvimento inclui compilador/provider gráfico/worker/
provider de processo reconstruídos juntos, seleciona frameworker e executa os
exemplos headless/janela após instalação em prefixo com espaços; a remoção
conserva arquivo pessoal. Não é release. O ZIP local é
`build/AssisScript-frameworker-development-20261103-windows-x64.zip`.
BUILD-INFO lista os hashes reais. Summary/development-bundle ficam fora do ZIP
para não criar referência ao próprio hash; suas cópias canônicas vão ao Git.

Oráculos: preorder e resultado esperado explícitos, contagem por XML independente
no cliente binário, índices de estado, fila cheia e comparação de eventos por
requests/identidades. A entrada inicial do novo teste ASIP usava atributos
sem aspas, válidos em HTDL mas inválidos no oráculo XML. O teste, não o produto,
foi corrigido para aspas explícitas. Os dois logs iniciais ficam preservados;
os resultados finais só contam as repetições completas aprovadas. Erros
iniciais de ambiente/compilação/fixture não são passes.

Recusa real de alocação do OS usa suprimentos 0/1/2/4/8, em ambos os modos,
sem estresse de OOM do sistema. Preserva Frame/worker e aborta candidato que
eventualmente complete. O teste cobre recusas de slabs e caminhos atingidos,
não cada alocação lógica nem quota agregada de RSS. Combina ainda fonte/código/
FS/SSC mutáveis após retorno, worker com fuel esgotado, vizinho independente,
compilação cancelada, publicação recusada/retry e descarte de gerações antigas.

Nova tentativa visual foi realizada nesta sessão usando a skill Computer Use.
O primeiro caminho não confirmado terminou em app approval timed out. Após
conferir o executável do pacote anterior, a janela **AssisScript - catalogo de
leitura** abriu e foi selecionada da listagem real. Screenshot-only falhou com
**FrameArrived timed out: timed out waiting on channel**. Nova seleção e captura
falharam com **window capture timed out: timed out waiting on channel**.
Zero screenshots/inputs; nenhum mecanismo alternativo de captura/UI. A janela
nova Frame/worker tem testes nativos once/smoke, sem inspeção visual desktop.
[Registro e hashes](../ecossistema/evidencias/m3-frame-worker-2026-11-03/desktop.json).
Leitor real/DPI/monitores/IME continuam pendentes.

Comandos principais, ASSIS_BIN apontando ao candidato fresco de cada host:

```text
gcc -O2 -std=c11 -municode -static -static-libgcc -Wl,--no-insert-timestamp src/assisc.c -o build/assis.exe
cc -O2 -std=c11 src/assisc.c -o build/assis-linux
python tools/collect-frame-worker-evidence.py
python tools/collect-frame-worker-evidence.py --resume
python tools/validate-examples.py --output <evidencia>/<host>-examples.json
python tools/verify-frame-worker-install.py
python tools/prepare-development-installer.py --profile worker
python tools/check-ecosystem-references.py --output <evidencia>/reference-integrity.json
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-frame-worker-evidence.py --write
python tools/verify-frame-worker-evidence.py
git diff --check
```

Linux usa Python3 no Ubuntu WSL2. A restrição inicial de acesso ao WSL e de
execução do GCC foi resolvida pelo fluxo normal de revisão. As fontes atuais
foram compiladas em ambos os hosts. Os 57 arquivos congelados têm integridade
conferida; os 16 cenários integrais dos rascunhos continuam not-run, sem serem
contados como conformidade visual ou de runtime.

## Fila integral, limites e próximo incremento

Próximo: loader de recursos locais sob concessão explícita, com resolução de
versões/cancelamento e integração ao candidato. Controles label/input/form,
imagem, live regions e hierarquia assistiva completa também continuam abertos.
SDK permanece escalar/read-only-1, sem strings/valores gerais, células por nó,
subscribe/unsubscribe ou mutação visual. Identidade incremental/editor,
shaping/bidi/IME, RSS/disco/perfis órfãos, sandbox macOS/ARM, rede/TLS/origens/
perfis, persistência, busca multidocumento, M4–M9, 24h reais, distribuição por
terceiro e todos os aceites permanecem integralmente na fila. Easy por último.
47,90% não mede prazo nem prontidão de páginas remotas; G2 segue aberto.

## Publicação

O usuário autorizou explicitamente publicação no GitHub nesta conversa, além
da autorização do masterprompt para Vibe-O-Coder/AssisScript. Commit, envio,
SHA/árvore/inventário remotos e tentativa de PR serão registrados em adendo.
Não se afirma merge, release ou CI remota nova aprovada.

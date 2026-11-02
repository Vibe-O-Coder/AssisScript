# Relatório — transações FS de página inteira e dirtiness por nó

> Publicação confirmada após autorização explícita; implementação 828d051 e
> adendo d6d0798 no remoto. A seção final registra verificação e PR indisponível.

02/11/2026, America/Fortaleza. Base pública f274c9f7d4dda1e1d9a7bfe92b172354b89a4203,
branch work/m5-page-presentation-2026-11-02, cópia isolada
C:/Users/babus/Desktop/AssisScript/work/page-presentation-20261102.

**44,90% → 45,30%; 0/5 → 0/5 gates. Meta 50% ainda pendente.**
E08-01 2→3 (+0,40); E02-03/E07-02/E08-04/E11-01 recebem evidência sem promoção.
Fundação M5, sem encerrar M3/M4/M5. Os 60 estados e cinco gates constam do
novo retrato no histórico. Pesos, aceites, baseline e história anterior não
mudaram. Publicação deste incremento é registrada no adendo ao final.

## Base, problema e resultado

A pasta original continua antiga/suja e foi preservada, assim como a cópia
htdl-recovery que outra sessão atualizava documentalmente. Worktrees, branches,
histórico, remoto e relatórios mais recentes foram consultados antes de escolher
a unidade. Nenhum subagente, reset, limpeza de outras pastas ou troca de branch
alheia foi usado. Esta cópia é um clone local sem hardlinks da implementação.

O conector GitHub confirmou f274c9f como cabeça pública do núcleo FS/SSC e seu
objeto commit/tree; a árvore c761d1e31e54f7606d51788ac1bb01860c0008ca coincide
com o Git local. A publicação FS/SSC antes pendente no masterprompt está,
portanto, resolvida. Não foi necessário republicar esse payload.

Antes, Program.evaluate publicava um Style por nó. Avaliar o primeiro nó com
sucesso e falhar no segundo não fornecia ao host uma transação da página
inteira. Não havia cache de contextos entre chamadas nem versão semântica
do Document. Isso era uma limitação explícita do núcleo anterior, sem exigir
nova sintaxe ou alteração da semântica da linguagem.

Agora [flowpage](../BIBLIOTECA-flowpage.md) é um coordenador real em AssisScript:
compila FS imutável, enumera todos os elementos apresentáveis, prepara em banco
separado e só publica quando todo o conjunto passou. O exemplo 55 demonstra
dois painéis com estado node independente. As saídas não são geometria.

## Implementação e decisões

Perfil page-fs-256-v1: até 256 elementos, incluindo body e descendentes hidden;
Inputs de tamanho fixado em 1..2048. begin/stage/commit/abort permitem contextos
por nó e qualquer ordem de preparação. refresh atende contexto comum. Conjunto
incompleto, nó repetido/forjado, documento alterado durante a preparação, erro FS
ou recusa de alocação impede toda a publicação. Commit troca índice de dois
bancos prealocados, sem copiar/alocar. Nenhum resultado candidato é consultável.

O cache compara instância/slot/geração, versão semântica e presença/tipo/valor
de todas as entradas. Não depende de hash ou dirty informado pelo chamador.
Entrada alterada reavalia o nó inteiro; mutação semântica aceita invalida todos
os nós. Contextos candidatos não contaminam cache confirmado após abort. O caso
sem mudanças não aloca Style, inclusive sob recusa real do alocador.

O grafo FS continua puro, tipado, com ramos curtos e produtor único. Células
page precisam do mesmo valor efetivo em todos os nós, incluindo aliases/defaults
e contextos sem binding. Células node podem diferir. Program.shared_state e
Inputs.capacity são inspeções locais do host, sem capacidade de página.

Document.semantic_version cresce só após append/texto/reparent/remoção aceitos;
reserva e falhas não incrementam. No-op aceito pode incrementar, conservadoramente.
Não há wrap. O campo substitui o limite que não era consultado depois de init:
corpo de 64 bytes, cobrança e quota na Tree permanecem iguais, verificados pela
suíte de memória. nodes() continua somente leitura, sem mutação pública que
contorne o contador. Não se introduz nova ABI de plataforma ou execução.

Após falha FS, saídas anteriores permanecem nos nós sobreviventes e checked/
disabled/hidden atuais continuam na árvore. Remoções/navegação revogam leituras
imediatamente; IDs textuais e slots reciclados não transferem estilo. Nó novo
sem conjunto válido usa padrões. O host ainda precisa reaplicar essas saídas
à árvore atual e gerar geometria/acessibilidade coerentes. Esta entrega não
afirma que o último quadro gráfico já realiza essa composição.

Reserva conservadora: 401000 + fonte + 2*capacidade*(20+4*inputs)*8 bytes de
corpos solicitados. Inclui programa, bancos, controlador e um Style transitório;
exclui alocador/RSS, Document/Inputs externos, layout/SSC/recursos. Construtor
fechado libera seus recursos parciais no drop. Não é quota integral de página.

Catálogo, shell e manifestos Windows incluem flowpage e seu fechamento de oito
bibliotecas. O novo bit opcional é 33; os anteriores não foram renumerados.
Makefile/CI Windows/Linux incluem a suíte. Não houve atualização de binário
rastreado, VSIX, pacote de release, PATH ou associações do usuário.

### Correção necessária na remoção Windows

A primeira distribuição executou 22/23 Node; a remoção do prefixo worker
retornou Windows 5. Log preservado, sem tratá-lo como aprovação. A mesma classe
de falha constava da unidade anterior de integração, sem correção estrutural.

O problema foi reproduzido com locks reais: o instalador anterior falha ao
remover um arquivo cujo lock é liberado após 250ms; também já tinha apagado
LICENSE antes de descobrir o executável permanentemente bloqueado. Os quatro
testes novos têm 2 falhas antes e 4 passes depois, com logs preservados.

Agora a remoção verifica primeiro bin/assis.exe e tenta por até um segundo
por arquivo nos erros access denied/sharing/lock. Não força readonly, muda
permissões, encerra processo nem agenda remoção no reboot. Falha persistente
continua retornando erro com código do OS; readonly é recusado. Os demais
arquivos ainda não têm desinstalação transacional: bloqueio posterior pode
deixar remoção parcial. O instalador não ganha essa promessa por este ajuste.

## Testes e evidências

[Resumo/hashes](../ecossistema/evidencias/m5-page-styles-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m5-page-styles-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m5-page-styles-2026-11-02/linux.json).

| Suíte de métodos, otimizado/referência conforme cada contrato | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Página FS nova | 17/0 | 17/0 |
| Memória de documento | 12/0 | 12/0 |
| Árvore/modelo independente | 9/0 | 9/0 |
| Parser HTDL | 16/0 | 16/0 |
| Catálogo HTDL | 16/0 | 16/0 |
| FluxStyle | 17/0 | 17/0 |
| SSC finito | 9/0 | 9/0 |
| Transações Reader | 15/0 | 11/4 |
| Reader/worker | 10/0 | 9/1 |
| Instalador Windows com lock real | 4/0 | not-run: específico Windows |
| **Total nativo aplicável** | **125/0** | **116/5** |
| Distribuição Node | **23/0** | not-run: Node não usado nesta matriz Linux |
| Exemplos | **57/57** | **57/57** |

Os cinco métodos Linux indisponíveis dependem de provider gráfico. Os quatro
testes específicos do instalador Windows não entram no denominador Linux.
Execução: Windows x64 10.0.19045 e Linux x64/WSL2; detalhes/compiladores/Python
e tempos por suíte ficam nos JSONs. ARM/macOS: somente geração dos cinco formatos
em otimizado/referência, astFallbacks=0; execução nativa permanece not-run.

A suíte nova compara 48 transações determinísticas, seed 2026110204, com modelo
Fraction independente para divisão e rollback, incluindo falha no último nó.
Exercita contextos iguais em donos diferentes, ausência/zero, aliases page,
estados node, ordem inversa, duplicação, capacidade/reserva, bind conflitante,
hidden, mudança de seletor, versão alterada durante candidato, reciclagem de
slot/ID textual, navegação/close, retry e recusa real do OS. O teste de disabled
confirma erro FS sem desfazer a semântica atual. OOM não derruba o vizinho nem
troca o banco confirmado; depois de liberar memória, nova tentativa passa.

FS mantém Fraction para literais/operações e SSC reexecuta as 42 matrizes;
hashes das trajetórias coincidem entre hosts. A precisão analítica continua
restrita ao ensaio 8px/3s, sem extrapolar para todo o domínio. Exemplos incluem
as duas terminações RPG. Exemplo 55 em cada modo: PANELS -524288 0 / WORK 1 2.
É pipeline local de dados, sem nova captura visual ou leitor de tela real.

Instalação própria Windows/Linux em prefixo com espaços verifica hashes de
todas as bibliotecas selecionadas, executa o exemplo pelo compilador instalado
e remove arquivos geridos preservando arquivo pessoal. Windows reexecuta os
23 métodos Node com instalador recém-construído. A tentativa inicial falha e
os ensaios de desenvolvimento não são somados aos passes finais.

Integridade dos 57 arquivos de referência congelados passou; os 16 cenários
integrados históricos continuam not-run. SDK embutido, geração dos coeficientes,
manifestos e aritmética documental passaram. CI foi configurada, sem nova
aprovação remota afirmada. Não houve novo soak de 24h ou aceite por terceiro.

Comandos principais, ASSIS_BIN apontando ao compilador próprio de cada host:

```text
gcc -O2 -std=c11 -municode -static -static-libgcc -Wl,--no-insert-timestamp src/assisc.c -o build/assis.exe
cc -O2 -std=c11 src/assisc.c -o build/assis-linux
python tools/collect-flowpage-evidence.py
python tools/validate-examples.py --output <evidência>/<host>-examples.json
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-flowpage-install.py
python tools/check-ecosystem-references.py --output <evidência>/reference-integrity.json
python tools/prepare-page-sdk.py --check
python tools/generate-ssc-coefficients.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-flowpage-evidence.py --write
python tools/verify-flowpage-evidence.py
git diff --check
```

O compilador Windows usou GCC UCRT64 de C:/msys64/ucrt64/bin; o Linux foi
reconstruído via WSL. Problemas iniciais de PATH/temporários e fontes de teste
foram corrigidos antes da matriz final. Limitações de empréstimos foram
resolvidas por banco de dados e Style temporário, sem alterar a linguagem.

## Arquivos e fila preservada

Implementação: stdlib/flowpage.assis, documents.assis, fluxstyle.assis e
src/windows_setup.c. Testes: test-flowpage.py, test-installer-retry.py,
exemplo 55 e ferramentas collect/verify-flowpage*. Documentação, régua, CI,
Makefile e catálogo/manifestos acompanham a implementação; inventário exato no
diff/commit. Cada fonte relevante e log tem SHA-256 no resumo ou JSON do host.

Próximo incremento: composição de layout/snapshot comum e canais SSC agregados
coordenados com o conjunto de saídas da página, depois ligação ao Reader.
O cache por nó não é invalidação fina por vértice; não há inspector/LSP FS/SSC.

Fila integral: identidade incremental de editor; catálogo completo no Reader;
desktop/leitor de tela/DPI/múltiplos monitores; shaping/bidi/edição/IME;
SDK/strings/eventos gerais; loader de HTDL/código/FS/SSC/recursos/versões;
layout/políticas/snapshots/canais da página; quota agregada/RSS/disco/perfis
órfãos; macOS/ARM nativos; rede/broker/perfis/cookies/cache; persistência/banco,
crawler/índice/serviço de busca; M4–M9, corpus visual, 24h reais, distribuição,
terceiro e cinco gates. Nenhum item foi dispensado para aproximar 50%.
**Easy continua a última etapa de todo o projeto.**

## Publicação

A revisão está pronta para branch de trabalho no remoto
https://github.com/Vibe-O-Coder/AssisScript.git, sem merge, force push ou release.
O prompt autoriza publicação normal. O adendo registrará o resultado real e
a conferência de SHA/árvore/arquivos; até essa confirmação não se afirma envio.
O SHA deste relatório é localizado pelo histórico, evitando hash autorreferente.


## Adendo — publicação bloqueada pela revisão automática

Implementação concluída em **828d051ecc6478202002fa3af0da63d79e409b84**,
63 arquivos de código/testes/documentação/evidências, todos com bytes do índice
conferidos contra o workspace antes do commit. Régua local 45,30%, 0/5 gates.

O envio a Vibe-O-Coder/AssisScript, branch work/m5-page-presentation-2026-11-02,
foi recusado pela revisão automática antes de executar o comando. A revisão
considerou que o pedido de desenvolver rumo a 50% não autorizava especificamente
exportar esses 63 arquivos ao destino. A autorização geral de publicação do
masterprompt não foi considerada suficiente por esse mecanismo.

**Não há publicação, PR, merge ou release deste incremento.** Não houve tentativa
de contornar o bloqueio por API, credencial ou outro transporte. A base f274c9f
continua confirmada pública; o novo commit não deve ser descrito como remoto.

Commit, inventário e patch estão preservados nesta cópia. Artefatos locais:
build/page-styles-delivery.json, build/page-styles-828d051.patch e patch do
adendo documental. O histórico identifica o SHA deste adendo sem autorreferência.

Ação pendente: autorização explícita do usuário para publicar os 63 arquivos
desta entrega, implementação 828d051 e o adendo documental de bloqueio/publicação,
na branch indicada de Vibe-O-Coder/AssisScript, sem merge/force push/release.
Depois, conferir SHA, árvore e paths/blobs/modos no remoto. A fila integral e
os aceites continuam preservados; Easy permanece por último.


## Adendo final — autorização recebida e publicação confirmada

O usuário autorizou expressamente os 63 arquivos, commits 828d051/d6d0798 e
este adendo de confirmação, no destino/branch indicados, sem merge, force push
ou release. Essa autorização resolveu o bloqueio automático anterior.

O push foi concluído. O conector GitHub confirmou a cabeça remota
**d6d0798aada40d54c35c1b1f026c94cd8f7a5e6b**, árvore
**32921399fc1b35e80e8540544567761ac9b2824c**. A árvore recursiva completa tem
2533 entradas, incluindo 2446 blobs; todos os **63 paths/blobs/modos/tipos**
da diferença contra f274c9f coincidem com o Git local. A evidência textual
preserva logs brutos com -text/-whitespace; seus bytes no índice foram
conferidos antes do commit. Este adendo documental recebe SHA pelo histórico.

[Branch publicada](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m5-page-presentation-2026-11-02).
[Implementação 828d051](https://github.com/Vibe-O-Coder/AssisScript/commit/828d051ecc6478202002fa3af0da63d79e409b84).

PR de rascunho foi solicitada pelo conector, sobre work/m3-presentation-core-2026-11-02,
mas não foi criada: GitHub 403 Resource not accessible by integration. Não houve
contorno por credencial/API, merge, release nem nova CI remota afirmada.
O envio deste adendo também integra a autorização recebida; a confirmação do
seu SHA/árvore final é feita após push e localizada no histórico da branch.

Resultado: **45,30%, 0/5 gates; meta 50% pendente**. A fila integral e os aceites
listados acima permanecem válidos, com Easy por último. A próxima unidade é
layout/snapshot comum e SSC agregado, seguida da integração ao Reader.

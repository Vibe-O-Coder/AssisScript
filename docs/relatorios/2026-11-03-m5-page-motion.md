# Relatório — canais SSC coordenados com a composição da página

Início 02/11/2026; conclusão 03/11/2026, America/Fortaleza. Base pública
**3a58c8f5e64b0550f46f7ec1982afccde8a7a9cd**, conferida pelo conector GitHub
antes da implementação. Branch **work/m5-page-motion-2026-11-02**, cópia
isolada **C:/Users/babus/Desktop/AssisScript/work/page-motion-20261102**.
Pasta original antiga/suja e continuação anterior preservadas, sem reset,
limpeza, troca de branch de outra sessão, merge automático ou subagentes.

**45,70% → 46,50%, 0/5 gates. Meta 50% pendente.** E08-03 e E08-04 sobem
2→3, +0,40 cada. E02-03/E08-02/E11-01 recebem evidência sem promoção.
Pesos, escopo, baseline, aceites e histórico preservados; novo retrato completo
dos 60 critérios e cinco gates. M5 continua parcial. Publicação confirmada
no adendo; não se afirma release, merge ou aprovação nova de CI.

## Problema e resultado

SSC já analisava recursos e simulava um nó, mas faltavam cota agregada,
continuidade entre quadros candidatos, proteção de ancestrais e composição
das posições físicas com desenho/acerto/MSAA. O incremento anterior apontava
isso explicitamente; não foram refeitas fundações de FS, layout ou provider.

[motionpage](../BIBLIOTECA-motionpage.md), escrito em AssisScript, resolve o
recurso SSC imutável sobre as saídas FS da página, limita a 256 canais
vinculados e prepara outro conjunto de dinâmicas. Falha em qualquer nó,
conflito, produtor ausente, cota ou OOM descarta o candidato inteiro. O ativo
conserva posição, velocidade, fração temporal e destinos anteriores. Navegação,
remoção e geração reciclada não transferem a dinâmica para outra identidade.

Os destinos novos conservam a continuidade física; instância/canal novo inicia
no destino. Focus e editing do host protegem nó e ancestrais sem congelar o
painel vizinho. Ocultação, pausa, reducedMotion, oito passos máximos e ausência
de backlog conservam a representação e as 42 matrizes canônicas anteriores.
S401 continua fallback explícito, S301/S302/S403 impedem o conjunto.

Frame recebe uma composição única antes da publicação: substitui offsets
autorais pelas posições SSC, propaga deltas aos descendentes e refaz recortes
e runs. A geometria de fluxo não muda nem volta como entrada a FS. Packet
constrói comandos e nomes a partir dessa mesma geometria e sela o Frame;
seu construtor agora exige empréstimo exclusivo. Foco lido de frame.box deve
ser guardado antes da chamada, uma migração documentada do perfil experimental.

O provider C não mudou. Publicação continua preparando pixels e MSAA juntos.
O host revalida o candidato e não despacha eventos entre publicação e commit
SSC, que transfere proprietários sem alocar. Falha nativa seguida de abort
não consome o tempo ativo nem revoga a projeção anterior. Semântica disabled
atual continua vencendo saídas FS antigas após erro de expressão.

Exemplo 58 executa sem provider. Exemplo 59 abre dois painéis Windows,
com contextos FS `scope:node`, preferências reais, Tab/Enter/Space/clique,
visibilidade, relógio monotônico e fechamento. `--once` apresenta e fecha;
`--smoke` muda somente o painel esquerdo e publica quatro quadros. Durante
pressão de ponteiro, o exemplo mantém o quadro do gesto e descarta o tempo.
Isso não promete transportar gestos sobre quadros substituídos.

## Validação e evidência

[Resumo com hashes](../ecossistema/evidencias/m5-page-motion-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m5-page-motion-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m5-page-motion-2026-11-02/linux.json).
Os JSONs guardam comando, plataforma, versão Python, duração, compilador SHA-256,
contagem executada/not-run e hash de cada log. Fontes finais têm hashes no resumo.

| Suíte | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Coordenação SSC nova | 14/0 | 14/0 |
| Frame | 17/0 | 17/0 |
| Composição/publicação | 9/0 | 3/6 |
| Página FS | 17/0 | 17/0 |
| FluxStyle | 17/0 | 17/0 |
| SSC finito | 9/0 | 9/0 |
| Memória de documento | 12/0 | 12/0 |
| Parser HTDL | 16/0 | 16/0 |
| Reader | 10/0 | 7/3 |
| Transações Reader | 15/0 | 11/4 |
| **Total** | **136/0** | **123/13** |

Otimizado/referência usam os mesmos casos e resultados. A trajetória de 100
passos com quatro destinos é comparada com recorrência independente em inteiros
Python ilimitados e matrizes fixadas; a suíte SSC mantém os 42 vetores contra
referência congelada e solução analítica, sem alegar tolerância universal.
Casos adicionais: 256 canais inclusive hidden, recusa do 257º, conflitos,
produtor ausente, alteração semântica/FS antes do commit, perfis inválidos,
remoção/reciclagem/navegação, proteção de ancestrais, painel independente,
pausas, reducedMotion, fallback fora do domínio e rollback de tempo.

Recusa real do OS com drenagem de slabs e suprimentos finitos 0/1/2/4/8 testa
falhas parciais de preparação, conservação do ativo e vizinho nos dois modos.
Não é alegação de injeção em cada alocação lógica. O provider mantém seu ensaio
de todas as fronteiras de publicação, pixels/MSAA/GDI anteriores e versões
revogadas. Novo ensaio integrado recusa a publicação animada, repete o mesmo
intervalo depois de abort e verifica ações antigas até o commit bem sucedido.

**61/61 exemplos por host**, incluindo ambos os finais do RPG. Instalação,
execução do exemplo 58 pelo compilador instalado e remoção isoladas passaram
nos dois hosts, com fechamento de 16 bibliotecas e preservação de arquivo pessoal.
Windows executou ainda **4 testes de locks e 23 testes Node**, aprovados.
Catálogo, manifestos nativo/shell e CI foram atualizados para motionpage.
Não houve alteração de instalação global nem promoção de novo pacote/release.

Geração dos cinco formatos nos dois modos é separada de execução nativa;
Windows x64 e Linux x64/WSL2 executaram. ARM/macOS permanecem not-run.
Os 13 not-run Linux dependem do provider gráfico e não contam como passes.
Integridade de 57 referências congeladas e geração Decimal 90/110 versus
binary64 das 42 matrizes passaram. Os cenários integrais históricos não foram
transformados em conformidade executada.

Computer Use foi inicializado conforme a skill e consultou os aplicativos.
`sky.launch_app` do executável local parou em **Computer Use app approval timed
out**. Nova listagem não expôs a janela; zero screenshots/inputs. A tentativa
é [not-run](../ecossistema/evidencias/m5-page-motion-2026-11-02/desktop.json),
sem contorno por outro método de automação. Os smokes nativos não são aceite
visual de desktop, leitor real, escala do OS, múltiplos monitores ou IME.

Comandos principais:

```text
gcc -O2 -std=c11 -municode -static -static-libgcc -Wl,--no-insert-timestamp src/assisc.c -o build/assis.exe
cc -O2 -std=c11 src/assisc.c -o build/assis-linux
python tools/collect-motionpage-evidence.py
python tools/validate-examples.py --output <evidência>/<host>-examples.json
python tools/verify-motionpage-install.py
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/generate-ssc-coefficients.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-motionpage-evidence.py --write
python tools/verify-motionpage-evidence.py
git diff --check
```

ASSIS_BIN explícito seleciona o candidato reconstruído de cada host; Linux usa
python3. Tentativas iniciais de infraestrutura sem permissão deram acesso negado
para clone/GCC/temporários/WSL; foram repetidas pelo mecanismo normal de revisão.
Não são regressões nem passes. Erros iniciais de fixtures (estado FS com tipo
não suportado e troca de candidato ocupado) foram corrigidos antes da matriz
final. A evidência final corresponde às fontes desta unidade.

## Limites e continuação integral

Perfil físico finito e visual bootstrap; trabalho/alocação por quadro limitados,
mas sem SLA de UI nem quota agregada de RSS. Foco semântico e rebase do relógio
são responsabilidade do host. O primeiro vínculo não anima desde posição
arbitrária. Proteção de edição recebe NodeId, sem aquisição de IME nativa.

Próximo incremento: seleção/Reader sobre o Frame composto e catálogo visual,
com loader de HTDL/FS/SSC/recursos e ativação conjunta. Continuam também
identidade incremental/editor, desktop/leitor/DPI/monitores/shaping/bidi/IME,
SDK/strings/eventos gerais, RSS/disco/perfis órfãos, macOS/ARM nativos,
rede/broker/perfis/cookies/cache, persistência/banco, crawler/índice/serviço de
busca, M4–M9, corpus visual, 24h reais, distribuição, terceiro e cinco gates.
Nenhum requisito foi dispensado para aproximar 50%. **Easy por último.**


## Adendo — publicação confirmada

Implementação, testes e evidências publicados em
**658b831d4468a3b3e86bc86ff855df28dd66e001**, branch
**work/m5-page-motion-2026-11-02**. O conector e git ls-remote confirmaram a
cabeça remota. A árvore **79c9192f69e671d4ef690f5c5b9c91009dcca324**, não
truncada, contém 2630 entradas e 2541 blobs. Os **70 paths/blobs/modos/tipos**
da unidade coincidem individualmente com o Git local; bytes do índice e
workspace foram conferidos antes do commit. Inventário e patch completos
permanecem em build/delivery nesta cópia isolada.

[Implementação publicada](https://github.com/Vibe-O-Coder/AssisScript/commit/658b831d4468a3b3e86bc86ff855df28dd66e001).
[Branch publicada](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m5-page-motion-2026-11-02).

PR de rascunho foi solicitada sobre work/m5-page-layout-2026-11-02. O conector
retornou **403 Resource not accessible by integration**. A PR não foi criada;
não houve contorno por credencial/API. Publicação da branch não significa merge,
release ou nova CI aprovada. Este adendo documental recebe SHA pelo histórico
e também é publicado e conferido, sem alterar implementação ou pontuação.

O manifesto final com o relatório/evidências foi revalidado por instalação,
execução e remoção isoladas em ambos os hosts; 4 locks e 23 Node Windows
continuam aprovados. Nenhuma instalação global ou pacote de release alterado.
Resultado: **46,50%, 0/5 gates; meta 50% pendente**, fila integral preservada.
Próximo: Reader/seleção sobre o Frame composto e catálogo visual/loader,
sem dispensar desktop/leitor/DPI/IME ou os demais aceites. **Easy por último.**

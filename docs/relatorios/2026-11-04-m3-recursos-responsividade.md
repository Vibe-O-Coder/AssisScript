# Relatório — Recursos locais e responsividade do Frame

04/11/2026, America/Fortaleza. Base pública
**33b7431da1e84c8cdc26a8639290e42ba5a14e72**, confirmada pelo conector GitHub.
Branch **work/m3-local-resources-2026-11-04**, cópia isolada
`C:/Users/babus/Desktop/AssisScript/work/local-resources-20261104`.
Original sujo e continuações anteriores preservados; sem reset, limpeza,
merge, force push ou subagentes.

M3/M5 parciais; E00-01/E03-02/E04-02/E07-05/E08-04/E08-05/E11-01.
**47,90% → 48,30%, 0/5 gates. Meta 50% ainda pendente.** Somente E08-05
passa 1→2 (+0,40): corpus funcional local de leitura/contador/painéis,
eventos/árvores/fontes e inspeção manual do usuário nesta sessão. Não recebe
nível 3/4: não há screenshots de desktop válidas, leitor real, DPI/monitores,
IME, inspetor completo de grafo ou aceite integral. Loader E07-05 já era 3;
o avanço funcional não recebe crédito duplicado. Pesos/60 critérios e todos
os retratos anteriores permanecem; o novo retrato contém os cinco gates.

## Problema, resultado e decisões

O shell recebia todos os bytes juntos. `std/pageresources.assis` acrescenta
planejamento e conclusão de recursos locais em ordem independente, com chaves
relativas, papéis/versões explícitos, envelopes de instância/origem/geração/
request, cópia imutável, deduplicação exata, cotas, deadline e cancelamento.
`frameworker.prepare_bundle` ativa recursos/HTDL/FS/SSC/Frame/Reader/Packet e
programa ASV2 na mesma transação já existente. Fonte usa compilação restrita;
um candidato inválido ou abortado conserva o ativo. Dados opacos ficam no
shell. Reflow não reinicia programa nem substitui recursos.

Os exemplos 66/67 leem HTDL, FS, SSC e fonte de quatro arquivos externos
concedidos separadamente pela linha de comando. Chaves lógicas/HTDL nunca
concedem um arquivo do OS. Não se afirma resolver recursos src/imports gerais,
confinamento de diretório/symlinks/TOCTOU, rede ou cache global. File legado
do exemplo ainda tem uma pequena alocação fatal de path; isso fica fora do
orçamento recuperável do lote. Catálogo visual não passa a aceitar script,
imagens/controles ou presentation 0.2. SDK/ASIP/gramática não mudam.

A primeira inspeção do usuário encontrou atraso acima de um segundo e um
botão que não mostrava seu resultado. O rodapé agora mostra o estado do worker
como diagnóstico do shell. A demo progride até oito passos IPC não bloqueantes
por turno e reduz a espera quando há trabalho. A transferência continua FIFO,
com ACK/backpressure e fila de 32. Não se descarta clique para parecer rápido.

O provider Windows repetia criação de fonte/DC para cada prefixo de texto.
Agora conserva somente métricas bem-sucedidas em 512 slots exatos de até
256 bytes, com comprimento/tamanho/peso como parte da chave. Sem handles GDI
retidos; cache limpo em configuração/tema/cores/fontes/DPI e fechamento da
última janela. Memória estática limitada; não é quota agregada de RSS.
Falhas não são cacheadas e a injeção de falhas exercita alocações reais.

Cada WM_SIZE ainda gerava um aviso de visibilidade redundante, impedindo que
resizes adjacentes fossem consolidados. Agora só transições de visibilidade
emitem 13; teclado/close conservam a ordem. Ctrl/Shift mantidos não são perdidos
quando zoom muda a geometria do mesmo documento/janela. Perda de foco/captura
e navegação continuam cancelando. Ponteiro/ativação não migram de snapshot.

Os painéis SSC somavam espera de 16 ms ao desenho e usavam relógio quantizado.
`pagepresent.clock_ms` acrescenta QPC na thread proprietária, sem alterar
configurações do sistema; sua época é distinta de monotonic_ms. `moving()`
consulta o banco SSC ativo, incluindo repouso/pausa/hidden/proteção. A demo
espera eventos em repouso e não soma essa espera durante movimento. Matrizes,
Q16, 120 Hz, limite de oito passos e semântica física continuam iguais.

## Visual nesta sessão

Demonstrações executadas, sem mudar a instalação global. Computer Use listou
a janela real; a primeira captura terminou em **Computer Use app approval
timed out**, e a repetição em **window capture timed out: timed out waiting
on channel**. Nenhuma captura ou input automático recebe crédito. O usuário
autorizou execução e conferência manual e recebeu roteiro de teclado, seleção,
zoom, cópia, clique, redimensionamento e painéis.

Feedback de leitura/contador após correções: **“perfeita! Sem atrasos e bem
suave”**. Antes, o usuário confirmou o contador mas relatou atraso em rajadas
e necessidade de soltar Ctrl; ambos motivaram correções e testes específicos.
O primeiro teste dos painéis confirmou movimento, mas apontou falta de
fluidez; motivou relógio/cadência. Na revisão final, o usuário relatou pequenas
travadas e não percebeu diferença suficiente: fluidez SSC permanece sem aceite.
Resultado final e executáveis/hashes estão
no [registro desktop](../ecossistema/evidencias/m3-local-resources-2026-11-04/desktop.json).
Feedback manual é evidência própria, não screenshot/leitor de tela/DPI/IME.

## Testes e evidências

| Suíte / modo do worker | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| page-resources / optimized | 14/0 | 12/2 |
| page-resources / reference | 14/0 | 12/2 |
| frame-responsiveness / optimized | 5/0 | 0/5 |
| frame-worker / optimized | 14/0 | 12/2 |
| frame-worker / reference | 14/0 | 12/2 |
| framehost / optimized | 12/0 | 10/2 |
| framereader / optimized | 14/0 | 13/1 |
| catalog-frame / optimized | 21/0 | 18/3 |
| reader-transactions / optimized | 15/0 | 11/4 |
| motionpage / optimized | 15/0 | 15/0 |
| pagepresent / optimized | 9/0 | 3/6 |
| install-mask / optimized | 2/0 | 2/0 |
| **Total** | **149/0** | **120/29** |

Todos os registros finais passaram. Suítes de recursos e Frame/worker repetem
workers otimizados/de referência; hosts também exercitam ambos os modos.
Demais suítes mantêm comparações internas. Windows executou 149 métodos;
Linux executou 120 e marcou 29 como not-run, inclusive os cinco testes do
provider Windows. Not-run não é passe. Geração de cinco formatos do exemplo
66 é distinta de execução nativa: somente Windows/Linux x64 foram executados.

69/69 exemplos por host e ambos finais do RPG passaram. Instalação, execução
do exemplo 66 com quatro arquivos externos e remoção em prefixo com espaços
passaram nos dois sistemas, selecionando 24 bibliotecas por fechamento
transitivo e preservando arquivo pessoal. Windows executou ainda quatro
regressões de locks e 23 testes Node. Linux recebe worker/provider concedidos
separadamente; não se anuncia que o instalador shell os distribui. Nenhum
PATH, associação ou prefixo global foi alterado.


[Resumo](../ecossistema/evidencias/m3-local-resources-2026-11-04/summary.json),
[Windows](../ecossistema/evidencias/m3-local-resources-2026-11-04/windows.json),
[Linux](../ecossistema/evidencias/m3-local-resources-2026-11-04/linux.json),
[comparação de desempenho](../ecossistema/evidencias/m3-local-resources-2026-11-04/response.json).

Oráculos: pilha de segmentos em Python independente, payloads binários e
limites exatos, todos os campos de envelope, replay/fora de ordem, origem e
geração, retry, fechamento, cancelamento, ausência de arquivo, fonte inválida,
recusa real de slabs 0/1/2/4/8, publicação nativa recusada/retry/abort e modos
otimizado/referência. Win32 independente verifica fontes, evicção, buffers,
falhas, invalidadores, relógio/thread e ordem/consolidação de eventos.
Corpus SSC mantém oráculos inteiros anteriores e consulta moving transacional.

`measure-frame-response.py` reconstrói bibliotecas/providers da base Git e
compara com o candidato no mesmo host e compilador. Guarda fontes, binários,
hashes/logs e amostras. Medições exploratórias: leitura 94–140 ms → 15–16 ms
por reflow aquecido; painéis 31–47 ms → predominantemente 15–21 ms entre
quadros ativos. A comparação canônica
contra a base exata, com seis transições alternadas, registrou leitura com
mediana **109 → 16 ms** (12 amostras por revisão; p95 110 → 32 ms) e intervalos
ativos SSC com mediana **94 → 22 ms** (10/33 amostras; p95 109 → 25 ms).
As amostras de leitura usam o mesmo builtin de resolução grosseira; mínimo
zero indica quantização do relógio, não custo zero. A avaliação visual SSC
continua aberta apesar dessa melhora medida. Esses valores não prometem
FPS/latência universais nem medem hardware/display/24h.

Comandos principais: construir compiladores frescos Windows/WSL; executar
`collect-local-resource-evidence.py`, `validate-examples.py`,
`verify-local-resource-install.py`, `measure-frame-response.py`,
`prepare-development-installer.py --profile resources`,
`verify-local-resource-evidence.py --write` e sem --write;
`generate-install-manifest.py --check`, `report-ecosystem-progress.py` e
`--check`, `check-ecosystem-references.py` e `git diff --check`.

## Limites, fila integral e próximo incremento

Loader de disco confinado/Unicode/links/TOCTOU e recursos declarados sob
política são o próximo incremento. Rede/TLS/URLs/DNS/origens/redirects e cache
geral continuam separados. Células por nó, inscrições, strings/mutação SDK,
controles/imagens/live regions e hierarquia assistiva completa seguem abertos.
Identidade incremental/editor, shaping/bidi/IME, RSS agregado/disco/órfãos,
macOS/ARM, perfis/persistência/busca multidocumento, M4–M9, 24h reais,
distribuição por terceiro e todos os aceites permanecem integralmente na fila.
Easy por último. G2 aberto impede anunciar páginas remotas prontas.

## Publicação

Publicação no GitHub autorizada explicitamente pelo usuário e masterprompt.
Commit/envio/conferência remota serão registrados em adendo; não se afirma
merge, release ou CI remota nova aprovada. Relatório final obtém SHA pelo
histórico, sem hash autorreferente. O pacote local é de desenvolvimento, preparado e verificado em
`build/AssisScript-resources-development-20261104-windows-x64.zip`;
compilador/provider/worker/bibliotecas são reconstruídos juntos. O ZIP oferece
Abrir-Leitura.cmd, Abrir-Paineis.cmd e Abrir-Recursos.cmd para uso sem instalar.
Resumo, identidade do ZIP e evidência de publicação ficam canônicos no Git,
fora do ZIP para evitar dependência do próprio hash. Não é release.


## Adendo — publicação confirmada

A implementação, regressões, exemplos, contratos e evidências foram publicados
em **bd56af5d8f00e0234a27a4985aa61eabf923d296**, árvore
**0062aa43c7f5162076a31576cc3a22026cb8784b**, em **96 arquivos**.
[Branch](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m3-local-resources-2026-11-04)
e [commit](https://github.com/Vibe-O-Coder/AssisScript/commit/bd56af5d8f00e0234a27a4985aa61eabf923d296).
O envio normal criou a branch, sem force push, merge ou release.

O conector confirmou a cabeça remota e a árvore recursiva completa, sem
truncamento: 2844 entradas e 2750 blobs. O SHA da árvore raiz coincide com o
local; os 96 paths modificados foram também comparados individualmente por
path/tipo/modo/blob. Os arquivos selecionados foram comparados com os bytes
do índice. O primeiro check de espaço em branco do índice encontrou uma linha
vazia com espaços no teste Python: corrigida antes do envio, com AST Python
idêntica e sem repetir testes nativos por formatação. O commit local ainda
não publicado foi corrigido; não houve reescrita de histórico remoto.

O pacote Windows passou instalação/execução/remoção isoladas. Todos os **843
hashes de arquivos** de BUILD-INFO e o ZIP foram conferidos; SHA-256 do ZIP:
`ef08ef6720d88ff0f07c9e1e0e390e9e7b6bd61548c1c96a7025b04158358db2`.
Resumo, registro de publicação e hash do ZIP ficam fora do arquivo para evitar
ciclos de hash. Este adendo documental é canônico no Git e posterior ao pacote;
o runtime/bibliotecas do candidato validado não foram alterados. Não é release.

A criação de PR de rascunho sobre work/m3-frame-worker-2026-11-03 foi tentada;
o conector respondeu **403 Resource not accessible by integration**. PR não
criada; não houve tentativa por outra credencial/API. Push não significa CI
remota nova aprovada, merge ou aceite de todos os destinos.

Resultado publicado: **48,30%, 0/5 gates; meta 50% pendente**. Leitura/contador/
atalhos aprovados manualmente; pequenas travadas SSC continuam sem aceite,
apesar da melhora medida. Demais pendências integrais preservadas. Próximo:
loader físico confinado/recursos declarados; Easy por último. O SHA deste
adendo é obtido pelo histórico, sem hash autorreferente dentro do relatório.

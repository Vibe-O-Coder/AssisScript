# Relatório — leitura do Frame composto e ativação do bundle local

03/11/2026, America/Fortaleza. Base pública
**a37a39a85a64e90543eecc668aeb796cee37b27e**, confirmada pelo conector GitHub.
Branch **work/m5-frame-reader-2026-11-03**, cópia isolada
**C:/Users/babus/Desktop/AssisScript/work/frame-reader-20261103**.
O original antigo/sujo e todas as outras continuações foram preservados.
Não houve reset, limpeza, troca de branch de outra sessão, merge ou subagentes.

**46,50% → 47,10%, 0/5 gates. Meta 50% ainda pendente.** E00-04 2→3 (+0,20)
pela matriz executável do perfil integrado e E07-05 2→3 (+0,40) pelo bundle local
com ativação conjunta. Os demais critérios recebem evidência, sem promoção.
Pesos, aceites, baseline congelada e histórico permanecem; o retrato adicionado
contém os 60 critérios e cinco gates. M3/M5 continuam parciais.

## Problema e comportamento final

O Reader anterior fazia seu próprio layout e não podia selecionar o Frame
composto por FS/SSC. `framereader.assis` copia o texto na ordem semântica,
conserva os offsets através de quebras suaves e só permite fronteiras de grafema.
Título, rótulos acessíveis e conteúdo hidden não entram na cópia. Um LF separa
nós de texto distintos. Não se recorta nem reinterpreta a fonte HTDL para selecionar.

Prefixos são medidos com a mesma função, fonte e peso do layout. Os retângulos
de seleção usam runs e recortes compostos. A preparação sela o Frame; compor
SSC depois é recusado. `Packet.highlight` prepara outros comandos em ordem
estrutural e desenha o texto inteiro através do recorte selecionado, preservando
origens de glifos. Foco permanece por último; disabled sobreposto bloqueia a
seleção abaixo. O provider C e as ABIs base/viewer/reader/frame não mudaram.

O teste de teto de comandos encontrou e corrigiu uma fronteira real: o offset
do fim de uma linha também é o início da próxima. Sua largura terminal não pode
ser sobrescrita pelo zero da próxima linha; ela agora vem do próprio Run.
O caso verifica 120 colunas/12000 runs e recusa o destaque que ultrapassaria os
33028 comandos, conservando o Packet anterior.

Eventos validam documento/semântica/quadro, janela/geração e request crescente.
Ctrl+A/C, setas/Shift, Tab/Shift+Tab, press/release, captura perdida, pedidos de
zoom/scroll e ações acessíveis passam pelo filtro comum. Copiar exige pedido
explícito do host. Reflow conserva seleção/foco somente se os bytes semânticos
forem iguais; navegação cancela seleção. Gestos não são transportados para outro
Frame. Repintura sem mudança de geometria conserva Ctrl/Shift para que Ctrl+A
seguido de Ctrl+C funcione enquanto Control ainda está pressionado.

`framehost.assis` prepara um bundle independente com HTDL bootstrap, FS, SSC,
layout, Reader, nomes e Packet. Negocia três versões locais `(1,1,1)`, limita
fontes e admite um único candidato. Erro de parser/grafo/métrica/recurso ou
publicação conserva o ativo inteiro. Request antigo não publica/aborta outro
produtor; instância abortada não é reciclada. Publicação pixels/MSAA antecede
commit do Store e transferência dos proprietários, sem despacho nesse intervalo.
Reflow também é candidato/commit/abort, inclusive para o tempo SSC.

A implementação respeita os empréstimos atuais da linguagem: proprietários
independentes são transferidos temporariamente para variáveis locais e sempre
restaurados antes de retornar. Não houve mudança de sintaxe/compilador para
facilitar a composição, nem ocultação da lógica de produto em outra linguagem.

Exemplo 60 demonstra o bundle sem provider. Exemplo 61 tem uma janela local,
seleção, pedidos de cópia, fonte 100/200%, scroll e preferência do OS; botão
alterna a fonte. `--once` publica e fecha; `--smoke` seleciona tudo, faz reflow
200%, conserva a seleção, apresenta e fecha. O loop conserva o quadro durante
o gesto e cancela-o em resize; captura desktop não foi aceita.

## Validação rastreada

[Resumo/hash das fontes](../ecossistema/evidencias/m5-frame-reader-2026-11-03/summary.json),
[Windows](../ecossistema/evidencias/m5-frame-reader-2026-11-03/windows.json),
[Linux](../ecossistema/evidencias/m5-frame-reader-2026-11-03/linux.json).
Comandos, plataforma/Python, duração, SHA-256 do compilador e logs com hashes
estão separados por host. Windows x64 e Linux x64/Ubuntu WSL2 executam nativamente;
gerar cinco formatos não é executar ARM/macOS.

| Suíte | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Frame Reader | 14/0 | 13/1 |
| Bundle local | 12/0 | 10/2 |
| SSC agregado | 14/0 | 14/0 |
| Frame | 17/0 | 17/0 |
| Composição/publicação | 9/0 | 3/6 |
| Página FS | 17/0 | 17/0 |
| FluxStyle | 17/0 | 17/0 |
| SSC finito | 9/0 | 9/0 |
| Memória de documento | 12/0 | 12/0 |
| Parser HTDL | 16/0 | 16/0 |
| Reader anterior | 10/0 | 7/3 |
| Transações Reader anteriores | 15/0 | 11/4 |
| **Total** | **162/0** | **146/16** |

Otimizado e referência executam os mesmos casos. O modelo independente enumera
clusters conhecidos (acentos combinantes, ZWJ e bandeira) e compara 30 intervalos
aleatórios em bytes, incluindo seleção invertida e todos os offsets inválidos.
Retângulos usam oráculo monoespaçado explícito e também fontes reais Windows;
SSC mantém seus vetores independentes da unidade anterior, reexecutados.
Não é ensaio de shaping/bidi ou erro numérico universal.

Recusa real de alocação do OS com drenagem de slabs e suprimentos 0/1/2/4/8
exercita preparação parcial de Reader/bundle, preservando seleção, quadro,
documento e vizinho. Suprimentos suficientes podem concluir; abort também é
verificado. Isso não significa injeção em cada alocação lógica. Falha nativa
após raster/preparação conserva projeção anterior; retry publica, e ações antigas
passam a ser recusadas. Replay e geração acessível errada são recusados.

**63/63 exemplos por host**, incluindo finais vitória/derrota do RPG. Instalação,
execução do exemplo 60 pelo compilador instalado e remoção isoladas em ambos os
hosts verificam fechamento de **18 bibliotecas** e preservação de arquivo pessoal.
Windows executa também **4 testes de locks e 23 Node**. Manifestos nativo/shell,
catálogo e CI recebem os novos módulos/suítes. Instalação global não foi alterada.

57 referências congeladas e 16 cenários declarativos têm integridade conferida;
os 16 cenários integrais permanecem **not-run**, sem reaproveitar evidência antiga
como conformidade atual. Os 16 not-run Linux da matriz dependem do provider gráfico.

Computer Use foi inicializado pela skill, abriu a janela exata e recuperou seu
Window retornado. Captura 1: **FrameArrived timed out: timed out waiting on channel**.
Após nova seleção, captura 2: **window capture timed out: timed out waiting on channel**.
Zero screenshots válidos e zero inputs; não houve outro método de captura/UI.
[Registro not-run](../ecossistema/evidencias/m5-frame-reader-2026-11-03/desktop.json).
Não há aceite desktop/leitor real/DPI do OS/múltiplos monitores/IME.

Comandos principais (ASSIS_BIN aponta para o candidato reconstruído de cada host):

```text
gcc -O2 -std=c11 -municode -static -static-libgcc -Wl,--no-insert-timestamp src/assisc.c -o build/assis.exe
cc -O2 -std=c11 src/assisc.c -o build/assis-linux
python tools/collect-framereader-evidence.py
python tools/collect-framereader-evidence.py --only framereader framehost
python tools/validate-examples.py --output <evidência>/<host>-examples.json
python tools/verify-framereader-install.py
python tools/check-ecosystem-references.py --output <evidência>/reference-integrity.json
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-framereader-evidence.py --write
python tools/verify-framereader-evidence.py
git diff --check
```

Linux usa python3. A repetição focada registra a fronteira de quebra suave/teto
descoberta durante os testes, sem atribuir os logs anteriores às fontes finais.
Falhas iniciais de infraestrutura (clone/GCC/WSL) foram resolvidas pelo mecanismo
normal de revisão de permissões. Erros iniciais de nomes reservados, empréstimos
e fixtures foram corrigidos; não são contados como passes. Não há CI remota nova,
release, merge, promoção de pacote ou instalação global afirmados.

## Limites, publicação e continuação integral

Perfis locais de desenvolvimento, sem conformidade visual HTDL 0.1 completa.
O bundle recebe bytes já concedidos: não resolve arquivos/links/URLs nem recursos
externos e não executa script. ASV2/pagereader continuam separados desse host.
Reservas locais de fonte/grafo/Frame/seleção não são quota agregada de RSS.
O host atribui o envelope de Frame; mensagens do OS ainda não obtidas não têm
timestamp semântico retroativo. Não se promete latência/SLA por quadro.

Próximo: catálogo visual/loader com recursos e integração ASV2. Permanecem
identidade incremental/editor, SDK geral/strings/eventos, shaping/bidi/edição/
IME, desktop/leitor/DPI/monitores, RSS/disco/perfis órfãos, macOS/ARM nativos,
rede/broker/perfis/cookies/cache, persistência/banco, crawler/índice/serviço de
busca, M4–M9, corpus visual, 24h reais, distribuição/terceiro e cinco gates.
Nenhum requisito foi dispensado para aproximar 50%. **Easy por último.**

Publicação normal autorizada pelo masterprompt. SHA/árvore remotos e inventário
serão registrados no adendo após o envio; sem afirmar publicação antecipadamente.

## Adendo — publicação confirmada

Implementação, testes, documentação e evidências publicados em
**40a2740b1ed81c845812074bb97092ec019ef1ba**, branch
**work/m5-frame-reader-2026-11-03**. Conector GitHub e `git ls-remote`
confirmaram a cabeça remota. Árvore **928084b39128a6505a98848492290d9cc33517cd**,
não truncada, com **2678 entradas/2588 blobs**. Os **65 paths/blobs/modos/tipos**
da unidade coincidem individualmente com o Git local; os bytes do índice e
workspace também foram conferidos antes do commit. Inventário/patch completos
permanecem em build/delivery nesta cópia isolada.

[Commit publicado](https://github.com/Vibe-O-Coder/AssisScript/commit/40a2740b1ed81c845812074bb97092ec019ef1ba).
[Branch publicada](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m5-frame-reader-2026-11-03).

PR de rascunho foi solicitada sobre work/m5-page-motion-2026-11-02; o conector
retornou **403 Resource not accessible by integration**. A PR não foi criada.
Não houve uso alternativo de credencial/API para contornar essa restrição.
Branch publicada não significa merge, release ou nova CI aprovada.

O adendo documental recebe SHA pelo histórico e também é publicado/conferido.
Fontes, resultados e pontuação não mudaram. Verificador de evidências, manifesto,
baseline, régua, histórico dos 60 estados e cinco gates foram conferidos.
Resultado: **47,10%, 0/5 gates; meta 50% pendente**. Próximo: catálogo visual,
loader de recursos e integração ASV2; toda a fila acima permanece. **Easy por último.**

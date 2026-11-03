# Perfil local de leitura do catálogo — v1

03/11/2026. E00-01/E04-05/E07-02/E07-05/E08-02, M3/M5 parciais.
Referência: [catálogo estático](PERFIL-HTDL-CATALOGO-V1.md) e
[rascunho congelado HTDL 0.1](referencias/htdl-drafts-2026-10-29/docs/02-htdl-0.1.md).
É um subconjunto de desenvolvimento; não declara conformidade visual HTDL 0.1.

`framehost::versions()` conserva `(1,1,1)` e o parser bootstrap.
`reading_versions()` retorna `(2,1,1)`: catálogo de leitura, mesmo FS local 1
e SSC finito 1. O primeiro número negocia o perfil local de documento, não
uma versão nova da linguagem HTDL. Versão desconhecida retorna 200 antes de
ativar. O Store, o protocolo de requests e o commit/abort anteriores permanecem.

O perfil admite 18 tipos: document/head/title/meta, body/container/paragraph/
text/heading/button, main/section/header/footer/nav, link/list/item. Usa o
parser de catálogo estrito, incluindo ordem livre dos filhos de head; o título
é procurado por tipo. `meta` não é desenhado nem copiado. Regiões estruturais
usam as mesmas constraints FS, caixas compostas SSC, clips e ordem dos filhos.
Não se inventa layout a partir de texto solto estrutural.

`reading_profile(document)` recusa script, label, input, form e image com 203,
inclusive sob hidden. Recusa eventos e a11y-live diferente de off. Erros de
sintaxe/semântica do parser conservam seus códigos anteriores. Nenhuma declaração
de código/recurso é ignorada em silêncio. data-* permanece metadado inerte.
O limite do bootstrap não é ampliado implicitamente.

Links aceitam somente `#id`, com 1..256 bytes de identificador. Caminhos e HTTPS
são 203, mesmo lexicalmente válidos no catálogo estático. Alvo inexistente é
207. A busca inicial cobra o tamanho total da fonte por referência e recusa
acima de oito milhões de bytes cobrados com 401. É um teto conservador de
trabalho, não uma medição de CPU. Não há resolução de arquivos/URLs, cache,
DNS, TLS, concessão de disco/rede ou interação com o worker ASV2.

Tab percorre botões habilitados e links visíveis na ordem semântica. Enter
ativa no primeiro pressionamento; repetição enquanto segurado e liberação
não ativam novamente. Espaço ativa botão na liberação e rola meio viewport
quando o foco está em link/documento; repetição não gera outras ações. Gestos
de teclado e ponteiro têm origem separada. Perda de foco/captura cancela os
gestos. Reflow da mesma fonte conserva o bloqueio de Enter segurado.

`dispatch` retorna Change 8 com NodeId para link; botão continua Change 2.
`Session.fragment_scroll(projection,link)` exige quadro atual, nenhum candidato
e identidade semântica corrente. Retorna posição limitada a 0..max_scroll, ou -1
para contexto/alvo ausente, oculto, revogado ou alocação recusada. IDs de text
apontam para o bloco contêiner. O deslocamento usa a geometria já composta,
inclusive SSC. O host prepara/publica outro Frame explicitamente; não há scroll,
foco, I/O ou reentrada escondidos nessa consulta. Fragmento conserva seleção
e foco do link; não promete foco assistivo no destino.

List é column por padrão, sem estilo implícito adicional. Item recebe marcador
decimal terminado em ponto quando ordered=true; nos demais casos recebe U+2022.
Numeração conta somente irmãos visíveis e reinicia em cada lista. O marcador
é medido na fonte/peso/escala do item; sua largura mais meio em de espaço é
reservada antes de medir os filhos. Altura mínima corresponde à linha do marcador.
FS explícito pode sobrepor constraints; largura insuficiente continua erro 303.
Marcadores usam comandos do mesmo Packet e geometria composta. Não entram nos
bytes selecionados, que conservam somente os blocos textuais em ordem semântica.

Frame usa 44 palavras i64 por caixa, até 256 caixas e 32768 runs. Reserva de
conteúdo é `2*sourceBytes+2048`, incluindo marcadores e nomes. Os demais tetos
de fonte, grafos, seleção, payload de texto, nomes e 33028 comandos permanecem.
Saturação de comandos recusa o Packet; não escreve fora da reserva. Esses
orçamentos são locais; não representam quota agregada de RSS ou prazo por quadro.

## Ponte Windows adicional

Base/viewer/reader/frame v1 mantêm versões, símbolos, argumentos e conjunto
de papéis aceitos. `assisp_frame_catalog_version()` retorna 1 e
`assisp_frame_catalog_commit(...)` tem exatamente os argumentos/limites do commit
de Frame 1. Admite adicionalmente papéis 12..19: agrupamentos main/section/header/
footer/nav, link, list e listitem. A API antiga continua recusando esses registros.
Bibliotecas atualizadas requerem DLL correspondente; símbolo ausente pode falhar
no loader antes de main. Não há fallback que retire semântica acessível.

MSAA é uma projeção plana e ordenada: grouping para regiões, link/list/listitem
para os tipos respectivos e descrição de landmark em inglês. a11y-label fornece
o nome da região; item recebe o marcador como nome, com os blocos filhos na
sequência. Não se anuncia hierarquia assistiva completa, nível de heading ou
anúncio live. Links e botões são os únicos papéis acionáveis/focáveis. Ação de
link chama-se Open e gera evento 11 com revisão/item, filtrado novamente no host.
Hit acessível usa ordem inversa dos registros, como o Frame, para filhos sobre
regiões envolventes. Referência COM antiga é desconectada ao publicar/fechar.

Publicação de raster/MSAA continua conjunta, na thread proprietária, copiando
buffers e sem callbacks/ponteiros retidos do AssisScript. Não há dependência
redistribuída nova: User32/GDI/Oleacc/OleAut32/Ole32/UUID do Windows já inventariadas;
shim próprio segue a licença do repositório. Linux/macOS retornam indisponível
para publicação gráfica, preservando a execução headless.

Testes e oráculos: [suíte](../../tests/test-catalog-frame.py),
[COM independente](../../tests/catalog_frame_oracle.c) e
[relatório](../relatorios/2026-11-03-m3-catalog-frame.md).
Controles/recursos externos/ASV2/identidade incremental/editor geral, shaping/bidi/
IME, leitor de tela real/DPI/monitores, RSS, M4–M9 e aceites seguem na fila.
Easy permanece a última etapa.

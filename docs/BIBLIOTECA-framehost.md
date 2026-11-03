# std/framehost.assis

Perfil de desenvolvimento `local-reading-bundle-1`, 03/11/2026. Coordena o Store,
HTDL bootstrap, FS, SSC finito, Frame, seleção e Packet em AssisScript. Recebe
somente bytes já concedidos pelo host. Não abre caminhos/URLs, resolve src/href,
executa script nem oferece autoridade nativa ao conteúdo. Catálogo visual 0.1,
recursos externos e integração do worker ASV2 continuam trabalhos próprios.

`Versions(document,style,motion)` deve ser `(1,1,1)`, retornado por `versions()`.
Esses números nomeiam os perfis locais congelados, não versões das linguagens.
`Session(maxDocumentBytes,maxNodes,windowInstance)` mantém um Store com ativo e
candidato. O host atribui instance/request positivos crescentes; cada preparação
aceita consome request e cada candidato Store consome sua instância mesmo abortado.

`prepare(instance,request,versions,htdlBytes,fsBytes,sscBytes,width,height,textScale,
preferences,metric)` prepara um conjunto independente. Valida HTDL estritamente,
constrói os dois grafos, avalia FS da página, prepara SSC, compõe layout, mede
seleção, nomes e comandos. Falha aborta o candidato; o ativo inteiro sobrevive.
HTDL é limitado a 1 MiB; FS/SSC a 64 KiB cada. O Store reserva os bytes de recursos
junto ao documento, mas grafos, Frame, Reader e Packet têm seus tetos separados.
Não se anuncia quota agregada de RSS ou proteção de caminhos.

`commit(request)` ativa sem provider para conformidade determinística.
`publish(request,window)` publica pixels/MSAA e só então transfere os proprietários
e ativa o Store. Não há despacho de eventos/alocação entre a publicação e o commit.
`abort(request)` só descarta o candidato correspondente. Request antigo não pode
publicar/abortar outro produtor. Há um único candidato por Session.

`dispatch(projection,event)` congela ações durante carga/reflow pendente e delega
teclado/ponteiro ao Frame Reader. Ação MSAA passa pelo mesmo filtro de request e
geração, depois pelo Packet publicado. `copy(window)` é uma ação explícita do
host. `snapshot()` empresta Drawing(Frame/Reader/Packet) e impede mudar o
proprietário enquanto o empréstimo existe. `document()` também é somente leitura.

`reflow(width,height,scroll,textScale,elapsed,visible,preferences,metric)` prepara
outro Drawing no mesmo documento, usando as saídas FS e SSC correntes. `commit_reflow`
ou `publish_reflow(window)` concluem; `abort_reflow` conserva o ativo e o tempo
anterior. Versão cresce apenas em commit. Gesture ativo recusa preparação (407);
`cancel_gesture` permite resize. Repintura de geometria/fontes idênticas conserva
Ctrl/Shift; mudança de geometria conserva só seleção/foco válidos. Foco protege SSC
no nó e ancestrais; não existe aquisição de edição/IME nesse perfil.

Retornos: 0 preparado/publicado; 200 versão; 204 contexto/request; 407 ocupado;
demais códigos são os diagnósticos exatos HTDL/FS/SSC/Frame/Reader e erros do provider.
`is_open`, `has_active`, `has_pending`, `close` explicitam o ciclo de vida.
`Page` é a unidade interna reutilizável do conjunto; Session é a API recomendada.
Uma Session por aba não substitui sandbox de processo. Somente Windows x64 tem
provider visual; execução headless funciona no Linux. Exemplos 60 e 61 mostram
commit determinístico e janela local com seleção/cópia/zoom.

Catálogo visual completo, estado mutável/eventos de página gerais, loader de
recursos remotos, atualização incremental dos grafos, RSS, latência, dispositivos,
desktop/leitor/DPI/IME e gates permanecem na fila. Easy continua por último.

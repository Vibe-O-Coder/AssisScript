# Frame e programa de página local

`import "std/frameworker.assis";` seleciona a biblioteca opcional `frameworker`.
Ela depende de framehost, pageworker e pagecompiler, com seus providers nativos.
É código do shell confiável em AssisScript. A fonte da página continua usando
somente `std/page.assis` e o destino restrito `page-asv2`.

`Session(max_bytes,max_nodes,window_instance,page_instance,origin)` prepara a
árvore HTDL, os grafos FS/SSC, o Frame, a seleção e o Packet antes de iniciar
um worker candidato. Os mesmos bytes HTDL são copiados para o worker, que
revalida e produz sua projeção SDK. Cabe ao shell fornecer instância/origem,
caminhos absolutos do compilador/worker, bytes e concessões explícitas.
HTDL não escolhe executável, arquivo, origem, concessão ou import nativo.

`prepare(path,source,fs,ssc,profile,code,restricted,width,height,scale,policy,
metric,limits,grants,now)` aceita ASV2 já compilado. `prepare_source(compiler,
path,source,program,fs,ssc,profile,reference,mib,cpu_seconds,restricted,width,
height,scale,policy,metric,limits,grants,now)` primeiro compila em processo
descartável com orçamento do OS. Em ambos, o retorno 0 inicia a preparação;
o shell chama `advance(now)` até `ready()`. Nenhum desses métodos espera a
execução de um manipulador de página na thread gráfica.

`Limits(memory,frames,fuel,calls,timeout)` conserva os limites de pagereader:
memória VM 0..65536 bytes, frames 1..128, fuel 1..1000000, calls 0..10000,
timeout 1..60000 ms por operação. Fonte HTDL/programa: até 65536 bytes cada;
FS/SSC: 65536 cada; ASV2: 16..131088 bytes. A métrica usa a assinatura de
pagepresent::measure. Escala 65536=100%; 131072=200% da fonte.
Orçamentos locais não são quota agregada de RSS ou garantia de latência.

`framehost::versions()` negocia bootstrap; `reading_versions()` negocia o
catálogo de leitura de 18 tipos. O worker recebe respectivamente LOAD/1 ou
LOAD_CATALOG/9. Não há fallback silencioso para perder tipos ou isolamento.
`Grants(document,counter)` concede somente as capacidades locais existentes.

`commit()` ativa o candidato em testes headless. `publish(window)` publica
primeiro raster/MSAA e só após sucesso transfere os proprietários do documento,
grafos, Frame e worker. Essas transferências não alocam nem chamam a página.
Falha nativa permite retry ou `abort()`, conservando o ativo. A morte do worker
após publicação é falha do programa: a leitura continua disponível e uma nova
navegação pode recuperar a execução. Não há transação distribuída do OS.

`dispatch(document_id,projection,event)` valida separadamente o documento e a
revisão visual. Reflow aumenta apenas `snapshot().frame.version()` e conserva
document_id/estado/código. Ações de botão vão à fila FIFO de 32 entradas, como
índice da projeção semântica inteira, incluindo head/inline/hidden; não como
índice de caixa, NodeId, ponteiro ou autorização. O retorno `Action.status=1`
indica backpressure após reconhecer o gesto; o shell decide sua política.
Não se deve reenviar o mesmo evento nativo já consumido. Repetição de Enter,
requests antigos e eventos de janela forjada não duplicam ações.

Links `#id` retornam Change 8 e permanecem ações locais do shell;
`fragment_scroll(projection,node)` consulta o alvo composto. Não vão ao SDK
como botão. Copy, scroll, zoom, seleção e repaint continuam explícitos no host.
`reflow(...)` prepara somente a apresentação; `commit_reflow()` ou
`publish_reflow(window)` a conclui; `abort_reflow()` descarta. `cancel_gesture()`
libera o congelamento de gesto antes de resize/timer. Durante preparação de
navegação/compilação, eventos de ação ficam suspensos. Abort conserva o ativo;
commit descarta seleção/fila antigas. Close cancela compilação e ambos workers.

`snapshot()`, `document()`, `result()`, `error()`, `queued()`, `worker_alive()`,
`candidate_id()` e `document_id()` expõem diagnóstico/estado local de leitura.
Não há empréstimo mutável da árvore nem mutação visual pelo programa ASV2.

Exemplos: [64, sem janela](../exemplos/64_frame_worker.assis), e
[65, janela Windows](../exemplos/65_frame_worker_window.assis). Ambos exigem os
caminhos absolutos do compilador e page-worker como argumentos; o 65 aceita
`--once`/`--smoke` como terceiro argumento. O pacote de desenvolvimento inclui
compilador, DLL gráfica, worker e DLL correspondente, com hashes conjuntos.

SDK continua escalar read-only-1: não oferece strings, células por nó,
subscribe/unsubscribe, edição/IME ou scripts HTDL. Loader externo, imagens,
formulários, live regions, rede/perfis, macOS/ARM e aceites desktop/leitor/DPI
permanecem tarefas próprias. Consulte o
[perfil](ecossistema/PERFIL-FRAME-WORKER-V1.md) e o
[relatório](relatorios/2026-11-03-m3-frame-worker.md).

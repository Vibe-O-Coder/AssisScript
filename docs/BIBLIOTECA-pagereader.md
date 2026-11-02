# pagereader — Reader e página ASV2 local

Perfil **reader-worker-local-1**, 02/11/2026. Shell/coordenador em AssisScript;
reutiliza Reader, HTDL, pagehost, ASIP/1 e worker existentes. Windows x64 tem
provider gráfico; Linux x64 tem execução headless com worker restrito.
Não amplia HTDL bootstrap ou htdl_v1/read-only-1. Não há página remota pronta.

`import "std/pagereader.assis"` é exclusivo do shell confiável. Página compila
com `std/page.assis`, destino `page-asv2`; nunca recebe DLL, ponteiro ou caminho
do host. Instância/origem/caminho do worker e concessões vêm do integrador.
O caminho e os bytes do worker/provider precisam procedência confiável.

## Preparação e commit

`Session(max_bytes,max_nodes,window_instance,page_instance,origin)` possui
Reader/Store, sessão de processos e FIFO de 32 ativações. Verifique `is_open`.
`Limits(memory,frames,fuel,calls,timeout)` conserva os limites do worker:
0..65536 bytes, 1..128 frames, 1..1000000 passos, 0..10000 imports,
1..60000 ms por resposta. `Grants(document,counter)` começa com duas decisões
explícitas, sem permissão derivada de atributos HTDL.

`prepare(path,source,code,restricted,width,height,row,metric,limits,grants,now)`
valida limites, reserva documento monotônico, copia bytes, prepara parser,
layout/grafemas/nomes acessíveis e inicia processo candidato. Fonte até 64 KiB;
código 16..131088 bytes. Sem reter empréstimos do chamador. Retorna 0 ao
iniciar, Hxxx em diagnóstico HTDL e erros negativos locais. Falha/abort após
reserva consome a identidade. Entrada inválida antes disso não a consome.

`advance(now)` faz no máximo um passo de candidato e uma operação de worker
ativo. O chamador fornece relógio monotônico e intercala o loop do OS. HELLO,
LOAD e ACK das concessões precisam ter sucesso antes de `ready()`. LOAD recebe
os mesmos bytes HTDL do Reader, copiados antes do trabalho assíncrono. Nenhum
programa candidato executa antes do commit. Falha mantém o documento/worker
ativo; `error()` informa a falha. `abort()` descarta somente o candidato.

`commit()` é headless. `publish(window)` publica a projeção acessível pendente
e só então realiza os dois commits locais, sem alocação de estado adicional.
Falha de MSAA mantém ambos os ativos e permite tentar novamente ou abortar.
Commit revoga worker anterior, seus requests e as ativações pendentes. Não há
transação distribuída com o escalonador do OS: um processo pode morrer após
o último ACK; `advance` detecta e conserva a leitura disponível.

`document_id`, `candidate_id`, `document` e `active_reader` expõem identidades
e empréstimos locais do shell; não os envie como capacidades para a página.
O documento interno do worker tem id 1 e geração 1, dentro de processo/epoch
novos. A identidade externa da navegação é monotônica por Session; igualdade
numérica entre Sessions não permite acesso cruzado.

## Eventos, pressão de retorno e falha

`dispatch(document,event)` devolve `Action(status,change)`. O Reader valida
documento, janela, request, foco, seleção e hidden/disabled. Ativação válida
vira evento kind 2, payload = índice na projeção imutável HTDL (até 1024
elementos). O script usa node_at/node_kind/node_flags sob concessão. O índice
é dado local; não concede autoridade. Ações acessíveis, teclado e ponteiro
seguem o mesmo caminho. Fonte nova invalida gestos/referências anteriores.

`status=0` aceito/ação local, `1` FIFO cheia, `-2` contexto antigo/candidato
pendente, `-9` worker encerrado. Fila cheia é recusa explícita; o chamador pode
informá-la ao usuário. Repetição nativa de Enter sem key-up conserva a regra
do Viewer e não gera novos cliques. Cada evento aceito fica na FIFO até ACK=0;
ACK=1 do worker conserva o evento e permite drenar a fila interna antes de
tentar novamente. Execução do evento atual tem prioridade sobre novos posts.

`advance` mantém quanta de 1000 instruções e um import SDK por tick; fila de
UI e fila interna do worker têm tetos separados de 32. Não há threads ou heap
compartilhado. `result()` é a última Reply (result/state/counter/steps etc.),
`queued()` conta ativações ainda sem ACK. Não confunda ACK com conclusão:
somente Reply de tick com code=2 concluiu o evento.

Worker com trap/timeout/protocolo inválido é fechado, fila é descartada e
`worker_alive()` fica falso. Reader conserva a árvore e permite leitura/cópia;
ativação passa a retornar -9. Uma nova preparação válida recupera a sessão.
`close` é idempotente e fecha candidato/ativo. Ao sair do escopo, os campos
own são destruídos e o drop de Worker encerra/recolhe seus processos.

`reflow`, `paint_with` encaminham a apresentação existente. Resize conserva
fonte/identidade e não reinicia o programa. Não há mutação da árvore pelo
script, strings/subscriptions gerais ou pacote completo de recursos.

## Exemplo e limites

```powershell
python tools/build-page-worker.py --output build/demo-reader
python tools/build-platform.py --output build/demo-reader/assis_platform_v1.dll
build/assis.exe build exemplos/pages/reader-counter.assis --target page-asv2 -o build/demo-reader/reader-counter.asv2
build/assis.exe build exemplos/50_page_reader.assis -o build/demo-reader/reader.exe
```

Execute `reader.exe` com caminho absoluto do worker e do ASV2 e, no Windows,
`--trusted-local`. O diretório precisa conter ambos os providers. O exemplo
tem contador visível no painel do shell e saída PAGE-STATE no terminal;
esse painel adicional ainda não publica valor assistivo. A ação do botão e
sua árvore Reader usam MSAA. Falha do worker mantém o documento legível.
O exemplo conserva File legado e sua alocação fatal de caminho, limitada a
4097 bytes; essa API não integra a quota recuperável da Session.

Windows `restricted=true` continua recusado (-3): Job/limites de processo
não isolam autoridade. Linux aplica o perfil seccomp existente; macOS/ARM
não foram executados. Preparação/parsing e teardown/kill/reap são síncronos;
Windows pode aguardar até 5 s no encerramento. Não há garantia de latência
de UI em tempo real. Copies/FIFOs/Reader têm memória adicional fora da quota
do Store; amostragem de RSS não é quota integral ou serviço de compilação.

FS/SSC/recursos, loader remoto, sandbox Windows/macOS, IME/shaping/bidi,
desktop/leitor real/DPI/monitores, 24h e aceites de distribuição permanecem
na fila integral. Nenhum gate é aprovado por esta biblioteca.

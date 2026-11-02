# std/pagehost — host local e escalonador de páginas

Biblioteca opcional em AssisScript, dependências pagevm e htdl. Serve somente
o shell confiável. O [perfil ASV2](ecossistema/PERFIL-PAGINA-ASV2.md) fixa
layout, API, identidades, custos e limitações.

`try_new Page(instance,origin)` reserva fila de 32 eventos e 32 células.
Falha é observada por null/is_open, sem afirmar recuperação de toda a memória
do processo. prepare(document,code,memory,frames,fuel,calls) copia bytes
validados e até 1024 elementos do documento HTDL já validado. Candidato ocupado
retorna -12; erro não altera ativo. abort descarta candidato; commit não aloca.
Navegação invalida concessões/handles/fila e zera estado privado. A projeção é
snapshot independente, sem ownership ou autoridade sobre a árvore do chamador.

grant_document exige instance,origin,generation,document; revoke_document é
permanente até nova geração. grant_counter é separado. post exige envelope
completo e request monotônico; 1 indica fila cheia e preserva o request para
nova tentativa. tick(quantum) retorna 0 idle, 1 yielded, 2 evento concluído,
ou erro terminal da VM. Uma resposta SDK é resolvida por tick. revoke cancela
execução e fila; close é idempotente e libera owners. Drop automático libera
as VMs, que invalidam seus estados no destrutor; não existe callback externo.

`try_new Group()` contém até 16 slots em toda sua vida. add consome Page
mesmo em falha; retorna índice ou -1 argumento, -4 OOM, -9 fechado/cheio.
page/page_mut produzem empréstimos ligados ao Group, nunca ponteiros livres.
close_page conserva o slot aposentado. poll(now_ms,max_quanta,quantum) visita
slots circularmente, inclui instâncias com erro e verifica deadlines. Poll
retorna visited/yielded/completed/failed/expired por visita; falha repetida não
é contagem de novos crashes. visited=-1 significa argumento/tempo inválido,
sem mudança de estado. Quantum inválido não consome evento.

Não há workers ou isolamento de processo, IO assíncrono, RSS, sandbox nativa,
loader de arquivos/rede/FS/SSC, árvore mutável de página ou integração com o
Reader visual. O host do exemplo conserva o File legado: sua cópia de caminho
tem alocação fatal limitada a 4097 bytes. Não usar esse exemplo como broker
de conteúdo remoto. Testes de integração estão em tests/test-page-host.py.

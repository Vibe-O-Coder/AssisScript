# log — stderr com níveis

Opcional, inclui `cli` automaticamente no instalador. `import "std/log.assis";`, namespace `log`.

`write(nivel,min,borrow mensagem,size): int` retorna 0 se filtrado, 1 se escrito e -1 em erro. Níveis 0..5, mínimo 0..6; mínimo 6 desativa tudo. Prefixo `[epoch_ms nivel] `, mensagem em bytes e LF final. Limite: 1 MiB por mensagem. Sem estado global, alocação de mensagem inteira ou arquivo oculto.

Mensagens preservam NUL, Unicode e quebras de linha; o chamador define o conteúdo. Uma falha pode produzir registro parcial; não há atomicidade entre escritores de processos diferentes. A implementação atual é síncrona. Consulte [IO](EVENTOS-E-PERSISTENCIA.md).

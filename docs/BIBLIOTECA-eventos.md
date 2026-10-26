# eventos — fila cooperativa

Opcional. `#yuri <std/eventos.assis>`, namespace `eventos`.

`criar(capacidade): own Loop`, capacidade 1..65536. `agendar(borrow mut loop,atraso,estado,acao): int` retorna ID ou zero; `cancelar(loop,id): bool`; `executar(loop,limite): int`; `parar(loop): void`.

Callbacks têm tipo `safe assis(borrow mut Loop,int):void`. Execução por prazo/ID, reagendamento após remoção da ação atual, orçamento de ações e empréstimo exclusivo verificado. Não é uma API de threads ou de sockets assíncronos. Contratos de cancelamento, erros, exposição dos campos, reentrância e relógio estão em [EVENTOS-E-PERSISTENCIA](EVENTOS-E-PERSISTENCIA.md). O [exemplo 23](../exemplos/23_eventos.assis) roda no perfil safe e libera a fila sem free manual.

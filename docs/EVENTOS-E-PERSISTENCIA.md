# Eventos, tempo e persistência — alpha.8

`monotonic_ms()` continua monotônico em milissegundos. `civil_ms()` retorna milissegundos desde Unix epoch UTC, sujeito a ajustes do sistema. `sleep_ms(ms)` espera 0..2147483647 ms; retorna zero ou -1, com `io_error()`. Linux retoma nanosleep após EINTR; Windows usa Sleep. Não usar relógio civil para deadlines.

`events::Loop` é uma fila de uma thread, com capacidade limitada, callbacks `safe assis(borrow mut Loop,int):void`, estado escalar e temporizadores monotônicos. `schedule` retorna ID crescente ou zero em erro/capacidade/overflow; `cancel` aceita somente IDs ainda pendentes. Empate de prazo usa ID. `run(loop,limite)` impõe orçamento de ações, remove a ação antes de chamar e permite reagendamento/cancelamento/parada dentro do callback. Execução reentrante retorna -2; falha de relógio/espera/estado retorna -1. `stop` não destrói ações pendentes.

Não há thread, captura de referência ou ambiente oculto no callback. O empréstimo exclusivo dura a chamada; ações podem fazer IO, e uma ação longa bloqueia a fila. Esperas usam fatias de até 50 ms. Os campos estruturais são expostos pelo modelo de structs atual; operações verificam os comprimentos/capacidade. O contrato público exige usar as funções para editar a fila. Não há polling de sockets/descritores ou cancelamento preemptivo. Ver [exemplo 23](../exemplos/23_eventos.assis).

## IO e persistência recuperáveis

- `write_bytes(canal,buffer,n)` escreve bytes em stdout (1) ou stderr (2), preservando NUL; retorna contagem parcial ou valor negativo. Buffer gerenciado tem capacidade verificada e empréstimo compartilhado durante a operação.
- `file_open(caminho,3)` cria exclusivamente: falha se já existir. Modos 0 leitura, 1 substituir e 2 append permanecem.
- `file_sync(arquivo)` solicita fsync/FlushFileBuffers; zero ou -1, com `io_error()`.
- `file_replace(origem,destino)` solicita rename/MoveFileExW(REPLACE_EXISTING|WRITE_THROUGH). Zero ou -1; exige mesmo filesystem para a garantia de substituição atômica. Não usa fallback copiar/apagar.
- `file_remove(caminho)` retorna zero ou -1. As APIs de caminho usam text C, com a mesma fronteira legada da alpha.7; Windows converte UTF-8 estritamente e libera temporários.

`cli::write_all`, `cli::saida` e `cli::read_bounded` tratam operações parciais/EOF com bloco auxiliar fixo. `cli::argument` oferece cópia own com comprimento; `cli::parse_integer` faz conversão estrita de bytes, sem depender de NUL.

O [exemplo 24](../exemplos/24_config_json.assis) valida configuração JSON de até 1 MiB antes de tocar a saída, cria temporário exclusivo, escreve completamente, sincroniza, fecha e substitui. Remove o temporário criado quando a operação normal falha. A conversão de caminhos dos argumentos fica em helpers com `unsafe` explícito. O temporário é informado pelo chamador e deve ser novo, no mesmo filesystem do destino. Há testes de reinício do processo, entrada inválida/grande, temporário preexistente, alvo diretório e erros de handle.

Isso avança **parcialmente** P4-STORE: há persistência nativa recuperável e substituição atômica. Não é a aplicação C completa de serviço, nem garante durabilidade contra queda de energia: falta sincronização do diretório no Linux, e não se simulou falha física. Processos/IPC, rede, concorrência e ensaio real de 24 horas continuam pendentes.

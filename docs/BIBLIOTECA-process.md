# process — processos isolados, pipes e locks

`import "std/process.assis";` fornece
`run_shell(borrow command:*byte, timeout_ms:int, max_bytes:int):own Output`
e `lock(borrow path:*byte):own Lock`. Buffers têm um NUL final e não aceitam
NUL interno. O comando tem até 16384 bytes; saída até 16 MiB e timeout até
60000 ms. `Output.body()` é slice emprestado; `size`, `exit_code` e `error`
separam conteúdo, status do filho e falhas do supervisor.

`run_shell` interpreta explicitamente `/bin/sh -c` ou `cmd.exe /d /s /c` do
diretório do sistema Windows. **Somente comandos confiáveis**: não concatenar
entrada externa como comando. Não é uma API argv sem shell. O filho herda
ambiente/cwd, tem stdin fechado/nulo e stdout/stderr unidos num pipe binário.
No Windows os comandos são convertidos de UTF-8 para UTF-16. Convenções de
sintaxe/saída do shell variam entre os sistemas.

Erros: 0 término observado, -1 argumento inválido, -2 limite de saída, -3
timeout, -4 falha do OS. Saída pode ser parcial em erro. Linux usa pipe CLOEXEC,
leitura não bloqueante e grupo de processos; Windows usa processo suspenso,
Job Object e pipe antes de retomar a execução. O supervisor encerra o grupo/job
ao exceder limites e na limpeza. Descendentes que escapem deliberadamente de
grupos/sessões não estão cobertos; não se trata de isolamento de código hostil.
Linux observa o filho com WNOWAIT antes de reap para não sinalizar PID reciclado.

`Lock.acquired()` indica aquisição exclusiva não bloqueante. Linux usa flock
num arquivo 0600 e CLOEXEC; Windows usa LockFileEx sobre o primeiro byte de
um arquivo compartilhável. Fechar/matar o processo libera o lock. O arquivo
fica em disco e pode ser reutilizado. O protocolo é cooperativo: todos os
escritores precisam usar o mesmo arquivo de lock.

O runtime e o alocador continuam de uma thread. Concorrência suportada nesta
entrega significa processos independentes, comunicação por pipes e arquivos
com exclusão explícita. Não há heap compartilhado, atomics ou callbacks C em
threads externas. Linux requer glibc x86_64; Windows usa KERNEL32.

## Aplicação C

`exemplos/28_persistent_service.assis`: executar com `estado temporário lock`.
O serviço recebe `inc`, `get` e `quit`, uma solicitação por linha em stdin, e
responde por stdout. Rejeita comandos acima de 64 bytes sem perder sincronismo.
Mantém um único escritor por lock do OS. O contador tem arquivo de 16 bytes
com magic/version, inteiro e checksum. Corrupção é recusada sem sobrescrever.

Atualizar exige criar temporário novo, escrever/sincronizar/fechar e substituir
o destino no mesmo filesystem. O contador em memória só avança após sucesso.
Temporário preexistente é preservado. Após encerramento forçado em repouso, o
serviço reabre o estado e readquire o mesmo lock sem apagar arquivos manualmente.
Se a queda acontecer durante commit, um temporário pode requerer recuperação
explícita; não há garantia de durabilidade por perda de energia/diretório sync.

Testes cobrem reinício, corrupção, erro de commit, contenção do lock, morte
forçada e liberação automática; processos/pipes cobrem código de saída,
stdout/stderr, limite, timeout e 40 criações sucessivas em debug.

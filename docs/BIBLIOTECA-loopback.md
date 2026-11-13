# loopback — sockets TCP locais

Importe `std/loopback.assis` para abrir um `Server(port, capacity)`.
O provider escuta somente em `127.0.0.1`. A porta zero delega a escolha ao
SO e `port()` devolve a porta efetiva. `port()==0` indica falha de abertura.
A capacidade é de 1 a 16 conexões. Os sockets são não bloqueantes e o
destrutor fecha as conexões e o listener.

`wait(mask, timeout)` aguarda de 0 a 1000 ms por atividade. Cada bit da
máscara seleciona escrita para o slot correspondente. Os demais slots
ativos aguardam leitura. `accept()` devolve um slot livre, `-2` quando
nenhum slot ou conexão está disponível e `-1` em falha do listener.
`receive` e `send` transferem até 65.536 bytes para buffers do chamador.
O resultado é o comprimento transferido, zero em EOF, `-2` quando a
operação pode ser repetida e `-1` em erro. Uma escrita curta exige nova
tentativa a partir do primeiro byte ainda pendente. `disconnect` encerra
um slot. O chamador conserva o estado de protocolo e o prazo de cada
conexão até encerrar seu slot.

O adaptador usa Winsock 2.2 no Windows x64 e glibc no Linux x64. ARM64 e
macOS retornam falha de abertura. `Server` serve hosts confiáveis que
implementam autenticação e controle de fluxo no protocolo. Consulte o
[serviço de consulta local](BIBLIOTECA-searchservice.md) para um exemplo.
[WSAPoll e flags do Winsock](https://learn.microsoft.com/en-us/windows/win32/api/winsock2/nf-winsock2-wsapoll).

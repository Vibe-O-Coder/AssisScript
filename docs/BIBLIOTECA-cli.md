# cli — argumentos e IO limitado

Opcional. Importe `#yuri <std/cli.assis>`; namespace `cli`.

`argument(indice): own Argument` devolve `ok`, `data` own e `size`; cópia independente com terminador final. `parse_integer(borrow data,size): ParsedInt` devolve ok/valor/posição e detecta overflow int64. Nenhuma dessas APIs depende de extrair ponteiro do proprietário.

`read_bounded(borrow mut File,borrow mut destino): int` lê até EOF ou falha/limite (-1). `write_all(borrow mut File,borrow data,size): int` e `saida(canal,borrow data,size): int` repetem operações parciais até concluir ou retornar -1. Saída usa stdout 1/stderr 2 e aceita bytes NUL. Um bloco auxiliar own de 4096 bytes mantém o custo de memória limitado; o chamador mantém os buffers originais.

Falha pode deixar dados parcialmente lidos/escritos. Persistência exige sincronizar/fechar/substituir como no [contrato](EVENTOS-E-PERSISTENCIA.md). Testes: system e aplicação de configuração.

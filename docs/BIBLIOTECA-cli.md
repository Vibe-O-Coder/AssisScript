# cli — argumentos e IO limitado

Opcional. Importe `#yuri <std/cli.assis>`; namespace `cli`.

`argumento(indice): own Argumento` devolve `ok`, `dados` own e `tamanho`; cópia independente com terminador final. `inteiro(borrow dados,tamanho): Inteiro` devolve ok/valor/posição e detecta overflow int64. Nenhuma dessas APIs depende de extrair ponteiro do proprietário.

`ler_limitado(borrow mut Arquivo,borrow mut destino): int` lê até EOF ou falha/limite (-1). `escrever_tudo(borrow mut Arquivo,borrow dados,tamanho): int` e `saida(canal,borrow dados,tamanho): int` repetem operações parciais até concluir ou retornar -1. Saída usa stdout 1/stderr 2 e aceita bytes NUL. Um bloco auxiliar own de 4096 bytes mantém o custo de memória limitado; o chamador mantém os buffers originais.

Falha pode deixar dados parcialmente lidos/escritos. Persistência exige sincronizar/fechar/substituir como no [contrato](EVENTOS-E-PERSISTENCIA.md). Testes: system e aplicação de configuração.

# cli — argumentos e IO limitado

Opcional. Importe `import "std/cli.assis";`; namespace `cli`.

`argument(indice): own Argument` devolve `ok`, `data` own e `size`; cópia independente com terminador final. `parse_integer(borrow data,size): ParsedInt` devolve ok/valor/posição e detecta overflow int64. Nenhuma dessas APIs depende de extrair ponteiro do proprietário.

`read_bounded(borrow mut File,borrow mut destino): int` lê até EOF ou falha/limite (-1). `write_all(borrow mut File,borrow data,size): int` e `write_output(channel,borrow data,size): int` repetem operações parciais até concluir ou retornar -1. Saída usa stdout 1/stderr 2 e aceita bytes NUL. Um bloco auxiliar own de 4096 bytes mantém o custo de memória limitado; o chamador mantém os buffers originais. `saida` foi renomeada para `write_output`; a migração está em API-MIGRATION.json.

Falha pode deixar dados parcialmente lidos/escritos. Persistência exige sincronizar/fechar/substituir como no [contrato](EVENTOS-E-PERSISTENCIA.md). Testes: system e aplicação de configuração.

## Entrada padrão tipada

Crie uma única `own input: cli::Stdin = new cli::Stdin(limite_em_bytes);`
para stdin. Ela lê em blocos de até 4096 bytes e conserva bytes já lidos da
próxima linha. Consuma stdin pela mesma instância durante a leitura. Outra
instância, `read_bytes` ou `read_line` na mesma origem pode perder a sequência.

- `input.readln()` devolve `parse::Parsed<int>`, com o comprimento em bytes.
  Após sucesso, `input.line()` empresta a fatia UTF-8 até a próxima leitura.
  Linhas vazias são sucesso. Remove LF e o CR de CRLF, mantém CR isolado e
  aceita a última linha sem quebra.
- `input.readint()`, `input.readfloat()` e `input.readbool()` convertem uma
  linha para `int`, `f64` e `bool`. Para outras larguras, leia com `readln`
  e aplique o parser desejado a `input.line()`.
- Além dos códigos de [parse](BIBLIOTECA-parse.md), o leitor usa 5 para EOF,
  6 para erro de I/O e 7 para limite inválido ou excedido. Linha longa é
  descartada até LF/EOF com memória limitada e a próxima leitura pode
  continuar. O offset do limite excedido é o próprio limite. Em erro de
  I/O, uma linha parcial pode ter sido consumida.

É uma API síncrona para entrada local. `safe` aplica as regras de memória e
ownership da linguagem. Para entrada de terminal, o encoding dos bytes vem
do ambiente. Redirecionamento em UTF-8 e console interativo devem ser
verificados separadamente. Veja [o exemplo](../exemplos/68_typed_input.assis).

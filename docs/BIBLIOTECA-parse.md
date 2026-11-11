# std/parse.assis

Importe `std/parse.assis` e use o namespace `parse`. As funções aceitam
`slice<byte>` com comprimento explícito. Literais podem ser passados
diretamente. O chamador pode obter uma fatia de um buffer gerenciado, de
`unicode::String.as_slice()` ou de `cli::Stdin.line()`.

| Funções | Contrato |
| --- | --- |
| `parse_i8`, `parse_i16`, `parse_i32`, `parse_i64` | Decimal ASCII com sinal opcional. Verifica o intervalo da largura antes de converter. `i64` é o alias de `int`. |
| `parse_u8`, `parse_u16`, `parse_u32`, `parse_u64` | Decimal ASCII, com `+` opcional. Rejeita qualquer sinal `-`. Aceita todo o intervalo de `u64`, inclusive 18446744073709551615. |
| `parse_f32`, `parse_f64` | Decimal ASCII com ponto e expoente `e`/`E` opcionais. Aceita `.5`, `1.` e `1e-2`. Rejeita vírgula, hex, NaN e infinito. |
| `parse_bool` | Aceita exatamente `true` e `false`. |
| `parse_text` | Valida UTF-8, inclusive vazio e NUL embutido. Retorna o comprimento em bytes e deixa a origem emprestada com o chamador. |
| `parse_string(data, destino)` | Substitui uma `unicode::String` por uma cópia independente e retorna seu comprimento. Preserva o destino em UTF-8 inválido (código 2 e offset) ou falha de alocação (código 4). |

Números e booleanos não removem espaços. Separadores e sufixos de literal
não fazem parte do formato de entrada. Reais são arredondados para o mais
próximo, com empate para o par, diretamente na precisão pedida. Resultado
infinito por arredondamento é erro. Subnormais e zero assinado são aceitos.
A conversão real usa até 800 bytes para dígitos significativos e registra se
há dígito não zero no restante. O ponto e o expoente não dependem de locale.

`Parsed<T>` é um registro Copy com `ok`, `value`, `code` e `position`. Em
caso de falha, consulte `code` antes de usar `value`. A posição é um offset
de bytes a partir de zero. `-1` indica que a posição não se aplica.

| Código | Significado |
| --- | --- |
| 0 | Sucesso |
| 1 | Entrada numérica/booleana vazia |
| 2 | Sintaxe ou UTF-8 inválido |
| 3 | Fora do intervalo |
| 4 | Falha de alocação |

O `text` legado é uma visão terminada em NUL. Para entrada externa, a
combinação de fatia e `unicode::String` preserva o comprimento e a propriedade.
A API legada `std/convert.assis` continua disponível com seu contrato próprio.
Veja [leitura de stdin](BIBLIOTECA-cli.md) e
[o programa de exemplo](../exemplos/68_typed_input.assis).

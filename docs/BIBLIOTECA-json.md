# json — UTF-8 com limites

Opcional, depende do texto obrigatório. Importe `import "std/json.assis";`; namespace `json`.

`validate(borrow data,size,profundidade,max_tokens): ValidationResult` verifica exatamente um documento. Resultado Copy contém `valid`, `position` em bytes e contagem de tokens. Profundidade de contêineres 1..64; orçamento explícito inclui pontuação. Strings exigem UTF-8 estrito, escapes conhecidos e pares de surrogates corretos. NUL não escapado é inválido; `\u0000` é válido. BOM é rejeitado. Números seguem a gramática JSON e não têm conversão ou overflow numérico nesta fase. Chaves duplicadas são aceitas e preservadas pelo lexer.

`next(borrow data,size,start): Token` permite percorrer spans de bytes sem reter referências. Tipos 0 EOF, 1 string, 2 number, 3 true, 4 false, 5 null; pontuação usa ASCII. Não substitui `validate`: tokenização isolada não confere gramática. Consumidores mantêm vivo o buffer e interpretam offsets somente dentro de seu tamanho.

`quote(borrow data,size,borrow mut destino): int` serializa uma string UTF-8 sem terminador; retorna comprimento ou -1. Pré-valida capacidade/UTF-8 e preserva o destino em falha. Bytes de controle usam `\u00xx`, inclusive NUL; aspas/backslash são escapados.

Validador: O(bytes), memória O(profundidade), sem árvore ou retenção proporcional a tokens. Serializador: duas passagens, sem alocação. Não há DOM, conversão decimal de JSON para float, busca de configuração por chave ou JSON incremental entre blocos. Exemplo 24 define limite de documento de 1 MiB. Testes confrontam casos válidos/serialização com o decoder JSON independente do Python e incluem limites/erros que aquele decoder tolera, como surrogate isolado.

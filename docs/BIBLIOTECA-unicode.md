# unicode — texto com comprimento e vidas

Importação: `import "std/unicode.assis";`. Opcional, offline, sem dependências.

`unicode::String` é o texto gerenciado novo: possui seus bytes, conserva NUL, valida UTF-8 estrito, guarda comprimento explícito e libera o buffer automaticamente. Usa-se com own/borrow, em campos own e em `owned::OwnedList<unicode::String>`. O `text` anterior continua sendo a interoperabilidade C terminada em zero; sua representação não é alterada silenciosamente.

| Operação | Contrato |
| --- | --- |
| `unicode::error(borrow slice<byte>):int` | -1 para UTF-8 válido; offset do primeiro erro. O(n), sem alocar |
| `unicode::next(borrow slice<byte>,indice:int):int` | Próxima fronteira; pré-condição: texto válido e índice em início de ponto de código |
| `new unicode::String()` | Cria texto vazio válido |
| `load(borrow mut self,borrow entrada:slice<byte>):bool` | Valida e copia; false preserva o texto anterior; aceita a entrada binária com NUL |
| `size(borrow self):int` | Comprimento em bytes, O(1) |
| `as_slice(borrow self):borrow(self) slice<byte>` | Fatia compartilhada da totalidade; sem alocar |
| `slice_range(borrow self,start:int,count:int):borrow(self) slice<byte>` | Exige limites e fronteiras de pontos de código; sem alocar |

Não há normalização, grafemas, escrita bidirecional ou alteração do conteúdo por uma visão. Recarregar/liberar enquanto uma visão vive é rejeitado. UTF-8 inválido é um erro recuperável de carregar/erro; recortar no meio de um código é violação de contrato. A biblioteca não alega que o caminho legado Texto/text tenha recebido essas garantias.

Veja [exemplo 25](../exemplos/25_recursos_e_unicode.assis) e [contratos](RECURSOS-E-FATIAS.md).

## Building and printing text (alpha.14)

print(string) and write(string) borrow as_slice automatically. write has no
separator or newline; print retains spaces and a final newline. Both preserve
NUL in slices. utf8("literal") creates a static slice without allocation, and
literal arguments coerce to slice<byte> when required by a function signature.

String adds reserve, clear, append(borrow slice<byte>), append_int(int) and
append_decimal(f64,places). Append validates UTF-8 and returns false without
changing the string on invalid input. Geometric growth gives amortized append.
append_int covers the full signed 64-bit range. append_decimal accepts 0..9
fractional places, rounds halves away from zero and rejects non-finite values
or scaled magnitude above 9e18; it is binary-float display formatting. The
owned string frees its buffer automatically; no dispose or free is required.

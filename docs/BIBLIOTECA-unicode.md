# unicode — texto com comprimento e vidas

Importação: `#yuri <std/unicode.assis>`. Opcional, offline, sem dependências.

`unicode::Texto` é o texto gerenciado novo: possui seus bytes, conserva NUL, valida UTF-8 estrito, guarda comprimento explícito e libera o buffer automaticamente. Usa-se com own/borrow, em campos own e em `proprios::Lista<unicode::Texto>`. O `text` anterior continua sendo a interoperabilidade C terminada em zero; sua representação não é alterada silenciosamente.

| Operação | Contrato |
| --- | --- |
| `unicode::erro(borrow slice<byte>):int` | -1 para UTF-8 válido; offset do primeiro erro. O(n), sem alocar |
| `unicode::proximo(borrow slice<byte>,indice:int):int` | Próxima fronteira; pré-condição: texto válido e índice em início de ponto de código |
| `new unicode::Texto()` | Cria texto vazio válido |
| `carregar(borrow mut self,borrow entrada:slice<byte>):bool` | Valida e copia; false preserva o texto anterior; aceita a entrada binária com NUL |
| `tamanho(borrow self):int` | Comprimento em bytes, O(1) |
| `visualizar(borrow self):borrow(self) slice<byte>` | Fatia compartilhada da totalidade; sem alocar |
| `recortar(borrow self,inicio:int,quantidade:int):borrow(self) slice<byte>` | Exige limites e fronteiras de pontos de código; sem alocar |

Não há normalização, grafemas, escrita bidirecional ou alteração do conteúdo por uma visão. Recarregar/liberar enquanto uma visão vive é rejeitado. UTF-8 inválido é um erro recuperável de carregar/erro; recortar no meio de um código é violação de contrato. A biblioteca não alega que o caminho legado Texto/text tenha recebido essas garantias.

Veja [exemplo 25](../exemplos/25_recursos_e_unicode.assis) e [contratos](RECURSOS-E-FATIAS.md).

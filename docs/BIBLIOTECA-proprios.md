# proprios — coleções de proprietários

Importação: `#yuri <std/owned.assis>`. Opcional, offline, sem dependências.

`owned::OwnedList<T>` admite recursos Move gerenciados: buffers, arquivos, structs/classes com contrato e outras coleções. Elementos escalares usam Array; `OwnedList<int>` é rejeitada. O limite é 1024 elementos, pois a destruição dos nós é recursiva e verifica a pilha.

| Método | Contrato | Custo |
| --- | --- | --- |
| `size(borrow self): int` | Número de elementos | O(1) |
| `push_front(borrow mut self, own value:T): void` | Consome alocação, retorno own ou move explícito; insere no início | O(1) |
| `get(borrow self, indice:int): borrow(self) T` | Empréstimo compartilhado; impede modificar/liberar a lista enquanto vivo | O(n) |
| `pop_front(borrow mut self): own T` | Transfere o primeiro elemento sem o destruir | O(1) |

Índice inválido, retirada vazia ou limite excedido são erros de contrato com diagnóstico fatal. Recursos restantes são liberados automaticamente em ordem da lista, cada um uma vez, inclusive em retornos antecipados. Não há referência compartilhada com contagem, persistência funcional ou aleatoriedade de hash. Array/HashMap legados não ganham ownership de objetos implicitamente.

Veja [exemplo 25](../exemplos/25_recursos_e_unicode.assis) e [contratos](RECURSOS-E-FATIAS.md).

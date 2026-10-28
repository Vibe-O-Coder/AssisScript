# proprios — coleções de proprietários

Importação: `import "std/owned.assis";`. Opcional, offline, sem dependências.

`owned::OwnedList<T>` admite recursos Move gerenciados: buffers, arquivos, structs/classes com contrato e outras coleções. Elementos escalares usam Array; `OwnedList<int>` é rejeitada. O limite é 1024 elementos, pois a destruição dos nós é recursiva e verifica a pilha.

| Método | Contrato | Custo |
| --- | --- | --- |
| `size(borrow self): int` | Número de elementos | O(1) |
| `push_front(borrow mut self, own value:T): void` | Consome alocação, retorno own ou move explícito; insere no início | O(1) |
| `get(borrow self, indice:int): borrow(self) T` | Empréstimo compartilhado; impede modificar/liberar a lista enquanto vivo | O(n) |
| `pop_front(borrow mut self): own T` | Transfere o primeiro elemento sem o destruir | O(1) |

Índice inválido, retirada vazia ou limite excedido são erros de contrato com diagnóstico fatal. Recursos restantes são liberados automaticamente em ordem da lista, cada um uma vez, inclusive em retornos antecipados. Não há referência compartilhada com contagem, persistência funcional ou aleatoriedade de hash. Array/HashMap legados não ganham ownership de objetos implicitamente.

Veja [exemplo 25](../exemplos/25_recursos_e_unicode.assis) e [contratos](RECURSOS-E-FATIAS.md).

## OwnedArray (alpha.14)

owned::OwnedArray<T> é uma coleção indexada de recursos Move: push(own T)
consome o item, get(index) devolve borrow(self) T e pop() transfere own T.
size() fornece o número de elementos. O contêiner destrói automaticamente
os itens restantes. Não há o teto artificial de 1024 da lista ligada.

A representação inicial é uma árvore binária indexada: push/get/pop são
O(log capacidade); destruição O(n), com pilha O(log capacidade). Não é um
buffer contíguo Array<own T>. Empréstimos de itens impedem mutar/consumir a
coleção enquanto estiverem vivos. Foram exercitados mais de quatro mil itens.

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
O(log capacidade); a destruição visita os nós remanescentes e seus recursos,
com pilha do índice O(log capacidade). Não é um
buffer contíguo Array<own T>. Empréstimos de itens impedem mutar/consumir a
coleção enquanto estiverem vivos. Foram exercitados mais de quatro mil itens.

### Continuação para o ecossistema HTDL (29/10/2026)

As operações abaixo integram a continuação reconciliada de M0.
Usam os contratos existentes de ownership, sem acrescentar sintaxe à linguagem.

| Método | Contrato | Custo da coleção |
| --- | --- | --- |
| `get_mut(borrow mut self,index:int): borrow mut(self) T` | Empresta um item com acesso exclusivo, inclusive aos seus campos own | O(log capacidade) |
| `replace(borrow mut self,index:int,own value:T): own T` | Consome o novo item e transfere o anterior; conserva tamanho e índices | O(log capacidade) |
| `swap_remove(borrow mut self,index:int): own T` | Transfere o item removido e move o último item para sua posição; não preserva ordem | O(log capacidade) |
| `clear(borrow mut self): void` | Destrói itens e nós de índice; reinicia tamanho e capacidade; pode ser repetido | O(nós alocados), mais os drops dos itens |

Todos os métodos indexados exigem `0 <= index < size()`. Falhas encerram com
status 70; não são erros recuperáveis de análise de documento. OOM continua
sendo fatal. O custo de destruição dos recursos guardados depende de cada tipo.

```assis
import "std/owned.assis";
struct Node {let value:int;own data:*byte;}
safe fn main():int {
    own nodes:owned::OwnedArray<Node>=new owned::OwnedArray<Node>();
    nodes.push(new Node(0,alloc<byte>(8)));
    {borrow mut node:Node=nodes.get_mut(0);node.value=42;}
    own previous:Node=nodes.replace(0,new Node(7,alloc<byte>(4)));
    own removed:Node=nodes.swap_remove(0);
    nodes.clear(); // previous e removed continuam vivos até sair do escopo.
    print(previous.value,removed.value); // 42 7
    return 0;
}
```

O empréstimo de `get_mut` abrange a coleção inteira. Enquanto ele vive, não se
pode ler a coleção, obter outro item, chamar `size`, substituir, remover, limpar
ou liberar o proprietário. Encerre o bloco antes da próxima operação. Não há
inferência de empréstimos disjuntos para índices diferentes. `get` conserva seu
retorno compartilhado e não pode ser promovido a empréstimo mutável.

`replace` e `swap_remove` exigem consumir o resultado own: use um vínculo own,
transferência ou `free` explícito. Eles não destroem o item transferido. `clear`
destrói somente os itens ainda pertencentes à coleção e permite reutilizá-la.

`pop` e `swap_remove` também liberam os ramos do índice que ficaram vazios.
A capacidade lógica pode conservar seu máximo anterior até `clear`, mas os
nós vazios removidos não ficam retidos. A profundidade permanece logarítmica.

Índices são posições físicas, não identidades estáveis de nós. Após
`swap_remove(i)`, atualize a posição do último item que foi movido. Não use esse
método para a ordem dos filhos de um documento sem uma estrutura de ordem
separada. O [exemplo de recursos de documento](../exemplos/32_document_resources.assis)
mostra a atualização de um mapa ID → posição e o descarte de um evento para ID
removido. Seus IDs não se repetem durante a execução; ele não implementa tokens
de página, gerações, isolamento nem conformidade HTDL.

Validação e limites: [relatório M0 de coleções](relatorios/2026-10-29-m0-owned.md).
O próximo contrato de identidades estáveis está no [plano do ecossistema](ecossistema/PLANO-MESTRE.md).

`OwnedArray.try_push(own value):bool` usa reserva recuperável do caminho de
índice. Consome value nos dois resultados; false o destrói uma única vez e
preserva tamanho, capacidade, posições e recursos anteriores. O crescimento
prepara ramos separados antes de publicar a troca. Não oferece quota em bytes
nem reserve geral; o controlador e push/pop/swap_remove existentes conservam
seus contratos. Custos O(log capacidade), incluindo rollback do caminho.
Contrato e evidência: [inserções recuperáveis](INSERCAO-FALLIVEL.md).

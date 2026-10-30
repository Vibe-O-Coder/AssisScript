# arena — identidades geracionais locais

Módulo opcional dos fontes de desenvolvimento, dependente de `owned`.
Importe `std/arena.assis`. A continuação try_insert exige o compilador com try_new;
os pacotes anteriores não recebem a API sem reconstrução.

`Arena<T>(instance,category,slot_limit,generation_limit)` guarda recursos Move
em slots estáveis. instance/category devem ser positivos; slot_limit não
negativo; generation_limit positivo, até INT64_MAX. O host confiável atribui
instância única por documento e categoria, sem reutilização na vida do processo.
Não crie duas arenas do mesmo domínio com a mesma instância/categoria.

`Handle` é valor Copy com categoria, instância, slot e geração. É identidade
local verificável, não credencial secreta, capacidade de autorização ou ponteiro.
Campos inspecionáveis não autorizam origem nem impedem adivinhar uma identidade
viva inteira; APIs de página futuras precisam de registro opaco/capacidades e
política próprios. A arena valida os quatro campos antes de acessar o slot.

| Operação | Resultado e contrato |
| --- | --- |
| `insert(own value:T): own Insertion<T>` | `Inserted(handle)` ou `Rejected(code,own value)`; rejeição transfere o recurso de volta, sem perdê-lo |
| `try_insert(own value:T): InsertStatus` | Resultado Copy `Inserted(handle)`/`Rejected(code)`, sem heap. Consome o recurso nos dois resultados; rejeição o destrói e mantém todo o estado anterior |
| `contains(handle): bool` | False para domínio/slot/geração inválidos, removidos ou instância encerrada |
| `get(handle): borrow(self) T` | Empréstimo compartilhado; exige contains verdadeiro |
| `get_mut(handle): borrow mut(self) T` | Empréstimo exclusivo da arena inteira; exige contains verdadeiro |
| `remove(handle): own Removal<T>` | `Missing` para identidade inválida; `Removed(own value)` transfere o recurso uma vez |
| `take(handle): own T` | Exige contains verdadeiro; transfere o recurso e invalida o handle sem alocar resultado |
| `erase(handle): bool` | Destrói o recurso presente e retorna true; identidade inválida retorna false sem mudar estado; não aloca resultado |
| `size(): int` | Recursos atualmente presentes |
| `slots_used(): int` | Slots alocados na instância, incluindo livres e aposentados |
| `close(): void` | Revoga todos os handles e destrói recursos restantes; idempotente |
| `reset(instance): bool` | Exige instância estritamente maior; em sucesso encerra anterior e reabre vazia; em rejeição nada muda |

Código de rejeição de insert: 1 arena fechada, 2 quota de slots esgotada.
O limite é de slots da instância, incluindo os aposentados; uma arena pode
estar vazia e sem possibilidade de inserir. Há reutilização de slots livres,
sem mover os demais. Ao remover, a geração aumenta antes da reutilização.
Ao atingir generation_limit, o slot é aposentado, sem wrap. O limite pode ser
pequeno nos testes; produção pode usar INT64_MAX. Instância máxima não pode
ser reaberta após close: o host precisa recusar novas instâncias nesse domínio.

Use contains/erase para tratar identidades expiradas sem abortar e sem alocar;
remove mantém seu resultado own e pode falhar fatalmente em OOM. get/get_mut/take
inválidos e precondições do construtor encerram com status 70. Não há retorno
borrow opcional nessa interface: o verificador atual exige origem viva em todos
os retornos emprestados. Empréstimos impedem mutação, reset, close e destruição
do proprietário enquanto estão ativos. init não é chamado manualmente.

A quota é lógica e não limita memória total. try_insert recusa OOM em slots e
ramos do índice com código 3; slot livre é reutilizado sem alocar. Códigos 1/2
mantêm os significados acima. O controlador, init e remove ainda podem falhar
fatalmente; insert e suas variantes de resultado conservam o contrato fatal.
insert rejeitado exige consumir o
resultado own para preservar/destruir o valor devolvido. Tipos exercitados:
structs, classes finais com drop e buffers próprios. Não há cópia de recurso.

contains/get/get_mut/take/erase/remove e inserção em slot existente custam
O(log slots) pela OwnedArray. Criar slot pode crescer seu índice; close/reset
visitam os nós remanescentes e drops dos recursos. Slots vazios conservam
metadados até reset/close, dentro da quota. A arena não define ordem de filhos,
árvore HTDL, snapshots, concorrência ou lifetime de callback/evento.

Veja [exemplo](../exemplos/34_generational_arena.assis),
[testes](../tests/test-arena.py) e [relatório](relatorios/2026-10-29-m1-arena.md).
Execução publicada cobre Windows/Linux x64; geração dos demais formatos não
equivale à execução nativa macOS/ARM64. Não há integração de Browser/HTDL.

Veja [objetos e inserções recuperáveis](INSERCAO-FALLIVEL.md) e
[exemplo](../exemplos/37_fallible_slots.assis).

## Remoção durante recuperação de memória (30/10/2026)

take/erase atualizam ocupação, geração, lista de slots livres e tamanho antes
de devolver/destruir o recurso. Conservam aposentadoria sem wrap, slots estáveis
e empréstimo exclusivo da arena inteira. take aceita um recurso null presente:
contains distingue esse caso de uma identidade inválida. take inválido é erro
R001/status 70; para um evento possivelmente expirado, use erase ou contains
antes de take. Nenhum callback é invocado entre a validação e a transferência.

take não chama o drop do recurso transferido. O custo de erase inclui o drop
do usuário, que pode alocar, fazer I/O ou falhar segundo seu contrato; a garantia
de não alocação cobre a operação da biblioteca. Drops de recursos aninhados e
close também conservam seus contratos. Não há captura de OOM, quota em bytes
ou sandbox implícita. As APIs anteriores não mudam seu contrato público.

Veja [exemplo de transferência](../exemplos/38_allocation_free_removal.assis),
[testes adversos](../tests/test-arena-removal.py) e
[relatório desta unidade](relatorios/2026-10-30-m1-remocao-sem-alocacao.md).

# std/buffers.assis — orçamento compartilhado de payload

Continuação M1-ALLOC de 01/11/2026, E02-03. Implementação em AssisScript,
dependência `owned`; não requer provider ou alteração de sintaxe/runtime.

`BufferPool(instance,max_bytes,max_buffers,generation_limit)` possui todos os
buffers e cobra a soma de suas capacidades. Um crescimento exige espaço para
**todos os buffers vivos mais a capacidade candidata inteira**, antes de
liberar a reserva antiga. A quota é de bytes de payload solicitado, não de
RSS, slab, cabeçalhos, alinhamento, metadados, pilha ou outros objetos do
documento. `max_buffers` limita slots, incluindo os aposentados. O índice
retém seus slots até `close`/`reset`/drop; esse custo não entra em `used_bytes`.

Construir com `try_new`, verificar `null` e depois `is_open()`. A recusa da
reserva inicial resulta em null. Se a reserva do índice falhar dentro de
`init`, o controlador existe mas fica fechado, sem quota ou slots publicados.
Não há alocação de resultado de erro. `reset` não reabre esse controlador
incompleto: destrua-o e tente outra construção. A configuração exige instância
e limite de geração positivos e limites de bytes/slots não negativos;
configuração inválida e segunda chamada de `init` são erros de contrato 70/R001.
`new` conserva a reserva inicial fatal; não o use para criação recuperável.

```assis
import "std/buffers.assis";
safe fn main():int{
    own pool:buffers::BufferPool=try_new buffers::BufferPool(1,1024,16,1000000);
    if(pool==null || !pool.is_open()){return 1;}
    val result:buffers::Creation=pool.try_create(128);
    match(result){
        Created(id){pool.set(id,0,byte(42));assert(pool.erase(id));}
        Rejected(code){print(code);return 1;}
    }
    assert(pool.used_bytes()==0);return 0;
}
```

| Operação | Contrato |
| --- | --- |
| `try_create(size): Creation` | Cria buffer zerado com tamanho/capacidade exatos; `Created(BufferId)` ou `Rejected(int)` Copy. 1 fechado, 2 limite de slots, 3 recusa do alocador, 4 tamanho negativo ou quota insuficiente. Checa nessa ordem, exceto tamanho/quota antes do limite de slots. |
| `try_reserve(id,capacity): bool` | Não reduz capacidade; rejeita ID expirado, negativo, quota ou OOM. False preserva bytes, tamanho, capacidade, quota e identidades. |
| `try_resize(id,size): bool` | Reserva se necessário; zera bytes que se tornam visíveis, inclusive após redução. Reduzir tamanho conserva capacidade e cobrança. |
| `release(id): bool` | Libera payload/cobrança, conserva identidade válida com tamanho/capacidade zero; repetição válida retorna true. |
| `erase(id): bool` | Libera payload/cobrança e invalida identidade; false para ID inválido. Recicla com geração maior, aposenta no limite sem wrap. |
| `contains(id): bool` | Confere instância, slot, geração, ocupação e controlador aberto. |
| `byte_size(id)`, `capacity(id)`, `get(id,index)`, `set(id,index,value)` | Exigem identidade válida; acesso a bytes exige índice no tamanho visível. Violação: 70/R001. Não expõem ponteiro ou empréstimo mutável do armazenamento. |
| `size()`, `slots_used()`, `used_bytes()`, `max_bytes()`, `is_open()` | Consultas do controlador; `size` conta buffers presentes, inclusive vazios. |
| `close()` | Invalida todos os IDs, libera payload/metadados do índice e zera cobrança; repetível. |
| `reset(instance): bool` | Só aceita instância estritamente maior; fecha e reabre sem alocar, conservando limites. IDs anteriores ficam inválidos. |

Zero bytes não reservam payload. Crescimento usa subtração `limit-used` antes
de somar, evitando overflow do contador. A troca publica dados e cobrança
somente após preparar todos os candidatos. Recusa durante `try_create` destrói
payload/slot/ramos candidatos, conservando o estado anterior. `release`,
`erase`, `close` e `reset` não alocam pela biblioteca; os recursos internos
não têm drops do usuário. O drop normal do pool destrói os recursos restantes.

`BufferId` é domínio próprio, com instância/slot/geração. O host confiável
atribui instâncias únicas entre pools e navegações; reutilizar o mesmo número
em dois pools viola esse contrato e pode produzir IDs iguais. Não é token de
autorização, segredo, ponteiro serializado ou sandbox. Não há sincronização
entre threads. Empréstimos do controlador obedecem exclusividade normal.

## Preparação antecipada de metadados — 01/11/2026

`prepare_slots(count): Preparation` assegura **ao menos count slots livres
recicláveis**, além dos buffers vivos. Não altera `size`, `used_bytes`, dados
ou IDs existentes, nem publica IDs novos. `ready_slots()` conta esse estoque.
`slots_used()` inclui slots preparados, ocupados e aposentados. Preparar não
reserva payload; os limites de slots e de payload continuam independentes.

O resultado Copy, sem alocação, é `Ready(ready)` ou
`Incomplete(code,ready)`. Códigos: 1 pool fechado; 2 teto de slots atingido;
3 recusa do alocador; 4 quantidade negativa ou maior que `max_buffers`.
Valida fechado antes de quantidade. **A preparação é incremental**: cada slot
completo fica disponível imediatamente; Incomplete preserva os slots já
preparados e informa o estoque total exato. Pode-se consumir esse estoque ou
tentar de novo. O candidato incompleto é destruído sem publicar índice livre.
Não há rollback integral da reserva; buffers vivos e quota permanecem intactos.

Criar buffer vazio a partir desse estoque e reciclar/liberar slots não aloca
pela biblioteca. Criar payload não vazio ainda pode falhar; nesse caso o
estoque permanece intacto. `release` conserva ocupação e não devolve um slot;
`erase` o devolve somente se a geração não estiver esgotada. Slots aposentados
continuam contando no teto; `close`/`reset` descartam o estoque e invalidam IDs.

Preparar k slots novos custa O(k log slots), além das alocações do índice.
O estoque pertence ao pool, segue ownership/exclusividade e é liberado em
close/reset/drop. Exemplo: [40_prepared_buffer_slots.assis](../exemplos/40_prepared_buffer_slots.assis).
Teste: `tests/test-buffer-preallocation.py`, modelo lógico independente,
recusa local do OS com laços limitados, consumo/reciclagem sem novas reservas,
progresso parcial e vizinho intacto. [Relatório](relatorios/2026-11-01-m1-reserva-metadados.md).

Lookup/remoção custam O(log slots); criação inclui caminho do índice e zeragem
de payload; crescimento copia o tamanho visível, resize zera o trecho novo.
Destruição visita os slots retidos e buffers. A preparação acima reserva
metadados; quota geral para arenas, texto, árvore ou documento permanece aberta.

Teste: `tests/test-shared-buffer-budget.py`, modelo Python de bytes/capacidades,
260 operações, seed 20261101, 10.000 reciclagens, quotas conjuntas/transitórias,
rejeições, rollback parcial e recusa real do OS. Casos com/sem otimização,
`--debug` sem blocos vivos e geração dos cinco formatos. Resultados próprios e
plataformas estão no [relatório](relatorios/2026-11-01-m1-orcamento-buffers.md).
Exemplo: [39_shared_buffer_budget.assis](../exemplos/39_shared_buffer_budget.assis).

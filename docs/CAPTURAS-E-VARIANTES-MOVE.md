# Capturas e variantes Move — 3.3.0-alpha.13

## Closures

```assis
safe fn main(): int {
    val offset: int = 40;
    own add: closure(int): int = closure [val offset: int = offset](x: int): int {
        return offset + x;
    };
    print(add(2));
    return 0;
}
```

Capturas são explícitas: `val nome: Tipo = expressão` copia um valor Copy;
`own nome: Tipo = move(dono)` transfere um recurso (também aceita alocação ou
retorno own); `borrow nome: Tipo = origem` empresta uma referência compartilhada.
Cada inicializador é avaliado uma vez, da esquerda para a direita, no ambiente
externo. Os nomes capturados só existem no corpo da closure; locais/parâmetros
podem ocultá-los. Não há captura implícita. O limite é 64 capturas por literal.

O corpo é verificado como safe, inclusive quando criado em função legada.
IO é permitido pelos contratos safe; FFI/ponteiros brutos exigem `unsafe`.
O tipo `closure(...): ...` é diferente de `safe fn(...): ...` e de `pure fn`.
Closures são recursos Move: declarar com own, transferir com move, emprestar em
assinaturas com borrow. As capturas val são snapshots imutáveis. Campos capturados
não podem ser substituídos ou consumidos separadamente: a closure pode ser chamada
novamente. Recursos capturados são destruídos uma vez, na ordem inversa, ao liberar
o ambiente. Closures podem possuir outras closures e ser retornadas por funções
genéricas. A assinatura inclui modos dos argumentos, retorno, vidas e receptor.

`closure mut [...]` produz `closure mut(...): ...`, com acesso exclusivo ao
ambiente em cada chamada. Permite alterar dados de recursos próprios capturados;
os vínculos capturados continuam imutáveis. Uma função que a chama exige
`borrow mut f: closure mut(...): ...`. Capturas borrow continuam compartilhadas,
mesmo no corpo mut. Capturar `borrow mut` ainda é rejeitado.

Capturas borrow exigem origem gerenciada viva, incluindo slices e outras closures.
O ambiente deve ser criado diretamente num vínculo own local. Os empréstimos ficam
ativos até o fim desse escopo, inclusive se a closure for liberada antes. A origem
não pode ser alterada, movida ou liberada enquanto o empréstimo estiver ativo.
Uma closure com captura borrow pode ser chamada e passada por borrow, mas não
movida, retornada, armazenada em outro proprietário ou aninhada como captura own.
Essa regra conservadora fecha a fuga de referências locais sem inferir ou apagar
vidas ao converter tipos de closure. Capturas próprias/Copy não têm essa restrição.

Retornos emprestados podem declarar `borrow(self) Tipo`, vinculando sua vida ao
ambiente, ou a um parâmetro borrow. No tipo de closure, parâmetros usam o índice
numérico, como os callbacks anteriores; `self` designa o ambiente. O proprietário
da closure permanece retido enquanto existir o resultado emprestado.

## Variantes Move

```assis
enum OwnedOption<T> { None; Some(own T); }
safe fn main(): int {
    own option: OwnedOption<*int> = new OwnedOption<*int>.Some(alloc<int>(2));
    match (option) {
        None {}
        Some(data) { print(len(data)); }
    }
    match (move(option)) {
        None {}
        Some(data) { data[0] = 42; print(data[0]); }
    }
    return 0;
}
```

Um payload `own Tipo` torna o enum inteiro Move, inclusive variantes vazias.
Payloads sem own continuam exigindo Copy. Enums Copy anteriores preservam seu
layout inline, ausência de alocação e APIs. Enums Move usam um recurso alocado
com tag e payload, com layout máximo de 4096 bytes. Não são Move inline.
Recursão por payload own é permitida; ciclos inline continuam rejeitados.

O construtor exige uma expressão por payload e transferência explícita de donos
existentes. Campos de recursos em structs/classes também podem conter esses enums.
A destruição consulta a tag e libera somente os payloads próprios da variante ativa,
na ordem inversa. Variantes vazias e campos já movidos são seguros para liberar.

`match(dono)` ou `match(emprestimo)` retém um empréstimo compartilhado durante todo
o braço. Payloads own são vínculos borrow; payloads Copy são cópias imutáveis.
`match(move(dono))` consome o enum; payloads own passam a ser donos independentes,
e o armazenamento original desses campos é zerado. Recursos não extraídos por
retorno/move são liberados ao sair do braço, incluindo return/break/continue.
O invólucro é liberado em todos os caminhos. A exaustividade e a união conservadora
dos estados dos ramos continuam obrigatórias. Sujeitos temporários exigem primeiro
um vínculo own, evitando vidas implícitas durante um match emprestado.

## Biblioteca, custo e compatibilidade

`closure` passa a ser palavra reservada; identificadores históricos com esse nome
precisam ser renomeados. Não há novo alias cultural para a palavra. As demais
assinaturas e representações anteriores permanecem compatíveis.

`errors.assis` acrescenta `OwnedOption<T>`, `OwnedResult<T,E>`,
`owned_option_is_some` e `owned_result_map`. T/U são recursos próprios; E é Copy.
O map consome o resultado, chama uma closure emprestada apenas para Ok e preserva
Err. `Option`/`Result` Copy existentes não mudam.

`iterators::reduce_with<A>` recebe closures emprestadas de transformação, filtro
e redução, sem coleções intermediárias. A é Copy; empréstimos compartilhados das
capturas permitem reutilizar o mesmo dado imutável no pipeline. A variante pure
`reduce` continua disponível. [Exemplo completo](../exemplos/30_closures_and_owned_results.assis).

Uma closure aloca um ambiente e usa despacho indireto por chamada; não há GC ou
boxing adicionado às funções globais/valores Copy. Cada instância concreta de
literal genérico recebe classe/método especializados pelo mecanismo AST existente.
A ABI usa o ambiente como receptor antes dos argumentos e preserva o destino
oculto de retornos compostos. Enums Move alocam um invólucro por construção.
Tempos, RAM, tamanho e compilação constam das medições alpha.13, com saídas conferidas.

Closures não são callbacks ABI C: `c_callback` continua exigindo função global
sem capturas. `events` existente conserva seu contrato anterior; closures são
aceitas por APIs que declaram explicitamente o novo tipo. Não há criação de
closures em pure, conversão implícita para função, captura borrow mut, FnOnce,
Move inline, inferência de captura, threads ou estruturas persistentes novas.
Não há operador `?` neste incremento. Essas limitações são diagnósticos e escolhas
de escopo, não garantias de isolamento de conteúdo hostil.

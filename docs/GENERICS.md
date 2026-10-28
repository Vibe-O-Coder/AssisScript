# Funções, structs e classes genéricas — 3.3.0-alpha.7

**Alpha.7:** value struct e enums são especializados pela mesma infraestrutura; retornos compostos e callbacks Copy conservam identidade e efeitos. [Contratos](VALORES-E-VARIANTES.md). Structs sem value e classes conservam as representações anteriores.

Continuação da alpha.2: [tipos de função, valores especializados e callbacks](FUNCOES-E-EFEITOS.md). `identidade::<int>` também pode ser um valor; tipos como `pure fn(int): int` podem ser argumentos de tipo e são substituídos estruturalmente. O efeito participa da identidade canônica.

Esta alpha continua a fase 1. Funções globais, structs e classes podem declarar até 16 parâmetros de tipo. O compilador guarda a árvore sintática e emite uma instância nativa por definição e combinação concreta de tipos utilizada. Não há interpretação, boxing ou despacho dinâmico acrescentado pela especialização de funções. Classes conservam o despacho virtual de métodos já existente.

```assis
pure fn identidade<T>(value: T): T { return value; }
struct Caixa<T> { let value: T; }
struct Par<A, B> { let primeiro: A; let segundo: B; }

fn main(): int {
    own caixa: Caixa<int> = new Caixa<int>(identidade::<int>(42));
    print(caixa.value, identidade::<bool>(true));
    return 0;
}
```

Saída: `42 aSsIs`. [Exemplo distribuído](../exemplos/16_generics.assis).

## Regras de uso

Chamadas genéricas exigem `nome::<Tipo, OutroTipo>(arg_count)`. A sintaxe explícita evita confundir argumentos de tipo com comparações `<` e `>`. Não existe inferência dos argumentos de tipo. Todos os argumentos devem ser fornecidos; `void` não é um argumento válido. A entrada `main` não pode ser genérica.

`Caixa<int>` e `Caixa<byte>` são tipos nominais distintos. `OutraCaixa<int>` também é distinto, mesmo com campos idênticos. Parâmetros chamados `T` em definições diferentes têm identidades diferentes. Os módulos continuam compartilhando um único espaço global; não há sobrecarga ou namespaces novos.

Tipos aninhados, ponteiros, vários parâmetros, imports e recursão com um conjunto finito de instâncias são suportados. Exemplos: `Caixa<Array<int>>`, `Array<Caixa<int>>`, `HashMap<int, Caixa<text>>` e um campo `next: Elo<T>` na própria `struct Elo<T>`. Os internos de coleções permanecem privados.

Structs continuam sendo referências ao heap. Atribuir uma struct compartilha a referência; especialização não implementa cópia por valor nem imutabilidade profunda. Campos explicitamente own de structs têm destruição gerenciada na alpha.6. `own Caixa<int>` e `own Caixa<text>` seguem a regra local de structs com campos escalares/text de vida externa. A alpha.6 acrescenta campos own de structs e contratos own/borrow nas assinaturas, inclusive em especializações; veja [contratos](OWNERSHIP-FUNCOES.md). Funções genéricas comuns com `text`, objetos e ponteiros conservam o contrato legado de memória.

## Validação e diagnósticos

As operações dependentes de `T` são verificadas depois da substituição concreta. Por exemplo, `assis soma<T>(a:T,b:T):T{return a+b;}` funciona com `int`; sua instância `bool` falha. Templates não utilizados não recebem validação completa de corpo; `check --library` não certifica todas as possíveis instanciações. Não há constraints/interfaces nesta alpha.

Templates `pure` aceitam especializações `int`, `byte`, `bool` e funções pure com o mesmo contrato recursivo. Operações proibidas, inclusive print em ramos mortos e chamadas a funções comuns, são rejeitadas também em templates pure não utilizados. Callbacks chamados nesses templates exigem contrato pure explícito; não há inferência/constraints para chamar um parâmetro de tipo arbitrário. Assinaturas e demais regras dependentes do tipo são verificadas em cada instância concreta. Parâmetros puros são imutáveis. As verificações normais de ownership e privacidade ocorrem antes da emissão, em check/build/run, com e sem otimizações e em ambos os destinos.

O diagnóstico preserva arquivo/linha da declaração original. Erros dentro de funções especializadas e na validação de campos de structs especializadas acrescentam o nome do template e arquivo/linha do uso que criou aquela instância. Uma instância reutilizada pelo cache relata seu primeiro ponto de criação, não todos os chamadores.

Há limites determinísticos de 256 instâncias de funções/structs/classes do usuário por compilação, 64 níveis de expansão e 64 níveis de ponteiros. O limite anterior de 256 coleções intrínsecas continua separado. Chamadas repetidas com os mesmos tipos reutilizam a instância. Expansão ilimitada, como `f::<*T>()` chamando a si mesma, é rejeitada com diagnóstico.

## Classes e herança na alpha.4

```assis
class Caixa<T> {
    private let value: T;
    fn init(value: T): void { self.value = value; }
    fn ler(): T { return self.value; }
}
class Filha<U> extends Caixa<U> {}
```

Campos, parâmetros, retornos, tipos de callback, variáveis locais, alocações e chamadas genéricas no corpo dos métodos recebem substituição estrutural. Métodos usam os parâmetros de tipo da classe; declarar parâmetros próprios, como `assis metodo<U>`, continua rejeitado. Não há métodos pure nem valores de método vinculados a um objeto nesta entrega.

`new Filha<int>(42)` usa o inicializador herdado com a assinatura concreta. Uma subclasse pode ter base genérica aplicada ou classe comum; uma classe comum também pode herdar `Caixa<int>`. `extends T`, structs como base e ciclos de herança são rejeitados. Sobrescritas conservam exatamente os parâmetros e retorno concretos. Uma referência `Filha<int>` pode ser usada como `Caixa<int>`, preservando despacho virtual, mas não como `Caixa<bool>`. Veja [18_classes_genericas.assis](../exemplos/18_classes_genericas.assis).

A identidade declaradora dos membros pertence à especialização concreta: um método de `Caixa<int>` acessa os privados de outra `Caixa<int>`, mas não os de `Caixa<bool>`. Subclasses e funções livres não ganham acesso, mesmo quando instanciadas dentro de um método autorizado. Métodos herdados mantêm a identidade da base. O cache é compartilhado com structs, e classes contam no mesmo limite de 256 instâncias do usuário; seus métodos não consomem entradas adicionais desse limite. A expansão por bases, campos, assinaturas ou corpos de métodos também é limitada a 64 níveis, inclusive quando progride pela fila de trabalho.

Todos os métodos de uma classe instanciada passam por tipos, privacidade, pureza e ownership antes da emissão, mesmo sem chamada. O corpo de um template de classe nunca instanciado permanece sem verificação concreta. Diagnósticos preservam arquivo/linha do método original e acrescentam seu nome e primeiro local de instanciação; erros de layout/campos usam o nome da classe.

Classes continuam referências mutáveis ao heap, alocadas com `new` e liberadas explicitamente com `free`. `own`/`borrow` de classes continuam rejeitados; não há destruição automática de campos nem novo contrato de vida. Especialização não torna objetos dados puros ou profundamente imutáveis. Bibliotecas e algoritmos funcionais conservam seus contratos anteriores.

## Implementação e continuação

`DefId` identifica definições e parâmetros de tipo; `TypeId` identifica tipos concretos, inclusive profundidade de ponteiros, por internamento. Tipos aplicados guardam argumentos estruturados e posições de origem. A substituição percorre AST e tipos por identidade; nomes gerados servem ao backend. `src/generics.h` contém resolução, clonagem, cache e fila transitiva. A representação kind/depth/name permanece como vista de compatibilidade do backend.

Desde a alpha.5, Array/HashMap usam a mesma rotina de especialização AST de classes. Os templates internos são analisados uma vez quando a compilação precisa de coleções; cada instância clona/substitui tipos e corpos por identidade, sem gerar/reanalisar fonte concreto. Ambos os corpos de hash são ASTs previamente analisadas; o tipo da chave seleciona o corpo de texto ou inteiro. O algoritmo de hash continua o mesmo.

Os tipos intrínsecos conservam cache canônico, identidade pública, layouts, APIs, privacidade, bounds, limpeza e limite próprio de 256 combinações, separado das 256 instâncias do usuário. A origem confiável é uma marca interna do compilador, não o caminho `<colecoes>` ou um nome forjável. Corpos concretos percorrem a mesma fila de tipagem/pureza/ownership antes da emissão. Tipos extensos de função não passam por conversão para texto e continuam distintos por efeito e estrutura.

Os mecanismos de especialização previstos na fase 1 estão implementados. A alpha.6 integra F1 às APIs gerenciadas map_own/filter_own/fold_borrow para escalares/funções pure. Métodos com parâmetros de tipo próprios e closures exigem incrementos posteriores; variantes e structs Copy por valor chegaram na alpha.7. Tipos de função com efeitos, valores de função, callbacks e map/filter/fold escalares chegaram na alpha.3; a alpha.6 acrescenta alternativas com ownership explícito. Pure e contratos de memória não são ampliados por esta migração.

Regressões: `python tests/test-generics.py` nos dois sistemas; `ASSIS_BIN` seleciona o candidato. Medições reproduzíveis: `tools/benchmark-generics.py`; resultados e limites de interpretação constam na validação da alpha.2.

Classes: `python tests/test-generic-classes.py`, ou `make test-generic-classes`. Medições específicas: `tools/benchmark-generic-classes.py`; ver [validação da alpha.4](VALIDACAO-3.3-ALPHA.4.md).

Coleções AST: `python tests/test-collections-ast.py`, ou `make test-collections-ast`. A comparação com o compilador da alpha.4 usa `tools/benchmark-collections-ast.py --baseline CAMINHO --output RELATORIO.json`. Veja [validação da alpha.5](VALIDACAO-3.3-ALPHA.5.md) e [estimativa atual de conclusão do plano](PROGRESSO.md).

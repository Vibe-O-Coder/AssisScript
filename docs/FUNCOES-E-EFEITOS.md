# Funções como valores e efeitos — 3.3.0-alpha.3

**Atualização 3.3.0-alpha.7:** Alpha.7 amplia pure a registros/variantes Copy e permite retornos/argumentos compostos em callbacks. [Contratos](VALORES-E-VARIANTES.md). Capturas permanecem pendentes.

Atualização alpha.6: contratos own/borrow e safe integram a identidade dos callbacks. As APIs legadas desta página permanecem compatíveis; as novas APIs gerenciadas estão em [OWNERSHIP-FUNCOES.md](OWNERSHIP-FUNCOES.md).

Funções globais podem ser passadas, retornadas, copiadas e chamadas por um vínculo. Não há capturas: cada valor contém o endereço de uma função nativa com vida até o fim do programa. Métodos continuam ligados ao receptor nas chamadas `obj.metodo(...)`; extrair um método como callback exigirá closures.

```assis
pure assis dobro(v: int): int { return v * 2; }
pure assis aplicar(f: pure assis(int): int, v: int): int { return f(v); }
pure assis escolher(): pure assis(int): int { return dobro; }
pure assis identidade<T>(v: T): T { return v; }

assis assis_assis(): int {
    val f: pure assis(int): int = identidade::<int>;
    print(aplicar(escolher(), f(21))); // 42
    return 0;
}
```

## Tipos e efeitos

`pure assis(int, byte): bool` é um tipo de função pura; `assis(int, byte): bool` admite efeitos. A ordem dos parâmetros, sua quantidade, seus tipos e o retorno fazem parte da identidade estrutural. Os nomes dos parâmetros não entram no tipo. A representação é uma palavra de 64 bits, sem ambiente capturado, boxing ou alocação ao criar/copiar o callback.

Uma função pura pode ser atribuída a um tipo que admite efeitos, conservando os demais tipos exatamente iguais. O caminho inverso é rejeitado, mesmo se o valor original era uma função pura: a chamada respeita o contrato estático do vínculo. Parâmetros e retornos dentro do tipo são invariantes, inclusive efeitos de callbacks aninhados. A conversão usual de um valor byte para int não converte `assis(byte): byte` em `assis(int): int`.

Tipos puros aceitam int, byte, bool, registros/variantes Copy e outros tipos de função pura, recursivamente, nos parâmetros e retorno. Text, ponteiros, objetos legados, coleções, void e funções com efeitos permanecem fora desse contrato puro. Tipos de função comuns aceitam void no retorno e, desde a alpha.6, contratos own/borrow e origem de vida no retorno; veja [ownership entre funções](OWNERSHIP-FUNCOES.md).

Nomes de funções não especializadas, `nome::<Tipo>` e variáveis de tipo de função são expressões. A especialização genérica exige argumentos explícitos também como valor. Tipos de função recebem TypeId canônico e participam do cache de especialização; o efeito faz parte da chave. Não há inferência, lambdas ou constraints novas. Em templates puros, callbacks chamados devem ter tipo `pure assis(...)` explícito, permitindo conferir efeitos mesmo sem uma instância concreta.

`val` fixa também vínculos de função; `let` permite trocar o callback por outro compatível. Parâmetros de funções pure permanecem imutáveis. Uma variável local oculta o nome global no seu escopo; argumentos de tipo numa variável local são rejeitados. Referências de função não aceitam aritmética, conversão para inteiro, free, move ou atribuição de null. `&nome_global` é rejeitado; o nome já fornece o valor da função.

## Chamadas nativas e memória

O compilador avalia a expressão do callback uma vez e depois os argumentos da esquerda para a direita. A chamada indireta usa a mesma convenção interna de pilha e retorno das chamadas diretas nos destinos PE32+/ELF64 x86_64. Não há adaptador para a ABI C/FFI.

Campos, Array e ponteiros tipados podem guardar funções no núcleo legado. Campos omitidos de uma struct são zerados; chamar um campo de função ainda zero falha com R001 e saída 70, antes do salto indireto. Isso não valida endereços arbitrários escritos por ponteiros brutos. Funções sem captura são valores sem recurso: podem compor campos/coleções aceitos por own, mas a vida do objeto que contém o campo continua sendo verificada. Argumentos gerenciados continuam impedidos de escapar por chamadas indiretas, como nas diretas.

## map, filter e fold

Importe `#yuri <std/algorithms.assis>`. APIs:

| Função | Contrato |
| --- | --- |
| `map<T,U>(Array<T>, pure assis(T): U): Array<U>` | Visita na ordem de entrada; novo array; O(n) tempo e espaço, além do custo dos callbacks |
| `filter<T>(Array<T>, pure assis(T): bool): Array<T>` | Preserva ordem e valores aceitos; novo array; O(n) tempo e espaço máximo |
| `fold<T,A>(Array<T>, A, pure assis(A,T): A): A` | Redução da esquerda para a direita; devolve inicial no vazio; O(n) tempo e O(1) espaço auxiliar |

T/U/A devem satisfazer o contrato escalar, Copy ou de função pura do callback. Não são coleções persistentes. As funções não alteram nem liberam a entrada. Map/filter sempre devolvem uma alocação independente, inclusive no vazio; o chamador deve usar `free` ou `defer free`. Fold não cria um array. O custo da alocação e do crescimento segue Array; falhas ainda abortam com os diagnósticos do runtime.

Essas APIs usam assinaturas legadas de Array: **não aceitam own/borrow como argumento**. Na alpha.6, use map_own/filter_own/fold_borrow para esses recursos, com empréstimos nas assinaturas e saída own. O exemplo usa `let` e `defer free` no mesmo escopo. Não há promessa nova de segurança de memória para referências legadas; o callback puro garante efeitos do cálculo, não propriedade da coleção. As operações são funções comuns, porque leem uma coleção mutável e podem alocar.

Veja [17_funcoes.assis](../exemplos/17_funcoes.assis), com saída `42` e `12` em linhas separadas. Classes genéricas chegaram na alpha.4, e a migração AST dos corpos das coleções foi entregue na alpha.5. Ownership entre funções chegou na alpha.6; closures e vidas gerais de text continuam pendentes.

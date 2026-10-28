# Ownership entre funções — 3.3.0-alpha.7

**Atualização alpha.9:** [Recursos/fatias e backend](RECURSOS-E-FATIAS.md) complementam os contratos abaixo: classes gerenciadas com receptor, slice<T>, texto UTF-8 com comprimento, vtable com drop e ELF PIE. [Handoff atual](HANDOFF-3.3-ALPHA.9.md).

**Atualização 3.3.0-alpha.7:** Alpha.7 amplia recursos gerenciados com Arquivo opaco e buffers/coleções de valores Copy. [IO](IO-E-APLICACAO-A.md) e [layout por valor](VALORES-E-VARIANTES.md). Classes/Texto gerais continuam pendentes.

O modelo gerenciado passa a cobrir parâmetros, retornos, chamadas indiretas e campos proprietários de structs. A representação continua sendo referência ao heap, com transferência afim e limpeza determinística. Não há GC, contagem de referências, boxing ou struct por valor novos.

## Contratos de chamada

```assis
struct Ponto { let x: int; }
safe fn create(n: int): own Ponto { return new Ponto(n); }
safe fn ler(borrow p: Ponto): int { return p.x; }
safe fn alterar(borrow mut p: Ponto, n: int): void { p.x = n; }
safe fn transferir(own p: Ponto): own Ponto { return move(p); }
safe fn observar(borrow p: Ponto): borrow(p) Ponto { return p; }
```

| Contrato | Regra |
| --- | --- |
| `own p: T` | Consome uma alocação, retorno own ou `move(dono)` explícito. O parâmetro é limpo ao sair da função, salvo transferência posterior. |
| `borrow p: T` | Leitura compartilhada. Aceita own/borrow compatível; não aceita referência legada sem origem gerenciada. |
| `borrow mut p: T` | Acesso exclusivo. Não aceita compartilhado, nem outra referência ativa ao mesmo recurso. |
| `: own T` | Retorna alocação, retorno own de outra função ou move. Quem recebe deve assumir own, transferir ou liberar explicitamente. Descartar o resultado é erro. |
| `: borrow(p) T` | Retorno derivado exclusivamente do parâmetro borrow p. Uma origem local, outro parâmetro ou um parâmetro own não pode escapar. |
| `: borrow mut(p) T` | Retorno exclusivo derivado de parâmetro borrow mut. Uma referência compartilhada nunca ganha mutabilidade. |

Um retorno declara uma única origem. Não há inferência, união de vidas ou vida estática implícita. Funções genéricas preservam contratos por identidade e verificam cada instância concreta. Parâmetros/retornos sem modo continuam legados; recursos gerenciados não podem atravessá-los. Empréstimos de text só podem ser encaminhados de uma origem já emprestada; não há conversão gerenciada de buffers para text.

## Funções como valores

```assis
val leitor: safe fn(borrow Ponto): int = ler;
val observar_fn: safe fn(borrow Ponto): borrow(0) Ponto = observar;
val transferir_fn: safe fn(own Ponto): own Ponto = transferir;
```

O índice de origem nos tipos de função começa em zero. Parâmetros e retorno têm contratos invariantes: trocar own por borrow, compartilhado por exclusivo ou a origem da vida muda o tipo. Pure pode entrar num contrato com efeitos; safe pode entrar num contrato legado, mas o caminho inverso exige uma função comprovadamente safe. Apagar safe impede chamá-la em safe sem uma fronteira unsafe. Não há adaptação implícita de ownership.

## Fluxo, reempréstimos e ordem de avaliação

Empréstimos locais terminam no fim do bloco. Pode-se reemprestar um borrow mut; durante o reempréstimo, a referência anterior fica suspensa para operações incompatíveis. Reempréstimos compartilhados permitem apenas leitura. A raiz inteira de uma struct é bloqueada, mesmo quando se empresta só um campo: não há prova de disjunção entre campos nesta entrega.

As chamadas avaliam argumentos da esquerda para a direita e mantêm cada empréstimo até a chamada terminar. Assim `f(p, move(p))` é rejeitado se o primeiro parâmetro empresta p. Resultados emprestados propagam sua origem para chamadas aninhadas, indexação e novas declarações borrow. Callbacks conservam as mesmas regras.

O endereço de uma atribuição fica reservado enquanto o lado direito é avaliado. Leituras são permitidas; mover/liberar/mutar a estrutura que sustenta o endereço é rejeitado. O receptor de método permanece emprestado durante os argumentos. Operações como `a.push(a[0])` podem ser rejeitadas por essa política conservadora; copie o escalar para um local antes da chamada.

Nos condicionais, estados de consumo são unidos apenas nos caminhos que continuam. Um ramo que retorna não invalida o proprietário no outro caminho. Se qualquer caminho que continua consome um recurso, o uso posterior é rejeitado. Consumo de proprietários externos a um laço é proibido inclusive na condição e em campos; declare dentro da iteração o recurso a consumir. Não há otimização de última utilização ou prova de laço com uma só iteração.

## Structs compostas e movimento parcial

```assis
struct Pacote { own itens: Array<int>; own buffer: *byte; let id: int; }

safe fn montar(): own Pacote {
    return new Pacote([1, 2], alloc<byte>(16), 42);
}

safe fn main(): int {
    own p: Pacote = montar();
    own itens: Array<int> = move(p.itens);
    p.itens = [3, 4];
    print(itens[0], p.itens[0], p.id);
    return 0;
}
```

`own` em campo só é aceito em struct. A construção posicional consome os campos own. A construção sem argumentos deixa esses campos nulos/vazios; indexação/acesso posterior conserva os diagnósticos de nulo/limites. Atribuir um campo own libera o conteúdo anterior, depois instala o novo proprietário. Campo movido é zerado; irmãos permanecem utilizáveis, mas mover/emprestar a struct inteira exige que todos os campos estejam válidos. A reinicialização em todos os caminhos restaura essa possibilidade. A limpeza/free da struct parcialmente movida é permitida e ignora os campos zerados.

Os campos são destruídos na ordem inversa da declaração; buffers internos de coleções também são liberados. Um helper por struct concreta permite destruição recursiva sem expansão infinita do código. Seus frames verificam o limite de pilha. O grafo de tipos aceita recursão nominal finita, com limite de 256 níveis na análise estrutural. O modelo rejeita criar ciclos de propriedade por move para um campo do próprio proprietário.

Os tipos own suportados são Arquivo, buffers primitivos/Copy, Array/HashMap de escalares/Copy/funções sem captura/text externo legado e structs compostas desses recursos. Classes/Texto, outros recursos externos e coleções de proprietários continuam sem destruição gerenciada. Campos let de referência que não sejam text externo são rejeitados em structs own. Text externo não recebe garantia de vida; safe o exclui. Structs sem value continuam referências. value struct e enums têm um contrato Copy separado, definido em VALORES-E-VARIANTES.md.

## Perfil safe e fronteira unsafe

`safe fn` verifica um subconjunto gerenciado. `--safe` exige que a entrada seja safe (ou pure); funções legadas chamadas por ela precisam estar dentro de `unsafe { ... }`. Funções safe concretas são verificadas mesmo sem chamada. Templates seguem a validação por instância; `check --library` não certifica combinações não utilizadas.

```assis
fn legado(n: int): int { return n + 1; }
safe fn main(): int {
    own a: Array<int> = [42];
    print(a[0]);
    unsafe { print(legado(1)); }
    return 0;
}
```

Fora de unsafe, referências locais/assinaturas exigem own/borrow, alocações exigem proprietário e chamadas exigem safe/pure. Métodos públicos das coleções gerenciadas são a fronteira intrínseca verificada. Ponteiros brutos, classes legadas, defer manual e conversões text/bytes exigem unsafe. Literais text e `val s: text = "literal"` são aceitos; assinaturas/text/coleções com armazenamento externo ainda são excluídos de safe.

Unsafe não desliga ownership, privacidade, pureza ou tipagem: não permite passar um own a uma função legada, criar um alias bruto dele ou retornar referência local. O código bruto introduzido explicitamente nessa fronteira continua sob responsabilidade do programa. A fronteira é opcional na migração: funções não marcadas permanecem legadas. Portanto P0-SAFE é parcial; não há segurança geral para todo código existente, FFI, isolamento de scripts ou ponteiros externos.

## Biblioteca funcional e migração

`safe` e `unsafe` passam a ser palavras reservadas; identificadores antigos com esses nomes precisam ser renomeados. Os contratos de funções antigas e as APIs manuais são preservados. Não há inferência que converta automaticamente uma referência legada em empréstimo gerenciado.

`std/algorithms.assis` oferece `safe map_own<T,U>(borrow Array<T>, callback pure): own Array<U>`, `filter_own<T>` e `fold_borrow<T,A>`. As duas primeiras têm saída independente e limpa automaticamente pelo chamador own; a terceira não aloca um array. Entrada é preservada. T/U/A devem satisfazer os callbacks puros escalares, Copy ou funções pure. As APIs antigas map/filter/fold continuam disponíveis com contratos manuais para compatibilidade.

O [exemplo 19](../exemplos/19_ownership_funcoes.assis) combina essas APIs, retorno emprestado de campo e extração parcial, com saída `6 3 24` e `4 8 12`. Execute com `assis run exemplos/19_ownership_funcoes.assis --safe --debug`.

A evolução fecha a integração de ownership de F1 para esse subconjunto de coleções. O núcleo Copy de F2, Result/Option/matching e arquivos chegaram na alpha.7. Recursos compostos gerais continuam abertos: classes/Texto, coleções de donos, variantes Move e closures precisam de incrementos próprios. Falhas fatais ainda encerram o processo sem desenrolar escopos; erros de arquivos são recuperáveis pelo contrato de IO-E-APLICACAO-A.md.

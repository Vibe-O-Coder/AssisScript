# Novidades experimentais 3.3.0-alpha.6

**Atualização 3.3.0-alpha.8:** Alpha.7 acrescenta [valores Copy e variantes](VALORES-E-VARIANTES.md), [IO e aplicação A](IO-E-APLICACAO-A.md). Pure aceita valores Copy; Option/Result e matching exaustivo estão implementados. [Progresso atual: 56%](PROGRESSO.md). As descrições das alphas anteriores abaixo são históricas.

Alpha.6: parâmetros/retornos own/borrow, vidas declaradas, campos own de structs, safe assis e unsafe { ... } estão documentados em [Ownership entre funções](OWNERSHIP-FUNCOES.md). A gramática completa acompanha essa extensão. As regras das seções históricas devem ser lidas com essa atualização.

A linguagem adota a direção funcional. Há funções como valores, tipos `pure assis(int): int`/`assis(int): int`, callbacks, composição e funções/structs/classes genéricas. `val` aceita também funções; `pure assis` admite escalares e funções puras em suas assinaturas. Veja [funções e efeitos](FUNCOES-E-EFEITOS.md), [generics](GENERICS.md), [programação funcional](PROGRAMACAO-FUNCIONAL.md) e [contratos de segurança](CONTRATOS-E-SEGURANCA.md). A gramática está em [GRAMATICA.ebnf](GRAMATICA.ebnf); as seções abaixo preservam o núcleo histórico. Classes genéricas admitem herança especializada desde a alpha.4; Array/HashMap usam especialização AST comum desde a alpha.5. A alpha.6 acrescenta vidas explícitas nas assinaturas. Métodos com parâmetros de tipo próprios e closures continuam pendentes. A [estimativa de conclusão do plano é 45%](PROGRESSO.md).

# Novidades da versão 3.2

A linguagem acrescenta `own`, `borrow`, `borrow mut`, `move`, `div { ... }`, `for`, `defer free`, `ler_bytes` e `agora`. Veja [memória e escopos](MEMORIA-OWNERSHIP.md) e [contratos e limites da versão](MELHORIAS-3.2.md). As palavras novas são reservadas. O manual abaixo preserva a descrição do núcleo anterior.

# Linguagem AssisScript 3.1

Novidades: [bibliotecas nativas e seus manuais](BIBLIOTECAS.md), [resultados recuperáveis e diagnósticos](ERROS.md), [otimizações e benchmarks](DESEMPENHO.md). `assert` admite uma mensagem text opcional, avaliada apenas na falha. `bytes(text)` e `text(*byte)` fornecem visões emprestadas para bibliotecas; consulte os contratos de memória em [texto](BIBLIOTECA-texto.md).

AssisScript tem tipagem estática, compilação nativa e gerenciamento manual de memória. Palavras distinguem maiúsculas de minúsculas. Os identificadores seguem `[A-Za-z_][A-Za-z_0-9]*`; palavras-chave, `Array`, `HashMap` e o prefixo `__assis_` são reservados. Os nomes já não precisam ser variações de Assis/Fodase.

## Programa e funções

```assis
/// Soma dois inteiros em aritmética modular de 64 bits.
assis somar(a: int, b: int): int {
    return a + b;
}

assis assis_assis(): int {
    let total: int = somar(20, 22);
    print("Total:", total);
    return 0;
}
```

A entrada é `assis_assis`, sem parâmetros, com retorno `int` ou `void`. Funções e métodos usam `assis`. Retornos não void precisam de valor em todos os caminhos. São permitidas recursão, chamadas antecipadas e recursão mútua. Variáveis locais precisam de inicialização e não podem ser declaradas duas vezes no mesmo escopo; escopos internos podem ocultar nomes externos.

## Tipos

| Tipo | Semântica |
| --- | --- |
| `int` | Inteiro com sinal de 64 bits |
| `byte` | Inteiro sem sinal de 8 bits |
| `bool` | `true` ou `false` |
| `text` | Referência a texto UTF-8 imutável |
| `void` | Somente retorno sem valor |
| `*T` | Ponteiro bruto para T |
| Nome de classe/struct | Referência nominal a instância no heap |
| `Array<T>` | Referência a sequência dinâmica homogênea |
| `HashMap<K, V>` | Referência a tabela hash tipada |

`byte` converte implicitamente para `int`. Redução para byte exige `byte(valor)` e preserva os oito bits inferiores. `int(valor)` e `bool(valor)` aceitam inteiros e booleanos; zero vira falso. `null` é atribuível a ponteiros, classes, structs e coleções, mas não a text. `void` não pode ser variável, campo, parâmetro nem elemento de coleção.

Campos começam em zero, falso, texto vazio ou referência nula. Uma variável de classe, struct ou coleção guarda uma referência; atribuí-la não cria cópia independente. Textos são imutáveis.

## Controle de fluxo

```assis
let contador: int = 0;
while (contador < 10) {
    contador += 1;
    if (contador == 3) { continue; }
    else if (contador == 8) { break; }
    else { print(contador); }
}
```

Condições exigem bool; corpos exigem chaves. Atribuição é instrução e não expressão. `break` e `continue` atuam no while mais interno. Não há `for`, `++`, `--`, exceções ou funções anônimas nesta versão.

## Classes e métodos

```assis
ASSIS Contador {
    let valor: int;

    assis assis_fodase(inicial: int): void { self.valor = inicial; }
    assis proximo(): int { self.valor += 1; return self.valor; }
}

ASSIS ContadorDuplo extends Contador {
    assis proximo(): int { self.valor += 2; return self.valor; }
}
```

`new Contador(10)` e `fodase Contador(10)` alocam e inicializam. O construtor se chama `assis_fodase` e retorna void. Todos os membros são públicos. Há herança simples e despacho virtual: uma referência à base pode receber uma derivada e chamar sua implementação real. Sobrescritas mantêm exatamente a assinatura. O inicializador é herdado; quando sobrescrito, a base não é chamada automaticamente. Não há `super`.

`free(objeto)` libera a instância, sem liberar automaticamente objetos guardados em seus campos. Não use referências após a liberação.

## Structs

```assis
struct Pessoa {
    let nome: text;
    let idade: int;
}

// Dentro de uma função:
let pessoa: Pessoa = new Pessoa("Miyabi", 24);
let outra: Pessoa = pessoa;
outra.idade += 1; // pessoa.idade também passa a 25
free(pessoa);    // outra também fica inválida
```

Struct cria um tipo nominal de registro, com campos públicos e sem métodos ou herança. Nesta versão, **struct usa semântica de referência**, como as classes, e não layout de struct C. A construção aceita zero argumentos (campos padrão) ou um valor por campo em ordem de declaração. Para copiar, construa explicitamente outro registro com os campos desejados.

## Coleções

```assis
let numeros: Array<int> = [10, 20, 30];
numeros.push(40);
numeros[0] += 1;
print(len(numeros), numeros.pop());

let pontos: HashMap<text, int> = new HashMap<text, int>();
pontos.set("Yuri", 42);
print(pontos.get("Yuri"), pontos.get_or("ausente", 0));
free(pontos);
free(numeros);
```

Literais `[...]` exigem contexto `Array<T>`: declaração, argumento, atribuição, campo de construtor ou retorno tipado. `[]` cria array vazio. Coleções podem ser aninhadas: `Array<Array<int>>`, `HashMap<text, Array<Pessoa>>`. Não há generics definidos pelo usuário.

`Array` verifica limites em leitura e escrita. `HashMap` aceita chaves text, int, byte ou bool. `free` libera também os buffers da própria coleção, mas **não os objetos e coleções armazenados**. Veja a API completa em [COLECOES.md](COLECOES.md).

## Ponteiros e alocação

```assis
let dados: *int = alloc<int>(4);
dados[0] = 42;
let endereco: *int = &dados[0];
print(*endereco);
free(dados);
```

`alloc<T>(quantidade)` aloca elementos zerados e retorna *T, validando quantidade negativa e overflow na multiplicação pelo tamanho. `&` obtém endereço e `*` dereferencia. Ponteiros brutos não verificam limites. Não há conversão de inteiro para ponteiro nem entre ponteiros incompatíveis. Ponteiro + n e ponteiro - n avançam em elementos do tipo apontado.

Buffers de text e de referências começam nulos; inicialize os elementos antes de ler. A garantia de texto vazio vale para campos de instância, não para buffers brutos. `free` recebe null, uma alocação original ou uma instância válida. Nunca libere endereço local, endereço interno ou uma alocação já liberada. Não há coletor de lixo.

## Números, operadores e avaliação

Literais: `42`, `1_000`, `0xff`, `0b1010`. Os bits são interpretados como int com sinal de 64 bits. Literais acima de 2^63 - 1 até 2^64 - 1 representam o valor negativo correspondente. Adição, subtração, multiplicação, negação e deslocamento à esquerda têm overflow modular. Divisão trunca para zero; -2^63 / -1 retorna -2^63 e o resto é zero.

| Categoria | Operadores |
| --- | --- |
| Aritmética | `+ - * / %` |
| Comparação | `== != < <= > >=` |
| Lógica | `&&` e `||` com curto-circuito; `!` |
| Bits | `&` `|` `^` `~` `<<` `>>` |
| Atribuição | `= += -= *= /= %= &= |= ^= <<= >>=` |
| Acesso | `valor.campo`, `valor.metodo(...)`, `valor[indice]` |
| Memória | `&valor`, `*ponteiro` |

Expressões e argumentos são avaliados da esquerda para a direita. Operações numéricas retornam int, inclusive entre bytes; atribuição composta a byte guarda os oito bits inferiores. Deslocamentos exigem 0 a 63; o deslocamento à direita preserva o sinal. Textos usam igualdade de conteúdo; objetos e coleções usam identidade de referência.

## Textos e funções embutidas

Textos aceitam escapes `\n`, `\r`, `\t`, `\0`, `\"`, `\\`, `\xNN` e `\uNNNN`, com codificação UTF-8. Surrogates isolados são rejeitados. Byte zero encerra operações de texto. `len("ação")` é 6; indexação retorna byte e verifica limites. Não há concatenação ou texto mutável nesta versão.

`print(valores...)` separa os valores por espaço e termina a linha; `print()` só quebra a linha. Objetos e ponteiros são mostrados como endereços hexadecimais. Booleanos preservam a saída histórica `aSsIs`/`fOdAsE`.

`len(valor)` aceita text, Array e HashMap. `assert(condicao)` exige bool e encerra com status 70 se falso. Falhas de execução incluem divisão por zero, ponteiro nulo, deslocamento inválido, alocação inválida, índice fora do limite e precondição violada.

## Comentários e documentação

`//` e `miyabi` comentam até o fim da linha; `/* ... */` e `te ... to` aceitam aninhamento. `te` e `to` isolados continuam reservados para comentários. Documente funções com linhas `///`, `miyabi` ou bloco `/** ... */` imediatamente acima da declaração. O VS Code mostra o texto e a assinatura, inclusive entre bibliotecas e pacotes.

```assis
/// Retorna o quadrado em aritmética modular de 64 bits.
/// @param valor Inteiro a multiplicar por ele mesmo.
/// @return Resultado da multiplicação.
assis quadrado(valor: int): int { return valor * valor; }
```

## Importação e pacotes

Use `#yuri <biblioteca.assis>` e `#body src.pillow`, em linhas próprias. Pacotes .pillow contêm apenas essas diretivas e comentários. `importa "caminho";` permanece como sintaxe legada. Detalhes em [BIBLIOTECAS.md](BIBLIOTECAS.md).

## Vocabulário histórico

| Preferido | Alias histórico |
| --- | --- |
| `let` | `Assis` |
| `int`, `byte`, `bool`, `text`, `void` | `AssIs`, `AssiS`, `FodAsE`, `FoDaSe`, `FODase` |
| `if`, `else`, `while`, `return` | `assIS`, `fodASE`, `ASSis`, `Fodase` |
| `print`, `new`, `free`, `self` | `FODASE`, `fodase`, `foDASE`, `aSSIS` |
| `true`, `false`, `null` | `aSsIs`, `fOdAsE`, `fOdase` |
| `break`, `continue`, `extends` | `FODasE`, `FodASE`, `ASSIS_FODASE` |
| `len(texto)` | `FODASE_fodase(texto)` |

`ASSIS_fodase(bytes)` continua alocando *byte. `assis`, `ASSIS`, `assis_assis` e `assis_fodase` preservam sua grafia original.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `tempo`, `log`, `iteradores` e `eventos` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

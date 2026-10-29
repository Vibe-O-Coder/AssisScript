# Gramáticas e análise de FluxStyle e SSC

Estado: **proposta de detalhamento de 27/10/2026**. Completa as referências [FS](10-fluxstyle-referencia.md) e [SSC](11-ssc-referencia.md). Não é um parser nem uma prova automática de ausência de ambiguidades. Os exemplos seguem em inglês. A gramática HTDL continua separada no documento [02](02-htdl-0.1.md).

## 1. Convenções compartilhadas

As EBNFs usam `[]` para opcional, `{}` para repetição e `|` para alternativa. Terminais entre aspas são exatos. Espaços e comentários podem separar tokens; não podem dividir um literal, um identificador ou `->`.

| Item léxico | Regra proposta |
| --- | --- |
| Codificação | UTF-8 válido, BOM apenas no início, CRLF/CR normalizados para LF |
| Identificador | `[A-Za-z_][A-Za-z0-9_]*`, sensível a maiúsculas |
| Número sem sinal | Dígitos decimais, opcionalmente `.` seguido de um ou mais dígitos; sem expoente, separador ou hexadecimal |
| Unidade | Adjacente ao número: `%`, `px`, `ms`, `s` ou `Hz`, com capitalização exata |
| Cor | `#` seguido de exatamente 3, 6 ou 8 dígitos hexadecimais |
| String | Aspas duplas; escapes `\"`, `\\`, `\n`, `\r`, `\t`; sem quebra de linha literal, NUL ou escape desconhecido |
| Comentário de linha | `//` até LF ou EOF |
| Comentário de bloco | `/* ... */`, com aninhamento e limite de profundidade do leitor |

O sinal é operador, não parte do token numérico: `-8px` é negação de um literal. A conversão numérica considera o sinal antes de checar a faixa pública, inclusive no limite negativo. `1.`, `.5`, `1e3`, `4 Hz`, `#12` e string sem fechamento são inválidos.

`50%` significa `number` igual a `0.5`; `50%px` não existe. `#fff` expande para `#ffffff`, e alfa omitido é 255. Cor de oito dígitos é RGBA, na ordem escrita. O domínio de cor permanece sRGB, sem aritmética de mistura no núcleo.

Strings são tokens, mas a semântica só as admite nas posições catalogadas. O núcleo atual usa strings como chaves de estado; mencionar fontes em um estudo anterior não cria uma propriedade pública de seleção arbitrária de fonte.

`flow`, `input`, `let`, `bind`, `to`, `true` e `false` são reservadas em FS. `motion`, `bind`, `to`, `true` e `false` são reservadas em SSC. Nomes de funções, namespaces e argumentos são reconhecidos por contexto; não podem ser redefinidos para simular uma primitiva do núcleo.

## 2. Arquivo FS

```ebnf
fsFile       = { flowDecl | binding }, EOF ;
flowDecl     = "flow", identifier, "{", { flowItem }, "}" ;
flowItem     = inputDecl | letDecl | output ;
inputDecl    = "input", identifier, ":", inputType, "=", source, ";" ;
inputType    = "bool" | "number" | "length" | "time" | "frequency"
             | "colorScheme" | "contrast" ;
letDecl      = "let", identifier, "=", expression, ";" ;
output       = expression, "->", outputPath, ";" ;
outputPath   = identifier, ".", identifier ;
source       = stateSource | sourcePath ;
stateSource  = "state", "(", string, ",", stateDefault,
               [ ",", "scope", ":", "node" ], ")" ;
stateDefault = "true" | "false" | signedNumber ;
signedNumber = [ "-" ], numberLiteral ;
sourcePath   = identifier, ".", identifier ;
binding      = "bind", selector, "to", identifier, ";" ;
selector     = ".", selectorName | "#", selectorName ;
```

`numberLiteral` é o número léxico com `%` opcional; `quantityLiteral` usa `px`, `ms`, `s` ou `Hz`. `selectorName` segue a forma dos tokens de `id`/`class` do HTDL: `[A-Za-z_][A-Za-z0-9_-]*`. O lexer reconhece cores em expressões e IDs no contexto depois de `bind`, evitando confundir `#abc` com uma cor.

`sourcePath` só admite as entradas catalogadas `parent.*`, `self.*` e `env.*`. O tipo declarado precisa corresponder à entrada. Para permitir as duas entradas enumeradas já propostas, `inputType` também admite **`colorScheme`** (`light`, `dark`) e **`contrast`** (`normal`, `high`); esses nomes de tipo passam a ser explícitos neste detalhamento. O código não pode declarar novas enumerações.

`state` só aceita `bool` ou `number` inteiro no primeiro SDK. O número padrão precisa representar um inteiro, mesmo que seja escrito com ponto decimal. `scope: node` é a única opção explícita; omitir significa página. Chaves obedecem `[a-z][a-z0-9_.-]*` depois de decodificar a string.

As declarações dentro do fluxo podem aparecer em qualquer ordem. Inputs e lets compartilham um espaço de nomes local; dois nomes iguais são erro. `let` pode referenciar outro `let` posterior, mas não pode ler uma saída nem outro fluxo. A declaração externa de um fluxo não é uma função chamável.

### Expressões

```ebnf
expression  = orExpr ;
orExpr      = andExpr, { "||", andExpr } ;
andExpr     = equality, { "&&", equality } ;
equality    = relation, [ ( "==" | "!=" ), relation ] ;
relation    = sum, [ ( "<" | "<=" | ">" | ">=" ), sum ] ;
sum         = product, { ( "+" | "-" ), product } ;
product     = unary, { ( "*" | "/" ), unary } ;
unary       = ( "-" | "!" ), unary | primary ;
primary     = numberLiteral | quantityLiteral | colorLiteral | string
            | "true" | "false" | identifier
            | call | "(", expression, ")" ;
call        = identifier, "(", [ callArgs ], ")" ;
callArgs    = expression, { ",", expression }
            | namedArg, { ",", namedArg } ;
namedArg    = identifier, ":", expression ;
```

Repetições de `+`, `-`, `*`, `/`, `&&` e `||` associam à esquerda. Não há comparação encadeada: `a < b < c` precisa ser reescrita com `&&`. Um identificador solto resolve primeiro um input/let local; quando não existe esse nome, só um membro conhecido de enumeração é aceito no tipo esperado. Não há acesso geral a membros em expressões; uma entrada externa deve ser declarada por `input`.

Chamadas pertencem a uma lista fechada:

| Primitiva | Forma |
| --- | --- |
| `choose` | Três argumentos posicionais, condição `bool`, ramos do mesmo tipo |
| `min`, `max` | Dois argumentos posicionais numéricos da mesma dimensão |
| `clamp` | Três argumentos posicionais da mesma dimensão; mínimo não supera máximo |
| `abs` | Um argumento posicional numérico |
| `block` | Nenhum argumento |
| `row`, `column` | Nenhum argumento ou exatamente `gap: length`; padrão `0px` |

`state` é uma fonte de input, não uma função geral de expressão. `row(8px)`, `choose(flag, a: 1px, b: 2px)` e argumentos nomeados repetidos são inválidos. Vírgula final não pertence ao núcleo. `&&`, `||` e `choose` têm avaliação curta; análise de nomes, tipos e ciclos considera todos os ramos.

### Domínios das propriedades

A tabela da referência FS define os tipos. Este detalhamento propõe ainda os seguintes domínios, aplicados **depois** da avaliação de uma expressão e **antes** da publicação:

| Propriedade | Domínio adicional |
| --- | --- |
| `layout.width`, `layout.height`, `layout.padding` | Comprimento maior ou igual a zero |
| `gap` de `row`/`column` | Comprimento maior ou igual a zero |
| `paint.radius` | Comprimento maior ou igual a zero; desenho limita o raio à caixa |
| `paint.opacity` | Entre 0 e 1, inclusive |
| `text.size` | Comprimento estritamente positivo, antes da política do usuário |
| `text.weight` | Inteiro entre 100 e 900, inclusive |
| `target.offsetX`, `target.offsetY` | Comprimento assinado, limitado pelo perfil numérico |

Negativos continuam válidos em cálculos intermediários de comprimento. `auto` é um padrão interno de largura/altura quando não há produtor; não é uma constante autoral da 0.1. Não há clamp silencioso de uma largura negativa. Propor `F404` para domínio de propriedade violado, distinto de overflow numérico `F401`.

### Diagnósticos complementares propostos

| Código | Uso |
| --- | --- |
| `F205` | Nome local, fluxo ou primitiva sem resolução |
| `F206` | Nome de input/let/flow duplicado no mesmo escopo |
| `F207` | Aridade ou argumento de primitiva inválido |
| `F404` | Valor representável, mas fora do domínio da propriedade |

Os códigos F101–F403 existentes mantêm seu significado. Uma ferramenta pode emitir mais de um erro independente, mas deve evitar mensagens derivadas de um símbolo já inválido.

## 3. Arquivo SSC

```ebnf
sscFile       = { motionDecl | binding }, EOF ;
motionDecl    = "motion", identifier, "{", { channel }, "}" ;
channel       = "spring", "(", springArg, ",", springArg, ",",
                springArg, ")", "->", presentationPath, ";" ;
springArg     = identifier, ":", springValue ;
springValue   = targetPath | signedQuantity | signedNumber ;
targetPath    = "fs", ".", "target", ".", identifier ;
presentationPath = "presentation", ".", identifier ;
signedQuantity = [ "-" ], quantityLiteral ;
```

`binding`, seletores e comentários têm as mesmas regras léxicas do FS. Os três argumentos são exatamente `target`, `frequency` e `dampingRatio`, em qualquer ordem e sem repetição. Valores são literais ou o caminho de destino; SSC 0.1 não tem `let`, expressões gerais, eventos, variáveis de estado ou chamadas ao AssisScript.

`target` deve ser `fs.target.offsetX` ou `fs.target.offsetY`; `frequency` deve usar `Hz`; `dampingRatio` é um número adimensional. A saída deve ser o mesmo eixo do destino lido. Faixas experimentais e aritmética são as do documento 11; a gramática não prova estabilidade numérica.

```sscr
motion PanelMotion {
    spring(target: fs.target.offsetY, frequency: 4Hz, dampingRatio: 0.8)
        -> presentation.offsetY;
}

bind .panel to PanelMotion;
```

Cada canal exige um produtor FS explícito. O valor padrão `0px` do motor não satisfaz essa dependência. Dois movimentos sobre eixos distintos são válidos; dois escritores do mesmo eixo são `S301`. Nome de `motion` duplicado no recurso recebe o código complementar proposto `S205`.

## 4. Fases do analisador

```text
bytes -> bounded lexer -> syntax tree with spans
      -> local name resolution -> type and domain checks
      -> dependency graph -> node binding and writer checks
      -> candidate presentation -> runtime evaluation
```

O parser não lê estado nem geometria. A resolução não escolhe um produtor vencedor. A ligação detecta restrições que dependem do nó concreto: `self.checked`, esquema de estado, escritores e disponibilidade da largura.

A avaliação verifica domínio e overflow também quando dependem de entradas dinâmicas. Validações constantes podem ocorrer antes, conservando o mesmo código de erro, mas a otimização não pode diagnosticar `F4xx` de uma expressão que a avaliação curta nunca alcançaria. `choose(false, 1px / 0, 8px)` é válido: os dois ramos têm tipo `length`, e só o segundo é avaliado. Em todos os casos, um candidato inválido não substitui a configuração ativa.

Posições de erro usam offsets de bytes UTF-8 internamente e linha/coluna UTF-16 base 1 para o editor, com fim exclusivo. Nenhum truncamento de string, saturação aritmética ou recuperação de sintaxe do editor transforma um recurso inválido em programa executável.

## 5. Recursos adiados deliberadamente

Importação entre fontes, funções do usuário, parâmetros de flow, seleção por ancestral, seletor por tipo, unidades relativas de fonte, gradientes, variáveis temporais e leitura da geometria final precisam de propostas separadas. A implementação inicial pode compartilhar bibliotecas de leitura e tipos, mas FS e SSC continuam linguagens distintas e diagnosticadas separadamente.

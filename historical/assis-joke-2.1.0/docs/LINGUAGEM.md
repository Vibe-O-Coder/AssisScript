# AssisScript 2.1: manual da linguagem

## Um programa inteiro

```assis
ASSIS AssisAssis {
    Assis Assis_assis: AssIs;

    assis assis_fodase(AssisFodase: AssIs): FODase {
        aSSIS.Assis_assis = AssisFodase;
    }

    assis FodaseFodase(): AssIs {
        aSSIS.Assis_assis += 1;
        Fodase aSSIS.Assis_assis;
    }
}

assis assis_assis(): AssIs {
    Assis AssisFodase: AssisAssis = fodase AssisAssis(41);
    FODASE("Resposta:", AssisFodase.FodaseFodase());
    foDASE(AssisFodase);
    Fodase 0;
}
```

O objeto começa em 41, o método incrementa para 42 e `foDASE` libera sua memória. `FODASE` imprime. `Fodase` retorna. `fodase` cria. A capitalização faz parte da linguagem.

## Vocabulário completo

| AssisScript | Significado |
| --- | --- |
| `ASSIS` | Declara classe |
| `ASSIS_FODASE` | Herda de uma classe |
| `assis` | Declara função ou método |
| `Assis` | Declara variável ou campo |
| `AssIs` | Inteiro com sinal de 64 bits |
| `AssiS` | Inteiro sem sinal de 8 bits, entre 0 e 255 |
| `FodAsE` | Booleano |
| `FoDaSe` | Texto imutável em UTF-8 |
| `FODase` | Ausência de retorno |
| `assIS` | Condicional `if` |
| `fodASE` | Alternativa `else` |
| `ASSis` | Laço `while` |
| `Fodase` | Retorno `return` |
| `FODASE(...)` | Imprime argumentos separados por espaço e uma quebra de linha |
| `fodase Classe(...)` | Aloca e inicializa objeto |
| `foDASE(...)` | Libera objeto ou bloco de memória |
| `aSSIS` | Referência à instância atual |
| `aSsIs` | Verdadeiro |
| `fOdAsE` | Falso |
| `fOdase` | Nulo |
| `FODasE` | Interrompe o laço mais próximo |
| `FodASE` | Continua o laço mais próximo |
| `ASSIS_fodase(n)` | Aloca `n` bytes zerados, retorna `*AssiS` |
| `FODASE_fodase(texto)` | Conta bytes UTF-8 até o primeiro byte nulo |

Dois identificadores têm função especial, mas continuam sendo nomes válidos:

| Nome | Contrato |
| --- | --- |
| `assis_assis` | Função de entrada, sem parâmetros; retorna `AssIs` ou `FODase` |
| `assis_fodase` | Inicializador de objeto; deve retornar `FODase` |

O retorno inteiro da entrada determina o status do processo pelos oito bits inferiores. Uma entrada `FODase` termina com status zero.

## A regra dos nomes

Um nome é uma ou mais ocorrências completas de `Assis` ou `Fodase`, em qualquer combinação de maiúsculas/minúsculas, opcionalmente separadas por **um** sublinhado:

```text
Válidos:   AssisAssis  FodaseAssis  ASSIS_assis  assis_Fodase_assis
Inválidos: contador   Assis42      Assis_       _Assis  Assis__Fodase
```

Nomes não podem coincidir com palavras-chave. `AssIs` é o tipo inteiro, mas `AssisAssis` pode ser o nome de uma classe. `AssisAssis` e `ASSISASSIS` são nomes diferentes.

Essa regra vale para classes, funções, métodos, campos, parâmetros e variáveis. Números, operadores, comentários e conteúdo de textos são livres. Assim, o programa pode imprimir uma frase normal sem exigir que o usuário leia apenas Assis.

## Recursos disponíveis

- Tipagem estática, variáveis locais e escopos com `{ ... }`.
- Funções, recursão, chamadas antecipadas e recursão mútua.
- Classes com campos, inicializadores e métodos de instância.
- Herança simples e despacho virtual de todos os métodos.
- Conversão implícita da classe derivada para sua base.
- Inteiros de 64 bits, bytes de 8 bits, booleanos e textos.
- Ponteiros tipados, ponteiros de ponteiros, endereçamento e indexação.
- Alocação e liberação manuais, sem coletor de lixo.
- Operações aritméticas e de bits com semântica de 64 bits definida.
- Avaliação da esquerda para a direita e curto-circuito em `&&` e `||`.
- Diagnósticos com arquivo, linha, coluna e indicação do ponto do erro.

### Tipos e conversões

```assis
Assis AssisAssis: AssIs = 42;
Assis AssisFodase: AssiS = AssiS(255);
Assis FodaseAssis: FodAsE = aSsIs;
Assis FodaseFodase: FoDaSe = "Texto livre: ação.";
Assis AssisAssisAssis: *AssIs = &AssisAssis;
```

Variáveis locais sempre precisam de um valor inicial. `AssiS` pode ser usado como `AssIs` automaticamente. A redução de um inteiro para byte exige `AssiS(...)` e guarda os oito bits inferiores: `AssiS(300)` vale 44. `AssIs(...)` e `FodAsE(...)` convertem inteiros/booleanos; zero vira falso e os demais valores viram verdadeiro. Não existem conversões de inteiro para ponteiro, nem conversões entre tipos de ponteiros incompatíveis.

Campos de objetos começam em zero, falso, texto vazio ou nulo, conforme o tipo. `FODase` só pode aparecer como retorno de função/método. Não existem variáveis ou ponteiros de tipo `FODase`.

### Controle de fluxo

```assis
Assis AssisAssis: AssIs = 0;
ASSis (AssisAssis < 10) {
    AssisAssis += 1;
    assIS (AssisAssis == 3) {
        FodASE;
    } fodASE assIS (AssisAssis == 8) {
        FODasE;
    } fodASE {
        FODASE(AssisAssis);
    }
}
```

As condições exigem `FodAsE`. Para testar um inteiro, compare com zero ou use `FodAsE(...)`. Corpos de `assIS`, `fodASE` e `ASSis` usam chaves. Ponto e vírgula termina declarações locais e instruções simples. Atribuição é instrução, não expressão: `AssisAssis = 2;` é permitido, `FODASE(AssisAssis = 2);` não é.

### Herança e polimorfismo

```assis
ASSIS AssisAssis {
    assis FodaseFodase(): AssIs { Fodase 10; }
}

ASSIS AssisAssisAssis ASSIS_FODASE AssisAssis {
    assis FodaseFodase(): AssIs { Fodase 42; }
}
```

Dentro de `assis_assis`:

```assis
Assis AssisFodase: AssisAssis = fodase AssisAssisAssis();
FODASE(AssisFodase.FodaseFodase()); // 42, embora a variável seja da base
foDASE(AssisFodase);
```

A sobrescrita mantém os tipos dos parâmetros e do retorno. A classe derivada herda os campos e o inicializador. Se ela sobrescrever o inicializador, deve manter a assinatura; a implementação da base não é chamada automaticamente nesse caso. Não há palavra `super` nesta versão. Campos não podem esconder campos ou métodos herdados.

Todos os membros são públicos. Uma variável de objeto guarda uma referência: copiá-la não clona a instância. O tipo declarado determina quais membros estão acessíveis; o tipo real determina qual implementação de método será executada.

### Ponteiros e memória manual

```assis
Assis AssisAssis: *AssiS = ASSIS_fodase(4);
AssisAssis[0] = AssiS(65);
*(AssisAssis + 1) = AssiS(66);
FODASE(AssisAssis[0], AssisAssis[1]); // 65 66
foDASE(AssisAssis);
```

`&variavel` obtém o endereço; `*ponteiro` lê ou altera o valor. `ponteiro + n` e `ponteiro - n` avançam ou recuam em **elementos do tipo apontado**, em unidades do tipo apontado. `ponteiro[indice]` também permite escrita. Endereços de campos e de referências de objeto são suportados.

`foDASE` deve receber somente nulo, objetos criados por `fodase` ou o endereço original de blocos criados por `ASSIS_fodase`. Não libere endereços de variáveis locais, endereços internos, nem a mesma alocação duas vezes. Depois da liberação, todas as referências ao bloco ficam inválidas. Objetos não liberam automaticamente outros objetos ou buffers guardados nos seus campos.

O runtime detecta acesso a ponteiro/objeto nulo, mas ponteiros brutos **não têm verificação de limites ou de duração de vida**. A responsabilidade por índices e tempo de vida pertence ao programa. Não há instrumentação automática de ponteiros nesta versão. A checagem de tipos não substitui essas regras de memória.

Os campos dos objetos ocupam células de oito bytes no runtime. Um campo `AssiS` não implica um objeto com layout compactado; o layout dos objetos não é uma interface binária pública. Buffers `*AssiS` são sequências reais de bytes.

### Operações e inteiros

| Categoria | Operadores |
| --- | --- |
| Aritmética | `+ - * / %` |
| Bits | `& \| ^ ~ << >>` |
| Comparação | `== != < <= > >=` |
| Lógica | `&& \|\| !` |
| Atribuição | `= += -= *= /= %= &= \|= ^= <<= >>=` |
| Memória | `&valor`, `*ponteiro`, `ponteiro[indice]` |
| Membros | `objeto.campo`, `objeto.metodo(...)` |

Literais aceitam decimal, hexadecimal e binário, inclusive separadores: `1_000`, `0xff`, `0b1010`. A representação é de 64 bits em complemento de dois. Literais entre `2^63` e `2^64 - 1` representam o inteiro com sinal correspondente; por exemplo, `0xffff_ffff_ffff_ffff` é -1.

Adição, subtração, multiplicação, negação e deslocamento à esquerda dão a volta em 64 bits. Divisão inteira trunca em direção a zero. O caso mínimo inteiro dividido por -1 retorna o próprio mínimo; seu resto é zero. Deslocamento à direita preserva o sinal. O número de posições deve estar entre 0 e 63. Divisão/resto por zero e deslocamentos inválidos encerram a execução com diagnóstico, sem depender de comportamento indefinido do C.

Operações numéricas produzem `AssIs`, inclusive quando os dois operandos são bytes. Atribuições compostas a um byte guardam os oito bits inferiores. Não existem `++` e `--` nesta versão; use `+= 1` e `-= 1`.

### Textos e saída

Textos usam aspas duplas e aceitam `\n`, `\t`, `\r`, `\0`, `\"`, `\\`, `\xNN` e `\uNNNN`. Os dois últimos representam pontos de código Unicode que são codificados em UTF-8. `\u` não aceita surrogates isolados.

`FODASE_fodase` mede **bytes**, não caracteres. `"ação"` tem 6 bytes em UTF-8. Indexar um texto produz `AssiS` e verifica os limites. Textos são imutáveis. O byte zero encerra o texto para saída, tamanho, comparação e indexação. `==` e `!=` comparam conteúdo de texto; entre objetos, comparam identidade.

```assis
FODASE("Assis", 42, aSsIs); // Assis 42 aSsIs
FODASE();                   // somente quebra de linha
```

Objetos e ponteiros são impressos como endereços. Os endereços são mostrados em hexadecimal com prefixo `0x`.


# AssisScript — linguagem atual (3.3.0-alpha.15)

A linguagem compila programas tipados para executáveis nativos x86_64. O perfil
seguro é o padrão. Comece por funções, valores e controle de fluxo; depois
aprenda propriedade, empréstimos, classes e closures. Código bruto e FFI são
fronteiras explícitas com `unsafe`.

## Programa, valores e controle de fluxo

```assis
const ANSWER: int = 40 + 2;
const MARKER: byte = '#';
pure fn double(value: int): int { return value * 2; }
safe fn main(): int {
    own values: Array<int> = [1, 2, 3];
    for (let i: int = 0; i < len(values); i += 1) {
        print(double(values[i]));
    }
    assert(ANSWER == 42 && MARKER == byte(35));
    return 0;
}
```

`let` cria vínculo mutável; `val`, vínculo local imutável; `const`, constante
global numérica, bool ou texto estático. Constantes podem referir outras
constantes declaradas depois; ciclos e expressões com efeitos são rejeitados.
`public const` exporta constantes de um namespace.

Tipos: `int`/`i64`, `byte`/`u8`, `i8`, `i16`, `i32`, `u16`, `u32`, `u64`, `f32`,
`f64`, `bool`, `text`, `void`, `File`, classes, registros, enums e slices.
Conversões numéricas são explícitas. Inteiros têm overflow modular; divisão
trunca em direção a zero. Condições exigem bool.

Literais de caractere são bytes: `'a'`, `'#'`, `'\n'`, `'\0'`, `'\xFF'`.
Caracteres com vários bytes UTF-8 usam texto, como `"é"`. Identificadores são
ASCII e distinguem maiúsculas. `if`/`else`, `while`, `for`, `break`, `continue`
e `return` compõem o controle de fluxo; blocos usam chaves.

Na continuação de desenvolvimento de 29/10/2026, `i++`, `++i`, `i--` e
`--i` são instruções sem valor, também aceitas na inicialização e no passo do
`for`. O destino numérico mutável é avaliado uma vez. Inteiros conservam
overflow modular; reais conservam o contrato IEEE. `print(i++)` e `print(++i)`
são rejeitados. Dois sinais unários independentes precisam de separação:
`+ +i` e `- -i`. Consulte o [contrato e a migração](INCREMENTO-E-DECREMENTO.md).
Os pacotes alpha.15 anteriores a essa continuação exigem reconstrução do
compilador para oferecer essas instruções.

Na primeira fatia M1, `try_alloc<T>(count)` retorna um buffer gerenciado zerado
ou null em tamanho inválido, overflow e recusa do sistema. Exige own em safe;
verifique null antes de consultar len ou indexar. `alloc<T>` e new mantêm falha
fatal. Veja [alocação recuperável e limites por buffer](ALOCACAO-FALLIVEL.md).

Comentários são `//` e `/* ... */`, com aninhamento nos blocos. `te`, `to` e
`miyabi` podem ser nomes comuns.

## Texto e saída

```assis
import "std/unicode.assis";
safe fn main(): int {
    write("HP ", 54, "/", 54, "\n");
    own output: unicode::String = new unicode::String();
    assert(output.append("Resultado: "));
    assert(output.append_decimal(0.1 + 0.2, 2));
    print(output);
    return 0;
}
```

`print` separa argumentos por espaço e termina a linha. `write` escreve
consecutivamente, sem separador ou quebra. Aceitam escalares, texto estático,
`slice<byte>` e objetos com `as_slice(borrow self):borrow(self) slice<byte>`.
Slices preservam NUL. Objetos arbitrários não viram endereços silenciosamente
em safe. Booleanos imprimem `true`/`false`.

`utf8("literal")` cria um slice estático sem alocação. Literais também se
convertem automaticamente em argumentos que esperam `slice<byte>`.
`write_bytes(canal, slice, quantidade)` verifica o limite. Canais: 1=stdout,
2=stderr. A origem de uma visão emprestada precisa continuar viva.

`unicode::String` oferece `load`, `append`, `append_int`, `append_decimal`,
`reserve`, `clear`, `size`, `as_slice` e `slice_range`, sem dispose/free manual.
`append_decimal` aceita 0..9 casas, arredonda metades para longe de zero e
rejeita valores não finitos ou magnitude escalada acima de 9e18. É formatação
de apresentação, sujeita à representação binária de f64.
`print(f64)` conserva o hexadecimal exato; para decimal use o formatador.
Interpolação como expressão ainda não existe.

`text` externo é uma referência C terminada em zero; a classe global `String`
também pertence à API manual. Novos programas safe devem preferir Unicode e slices.

## Propriedade e classes

`own` possui um recurso. Ao sair do bloco, a linguagem libera os campos own e
o recurso, inclusive em return, break e continue. `move` transfere a posse e
invalida a origem. `borrow` permite leitura compartilhada; `borrow mut`, mutação
exclusiva. Uma visão bloqueia mutação/liberação de sua origem. Não há GC.

```assis
class Actor {
    let hp: int;
    fn init(borrow mut self, hp: int): void { self.hp = hp; }
    fn health(borrow self): int { return self.hp; }
}
class Hero extends Actor {
    fn init(borrow mut self, hp: int, bonus: int): void { super.init(hp + bonus); }
    fn health(borrow self): int { return super.health(); }
}
safe fn main(): int {
    own actor: Actor = new Hero(40, 14);
    if (actor is Hero) {
        borrow hero: Hero = actor as Hero;
        print(hero.health());
    }
    return 0;
}
```

Cada classe pode ter sua assinatura de init. `super.init(...)` chama a base
diretamente e deve ser a primeira instrução, uma única vez. Se a base tiver
init sem argumentos e a derivada omitir a chamada, o compilador a insere.
Se a classe não declarar init, herda o existente. `super.metodo(...)` chama a
implementação da base. Métodos comuns continuam virtuais e preservam assinatura
e receptor na sobrescrita.

Métodos de classes own declaram `borrow self` ou `borrow mut self`; campos de
recurso são own. `private` restringe acesso à classe declaradora. `final class`
impede herança. `drop(borrow mut self):void` é um gancho de final class, seguido
pela destruição dos campos own.

`is` consulta o tipo dinâmico, incluindo bases; null resulta false. `as`
produz uma referência do tipo pedido ou null, sem alocar nem transferir posse.
Em safe, vincule o resultado com borrow. O proprietário deve permanecer vivo. Retornos own precisam de vínculo local,
transferência para outro own ou free explícito; não se descartam implicitamente
por indexação, len ou chamada de método.

Receptores mutáveis usam reserva em duas fases: `obj.set(obj.campo)` e
`obj.set(obj.read())` são permitidas. Empréstimos persistentes, argumentos que
aliasam o receptor e mutações aninhadas conflitantes continuam rejeitados.

## Coleções, valores e funções

`Array<T>` e `HashMap<K,V>` armazenam valores escalares/Copy. A propriedade do
contêiner libera seus buffers. `owned::OwnedArray<T>` armazena recursos Move:
`push` consome, `get` empresta e `pop` transfere. Sua implementação inicial é uma
árvore indexada: operações O(log capacidade), destruição O(n) com pilha
logarítmica. Não é um buffer contíguo `Array<own T>`. `OwnedList` conserva seu
contrato anterior, inclusive o limite de 1024 nós.

`struct` cria registros no heap. `value struct` e enums sem campos own são
Copy inline. Enums com payload own são Move. `match` exige todas as variantes;
`match(move(valor))` transfere payloads.

`pure fn` não permite IO nem recursos; `safe fn` usa contratos verificados.
Funções sem esses modificadores têm efeito manual e são chamadas por safe
através de `unsafe`. Tipos de função preservam efeitos. Generics de funções e
classes usam especialização; métodos com parâmetros de tipo próprios ainda
não são aceitos.

Closures já existem com capturas explícitas val/own/borrow:
`closure[val factor:int=2](n:int):int{return factor*n;}`. O ambiente tem
propriedade determinística; capturas emprestadas não escapam.
[Contrato](CAPTURAS-E-VARIANTES-MOVE.md).

## Bibliotecas e ferramentas

`import "std/unicode.assis";` importa módulos. Namespaces qualificam nomes.
`random::Random` fornece sorteio reproduzível. `algorithms.assis` fornece
`sort(borrow mut Array<int>)` por heapsort. [Catálogo](../stdlib/catalogo.json).

```sh
assis new hello
assis check hello/assis.assis
assis run hello/assis.assis --debug
assis build hello/assis.assis --target linux-x64 -o hello-linux
assis build hello/assis.assis --target windows-x64 -o hello-windows
assis build hello/assis.assis --target macos-x64 -o hello-macos
```

Linux usa ELF, Windows usa PE e macOS usa Mach-O experimental, todos x86_64.
`run` exige o alvo local. [Suporte e limites macOS](MACOS.md).

`--legacy` seleciona memória manual em sintaxe canônica. Não reativa o antigo
dialeto. A edição de brincadeira fica em [historical](HISTORICAL.md).
`tools/migrate-syntax.py` migra fontes antigas; revise o resultado.
Aliases Assis/Fodase, #yuri/#body e comentários por palavras foram removidos.

O alvo nativo serve a ferramentas e motores do ecossistema; não oferece
isolamento para scripts de páginas. Navegador, DOM, execução isolada,
assincronia geral, interfaces e concorrência ficam fora desta revisão.

O backend da alpha.15 acrescenta [IR escalar e liveness global](BACKEND-ALPHA15.md), sem alterar a sintaxe ou os contratos de ownership.

# random

`import "std/random.assis";` disponibiliza `random::Random`, com propriedade
automática. A semente determina a sequência; zero recebe uma semente fixa.

```assis
import "std/random.assis";
safe fn main(): int {
    own rng: random::Random = new random::Random(u64(42));
    print(rng.range(1, 7));
    return 0;
}
```

`next_u64()` usa xorshift64*. `range(low, high)` inclui low e exclui high,
exige high > low e usa rejeição para evitar viés de módulo. Aceita extremos
inteiros com sinal. O gerador serve a jogos e simulações; não é criptográfico.

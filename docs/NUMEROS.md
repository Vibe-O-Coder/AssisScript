# Números nativos — alpha.8

`int`/`i64` são o mesmo inteiro com sinal de 64 bits; `byte`/`u8` são o mesmo inteiro sem sinal de 8 bits. Acrescentados `i8`, `i16`, `i32`, `u16`, `u32`, `u64`, `f32` e `f64`. São valores Copy, aceitos em funções, callbacks, campos, enums, buffers e coleções. Inteiros também podem ser chaves de HashMap. Não há boxing ou dependência de libc nos programas gerados.

## Contrato

- Inteiros usam complemento de dois, overflow modular e conversões inteiras pelos bits baixos. Operações entre larguras novas exigem tipos iguais; conversões são explícitas. A compatibilidade histórica `int`/`byte` e seu resultado `int` continua. O lado direito de shift também pode ser `int`.
- Divisão inteira trunca para zero; resto tem o sinal do dividendo. Mínimo com sinal dividido por -1 volta ao mínimo, com resto zero. Zero como divisor é erro fatal do contrato. Shifts exigem contagem em `[0, bits)`; deslocamento à direita é aritmético em tipos com sinal e lógico nos novos tipos sem sinal. `byte` conserva a promoção histórica a `int`.
- `f32` e `f64` usam IEEE-754 binário, com arredondamento ao mais próximo e empate para par, inclusive conversão direta de inteiro a f32. Não há promoção implícita entre reais, nem mistura com inteiros. Literais decimais com ponto ou expoente são f64; use `f32(1.5)` explicitamente. Literais infinitos por overflow são rejeitados; resultados de operações podem ser infinitos/NaN. Subnormais são preservados.
- Comparações escalares e de campos reais em valores compostos seguem IEEE: NaN é diferente de todo valor, inclusive de si; comparações ordenadas com NaN são falsas; +0 e -0 são iguais. Enums comparam somente o payload ativo. `bool(real)` é falso para ambos os zeros e verdadeiro para os demais valores, inclusive NaN.
- Real para inteiro trunca e satura no intervalo do destino; NaN converte para zero. Inteiro para real arredonda; `f32` recebe uma única conversão, sem arredondamento intermediário em f64.
- `print(u64)` imprime decimal sem sinal. `print(f32/f64)` imprime hexadecimal exato, independente de locale: `0x1.8000000000000p+0` equivale a 1,5. NaN/infinito usam `nan`/`inf`, com sinal quando presente. Essa saída é deliberadamente exata; formatação decimal amigável/mais curta ainda não está implementada.

Buffers têm elementos de 1/2/4/8 bytes conforme o tipo; campos de registros Copy conservam os slots alinhados da ABI alpha.7. Argumentos/retornos escalares viajam como bits em um word da ABI interna. Não confundir essa convenção com ABI C.

Testes: `tests/test-numbers.py`, com inteiros calculados independentemente em Python, valores IEEE reconstruídos por bits, extremos/subnormais, NaN, unsigned64, conversões, ABI, generics, coleções e ambos os modos de emissão. O otimizador antigo de inteiros fica restrito aos contratos em que já era válido; não dobra reais por aproximação no compilador.

Migração: os nomes novos de tipos agora são palavras reservadas. Renomeie variáveis/funções antigas chamadas `i8`, `f64` etc. antes de atualizar esses fontes. `int` e `byte` conservam as regras legadas; não há conversão automática dos números de um programa antigo para float.

# Incremento e decremento como instruções

Continuação de desenvolvimento de 29/10/2026 sobre a alpha.15. O compilador
precisa ser reconstruído a partir da revisão que contém esta mudança; o número
da versão, sozinho, não identifica o candidato. Nenhum pacote é promovido aqui.

`n++`, `++n`, `n--` e `--n` atualizam uma posição numérica mutável e não
produzem valor. As duas posições do operador têm a mesma semântica. São
aceitas como instrução própria e na inicialização ou no passo do `for`.
`continue` executa o passo; `break` não o executa.

```assis
safe fn main(): int {
    let total: int = 0;
    for (let i: int = 0; i < 4; i++) {
        if (i == 1) { continue; }
        ++total;
    }
    assert(total == 3);
    return 0;
}
```

O destino é avaliado uma vez, inclusive seus índices e receptor. A atualização
usa um do próprio tipo do destino: `int`/`i64`, `byte`/`u8`, `i8`, `i16`,
`i32`, `u16`, `u32`, `u64`, `f32` ou `f64`. Conserva as regras de
[números](NUMEROS.md): overflow inteiro modular, arredondamento IEEE e
propagação de NaN/Inf. Não há aritmética implícita de ponteiros.

As mesmas regras de atribuição composta verificam ownership, efeitos,
visibilidade e empréstimos. `val`, `const`, parâmetros imutáveis, posições
compartilhadas, campos privados inacessíveis, booleanos, ponteiros e resultados
temporários não graváveis são rejeitados. Empréstimo exclusivo válido continua
permitindo atualizar o conteúdo.

Migração: a revisão anterior lia `++n` e `--n` como dois operadores unários.
Esses tokens agora são indivisíveis. `print(++n)`, `let x:int=n++` e
`n++++` são erros `A001`; não existe valor antigo ou novo produzido pelo
operador. Para manter dois sinais unários independentes, use `+ +n` ou `- -n`.

A implementação reaproveita atribuição composta, verificação e IR tipada,
sem novo opcode de runtime. A suíte `tests/test-increment.py` executa positivo
e negativo em otimizado/referência, verifica avaliação única, compara sequências
inteiras com modelo Python de largura fixa e gera os cinco destinos nativos.
Geração de ELF/PE/Mach-O não equivale a execução nativa em todos eles.

Veja o [exemplo executável](../exemplos/33_increment.assis) e o
[relatório de reconciliação](relatorios/2026-10-29-m0-incremento.md).

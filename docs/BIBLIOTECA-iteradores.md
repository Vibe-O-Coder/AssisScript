# iteradores — pipelines imutáveis

Opcional. `#yuri <std/iterators.assis>`, namespace `iterators`.

`Range(current,end,step)` é Copy; fim é exclusivo, passo pode ser negativo. `next(it): Step` retorna `End` ou `Item(value,seguinte)` por valor. Passo zero e overflow do próximo estado terminam; o último valor válido não é perdido.

`reduce<A>(intervalo,inicial,transformar,aceitar,combinar): A` integra map/filter/fold, em ordem, sem alocar coleções intermediárias. Callbacks exigem `pure`; tipos concretos passam por verificação após especialização. Custo O(itens), memória O(1) além do acumulador. Não é inferência de fusão do otimizador. Não há captura de closures nem compartilhamento persistente de coleções; F3 continua parcial.

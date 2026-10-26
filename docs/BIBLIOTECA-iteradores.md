# iteradores — pipelines imutáveis

Opcional. `#yuri <std/iteradores.assis>`, namespace `iteradores`.

`Intervalo(atual,fim,passo)` é Copy; fim é exclusivo, passo pode ser negativo. `proximo(it): Passo` retorna `Fim` ou `Item(valor,seguinte)` por valor. Passo zero e overflow do próximo estado terminam; o último valor válido não é perdido.

`reduzir<A>(intervalo,inicial,transformar,aceitar,combinar): A` integra map/filter/fold, em ordem, sem alocar coleções intermediárias. Callbacks exigem `pure`; tipos concretos passam por verificação após especialização. Custo O(itens), memória O(1) além do acumulador. Não é inferência de fusão do otimizador. Não há captura de closures nem compartilhamento persistente de coleções; F3 continua parcial.

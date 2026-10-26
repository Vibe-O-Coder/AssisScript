# Programação funcional — 3.3.0-alpha.7

**Atualização 3.3.0-alpha.7:** Alpha.7: registros imutáveis Copy, enums, Option/Result e matching exaustivo sem alocação, com pureza e recursão direta em cauda. Consulte [valores](VALORES-E-VARIANTES.md). Closures/capturas, variantes Move e coleções persistentes continuam pendentes; os estados anteriores abaixo são históricos.

Na alpha.6, pipelines de coleções escalares podem usar empréstimos e saídas own, sem free manual. Funções safe admitem efeitos controlados; pure continua com o contrato escalar anterior. [Exemplo 19](../exemplos/19_ownership_funcoes.assis).

A direção da linguagem é funcional. Vínculos imutáveis e pureza escalar chegaram na alpha.1; funções/structs genéricas na alpha.2. A alpha.3 acrescenta [funções como valores e efeitos em tipos](FUNCOES-E-EFEITOS.md), callbacks, composição e map/filter/fold genéricos com arrays legados. Registros Copy, variantes e pattern matching chegaram na alpha.7. Lambdas/closures e dados persistentes continuam pendentes. A trilha F0–F4 no [plano](PLANO-EVOLUCAO-E-HANDOFF.md) define sua continuação.

```assis
pure assis dobro(n: int): int { return n * 2; }

pure assis calcular(n: int): int {
    val parcial: int = dobro(n);
    return parcial + 1;
}

assis assis_assis(): int {
    val resultado: int = calcular(20);
    print(resultado);
    return 0;
}
```

Saída: `41`. O cálculo não depende do terminal; a função de entrada concentra a saída. Veja [15_funcional.assis](../exemplos/15_funcional.assis).

## Vínculos `val`

`val nome: Tipo = expressão;` exige inicialização e aceita int, byte, bool, text e funções sem captura. O vínculo não pode receber `=`, atribuição composta ou ter seu endereço extraído com `&`. O valor pode ser copiado para um `let` independente. Escopos internos podem ocultar o nome como no núcleo anterior. `val` é local: não declara campos nem modifica assinaturas de parâmetros comuns.

`val` de text fixa o vínculo; **não comprova a vida nem congela a memória de um buffer externo**. `text(buffer)` e `bytes(strings)` conservam o contrato legado documentado. Por isso text ainda não entra nas assinaturas puras. Objetos, coleções e ponteiros não são aceitos em `val` nesta etapa; estender a palavra a referências mutáveis sem constância profunda produziria uma garantia enganosa.

`let`/`Assis` continuam mutáveis para compatibilidade. Prefira `val` em cálculos novos quando não precisar atualizar o vínculo. `for(val i: int=0; i<3; i+=1)` é rejeitado, porque seu incremento tenta reatribuir i.

## Funções `pure assis`

Disponível para funções globais com parâmetros e retorno int, byte, bool, valores Copy ou funções puras que obedecem ao mesmo contrato recursivamente. Parâmetros são imutáveis, sem extração de endereço. O verificador analisa os corpos e os contratos das chamadas diretas/indiretas; a grafia do nome ou o arquivo não concedem pureza. Recursão, recursão mútua e chamadas a declarações posteriores funcionam.

Operações permitidas: construção/leitura/comparação de valores Copy, matching, aritmética e comparação escalares, curto-circuito, conversões int/byte/bool, condicionais, laços, vínculos locais e chamadas a outras funções declaradas `pure`. Acumuladores locais `let` podem mudar: nenhum estado deles escapa. A semântica numérica continua modular como na 3.2.

São rejeitados IO/print, relógio, leitura, assert explícito, alocação no heap, free/defer, ponteiros, objetos legados, arrays, text e chamadas a funções comuns, mesmo se o corpo parecer puro. Callbacks exigem tipo pure explícito. Métodos puros permanecem pendentes. Não há inferência automática de pureza.

A verificação ocorre antes da emissão, em `check`, `build` e `run`, com e sem otimizações. Efeitos em ramos mortos e funções nunca chamadas também são rejeitados. `pure` não suprime verificações de limites ou erros; o modo otimizado elimina chamadas diretas em cauda com o contrato descrito em VALORES-E-VARIANTES.md.

Pureza **não** garante que a função termine ou que operações inválidas não falhem: divisão por zero, deslocamento inválido e recursão excessiva mantêm os diagnósticos existentes. Na alpha.7 há eliminação de recursão direta em cauda em pure, no modo otimizado; não há TCO mútua/indireta ou para funções com efeitos.

## Migração e próxima etapa

`private`, `val` e `pure` passam a ser palavras reservadas; renomeie identificadores antigos que usem esses nomes. Nenhuma alteração silenciosa transforma `let` em imutável. O compilador não anuncia um modo funcional completo ou segurança geral de memória nesta entrega.

DefId/TypeId, AST parametrizada e monomorfização de funções/structs começaram na alpha.2. `pure assis identidade<T>(v:T):T{return v;}` admite `int`, `byte`, `bool` e, desde a alpha.3, funções pure e, na alpha.7, valores Copy; `identidade::<text>("a")` é rejeitada quando a função é pure. Templates pure rejeitam operações proibidas e chamadas com efeitos mesmo sem instanciação; a verificação dependente do tipo ocorre em cada instância.

Tipos de função com efeitos, valores de função, callbacks e composição foram implementados na alpha.3. O compilador rejeita funções com efeitos num callback puro, inclusive por aliases e em templates puros nunca instanciados. Classes genéricas chegaram na alpha.4 com semântica de referência mutável legada; não ampliam o subconjunto pure. A migração dos corpos das coleções para AST foi concluída na alpha.5. Empréstimos nas assinaturas e APIs map_own/filter_own/fold_borrow chegaram na alpha.6; leia [ownership entre funções](OWNERSHIP-FUNCOES.md). Não ampliar pure a text/objetos antes de resolver as vidas e mutabilidade desses valores.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `time`, `log`, `iterators` e `events` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

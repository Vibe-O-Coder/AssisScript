# Valores e variantes — 3.3.0-alpha.7

`value struct` acrescenta registros imutáveis Copy com armazenamento por valor. `struct` e `ASSIS` existentes conservam suas referências ao heap. `value` é contextual: nomes de parâmetros como `value` continuam válidos.

```assis
value struct Ponto { let x: int; let y: int; }
pure assis deslocar(p: Ponto): Ponto { return new Ponto(p.x + 1, p.y); }

enum Option<T> { None; Some(T); }
enum Result<T, E> { Ok(T); Err(E); }

pure assis ler(o: Option<Ponto>): int {
    match (o) {
        None { return 0; }
        Some(p) { return p.x + p.y; }
    }
}
```

## Copy, Move e imutabilidade

Escalares, callbacks pure, registros por valor e variantes formadas recursivamente desses tipos são Copy. Atribuições, argumentos, retornos, extrações de campos e cargas de coleções produzem cópias independentes. Um `let` de valor admite substituir o valor inteiro; seus campos continuam imutáveis. `val`, parâmetros pure e vínculos de match também impedem substituir o vínculo. Endereços de valores não podem ser extraídos, nem seus campos alterados por um alias.

Valores Copy usam `let`/`val`; aplicar own/borrow/free/move diretamente a eles é rejeitado. Um buffer ou uma coleção que contém valores Copy continua sendo um recurso own separado. Essa distinção também vale para campos e parâmetros genéricos.

Recursos own existentes são Move: transferência exige `move`, empréstimos têm vida verificada e destruição ocorre na saída. Buffers e structs legadas continuam usando essa representação de recurso. Um campo próprio de `value struct` ou payload de enum **não admite** own, text, ponteiros, Arquivo, coleções ou classes. Essas combinações são rejeitadas; não há cópia implícita de um recurso nem variante Move inline nesta versão. Registros legados gerenciados podem combinar campos Copy por valor e campos own separados.

Um registro por valor aceita zero argumentos (valor zerado) ou um argumento por campo. Campos privados mantêm a identidade declaradora e as restrições de construção/leitura. Registros por valor não têm métodos ou herança. Enums exigem `new Tipo.Variação(argumentos)`, inclusive variantes vazias. Aridade e tipos são conferidos após especialização. `enum` e `match`, assim como os nomes dos novos intrínsecos de IO, passam a ser reservados.

## Matching e efeitos

`match (sujeito) { Variante(vinculos) { instrucoes } ... }` é uma instrução. Exige todas as variantes exatamente uma vez, sem wildcard ou braços inalcançáveis duplicados. O sujeito é avaliado uma vez; vínculos são cópias imutáveis com escopo do braço. Matching aninhado usa outro match dentro do braço. Não há guards, padrões literais/desestruturados em profundidade, expressão match ou operador `?` de propagação.

O fluxo considera return, break e continue. O estado de recursos é unido apenas nos braços que continuam; sair por erro libera proprietários de todos os escopos encerrados. Pure admite construir/ler/comparar esses valores, além dos escalares/callbacks anteriores. IO, ponteiros, text e alocação no heap continuam proibidos. Templates pure não instanciados também são auditados, inclusive chamadas dentro dos braços e callbacks vinculados por padrões.

`stdlib/erros.assis` oferece Option/Result, `option_or`, `option_map` e `result_map`. Os auxiliares preservam o erro e aceitam callbacks pure. Não capturam ambientes. Resultados com recursos proprietários ou text continuam fora desse contrato Copy; abrir arquivo usa um proprietário anulável com erro nativo separado.

## Layout e emissão

Campos ocupam slots alinhados a 8 bytes; byte/bool escalares continuam ocupando um byte nos buffers. Um registro soma os slots dos campos, incluindo valores aninhados. Enum ocupa uma tag de 8 bytes e o maior payload, com preenchimento zerado. Valores vazios têm 8 bytes. Limites: 4096 bytes por valor, 64 níveis de layout e 256 variantes. Ciclos inline são rejeitados. Especializações usam a infraestrutura AST e os limites já publicados; não há substituição textual.

Valores residem no frame, em elementos de buffers/coleções e em campos inline. Construção, passagem e retorno não alocam no heap. O backend usa endereços temporários para copiar bytes, mas nenhum desses endereços escapa como referência da linguagem. Cada expressão composta recebe um temporário independente, preservando argumentos já avaliados quando argumentos posteriores têm efeitos. Retornos usam um destino fornecido pelo chamador, também em chamadas indiretas e virtuais. Frame acima de 16 MiB é rejeitado antes da emissão; a execução conserva a verificação de pilha. Ver [ABI](ABI-NATIVA.md).

Cópias até 64 bytes usam cargas/gravações de words; as maiores usam cópia de bloco. Construções e chamadas já preenchem seu destino e não repetem a cópia para o mesmo endereço. No modo otimizado, ler um campo escalar de um valor local não copia todo o agregado. Essas escolhas preservam os snapshots necessários entre argumentos e não retiram verificações de índices, pilha ou ownership.

Igualdade de valores compara a representação canônica, inclusive tag e preenchimento. Como os campos só admitem Copy e não podem ser mutados isoladamente, o preenchimento é inicializado. Array/HashMap podem conter valores Copy; chaves de mapas mantêm os tipos anteriores. Buffers gerenciados de valores verificam índices pelo tamanho real do elemento. Print exige extrair campos ou fazer match, evitando imprimir um endereço temporário como se fosse o valor.

Recursão direta em posição de cauda em funções pure é eliminada no modo otimizado: argumentos são avaliados da esquerda para a direita antes de substituir os parâmetros, reutilizando o frame. Inclui parâmetros e retornos compostos. Sem otimização há chamadas normais e o diagnóstico de estouro de pilha. Não há otimização de recursão mútua, chamadas indiretas ou funções com recursos/efeitos.

Exemplo: [20_valores_e_resultados.assis](../exemplos/20_valores_e_resultados.assis). Evidência: `tests/test-values.py` e [validação](VALIDACAO-3.3-ALPHA.7.md). Closures/capturas, variantes Move, compartilhamento persistente e propagação permanecem pendentes; F2 completo/F3 não são declarados concluídos.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `tempo`, `log`, `iteradores` e `eventos` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

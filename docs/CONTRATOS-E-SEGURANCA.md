# Contratos e fronteiras — 3.3.0-alpha.6

Atualização alpha.6: [contratos interprocedurais e perfil safe](OWNERSHIP-FUNCOES.md) verificam recursos gerenciados. A fronteira unsafe é obrigatória dentro de funções safe; a migração global e text externo permanecem abertos (P0-SAFE parcial). Os parágrafos por versão abaixo preservam seus limites históricos.

## Privacidade nominal

`private let campo: Tipo;` e `private assis metodo(...): Tipo { ... }` restringem acesso à classe que declara o membro. O compilador guarda sua classe declaradora e compara a identidade com a classe do método em análise. É permitido acessar outra instância da mesma classe. Funções livres, subclasses, módulos no mesmo arquivo e tipos de mesmo formato não recebem acesso. Campos públicos continuam sendo o padrão; prefixo `_` isolado não implica privacidade.

Métodos privados não podem ser sobrescritos nem substituir um método público herdado. Um inicializador privado não pode ser invocado por `new` externo. Construtores posicionais de structs não podem inicializar campos privados externamente; a criação zerada não revela os campos.

Na alpha.4, cada especialização de classe genérica tem identidade declaradora própria. `Caixa<int>` e `Caixa<bool>` não compartilham privilégios privados. Clones dos métodos conservam a classe concreta como origem; métodos herdados conservam a origem da base. Classes usam referências e memória legadas: `own` de classe e destruição de recursos em campos permanecem sem suporte.

Todos os campos de Array/HashMap e os auxiliares `_hash`, `_find`, `_rehash` do mapa são privados. Os buffers de Texto e a lista proprietária `_campos` de DocumentoCSV também são privados. O parser CSV passou a executar no método da própria classe. `ler_csv` preserva sua assinatura; `DocumentoCSV.analisar` reutiliza a instância, descartando o conteúdo anterior e invalidando suas visualizações. `Texto.remover_ultimo_byte` oferece truncamento verificado por byte para a leitura de linhas; pode cortar UTF-8, como outras APIs de bytes.

Os fontes intrínsecos de coleções recebem uma marca interna criada pelo compilador. Um nome lógico contendo `<colecoes>` não altera a confiança do lexer; `__assis_` continua reservado inclusive em stdin/overlays. A privacidade é verificada em todos os modos e backends antes da geração de endereços.

Ao reutilizar um DocumentoCSV, analisar copia temporariamente a entrada antes de liberar os campos antigos, aceitando uma visualização do próprio documento. Isso acrescenta O(n) de memória temporária à API em memória; streaming continua pendente.

## Contratos de memória que permanecem

| Área | Garantia atual | Limite |
| --- | --- | --- |
| Array indexado | Índice verificado contra tamanho privado | Referência legada pode estar pendente após free |
| HashMap | Metadados privados e APIs tipadas | Hash adverso, propriedade de elementos e vidas externas continuam pendentes |
| own/borrow | Fluxo, exclusividade, consumo e vidas declaradas em funções e campos own de structs | Classes/Texto, proprietários em coleções e text externo continuam abertos |
| Texto/CSV | Buffers privados e operação por métodos | Visões, campos públicos e descarte legado ainda exigem disciplina do chamador |
| val | Vínculo imutável sem endereço exposto | text externo pode perder validade; ainda não há constância profunda de objetos |
| pure | Cálculo escalar e callbacks de função pure, sem efeitos externos aceitos | Não comprova término nem ausência de falhas de execução |

O perfil nativo legado continua permitindo ponteiros brutos, `alloc`, `bytes`, conversão `text`, aritmética/desreferência de ponteiros e `free`. Essas operações exigem origem, limites, aliasing e vida válidos, sob responsabilidade do programa. **Na alpha.6, funções safe exigem bloco unsafe para essa fronteira; a adoção global continua opcional.** Encapsulamento fecha B01 no nível de membros; não contém corrupção arbitrária causada por ponteiros legados ou FFI futura.

O subconjunto pure desta alpha rejeita essas operações. Funções sem captura já podem ser valores puros com efeitos tipados; ampliar pureza a referências e dados compostos ainda exige vidas nos tipos, análise de escapes e contratos de cópia/move e destruição. `text` emprestado não deve ser promovido a dado puro por conveniência.

Chamadas indiretas conservam a restrição de fuga de argumentos gerenciados e respeitam o efeito estático do callback. Funções sem captura não possuem recurso a destruir e podem ser elementos/campos de own. Map/filter/fold usam Array legado; map/filter retornam nova alocação de liberação explícita. Veja [funções e efeitos](FUNCOES-E-EFEITOS.md).

## Especialização genérica

Funções e structs genéricas da alpha.2 preservam os contratos anteriores. A instância de uma função global continua sem classe declaradora; chamar um template de dentro de um método não lhe concede acesso aos privados desse método. Campos de uma struct especializada pertencem à identidade nominal dessa instância. Tipagem, pureza e ownership locais são repetidos sobre cada corpo especializado.

Generics preservam os contratos own/borrow da alpha.6; não acrescentam transferência implícita: passar um `own` por uma função genérica legada continua sendo rejeitado. `Caixa<text>` aceita o mesmo text de vida externa do núcleo anterior; não amplia a garantia de vida. `Caixa<Array<int>>` com campo let continua legada; declare o campo own para obter um proprietário composto verificado. Leia [GENERICS.md](GENERICS.md) para os limites de instanciação e validação dos templates.

Não executar código de páginas ou arquivos não confiáveis com o runtime AOT irrestrito. O perfil restrito do navegador permanece como projeto futuro do plano.

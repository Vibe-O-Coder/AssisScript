Continuação: [pageframe](BIBLIOTECA-pageframe.md) consome o conjunto confirmado
e constrói layout/snapshot; [pagepresent](BIBLIOTECA-pagepresent.md) publica
desenho e projeção MSAA juntos no Windows. `document_instance()` identifica
a origem do conjunto. Flowpage não reavalia entradas a partir da geometria.

# flowpage — transações FS de página inteira, v1

`import "std/flowpage.assis";` Biblioteca opcional em AssisScript, dependente
de fluxstyle. Instalação: `--with flowpage`. Perfil **page-fs-256-v1**;
[exemplo 55](../exemplos/55_page_styles.assis). Não calcula geometria.

`try_new Page(source,max_nodes,input_capacity,max_bytes)` compila um recurso FS
imutável e reserva dois bancos de saídas/contextos. Confira null, is_open() e
diagnostic(). Aceita 1..256 elementos apresentáveis e 1..2048 índices de entrada
por nó. Fonte e avaliador mantêm os limites do [FS](BIBLIOTECA-fluxstyle.md).

`reservation(source_bytes,nodes,inputs)` retorna -1 para limites inválidos ou
`401000 + source_bytes + 2 * nodes * (20 + 4 * inputs) * 8` bytes. É reserva
conservadora de corpos solicitados: programa, controlador, bancos e um Style
transitório. Exclui cabeçalhos do alocador/RSS, Document, Inputs do chamador,
layout, SSC e recursos. Valida o limite antes da construção; recursos parciais
de construção fechada são liberados no drop. Não mantenha donos fechados vivos.

`input_index(flow,name)` resolve índices da revisão compilada. stage exige
Inputs com exatamente input_capacity posições. O host fornece contexto por nó,
inclusive largura descendente resolvida; não há leitura de geometria final/OS.

## Transação

1. `begin(document)` enumera todos os elementos apresentáveis da árvore
   validada, incluindo body e descendentes hidden. Exclui head/title/meta/script.
   Guarda instância e versão semântica; recusa capacidade insuficiente.
2. `stage(document,node,inputs)` prepara um nó enumerado, em qualquer ordem.
   Repetir um nó é erro. Nenhuma saída candidata fica disponível ao leitor.
3. `commit(document)` exige todos os nós preparados, nenhum erro e a mesma
   instância/versão semântica. Troca o índice dos bancos sem alocar/copiar,
   incrementa version() e publica todas as saídas juntas.

`refresh(document,inputs)` executa as três etapas com contexto comum. Uma
transação ocupada retorna 204 sem abortar o candidato anterior. `abort()`
descarta preparação, conservando saídas/contextos confirmados. Após erro de
chamada explícita, use abort antes de novo begin; refresh faz isso para sua
própria tentativa. Abort conserva diagnóstico; novo begin o limpa.

Falha de expressão/produtor/cota/alocação em qualquer nó impede o conjunto
inteiro. `diagnostic()` conserva código/span/UTF-16 do FS; diagnostic_node()
identifica o nó. Coordenador: 204 estado/identidade/incompletude/entrada,
401 reserva/alocação/capacidade, 304 célula compartilhada inconsistente;
esses erros têm span vazio. Não há publicação parcial.

Células node podem diferir. Células page exigem um valor efetivo igual em
todos os contextos, incluindo nós sem binding. Defaults, aliases e tipos são
resolvidos pelo schema compilado. O host fornece estado page a todos os nós;
esta biblioteca não é o armazenamento mutável de células da aplicação.

## Dirtiness e leitura

O cache compara identidade completa, versão semântica do Document e todas as
entradas normalizadas: presença/tipo/valor. Não usa hash ou dirty externo.
Sem mudanças, reutiliza saídas sem alocar Style. Entrada alterada reavalia
o nó inteiro; mutação semântica aceita invalida todos os nós. Não é cache
por vértice/propriedade. Buscas/comparações são limitadas por 256 nós e 2048
entradas, sem promessa de latência de UI. Ausência difere de zero presente.

evaluations() e cache_hits() contam trabalho da última preparação, inclusive
tentativa recusada. Cache candidato só passa a valer com commit; abort não
torna entradas falhas reutilizáveis. size(), node_at() e semantic_version()
descrevem o conjunto autoral confirmado. version() também cresce em um commit
sem novas avaliações. Contadores não são uma API de tempo de página.

`has(document,node,property)` e `value(...)` validam a árvore atual e a
identidade completa a cada leitura. value retorna Number(204,0) para ausência
ou identidade inválida. Remoção/navegação revoga saídas imediatamente. Nó novo
usa padrões até avaliação válida. ID textual não transfere saídas. Nó vivo
conserva últimas saídas após falha FS, junto à semântica atual; a biblioteca
nunca desfaz checked/disabled/hidden ou mutações já aceitas. node_at pode
retornar um ID removido do conjunto antigo: valide por has antes de consumir.

Document.semantic_version() cresce após append/texto/reparent/remoção aceitos,
inclusive no-op; falhas e reserva de slots não incrementam. Esgotamento recusa
mutações, sem wrap. O controlador mantém 64 bytes usando o campo de limite
que não era consultado após init; a quota permanece na Tree. nodes() continua
somente leitura, sem bypass público desse contador. close() é idempotente,
invalida leituras e libera programa/bancos; drop também libera sem close.
API de host local confiável: NodeIds/versões não são capacidades ou IPC.

## Integrações pendentes

O conjunto contém saídas autorais, sem layout, desenho, hit test ou ponte
assistiva. Após erro FS, o host precisa reaplicar saídas sobreviventes à
semântica atual e construir geometria coerente; se isso falhar, bloquear
acerto e informar o problema. A biblioteca não corrige o último quadro gráfico
automaticamente. Reader permanece bootstrap. SSC/quota de canais, foco/IME,
loader, inspector/LSP, catálogo visual, RSS e aceites continuam na fila.
Nenhum marco/gate é encerrado. Easy permanece por último.

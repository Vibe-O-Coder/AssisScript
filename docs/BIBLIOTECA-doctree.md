# std/doctree.assis — árvore de documento com orçamento

Unidade M1-ALLOC / E02-03 de 01/11/2026. Lógica inteiramente em AssisScript,
sem sintaxe nova, provider ou alteração de compilador. Dependências: buffers,
unicode e, transitivamente, owned. Exemplo: [41_document_tree_budget.assis](../exemplos/41_document_tree_budget.assis).

`Tree(instance,max_bytes,max_nodes,generation_limit)` possui uma árvore
ordenada de raiz única. Cada nó ocupa um slot da arena de bytes do BufferPool:
128 bytes de registro mais texto UTF-8. Os cinco links (pai, primeiro/último
filho, irmão anterior/próximo) usam identidades completas; o último word é o
kind positivo atribuído pela aplicação. O módulo não interpreta tipos HTDL,
atributos, modelos de conteúdo, entidades ou perfis. Não é um parser/DOM HTDL.

O registro privado contém 16 inteiros não negativos em little-endian. Não é
um formato público de arquivo ou IPC. Não guarda ponteiros. A arena genérica
`arena::Arena<T>` conserva seu contrato; esta árvore usa a arena de buffers
para cobrar os próprios registros reais junto ao texto, sem simular uma
contagem de objetos de tamanho arbitrário.

## Construção, identidade e limites

Construa com `try_new`, verifique null e `is_open()`. A recusa de alocação do
controlador retorna null; recusa nos controladores internos deixa a árvore
fechada. Não há resultado de erro alocado. Um controlador incompleto não pode
ser reaberto por reset; destrua-o e tente novamente. Configuração inválida é
erro de contrato 70/R001: instância/limite de geração positivos, bytes/nós não
negativos. `new` conserva sua alocação inicial fatal.

`NodeId(instance,slot,generation)` é Copy; o valor todo zero significa ausência
(`absent`). O host atribui instâncias positivas únicas entre documentos e
navegações. IDs velhos, forjados e de outro documento são rejeitados pelas
operações recuperáveis. IDs não são capacidades de segurança. Não há acesso
concorrente sincronizado nem ponteiros/visões de texto expostos.

O teto de nós limita slots históricos, incluindo aposentados. Uma remoção
recicla o slot com geração maior, ou o aposenta sem wrap. `reset(instance)`
exige instância estritamente maior, libera tudo e permite reutilizar o limite.

## Cobrança e transações

`used_bytes()` é a soma das capacidades dos buffers de nós: registro de 128
bytes e reserva de texto. Anexar cobra exatamente `128 + len(input)`.
Crescer texto exige espaço transitório para **todos os registros antigos mais
o candidato inteiro de 128 + tamanho novo**, antes de liberar o antigo.
Reduzir texto conserva capacidade e cobrança; apagar o nó libera ambas.

Exemplo com quota 400: raiz vazia cobra 128, filho com um byte cobra 129,
total 257. Crescer esse filho para 16 bytes exige 257 + 144 = 401 e falha;
15 bytes exigem 400 e passam, deixando cobrança final 271. Não se cobra
apenas a diferença entre capacidades. Checagens por subtração precedem somas.

Falha de append/set_text por quota, UTF-8 ou OOM preserva conteúdo, links,
identidades, ocupação e cobrança dos nós vivos. Append prepara payload e slot
antes de publicar links. A entrada é emprestada, copiada, nunca retida e não
pode apontar para texto interno por API pública. Reparent valida todos os
ancestrais antes de alterar links. Remoção de subárvore usa pós-ordem iterativa,
sem alocação ou pilha recursiva proporcional à profundidade do documento.

**Fora da quota:** índices/slots do BufferPool, controladores, cabeçalhos,
alinhamento, slabs/cache do alocador, pilha, fontes emprestadas, atributos e
outros recursos futuros. `prepare_nodes(n)` só prepara metadados e retorna
`buffers::Preparation`, com o mesmo progresso parcial da biblioteca buffers;
não reserva registros/texto nem garante append sob recusa do alocador.
Não há quota integral de documento/RSS, snapshot transacional de uma página
inteira, compactação de texto ou contrato de tempo constante nesta unidade.

## API

| Operação | Contrato |
| --- | --- |
| `try_append(parent,kind,input): Append` | Primeiro nó exige parent zero; demais exigem pai vivo. Anexa ao fim dos filhos. `Appended(NodeId)` ou `Rejected(code)` Copy. |
| `try_set_text(id,input): bool` | Copia UTF-8 válido, incluindo NUL. False não altera estado. Não normaliza/segmenta. |
| `try_reparent(id,parent): bool` | Move subárvore ao fim dos filhos; rejeita raiz, IDs inválidos e ciclos. Mesmo pai retorna true preservando ordem. Sem alocação. |
| `erase_subtree(id): bool` | Destrói nó e descendentes, invalida IDs e devolve quota. ID inválido: false. Sem alocação. |
| `root()`, `contains(id)`, `size()`, `slots_used()`, `used_bytes()`, `is_open()` | Consultas. Raiz ausente é zero, slots_used inclui aposentados e preparados. |
| `parent`, `first_child`, `last_child`, `previous_sibling`, `next_sibling`, `kind`, `text_size`, `node_capacity` | Exigem ID vivo; ausência de relação retorna NodeId zero. node_capacity inclui registro. |
| `text_byte(id,index): byte` | Exige índice dentro do texto visível e ID vivo, caso contrário 70/R001. |
| `prepare_nodes(n)` | Mesmo contrato de prepare_slots; árvore incompleta/fechada retorna Incomplete(1,0). |
| `close()` | Repetível, libera payload/metadados, invalida IDs, zera raiz e contadores. |
| `reset(instance): bool` | Fecha e reabre com instância nova, mantendo limites. Falha não altera estado. |

Precedência de erros de append: fechado (1); pai/raiz/kind inválidos (5);
quota/comprimento (4); UTF-8 inválido (6); em seguida slot esgotado (2) ou
alocador (3). Alterar texto retorna bool. Consultas inválidas são erro de
contrato, não uma tentativa de recuperação. Destruição normal do proprietário
libera tudo; não há drops de código de página nesta biblioteca.

Consultas de bytes/links passam pelo índice O(log slots) do pool; copiar texto
repete esse custo por byte. Reparent percorre ancestrais e apagar subárvore
visita seus nós, sem recursão do documento. Desempenho para documentos grandes
ainda exige medição e otimização. Os limites de profundidade do futuro parser
permanecem independentes.

Evidências, plataformas e limites: [relatório M1](relatorios/2026-11-01-m1-arvore-orcamento.md).

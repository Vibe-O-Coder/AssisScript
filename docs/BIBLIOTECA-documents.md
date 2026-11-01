# std/documents.assis — documentos candidatos com armazenamento cobrado

M1-ALLOC / E02-03, 01/11/2026. Implementação em AssisScript, dependência
`doctree` (transitivamente `buffers`, `owned`, `unicode`). Exemplo executável:
[42_document_candidate.assis](../exemplos/42_document_candidate.assis).

`Store(max_bytes,max_nodes,generation_limit)` conserva um documento ativo e
um candidato sob o mesmo teto. `begin(instance,source)` copia a fonte UTF-8;
a aplicação constrói a árvore genérica pelo candidato. `abort(instance)`
descarta todos os recursos do candidato, inclusive metadados já preparados.
`commit(instance)` exige candidato aberto, instância correspondente e raiz;
transfere o candidato para ativo e destrói o anterior, sem nova alocação.
O chamador valida sintaxe e semântica do seu formato antes de commit. Esta
biblioteca não interpreta HTDL, atributos, layout ou código de página.

## O que entra no teto

`storage_bytes()` soma os corpos solicitados ao alocador nativo, inclusive a
palavra de vtable, e as capacidades dos buffers. Fonte, registro/texto dos
nós, controladores, slots preparados/ocupados/aposentados e todos os nós do
índice contam. Crescimento exige espaço para o buffer antigo **e o candidato
inteiro** antes da troca. Descartar candidato libera sua fonte/árvore/índice.

| Recurso nativo v1 | Bytes cobrados |
| --- | ---: |
| Store | 72 |
| Document | 64 |
| Tree | 48 |
| BufferPool | 112 |
| OwnedArray de slots | 32 |
| Slot | 56 |
| ArrayNode do índice | 32 |
| Fonte própria | Comprimento UTF-8 |
| Buffer de nó | Capacidade: ao menos 128 + texto UTF-8 |

Um documento aberto vazio custa 256 bytes; a primeira raiz sem texto adiciona
216 (registro 128 + Slot 56 + ArrayNode 32). Store + esse documento custam
544. Com teto 800, cabe outro documento vazio de 256 bytes, mas sua raiz
será recusada. Somente a contagem de payload não capturaria esse limite.

Os tamanhos são do layout nativo v1 de palavras de 64 bits e não são uma ABI
de persistência. A saída `ir` informa `layout` e `allocationBytes` nas
construções; os testes conferem as cobranças contra os argumentos reais
selecionados para alocação pelos emissores. Alterar um layout exige atualizar
contrato, cobrança e evidência. Não há sintaxe nova.

O teto **não mede RSS**: cabeçalhos/alinhamento do alocador, slabs/cache,
pilha, código e fonte emprestada pelo chamador não entram. Atributos, imagens,
fontes gráficas e recursos futuros não são armazenados por este módulo e
exigirão integração própria. Não há quota total de processo ou sandbox.

## Construção e falhas

Use `try_new` e confira null e `is_open()`. A alocação inicial de `new`
continua fatal. Store exige max_bytes >= 72, max_nodes >= 0 e limite de
geração positivo; Document exige instância positiva e limites não negativos.
Parâmetros inválidos são erros de contrato 70/R001. Chamada explícita de init
fora de construção é rejeitada pelo frontend (A001).

Document direto pode ficar fechado quando fonte, quota ou alocação falham;
seus recursos parciais são destruídos antes de init retornar. Um Document
fechado sem recursos custa seu controlador de 64 bytes. Não há reabertura.
Store valida quota/UTF-8 antes de construir; falha não altera ativo, cobrança,
candidato ou última instância aceita. Não se aloca para retornar erro.

| API de Store | Resultado |
| --- | --- |
| `begin(instance,source): int` | 0 sucesso; 1 fechado; 7 já há candidato; 5 instância não crescente; 4 teto insuficiente; 6 UTF-8 inválido; 3 recusa do alocador. Esta é a precedência. |
| `candidate(): borrow mut(self) Document` | Exige candidato. A árvore pode crescer só dentro do saldo reservado no início. |
| `active_document(): borrow(self) Document` | Exige ativo; leitura. |
| `commit(instance): bool` | False preserva os dois documentos; true libera o ativo anterior. Uma raiz genérica não comprova conformidade de formato. |
| `abort(instance): bool` | False para instância diferente/ausente; true libera candidato completo. |
| `storage_bytes`, `has_active`, `has_candidate`, `is_open` | Consultas. |
| `close()` | Repetível, descarta os dois documentos e conserva apenas Store (72 bytes). Não reabre. |

Instâncias aceitas crescem estritamente, inclusive após abort. Uma tentativa
recusada não publica IDs e não consome instância. O host atribui instâncias
únicas entre Stores e navegações; o módulo não gera uma identidade global.
Não há wrap no máximo int. NodeId não é capacidade de segurança.

Document oferece `try_append`, `try_set_text`, `try_reparent`, `erase_subtree`
e `prepare_nodes`, seguindo os resultados da árvore; `nodes()` retorna uma
visão somente para leitura. `source_size`/`source_byte` leem a cópia própria,
com NUL permitido. `instance`, `has_root`, `storage_bytes`, `is_open` e `close`
completam a API. Fechar libera fonte e árvore; operações recuperáveis passam
a recusar. Índice inválido ou visão de documento fechado causa 70/R001.

Empréstimos bloqueiam mutação/navegação enquanto estiverem vivos. Nenhum
ponteiro interno escapa. Não há sincronização entre threads ou callbacks de
página. O saldo reservado ao candidato não aumenta quando o ativo é liberado;
o ativo só é exposto para leitura. Uma tentativa futura recebe o saldo atual.

Preparação de nós mantém o progresso parcial no candidato, dentro do teto;
abort é o rollback completo. Recusa de append/crescimento mantém nós vivos,
links, bytes e cobrança. Commit/abort/close não alocam pela biblioteca.

Testes e limitações por sistema no
[relatório desta unidade](relatorios/2026-11-01-m1-documento-candidato.md).

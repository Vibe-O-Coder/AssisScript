# Extração HTDL para o índice local

`std/htdlsearch.assis` recebe uma árvore HTDL validada pelo parser.
`Page(document, max_text, max_links, max_link_bytes)` copia texto do corpo
visível e alternativas de imagens informativas. Colapsa espaços ASCII e
insere separação entre blocos. Preserva concatenação nos nós `text` inline.
Os offsets do índice correspondem ao texto resultante em UTF-8. Cabeçalho,
conteúdo oculto e atributos de valores de controles ficam fora do corpus.

`content_bytes()` empresta o texto. `link_count()` e `link(i)` enumeram
as referências de links visíveis na ordem da árvore, incluindo fragmentos
quando presentes. Os links são dados. Cabe ao consumidor aplicar política
de navegação e concessão antes de tentar resolvê-los. A biblioteca não lê
arquivos, resolve URLs, decodifica imagens ou executa scripts.

A extração é síncrona. O máximo é 16 KiB de texto, 256 links e 64 KiB de
bytes de endereços. `status()` devolve 0, H204 para contexto ou limites
inválidos e H401 para orçamento excedido ou alocação recusada.
`current(document)` compara a instância e a revisão semântica.
Falha de extração descarta o lote no [exemplo 71](../exemplos/71_search_index.assis).

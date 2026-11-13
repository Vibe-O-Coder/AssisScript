# searchsegments — índice por faixas de documentos

O [exemplo 71](../exemplos/71_search_index.assis) aceita `build-segmented`,
`apply-segmented` e `query-segmented and|or|phrase TEXTO [OFFSET]`.
Os dois comandos de escrita também aceitam o sufixo `-htdl`. Os lotes
conservam `ID<TAB>CONTEÚDO` e a remoção com ID sem texto. Envie as faixas
em ordem crescente. Dentro de uma faixa, os IDs podem vir em qualquer
ordem e a última operação sobre um ID prevalece.

Cada faixa cobre 4.096 IDs, começando em 1–4.096 e terminando em
61.441–65.535. São até 65.536 ocorrências e 4 MiB de termos por faixa.
O arquivo `webassis.asis` tem um cabeçalho de oito bytes
`41 53 49 53 01 10 00 00`, seguido por 16 frames de estrutura
[ASIX 1](BIBLIOTECA-searchindex.md) com IDs locais. O estado inicial do
FNV-1a de cada frame é `2166136261 XOR número_da_faixa`, com número
de 1 a 16. A leitura valida comprimento, ordem, normalização, ocorrências,
checksum de cada frame e EOF. O checksum cobre corrupção acidental.

A consulta libera uma faixa antes de abrir a próxima. Conserva apenas as
primeiras 256 posições globais, por frequência decrescente e ID crescente,
e entrega os resultados após verificar o arquivo completo. A escrita
completa usa o mesmo lock, flush, troca atômica e recuperação do índice
local. Um candidato interrompido fica em `webassis.asis.pending` e a
próxima escrita o descarta. `apply-segmented` recompõe um segmento por vez
e remove ocorrências obsoletas ao publicar. Um erro em uma faixa posterior
preserva o arquivo anterior.

O formato separado permite manter arquivos ASIX 1 existentes ao lado da
variante segmentada. Para gerar ASIS a partir do corpus de origem, envie
os lotes novamente em ordem de faixa. A operação reescreve o arquivo
completo e pode exigir espaço para os dois arquivos. Segmentos imutáveis
com merge seletivo, compressão, migração automática e testes de perda
física de energia permanecem pendentes.

`std/searchsegments.assis` oferece `part_of`, `local_id`, `new_part`,
`write_header`, `read_header`, `check_end` e `query`.
`query` recebe um `File` posicionado no início, termos UTF-8, modo 1 a 3,
offset e buffer de `searchindex::Hit`. Um retorno negativo indica falha.
O [serviço HTTP local](BIBLIOTECA-searchservice.md) usa esse caminho
quando iniciado com `--segments`.

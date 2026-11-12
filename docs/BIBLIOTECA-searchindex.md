# Índice local posicional

`std/searchindex.assis` implementa um índice invertido em AssisScript.
`Index(max_document_id, max_postings, max_term_bytes)` reserva os três limites
antes de aceitar dados. Os limites máximos são ID 65.535, 524.288 ocorrências
e 16 MiB de bytes de termos. Cada documento fornecido a `upsert` pode ter até
16 KiB de UTF-8 e cada termo até 128 bytes. Um ID positivo identifica o documento
durante substituições. `remove` invalida suas ocorrências. Uma falha de
`upsert` preserva a versão anterior no índice em memória.

`seal` descarta ocorrências de gerações antigas e ordena por hash, ID e
ordinal. Os bytes de termos obsoletos são recuperados ao abrir o snapshot
compactado. `query` compara também os bytes dos termos em cada colisão.
Modo 1 exige todos os termos distintos, modo 2 aceita qualquer um e modo 3
exige termos adjacentes, inclusive repetições. A frequência soma as ocorrências
pertinentes ou as ocorrências da frase. Empates usam ID crescente. Cada
resultado tem ID, frequência e primeiro offset em bytes do texto indexado.
O vetor de saída e o offset delimitam as primeiras 256 posições ordenadas.
A consulta aceita até 2.048 bytes e 16 termos.

A análise separa alfanuméricos ASCII da pontuação e de um conjunto declarado
de espaços e pontuação Unicode. A comparação ignora caixa em ASCII e nas
letras Latin-1 correspondentes. Preserva os outros bytes, incluindo formas
Unicode compostas e decompostas. O perfil ainda cobre consultas exatas sobre
os termos UTF-8 preservados.

## Snapshot ASIX 1

Todos os inteiros usam 32 bits sem sinal em little-endian. O cabeçalho contém
`ASIX`, versão, total de documentos, total de ocorrências e comprimento
integral. Seguem os IDs crescentes, inclusive de documentos vazios. Cada
ocorrência armazena ID, ordinal, offset original, comprimento e bytes
normalizados. Um FNV-1a de 32 bits cobre os bytes anteriores ao rodapé.
A leitura verifica contagens e orçamento antes de alocar, comprimento exato,
checksum, ordenação, UTF-8, limites e sequência de offsets por documento.
O formato destina o checksum à detecção de corrupção acidental.

`write` exige o índice selado. `read` recebe um objeto novo e um `File` já
aberto. Uma leitura recusada deixa o candidato indisponível. Os estados da
biblioteca são 0 sucesso, 1 argumento/UTF-8, 2 cota, 3 snapshot inválido,
4 I/O/alocação e 5 estado incompatível. `query` devolve erros negativos.

## Uso pelo exemplo 71

Compile [71_search_index.assis](../exemplos/71_search_index.assis) e execute em
um diretório local dedicado e controlado pelo usuário. Use um diretório
distinto por corpus. `build` substitui o corpus por inteiro. `apply` abre
o snapshot e aplica o lote de stdin. Envie uma linha UTF-8 `ID<TAB>TEXTO`
por documento, ou somente o ID para removê-lo. `build-htdl` e `apply-htdl`
recebem HTDL 0.1 completo na coluna de texto, em uma linha por documento.
`query and|or|phrase TEXTO [OFFSET]` lê o snapshot e imprime até 10 linhas
`ID FREQUÊNCIA OFFSET_EM_BYTES`. O [extrator HTDL](BIBLIOTECA-htdlsearch.md)
define os offsets do texto derivado.

```text
search-index build
1	Leitura local e busca persistente
2	Busca persistente após reinício
search-index query phrase "busca persistente"
```

No exemplo acima, as duas linhas de dados chegam via stdin. Feche o fluxo
para confirmar o lote. O exemplo mantém um lock exclusivo por diretório para
escrita, prepara `webassis.asix.pending`, faz flush e publica por substituição
atômica. Em Linux, sincroniza o diretório após a troca. Em Windows, usa
`MoveFileExW` com `WRITE_THROUGH` pelo runtime. O código 8 indica que o lock
falhou. O código 9 indica que a troca ocorreu e a sincronização posterior
falhou. Consulte o snapshot antes de repetir nessa situação. Em Windows uma
substituição pode falhar enquanto outro processo mantém o arquivo aberto.
As entradas anteriores permanecem consultáveis após uma troca recusada.

O snapshot é carregado inteiro. A aplicação de lotes exige espaço para a
versão antiga e a candidata durante a troca. A liberação do lock após kill
e a preservação do arquivo anterior sob falha de gravação têm testes nativos.
Backup, migração entre versões, segmentos maiores que RAM, ranking por
relevância, crawler, serviço, integração no Browser e teste de perda física
de energia continuam abertos.

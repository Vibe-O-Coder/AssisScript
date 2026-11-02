# htdl — parser HTDL bootstrap

`import "std/htdl.assis";` depende de documents/doctree/buffers/owned/unicode.
Implementação em AssisScript, sem provider adicional ou sintaxe nova.
O [exemplo compilável](../exemplos/43_htdl_bootstrap.assis) abre e consulta
um documento do perfil **viewer-local-bootstrap-v1**. Não cria janela.

## Contrato e ativação

`load(borrow mut store:documents::Store, instance:int, borrow source:slice<byte>):Diagnostic`
valida UTF-8 e o perfil antes de ativar. `code==0` significa documento válido
e commit concluído. Uma falha depois de begin aborta o candidato inteiro;
o documento ativo e outras instâncias permanecem válidos. Um candidato
preexistente não é abortado por load. Instâncias atribuídas pelo host devem
ser positivas e crescentes; uma tentativa que abriu candidato consome seu ID
mesmo se o parser falhar. Isso não é autorização de acesso ou origem.

Tipos aceitos: document/head/title/body/container/paragraph/text/heading/button.
A gramática é a do [snapshot HTDL 0.1](ecossistema/referencias/htdl-drafts-2026-10-29/docs/02-htdl-0.1.md),
restrita pelo [perfil congelado](ecossistema/PERFIL-VISUALIZADOR-V1.md).
Há BOM opcional, comentários, três formas de valor de atributo, entidades
nomeadas/numéricas decodificadas uma vez e normalização CR/CRLF para LF.
NUL, controles proibidos, UTF-8 inválido, tags/atributos repetidos, entidades
inválidas, versões desconhecidas e modelos de conteúdo inválidos são recusados.
IDs são únicos e classes são normalizadas mantendo a primeira ocorrência.
`level` usa um dígito de 1 a 6. Nenhuma URL/rede/script é executada.

O parser preserva texto decodificado e intervalos da fonte própria. A árvore
mantém espaços para inspeção; colapso de texto entre fragmentos é trabalho da
apresentação. Não implementa renderização, foco, teclado ou ponte acessível.
Nome de button exige texto visível não vazio ou a11y-label não vazio;
hidden/disabled são atributos validados, sem interação nativa nesta biblioteca.

## Diagnósticos e limites

`Diagnostic` é Copy: code, start/end em bytes; line/column e
end_line/end_column UTF-16 base 1, fim exclusivo. Códigos numéricos correspondem
a H101, H102, H200–H206 e H401 do perfil. Retorna o primeiro erro; não há
recuperação para edição de documento inválido. Falhas de Store/instância,
quota ou alocador retornam H401. Esse código não distingue OOM de quota.

Antes do parsing: fonte até 1 MiB. Durante parsing: até 20.000 nós semânticos
(elementos e fragmentos de texto), profundidade 256, 64 atributos por elemento
e 64 KiB decodificados por valor. A lista permitida tem apenas dez atributos;
repetições/atributos desconhecidos podem falhar antes do teto de 64.
Uma guarda operacional adicional limita a normalização de classes a oito
milhões de unidades de comparação/varredura, com H401; não muda a gramática.
Esses valores não são promessa de latência ou limites de processo.

Parsing, validação e percursos da árvore são iterativos. IDs são conferidos
com heapsort, sem tabela hash sujeita a colisões; a duplicata reportada é a
segunda ocorrência na fonte. Há O(n log n) comparações de IDs, cada uma
proporcional ao prefixo comum; classes têm guarda de trabalho explícita.

## Armazenamento e consulta

Elementos (kind interno 1), fragmentos textuais (2) e atributos (100+chave)
usam registros reais da mesma doctree. Cada payload começa com 16 bytes ASCII
internos, dois offsets em oito nibbles codificados como 48..63, seguidos do
valor UTF-8. Essa representação é local, sem ABI persistente ou de página.
Os spans de elemento cobrem abertura a fechamento; os de atributo cobrem
nome/valor; os de texto cobrem a sequência original antes da decodificação.
Comentários e BOM permanecem na fonte; não criam nós.

O teto de documents inclui fonte, árvore, atributos, spans e metadados.
`begin_reserved` reserva também Parser (96 bytes de corpo nativo v1), scratch
de `source_size+16` bytes e vetor de `min(20000, source_size/11+1)` int64s.
`workspace_bytes` expõe essa reserva. Ela é conservadora e permanece retirada
do teto do documento depois da liberação do parser. Um ID exige mais de onze
bytes de fonte, e não há remoção/reciclagem durante parsing. A ordenação usa
slots com geração 1 somente dentro dessa construção.
Cabeçalhos/alinhamento/slabs/RSS, pilha, entrada emprestada e buffers de I/O
do chamador permanecem fora. Não é quota total de processo.

Consultas exigem uma árvore produzida por load com sucesso. `kind` devolve
1..9 para os tipos na ordem acima; `first_element`/`next_element` ignoram
atributos e fragmentos. `find_id` faz percurso O(n) e retorna NodeId nulo
quando ausente. `attribute(tree,node,key)` usa chaves: type=1, version=2,
lang=3, level=4, id=5, class=6, hidden=7, disabled=8, action=9, a11y-label=10.
`value_size`/`value_byte`/`value_equals` leem o valor decodificado;
`span_start`/`span_end` leem os offsets originais. Views emprestadas impedem
reload mutável. IDs antigos não pertencem ao documento de outra instância.

Há edição transacional do subconjunto bootstrap descrita abaixo. Não há seletor
CSS, SDK htdl_v1 para página, loader de recursos, HTML, FS/SSC ou conformidade
completa HTDL 0.1. M3/G1 ficam abertos.
Corpus e testes: [test-htdl-parser.py](../tests/test-htdl-parser.py), com
XML ElementTree como oráculo independente somente na sintaxe em comum;
Unicode U+FFFF usa o escalar Python, pois XML o proíbe e HTDL o permite.

## Consultas e alterações transacionais

`query(tree,type_id,token,after)` percorre elementos em pré-ordem. Tipo 0 e
token vazio são curingas; tipos 1..9 e uma classe exata são suportados.
`after` nulo inicia o percurso; cursor expirado é recusado. Não há seletores
CSS compostos. Retorna NodeId ausente tanto em fim/argumento inválido como na
guarda de oito milhões de comparações de classes; não promete busca indexada.

`stage(store,instance,source,temporary_bytes)` faz a mesma validação de `load`,
mas deixa o candidato validado sem ativar. O chamador deve commit/abort.
Uma falha aborta somente o candidato criado pela chamada. A reserva adicional
de 0..2 MiB cobra buffers temporários do chamador junto com o parser. Não
transforma o teto em quota de processo; precisa contabilizar separadamente
Reader/View, corpos do shell, buffers externos e overhead do alocador.

`try_new htdl::Patch(document,start,end,replacement)` constrói uma fonte própria
até 1 MiB substituindo `[start,end)` em bytes. Consulte proprietário não nulo
e `is_open()`. Ranges inválidos e UTF-8 partido são recusados; sintaxe/semântica
são validadas posteriormente por stage. Inserção e remoção de elementos usam
spans da árvore validada. Texto literal exige escapar `&`/`<`; a API de range
recebe **fonte HTDL**, não texto a ser escapado automaticamente.

`set_boolean(document,node,key,value)` produz Patch para hidden=7 ou disabled=8,
inserindo o atributo se ausente. Exige nó vivo de elemento; aplicar disabled a
paragraph continua produzindo erro semântico, sem ativação. `Patch::instance()`
impede reaplicar uma edição derivada de documento antigo. Cada transação muda
a instância de todos os NodeIds: igualdade de ID textual não preserva slots.
Não é edição incremental nem recuperação de fonte inválida para editor.

Para coordenar árvore, foco e acessibilidade, use `reader::Session` conforme
[contrato](BIBLIOTECA-reader.md), [exemplo 46](../exemplos/46_reader_transactions.assis)
e [testes](../tests/test-reader-transactions.py).

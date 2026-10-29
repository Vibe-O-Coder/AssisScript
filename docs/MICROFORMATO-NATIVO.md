# Prova nativa de microformato — M0

Perfil de teste `nested-div-probe-v1`, não uma versão HTDL.
O fonte está em `tests/fixtures/htdl-core.assis`. Ele aceita sequências de
`<div>...</div>` aninhadas, texto UTF-8 e texto fora de elementos, inclusive
documento vazio e NUL. Atributos, comentários, tags abreviadas e nomes de tag
diferentes são rejeitados. Entidades não são interpretadas; `&amp;` é texto
literal. O formato não substitui a gramática real HTDL.

O leitor limita entrada a 1 MiB, 20.000 nós e 4.096 níveis. Parsing é iterativo;
os nós guardam offsets e índice do pai. Erro 1 indica limite; 2, UTF-8 inválido;
3, sintaxe; 4, aninhamento. A saída parcial deve ser descartada após erro.
Erro de leitura retorna 2 no processo, com `ERR read`; erro de parsing retorna
1, com `ERR <código>`. OOM continua fatal: os limites lógicos não são quotas
recuperáveis de heap ou CPU.

A contagem de palavras usa letras ASCII e bytes não ASCII como componentes,
com case folding apenas ASCII. Todos os hashes são deliberadamente forçados
a colidir para conferir comparação exata. Isso prova correção dos resultados,
sem resistência de custo a entradas hostis. Não há índice multidocumento,
ranking, crawler, persistência ou análise linguística Unicode completa.

O processo imprime número de nós, termos distintos e ocorrências de `assis`
e `htdl`; quando há nós, imprime pai do primeiro, pai do último e validade do
intervalo do último. Essa interface é exclusiva do corpus de teste.

`tests/test-htdl-readiness.py` compara entradas geradas a oráculos de palavras
e árvores construídas em Python, testa limites exatos/excedidos e gera os cinco
formatos nativos. Executa somente o destino do host. Também demonstra que código
`safe` pode escrever em arquivo próprio de teste e que o compilador aceita
laço infinito; isso não é fronteira de autoridade para páginas remotas.

Resultados e publicação: [relatório M0](relatorios/2026-10-29-m0-microparser.md).

# M7 — Busca local persistente

12/11/2026, America/Fortaleza. Base pública
`b833e8182eb0c63d7e0fc58754decd5012220a5f`, confirmada com
`git ls-remote`. Branch `work/ecosystem-2026-11-11`, cópia isolada
`work/eco-70-20261111`. IDs E09-01/02/03/05 e E10-01/03/04.
**50,40% → 54,30%, 0/5 gates.** A meta de 70% continua a 15,70 pontos.

## Entrega

A contagem de termos em um documento evoluiu para consulta a um índice
invertido com IDs e posições de vários documentos. O [exemplo 71](../../exemplos/71_search_index.assis)
compila e consulta lotes de texto ou HTDL, aplica substituições e remoções,
e reabre o snapshot em outro processo. AND, OR e frases retornam até dez
resultados por página no CLI. A pontuação soma frequência, com desempate
por ID. O índice verifica os bytes do termo após buscar por hash.

[searchindex](../BIBLIOTECA-searchindex.md) define o formato ASIX 1,
limites, offsets e códigos de falha. A leitura verifica comprimento exato,
checksum, identidade, ordenação, termos normalizados e ordinais/posições por
documento. [htdlsearch](../BIBLIOTECA-htdlsearch.md) extrai texto visível e alt,
e entrega links como dados para um consumidor. O parser 0.1 valida o documento
antes da extração. Cabeçalho, valores de controles e conteúdo oculto ficam
fora do texto indexado. A implementação permanece em AssisScript.

O CLI mantém uma trava exclusiva para escritores, arquivo candidato separado,
flush, troca atômica e recuperação do arquivo pendente. Linux também solicita
flush do diretório. No Windows a troca usa o sinalizador WRITE_THROUGH do
runtime. O retorno após uma falha tardia de flush distingue arquivo já trocado
de troca recusada. O módulo e o extrator entraram no catálogo opcional e na
seleção transitiva do instalador.

## Evidência

A suíte independente gera 10.000 documentos com seed 187 e valida os 65.058
postings, inclusive offsets UTF-8, contra um modelo Python. O arquivo de
1.526.021 bytes e seu SHA coincidem em Windows/Linux x64 e em ambos os modos
do compilador. O modelo confirma consultas e paginação, mutação e remoção
após reinício, repetição em frases e colisão real de FNV-1a. O teste de HTDL
verifica entidades, texto inline, alt, exclusão de valores/ocultos, links,
cota de extração e atomicidade de lote inválido.

Os testes recusam truncamento, tamanho forjado, versão desconhecida,
corrupção, IDs inválidos e ordinal duplicado em hashes diferentes.
Um escritor concorrente é recusado enquanto um leitor ainda consulta a versão
anterior. O teste mata o escritor, coloca um arquivo pendente parcial e
confirma recuperação. Linux também força uma escrita parcial com RLIMIT_FSIZE.
A tentativa de preparar o índice onde o nome reservado é um diretório falha
sem substituir o snapshot nos dois hosts.

Comandos principais, com ASSIS_BIN apontando para o compilador reconstruído:

```text
python tests/test-searchindex.py
python tools/verify-local-resource-install.py --confined --search-forms --output build/session/install
python tools/validate-examples.py --output build/session/examples.json
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py --check
```

[Resultados Windows](../ecossistema/evidencias/ecosystem-2026-11-12/search-windows.json) ·
[Resultados Linux](../ecossistema/evidencias/ecosystem-2026-11-12/search-linux.json) ·
[Matriz e hashes](../ecossistema/evidencias/ecosystem-2026-11-12/summary.json).
As amostras de latência incluem criação do processo e reabertura/verificação
do arquivo. O conjunto pequeno de amostras registra os valores observados,
com a medição de p95 do marco completo ainda pendente.

## Pontos e limites

E09-01/02 e E10-01 passaram de 1 a 2. E09-03/05 e E10-03/04 passaram de 0
a 2. Os sete critérios refletem um perfil local limitado. E09-04, E10-02 e
E10-05 conservam os estados anteriores. A avaliação requer o conjunto maior
que RAM, segmentos/merge sob falha, backup/migração, ranking em corpus
rotulado, crawler e serviço integrado para avançar. O teste de kill difere
do aceite de perda física de energia. macOS e ARM64 continuam sem execução
nativa desta unidade. O [relatório de formulários e gates](2026-11-12-m3-formularios-visuais.md)
mantém a fila restante.

## Publicação

O destino desta unidade é [Vibe-O-Coder/AssisScript](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-11).
O histórico Git identifica a revisão do relatório. O adendo da rodada
registra o resultado da conferência do remoto.

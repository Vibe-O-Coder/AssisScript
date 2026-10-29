# M0 parcial — reconciliação da prova de microformato

Data: **29/10/2026**. IDs **E07-01/E10-01**, evidência limitada de **E02-05**.
Marco **M0 aberto**; nenhum gate promovido. Base
`9c09baf934eb2ae6a73dd7a15df4d8fa3c30717f` (coleções, PR #5), branch
`work/m0-microparser-2026-10-29`, remoto Vibe-O-Coder/AssisScript.

## Problema e resultado

A baseline citava um microparser e uma prova de contagem de palavras que
permaneciam locais. Esta unidade publica os fontes/testes revisados dessa
continuação, sem reaproveitar seus JSONs históricos ou modificar o compilador.
O perfil real é `nested-div-probe-v1`: div aninhado, texto UTF-8 e nenhum
atributo/comentário/escape. Não é gramática, parser ou conformidade HTDL.

O fonte percorre entrada iterativamente, armazena índices de pais e offsets,
aplica limites de bytes/nós/profundidade e retorna códigos de parsing.
A contagem de palavras compara bytes após case folding ASCII, mesmo quando
todos os hashes colidem. É uma prova em um documento, sem busca multidocumento.
Antes, a branch não tinha esses programas; depois, há reprodução pública
positiva/negativa em dois sistemas. Nenhum recurso foi declarado ausente por
inspeção: os programas executam usando o compilador atual sem mudança nativa.

Foram assumidos da continuação local somente `tests/fixtures/htdl-core.assis`
e `tests/test-htdl-readiness.py`. O teste recebeu dois métodos novos com
limites exatos, sintaxe explicitamente não suportada, UTF-8 hostil e 40 árvores
geradas com oráculo independente de construção. A pasta original conserva seus
arquivos de auditoria e resultados históricos, sem incorporá-los como execução
desta sessão.

## Arquivos e contrato

Os dois fontes citados, `tools/validate-microformat.py`,
`docs/MICROFORMATO-NATIVO.md`, este relatório, evidências e progresso em
`docs/ecossistema/`, integração em Makefile/CI/runner nativo e manifesto.
O documento de contrato registra erros, cobertura e limitações. Não há nova
API de produto, sintaxe, provider ou versão de pacote.

Limites inclusivos: 1 MiB, 20.000 nós e 4.096 níveis. OOM permanece fatal;
esses limites não são quotas de heap/CPU. Entidades permanecem literais;
texto fora de elementos e NUL são aceitos pelo perfil de teste.
Colisões forçadas comprovam resultados exatos, sem prometer custo resistente.

## Verificação desta unidade

Os candidatos reconstruídos na unidade imediatamente anterior foram mantidos
com os mesmos bytes; não há alteração do compilador ou stdlib nesta unidade.
Windows x64: SHA-256
`da249e894a274f8d8f2fd72b98744a6fe39a190b60a44b7fc8648a0321a75244`.
Linux x64/WSL: SHA-256
`8cb653df1dfc063e4e2645cd70e8e3922b58c78141d3d6c7ce3011499b2b81ec`.
Os hashes foram conferidos nesta rodada, sem atribuir testes anteriores à prova.

```powershell
$env:ASSIS_BIN=(Resolve-Path build/assis-m0-owned.exe).Path
python tools/validate-microformat.py --output build/micro-validation/windows-x64.json
```

```sh
ASSIS_BIN="$PWD/build/assis-m0-owned-linux" python3 tools/validate-microformat.py --output build/micro-validation/linux-x64.json
```

**8/8 métodos passaram em Windows e 8/8 em Linux, retorno 0, sem dispensas**.
Os testes usam otimizado/referência, saída exata e debug sem vazamentos.
Cobrem 5.000 irmãos, 4.096 níveis, erros de sintaxe/aninhamento/UTF-8,
limites excedidos e exatos, 32 entradas de palavras e 40 árvores geradas.
São gerados os cinco formatos em ambos os modos; só Windows/Linux x64 são
executados nativamente. A prova de autoridade escreve apenas em arquivo
temporário próprio e confirma que `safe` permite arquivo e aceita laço infinito
na compilação; não executa esse laço.

Evidências: `docs/ecossistema/evidencias/m0-microparser-2026-10-29/`, com
JSONs por host, hashes de fontes/candidatos/logs e saída integral das suítes.
`python tools/report-ecosystem-progress.py`, modo `--check`, gerador de
manifesto e seu `--check`, e `git diff --check` conferem a parte documental.

Execução macOS/ARM64, conformidade HTDL/FS/SSC, arena geracional, janela,
isolamento, busca persistente/multidocumento, falhas de leitura injetadas, OOM,
soak e distribuição: **not-run**. A CI foi integrada, sem afirmar aprovação
remota. A complexidade sob colisões permanece uma limitação explícita.

## Régua, publicação e continuidade

**20,10% → 20,10%; 0/5 → 0/5 gates**. E07-01/E10-01 permanecem nível 1;
E02-05 também permanece nível 1. Suas fontes locais são complementadas por
evidência rastreável nova; o microformato não recebe crédito de HTDL real.
Histórico completo acrescentado, pesos e trilha antiga preservados.

Publicação normal: commit/push da branch indicada e PR incremental sobre a
branch de coleções; SHA remoto conferido no encerramento. O SHA deste relatório
é consultável por `git log --follow -- docs/relatorios/2026-10-29-m0-microparser.md`.
Push não significa CI aprovada, merge ou release.

Próxima tarefa: contratos mínimos do visualizador/ponte/runtime de página,
com referência versionada dos rascunhos; arena com categoria, instância,
geração e oráculo independente é a próxima fundação funcional de M1.

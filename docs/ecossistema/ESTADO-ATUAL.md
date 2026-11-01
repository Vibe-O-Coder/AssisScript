# Continuidade verificada — AssisScript e ecossistema

## Estado de continuidade — 01/11/2026

Leia o [índice atual](ESTADO-ATUAL.md). A pasta original ainda está no
planejamento `1ed22f5`, com alterações alheias preservadas. Base desta unidade:
`ebd3185ae952a85c64cb2a83cd014ac07c0e8c7f`, branch
`work/m3-htdl-parser-2026-11-01`, PR de rascunho #17 aberta/sem merge,
com SHA remoto conferido pelo conector/API antes do desenvolvimento.

Continuação em `AssisScript/work/htdl-viewer-20261101`, branch
`work/m2-htdl-viewer-2026-11-01`. Consulte o
[relatório M2/M3](../relatorios/2026-11-01-m2-visualizador-htdl.md) e seu
adendo de publicação; confirme SHA remoto e PR antes de continuar. O SHA
documental final é obtido pelo histórico. Ao ler a cópia original, abra o
[relatório local](<C:/Users/babus/Desktop/AssisScript/work/htdl-viewer-20261101/docs/relatorios/2026-11-01-m2-visualizador-htdl.md>).

Implementação/testes em `d39371d8cbaefa85df7ed9923c78df495c584a98`, 62 paths.
O push foi rejeitado antes de executar pela revisão automática, que exigiu
autorização direta para o payload/destino públicos exatos. **Sem publicação
ou PR nova confirmadas**; não usar rota alternativa. Autorizar os 62 arquivos
da revisão final ao Vibe-O-Coder/AssisScript e PR de rascunho sobre #17 é a
ação pendente. Adendo do relatório/histórico guardam a revisão documental final.

Já existem reconciliações M0, contratos, arena geracional, provider Windows,
alocação/remoção recuperáveis, BufferPool, árvore/fonte/metadados próprios,
candidato/ativo transacional e parser HTDL bootstrap real. Não reimplemente.
`std/viewer.assis` apresenta a árvore validada com texto medido, quebra,
foco/teclado/clique/scroll e snapshot próprio. O exemplo 44 abre arquivo local,
redimensiona e fecha. Extensão viewer 1 preserva imports/ABI do window base.
São lógica de produto em AssisScript e adaptação User32/GDI pequena.

Régua: **27,00/100, 0/5 gates**; meta de 30% ainda não atingida. E04-02/E04-03=2,
E04-04=1, E07-04=2, E08-02/E08-05=1; demais estados preservados. M2/M3 parciais.
Windows: 106 métodos executados/1 not-run; Linux: 85/3, sem provider gráfico.
Geração dos cinco formatos não é execução ARM/macOS. Três dumps de superfície
foram inspecionados e têm bytes iguais nos dois modos; captura real da janela
via Computer Use falhou duas vezes, sem aceite visual de desktop/200%/leitor.

O workspace de View é adicional ao Store; não é quota de RSS/processo. O File
legado do exemplo conserva alocação fatal limitada de caminho. IDs não são
capacidades. O envelope de documento recusa eventos semânticos antigos, mas
não cancela mensagens do OS ainda não obtidas antes de navegação. Não há
seleção/IME/acessibilidade, rede, programa de página, FS/SSC ou HTDL 0.1 completo.

Próximo: seleção de texto, ponte acessível e aceite real 200%/monitores/leitor
de tela/captura do desktop. Catálogo completo, recuperação de editor e mutações
semânticas seguem abertos. M0-EXEC exige spikes VM/Wasm/decisão independentes;
M1 ainda não fecha RSS. Use o JSON e a fila efetivos. Easy permanece a última
etapa de todo o projeto. Publicar branch não significa merge, release ou CI.

As seções e entregas M1/M3 abaixo preservam seus estados históricos. A continuação efetiva é a M2/M3 acima.

## Encontrar a revisão que deve continuar

A pasta original `AssisScript/AssisScript` ainda estava em `1ed22f5`, branch
de planejamento, com 31 alterações antigas. Há worktrees e branches
descendentes com entregas publicadas. A maior data de um arquivo, o diretório
inicial e a branch padrão do GitHub não identificam por si sós a ponta útil.

Antes de implementar, confira `git worktree list --porcelain`, `git branch -a`,
`git log --all --oneline --decorate`, status e remoto. Leia os relatórios da
linhagem escolhida e confirme seu SHA remoto. Trabalhe em cópia isolada limpa
quando houver fontes locais antigas; não publique novamente essas fontes.
Branches podem divergir: ancestralidade e contratos precisam ser comparados.

Esta unidade usa a cópia `AssisScript/work/htdl-parser-20261101`.
O [masterprompt](MASTERPROMPT.md) também é atualizado no caminho original
solicitado pelo usuário, para que ele conduza à linhagem atual.

## Entregas existentes e relatórios relacionados

Os links fixam as revisões de cada relatório. São evidências históricas das
próprias unidades, não testes reexecutados nesta.

| Entrega | Revisão e relatório |
| --- | --- |
| Planejamento, 60 critérios e baseline 19,90% | [1ed22f5 — planejamento](https://github.com/Vibe-O-Coder/AssisScript/blob/1ed22f5c898f21f06c429774992469177bdfd3d9/docs/relatorios/2026-10-29-planejamento-ecossistema.md) |
| M0: `++`/`--` e tipos/empréstimos/editor | [67695a5 — incremento](https://github.com/Vibe-O-Coder/AssisScript/blob/67695a55a2df2a9db624676b990c6d907f5a8e6c/docs/relatorios/2026-10-29-m0-incremento.md) |
| M0: OwnedArray mutável reconciliado | [9c09baf — coleções](https://github.com/Vibe-O-Coder/AssisScript/blob/9c09baf934eb2ae6a73dd7a15df4d8fa3c30717f/docs/relatorios/2026-10-29-m0-owned.md) |
| M0: microformato e modelos independentes | [d842f98 — microparser](https://github.com/Vibe-O-Coder/AssisScript/blob/d842f98702a3321bf33f649eb300b2466f7b2009/docs/relatorios/2026-10-29-m0-microparser.md) |
| M0: perfil bootstrap, ABI, ADR e snapshot HTDL | [ebe5928 — contratos](https://github.com/Vibe-O-Coder/AssisScript/blob/ebe5928999d8e01e5b224a2c211ba1b575dee783/docs/relatorios/2026-10-29-m0-contratos.md) |
| M1: arena geracional e aposentadoria | [6208ecb — arena](https://github.com/Vibe-O-Coder/AssisScript/blob/6208ecb5bd5801defcd9c0e6b1809ba731a942db/docs/relatorios/2026-10-29-m1-arena.md) |
| M1: provider Windows, janela e fronteira C | [038f00d — plataforma](https://github.com/Vibe-O-Coder/AssisScript/blob/038f00d83ef1c413cb3031e5ad59cb4675f4b534/docs/relatorios/2026-10-29-m1-plataforma-windows.md) |
| M1: `try_alloc`, ByteBuffer e limites recuperáveis | [085fb41 — alocação](https://github.com/Vibe-O-Coder/AssisScript/blob/085fb4109b5389742be8d562cdab34de69747e6f/docs/relatorios/2026-10-29-m1-alocacao.md) |
| M1: `try_new` e inserções fallíveis | [795d899 — slots](https://github.com/Vibe-O-Coder/AssisScript/blob/795d899394f0444381999dcb0fef7c011f4b99f7/docs/relatorios/2026-10-30-m1-slots-falliveis.md) |
| M1: transferência/remoção sem alocação de resultado | [52c8bb1 — remoção](https://github.com/Vibe-O-Coder/AssisScript/blob/52c8bb1f1d7482865660580941637a3074329167/docs/relatorios/2026-10-30-m1-remocao-sem-alocacao.md) |
| M1: quota conjunta e transitória de payload | [a77f3d6 — orçamento e publicação confirmada](https://github.com/Vibe-O-Coder/AssisScript/blob/a77f3d6d377d233886f586d11a676c2554062ceb/docs/relatorios/2026-11-01-m1-orcamento-buffers.md) |
| M1: preparação de metadados e continuidade | [ee852b1 — metadados](https://github.com/Vibe-O-Coder/AssisScript/blob/ee852b13721f81553169d716dd803e9fc36d96ad/docs/relatorios/2026-11-01-m1-reserva-metadados.md) |
| M1: árvore e texto no orçamento de payload | [relatório atual](https://github.com/Vibe-O-Coder/AssisScript/blob/work/m1-document-store-2026-11-01/docs/relatorios/2026-11-01-m1-arvore-orcamento.md) — publicação confirmada, PR #15 |
| M1: metadados, fonte própria e candidato/ativo | [relatório](../relatorios/2026-11-01-m1-documento-candidato.md) — PR #16 |
| M3: parser bootstrap, atributos/spans e ativação validada | [relatório atual](../relatorios/2026-11-01-m3-parser-htdl.md) |

## Contratos e limites da base M1

Na revisão atual, consulte [fila operacional](FILA-M0-M1.md),
[perfil do visualizador](PERFIL-VISUALIZADOR-V1.md),
[ABI de plataforma](ABI-PLATAFORMA-V1.md),
[ADR do executor](ADR-0001-EXECUCAO-PAGINA.md),
[snapshot e proveniência dos rascunhos](referencias/htdl-drafts-2026-10-29/PROVENANCE.json)
e [progresso calculado](PROGRESSO.md).

O formato restrito VM/Wasm ainda requer spikes e decisão. O microparser não
implementa HTDL. O provider Windows é prova parcial, sem visualizador completo,
IME/acessibilidade ou aceite visual M2. Arena e BufferId dependem de instâncias
atribuídas pelo host e não são capacidades de segurança.

BufferPool cobra payload; `doctree::Tree` usa essa arena de bytes para cobrar
os registros reais de 128 bytes e o texto UTF-8 no mesmo teto, incluindo
candidato inteiro durante crescimento. Recusa preserva conteúdo/links/IDs.
Reparent sem ciclos e remoção iterativa não alocam pela biblioteca. A árvore
é genérica, sem parser ou modelos de conteúdo HTDL. Contrato em
[BIBLIOTECA-doctree.md](../BIBLIOTECA-doctree.md).

A preparação de slots reserva metadados reutilizáveis, com progresso parcial.
O teto adicional de armazenamento cobra índice/slots/controladores; documents
inclui fonte própria e candidato/ativo. Overhead/RSS, pilha e recursos futuros
continuam fora do contrato. M0/M1 e G1–G5 permanecem abertos.
Os 100/100 antigos continuam restritos às fases 0–6.

Próximo: parser M3 e atributos cobrados. Deve consumir a árvore recuperável e tem
contrato de conformidade próprio. Executor M0-EXEC e validação visual M2
seguem independentes. Web/Easy continuam no registro futuro; Easy é a última etapa.

## Continuação: armazenamento e candidato completo

`BufferPool.try_limit_storage` cobra controladores/slots/índice e payload;
`used_bytes` conserva o contrato de payload. A árvore expõe o mesmo teto
adicional. `documents::Store` acrescenta fonte própria e candidato/ativo sob
um teto compartilhado, abort completo e commit sem alocação após raiz e
instância correspondentes. O formato ainda é validado pelo chamador.
Contrato: [documents](../BIBLIOTECA-documents.md). Evidência/limites:
[relatório atual](../relatorios/2026-11-01-m1-documento-candidato.md).

Metadados e fonte própria entram na cobrança de corpos nativos solicitados;
headers/alinhamento/slabs/cache/RSS, pilha e recursos ainda não implementados
continuam fora. Parser HTDL M3 deve integrar atributos e corpus reais antes de
ativação. Executor M0-EXEC e experiência visual M2 continuam na fila.

## Continuação M3 — parser HTDL bootstrap

`std/htdl.assis` faz parsing/validação iterativos, guarda atributos e spans
na árvore cobrada e ativa somente após validação. Erros/quota/OOM abortam
candidato inteiro; consultas são somente leitura. Perfil de nove tipos;
sem janela/acessibilidade, código, rede, FS/SSC ou conformidade completa 0.1.
[Contrato](../BIBLIOTECA-htdl.md), [relatório](../relatorios/2026-11-01-m3-parser-htdl.md)
e [evidência atual](evidencias/m3-htdl-parser-2026-11-01/summary.json).
Próximo: M2-WINDOW e apresentação/interação M3, mantendo executor VM/Wasm,
catálogo completo, recuperação de editor e mutações na fila. Os parágrafos
anteriores sobre ausência de parser descrevem suas respectivas entregas M1.


## Continuação M2/M3 — apresentação HTDL local

[Relatório](../relatorios/2026-11-01-m2-visualizador-htdl.md),
[contrato](../BIBLIOTECA-viewer.md),
[evidência](evidencias/m2-viewer-2026-11-01/summary.json).
Texto medido, snapshots próprios, hidden/disabled, foco, teclado/clique/roda,
scroll e resize integram a árvore validada. Não há seleção/árvore assistiva/IME
ou aceite 200%; a captura desktop falhou. Não repetir parser ou memória.
Próximo: seleção/acessibilidade e verificação real de desktop, mantendo
M0-EXEC, catálogo completo, mutações e demais marcos na fila. 27,00%, 0/5 gates.

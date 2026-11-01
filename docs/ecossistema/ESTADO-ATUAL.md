# Continuidade verificada — AssisScript e ecossistema

Atualização: **01/11/2026**. Régua v1: **22,30/100, 0/5 gates**.
Base desta unidade: `ee852b13721f81553169d716dd803e9fc36d96ad`,
branch `work/ecosystem-current-2026-11-01`,
[PR #14](https://github.com/Vibe-O-Coder/AssisScript/pull/14), confirmada aberta
e em rascunho nesta sessão pelo conector GitHub, com o mesmo SHA local/remoto.
A nova continuação é `work/m1-document-store-2026-11-01`, baseada nela.
Publicação e revisão exata no [relatório da árvore](../relatorios/2026-11-01-m1-arvore-orcamento.md).
Não há merge automático nem release nesta unidade.

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

Esta unidade usa a cópia `AssisScript/work/document-store-20261101`.
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
| Esta unidade: árvore e texto no orçamento de payload | [relatório atual](https://github.com/Vibe-O-Coder/AssisScript/blob/work/m1-document-store-2026-11-01/docs/relatorios/2026-11-01-m1-arvore-orcamento.md) |

## Contratos e limites atuais

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
Metadados do índice, controladores, overhead/RSS, fonte, atributos e outros
recursos futuros continuam fora da quota. M0/M1 e G1–G5 permanecem abertos.
Os 100/100 antigos continuam restritos às fases 0–6.

Próximo M1-ALLOC: contabilizar metadados/demais recursos e preparar candidato
completo com rollback. Parser M3 deve consumir a árvore recuperável e tem
contrato de conformidade próprio. Executor M0-EXEC e validação visual M2
seguem independentes. Web/Easy continuam no registro futuro; Easy é a última etapa.

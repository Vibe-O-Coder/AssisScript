# Progresso — capacidade do AssisScript para o ecossistema web

Data: 2026-11-01. Régua v1. **28,90/100 pontos (28,90%)**, com **0/5 gates aprovados**.

Estado da avaliação: `partial-native-retest-m3-reader`. Escopo: Capacidade do AssisScript nativo, runtime, bibliotecas e ferramentas para implementar Browser, buscador e ecossistema HTDL/FS/SSC, comprovada por integrações de referência.

Unidade Reader: seleção de escalares e cópia, zoom da fonte/reflow 100/200%, projeção acessível MSAA e cliente externo Windows; biblioteca e fallback Linux x64 têm resultados próprios. Geração estrangeira não é execução. Captura Computer Use falhou em app approval timed out; leitor de tela real, IME/grafemas, monitores/DPI do OS, contraste/movimento, layout FS/SSC, sandbox e CI global continuam abertos. Detalhes e contagens exatas no relatório da unidade; nenhum gate aprovado. O número não mede prazo, esforço restante ou prontidão para produção. Casas decimais tornam a soma auditável; não significam precisão de previsão.

Os 100/100 das antigas fases 0–6 medem outro escopo e permanecem preservados. Esta régua tem 60 critérios em 12 frentes; cinco critérios dividem igualmente o peso de cada frente. Níveis 0–4 rendem 0%, 25%, 50%, 75% e 100% do crédito. Fórmula: `Σ peso × soma(níveis) / 20`. Só há conclusão com todos os critérios em 4 e os cinco gates aprovados.

[Plano completo](PLANO-MESTRE.md) · [Fonte dos estados](PROGRESSO.json) · [Baseline e hashes](BASELINE-2026-10-29.json) · [Masterprompt](MASTERPROMPT.md)

## Pontuação por frente

| Frente | Peso | Níveis dos cinco critérios | Pontos |
| --- | ---: | --- | ---: |
| E00 — Contratos, arquitetura e rastreabilidade | 4 | 1, 1, 1, 2, 2 | 1,40 |
| E01 — Linguagem, compilador e garantias semânticas | 14 | 2, 3, 2, 2, 3 | 8,40 |
| E02 — Memória, coleções, texto e dados grandes | 8 | 2, 2, 2, 2, 1 | 3,60 |
| E03 — Sistema, tarefas, processos e integração de eventos | 10 | 1, 1, 2, 2, 0 | 3,00 |
| E04 — Plataforma gráfica, entrada e acessibilidade | 10 | 2, 2, 2, 2, 2 | 5,00 |
| E05 — Rede, URLs e serviços web | 8 | 1, 0, 0, 0, 0 | 0,40 |
| E06 — Executor restrito, capacidades e isolamento | 10 | 0, 0, 0, 0, 0 | 0,00 |
| E07 — HTDL, árvore semântica e SDK de documentos | 8 | 2, 1, 0, 2, 1 | 2,40 |
| E08 — FluxStyle, SSC, layout e integração visual | 8 | 0, 2, 0, 0, 1 | 1,20 |
| E09 — Persistência, perfil e formatos de armazenamento | 8 | 1, 1, 0, 0, 0 | 0,80 |
| E10 — Rastreamento, indexação e consulta do buscador | 6 | 1, 0, 0, 0, 0 | 0,30 |
| E11 — Ferramentas, distribuição e aceite integrado | 6 | 2, 2, 2, 1, 1 | 2,40 |
| **Total** | **100** | **60 critérios** | **28,90** |

## Gates de integração

| Gate | Aceitação | Estado |
| --- | --- | --- |
| G1 | Visualizador local | Não aprovado |
| G2 | Página remota isolada | Não aprovado |
| G3 | Ecossistema visual integrado | Não aprovado |
| G4 | Busca persistente integrada | Não aprovado |
| G5 | Distribuição e aceite final | Não aprovado |

G2 aberto impede anunciar execução segura de páginas remotas. Pontuação alta não dispensa nenhum gate. A aprovação exige relatório do marco, testes e revisão exata.

## Histórico congelado

| Data | Retrato | Pontos | Gates |
| --- | --- | ---: | ---: |
| 2026-10-29 | Baseline documental inicial; sem novos testes do runtime | 19,90 | 0/5 |
| 2026-10-29 | M0 parcial: reconciliação ++/--, testes próprios e rastreabilidade da publicação | 20,10 | 0/5 |
| 2026-10-29 | M0 parcial: OwnedArray mutável publicado com modelos independentes; níveis preservados | 20,10 | 0/5 |
| 2026-10-29 | M0 parcial: prova de microformato reconciliada, 8/8 por host; níveis preservados | 20,10 | 0/5 |
| 2026-10-29 | M0 parcial: snapshot e contratos versionados; sem promoção de runtime | 20,10 | 0/5 |
| 2026-10-29 | M1 parcial: arena com identidades geracionais nativas; E02-02 de 1 para 2 | 20,50 | 0/5 |
| 2026-10-29 | M1 parcial: janela/eventos Windows e desenho por software; E04-02/E04-03 de 0 para 1 | 21,50 | 0/5 |
| 2026-10-29 | M1 parcial: alocação recuperável de buffers e limite por instância; E02-03 de 0 para 1 | 21,90 | 0/5 |
| 2026-10-30 | M1 parcial: reserva inicial de objetos e inserções Move/slots recuperáveis; E02-03 de 1 para 2 | 22,30 | 0/5 |
| 2026-10-30 | M1 parcial: take/erase e swap_remove sem alocação na biblioteca; níveis preservados | 22,30 | 0/5 |
| 2026-11-01 | M1 parcial: orçamento conjunto de payload em pool de buffers; níveis preservados | 22,30 | 0/5 |
| 2026-11-01 | Preparação de metadados e continuidade reconciliada; níveis/gates preservados | 22,30 | 0/5 |
| 2026-11-01 | M1: árvore ordenada e texto UTF-8 no orçamento compartilhado; níveis/gates preservados | 22,30 | 0/5 |
| 2026-11-01 | M1: metadados/fonte cobrados e candidato completo transacional; níveis/gates preservados | 22,30 | 0/5 |
| 2026-11-01 | M3 parcial: parser HTDL real bootstrap, driver/corpus e ativação validada; 0/5 gates | 23,90 | 0/5 |
| 2026-11-01 | M2/M3 parcial: janela HTDL, apresentação textual, foco/eventos/scroll e superfícies; 27,00%, 0/5 gates | 27,00 | 0/5 |
| 2026-11-01 | M3 parcial: seleção/cópia, zoom 100/200% e MSAA externo pelo mesmo snapshot; 28,90%, 0/5 gates | 28,90 | 0/5 |

## Estado e evidência dos 60 critérios

### E00 — Contratos, arquitetura e rastreabilidade

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E00-01 — Especificações versionadas | 1/4 | Há rascunhos no projeto irmão; não foram congelados nem certificados. `local:htdl/docs/14-fundamentos-e-perfis.md`; `local:htdl/docs/19-conformidade-e-cenarios.md`; [2026-10-29-m0-contratos.md](../../docs/relatorios/2026-10-29-m0-contratos.md); [PROVENANCE.json](../../docs/ecossistema/referencias/htdl-drafts-2026-10-29/PROVENANCE.json) |
| E00-02 — Modelo de ameaças e privacidade | 1/4 | Arquitetura de capacidades existe como proposta. `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md` |
| E00-03 — Fronteiras e decisões arquiteturais | 1/4 | Há desenho documental; nenhuma integração nativa observada. `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md`; [2026-10-29-m0-contratos.md](../../docs/relatorios/2026-10-29-m0-contratos.md); [PROVENANCE.json](../../docs/ecossistema/referencias/htdl-drafts-2026-10-29/PROVENANCE.json) |
| E00-04 — Driver e matriz de conformidade | 2/4 | Driver nativo do perfil bootstrap com corpus declarativo, diagnóstico e árvore, oráculo XML independente na sintaxe em comum e execução Windows/Linux x64. Matriz distingue formatos gerados de execução e produto not-run; FS/SSC e catálogo completo não têm driver integrado. `local:htdl/docs/19-conformidade-e-cenarios.md`; [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json); [htdl-bootstrap-corpus.json](../../tests/fixtures/htdl-bootstrap-corpus.json) |
| E00-05 — Inventário, publicação e relatório | 2/4 | Rastreabilidade exercitada na unidade M0 de ++/--: fontes isoladas, builds próprios, logs/hashes, sete suítes por Windows/Linux x64, relatório e branch de publicação. Inventário e aceite integrado do produto permanecem abertos. [HANDOFF-ARM64-V1.md](../../docs/HANDOFF-ARM64-V1.md); [SUPPORT.md](../../docs/SUPPORT.md); [2026-10-29-m0-incremento.md](../../docs/relatorios/2026-10-29-m0-incremento.md); [windows-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/windows-x64.json); [linux-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/linux-x64.json); [2026-10-29-m0-owned.md](../../docs/relatorios/2026-10-29-m0-owned.md); [2026-10-29-m1-arena.md](../../docs/relatorios/2026-10-29-m1-arena.md); [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json); [ESTADO-ATUAL.md](../../docs/ecossistema/ESTADO-ATUAL.md); [2026-11-01-m1-reserva-metadados.md](../../docs/relatorios/2026-11-01-m1-reserva-metadados.md); [2026-11-01-m1-arvore-orcamento.md](../../docs/relatorios/2026-11-01-m1-arvore-orcamento.md); [windows.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/windows.json); [linux.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/linux.json); [2026-11-01-m1-documento-candidato.md](../../docs/relatorios/2026-11-01-m1-documento-candidato.md); [summary.json](../../docs/ecossistema/evidencias/m1-document-memory-2026-11-01/summary.json); [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json) |

### E01 — Linguagem, compilador e garantias semânticas

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E01-01 — DataLayout e ABI por destino | 2/4 | Destinos nativos e ABI escalar existem; novo destino de página não existe. [ARM64-NATIVO.md](../../docs/ARM64-NATIVO.md); [ABI-NATIVA.md](../../docs/ABI-NATIVA.md); [FFI-C.md](../../docs/FFI-C.md) |
| E01-02 — Tipos e abstrações para programas grandes | 3/4 | Mecanismos nativos demonstrados; ainda sem integração nos produtos. A reconciliação de ++/-- tem reexecução própria em Windows/Linux x64, sem promover o nível por essa fatia. [GENERICS.md](../../docs/GENERICS.md); [VALORES-E-VARIANTES.md](../../docs/VALORES-E-VARIANTES.md); [CAPTURAS-E-VARIANTES-MOVE.md](../../docs/CAPTURAS-E-VARIANTES-MOVE.md); [FUNCOES-E-EFEITOS.md](../../docs/FUNCOES-E-EFEITOS.md); [2026-10-29-m0-incremento.md](../../docs/relatorios/2026-10-29-m0-incremento.md); [windows-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/windows-x64.json); [linux-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/linux-x64.json) |
| E01-03 — Ownership, vidas e destruição | 2/4 | Verificador e recursos proprietários existem com restrições explícitas. [OWNERSHIP-FUNCOES.md](../../docs/OWNERSHIP-FUNCOES.md); [RECURSOS-E-FATIAS.md](../../docs/RECURSOS-E-FATIAS.md); [SAFE-DEFAULT.md](../../docs/SAFE-DEFAULT.md); [2026-10-29-m0-owned.md](../../docs/relatorios/2026-10-29-m0-owned.md); [2026-10-29-m1-arena.md](../../docs/relatorios/2026-10-29-m1-arena.md); [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json) |
| E01-04 — Erros, números e contratos de falha | 2/4 | Result e números nativos disponíveis; contrato geral de OOM/host ainda aberto. [NUMEROS.md](../../docs/NUMEROS.md); [VALORES-E-VARIANTES.md](../../docs/VALORES-E-VARIANTES.md); [ERROS.md](../../docs/ERROS.md) |
| E01-05 — IR, otimização e diagnósticos | 3/4 | IR nativa integral e validação histórica; formato restrito permanece aberto. A fatia ++/-- e regressões foram reexecutadas nos dois modos em Windows/Linux x64; outros alvos tiveram somente geração nesta unidade. [BACKEND-IR-COMPLETA.md](../../docs/BACKEND-IR-COMPLETA.md); [BACKEND-ALPHA15.md](../../docs/BACKEND-ALPHA15.md); [VALIDACAO-TARGETS-V1.json](../../docs/VALIDACAO-TARGETS-V1.json); [2026-10-29-m0-incremento.md](../../docs/relatorios/2026-10-29-m0-incremento.md); [windows-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/windows-x64.json); [linux-x64.json](../../docs/ecossistema/evidencias/m0-incremento-2026-10-29/linux-x64.json) |

### E02 — Memória, coleções, texto e dados grandes

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E02-01 — Coleções proprietárias mutáveis | 2/4 | OwnedArray mutável reconciliado e testado em Windows/Linux x64; mutação, transferência, remoção, drops e modelos independentes. Outras coleções, ordem de filhos e integração completas permanecem abertas. [owned.assis](../../stdlib/owned.assis); [test-owned-mutation.py](../../tests/test-owned-mutation.py); [2026-10-29-m0-owned.md](../../docs/relatorios/2026-10-29-m0-owned.md); [summary.json](../../docs/ecossistema/evidencias/m0-owned-2026-10-29/summary.json) |
| E02-02 — Arenas e identidades estáveis | 2/4 | Arena e árvore ordenada nativas com instância/slot/geração, reciclagem e aposentadoria sem wrap; navegação por candidato/ativo invalida IDs antigos. Windows/Linux x64 contra modelos independentes. Identidades locais não são capacidades; integração HTDL permanece aberta. [arena.assis](../../stdlib/arena.assis); [test-arena.py](../../tests/test-arena.py); [2026-10-29-m1-arena.md](../../docs/relatorios/2026-10-29-m1-arena.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-arena-2026-10-29/windows-x64.json); [linux-x64.json](../../docs/ecossistema/evidencias/m1-arena-2026-10-29/linux-x64.json); [2026-11-01-m1-arvore-orcamento.md](../../docs/relatorios/2026-11-01-m1-arvore-orcamento.md); [windows.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/windows.json); [linux.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/linux.json); [2026-11-01-m1-documento-candidato.md](../../docs/relatorios/2026-11-01-m1-documento-candidato.md); [summary.json](../../docs/ecossistema/evidencias/m1-document-memory-2026-11-01/summary.json) |
| E02-03 — Alocação e quotas recuperáveis | 2/4 | try_alloc/try_new, inserções/remoções recuperáveis, BufferPool e árvore/texto demonstrados. Teto opcional cobre corpos nativos de controladores/slots/índice; documents acrescenta fonte própria e candidato/ativo, com abort completo e commit sem alocação. OOM por fronteira em Windows/Linux; overhead/RSS, atributos e recursos futuros/integração HTDL permanecem abertos. [ALOCACAO-FALLIVEL.md](../../docs/ALOCACAO-FALLIVEL.md); [memory.assis](../../stdlib/memory.assis); [test-fallible-allocation.py](../../tests/test-fallible-allocation.py); [summary.json](../../docs/ecossistema/evidencias/m1-alocacao-2026-10-29/summary.json); [2026-10-29-m1-alocacao.md](../../docs/relatorios/2026-10-29-m1-alocacao.md); [INSERCAO-FALLIVEL.md](../../docs/INSERCAO-FALLIVEL.md); [2026-10-30-m1-slots-falliveis.md](../../docs/relatorios/2026-10-30-m1-slots-falliveis.md); [summary.json](../../docs/ecossistema/evidencias/m1-slots-2026-10-29/summary.json); [2026-10-30-m1-remocao-sem-alocacao.md](../../docs/relatorios/2026-10-30-m1-remocao-sem-alocacao.md); [summary.json](../../docs/ecossistema/evidencias/m1-removal-2026-10-30/summary.json); [test-arena-removal.py](../../tests/test-arena-removal.py); [BIBLIOTECA-buffers.md](../../docs/BIBLIOTECA-buffers.md); [buffers.assis](../../stdlib/buffers.assis); [test-shared-buffer-budget.py](../../tests/test-shared-buffer-budget.py); [2026-11-01-m1-orcamento-buffers.md](../../docs/relatorios/2026-11-01-m1-orcamento-buffers.md); [summary.json](../../docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01/summary.json); [test-buffer-preallocation.py](../../tests/test-buffer-preallocation.py); [2026-11-01-m1-reserva-metadados.md](../../docs/relatorios/2026-11-01-m1-reserva-metadados.md); [summary.json](../../docs/ecossistema/evidencias/m1-buffer-preallocation-2026-11-01/summary.json); [2026-11-01-m1-arvore-orcamento.md](../../docs/relatorios/2026-11-01-m1-arvore-orcamento.md); [windows.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/windows.json); [linux.json](../../docs/ecossistema/evidencias/m1-document-tree-2026-11-01/linux.json); [2026-11-01-m1-documento-candidato.md](../../docs/relatorios/2026-11-01-m1-documento-candidato.md); [summary.json](../../docs/ecossistema/evidencias/m1-document-memory-2026-11-01/summary.json); [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json) |
| E02-04 — Unicode e edição de texto | 2/4 | String UTF-8 com vida/comprimento existe; processamento linguístico completo não existe. [BIBLIOTECA-unicode.md](../../docs/BIBLIOTECA-unicode.md); [BIBLIOTECA-texto.md](../../docs/BIBLIOTECA-texto.md) |
| E02-05 — Mapas e armazenamento eficientes | 1/4 | Há mapas e prova de colisões por correção; resistência de custo não comprovada. [COLECOES.md](../../docs/COLECOES.md); `local:assis/docs/AUDITORIA-HTDL.md`; [2026-10-29-m0-microparser.md](../../docs/relatorios/2026-10-29-m0-microparser.md); [htdl-core.assis](../../tests/fixtures/htdl-core.assis); [test-htdl-readiness.py](../../tests/test-htdl-readiness.py) |

### E03 — Sistema, tarefas, processos e integração de eventos

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E03-01 — Arquivos, caminhos e diretórios | 1/4 | Arquivos/argumentos existem; API geral de diretórios e confinamento ainda aberta. [IO-E-APLICACAO-A.md](../../docs/IO-E-APLICACAO-A.md); [BIBLIOTECA-cli.md](../../docs/BIBLIOTECA-cli.md) |
| E03-02 — Loop responsivo e I/O não bloqueante | 1/4 | Fila cooperativa e polling de rede separados; sem loop gráfico integrado. [EVENTOS-E-PERSISTENCIA.md](../../docs/EVENTOS-E-PERSISTENCIA.md); [BIBLIOTECA-eventos.md](../../docs/BIBLIOTECA-eventos.md); [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md); [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json) |
| E03-03 — Workers, IPC e supervisão | 2/4 | Processos, pipes e supervisão delimitados disponíveis. [BIBLIOTECA-process.md](../../docs/BIBLIOTECA-process.md); [FFI-C.md](../../docs/FFI-C.md) |
| E03-04 — Ciclo de vida de recursos e assinaturas | 2/4 | Recursos own e cancelamento básicos existem; ainda sem ciclo de vida de aba. [OWNERSHIP-FUNCOES.md](../../docs/OWNERSHIP-FUNCOES.md); [BIBLIOTECA-eventos.md](../../docs/BIBLIOTECA-eventos.md); [BIBLIOTECA-process.md](../../docs/BIBLIOTECA-process.md) |
| E03-05 — Paralelismo com contrato seguro | 0/4 | Sem contrato de threads ou integração paralela do motor. [EVENTOS-E-PERSISTENCIA.md](../../docs/EVENTOS-E-PERSISTENCIA.md) |

### E04 — Plataforma gráfica, entrada e acessibilidade

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E04-01 — Ponte nativa segura e versionada | 2/4 | ABI C escalar e callbacks síncronos existem; bibliotecas gráficas não integradas. [FFI-C.md](../../docs/FFI-C.md); [ARM64-NATIVO.md](../../docs/ARM64-NATIVO.md); [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json) |
| E04-02 — Janela, monitores e eventos | 2/4 | Janela Windows x64 integrada a HTDL local: teclado/clique/roda/resize/close e recursos contados. Captura desktop, monitores/200%, touch e suspensão seguem pendentes. `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md`; [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json); [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json) |
| E04-03 — Desenho, imagens e composição | 2/4 | Composição software de texto/retângulos e clipping integrados ao snapshot, modelo independente por pixel e superfícies equivalentes. Imagens/transforms e perda de dispositivo completa faltam. `local:htdl/docs/17-execucao-transacoes-e-layout.md`; [2026-10-29-m1-plataforma-windows.md](../../docs/relatorios/2026-10-29-m1-plataforma-windows.md); [windows-x64.json](../../docs/ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json); [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json) |
| E04-04 — Fontes, edição e entrada de texto | 2/4 | Seleção de leitura em fronteiras UTF-8, clipboard isolado e fonte 100/200% com reflow demonstrados no Reader Windows x64, além da medição anterior. Graphemes, shaping/bidi completos, edição/IME e DPI/monitores do OS permanecem abertos. [BIBLIOTECA-unicode.md](../../docs/BIBLIOTECA-unicode.md); [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json); [2026-11-01-m3-leitura-acessivel.md](../../docs/relatorios/2026-11-01-m3-leitura-acessivel.md); [summary.json](../../docs/ecossistema/evidencias/m3-reader-2026-11-01/summary.json); [test-htdl-reader.py](../../tests/test-htdl-reader.py); [reader_oracle.c](../../tests/reader_oracle.c) |
| E04-05 — Acessibilidade e políticas do usuário | 2/4 | Projeção MSAA nativa documento/blocos, nomes/roles/disabled/offscreen/foco/geometria e ação padrão via fila com identidade, testada por cliente externo e oráculo C com falhas/lifetime. Projeção plana; leitor de tela real, UIA TextPattern e políticas de contraste/movimento ainda sem aceite. `local:htdl/docs/14-fundamentos-e-perfis.md`; `local:htdl/docs/19-conformidade-e-cenarios.md`; [2026-11-01-m3-leitura-acessivel.md](../../docs/relatorios/2026-11-01-m3-leitura-acessivel.md); [summary.json](../../docs/ecossistema/evidencias/m3-reader-2026-11-01/summary.json); [test-htdl-reader.py](../../tests/test-htdl-reader.py); [reader_oracle.c](../../tests/reader_oracle.c) |

### E05 — Rede, URLs e serviços web

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E05-01 — Cliente HTTP(S) geral | 1/4 | GET cooperativo limitado existe; não é cliente de navegação completo. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md); [BIBLIOTECA-http.md](../../docs/BIBLIOTECA-http.md) |
| E05-02 — Políticas de navegação e origem | 0/4 | Esses serviços estão desabilitados ou ausentes no cliente delimitado. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md) |
| E05-03 — URL, DNS e codificação | 0/4 | Aceitar URL via libcurl não é biblioteca pública de URL/origem. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md) |
| E05-04 — Streaming e canais contínuos | 0/4 | Corpo limitado em memória, sem streaming geral demonstrado. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md) |
| E05-05 — Servidor e serviço de consulta | 0/4 | Não há servidor HTTP ou API socket geral demonstrados. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md) |

### E06 — Executor restrito, capacidades e isolamento

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E06-01 — Formato de execução de página | 0/4 | browser-wasm32 é proposta, não alvo existente. `local:htdl/docs/03-assisscript-no-navegador.md`; [ARM64-NATIVO.md](../../docs/ARM64-NATIVO.md) |
| E06-02 — Memória, CPU e interrupção | 0/4 | safe e timeout externo não demonstram essas garantias. [SAFE-DEFAULT.md](../../docs/SAFE-DEFAULT.md); `local:assis/docs/AUDITORIA-HTDL.md` |
| E06-03 — Capacidades e API hospedeira | 0/4 | Modelo descrito, sem enforcement executável. `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md` |
| E06-04 — Sandbox de processo por OS | 0/4 | Criar processo por si só não isola autoridade. [BIBLIOTECA-process.md](../../docs/BIBLIOTECA-process.md); `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md` |
| E06-05 — Ciclo de vida e recuperação de aba | 0/4 | Nenhum runtime de aba integrado disponível. `local:htdl/docs/15-htdl-0.2-e-carregamento.md` |

### E07 — HTDL, árvore semântica e SDK de documentos

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E07-01 — Parser e diagnóstico HTDL real | 2/4 | Parser real do perfil viewer-local-bootstrap-v1 em AssisScript, com atributos/entidades/comentários, modelos de conteúdo, UTF-8/UTF-16, spans, limites, IDs e corpus adverso nativo. Catálogo HTDL completo e recuperação de editor permanecem abertos. `local:assis/docs/AUDITORIA-HTDL.md`; `local:htdl/docs/02-htdl-0.1.md`; [2026-10-29-m0-microparser.md](../../docs/relatorios/2026-10-29-m0-microparser.md); [htdl-core.assis](../../tests/fixtures/htdl-core.assis); [test-htdl-readiness.py](../../tests/test-htdl-readiness.py); [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json); [htdl-bootstrap-corpus.json](../../tests/fixtures/htdl-bootstrap-corpus.json) |
| E07-02 — Árvore, seletores e mutações | 1/4 | Fundação de árvore HTDL tipada, atributos cobrados, consulta por ID e navegação ordenada somente leitura, com identidade por instância. Seletores gerais, mutação HTDL validada, foco/acessibilidade e transações semânticas continuam abertos. `local:htdl/docs/17-execucao-transacoes-e-layout.md`; [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json); [htdl-bootstrap-corpus.json](../../tests/fixtures/htdl-bootstrap-corpus.json) |
| E07-03 — SDK e ABI htdl_v1 | 0/4 | SDK e nomes antigos dos rascunhos não são API implementada. `local:htdl/docs/03-assisscript-no-navegador.md`; [ENGLISH-API.md](../../docs/ENGLISH-API.md) |
| E07-04 — Estado, eventos e transações | 2/4 | Estado de foco/gestos/scroll por documento e eventos determinísticos com identidade/seq, hidden/disabled e fechamento. Sem células/inscrições, handlers de página, mutação ou transações completas. `local:htdl/docs/17-execucao-transacoes-e-layout.md`; [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json) |
| E07-05 — Loader e ativação atômica | 1/4 | Fonte HTDL local fornecida pelo host é validada antes do commit; falha aborta candidato completo e preserva ativo/vizinho, candidato externo ocupado e IDs antigos. Resolução de arquivos/origem, código, recursos, FS/SSC, rede e resposta assíncrona tardia não implementados. `local:htdl/docs/15-htdl-0.2-e-carregamento.md`; [2026-11-01-m3-parser-htdl.md](../../docs/relatorios/2026-11-01-m3-parser-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json); [htdl-bootstrap-corpus.json](../../tests/fixtures/htdl-bootstrap-corpus.json) |

### E08 — FluxStyle, SSC, layout e integração visual

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E08-01 — Frontend e avaliador FluxStyle | 0/4 | Rascunhos e exemplos conceituais, sem avaliador nativo demonstrado. `local:htdl/docs/16-gramaticas-fs-e-ssc.md`; `local:htdl/docs/12-contrato-fs-ssc-e-assisscript.md` |
| E08-02 — Layout e snapshots coerentes | 2/4 | Snapshot textual próprio agora alimenta desenho, seleção/hit testing, reflow 100/200% e geometria acessível MSAA dos mesmos blocos/linhas inteiras, com falha transacional de construção/publicação. Constraints row/column, FS/SSC e integração completa continuam abertos. `local:htdl/docs/17-execucao-transacoes-e-layout.md`; `local:htdl/docs/19-conformidade-e-cenarios.md`; [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json); [2026-11-01-m3-leitura-acessivel.md](../../docs/relatorios/2026-11-01-m3-leitura-acessivel.md); [summary.json](../../docs/ecossistema/evidencias/m3-reader-2026-11-01/summary.json); [test-htdl-reader.py](../../tests/test-htdl-reader.py); [reader_oracle.c](../../tests/reader_oracle.c) |
| E08-03 — Perfil numérico e temporal SSC | 0/4 | Simulador isolado não é motor SSC integrado ao navegador. `local:htdl/docs/12-contrato-fs-ssc-e-assisscript.md`; `local:htdl/docs/16-gramaticas-fs-e-ssc.md` |
| E08-04 — Foco, movimento e falhas reativas | 0/4 | Regras propostas, ainda sem execução ponta a ponta. `local:htdl/docs/17-execucao-transacoes-e-layout.md` |
| E08-05 — Corpus visual e inspeção | 1/4 | Artigo HTDL em três dumps reais da superfície Windows, inspecionados e iguais entre modos, com entrada nativa. Captura de desktop falhou; contador/dois painéis/leitor de tela/grafo permanecem pendentes. `local:htdl/docs/19-conformidade-e-cenarios.md`; [2026-11-01-m2-visualizador-htdl.md](../../docs/relatorios/2026-11-01-m2-visualizador-htdl.md); [summary.json](../../docs/ecossistema/evidencias/m2-viewer-2026-11-01/summary.json) |

### E09 — Persistência, perfil e formatos de armazenamento

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E09-01 — Commit durável e recuperação | 1/4 | Substituição atômica e serviço C existem; durabilidade física não certificada. [EVENTOS-E-PERSISTENCIA.md](../../docs/EVENTOS-E-PERSISTENCIA.md); [BIBLIOTECA-process.md](../../docs/BIBLIOTECA-process.md) |
| E09-02 — Serialização e formatos versionados | 1/4 | JSON limitado e arquivos existem; formatos do perfil/índice não. [BIBLIOTECA-json.md](../../docs/BIBLIOTECA-json.md); [IO-E-APLICACAO-A.md](../../docs/IO-E-APLICACAO-A.md) |
| E09-03 — Banco, segmentos e consultas | 0/4 | Sem mecanismo geral de banco ou índice persistente demonstrado. [BIBLIOTECAS.md](../../docs/BIBLIOTECAS.md) |
| E09-04 — Perfil, partições e dados sensíveis | 0/4 | Diretórios do Browser e WebAssis estão sem implementação. `local:htdl/docs/18-arquitetura-nativa-e-capacidades.md` |
| E09-05 — Quotas, migração e concorrência | 0/4 | Locks nativos delimitados não resolvem ciclo de vida do perfil. [BIBLIOTECA-process.md](../../docs/BIBLIOTECA-process.md) |

### E10 — Rastreamento, indexação e consulta do buscador

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E10-01 — Extração e análise linguística | 1/4 | Prova local conta palavras em um documento com conversão ASCII. `local:assis/docs/AUDITORIA-HTDL.md`; [2026-10-29-m0-microparser.md](../../docs/relatorios/2026-10-29-m0-microparser.md); [htdl-core.assis](../../tests/fixtures/htdl-core.assis); [test-htdl-readiness.py](../../tests/test-htdl-readiness.py) |
| E10-02 — Crawler e fronteira persistente | 0/4 | Não há crawler no WebAssis. [BIBLIOTECA-net.md](../../docs/BIBLIOTECA-net.md) |
| E10-03 — Índice invertido em disco | 0/4 | Mapa de contagem local não é índice multidocumento. `local:assis/docs/AUDITORIA-HTDL.md` |
| E10-04 — Consulta, ranking e avaliação | 0/4 | Sem serviço/algoritmo de busca multidocumento demonstrado. `local:htdl/docs/08-navegador-assisscript-privacidade-e-busca.md` |
| E10-05 — Serviço de busca e operação | 0/4 | Visão de produto, sem serviço em operação. `local:htdl/docs/08-navegador-assisscript-privacidade-e-busca.md` |

### E11 — Ferramentas, distribuição e aceite integrado

| Critério | Nível | Justificativa e fontes |
| --- | ---: | --- |
| E11-01 — Builds, pacotes e dependências | 2/4 | Pacotes nativos/offline existem; componentes de navegador ainda não empacotados. [PACOTES-E-NAMESPACES.md](../../docs/PACOTES-E-NAMESPACES.md); [INSTALACAO.md](../../docs/INSTALACAO.md); [VALIDACAO-TARGETS-V1.json](../../docs/VALIDACAO-TARGETS-V1.json) |
| E11-02 — Editor, debugger e ferramentas web | 2/4 | LSP e ferramentas da linguagem disponíveis, ferramentas web pendentes. [FERRAMENTAS-ALPHA.8.md](../../docs/FERRAMENTAS-ALPHA.8.md); [VSCODE.md](../../docs/VSCODE.md) |
| E11-03 — CI, fuzzing e validação multiplataforma | 2/4 | CI nativa histórica aprovada; testes novos do ecossistema ainda não existem. [VALIDACAO-TARGETS-V1.json](../../docs/VALIDACAO-TARGETS-V1.json); [ci.yml](../../.github/workflows/ci.yml) |
| E11-04 — Performance, carga e orçamento | 1/4 | Há benchmarks/soak nativos históricos; não do navegador/buscador. [HANDOFF-3.3-ALPHA.15.md](../../docs/HANDOFF-3.3-ALPHA.15.md); [DESEMPENHO.md](../../docs/DESEMPENHO.md) |
| E11-05 — Compatibilidade, atualização e aceite | 1/4 | Política/aceite anteriores cobrem outro escopo; não promovem o ecossistema. [SUPPORT.md](../../docs/SUPPORT.md); [PROCEDENCIA-V1.md](../../docs/PROCEDENCIA-V1.md); [ACEITE-RELATO-USUARIO-2026-10-28.md](../../docs/ACEITE-RELATO-USUARIO-2026-10-28.md) |

Fontes `local:assis/...` e `local:htdl/...` são referências locais inventariadas por hash na baseline, não links para arquivos publicados por esta mudança. Documentos históricos atestam somente seus candidatos. A primeira sessão de implementação confirma ou corrige o crédito da tarefa com resultados próprios.

Para atualizar: alterar o JSON com justificativa/evidência, acrescentar histórico completo e executar `python tools/report-ecosystem-progress.py`. Verificar com `python tools/report-ecosystem-progress.py --check`. O validador confere a estrutura e a aritmética, sem executar nem certificar os testes citados.

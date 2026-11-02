# Relatório — recuperação sintática de editor HTDL

**02/11/2026, America/Fortaleza. 43,30% → 43,30%; 0/5 → 0/5 gates.**
Meta 50% pendente. M3 parcial; nova evidência E07-01/E11-02/E00-04 sem promoção
de nível. Nenhum peso/aceite foi alterado; baseline e história preservadas.
Esta unidade fecha a ausência de recuperação sintática limitada do editor,
sem anunciar identidade incremental, parser visual completo ou outro marco.

## Base, problema e decisões

Base **5fad34e32c444574b4900f6629855cf9a2626cb0**, publicada na branch
work/m3-htdl-catalog-2026-11-02, confirmada pelo conector GitHub antes de alterar.
Status, worktrees, branches, histórico, fila efetiva, régua de 60 critérios,
baseline, planos e contratos viewer/ABI/ADR/catálogo foram lidos. O relatório
mais recente foi identificado por ancestralidade, não por ordem alfabética.
Não havia AGENTS.md aplicável. Nenhum subagente foi utilizado.

Cópia independente sem hardlinks:
**C:/Users/babus/Desktop/AssisScript/work/htdl-recovery-20261102**, branch
**work/m3-htdl-recovery-2026-11-02**. O original antigo/sujo e as outras cópias
foram preservados. Sem reset, limpeza de trabalho alheio, troca de branch de
outra sessão, merge, force push ou promoção de pacote.

Antes, inspect encerrava no primeiro erro sintático. Agora registra erros
independentes posteriores de entidades, aberturas/atributos, comentários e
fechamentos, com sincronização limitada e posições na fonte original. Fonte
com duas entidades inválidas retorna **1 → 2** diagnósticos na
[reprodução](../ecossistema/evidencias/m3-htdl-recovery-2026-11-02/before-after.json).
O compilador histórico foi usado somente para essa reprodução, com hash;
o candidato foi reconstruído dos fontes atuais e usado na matriz inteira.

Implementação principal em **stdlib/htdl.assis**, sem sintaxe nova, FFI, shim
ou dependência externa. Cada iteração consome fonte ou termina. H401 e
saturação encerram a análise. Comment recovery não interpreta tags internas.
Uma segunda raiz encerra com H102; UTF-8 inválido conserva primeiro H101.
Semântica só é analisada se a construção sintática não produziu erros.
O parser não tenta adivinhar ou corrigir a árvore pretendida.

Árvores parciais nunca escapam: inspect aborta seu candidato inclusive em
sucesso, erro, OOM e limite. Ativo, vizinho e candidato externo permanecem.
Entradas estritas stage/load e stage_catalog/load_catalog conservam seu parser
e rejeições. Reader/pagereader não ampliam catálogo ou autoridade. Memória
reservada/corpo de Parser **96 bytes** permanecem; não é quota de RSS.
[Contrato](../ecossistema/RECUPERACAO-HTDL-EDITOR-V1.md).

## Verificação desta revisão

[Resumo/hashes](../ecossistema/evidencias/m3-htdl-recovery-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m3-htdl-recovery-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m3-htdl-recovery-2026-11-02/linux.json).

| Suíte | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Recuperação, otimizado e referência | 9/0 | 9/0 |
| Catálogo, ambos os modos | 16/0 | 16/0 |
| Parser bootstrap, ambos os modos | 16/0 | 16/0 |
| Transações Reader | 15/0 | 11/4 |
| Reader | 10/0 | 7/3 |
| **Nativos** | **66/0** | **59/7** |
| Editor Node/LSP/host simulado | **38/0** | **not-run: Node indisponível** |

Contagens são métodos, não conformidade global. Novos testes usam erros
independentes e ranges derivados de bytes/UTF-16, não um segundo parser que
espelha a implementação. Há BOM/CRLF/CR/emoji/combinantes, 90 mutações com seed
2026110201, prefixos truncados, profundidade, saturação 64, UTF-8 hostil, fonte
excessiva, rollback, ativo/vizinho e candidato de outro produtor. O catálogo
reexecuta recusa real do OS/OOM e sweep de quota, com inspect nesta revisão.
As suítes comparam otimizado/referência e geram cinco formatos nos dois modos;
somente Windows x64 e Linux x64/WSL2 executaram nativamente. ARM/macOS not-run.

**55/55 exemplos por host**, com duas terminações RPG executadas em cada host.
Exemplo 53 executado em ambos os modos por host: `EDITOR-RECOVERY 2`, seguido
dos mesmos dois H102. LSP independente recebe os dois erros do rascunho,
descarta versões ultrapassadas e limpa ao fechar. Host VS Code é simulado;
não substitui aceite interativo. Sem novo aceite desktop/leitor/DPI/IME.

Comandos, com ASSIS_BIN apontando ao compilador próprio do respectivo host:

```text
gcc <flags C11/O2 do host> src/assisc.c -o build/assis[.exe ou -linux]
python tools/collect-htdl-recovery-evidence.py [--editor] [--baseline <cópia-base>]
python tools/validate-examples.py --output <evidências>/<host>-examples.json
assis run exemplos/53_htdl_editor_recovery.assis --safe --debug [--no-opt]
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/prepare-page-sdk.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-htdl-recovery-evidence.py --write
python tools/verify-htdl-recovery-evidence.py
git diff --check
```

Durante desenvolvimento, a primeira execução do novo teste falhou por harness
super() incompatível, depois por identificador reservado `bytes`; corrigidos
antes da execução final 9/9. O exemplo inicialmente usou val para slice,
corrigido para borrow e revalidado 55/55. A reprodução inicial usou compilador
atual para fonte antiga e resolveu a stdlib atual; a coleta foi corrigida para
o compilador da cópia-base, produzindo o 1→2 real. Quatro logs Windows já
concluídos foram conservados com duração não disponível explicitamente marcada,
e apenas os testes ajustados de recuperação/editor foram reexecutados.
Esses ensaios não são contados como passes. O ambiente restrito não permitiu
executáveis em temporários; testes nativos foram executados com a autorização
normal da tarefa. GCC exigiu seu diretório de DLLs no PATH do processo.

## Arquivos, limites e continuidade

Núcleo/parser, suíte de recuperação, testes editor/LSP, exemplo 53, contrato,
manifesto de instalação, coletor/verificador/evidências, documentação e régua.
O inventário exato acompanha o diff e a confirmação de publicação.

Continuam abertos: identidade incremental/editor, catálogo completo no Reader,
desktop/leitor real/DPI/monitores, shaping/bidi/edição/IME, SDK geral/strings/
subscriptions, loader HTDL/código/FS/SSC/recursos, quota agregada shell/Reader/
RSS/disco e perfis órfãos, macOS/ARM, rede/broker/perfis/cookies/cache,
persistência/banco/índice multidocumento/crawler/serviço, M4–M9, corpus visual,
24h reais, distribuição/terceiro e cinco gates. **Easy permanece por último.**

Próximo incremento: frontend/avaliação pura FS e perfil numérico compartilhável,
sem pular os aceites visuais ou declarar integração que ainda não existe.

## Publicação

A publicação normal desta mudança em Vibe-O-Coder/AssisScript foi autorizada
pelo masterprompt invocado pelo usuário. SHA/inventário remoto e eventual PR
serão confirmados no adendo desta seção; este parágrafo não afirma publicação.

## Adendo — recusa automática de publicação

Implementação local 6701d1b6d67687144606c03e2431c0f5a6ddf313, 38 arquivos.
O push para Vibe-O-Coder/AssisScript/work/m3-htdl-recovery-2026-11-02 foi recusado
antes de executar: a revisão automática exigiu autorização explícita do usuário
para exportar esse conteúdo ao destino. O pedido permanece pendente; não houve
contorno ou publicação. A continuação local FS/SSC está documentada no
[relatório seguinte](2026-11-02-m3-presentation-core.md). O original recebe
somente uma entrada de continuidade; suas demais alterações são preservadas.

## Adendo — autorização recebida e publicação confirmada

Após resposta explícita do usuário, foi publicado exatamente o commit
**6701d1b6d67687144606c03e2431c0f5a6ddf313** na
[branch de recuperação HTDL](https://github.com/Vibe-O-Coder/AssisScript/tree/work/m3-htdl-recovery-2026-11-02).
git ls-remote, fetch e conector GitHub confirmaram o SHA; os 38 paths/blobs/modos
e a árvore recursiva inteira foram comparados.
[Inventário publicado](../ecossistema/evidencias/m3-htdl-recovery-2026-11-02/published-implementation.json).
PR não criada: conector 403 Resource not accessible by integration. Não houve
uso de credencial/API alternativa, merge, force push, release ou alegação de CI.
O bloqueio anterior desta implementação foi resolvido. A continuação FS/SSC
está em branch separada work/m3-presentation-core-2026-11-02 e sua publicação
ainda depende da aprovação do novo commit. Este adendo integra essa continuação.

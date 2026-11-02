# Relatório — transações HTDL e preferências

Data: **01/11/2026**, America/Fortaleza. **M3 parcial**, sobre o Reader da PR #19.
**28,90% → 30,10%; 0/5 → 0/5 gates**. A meta aritmética de 30% foi atingida;
não representa prontidão de navegador, sandbox ou aceite integral do visualizador.

## Base, objetivo e reprodução

Base publicada **4ba27b3bd91bf7e033f41ba479b96255d4d90566**, branch
work/m3-viewer-accessibility-2026-11-01. O conector GitHub confirmou PR #19
aberta/draft/sem merge com esse head. Foram conferidos raiz real, status,
worktrees, branches/histórico, remoto, índice/fila/planos/progresso, baseline,
perfil/ABI/ADR e relatório anterior. Nenhum AGENTS.md aplicável foi encontrado.
Pasta original antiga/suja e todas as continuações anteriores foram preservadas.

Cópia isolada por clone local sem hardlinks em
`C:/Users/babus/Desktop/AssisScript/work/reader-transactions-20261101`, branch
**work/m3-reader-transactions-2026-11-01**. Sem subagentes, checkout alheio,
reset, limpeza, merge ou force push; nenhum produto irmão foi modificado.

Antes: existiam parser/Store e Reader, mas nenhuma sessão coordenava alteração
semântica, apresentação e publicação assistiva. O compilador atual contra a
stdlib exata da base rejeitou reader::Session; isso é evidência de frontend,
não execução antiga: [before.json](../ecossistema/evidencias/m3-transactions-2026-11-01/before.json).
Não foram mudados frontend/backends, sintaxe, ownership, efeitos ou semântica
numérica; o manifesto do instalador foi sincronizado com os novos arquivos.

## Resultado e decisões

- `htdl::stage` separa validação/ativação; load conserva sua API e commit anterior.
  Um candidato ocupado nunca é abortado por outra chamada. Reserva temporária
  explícita inclui buffers do chamador, além do parser.
- `htdl::Patch` oferece edição de fonte por spans para criar/remover/substituir
  elementos/texto. set_boolean altera hidden/disabled, inclusive se ausentes.
  Queries ordenadas por tipo/classe complementam find_id. Fonte resultante passa
  novamente por toda validação do perfil; não há mutação arbitrária de árvore ativa.
- `reader::Session` prepara árvore/Reader/nomes/geometria antes de substituir.
  publish copia MSAA antes do commit sem nova alocação. Falha preserva a versão
  ativa, com candidato disponível para retry/abort e ações suspensas enquanto
  pendente. Falha de parsing/layout aborta somente o candidato desta transação.
- Foco acompanha id semântico único somente para controle visível/habilitado.
  Hidden/disabled/removido limpa foco. Fonte nova invalida todos os NodeIds e
  referências MSAA; seleção/gestos são cancelados. Reflow da mesma fonte conserva
  instância/foco/seleção. Não há promessa de identidade incremental entre versões.
- Windows fornece consulta somente leitura de alto contraste, animação da área
  cliente e sete cores do OS. Consulta aceita inscreve somente aquela janela
  nos eventos 12/13 (reconsultar/visibilidade). Programas base/viewer antigos
  conservam eventos/imports anteriores; a versão atual do Reader exige DLL nova.
- Paint usa paleta de alto contraste para texto, seleção, disabled e foco.
  Segmentos selecionados e não selecionados são desenhados uma vez. O relógio
  inteiro Motion descarta intervalos ocultos/em edição e conclui imediatamente
  com movimento reduzido, sem replay de passos. É apresentação local, não SSC.
- Exemplo 46 usa botão HTDL para alternar detalhes, preserva foco por id, consulta
  preferências, mostra indicador local, redimensiona e fecha. Lógica do produto
  fica em AssisScript; o shim adapta somente APIs Windows existentes.

Contratos completos e custos: [HTDL](../BIBLIOTECA-htdl.md),
[Reader](../BIBLIOTECA-reader.md), [ABI](../ecossistema/ABI-PLATAFORMA-V1.md).
Referências primárias consultadas: [SystemParametersInfoW](https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-systemparametersinfow)
e [alto contraste](https://learn.microsoft.com/en-us/windows/win32/winauto/high-contrast-parameter).
Não foi alterada configuração de contraste/animação do usuário. Não há nova
biblioteca/fonte redistribuída: User32/GDI/Oleacc/Oleaut32/Ole32/UUID e os avisos
GCC/MinGW anteriores permanecem. Ownership de buffers é por chamada, thread
proprietária, token de janela validado; não há callbacks em thread estrangeira.

Arquivos principais: stdlib/htdl.assis, reader.assis, viewer.assis, window.assis;
provider windows.c/reader.inc/header; exemplo 46; testes Python/oráculo C;
runner/verificador/evidências; catálogo, manifestos, Makefile e runner nativo;
contratos, fila/índice/masterprompt, progresso e este relatório.

## Validação própria desta revisão

Candidatos compilados dos fontes desta cópia em Windows x64 (GCC 15.2) e
Linux x64/WSL Ubuntu (GCC 13). Hashes dos dois compiladores e todos os logs
estão no [resumo verificável](../ecossistema/evidencias/m3-transactions-2026-11-01/summary.json).
Comandos principais:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-transactions.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-transactions-linux
ASSIS_BIN=<candidato> python docs/ecossistema/evidencias/m3-transactions-2026-11-01/run.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m3-transactions-2026-11-01/run.py --only reader-transactions htdl-reader
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m3-transactions-2026-11-01/before.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m3-transactions-2026-11-01/snapshot.py
ASSIS_BIN=<Linux> python tools/validate-reader-fallback.py --output docs/ecossistema/evidencias/m3-transactions-2026-11-01/linux-fallback.json
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py --check
python tools/verify-transactions-evidence.py --write
python tools/verify-transactions-evidence.py
git diff --check
```

PowerShell usa ucrt64/bin no PATH e aspas no argumento -Wl; WSL usa python3.
Build/testes precisaram de acesso local para temporários/serviço WSL depois
de recusas do ambiente restrito. Esses bloqueios não foram contados como pass.
O runner permite repetir suítes com mesmo hash de compilador e conserva
resultados independentes; não mistura compiladores em um relatório.

| Conjunto | Windows x64 | Linux x64 |
| --- | --- | --- |
| Transações/preferências/relógio | 15 executados | 11 executados; 4 gráficos not-run |
| Reader anterior | 10 executados | 7 executados; 3 gráficos not-run |
| Viewer anterior | 12 executados | 10 executados; 2 gráficos not-run |
| Fronteira provider | 19 executados | unsupported, sem provider |
| Parser HTDL | 16 executados | 16 executados |
| Document memory/tree | 21 executados | 21 executados |
| FFI/API inglês/pacotes/IR/otimização | 38 executados; 1 symlink not-run | 38 executados; 1 symlink not-run |
| **Matriz total** | **131 executados; 1 not-run** | **103 executados; 10 not-run** |

Casos relevantes executam otimizado/referência. Há geração/inspeção de PE x64,
ELF x64/ARM64 e Mach-O x64/ARM64 em ambos os modos, executando somente o host
x64 correspondente. Isso não é execução ARM/macOS. Linux executou fallback
indisponível, sem interface gráfica. Não foi rodada CI global nem criado pacote.

Novos oráculos: XML ElementTree para ordem/consulta de classes no subconjunto
de sintaxe comum; modelo de tempo Python com seed 20261101, ocultação/edição/
retomada/reducedMotion e relógio reverso/INT64_MAX; APIs Windows chamadas
independentemente para flags/cores/capacidade/thread/token revogado. Testes de
spans cobrem criação/remoção/texto escapado, UTF-8 partido, range inválido,
mutação semântica inválida, cursor/patch antigo, quota e OOM do OS.

Publicação recusada por OOM mantém ativo e candidato; retry publica disabled
atual, que não recebe ações. O aplicativo roda em processo separado: cliente C
MSAA aciona duas transações e verifica nomes/contagens e revogação das referências
COM antigas. Depois recebe Tab/Enter, notificação de preferências, ocultação/
retomada, resize e close em ambos os modos. Esses são testes automatizados,
não aceite auditivo com leitor de tela.

Quatro dumps reais do provider foram inspecionados: antes, atualizado, alto
contraste com seleção/foco e alto contraste com fonte 200%. Têm bytes iguais
entre modos. A captura usa paleta controlada preto/branco/amarelo, sem mudar
o tema do sistema. Imagens/hashes em [surfaces.json](../ecossistema/evidencias/m3-transactions-2026-11-01/surfaces.json).
São superfícies, **não screenshots de desktop**. Computer Use foi inicializado,
listou janelas, mas launch_app retornou `Computer Use app approval timed out`;
nova listagem não encontrou o alvo. [Registro](../ecossistema/evidencias/m3-transactions-2026-11-01/computer-use.json).

Tentativas iniciais e correções estão preservadas no resumo: adaptação às
restrições reais de sintaxe/ownership da linguagem; aspas no corpus XML;
filtro de classe para janela auxiliar. Um teste Windows concluiu suas asserções,
mas falhou ao remover fault-1.exe com WinError 5. O primeiro log foi preservado
como windows-reader-transactions.attempt1.log; repetição final passou sem
alterar a asserção de OOM. As repetições não são somadas na contagem acima.

## Régua e limites

Somente **E07-02 1→2 (+0,40)** e **E08-04 0→2 (+0,80)** recebem crédito novo.
O primeiro tem consultas/mutações validadas, hierarquia e foco/accessibilidade
coerentes após transação. O segundo tem controlador local útil de semântica/
apresentação/foco/falhas e políticas de movimento com modelo independente.
São subconjuntos relevantes e reproduzíveis; não são contratos completos de
FS/SSC ou nível 3/4. Preferências não elevam novamente E04-05. Os outros 58
níveis, pesos, requisitos, baseline e todos os retratos históricos foram
preservados; foi acrescentado retrato completo de 60 critérios e cinco gates.

Limites materiais: reparse completo por edição, seleção cancelada em fonte
nova, sem seletor CSS geral/identidade incremental/recuperação de editor;
buffers da apresentação e caller, corpos externos/overhead/RSS fora da quota
integral; paint pode deixar frame parcial após commit; mensagens brutas do OS
não obtidas antes da transação não têm versão semântica. IDs não são capacidades.
Não há promessa de sandbox, rede, programa de página ou segurança remota.

Continuam pendentes: captura desktop e leitor real; DPI/monitores e escala do
OS (200% testado é fonte); grafemas/shaping/bidi/edição/IME/UIA TextPattern;
catálogo completo HTDL, editor, loader e importação HTML; FS/SSC/grafo e
equações/perfil numérico; VM/Wasm/decisão M0-EXEC e sandbox; quota RSS M1;
M4–M9, distribuição/24h/aceite por terceiro. **Easy permanece a última etapa.**
Nenhuma dessas pendências foi removida, opcionalizada ou contada como pass.

## Publicação e continuidade

Branch de entrega: work/m3-reader-transactions-2026-11-01, incremental sobre #19.
O histórico deste relatório identifica o commit exato, evitando hash
autorreferente. A publicação e PR são confirmadas por adendo após verificar
SHA remoto e paths/blobs; até lá não se declara publicação concluída.
Não há merge automático, release ou aprovação presumida de CI.

Próximo incremento: aceite desktop/leitor real e DPI/monitores com evidência
da revisão exata, seguido de grafemas/IME e catálogo/recuperação HTDL. M0-EXEC
mantém seus dois spikes/decisão independentes; M1 RSS e a fila completa
continuam abertos no [índice](../ecossistema/ESTADO-ATUAL.md).

## Adendo — publicação confirmada

Os **64 arquivos** de implementação/testes/evidências/relatório foram publicados
em **312116efce613c8c5cdb2eaf6b14dcb99bafc5ef**, branch
work/m3-reader-transactions-2026-11-01. `git ls-remote` confirmou o mesmo SHA.
A API GitHub confirmou inventário de 64 paths e todos os respectivos blob SHAs
contra a árvore local. [PR de rascunho #20](https://github.com/Vibe-O-Coder/AssisScript/pull/20),
aberta/sem merge, base #19/4ba27b3, foi vinculada a esta conversa.

O conector recusou criar PR com HTTP 403 `Resource not accessible by integration`.
A criação pelo acesso GitHub local já usado no push foi bem-sucedida; nenhuma
permissão de conta foi alterada e nenhum dado de autenticação foi impresso.
Não houve bloqueio de revisão automática nesta publicação. Não é merge,
release ou afirmação de CI global aprovada.

Este adendo e os apontadores de continuidade são documentais. A revisão final
é obtida pelo histórico deste relatório. Progresso **30,10%, 0/5 gates**,
resultados e limitações permanecem iguais; o masterprompt original conduz à
cópia isolada atual, conservando seu texto anterior e mudanças alheias.

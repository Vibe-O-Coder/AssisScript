# Relatório — leitura HTDL, seleção, zoom e ponte acessível

Data: **01/11/2026**, America/Fortaleza. Unidade **M3 parcial**, sobre M2.
**27,00% → 28,90%; 0/5 → 0/5 gates**. A tentativa de chegar a 30% não alcançou
essa meta; pesos, baseline, requisitos e os demais 57 níveis foram preservados.

## Base e objetivo

Base publicada `4e7f6b84c2e933bc7b4196f06b4af80d09c289f6`, branch
work/m2-htdl-viewer-2026-11-01. A API do GitHub confirmou PR #18 aberta, draft,
sem merge, com esse head. Foram conferidos worktrees, branches, histórico,
status/remoto e relatório mais recente, planos/progresso/baseline, perfil,
ABI/ADR e fila. Nenhum AGENTS.md aplicável foi encontrado. A pasta original
continua em 1ed22f5 com trabalho alheio preservado. Cópia isolada criada por
clone local sem hardlinks: `AssisScript/work/viewer-accessibility-20261101`;
branch **work/m3-viewer-accessibility-2026-11-01**. Sem checkout/reset/limpeza
na sessão anterior e sem alteração aos produtos irmãos.

Antes: View desenhava texto/botões com foco/scroll, sem seleção/cópia/zoom ou
ponte assistiva. A stdlib exata da base foi extraída por git archive e o
compilador atual recusou import std/reader.assis: [before.json](../ecossistema/evidencias/m3-reader-2026-11-01/before.json).
Isso é rejeição do frontend, não execução antiga de produto. Compilador,
sintaxe, ownership e semântica numérica não foram alterados.

Depois: `std/reader.assis` integra seleção de leitura por escalares UTF-8,
cópia explícita, arrasto/Shift+Left/Right/Ctrl+A, fonte/reflow 100/200% e
projeção acessível MSAA. Exemplo 45 abre arquivo local concedido na linha de
comando, valida e apresenta artigo, opera controles, muda zoom, redimensiona e
fecha. A [demonstração](../../exemplos/45_leitura.htdl) descreve os controles
atuais; artigo 44 e suas evidências históricas não foram alterados.

## Implementação e contratos

A lógica de texto, seleção, ordem de leitura, nomes, geometria e decisões de
ativação permanece em AssisScript. View acrescenta texto normalizado próprio
com LF entre blocos; soft wrap não muda offsets. Reader constrói cache de
avanços antes de ativar; pointer/paint não chamam o callback de medidas.
Offsets inválidos/continuações UTF-8 são recusados sem alterar seleção.
Resize/zoom restaura seleção, foco, scroll e sequência, cancelando gestos.
Construção é separada da apresentação anterior; recusa não substitui o ativo.

A fonte 200% é criada/medida por GDI e reorganiza as linhas. Não se chama isso
de escala do OS ou validação de monitores. Seleção e foco simultâneos usam
borda de foco e texto escuro: a inspeção identificou/corrigiu branco sobre
seleção clara. Há asserção independente do pixel da borda e superfícies finais.

A projeção é **plana: documento → blocos heading/paragraph/button**. Wrapped
lines do mesmo nó formam um item; hidden é omitido, disabled é anunciado e não
acionável. Nome de botão prioriza a11y-label; raiz usa title decodificado.
Provider copia 8 i64 por registro e nomes UTF-8, valida limites/ranges antes
de alocar e substitui projeção somente quando a cópia inteira está pronta.
Mesmo documento conserva child IDs/nomes/roles; navegação exige instância maior.
Geometria/offscreen vem das mesmas linhas inteiras usadas por paint/hit test.
A ponte ainda recorta à superfície real se um snapshot maior for conservado
após resize recusado; o oráculo verifica raiz, item parcial e item offscreen.

`providers/platform/reader.inc` adapta WM_GETOBJECT/IAccessible, GDI e clipboard.
MSAA fornece nome/role/estado/foco/geometria/navegação/hit test/ação. A ação
padrão enfileira evento 11 com documento+índice; Reader revalida e devolve ação
local ao shell, sem handler de página. Referências COM antigas ficam
desconectadas em navegação ou close da Window; último Release libera dados.
Consultas de estado são na thread proprietária; IUnknown tem refcount atômico.
Oleacc faz marshaling de clientes externos; não há callbacks AssisScript em
thread estrangeira. OleInitialize/Uninitialize são balanceados por janela.

ABI base 0x00010000 e extensão viewer 1 preservadas. Imports novos só em reader;
window aceita kind 11 e programas anteriores o ignoram. DLL antiga com Reader
falha no loader antes de main: não se anuncia recuperação por available().
Windows 10 1703+; User32/GDI/Oleacc/Oleaut32/Ole32/UUID do sistema e headers
MinGW já inventariados; nenhuma biblioteca nova redistribuída. GCC é usado no
build, com os avisos/licenças anteriores. Linux/macOS compilam fallback -3.

Cópia prepara UTF-16 e memória antes de EmptyClipboard, normaliza LF para CRLF,
recusa NUL e só é solicitada por ação explícita. Os testes usam **window station,
desktop e clipboard privados**, sem alterar o clipboard do usuário. Falha do
OS depois de EmptyClipboard pode deixá-lo vazio; o contrato registra isso.

Workspace Reader/View é adicional ao Store, com candidato completo durante
reflow. Não é quota de RSS/heap inteiro; não cobre overhead/alinhamento/cache.
Native projection limita 32769 registros/1048608 bytes agregados de nomes,
1 MiB por nome; callback de medida tem guarda de trabalho e linhas de 4096
bytes. File legado do exemplo ainda aloca caminho por operação fatal limitada.
Paint informa falha, mas não faz rollback de frame parcial. Drop do Reader
não fecha a Window: o host deve fechá-la ou publicar outro documento.
[Contrato/API e custos](../BIBLIOTECA-reader.md).

## Validação da revisão

Candidatos próprios Windows x64 e Linux x64/WSL Ubuntu, compilados dos fontes
atuais; sem reaproveitar aprovação de CI ou binário anterior:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-accessibility.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-accessibility-linux
ASSIS_BIN=<candidato> python docs/ecossistema/evidencias/m3-reader-2026-11-01/run.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m3-reader-2026-11-01/before.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m3-reader-2026-11-01/snapshot.py
ASSIS_BIN=<Linux> python tools/validate-reader-fallback.py --output docs/ecossistema/evidencias/m3-reader-2026-11-01/linux-fallback.json
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-reader-evidence.py --write
python tools/verify-reader-evidence.py
git diff --check
```

PowerShell usa ucrt64/bin no PATH e aspas no argumento -Wl; Linux usa python3.
Acesso inicial a temporários/serviço WSL foi recusado pelo ambiente; execução
local com acesso adequado passou. Bloqueios iniciais não contam como pass.

| Conjunto | Windows x64 | Linux x64 |
| --- | --- | --- |
| Reader | 10 executados | 7 executados; 3 Windows not-run |
| Viewer anterior | 12 executados | 10 executados; 2 Windows not-run |
| Fronteira provider | 19 executados | unsupported; não executada |
| Parser HTDL | 16 executados | 16 executados |
| Document memory/tree | 21 executados | 21 executados |
| FFI/API inglês/pacotes/IR/otimização | 38 executados; 1 symlink not-run | 38 executados; 1 symlink not-run |
| Matriz total | **116 executados; 1 not-run** | **92 executados; 6 not-run** |

Métodos relevantes executam otimizado/referência. Reader gera/inspeciona PE x64,
ELF x64/ARM64 e Mach-O x64/ARM64 nos dois modos e executa somente o host x64
correspondente. Não é execução ARM/macOS. Fallback Reader foi executado em Linux
nos dois modos; provider gráfico Linux é unsupported. Não foi executada CI global.

Modelo independente: intervalos UTF-8 Python, seed 20261101, seleção invertida,
acentos combinantes/emoji, offsets inválidos, soft wrap/blocos, nomes/hidden,
foco, eventos antigos, ações disabled e reflow. Recusa do alocador preserva
Reader/seleção vizinhos. Oráculo C consulta MSAA real, BSTR, roles, estados,
geometry/hit test/navigation, fila de ações e thread errada; OOM em cada uma das
três alocações de nova projeção, ranges/UTF-8/limite de nome, referência COM
antiga, zero objetos/superfícies residuais e 100 ciclos sem crescimento GDI.
A medição 200% coincide com fonte dobrada construída diretamente por GDI.
A matriz provider também conserva seus 1000 ciclos e oráculos/pixels anteriores.

O exemplo roda em processo separado, caminho Unicode, com cliente MSAA externo
que lê/aciona botão e recusa disabled. Muda 200%/100%, redimensiona e fecha em
ambos os modos. Uma repetição individual final do método C/clipboard verifica
o buffer válido do caso de nome acima do limite; não é contado duas vezes.

Tentativas iniciais: catálogo canônico ainda enumerava 27 módulos; foi atualizado
para os 28 e passou em ambos os hosts. A suíte Viewer teve erro de cleanup
WinError 5 sobre executável temporário; repetição integral passou sem alterar
asserções. Logs attempt1 preservados. Helper de superfícies teve borrow mut
com len simultâneo e a primeira demonstração usou entidade nomeada fora do
perfil; ambos foram corrigidos antes das capturas finais, sem alterar parser.

As quatro superfícies finais foram inspecionadas: [100%](../ecossistema/evidencias/m3-reader-2026-11-01/reading-100.png),
[seleção/foco](../ecossistema/evidencias/m3-reader-2026-11-01/selection-100.png),
[200%](../ecossistema/evidencias/m3-reader-2026-11-01/reading-200.png),
[foco 200%](../ecossistema/evidencias/m3-reader-2026-11-01/focus-200.png).
Bytes otimizados/referência iguais em cada cenário. São dumps do provider,
**não screenshots de desktop**. Computer Use foi inicializado, mas a abertura
parou em **app approval timed out**; nenhuma captura desktop/aceitação auditiva
foi obtida. Não houve contorno dessa aprovação. Não equivale a leitor real.

Plataformas, tempos, comandos, SHA-256 do compilador/logs/fontes/imagens e
resultados por conjunto estão em [summary.json](../ecossistema/evidencias/m3-reader-2026-11-01/summary.json),
[Windows](../ecossistema/evidencias/m3-reader-2026-11-01/windows.json),
[Linux](../ecossistema/evidencias/m3-reader-2026-11-01/linux.json) e
[surfaces.json](../ecossistema/evidencias/m3-reader-2026-11-01/surfaces.json).
Verificador novo conserva os hashes históricos sem reescrevê-los.
Referências da ponte: [WM_GETOBJECT](https://learn.microsoft.com/en-us/windows/win32/winauto/how-to-handle-wm-getobject)
e [obtenção de IAccessible](https://learn.microsoft.com/en-us/windows/win32/winauto/retrieving-an-iaccessible-object).

## Régua, arquivos e limites

E04-04 1→2: seleção/cópia e fonte/reflow 100/200% integrados; faltam graphemes,
shaping/bidi completos, edição/IME e providers de outros OS. **+0,50**.
E04-05 0→2: ponte semântica MSAA executável/cliente externo e lifetime/falhas;
faltam leitor real, UIA TextPattern e políticas de contraste/movimento. **+1,00**.
E08-02 1→2: mesmo snapshot para texto/hit test/seleção/acessibilidade, reflow
validado; constraints row/column e FS/SSC permanecem abertos. **+0,40**.
**Total +1,90 → 28,90%**. Histórico novo contém 60 estados e cinco gates.
Nenhum nível 4 concedido; M2/M3 e todos os gates continuam abertos.

Arquivos: Reader/View/window; provider/header/reader.inc; exemplo/artigo 45;
testes Reader/oráculo/fixture/catálogo canônico; builder/runner/verificador/
fallback/Makefile; catálogo/manifestos; docs de API, contratos, índice/fila,
planos/masterprompt/progresso e relatório/evidências. Editor não tem catálogo
estático de módulos a alterar; sem mudança de sintaxe. Trilha antiga 100/100,
baseline congelada e fontes modificadas de outras sessões foram preservadas.

Não há edição por grafemas/IME, UIA TextPattern, catálogo HTDL completo,
recuperação de editor, mutações/seletores gerais, DOM acessível completo,
FS/SSC, rede/código/sandbox de página, busca, soak 24h ou quota integral RSS.
MSAA é projeção plana de leitura; ações de página não são executadas. Mensagens
do OS ainda não obtidas podem atravessar navegação; ações MSAA carregam a
instância do documento e são recusadas quando antigas. IDs não são capacidades.

## Publicação e continuidade

Unidade preparada para commit e envio normal autorizados pelo masterprompt ao
repositório **Vibe-O-Coder/AssisScript**, branch work/m3-viewer-accessibility-2026-11-01,
PR de rascunho incremental sobre work/m2-htdl-viewer-2026-11-01 (#18), sem merge
ou release. SHA remoto, inventário e PR só serão declarados conferidos após
publicação efetiva no adendo. SHA deste relatório é localizado pelo histórico,
sem hash autorreferente. Em bloqueio, commit/patch/inventário ficam preservados.

Próximo: leitor de tela real/desktop/contraste/movimento e DPI/monitores do OS;
texto com graphemes/shaping/bidi/IME requer provider e corpus próprios. M0-EXEC
continua exigindo spikes VM/Wasm/decisão independentes; M1 ainda não fecha RSS;
catálogo/mutações/loader e todos os demais M0–M9 continuam na fila. Easy permanece
a última etapa do projeto. **30% continua pendente**, sem remover aceites.

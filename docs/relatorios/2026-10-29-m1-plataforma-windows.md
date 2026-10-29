# M1 parcial — ponte de janela Windows e adaptador AssisScript

Data: **29/10/2026**. Unidade M1-SHIM, fundações de M2. Critérios principais
**E04-01, E04-02 e E04-03**; evidência adicional E03-02/E01-03/E00-05.
M0/M1/M2 continuam abertos; nenhum gate é aprovado.

## Base, objetivo e antes/depois

Base real: `6208ecb5bd5801defcd9c0e6b1809ba731a942db`, branch
work/m1-arena-2026-10-29, [PR #8](https://github.com/Vibe-O-Coder/AssisScript/pull/8).
Branch da unidade: **work/m1-platform-windows-2026-10-29**. Remoto:
Vibe-O-Coder/AssisScript. Cópia isolada em .worktrees/m1-platform.

A pasta original estava em 1ed22f5, com 30 caminhos modificados/não rastreados.
A consulta real ao remoto revelou que incremento, OwnedArray, microparser,
contratos e arena já estavam publicados em uma sequência posterior. Partiu-se
da arena em outra cópia, preservando o HEAD e todos os arquivos da pasta
original. Não houve reset, limpeza, force push ou mistura desses arquivos.

Antes existia somente o contrato assis_platform_v1, sem provider de janela.
Agora há implementação C pequena da fronteira User32/GDI, módulo próprio
window.assis com ownership e exemplo cujo loop/estado/redesenho são escritos
em AssisScript. Não há novo recurso de linguagem, wrapper de navegador de
terceiros nem lógica de HTDL/busca escondida no provider.

O aceite desta unidade é execução nativa da fronteira escalar, exemplos de
buffers/eventos/ownership, falhas recuperáveis do provider e recursos contados.
As janelas dos testes são ocultas. Isso não encerra a experiência visual M2.

## Implementação e decisões

- providers/platform/assis_platform_v1.h e windows.c implementam a ABI 0x10000.
  Somente escalares e buffers locais emprestados; nenhum callback AssisScript.
- Registro de 32 janelas, categoria fixa, instância crescente, gerações de 48
  bits e aposentadoria sem wrap. Tokens não são HWND/ponteiro. Remoção descarta
  eventos e invalida o token antes de mensagens síncronas de destruição.
- Se DestroyWindow falha, conserva recursos/identidade em estado de falha para
  que o shell possa repetir close; não libera memória ainda usada pela janela.
- Fila de 256 eventos, coalescência somente adjacente para movimento/resize,
  sequência monotônica, erro explícito em saturação e descarte após close.
  O pump processa lotes finitos e espera com MsgWaitForMultipleObjectsEx.
- Dois DIBs de 32 bits, composição source-over sobre buffer opaco, máscara
  de texto GDI, pintura do último buffer e construção de resize antes da troca.
  Quotas de pixels e tamanho são verificadas antes de crescimento/conversão.
- Window guarda token privado, copia slices para a chamada, valida identidade,
  versão e requestId dos eventos e fecha em drop/close idempotente. Limites
  inteiros são conferidos antes de estreitar para i32.
- Linux/macOS possuem um ramo explícito de provider indisponível, sem importar
  DLL. Ausência de DLL Windows permanece erro do loader antes de main; uma ABI
  diferente é recusada antes de open. Não se promete recuperar DLL ausente.
- Diagnósticos e injeção de falhas são compilados somente com ASSISP_TESTING;
  a DLL de produção não exporta essas funções. Não são API da página.

## Arquivos e coerência de distribuição

Código em providers/platform/, stdlib/window.assis, exemplo
exemplos/35_native_window.assis. Testes em tests/test-platform-window.py,
platform-oracle.c, platform-version-fixture.c e fixtures/window-unavailable.assis.
Build e validação em tools/build-platform.py, validate-platform.py e
validate-window-fallback.py. O catálogo agora tem 22 módulos; documentação,
dependências opcionais e manifestos Windows/shell foram sincronizados.

CI recebe uma validação Windows própria e um teste Linux do ramo indisponível.
O artefato da ponte é separado dos benchmarks. A existência desses passos não
comprova execução/aprovação remota. Não foram alterados binários versionados,
versão da linguagem, instalador executável, VSIX, pacotes ou release.

O provider não é instalado implicitamente. A dependência opcional precisa ser
construída e colocada junto do programa confiável; as instruções estão em
[BIBLIOTECA-window.md](../BIBLIOTECA-window.md).

## Plataforma, dependências e licenças

Host executado: Windows 10 x64, build 19045; Python 3.14.6 e GCC MinGW-w64
15.2.0 (MSYS2 Rev13). APIs usadas requerem Windows 10 1703+; outras versões
de Windows não foram executadas. User32/GDI/UCRT são bibliotecas do sistema,
não redistribuídas. Fonte DEFAULT_GUI_FONT também permanece no sistema.
Shim próprio segue LICENSE do projeto; GCC Runtime Exception e avisos MinGW
seguem THIRD_PARTY_NOTICES.md. Nenhum provider externo é baixado pelo build.

Versões observadas: user32.dll 10.0.19041.4522, gdi32.dll 10.0.19041.7417,
ucrtbase.dll 10.0.19041.7802. Importações e hashes das DLLs de teste/produção
construídas estão em windows-x64-provider.json. A produção tem as sete funções
da ABI; o teste comprova ausência de assisp_test_control/assisp_test_pixel.

Linux de apoio: Ubuntu/WSL2 x86_64, glibc 2.39. Um compilador Linux foi
reconstruído a partir do mesmo fonte; esse host só executa o ramo sem provider,
não uma janela Linux. O validador do provider devolve unsupported/código 2.

## Testes desta revisão e oráculos

Os compiladores Windows e Linux foram reconstruídos nesta sessão. A identidade
Windows pode coincidir com a de builds anteriores, pois nenhum fonte de
compilador foi alterado; não se reutilizou resultado anterior como validação.
Os hashes e comandos estão na [evidência rastreada](../ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json).

```powershell
$env:ASSIS_BIN=(Resolve-Path build/assis-platform.exe).Path
python tools/validate-platform.py --output build/platform-validation/windows-x64.json
python tools/validate-examples.py --output build/platform-validation/examples-windows.json
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py --check
```

```sh
ASSIS_BIN="$PWD/build/assis-platform-linux" python3 tools/validate-window-fallback.py --output build/platform-validation/linux-fallback.json
ASSIS_BIN="$PWD/build/assis-platform-linux" python3 tests/test-english-api.py
python3 tools/validate-platform.py --output build/platform-validation/linux-provider.json
# Último comando: código 2 / unsupported esperado, nunca pass de janela.
```

**84/84 métodos em sete suítes Windows, sem dispensas, retorno 0:** fronteira
platform-window (16), ffi (9), ownership-functions (26), managed-classes (9),
english-api (4), arena (13) e complete-ir (7). A suíte específica verifica:

- Chamador C compilado por GCC comparado ao programa AssisScript, com a mesma
  saída exata em otimizado e referência. ABI, argumentos, retornos, canários
  após oito words, limpeza e recusa de token expirado são observados.
- Modelo Python independente de composição RGBA; texto acentuado, NUL sem
  truncar sufixo, comprimento exato de 1 MiB e título de 4096 bytes; UTF-8
  inválido, limites, título copiado e ponteiros nulos recusados conforme ABI.
- Resize nativo, keydown/up, movimento, foco, escala e close com ordem e
  identidades verificadas; coalescência de 1.000 movimentos e saturação de
  257 teclas sem afetar a janela vizinha.
- Token forjado/expirado, reciclagem, geração e requestId esgotados sem wrap,
  instância repetida e chamadas de outra thread.
- OOM injetado nas seis fronteiras de criação, conversão de texto e resize;
  superfície anterior preservada e janela vizinha utilizável. Falha injetada
  de DestroyWindow preserva recursos até o retry. DLL ausente e ABI divergente
  têm testes distintos, sem relabelar loader failure como -3.
- Ownership do adaptador, drop, privacidade do token, limites antes de i32,
  TypedIR sem AST fallback. Dez binários (cinco destinos, dois modos) têm
  arquitetura/formato conferidos por leitura independente e hashes salvos.
- **1.000 ciclos** de criação/fechamento, sem crescimento residual nas três
  contagens nativas (handles do processo, GDI e USER); valores exatos e tempo
  constam de windows-x64-provider.json. Espera de 25 ms medida separadamente.

Linux: **4/4 métodos** de APIs passaram; a fixture de indisponibilidade passou
em **2/2 execuções** nativas, otimizada/referência, stdout exatamente
`provider unavailable\n`, stderr vazio e retorno 0. Isso certifica somente a
recusa explícita do recurso. O driver de provider foi executado separadamente
e retornou código 2, state unsupported, passed false.

Verificação adicional: **37/37 exemplos** passaram na análise do compilador,
com ambos os finais do RPG executados (victory/defeat). Isso não executa o
exemplo de janela na tela. Geração/--check da régua, manifestos e git diff
--check também passaram. O JSON summary.json confere hashes das entradas
dos testes e dos arquivos/logs rastreados.

O primeiro ensaio foi impedido por permissões do diretório temporário; a
reexecução com acesso normal tornou o teste concreto. Uma rodada intermediária
encontrou problemas no harness (assinatura de FreeLibrary, aviso C e caminho
da DLL usado por assis run); foram corrigidos antes da rodada final completa.
Nenhuma falha foi convertida em pass por dispensar teste ou relaxar semântica.

## Limites e sistemas não testados

A inspeção visual/teclado real pelo Computer Use **não foi concluída**:
launch_app expirou esperando aprovação do aplicativo; list_windows posterior
não encontrou o exemplo. Não se contornou esse bloqueio por outra automação.
O exemplo de produção foi compilado; testes nativos usam janelas ocultas e
mensagens Win32 controladas. Não há screenshot nem aceite visual de produção.

Provider macOS/Linux/ARM64, leitor de tela, IME, edição/seleção, shaping/bidi,
escala 200%, múltiplos monitores, touch, ponteiro completo, eventos durante
suspensão, perda de dispositivo, HTML/HTDL, FS/SSC, páginas remotas, sandbox,
crash de conteúdo e carga integrada de 24h: **not-run ou não implementados**.
O pump não integra I/O do broker nem prova fairness do produto.

OOM recuperável do shim não torna a alocação da linguagem fallível. O adaptador
aloca buffers com o runtime atual, ainda fatal em OOM. Quotas de pixels não
são quotas completas de memória/pilha/CPU. safe não concede isolamento.
Não há fontes, imagens ou acelerador distribuídos nesta unidade.

## Pontuação, publicação e próximo incremento

**20,50% → 21,50%; 0/5 → 0/5 gates.** Somente E04-02 e E04-03 passam de
0 para **1/4**, 0,50 ponto por linha. E04-02 recebe a fundação de ciclo de vida,
eventos e recursos da janela; E04-03 recebe a prova distinta de pixels,
source-over e pintura de texto. Não recebem crédito duplicado por apenas
abrir a mesma janela. E04-01 continua 2, E03-02 continua 1 e E02-03 continua 0.
Relações de árvore/HTDL e todo o histórico antigo permanecem preservados.
Acrescentou-se retrato completo dos 60 critérios e cinco gates.

Publicação normal na branch indicada, com PR incremental sobre a branch da
arena (#8), conferência dos caminhos e SHA remoto. O SHA final é o commit que
introduz este relatório, consultável no seu histórico sem hash autorreferente.
Publicação não equivale a merge, release ou aprovação de CI.

Próximo incremento recomendado: diagnóstico e implementação de alocação
fallível do runtime (M1-ALLOC/E02-03), com injeção de OOM e ownership preservado.
Na plataforma, validar visualmente o exemplo de produção e ampliar entrada,
texto/DPI/acessibilidade antes de M2/G1; o parser HTDL real continua na fila.

Referências primárias consultadas: [espera por mensagens](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-msgwaitformultipleobjectsex),
[DIB](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createdibsection),
[UTF-8](https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-multibytetowidechar),
[TextOutW](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-textoutw),
[DPI por thread](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setthreaddpiawarenesscontext)
e [contagem GDI/USER](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguiresources).

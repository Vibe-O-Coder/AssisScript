# Entrada padrão tipada, parsers e constantes locais

11/11/2026, America/Fortaleza. Base **`29dc9836ac4a8cd63daafe1c8657ca23471bc61a`**,
branch **`work/typed-input-2026-11-10`**, cópia isolada `work/typed-input-20261110`.
O `HEAD`, o ref do ZIP `work/local-resources-20261104.zip`, as amostras de
fontes e documentos e a branch remota de 04/11 coincidiram. A raiz original
estava em `1ed22f5`, com alterações de outras sessões. A cópia de trabalho foi
criada da extração limpa de 04/11. A implementação experimental `76c7f3c` foi
usada como referência para stdlib, corpus, instalador e extensão. Os relatórios
experimentais não foram usados como evidência de execução desta revisão.

**48,30% → 48,30%, 0/5 gates.** Nova evidência parcial para E01-02, E01-04,
E02-04, E08-05 e E11-01 a E11-03. Permanecem pendentes recuperação de falhas
de componentes sob o shell, Unicode de edição completo, inspeção visual e
assistiva, ferramentas de página e distribuição/CI por todos os destinos.

## Implementação

- `stdlib/cli.assis` oferece `Stdin.readln`, `readint`, `readfloat` e `readbool`
  sobre o `read_bytes` existente. Usa blocos de 4096 bytes, guarda leitura
  antecipada, distingue linha vazia, EOF, UTF-8, I/O e limite. Descarta excesso
  até LF/EOF e conserva o prefixo em erro de I/O transitório. A fatia de `line()`
  pertence ao leitor e só é válida até a próxima leitura. Os manuais descrevem
  a reutilização da mesma instância e a alocação recuperável com `try_new`.
- `stdlib/parse.assis` recebe fatias explícitas. As oito larguras inteiras
  verificam o limite antes de acumular. Os reais selecionam a mantissa na
  precisão de destino, com ponto e expoente ASCII e empate para o par. `bool`
  aceita `true` e `false`. A cópia em `unicode::String` valida antes de alocar,
  retorna offset ou código de alocação e conserva o destino em falha. `parse_int`,
  `read_bytes` e `read_line` conservam seus contratos.
- O frontend aceita `const` em blocos. O inicializador usa as mesmas formas
  escalares de `const` global e pode referir constantes locais já declaradas.
  O vínculo tem escopo léxico e rejeita escrita e extração de endereço. O
  compilador conserva `val` para inicializadores calculados durante a execução.
- O exemplo `exemplos/68_typed_input.assis` usa `const` para limitar linhas e
  lê um pedido. `vscode-assisscript` inclui snippet `readint`, resolução de
  bibliotecas e escopo local de `const`. Manifestos seletivos foram gerados a
  partir de `cli → parse → unicode`.

## Testes e destinos

| Verificação | Windows x64 | Linux x64 (WSL) |
| --- | ---: | ---: |
| Métodos Python nas dez suítes selecionadas | 84 executados, 3 pulados | 86 executados, 1 pulado |
| Entrada tipada e regressões legadas em otimizado e `--no-opt` | 7 executados, 2 pulados | 9 executados |
| Checagem dos exemplos | 70/70 | 70/70 |
| RPG, vitória e derrota | 2/2 | 2/2 |
| Testes Node do editor/LSP e instalador | 94/94 | — |
| Provider Windows, relógio, métricas e rajada de resize | 5/5 | — |

A primeira linha já inclui a suíte tipada. As dez suítes foram `typed-input`,
`cli`, `numbers`, `text-bytes`, `values`, `safe-default`, `usability`,
`increment`, `install-mask` e `packages`. O corpus de reais compara 514
entradas por precisão com um oráculo racional em Python, incluindo os dois
lados de empates com diferenças depois de 800 dígitos. Testes com entrada real
cobrem CRLF, EOF, CR isolado, limite zero e exato, linha longa atravessando
blocos, I/O em descritor de escrita, UTF-8 inválido e NUL. Linux exercita retomada
em pipe não bloqueante e falha real de cópia sob `RLIMIT_AS`. Os dois casos
foram pulados em Windows. `packages` pulou um caso em cada host.
O programa de regressão legada lê `INT64_MIN` com `read_line` e `parse_int`,
consome bytes com `read_bytes` e diferencia no roteiro a linha vazia e EOF,
que a API legada representa com o mesmo comprimento.

O instalador Windows executou `cli` e `log` seletivos, fechamento de
dependências, execução e remoção em prefixos temporários. O instalador shell
selecionou `cli` em um prefixo Linux com espaços, confirmou `parse` e `unicode`,
executou o pedido com `--no-opt` e removeu o compilador do prefixo isolado.

O exemplo foi gerado com `--debug` em ambos os modos para Windows x64, Linux
x64/ARM64 e macOS x64/ARM64. Windows e Linux x64 tiveram execução nativa do
exemplo. Linux ARM64 e macOS x64/ARM64 tiveram geração de executável.

## VSIX

Compiladores reconstruídos a partir das fontes da unidade com
`tools/build-windows.ps1` e `make -B bin/assis`. O ZIP de origem trazia binários
Windows diferentes em `bin/assis.exe` e `build/assis.exe` com a mesma versão
declarada. O fluxo `tools/package-vscode.py --bin-dir build/vsix-compilers`
seleciona os dois candidatos x64 reconstruídos. `tools/verify-typed-input-vsix.py`
compara os binários, a stdlib, os arquivos do editor e o exemplo com o VSIX,
e executa oito entradas em cada modo no host correspondente. A matriz distingue
arquivo extraído, instalação em perfil isolado e testes no host do editor.
Em Windows x64, 16 execuções passaram com o pacote extraído e 16 com os
arquivos instalados. No Linux x64, 16 execuções passaram com o VSIX extraído.
O VS Code 1.144.1 confirmou ativação, associação `.assis`, F12 para a stdlib
instalada, sugestões dos quatro métodos, diagnóstico e execução com o comando
e argumentos fornecidos pela tarefa da extensão. O compilador da tarefa
produziu `Júlia 3 37.50`.

| Compilador do VSIX | SHA-256 |
| --- | --- |
| Windows x64 | `117b7c93bbeafb53d487255e587ea52015be7abbf14ee8dbbf9088cd50730b4e` |
| Linux x64 | `8b6f0d66d8f4d3ea87d018579489345a936722d86b73f60614b6bccac9d53946` |

O pacote está em `dist/assisscript-3.3.0-alpha.15.vsix`. Os registros de
verificação e identidade do ZIP ficam em
[evidências](../ecossistema/evidencias/typed-input-2026-11-11/summary.json).
As evidências de hash do próprio VSIX ficam no Git ao lado do pacote de
desenvolvimento. A cópia embutida do relatório antecede a conferência do ZIP.

## Desktop

As duas janelas de 04/11 abriram. A árvore de acessibilidade da leitura expôs
documento, botão do contador, link e listas. A dos painéis expôs os dois
botões. Tab moveu o foco para «Alternar esquerdo». A tentativa de captura
retornou `FrameArrived timed out: timed out waiting on channel`, e o clique
pelo botão da árvore retornou `coordinate input geometry is unavailable`.
A troca de foco seguinte no SSC foi interrompida com `user input was detected
in this window`. O teclado da leitura não forneceu confirmação de foco.

| Aceite | Estado nesta sessão |
| --- | --- |
| Foco SSC | Botão esquerdo confirmado após Tab pela árvore |
| Cliques, Espaço/Enter, fluidez durante resize | Pendente de observação visual |
| Rajada, seleção, cópia, zoom e escala da leitura | Pendente de observação visual |
| Leitor de tela | Árvore inspecionada. Anúncios de leitor real pendentes |
| DPI e múltiplos monitores | Pendentes, inclusive transição entre escalas |
| IME | Pendente. A demo de leitura não é editável |

Para reabrir, use `Abrir-Paineis.cmd` e `Abrir-Leitura.cmd` em
`work/local-resources-20261104/build/resources-development-windows-20261104/`.
Nos painéis, use Tab/Shift+Tab, clique e Espaço/Enter, depois redimensione em
movimento. Registre ordem do foco, alternâncias por ação e travadas. Na leitura,
clique dez vezes em rajada e confira incremento de dez. Arraste para selecionar,
use Ctrl+C e cole em um editor. Teste Ctrl+`+`, Ctrl+`-` e Ctrl+`0`. Registre
atraso, cliques perdidos, texto copiado e se o zoom preserva o estado. Com leitor
de tela, informe nomes e ordem anunciados. Para escala, confira legibilidade e
alvos ao mover a janela entre monitores de DPI diferentes. Para IME, use um
arquivo editável no VS Code e observe pré-edição, confirmação e cancelamento da
composição com um método de entrada instalado.

## Continuação e publicação

A [fila integral](../ecossistema/FILA-M0-M1.md) segue vigente. A próxima unidade
é o loader físico confinado de recursos declarados, com concessão explícita,
validação do handle aberto, casos de links/reparse points, Unicode, cotas e
preservação do Frame ativo em falha. Mantêm-se os aceites desktop e demais
critérios de rede, persistência, busca, distribuição e integração.

A branch de trabalho foi autorizada para publicação. O SHA do relatório é
obtido pelo histórico. O estado remoto observado é registrado nas evidências
da unidade.

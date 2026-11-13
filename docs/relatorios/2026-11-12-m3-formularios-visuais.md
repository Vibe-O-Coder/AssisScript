# M3 — Formulários locais, inspeção visual e gates

12/11/2026, America/Fortaleza. Base pública
`b833e8182eb0c63d7e0fc58754decd5012220a5f`, branch
`work/ecosystem-2026-11-11`, cópia `work/eco-70-20261111`.
E04-03/05, E07-04 e E08-02/05 recebem evidência. O incremento de formulários
mantém a régua em **54,30%, 0/5 gates** após o [avanço M7](2026-11-12-m7-busca-local.md).
O retrato integral está em [PROGRESSO.md](../ecossistema/PROGRESSO.md).

## Implementação e teste

O [perfil de formulários](../ecossistema/PERFIL-FORMULARIOS-LOCAIS-V1.md)
ativa caixas de seleção, rótulos e validação local. Reutiliza a árvore HTDL,
FS/SSC, Reader e publicação em conjunto. A alteração da caixa é preparada
em outro Frame. O commit nativo publica geometria, raster e MSAA. Abortar ou
recusar a publicação conserva o estado. A troca de documento revoga a ação e
reinicia o valor. A ABI nova projeta papel e estado marcado no Windows.

O [exemplo 72](../../exemplos/72_local_forms_window.assis) oferece a janela
e o modo `--smoke`. A [suíte de formulários](../../tests/test-frame-forms.py)
cobre rótulo, foco, Espaço com repetição, gesto interrompido, campo requerido,
campo desabilitado, versão antiga, reflow a 200%, navegação e falha do
provider. O [oráculo COM](../../tests/catalog_frame_oracle.c) verifica
papel, estado, nome da ação, eventos, rejeição na ABI anterior e revogação
de uma projeção substituída. [Matriz, comandos e hashes](../ecossistema/evidencias/ecosystem-2026-11-12/summary.json).

A matriz final executou **155 testes no Windows x64** e **138 no Linux x64
(Ubuntu WSL2)**, com 4 e 21 casos pulados, respectivamente. A checagem passou
em **73/73 exemplos por host** e executou os dois finais do RPG. As
instalações em prefixos isolados fecharam 32 bibliotecas na seleção e
executaram o índice instalado. O Windows executou também a janela instalada,
4 testes de locks do instalador e 40 testes Node. O manifesto e a régua
passaram em `--check`.

O compilador emitiu a demo em PE Windows x64, ELF Linux x64/ARM64 e Mach-O
macOS x64/ARM64. A evidência gráfica é Windows x64 e a execução Linux x64
é headless. A verificação de integridade conferiu 57 arquivos da referência
congelada. Os 16 cenários de integração da referência seguem como not-run.

## Inspeção visual

O [oráculo nativo](../../tools/check-frame-visual.py) renderizou oito
superfícies do cliente GDI. Os rasters coincidiram byte a byte nos modos
otimizado e de referência. O contador passou de 0 a 10, com diferença restrita
ao rodapé. O zoom de leitura preservou a seleção. O painel esquerdo se moveu
quatro passos de 25 ms, com os pixels do painel direito preservados. No
formulário, a primeira inspeção mostrou um centro preenchido que podia
parecer indeterminado. A versão final usa uma marca de seleção distinta e um
contorno de foco ao redor do controle. A diferença entre desmarcado e
marcado ficou dentro do retângulo `[24,105,46,127]`. A 200% o formulário
mostrou a validação local concluída.

[Leitura e seleção](../ecossistema/evidencias/ecosystem-2026-11-12/reading-200.png) ·
[Painéis antes](../ecossistema/evidencias/ecosystem-2026-11-12/panels-initial.png) ·
[Painéis depois](../ecossistema/evidencias/ecosystem-2026-11-12/panels-moved.png) ·
[Formulário desmarcado](../ecossistema/evidencias/ecosystem-2026-11-12/forms-unchecked.png) ·
[Formulário marcado](../ecossistema/evidencias/ecosystem-2026-11-12/forms-checked.png) ·
[Formulário a 200%](../ecossistema/evidencias/ecosystem-2026-11-12/forms-200.png).

O Computer Use retornou `Computer Use app approval timed out` nas tentativas
de abrir leitura, catálogo e formulário. As listagens seguintes não
retornaram janela alvo. Houve zero capturas de desktop e zero entradas de
Computer Use. O aceite de leitor de tela real, escala do sistema, monitores,
IME e fluidez percebida permanece pendente. O zoom de 200% testado é de texto.
[Registro desktop](../ecossistema/evidencias/ecosystem-2026-11-12/desktop.json) ·
[Hashes visuais](../ecossistema/evidencias/ecosystem-2026-11-12/visual.json).

## Evidência exigida para aprovar os gates

Cada aprovação exige relatório do marco, dependências e resultados
reproduzíveis na revisão publicada exata. Vincule a matriz, hashes, versões
de SO/provider, resultados esperados e observados e limitações. Anexe a
evidência à entrada de gate em `PROGRESSO.json` e registre um retrato
integral dos 60 critérios e cinco gates. O gerador verifica a consistência
desse registro. [Plano mestre](../ecossistema/PLANO-MESTRE.md).

| Gate | Entrega pendente para aprovação | Execução e evidência |
| --- | --- | --- |
| G1 — Visualizador local | Completar o perfil M3. Campos de texto/número, seleção em edição, IME, imagens sob limites, importação HTML estática inicial e projeção assistiva. | Rodar corpus local, concessões e entradas inválidas. Demonstrar navegação por teclado/ponteiro, zoom, DPI e troca de monitor. Registrar o percurso com leitor de tela real no desktop e verificar recursos após fechar. |
| G2 — Página remota isolada | Completar M4/M6. SDK e capacidades revogáveis, sandbox por SO do perfil, broker TLS/DNS com validação de cada salto, partição de origem/perfil e ciclo de abas. | Usar servidor controlado, DNS/redirect hostis e conteúdo com tentativa real de escapar. Provar limites, cancelamento, reload, rollback, isolamento da aba vizinha e política de dados. |
| G3 — Apresentação integrada | Completar M5. HTDL, FluxStyle, layout e SSC com invalidação incremental, estados por nó, inspeção de grafo e live regions. | Executar corpus normativo e cenários integrados de leitura, contador, dois painéis, ciclos e falhas, foco, aba oculta, movimento reduzido e anúncios assistivos. Medir frame/latência no candidato. |
| G4 — Busca persistente integrada | Completar M7/M8. Segmentos maiores que RAM, recuperação/compactação e crawler com fronteira persistente, robots e limites por host. Integrar serviço e consulta voluntária pelo Browser. | Executar corpus rotulado, restart/crash/compactação, consulta durante reindexação, abuso de protocolo e bloqueio de destinos proibidos. Medir relevância, latência, throughput e privacidade dos logs. |
| G5 — Distribuição e aceite final | Completar M9 sobre os marcos anteriores. Validar pacote/SDK/editor/providers/instaladores e CI nativa nos alvos anunciados. | Usar a revisão exata em 24 h reais de carga integrada UI/worker/rede/índice com falhas e reinícios. Registrar RSS, handles, p95/p99, recuperação, hashes e aceite por terceiro. |

## Continuação

A [fila operacional](../ecossistema/FILA-M0-M1.md) conserva o SDK geral,
células por nó, inscrições, valores/strings, identidade incremental/editor,
imagens, live regions e edição. O trabalho transversal abrange RSS/disco e
perfis órfãos, macOS/ARM64, isolamento geral, broker e perfis, persistência,
busca, M4–M9, carga de 24 h, distribuição e aceites. Easy fica na última etapa.
Próxima unidade visual: edição de texto/número com buffer por nó e eventos
nativos de texto antes da integração IME. A busca pode avançar em segmentos
e recuperação sem depender da UI.

## Publicação

O destino da rodada é a [branch de trabalho](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-11).
O adendo registra a conferência do GitHub e a situação da PR.

### Adendo — revisão automática do envio

A revisão automática bloqueou a execução do push do commit
`51fbc67de98fe7e2a1cb2cbe67582683ca482b43`. Ela considerou genérica a
autorização de publicação no GitHub e exigiu consentimento explícito para os
57 arquivos desta unidade no destino público `Vibe-O-Coder/AssisScript`,
branch `work/ecosystem-2026-11-11`. A carga inclui fontes, exemplos, testes,
manifestos, workflow, relatórios e evidências de fixtures sintéticas.
O commit e a árvore `99088b8858541b32a58b22c09b7ca9d345e7c316` foram
preservados. A revisão recusou o envio antes da execução.

O resultado local é **54,30%, 0/5 gates**. A base pública confirmada
`b833e81` registra **50,40%, 0/5 gates**. A ação pendente é autorizar
explicitamente os 57 arquivos desta rodada, incluindo este registro, no
repositório e branch acima. Após a autorização, o próximo passo é repetir
o fluxo normal de envio e conferir SHA, árvore e inventário remotos.
O patch e o inventário revisáveis ficam em `build/session/delivery` na
cópia isolada. O SHA deste adendo é identificado pelo histórico Git.

### Adendo — estado do remoto verificado na continuação

`git ls-remote` confirmou `13e81a897388e694d9a02bcfb4b3984665d7c3c9`
como cabeça pública de `work/ecosystem-2026-11-11`. Essa revisão inclui
`51fbc67` e registra **54,30%, 0/5 gates**. A recusa acima pertence à
tentativa anterior. [Branch publicada](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-11).

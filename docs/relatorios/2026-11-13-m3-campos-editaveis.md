# M3 — Campos locais de texto e número

13/11/2026, America/Fortaleza. Cópia `work/eco-70-20261112`, branch
`work/ecosystem-2026-11-12`. Base pública
`48a18b7b3116940e00d008ac6b2610ba6a2dc175`. E02-04, E04-01/04/05,
E07-04 e E08-02/05 recebem evidência. **58,00% → 58,50%, 0/5 gates.**
E04-04 passa 2→3 por edição integrada, testes de grafemas e entrada
adversa, seleção e zoom de texto. Os demais níveis são preservados.

## Implementação

O perfil `(4,1,1)` inclui texto e inteiro. Cada campo possui um buffer
UTF-8 e seleção por `NodeId`. O Frame candidato copia os campos da mesma
instância e aplica o pedido ao nó em foco. A revisão e a sequência do
evento invalidam pedidos antigos. A publicação confirma valor, seleção,
geometria e MSAA na mesma transação. Reflow mantém os campos, navegação
reinicia os valores e abort preserva o quadro ativo.

Setas, Home/End, seleção por Shift e Ctrl+A operam em grafemas. Backspace
e Delete removem grafemas inteiros. Ctrl+C copia a seleção do campo.
Clique foca o campo ou o rótulo. Placeholder e valor têm pintura própria
na ordem dos nós. Na submissão, a validação percorre os controles em ordem
de árvore. Aceita int64 decimal opcionalmente negativo. O conteúdo digitado
pode ficar temporariamente inválido. A demo apresenta o resultado local.
[Perfil](../ecossistema/PERFIL-EDICAO-LOCAL-V1.md) ·
[Biblioteca](../BIBLIOTECA-pageedit.md) ·
[Exemplo](../../exemplos/74_editable_forms_window.assis).

O provider Windows adiciona um evento de texto por escalar, com instância
de documento. Um par substituto UTF-16 gera um escalar. Unidade baixa
órfã, controle e metade de par de um documento anterior são descartados.
O teste nativo confirma que o caractere de uma tecla chega antes de Tab
já enfileirado. O commit de edição valida limites, nomes e valores antes
de publicar. MSAA projeta papel, foco, nome e valor. A escrita de valor
pela interface MSAA fica fora do perfil.

## Testes e inspeção

Windows x64 e Linux x64 (Ubuntu WSL2) executaram a suíte de edição com
texto combinante, emoji, rollback, seleção, números extremos,
pressão/liberação, quota e troca de documento. A matriz registra os
testes executados, modos e hashes. As regressões de formulário, janela
e instalação também foram repetidas. [Matriz](../ecossistema/evidencias/frame-editing-2026-11-13/summary.json).

As quatro suítes focadas passaram em 32 testes Windows e 24 Linux, com
oito casos gráficos pulados no Linux. A checagem aprovou 75/75 exemplos
e ambos os finais do RPG por host. A instalação isolada fechou 36
bibliotecas e executou as demos do prefixo. Windows também executou
quatro testes de locks e 40 testes Node. Os compiladores x64 de teste
e os comandos estão no resumo.

Os dez rasters Windows coincidiram entre os modos otimizado e referência.
O formulário inicial mostra o placeholder e o número em edição. O
quadro a 200% mostra `Júlia`, `-3` e a confirmação de validação.
[Inicial](../ecossistema/evidencias/frame-editing-2026-11-13/editing-initial.png) ·
[A 200%](../ecossistema/evidencias/frame-editing-2026-11-13/editing-200.png) ·
[Hashes](../ecossistema/evidencias/frame-editing-2026-11-13/visual.json).

O Computer Use abriu a janela na segunda tentativa. Tab focou Nome e
Quantidade inteira. A árvore confirmou `j` e `-3` após as respectivas
teclas. A entrada Unicode por `type_text` ficou sem confirmação no
desktop. O provider foi validado separadamente com mensagens UTF-16
nativas e o raster mostra o resultado acentuado. As duas capturas de
desktop expiraram. [Registro](../ecossistema/evidencias/frame-editing-2026-11-13/desktop.json).

Restam composição IME, colagem, seleção por arraste nos campos, bidi,
leitor de tela real, DPI/monitores e fluidez SSC no desktop. Os perfis 1–3
permanecem disponíveis, assim como o escopo ASV2 1–2. macOS e ARM64 ficam
fora da execução nativa deste incremento. O próximo item de M3 é IME,
seguido de imagens, importação HTML e regiões de anúncio.
[Fila integral](../ecossistema/FILA-M0-M1.md).

## Publicação

O [commit de busca](https://github.com/Vibe-O-Coder/AssisScript/commit/48a18b7b3116940e00d008ac6b2610ba6a2dc175)
é a base publicada. A revisão de edição é identificada pelo histórico
da [branch](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-12).
A [atualização local do compilador e do VS Code](2026-11-13-compilador-vsix.md)
usa o candidato reconstruído da base publicada.

# viewer — apresentação HTDL local bootstrap

`import "std/viewer.assis";` depende de htdl e window. Windows x64 possui
provider de desenho; Linux/macOS compilam o fallback explícito. A lógica de
texto, geometria, foco, rolagem e interação é AssisScript, sem código de página.

## Construção e uso

```powershell
python tools/build-platform.py --output build/viewer/assis_platform_v1.dll
build/assis-viewer.exe build exemplos/44_htdl_viewer.assis --safe --debug -o build/viewer/htdl-viewer.exe
build/viewer/htdl-viewer.exe exemplos/44_artigo.htdl
```

Use um compilador reconstruído da revisão atual. O exemplo abre somente o
caminho local passado explicitamente, até 1 MiB, valida HTDL e constrói a
apresentação antes de criar a janela. Não resolve recursos, rede, estilos ou
programas. O título da janela é do shell. A concessão de caminho pertence ao
chamador confiável; não é uma política de acesso de página.

`View(document, window_instance, width, height, row_height, measure)` recebe
Document validado por htdl::load e um callback confiável
`safe fn(borrow slice<byte>):int`, que mede pixels ou retorna erro negativo.
Na janela real usa-se viewer::text_width e a altura obtida por viewer::measure("M").
`try_new` e `is_open` devem ser conferidos. Não passar uma árvore genérica
não validada. O construtor não mantém empréstimo do documento ou do callback.

A apresentação possui seus bytes e linhas, com NodeId completo. Pode sobreviver
ao fechamento do Store, mas a aplicação deve fechá-la ao descartar a página.
Reconstruir outro owner e trocá-lo somente após sucesso conserva a apresentação
anterior em falha. `restore` conserva foco por NodeId, sequência e scroll
limitado no resize, cancelando gesto de ponteiro/Espaço e preservando Enter
pressionado para impedir repetição extra. Não é mutação semântica HTDL.

## Texto e limites

Percurso iterativo na ordem do documento; head e subárvores hidden são
omitidos. Paragraph/heading/button são blocos; text é inline. Espaço ASCII
colapsa entre fragmentos; extremos são removidos. Botão sem texto usa seu
a11y-label como alternativa visual. Disabled conserva desenho e não participa
de foco/ativação. Sem árvore acessível exportada nesta unidade.

Quebra gulosa usa medidas do provider, mantém palavras que cabem e divide
palavras grandes em fronteiras de escalares UTF-8. Não promete segmentação
por grafema, bidi, shaping completo, hifenização ou quebra Unicode UAX14.
Cada chamada mede até 4096 bytes. Uma unidade escalar maior que a largura
útil faz a construção falhar. Width 96..16384, height 64..16384 e row_height
1..256; largura de texto width-72. Limites do provider continuam aplicáveis.

Há no máximo 32768 linhas, até source_size bytes de texto próprio e reserva
de `min(32768, source_size+tree.size+1)` registros Line. O corpo nativo de Line
tem 72 bytes em v1. Guarda de oito milhões de bytes acumulados limita medidas
de prefixos; o callback deve ser confiável e limitado. O teto é de workspace
local, adicional ao Store, não é quota de RSS, do processo ou da página.
Bytes, linhas, objeto e temporários do adaptador usam alocação recuperável.
O File legado do exemplo ainda usa uma alocação fatal de caminho até 32768
bytes; não se anuncia recuperação integral de OOM da aplicação.

## Interação e ciclo de vida

`dispatch(document_instance,event)` retorna Change Copy: kind 0 ignorado,
1 repintar, 2 ativação local com NodeId, 3 pedido de fechamento. Não registra
handlers ou executa código de página. O shell marca cada evento com o documento
vigente quando ele é obtido; deve preservar esse envelope se adiar a entrega.
Instância de documento/janela incorreta, sequência antiga, status inválido ou
View fechada são ignorados. Window valida também token/geração/ABI na fronteira.
Essa checagem não cancela por si só mensagens do OS que ainda não foram
obtidas antes de uma navegação; um loader com essa política continua pendente.

Tab/Shift+Tab percorrem botões habilitados. Enter ativa no primeiro down;
Espaço na liberação, sem ativação adicional por repetição. Clique exige down/up
no mesmo botão visível. Perda de foco/captura cancela gestos. Setas, PageUp/
PageDown, Home/End e roda fazem scroll limitado. Foco sequencial revela o
botão. Close/Escape encerram a apresentação; close repetido é inofensivo.

`paint` usa a mesma geometria de hit testing. Linhas parciais nas bordas são
omitidas por inteiro. O fallback é software GDI com fonte do sistema; não há
zoom, seleção, clipboard, IME, imagens, FS/SSC ou leitores de tela.
Resize menor que o mínimo conserva o snapshot anterior com clipping da
superfície nativa, sem garantir uma experiência útil nessa dimensão.

## Evidências e alcance

[Testes](../tests/test-htdl-viewer.py): textwrap Python com métricas escalares
independentes, Unicode/inline/hidden, foco, teclado/ponteiro, scroll, falha de
medição/OOM, snapshot após fechamento, exemplo real e fronteira Windows.
Geração dos cinco formatos é distinta de execução nativa. A captura Computer
Use pode falhar; um dump da superfície nativa é identificado como tal e não
como prova de leitor de tela, 200%, usabilidade ou conformidade visual completa.

[Relatório da unidade](relatorios/2026-11-01-m2-visualizador-htdl.md).
M2 e M3 são parciais; M0-EXEC, seleção/acessibilidade, catálogo completo,
recuperação de editor, mutações e todos os gates permanecem abertos.

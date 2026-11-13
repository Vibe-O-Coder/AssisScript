# Perfil HTDL de edição local

`framehost::editing_versions()` negocia `(4,1,1)`. O perfil acrescenta
`input kind=text` e `input kind=number` aos formulários locais. A ausência
de `kind` usa texto. Rótulos seguem o mesmo vínculo por ID do checkbox.
O valor inicial, o placeholder, o nome acessível e a seleção de leitura
têm funções próprias. A seleção de leitura ignora os valores editáveis.
O Form valida os controles em ordem de árvore e devolve a primeira falha.
Campos desabilitados ficam fora da validação. Campos numéricos opcionais
vazios passam. Um valor numérico preenchido exige decimal inteiro int64.

Tab foca os controles habilitados. Clique foca o campo ou o rótulo e
posiciona a seleção. Setas, Home/End e Shift operam em grafemas, Ctrl+A
seleciona o campo, Ctrl+C copia a seleção e Backspace/Delete removem
grafemas completos. O valor cabe em uma linha com recorte e ajuste
horizontal pelo cursor. A demo usa foco, placeholder e zoom de texto.

`Session.dispatch` devolve mudança 12 para uma edição. O host chama
`edit_field(projection,request,node,width,height,scroll,scale,policy,metric)`
e publica por `publish_reflow`, ou usa `commit_reflow` headless. A
revogação de projeção e a troca de documento invalidam operações antigas.
Os perfis 1–3 mantêm seus subconjuntos. O worker ASV2 continua nos perfis
1–2. [Biblioteca](../BIBLIOTECA-pageedit.md).

No Windows x64, `pagepresent::text_events` habilita a extensão de entrada
por janela. `WM_CHAR` combina UTF-16, `WM_UNICHAR` recebe um escalar, e o
evento 14 carrega escalar e instância de documento. O commit de edição
acrescenta papéis 24/25 de campo editável e um comprimento u16 seguido
do valor UTF-8 após cada nome correspondente. MSAA entrega o valor
publicado para leitura. A escrita permanece sob controle do host.

Composição IME, colagem, seleção por arraste em campos, bidi, acesso de
escrita por tecnologias assistivas e eventos autorais de página seguem
na fila. O [exemplo 74](../../exemplos/74_editable_forms_window.assis)
abre a demo Windows. `--smoke` exercita edição e submissão a 200%.

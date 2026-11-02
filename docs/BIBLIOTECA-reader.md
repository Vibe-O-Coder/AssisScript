# std/reader — leitura HTDL local, seleção e MSAA

`import "std/reader.assis";` Biblioteca opcional dependente de `viewer`.
Lógica de seleção, apresentação e semântica em AssisScript. A extensão reader 1
do provider Windows adapta GDI, clipboard e MSAA, sem executar código de página.
Outros destinos compilam fallback explícito indisponível (-3).

`create(document, window_instance, width, height, scale)` devolve um proprietário
Reader; use `try_new Reader(document,window_instance,width,height,row,metric)`
para medidas confiáveis próprias. Verifique proprietário não nulo e `is_open()`.
Escalas públicas são 1000/2000 (100/200%). A fonte 200% é criada e medida antes
da nova quebra; não é esticamento de uma imagem nem ajuste de DPI do sistema.
`snapshot()` e consultas de texto/itens exigem Reader aberto. Fatias emprestadas
não sobrevivem a substituição/drop. O objeto guarda todos os dados apresentados,
nomes e geometrias; não retém documento, Store ou callback de medida.

## Seleção e eventos

`select(anchor,caret)` aceita offsets de bytes em fronteiras de escalares UTF-8,
inclusive seleção invertida e vazia. Offset inválido retorna false e preserva
seleção. `selection_start/end`, `selected_text()` e snapshot são consultas.
Cada bloco termina em LF; quebras de linha visuais não acrescentam bytes.
Espaços já colapsados pelo viewer são preservados ao copiar entre linhas.
Seleção é de leitura: pode separar acento combinante de sua base. Não há
segmentação por grafema, edição, bidi completo, IME ou UIA TextPattern.

Arrastar em texto seleciona; botões conservam press/release do viewer.
Shift+Left/Right estende por escalar; Ctrl+A seleciona tudo, Ctrl+C solicita
cópia; Ctrl+plus/minus/0 solicita 200/100%. Outros atalhos seguem o viewer.
Perda de foco/captura cancela arrasto/modificadores. Eventos precisam ter
documento/janela/sequência atuais. Reader::dispatch devolve viewer::Change:
0 ignorado, 1 redesenhar, 2 ativar botão local, 3 fechar, 4 copiar,
5 solicitar 200%, 6 solicitar 100%. O shell consome solicitações explicitamente.

`copy(window)` copia somente após solicitação explícita do usuário. Buffer e
conversão UTF-16 são preparados antes de abrir/limpar o clipboard; LF vira CRLF.
NUL é recusado para evitar truncamento de CF_UNICODETEXT. Sem seleção é no-op.
Falha antes de EmptyClipboard preserva o anterior; falha posterior da API do OS
pode deixá-lo vazio. Não há leitura, polling ou sincronização de clipboard.
Testes de cópia usam window station e clipboard privados, sem tocar no do usuário.

`restore(previous)` de mesmo documento restaura seleção, foco, scroll e
sequência; cancela gesto/modificadores. Construa candidato à parte e substitua
somente após aberto/publicação aceita. Recusa de construção preserva o anterior.
Falha de paint é informada; a superfície não tem rollback de frame parcial.

## Projeção acessível e ownership

`item_count/item/item_name` expõem blocos semânticos visíveis. Wrapped lines do
mesmo nó formam um item. Hidden não entra; disabled entra como indisponível.
Nome de botão usa a11y-label quando presente, mesmo com texto visual diferente.
Raiz usa o title decodificado. A projeção é plana: documento → heading,
paragraph e button. Containers/fragmentos inline não têm objeto independente.
Não se anuncia árvore DOM completa, seletores/mutações ou htdl_v1.

`publish(window)` envia cópia de 8 palavras i64 por registro e nomes UTF-8.
Provider valida versão, limites/ranges/fronteiras antes de reservar o candidato.
Sucesso substitui atomicamente a projeção; falha conserva anterior e vizinhos.
Mesmo documento conserva ordem/nome/role dos child IDs; fonte nova exige
instância estritamente maior. Geometria e offscreen derivam das mesmas linhas
inteiras usadas por paint e hit test. A ponte recorta novamente à superfície
nativa real quando um snapshot anterior é maior que a janela após reflow recusado. Foco semântico é anunciado ao MSAA.

WM_GETOBJECT/IAccessible fornecem nome, role, descrição de heading, estado,
foco, localização em tela, navegação, hit testing e ação padrão. São simple
child IDs da projeção, não NodeIds ou capacidades de segurança. Ação padrão
enfileira evento 11 com documento+índice; AssisScript revalida documento,
sequência, role e disabled antes de entregar ativação ao shell. Referência COM
antiga fica desconectada em navegação/fechamento de janela; seu armazenamento
é liberado quando o último cliente a solta. Drop do Reader não fecha janela:
o host deve fechar a Window ou publicar documento novo e descartar os eventos.

Todas as chamadas ficam na thread proprietária. Oleacc faz marshaling para
clientes de outros processos; callbacks diretos em thread errada são recusados.
OleInitialize é balanceado por janela com projeção. Windows 10 1703+;
User32/GDI/Oleacc/Oleaut32/Ole32 e UUID do sistema, sem dependência redistribuída.
Imports novos só em reader: window e viewer mantêm sua negociação anterior.
DLL antiga sem os novos símbolos falha no loader; `available` não recupera isso.

## Custos, falhas e alcance

Além do workspace do View e do Store: L itens de 72 bytes, (L+1)*64 bytes de registros, S+32 bytes para nomes e (T+1)*8 bytes para avanços de texto,
com L linhas, S source_size e T texto normalizado. Provider copia até 32769
registros/1048608 bytes de nomes por publicação, conservando o anterior durante
alocação. Corpos/controladores, headers/cache/alinhamento/RSS não são quota
integral. Prepare espaço também para candidato completo no resize/zoom.
Cache de avanços tem guarda adicional de 8 milhões de bytes medidos;
ponteiro/paint não chamam o callback de medidas. Cada linha tem até 4096 bytes.

Status: 0 sucesso; -1 argumento/UTF-8/escala/range; -2 expirado/documento antigo;
-3 provider não implementado; -4 OOM/recurso; -5 thread; -6 plataforma/clipboard.
Paint retorna bool e pode falhar após modificar a superfície. API de janela e
ABI C continuam confiáveis e locais, sem validação de ponteiros arbitrários.

[Exemplo 45](../exemplos/45_htdl_reader.assis),
[testes e oráculo](../tests/test-htdl-reader.py),
[relatório](relatorios/2026-11-01-m3-leitura-acessivel.md).
Execução Windows/Linux x64 é registrada separadamente de geração de formatos.
MSAA automatizado não comprova experiência auditiva em leitor de tela.
Captura desktop, monitores/escala do OS, leitor real e IME seguem sem aceite.
Contraste/movimento têm a continuação parcial abaixo. Nenhum gate é fechado.

## Sessão, foco e atualização semântica

`try_new reader::Session(max_bytes,max_nodes,window_instance)` controla Store e
Readers ativo/candidato; consulte proprietário e `is_open()`. `prepare(instance,
source,width,height,row,metric)` valida HTDL e constrói texto, layout e nomes
acessíveis. Sucesso 0 deixa `has_pending()` sem mudar `document()`/`active_reader()`.
`prepare_patch` exige Patch aberto da instância ativa e reserva também seu buffer
no teto do Store. Uma fonte emprestada em prepare continua responsabilidade do
chamador. A reserva conservadora fica retirada do teto do documento depois do
commit, como ocorre com o parser anterior. Não é quota de RSS.

Retornos: Hxxx de sintaxe/semântica/Store; -1 sessão/edição inválida; -4
layout/medida/alocação; -7 candidato pendente. Tentativa que abriu candidato
consome a instância mesmo quando abortada: mantenha contador separado da ativa.
Falhas preservam documento, seleção, foco e Reader anterior. `abort()` cancela
o candidato. `commit()` serve integração sem provider; o host Windows usa
`publish(window)`: somente após a cópia MSAA inteira ser aceita ele faz commit
do Store e troca Reader, sem novas alocações. Publicação recusada mantém o
candidato para retry/abort e bloqueia ações até resolver a transação.

Foco é mapeado pelo atributo id único entre documentos; só botão visível e
habilitado no novo snapshot aceita a restauração. Remover/ocultar/desabilitar
o focado limpa foco, sem acionar outro botão. Scroll é limitado ao novo tamanho.
Seleção e gestos são cancelados na mudança de fonte. Todos os NodeIds e
referências MSAA anteriores são invalidados; ações MSAA carregam instância e
são recusadas se antigas. Mensagens brutas do OS ainda não obtidas antes da
transação não têm versão de documento: esse limite anterior permanece aberto.

`dispatch(document,event)` e `paint/paint_with` operam somente sobre o ativo.
`reflow(window,width,height,row,metric)` preserva a mesma instância, foco e
seleção; constrói/publica antes de trocar. Recusa conserva anterior. Uma
falha de paint pode deixar frame parcial e não desfaz commit já publicado.
As chamadas são síncronas, sem callbacks retidos ou trabalho de página.

## Preferências e relógio de apresentação

`preferences(window):Preferences` consulta contraste, animação de área cliente
e cores do Windows. Não altera preferências do usuário. Resultado tem status,
high_contrast/reduced_motion e sete cores RGBA opacas. Em falha, o host conserva
a última consulta válida; defaults usam movimento reduzido. Chamadas exigem
thread proprietária e janela viva. Linux/macOS retornam status -3.

Após consulta nativa bem-sucedida, somente essa janela recebe eventos 12
(preferências mudaram) e 13 (visível=arg0). Reconsultar em 12. Minimização e
show/hide alimentam 13; o primeiro estado visível é responsabilidade do shell.
Visibilidade aqui não detecta oclusão por outra janela ou aba de navegador.
Imports base/viewer e versão Reader 1 permanecem; o novo Reader requer a DLL
com assisp_preferences. DLL antiga sem símbolo falha no loader antes de main.

`paint_with(window,scale,p)` usa a paleta de sistema quando high_contrast está
ativo, inclusive texto de seleção/foco/disabled. Fora desse modo conserva a
paleta padrão. O provider não escolhe semântica ou estilos de produto.
Segmentos selecionados e não selecionados são desenhados uma vez cada. Não há
certificação universal de contraste nem teste de mudança real do tema do OS:
testes comparam a consulta ao OS e usam paleta controlada sem mudar o sistema.

`Motion::start(now_ms,duration_ms)` aceita relógio não negativo e duração
1..60000 ms; `sample(now,visible,editing,reduced)` retorna progresso inteiro
0..1000. Tempo reverso é ignorado. Amostras em estado oculto/edição descartam
intervalos; a primeira após retomar também descarta o intervalo de transição.
Movimento reduzido conclui imediatamente; não há fila de passos físicos a
reproduzir. O chamador deve amostrar mudanças de política/visibilidade. Isso é
relógio linear de apresentação, sem parser/equações/perfil temporal SSC, FS,
editor ou scheduler de abas. O exemplo usa apenas indicador local de alteração.

[Relatório desta unidade](relatorios/2026-11-01-m3-transacoes-preferencias.md),
[testes e oráculos](../tests/test-reader-transactions.py).

Continuação 03/11/2026: [catálogo de leitura](ecossistema/PERFIL-LEITURA-CATALOGO-V1.md) acrescenta regiões, listas/marcadores medidos e links por fragmento. `reading_profile`, `interactive`, `structural`, `marker(i)`, `marker_bounds(i)` e `fragment_scroll(document,link)` explicitam o perfil. Armazenamento passa a 44 palavras por caixa e `2*sourceBytes+2048` bytes de conteúdo. As seções abaixo preservam o contrato anterior onde não ampliado.

Continuação: `compose(document,motionpage)` compõe uma vez no candidato; Packet toma empréstimo exclusivo e sela o Frame. [Contrato agregado](BIBLIOTECA-motionpage.md). As posições finais continuam compartilhadas por desenho, hit test e acessibilidade.

# pageframe — layout e snapshot local v1

`import "std/pageframe.assis";` / `--with pageframe`. Implementação em
AssisScript, sem provider. [Perfil](ecossistema/PERFIL-FRAME-LOCAL-V1.md),
[exemplo sem janela](../exemplos/56_page_frame.assis).

`try_new Frame(document,page,frame_version,width,height,scroll_y,text_scale,
max_bytes,metric)` constrói um candidato proprietário. Verifique null,
is_open(), status() e diagnostic_node(). O anterior só deve ser substituído
após sucesso. Não conserva empréstimos do Document/Page. Texto e nomes são
cópias próprias, consultáveis depois do fechamento da fonte.

`metric(bytes,size_q,weight_q)` é função safe do host e retorna
`(height_px << 32) | width_px`, ou erro negativo. size e weight usam Q16.16.
Ela precisa medir a mesma fonte usada pelo desenho; pagepresent::measure é
a adaptação Windows. Um retorno inválido impede todo o candidato. Não se
aceita quebrar um grafema maior que a largura ou 4096 bytes.

Perfil bootstrap visual: body/container/paragraph/text/heading/button. O
catálogo estático continua separado: controles adicionais são L203, inclusive
quando o parser os aceita. text inline sem saída própria acompanha o bloco;
saída autoral nesse fragmento e paint.radius não zero são L203. Ainda não há
shaping por runs de estilos mistos, imagens ou controles de formulário.

Larguras descem do viewport/pai; altura automática sobe das linhas/filhos.
Padding faz parte da largura/altura explícita. block/column empilham filhos;
row exige largura explícita em cada filho. Gap, alinhamento transversal,
text.align e alturas explícitas são aplicados sem realimentação em FS.
Transformações de offset movem composição e descendentes, sem mudar o espaço
ocupado no fluxo. A entrada FS parent.availableWidth continua fornecida pelo
host: este módulo consome saídas confirmadas e não reavalia o grafo.

Overflow clip recorta conteúdo e descendentes; scroll também reserva sempre
12px horizontais. Há rolagem vertical do documento, com clamp e max_scroll().
Rolagem independente de contêineres internos ainda não está implementada.
Texto colapsa whitespace e prefere quebrar em espaços inteiros. Palavras que
excedem a largura quebram entre grafemas Unicode 17. O Reader recompõe o espaço
na cópia e conserva os offsets ao redimensionar. A escala 1..4 aplica-se uma
vez ao tamanho base. Hifenação e regras completas de quebra Unicode ficam fora
do perfil.
Pixels inteiros são arredondados por `(q+32768)>>16`; não é layout subpixel.

`box(i)` retorna Box com NodeId, tipo, disabled, bounds/clip, cores, opacidade,
tamanho e peso. `run(i)` / `run_text(i)` fornecem posição e bytes medidos.
`accessible_bounds(i)` é a interseção final usada também pelo hit test;
`content_clip(i)` recorta texto. `name(i)` e `title()` são cópias UTF-8.
size(), run_count(), viewport(), scroll_y(), max_scroll() consultam o snapshot.
instance(), semantic_version(), style_version() e version() identificam origem.

`current(document)` exige identidade e versão semântica exatas. `hit(document,
frame_version,x,y)` devolve somente botão elegível, no topo da composição.
Um bloco/controle disabled sobreposto impede atingir um botão atrás dele.
Frame antigo, removido ou de outra instância não autoriza interação.
`next_focus(document,previous,backward)` segue a ordem semântica e ignora
disabled/hidden; sem alvo elegível retorna NodeId vazio. `eligible(...)` pode
ser consultado pelo host. IDs e versões são locais, sem autoridade de página.

FS com erro mantém o conjunto autoral anterior nos nós sobreviventes: Frame
reaplica essas saídas à semântica atual. disabled/hidden/remoção vencem o cache;
nós novos usam padrões. Em nova instância sem saídas, style_version() é zero.
Se o próprio Frame falha, conserve o quadro anterior e bloqueie interação até
uma reconstrução coerente. A demonstração Windows implementa esse bloqueio.

Limites: 256 caixas, 32768 runs, fonte até 1MiB, viewport 1..16384, scroll e
altura automática até 16777216px, fonte final 1..256px; até oito milhões de
bytes somados nas medidas de prefixos. Workspace exige reserva conservadora
de `6000000 + 2*source_size` bytes solicitados, validada antes de alocar.
Não é quota de RSS, CPU, Document/Page, Packet ou provider. Construtores
fechados liberam recursos parciais no drop. close() libera e é idempotente.

L203 recurso fora do perfil; L204 estado/parâmetro/identidade; L303 constraint
ou grafema que não cabe; L304 métrica inválida; L401 reserva/alocação/limite.
Diagnósticos do layout identificam nó, sem inventar um span FS. Nenhum gate,
aceite de desktop/leitor real ou conformidade integral é concedido por esta API.

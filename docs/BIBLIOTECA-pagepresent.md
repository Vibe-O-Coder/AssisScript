Continuação 03/11/2026: [extensão catalog-reading 1](ecossistema/PERFIL-LEITURA-CATALOGO-V1.md) publica papéis 12..19 por símbolo próprio, mantendo Frame 1. `catalog_available()` negocia a extensão; DLL atualizada é obrigatória para as bibliotecas novas. Marcadores são comandos sem offsets de seleção; erro de limite conserva o Packet anterior.

Continuação: o construtor de Packet recebe `borrow mut frame`, sela o candidato depois de construir comandos/nomes e recusa composição tardia. Guarde em variável separada um foco lido do próprio Frame antes de passá-lo ao construtor. [Movimento agregado](BIBLIOTECA-motionpage.md).

# pagepresent — composição Windows do snapshot local v1

`import "std/pagepresent.assis";` / `--with pagepresent`. Lógica de composição,
ordem, cores/políticas, foco e projeção em AssisScript; raster/fontes/COM no
provider Windows User32/GDI existente. [Perfil/ABI](ecossistema/PERFIL-FRAME-LOCAL-V1.md),
[demonstração](../exemplos/57_page_frame_window.assis).

`available()` exige extensão frame 1. Ausência da DLL/símbolo obrigatório é
erro do loader antes de main. Linux/macOS retornam indisponível, não um passe
gráfico. Não se adiciona dependência redistribuída ou fonte de terceiros.

`measure(bytes,size_q,weight_q)` mede fonte GDI derivada de DEFAULT_GUI_FONT,
altura em pixels 1..256 e peso 100..900. As mesmas escolhas são usadas pelo
desenho. Arredondamento Q16.16 e retorno empacotado seguem pageframe. O host
confiável recebe a métrica; não se exporta geometria/relógio à página.

`try_new Packet(frame,focus,preferences,max_bytes)` copia comandos, texto e
nomes de um único Frame. Confira null/is_open(). Preferences vem de reader;
status diferente de zero impede construção. Contraste alto substitui cores
autorais; disabled e indicador de foco nativo vencem opacidade/cor do autor.
Opacidade é aplicada aos primitivos do próprio nó, sem herança genérica ou
isolamento de grupo. O foco não é concedido a um botão disabled.

Reserva conservadora mínima 10000000 bytes solicitados. Exclui Frame,
Document/Page, allocator/RSS, superfície nativa e fontes. Texto até 2097216
bytes, nomes até 1048608, 256 registros acessíveis. Os comandos têm teto de
33028 e a área total de recortes rasterizados não pode exceder 67108864 pixels.
Exceder limite, OOM ou falha GDI recusa toda a publicação.

`publish(window,frame,document)` exige snapshot atual e Packet ainda não
publicado. O provider prepara outra superfície, rasteriza tudo e prepara a
cópia acessível; só troca ambas após sucesso. Erros preservam pixels, nomes,
geometria e objeto COM anteriores. A alocação transitória da segunda superfície
entra na guarda nativa de pixels. Nenhum ponteiro do chamador é retido.

Após publish=0, adote Frame/Packet juntos e chame window.present() para pedir
apresentação física. Uma falha dessa chamada posterior não desfaz o commit
lógico. Recusa de layout/preparação deve bloquear o acerto do conteúdo e
informar diagnóstico; a janela pode continuar fechável e aceitar nova tentativa.
Não se promete preservação perfeita de pixels após resize nativo ou falha do OS.

Frame.version é também a identidade monotônica da projeção nesta janela.
Use valor estritamente crescente, sem wrap, para cada novo Frame/foco/scroll.
Não misture Reader::Session e esta API na mesma Window. A projeção é plana:
documento mais blocos paragraph/heading/button, como a ponte MSAA existente.
Cada publicação nova desconecta o objeto COM anterior.

`action(frame,document,projection,item)` valida elegibilidade, versão semântica,
identidade completa, projeção recebida e projeção ainda atual no provider.
Após outro Packet publicar ou fechar a Window, ações antigas são recusadas,
mesmo se o dono anterior continuar vivo. Use somente o Frame/Packet ativos
também para hit test. O host revalida e cancela gestos em reflow/navegação.
command_count(), paint_bounds(i), item_count(), item_box(i), item_bounds(i)
permitem inspeção confiável, sem expor autoridade de página. close é idempotente.

Build do provider: `python tools/build-platform.py --output build/assis_platform_v1.dll`.
Compile a demonstração para a mesma pasta e execute com `--once` para abrir,
publicar e fechar, ou sem argumento para teclado/ponteiro/redimensionamento.
O instalador seleciona bibliotecas e exemplos; não instala automaticamente a
DLL de desenvolvimento. SSC, seleção de leitura, IME, catálogo completo visual,
DPI/monitores/leitor real e aceites finais continuam separados.

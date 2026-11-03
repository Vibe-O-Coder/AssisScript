Continuação 03/11/2026: [perfil de leitura](ecossistema/PERFIL-LEITURA-CATALOGO-V1.md) inclui links. Change 8 é ativação de fragmento; Enter ativa no pressionamento sem repetição, Espaço ativa botão na liberação e rola no link/documento. Gestos de teclado/ponteiro não completam um ao outro. Enter segurado é conservado em reflow da mesma fonte.

# std/framereader.assis

Perfil experimental `frame-reading-local-1`, 03/11/2026. Lógica em AssisScript;
sem novo provider ou ABI. Importa pageframe e reader. Usa o índice de grafemas
Unicode 17 já versionado, sem novo algoritmo Unicode. Não oferece edição/IME.

`Reader(frame,document,windowInstance,maxBytes,metric)` recebe empréstimo mutável
do Frame, mede prefixos por grafema com a mesma função do layout e sela o quadro
em sucesso. Compor SSC deve preceder essa construção. `is_open`/`status` indicam
sucesso; 204 contexto, 304 métrica incompatível, 401 recurso/limite. O proprietário
anterior deve ser conservado até a publicação do candidato.

O texto proprietário concatena runs na ordem semântica. Quebras de layout não
inserem bytes; nós de texto distintos recebem LF entre si. Título, a11y-label e
conteúdo hidden não entram na seleção. `text_bytes`, `selected_text`,
`selection_start/end` e `run_start` usam offsets nesse texto, nunca na fonte HTDL.
`select(frame,document,anchor,caret)` recusa offsets interiores de grafema,
negativos, além do fim ou snapshot semântico antigo. Seleção invertida é válida.

`highlight(frame,runIndex)` fornece o retângulo selecionado já composto e recortado.
`Packet.highlight(frame,document,selection,preferences)` constrói comandos em ordem
estrutural: fundo selecionado, texto inteiro original e texto inteiro recortado
com a cor da seleção. Isso preserva origens de glifos e a mesma fonte; não altera
medida, fluxo, MSAA ou geometria do Frame. A indicação de foco continua por último.
Falha não modifica o Packet; somente uma aplicação é permitida antes de publicar.
O teto nativo de 33028 comandos permanece e pode recusar seleção extensa.

`dispatch(frame,document,projection,event)` valida instância da janela, geração,
requestId crescente e Frame/semântica. `accept` oferece o mesmo filtro para ações
acessíveis, que ainda precisam de `Packet.action` e da projeção publicada atual.
Change: 1 repintura/foco, 2 ativação, 3 fechar, 4 copiar, 5/6 fonte 200/100%, 7
scroll. Ctrl+A, Ctrl+C, setas/Shift, Tab/Shift+Tab, Enter/Space e gesto de ponteiro
são locais. Ativação exige press/release no mesmo controle. Overlay disabled
impede seleção/ação do texto abaixo. `scroll_target` é pedido, não mutação de layout.

`restore` conserva seleção/foco e último request somente no mesmo documento e
versão semântica, com texto byte a byte igual. Reflow cancela gestos/modificadores.
`restore_keys` permite ao host conservar somente Ctrl/Shift numa repintura de
geometria idêntica. Navegação não transfere seleção. `cancel_gesture` atende
resize/perda de captura. O host conserva o Frame durante o gesto, sem carregar
dívida temporal; eventos do OS ainda não obtidos não ganham uma data semântica
retroativa. O filtro depende do envelope atribuído pelo host confiável.

`copy(frame,document,window)` só atua por solicitação explícita do host e usa a
ponte Reader existente; não é capacidade de página. `reader::copy_text` compartilha
a implementação limitada da cópia com o Reader anterior. Windows x64 tem provider;
Linux/macOS retornam indisponível. DLL ausente continua erro de loader.

Até 32768 runs e 1 MiB de texto, com buffer reservado até 1081344 bytes; maxBytes
deve admitir 20 MB de corpos
solicitados/workspace, incluindo índices. Prefixos têm teto de 8 milhões de bytes
medidos; trabalho por ponto é linear nos runs. O teto é reserva conservadora local,
não quota de RSS ou memória agregada de abas. Fonte maior que a largura ou grafema
acima de 4096 bytes conserva a recusa do Frame. Normalização, palavras, shaping/
bidi, edição, IME, DPI do OS, leitor real e aceites integrais continuam pendentes.

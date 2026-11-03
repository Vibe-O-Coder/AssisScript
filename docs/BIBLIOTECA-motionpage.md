# motionpage — coordenação SSC da página, v1

`import "std/motionpage.assis";` depende de sanscript/flowpage. Instalação
opcional `--with motionpage`; pageframe fecha essa dependência automaticamente.
Implementação em AssisScript, sem novo provider ou mudança da gramática.
Perfil **page-motion-256-v1**, sobre **ssc-grid-42-q16-v1**. Exemplos
[58, sem janela](../exemplos/58_page_motion.assis) e
[59, dois painéis Windows](../exemplos/59_page_motion_window.assis).

`try_new Page(source,max_bytes)` compila um recurso SSC imutável. Consulte null,
is_open(), status(). `reservation(source_bytes)` exige 600000 + source_size,
até 64 KiB. Essa reserva conservadora cobre corpos solicitados de programa,
controladores, dois conjuntos de até 256 nós, índices e Style transitório.
Não mede cabeçalhos do alocador, RSS, Document, FS, Frame ou provider. O host
mantém o vínculo com o mesmo recurso FS; substituir esse recurso exige outro
coordenador. Identidades e versões locais não são capacidades da página.

`prepare(document,styles,elapsed_ms,tab_visible,focus,editing,reduced)` constrói
outro conjunto, sem alterar o ativo. Enumera também subárvores ocultas. Cada
nó aceita até dois canais; o candidato inteiro é recusado ao ultrapassar
**256 canais vinculados**, mesmo ocultos ou em repouso. Um canal transitório
de verificação pode existir antes da recusa, mas não se torna vinculável.
Conflito S301, produtor ausente S302 e limite/alocação S403 abortam o conjunto.
Novo prepare enquanto ocupado retorna S403 conservando o candidato existente.

Destinos FS e semântica são fotografados pela instância, versão semântica e
versão de estilo. `ready(document)` e `prepared(document,styles)` revalidam.
`candidate_version()`, `candidate_style()`, `candidate_channels()` e
`value(document,node,axis)` consultam somente o candidato. Eixo ausente retorna
S302; documento/nó/candidato revogado retorna S403. `fallback()` informa S401
quando um destino válido precisou de aplicação direta; prepare retorna zero
nesse caso recuperável. status() conserva o último erro de coordenação.

Nós sobreviventes da mesma identidade e perfil físico herdam posição,
velocidade, repouso, fração temporal e políticas. Retargeting conserva dinâmica;
novo nó/geração/documento inicia no destino. Proteger foco ou edição congela
também todos os ancestrais que moveriam a subárvore, zerando velocidade e
guardando destinos novos. Handles expirados de foco/edição são ignorados.
O host fornece o foco semântico vigente; aquisição/IME nativos continuam fora
desta API. Semântica atual hidden/remoção vence estilos antigos após erro FS.

O tempo herda o contrato SSC: 0..60000 ms, 1/120s, até oito passos por avanço,
sem dívida inteira; pausa de aba descarta retorno, hidden reaparece no destino,
movimento reduzido aplica destinos. O módulo não lê relógio nem expõe tempo ao
conteúdo. O host rebaseia o relógio após falha/ocultação; abort não recupera
intervalos reais que passaram enquanto o quadro foi recusado.

O host constrói outro Frame e chama `frame.compose(document,motion)` uma vez,
antes de construir Packet. A composição substitui offsets autorais por posições
SSC, propaga deltas aos descendentes e refaz clips/runs. Dimensões, ordem,
restrições e extensão de scroll não mudam. Não há retorno geométrico a FS.
Packet toma empréstimo exclusivo do Frame durante sua construção e o sela
após sucesso; composição posterior é recusada. Fontes antigas que passam
`frame.box(...).node` no mesmo argumento precisam guardar o NodeId antes.

Depois de preparar Packet, o host revalida prepared, publica pixels/MSAA e
chama `commit(document,styles)` sem despachar eventos entre essas chamadas.
Commit valida e transfere proprietários sem alocar; incrementa version().
Se qualquer preparação/publicação falhar, `abort()` libera candidato e conserva
tempo/dinâmica ativos. O host mantém o quadro válido e bloqueia interação se
ficou incoerente com semântica atual. `close()` é idempotente e libera ambos.

O exemplo 59 usa contextos `scope:node`, preferência Windows de contraste/
movimento reduzido, eventos de visibilidade, tempo monotônico, Tab/teclas/clique,
revogação de gestos por quadro e cancelamento ao fechar. Durante uma pressão de
ponteiro ele conserva o quadro e descarta o intervalo; é política do exemplo,
sem promessa de capturar gestos sobre quadros substituídos.

Limites preservados: perfil finito de 42 matrizes, catálogo visual bootstrap,
sem seleção de leitura integrada, edição/IME, shaping/bidi, DPI/monitores,
inspector/LSP SSC, loader/recursos, RSS agregado ou conformidade visual completa.
Linux/macOS não têm provider gráfico por esta mudança. Nenhum gate fechado.
Easy permanece por último.

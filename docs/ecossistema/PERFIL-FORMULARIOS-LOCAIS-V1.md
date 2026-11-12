# Perfil local de formulários com caixas de seleção

`framehost::forms_versions()` negocia `(3,1,1)` no visualizador local.
Acrescenta `form`, `label` e `input kind=checkbox` ao catálogo de leitura.
O parser 0.1 valida associação por ID, unicidade de nomes e ancestral de
`button action=submit`. Para um checkbox visível, o nome acessível vem de
`a11y-label` ou do primeiro rótulo visível correspondente. O campo recebe
H207 se ambos faltarem. Rótulos ligados a campos ocultos ou desabilitados
são inertes. As referências de rótulo têm teto de 256 bytes e compartilham
o orçamento de varredura com os fragmentos.

Tab percorre controles habilitados. Espaço alterna o checkbox na liberação.
O ponteiro exige pressão e liberação na mesma caixa ou no mesmo rótulo.
Clicar o rótulo foca o checkbox associado. A ação MSAA também solicita
alternância. O estado visual usa a mesma caixa que governa o hit test.
Controles desabilitados continuam com seu estado e não podem ser acionados.

A mudança 9 de `dispatch` contém o checkbox alvo. O host chama
`toggle_checkbox(projection,node,width,height,scroll,scale,preferences,metric)`
para preparar o quadro. `commit_reflow` e `publish_reflow` confirmam o
estado. Um erro de publicação ou `abort_reflow` preserva o estado anterior.
O estado acompanha o mesmo documento no reflow e é reinicializado do HTDL na
navegação. Revisões e NodeIds antigos não autorizam alterações.

A ativação de um botão de submissão devolve mudança 10 com o formulário
quando válido, ou mudança 11 com o primeiro checkbox obrigatório habilitado
e desmarcado. Um campo oculto conserva o valor declarado para validação.
A ação é entregue ao host local. A demo exibe o resultado da validação,
sem transporte de dados. O perfil continua recusando campos de texto/número,
imagem, live regions, scripts e handlers autorais com H203.
`frameworker` negocia os perfis 1 e 2. A versão 3 recebe H200 antes de
criar um candidato do compilador ou do worker.

## Provider Windows x64

A ABI adiciona `assisp_frame_forms_version` e `assisp_frame_forms_commit`.
Os oito inteiros de cada item preservam o layout. A função aceita os papéis
20 (rótulo), 21 (checkbox) e 22 (agrupamento), além dos papéis do catálogo
de leitura. Somente o papel 21 aceita o bit 8 de estado marcado.
MSAA expõe `ROLE_SYSTEM_CHECKBUTTON`, estado marcado e ações Check/Uncheck.
Os commits de ABI anteriores conservam a validação dos próprios papéis.
Uma compilação com a biblioteca atual requer a DLL correspondente.
O Linux permite o commit determinístico headless.

[Exemplo 72](../../exemplos/72_local_forms_window.assis) abre a janela.
`--smoke` testa foco, alternância, validação e zoom de texto a 200%.
A projeção MSAA continua plana. Campos editáveis, leitor de tela real,
DPI do sistema, IME e configurações de monitores têm aceites próprios.

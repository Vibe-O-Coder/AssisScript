# Perfil viewer-local-bootstrap-v1 — contrato de desenvolvimento

Data de congelamento deste contrato: 29/10/2026. Estado: **não implementado**.
Destino inicial: prova Windows x64; Linux/macOS continuam alvos a validar.
Nenhuma promessa de suporte nativo é ampliada por este documento.

A referência pública é o [snapshot dos rascunhos](referencias/htdl-drafts-2026-10-29/PROVENANCE.json),
em particular [HTDL 0.1](referencias/htdl-drafts-2026-10-29/docs/02-htdl-0.1.md).
Os rascunhos permanecem revisáveis. Este perfil congela uma tarefa de
implementação, não ratifica toda a linguagem nem substitui suas versões.

O primeiro parser real aceitará UTF-8 com BOM opcional, comentários, entidades
nomeadas/numéricas e atributos com aspas simples/duplas ou sem aspas conforme
a gramática 0.1. Exigirá raiz document com version="0.1" e lang não vazio,
head com um title não vazio seguido de body. O subconjunto de tipos é
document, head, title, body, container, paragraph, text, heading e button.
Aplicam-se os modelos de conteúdo e restrições desses tipos da referência.

Atributos: type; version/lang na raiz; level em heading; id, class, hidden nos
tipos de corpo; disabled/action="button" e a11y-label em button. Valores,
classes, IDs únicos, texto e Unicode seguem o rascunho. Não se aceitam atributos
desconhecidos. script/on:*, presentation, imagens, links, formulários e inputs
recebem diagnóstico de recurso fora do perfil. Não são ignorados nem executados.
Button mantém foco, teclado e estado nativos, sem manipulador de página.

Diagnósticos do perfil: H101 UTF-8/léxico; H102 sintaxe/entidade; H200 versão;
H201 type ausente; H202 atributo repetido; H203 recurso fora do perfil;
H204 estrutura; H205 ID repetido; H206 valor inválido; H401 limite.
Offsets internos em bytes; linha/coluna UTF-16 base 1 e fim exclusivo na saída.
O primeiro erro impede ativação; a página anterior permanece válida.

Limites iniciais, verificados antes de crescimento/cópia: 1 MiB de fonte,
20.000 nós, profundidade 256, 64 atributos por nó e 64 KiB por valor de atributo.
São limites de parsing. Recuperação de OOM e quotas totais continuam trabalho
de E02-03; não se anunciam por cumprir esses limites.

O visualizador abre documento local sob concessão explícita, sem rede ou
execução de fonte/binário de página. Shell e conteúdo conservam identidades
distintas. Nome/role/disabled/hidden/foco serão exportados pela ponte acessível;
texto acentuado, Tab/Enter/Espaço, scroll e escala 200% têm aceite próprio.
Uma janela desenhada sem esses itens continua prova parcial.

Aceite de parser: corpus positivo/negativo da sintaxe real, Unicode, entidades,
modelos de conteúdo e limites; comparação de árvore/diagnósticos com oráculo.
Aceite de janela: abrir, texto, redimensionar, teclado/ponteiro e fechar com
contagem de recursos. Aceite de integração: leitura longa e botão acessível,
sem estado/handle tardio após navegação. Todos estão **not-run** neste contrato.

O perfil completo document-local-0.1 e G1 continuam exigindo o catálogo completo,
recursos, controles e acessibilidade do plano. Este subconjunto não aprova G1.
FluxStyle/SSC, importação HTML e runtime de página têm contratos separados.

# Perfil viewer-local-bootstrap-v1 — contrato de desenvolvimento

Continuação Unicode em 01/11/2026: seleção, navegação por setas, hit test e
quebra agora preservam grafemas estendidos Unicode 17/UAX29 rev47. Índice e
cursor são AssisScript, com tabelas/corpus oficial versionados e licença.
Assinaturas preservadas; offsets dentro de grafema passam a ser recusados.
Grafema acima do viewport/4096 bytes recusa o candidato. Não acrescenta
normalização, palavras, shaping/bidi, edição ou IME. Contratos atuais em
[graphemes](../BIBLIOTECA-graphemes.md), [Reader](../BIBLIOTECA-reader.md) e
[relatório](../relatorios/2026-11-01-m3-unicode-m0-vm.md). Catálogo bootstrap,
ABI nativa e requisitos de aceite desktop/leitor/DPI/G1 continuam iguais.

Continuação de 01/11/2026: `reader::Session` oferece mudanças validadas da
fonte/árvore e apresentação com publicação MSAA antes de commit. Seletores
locais por tipo/classe e patches de hidden/disabled estão no
[contrato HTDL](../BIBLIOTECA-htdl.md). Foco segue id semântico somente se o
novo controle está visível/habilitado; NodeIds/referências antigos são revogados.
Preferências de contraste/animação são consultadas e o relógio local descarta
intervalos ocultos/em edição. Contrato, custos e limites em
[Reader](../BIBLIOTECA-reader.md) e no
[relatório](../relatorios/2026-11-01-m3-transacoes-preferencias.md).
Não amplia o catálogo bootstrap, não executa página nem implementa FS/SSC.
Desktop/leitor real/DPI/monitores/IME e G1 continuam pendentes. As seções abaixo
preservam o histórico e seus not-run, sem substituir a evidência desta unidade.

Data de congelamento deste contrato: 29/10/2026. Estado em 01/11/2026:
**parser e apresentação local bootstrap implementados parcialmente**.
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
sem estado/handle tardio após navegação. O parser foi executado em Windows/Linux
x64; evidência no [relatório M3](../relatorios/2026-11-01-m3-parser-htdl.md).
Janela Windows x64 e integração local foram exercitadas na unidade
[M2](../relatorios/2026-11-01-m2-visualizador-htdl.md). Seleção, IME,
acessibilidade, 200% e captura da janela real permanecem sem aceite.

Limite operacional adicional: normalização de classes tem guarda de oito
milhões de unidades de comparação/varredura, retornando H401. Não altera a
gramática. O parser representa level por um dígito 1..6; recuperação de editor,
catálogo completo e apresentação ficam fora desta entrega.

O perfil completo document-local-0.1 e G1 continuam exigindo o catálogo completo,
recursos, controles e acessibilidade do plano. Este subconjunto não aprova G1.
FluxStyle/SSC, importação HTML e runtime de página têm contratos separados.

## Continuação reader 1 — 01/11/2026

Seleção de leitura por escalares UTF-8, cópia explícita, zoom de fonte/reflow
100/200% e projeção MSAA plana documento/blocos foram implementados em
std/reader.assis. [Contrato completo](../BIBLIOTECA-reader.md),
[relatório e evidência](../relatorios/2026-11-01-m3-leitura-acessivel.md).
A ABI base 0x00010000 e extensão viewer 1 permanecem; imports novos só no Reader.
Eventos 11 carregam document_instance/child_index e são revalidados pelo host.
Ponte copia buffers, não retém ponteiros AssisScript; referências COM antigas
ficam desconectadas em navegação/close da Window. Novos imports/formatos estão
no header assis_platform_v1.h e em providers/platform/reader.inc.
A projeção usa 8 palavras i64 por registro: role,flags,x,y,width,height,
name_offset,name_length. Registro 0 é document=1; demais 6/8/9 são paragraph/
heading/button. Flags disabled=1, focused=2, offscreen=4. Até 32769 registros,
1048608 bytes de nomes; ranges/UTF-8/identidade validados antes de cópia.

Cliente MSAA externo, clipboard isolado, fontes GDI e casos adversos têm
execução Windows x64; Linux tem biblioteca/fallback, sem provider. Quatro
surfaces reais são dumps, não screenshots de desktop. Computer Use parou em
app approval timed out. Leitor real, contraste/movimento, DPI multimonitor,
grafemas/edição/IME e UIA TextPattern continuam sem aceite. A escala 200% da
fonte não é escala do OS. Nenhum gate aprovado. O not-run anterior é histórico.

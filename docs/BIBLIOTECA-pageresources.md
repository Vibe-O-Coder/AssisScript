# Recursos locais imutáveis

`import "std/pageresources.assis";` seleciona `pageresources`, dependente de
`owned`. É infraestrutura do shell confiável em AssisScript. Não é import do
SDK de página e não abre arquivos, URLs, diretórios, processos ou rede.

`Path(importer,reference)` resolve chaves lógicas relativas, com `.` e `..`,
sem permitir escape da raiz. O resultado é sensível a maiúsculas e limitado a
1024 bytes. O perfil v1 admite ASCII alfanumérico, `_`, `-`, `.`, `/`; recusa
caminhos absolutos, barras invertidas, esquemas, percent encoding, query,
fragmento, segmentos vazios, nomes reservados Windows e pontos finais.
`status()` retorna 0, -1 para chave inválida ou -4 para recusa de alocação.
`content()` empresta a chave normalizada. Isso não verifica symlinks, TOCTOU ou
permissões do disco: a chave nunca é passada a uma API de arquivos.

`Batch(instance,origin,generation,max_entries,max_bytes,deadline)` permite
1..64 entradas e 0..4 MiB de payload copiado. IDs positivos e deadline absoluto
positivo são atribuídos pelo host. IDs não são capacidades. O produtor único
passa por planejamento, selagem, conclusão e cancelamento.

`add(kind,version,importer,reference)` retorna request positivo ou erro.
Tipos: 1 HTDL (versão de perfil 1 bootstrap ou 2 leitura), 2 FS local 1,
3 SSC local 1, 4 fonte de página 1, 5 ASV2 1 e 6 dados opacos 1. Há uma raiz por
papel ativo; fonte e ASV2 são exclusivos. A mesma chave/tipo/versão deduplica
exatamente; conflitos recebem -16. Dados opacos podem ter várias chaves.
Não há descoberta transitiva de imports nem inferência de arquivos por HTDL.

`seal(now)` fixa a ordem do plano. `envelope(index)` copia
`Request(instance,origin,generation,request,kind,version)` e `path(index)`
empresta a chave, sem autoridade de I/O. `deliver(request,payload,now)` aceita
respostas fora de ordem, confere todos os campos antes de copiar e recusa
duplicatas. Até 65536 bytes por HTDL/FS/SSC/fonte, 131088 por ASV2 e 1 MiB por
dado opaco, sempre dentro do teto agregado. Payload binário pode conter NUL.
Falha de envelope, versão, quota ou alocação não ocupa o slot; permite retry.
O host mantém separadas as concessões para obter os bytes.

`poll(now)` retorna 0 pendente, 1 completo ou erro. O host deve chamá-lo mesmo
sem respostas. Deadline vencido cancela tudo; `cancel()` também revoga todos
os requests e libera os proprietários. Artefato completo não expira pelo
deadline de carga. `content(index)` só empresta bytes completos e imutáveis;
o empréstimo termina antes de cancelamento/destruição. `role(kind)` retorna
índice ou -1. `complete`, `status`, `size` e `used_bytes` dão diagnóstico local.

Erros: -1 argumento/chave; -2 contexto/replay; -3 quota; -4 OOM; -8 deadline;
-9 fechado/cancelado; -12 fase; -16 tipo/versão/conflito. Não há cache global,
persistência, concessão transferível ou log de conteúdo privado. A deduplicação
é um cache exato limitado ao próprio lote, com busca de no máximo 64 chaves.

`frameworker::Session.prepare_bundle` consome um lote completo com os quatro
papéis ativos, confere instance/origin e reserva geração crescente inclusive
em tentativa que falhe. Compila fonte sob os limites existentes ou valida
ASV2. Só transfere os recursos ao ativo após o mesmo commit/raster/MSAA do
documento/worker. Falha ou abort conserva os recursos antigos; reflow conserva
o lote e o estado do programa. Navegação legada o substitui e close o libera.
Dados opacos ficam no shell, sem virar strings, imagens ou concessões do SDK.

Os exemplos 66 e 67 carregam quatro arquivos externos passados separadamente
na linha de comando: compilador, worker, HTDL, FS, SSC, fonte de página.
Os paths de OS são concessões explícitas; não são calculados a partir de src.
O exemplo usa File legado: sua pequena cópia de path ainda tem alocação fatal;
isso não é quota recuperável de disco/RSS. Loader confinado a diretório,
symlinks/TOCTOU, Unicode em chaves, rede/origens/redirects, recursos declarados
e cache compartilhado permanecem tarefas próprias. Fonte HTDL continua sem
script no perfil visual; a apresentação 0.2 não foi inventada na gramática 0.1.

[Perfil](ecossistema/PERFIL-RECURSOS-LOCAIS-V1.md) e
[relatório](relatorios/2026-11-04-m3-recursos-responsividade.md).

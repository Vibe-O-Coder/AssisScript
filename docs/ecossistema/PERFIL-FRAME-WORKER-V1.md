# frame-worker-local-1

03/11/2026. Integração local de desenvolvimento E07-04/E07-05, sem gate aprovado.
Conserva HTDL bootstrap e reading `(2,1,1)`, FS/SSC locais 1, ASV2 e SDK
read-only-1. [API, limites e falhas](../BIBLIOTECA-frameworker.md).

O shell entrega bytes HTDL/FS/SSC e fonte/ASV2 separadamente. A página não
escolhe arquivos, URL, executável, origem, perfil, versão ou concessão. A
fonte vai ao compilador descartável ASC1/1, com limites OS e deadline; somente
ASV2 validado chega ao worker. Os providers C existentes continuam adaptando
OS/IPC/COM/raster; a coordenação e lógica de página permanecem AssisScript.
Nenhuma nova dependência redistribuída, licença, ABI C ou sintaxe foi criada.

O protocolo ASIP/1 acrescenta operação **9 LOAD_CATALOG**, resposta 137.
Tem exatamente o payload/limites e argumentos da operação 1 LOAD: comprimento
u32 da fonte, bytes HTDL e bytes ASV2, seguido dos campos já existentes para
memória/frames/fuel/calls no header. Deve ser a primeira request=1, com
identidade positiva; segunda carga é inválida. O worker aplica stage_catalog,
commita documento validado e prepara a projeção imutável do SDK. Isso não
executa script/event attributes nem abre recursos referenciados pelo HTDL.

LOAD/1 mantém parser bootstrap estrito; fontes de catálogo não são aceitas
implicitamente. Um worker antigo recusa 9 e a preparação falha, mantendo o
ativo. O supervisor exige resposta 137 com instância/origem/geração/request,
campos reservados e declaração de isolamento consistentes. Não tenta LOAD/1
após uma recusa. ABI/provider worker 1 não muda: o código AssisScript do worker
deve corresponder ao contrato e ser distribuído com o candidato.

O Frame aplica o perfil visual de 18 tipos e valida FS/SSC/links antes de
iniciar o worker. LOAD_CATALOG isoladamente oferece projeção estática do
catálogo validado, sem prometer o perfil visual, rede, execução de scripts
ou maior autoridade. O SDK é o mesmo conjunto de imports 1..8.

Ativação: compilação opcional → validação HTDL/FS/SSC/Frame/Reader/Packet →
worker restrito pronto → LOAD e concessões confirmadas → publish raster/MSAA
→ transferências sem alocação. Durante o preparo, o programa anterior pode
continuar suas fatias, mas as novas ações nativas são suspensas. Abort/falha
do candidato cancela seus recursos e conserva estado/leitura/fila ativos.
Commit revoga worker, handles, seleção e fila antigos em conjunto. A fila
ACK=1 não perde evento; o programa recebe fatias até haver espaço.

Reflow não muda a projeção semântica do SDK. A identidade visual é separada
da identidade do documento; eventos precisam das duas. O payload do botão é
seu ordinal no preorder HTDL completo, jamais a caixa visual. Links continuam
fragmentos locais do host. Snapshot e seleção não podem ser usados para
construir concessões. Morte/fuel/deadline do programa conserva o visualizador.

Aceite desta unidade: matrizes nativas Windows/Linux x64 com ambos modos de
host e worker, preorder independente, teclado/ponteiro/MSAA, navegação/abort,
reflow, OOM real, vizinho, compilação limitada, LOAD/1 estrito e entradas
hostis de LOAD/9. Geração para cinco formatos é separada da execução nativa.
Computer Use abriu a demonstração anterior, mas ambas capturas expiraram;
desktop/leitor real/DPI/monitores/IME não recebem aceite.

Strings/valores SDK gerais, células por nó, inscrições de eventos, loader de
recursos externos, controles/imagens/live regions, identidade incremental,
RSS agregado/disco/órfãos, rede/perfis, macOS/ARM, busca, M4–M9, 24h,
distribuição por terceiro e os cinco gates continuam na fila. Easy por último.

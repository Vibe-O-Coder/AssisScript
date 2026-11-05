# local-resource-batch-1

04/11/2026. M3/M5 parciais; E00-01/E03-02/E04-02/E07-05/E08-04/E08-05/E11-01.
O contrato executável está em [pageresources](../BIBLIOTECA-pageresources.md).
HTDL 0.1, perfis visuais 1/2, FS/SSC 1, ASV2, SDK read-only-1 e ASIP/1
continuam com as versões anteriores. Não existe grant de arquivos no bytecode.

Modelo de autoridade: o shell escolhe um plano finito e obtém bytes por
concessões separadas. O lote confere envelopes e copia antes de concluir;
chaves lógicas não se convertem em caminhos do OS. Não anuncia confinamento
de diretório nem usa uma normalização lexical para provar contenção física.
Fonte, código, estilos, relógios, concessões e executáveis são entradas
distintas. O consumidor de um recurso valida a sintaxe antes da ativação.
Uma resposta antiga/forjada/duplicada nunca substitui bytes já aceitos.

O lote é o artefato imutável de uma navegação; pode terminar em ordem diferente
do plano. Não ativa resultados parciais. A associação ao frameworker reserva
uma geração crescente do contexto host e publica leitura/programa/recursos
conjuntamente. Antes de commit, o ativo permanece disponível; abort fecha
candidato/compilação e conserva o anterior. Close revoga ambos. Nenhum ponteiro
cruza processos. Falhas posteriores do programa mantêm o visualizador.

Responsividade: métricas Windows curtas usam cache exato limitado a 512
entradas de 256 bytes, tamanho/peso/fontes e comprimentos conferidos. Sucessos
somente; sem handles GDI retidos. Tema/cores/configuração/DPI e fechamento da
última janela limpam o cache; falhas nativas são reexecutadas nos testes.
O cache é adaptação de métricas do OS, não cache de código nem política de
origem. Provider, cabeçalhos e executáveis precisam ser distribuídos juntos.

`assisp_frame_clock`/`pagepresent::clock_ms` oferecem milissegundos monotônicos
de QueryPerformanceCounter na thread proprietária; erro -5 thread, -6 OS.
Ponteiros não entram/saem. A época é diferente de monotonic_ms: não misturar
relógios em um deadline. Linux/macOS têm fallback monotonic_ms, sem prometer
provider gráfico. Nenhuma configuração de timer do OS é escrita. ABI base,
viewer/reader/frame/catalog existentes permanecem; o novo símbolo exige DLL
correspondente para callers que o importam.

`motionpage::Page.moving()` considera somente o banco ativo, consultando
repouso/pausa/hidden/proteção de `sanscript::Motion`. Não avança física nem
altera as 42 matrizes/120 Hz/oito passos/rounding. A demo não soma espera de
16 ms ao desenho enquanto há dinâmica; em repouso espera eventos. Foco,
gestos, reduced motion e descarte de tempo oculto permanecem obrigatórios.

Visibilidade Windows é emitida somente em transições; evita separar cada par
de resize por um evento 13 redundante. Teclas/close conservam ordem. Ctrl/Shift
do mesmo documento/janela sobrevivem a zoom/scroll reflow; perda de foco ou
captura e navegação cancelam. Não se transfere gesto de ponteiro nem ativação
para um novo snapshot. A demo mostra resultado do worker em rodapé do shell;
não é live region, mutação HTDL, input editável ou suporte de colagem.

Oráculos: pilha de segmentos independente, bytes/quotas explícitos, envelopes
corrompidos e respostas fora de ordem; fontes/executáveis reais em ambos modos,
recusa de slabs do OS, worker restrito e rollback; Win32 independente para
fontes/ordem de eventos/clock e medições comparáveis com revisão base. Testes
de geração para ARM/macOS não recebem crédito de execução. Rede, loader
físico, SDK geral, controles/imagens/live regions, RSS/disco/órfãos, todas as
plataformas/aceites e Easy por último permanecem na fila.

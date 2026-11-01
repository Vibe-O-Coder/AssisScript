# Fila operacional após as reconciliações M0

Atualização operacional: 01/11/2026. O histórico das entregas está abaixo da
tabela. M0/M1 permanecem abertos. Cada tarefa produz teste, evidência, relatório
e publicação próprios. As durações dos testes de fundação foram medidas nos
JSONs das reconciliações; elas não permitem estimar esforço de produto.
As estimativas abaixo são hipóteses em sessões de escopo, a revisar após o
primeiro spike de cada área, sem prazo de entrega global.

| Tarefa | Entrada → saída | Dependência | Aceite | Estimativa inicial / risco |
| --- | --- | --- | --- | --- |
| M0-REF | Rascunhos locais → snapshot público com hashes | Nenhuma | Integridade de arquivos e corpus; execução marcada not-run | Entregue nesta unidade; não ratifica os rascunhos |
| M0-PROFILE | HTDL 0.1 → perfil bootstrap e diagnósticos fixados | M0-REF | Contrato do subconjunto e casos positivos/negativos planejados | Contrato entregue; implementação em tarefa própria |
| M0-ABI | FFI escalar → contrato assis_platform_v1 | E01 | Interface/ownership/thread/falhas e inventário | Contrato entregue; risco de provider e texto permanece |
| M0-EXEC | ADR-0001 → dois spikes e escolha fundamentada | E01/E03 | Semântica e autoridade medidas | 2 sessões para spikes, mais decisão; sandbox separada |
| M1-ARENA | OwnedArray → handles de categoria/instância/geração | E02-01/M0-REF | Modelo independente, reciclagem, geração esgotada, drops e empréstimos | Entregue como subconjunto; arena genérica sem quota integral |
| M1-ALLOC | Runtime → reserve/alocação fallível e quotas | E01/E02 | OOM injetado preserva estado e vizinhos | Entregues try_alloc/try_new, slots/remoção, BufferPool/preparação e doctree com registro/texto cobrados; quota integral pendente |
| M1-SHIM | Contrato ABI → provider Windows mínimo | M0-ABI | Oráculo C/AssisScript, falhas e recursos contados | Prova Windows entregue; outros sistemas e integração visual pendentes |
| M2-WINDOW | Shim → janela com texto/eventos/redimensionamento | M1-SHIM | Execução nativa, loop responsivo e fechamento | Reestimar após spike; acessibilidade não implícita |
| M3-PARSER | Perfil bootstrap → parser real e árvore | M1-ARENA/M0-PROFILE | Corpus real com atributos/entidades/estrutura e diagnósticos | Reestimar após arena; microformato não serve como parser |

Atualização M1: arena entregue no commit 6208ecb; provider Windows entregue
como prova parcial com módulo window, exemplo, oráculo C, falhas e recursos
contados (relatório 2026-10-29-m1-plataforma-windows.md). Alocação de buffers recuperável entregue em M1-ALLOC (relatório
2026-10-29-m1-alocacao.md); OOM de objetos/arenas e o visualizador integrado
continuam pendentes. M2 exige ampliar teclado/ponteiro,
texto/DPI e acessibilidade, além de verificar a experiência visual.

Ordem imediata: completar o contrato de cobrança de metadados/demais recursos
por documento e preparar candidato completo; spikes do executor em paralelo
conceitual, sem depender de fechar toda a frente de memória. O parser M3 pode
usar a árvore recuperável com seus limites explícitos. Nenhuma delegação
automática é requerida. Não pontuar hipóteses ou marcar not-run como pass.

Continuação de 30/10/2026: try_new e inserções recuperáveis de OwnedArray/Arena
entregues no [relatório de slots](../relatorios/2026-10-30-m1-slots-falliveis.md).
O retorno Copy evita alocar para informar OOM; APIs antigas preservam contratos.
Próxima unidade M1-ALLOC: orçamento de memória compartilhado por documento,
reserva antecipada e criação/remoção de controladores sem caminho fatal.
M0-EXEC e a verificação visual M2 continuam na fila com contratos próprios.

Continuação de 30/10/2026: take/erase na arena e swap_remove sem reconstrução
de caminho entregues no [relatório de remoção](../relatorios/2026-10-30-m1-remocao-sem-alocacao.md).
Há liberação/transferência sem alocar resultado, inclusive sob recusa do OS.
remove antigo conserva o resultado own fatal. Quota compartilhada por documento,
reserva antecipada e construção de controladores continuam sendo o próximo
incremento M1-ALLOC. Esta entrega não encerra M1 nem aprova gates.

Continuação de 01/11/2026: pool de buffers com quota conjunta de payload,
crescimento transitório, IDs geracionais e controladores fallíveis no
[relatório de orçamento](../relatorios/2026-11-01-m1-orcamento-buffers.md).
A quota cobre somente buffers desse pool, com teto adicional de slots.
Próximo M1-ALLOC: reserva antecipada de metadados e integração do orçamento
com arena/árvore/texto por documento; contabilizar overhead/RSS exige contrato
próprio. M0-EXEC, M2 e todos os gates permanecem abertos.

Continuação de 01/11/2026: preparação antecipada de slots do BufferPool,
com resultado Copy e progresso parcial explícito, no
[relatório de metadados](../relatorios/2026-11-01-m1-reserva-metadados.md).
O estoque permite criar buffers vazios e reciclar identidades sem novas
alocações. Payload não vazio continua dependente do alocador e a quota exclui
metadados. Próximo M1-ALLOC: integração do orçamento com arena/árvore/texto
por documento, cobrança e rollback. Estado/relatórios da linhagem estão no
[índice de continuidade](ESTADO-ATUAL.md); não repetir as reconciliações M0.

Continuação de 01/11/2026: `std/doctree.assis` integra a árvore ordenada e seu
texto UTF-8 na arena de bytes do BufferPool. Registros reais de 128 bytes,
texto e crescimento transitório dividem orçamento; recusas de append/texto
preservam os nós vivos. Reparent valida ciclos antes da mudança; apagar uma
subárvore é iterativo e sem alocação. Não implementa parser/semântica HTDL e
não encerra quota integral. Consulte o [relatório de árvore e orçamento](../relatorios/2026-11-01-m1-arvore-orcamento.md).
Próximo: metadados e recursos fora do pool, candidato completo transacional,
parser M3 pelo perfil congelado; M0-EXEC/M2 continuam com aceites próprios.

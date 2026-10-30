# Fila operacional após as reconciliações M0

29/10/2026. M0 permanece aberto. Cada tarefa produz teste, evidência, relatório
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
| M1-ARENA | OwnedArray → handles de categoria/instância/geração | E02-01/M0-REF | Modelo independente, reciclagem, geração esgotada, drops e empréstimos | 1 sessão para subconjunto nativo; OOM separado |
| M1-ALLOC | Runtime → reserve/alocação fallível e quotas | E01/E02 | OOM injetado preserva estado e vizinhos | Primeira fatia entregue: try_alloc/ByteBuffer; new/arenas e quota total pendentes |
| M1-SHIM | Contrato ABI → provider Windows mínimo | M0-ABI | Oráculo C/AssisScript, falhas e recursos contados | 1 sessão de spike; licenças/versões no build |
| M2-WINDOW | Shim → janela com texto/eventos/redimensionamento | M1-SHIM | Execução nativa, loop responsivo e fechamento | Reestimar após spike; acessibilidade não implícita |
| M3-PARSER | Perfil bootstrap → parser real e árvore | M1-ARENA/M0-PROFILE | Corpus real com atributos/entidades/estrutura e diagnósticos | Reestimar após arena; microformato não serve como parser |

Atualização M1: arena entregue no commit 6208ecb; provider Windows entregue
como prova parcial com módulo window, exemplo, oráculo C, falhas e recursos
contados (relatório 2026-10-29-m1-plataforma-windows.md). Alocação de buffers recuperável entregue em M1-ALLOC (relatório
2026-10-29-m1-alocacao.md); OOM de objetos/arenas e o visualizador integrado
continuam pendentes. M2 exige ampliar teclado/ponteiro,
texto/DPI e acessibilidade, além de verificar a experiência visual.

Ordem imediata: alocação recuperável de objetos/arenas, quota compartilhada por
documento e spikes do executor. A primeira fatia try_alloc/ByteBuffer não
encerra M1-ALLOC nem exige terminar uma frente inteira. Nenhuma delegação
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

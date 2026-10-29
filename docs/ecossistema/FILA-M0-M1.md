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
| M1-ALLOC | Runtime → reserve/alocação fallível e quotas | E01/E02 | OOM injetado preserva estado e vizinhos | 1 sessão de diagnóstico, depois reestimar |
| M1-SHIM | Contrato ABI → provider Windows mínimo | M0-ABI | Oráculo C/AssisScript, falhas e recursos contados | 1 sessão de spike; licenças/versões no build |
| M2-WINDOW | Shim → janela com texto/eventos/redimensionamento | M1-SHIM | Execução nativa, loop responsivo e fechamento | Reestimar após spike; acessibilidade não implícita |
| M3-PARSER | Perfil bootstrap → parser real e árvore | M1-ARENA/M0-PROFILE | Corpus real com atributos/entidades/estrutura e diagnósticos | Reestimar após arena; microformato não serve como parser |

Atualização M1: arena entregue no commit 6208ecb; provider Windows entregue
como prova parcial com módulo window, exemplo, oráculo C, falhas e recursos
contados (relatório 2026-10-29-m1-plataforma-windows.md). OOM do runtime e
visualizador integrado continuam pendentes. M2 exige ampliar teclado/ponteiro,
texto/DPI e acessibilidade, além de verificar a experiência visual.

Ordem imediata: alocação fallível do runtime e spikes do executor são tarefas pequenas
independentes, sem exigir terminar uma frente inteira. Nenhuma delegação
automática é requerida. Não pontuar hipóteses ou marcar not-run como pass.

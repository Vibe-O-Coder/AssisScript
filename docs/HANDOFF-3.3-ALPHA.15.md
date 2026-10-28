# Continuação — 3.3.0-alpha.15

Entrega: 27/10/2026; conferência das 24 horas: 28/10/2026, contexto do usuário.
Base recebida: alpha.14 com alterações
locais anteriores preservadas. Binários alpha.14 comparáveis e patch dos arquivos
rastreados em `build/alpha14-baseline`; sem reset, commit ou push automático.

## Entrega

Expressões escalares em IR tipada com emissão nativa, alocação global por
liveness/interferência e provas de intervalos para percursos reversos e offsets.
[Contratos e análise da linguagem](BACKEND-ALPHA15.md),
[exemplo](../exemplos/32_backend_evolution.assis),
[evidência atual](VALIDACAO-ALPHA15.json).

**94% estimados (94/100 pontos)** pela mesma régua de 35 critérios.
P5-OPT avança de parcial a concluído (+1); P5-IR avança tecnicamente e mantém
crédito parcial. P4-SOAK foi concluído após a conferência dos dois relatórios
reais de 24 horas (+1,5). Não há alteração de pesos nem crédito por testes futuros.

## Limites e próxima continuação

100% permanece aberto. Faltam 6 pontos: emissão integral por IR (1),
ARM64/macOS validados (2), direitos/revisão de distribuição
(1) e aceite independente (2). [Roteiro atualizado](RESTANTE-PARA-100.md).

Os binários ativos, versão do editor, catálogo, lockfile, instaladores e pacotes
devem corresponder à mesma alpha.15. `tools/test-native.py` inclui 31 suítes;
`make test-alpha15` executa os casos novos. `--no-opt` conserva emissão AST.
Reconstruir runtimes/compiladores e conferir os hashes antes de empacotar.

Não atribuir 24 horas a ensaios curtos, CI remota a testes locais, execução macOS
a inspeção Mach-O nem aceite independente à revisão do agente. Resultados e
eventuais processos em andamento ficam na validação desta entrega.

## Validação concluída

- 31 suítes e 283 testes por sistema em Windows/Linux, com/sem otimização;
  resultados independentes para números e cobertura de ownership, closures,
  variantes, arquivos, FFI/rede/processos e backend.
- 85 testes de editor/LSP; harnesses de 130 casos Windows, 133 Linux,
  28 de módulos/instalação e 41 de PE. Há sobreposição; não somar como únicos.
- 33 exemplos no perfil padrão; RPG termina em vitória/derrota com as sementes
  documentadas. O exemplo 32 executa e imprime 18.
- Três runtimes regenerados nas reconstruções limpas. Compiladores de bytes
  idênticos aos ativos; sobre cada reconstrução rodaram as três suítes de
  backend/depuração/números. As 31 suítes completas rodaram nos binários ativos.
- Inventários por ligação real atualizados e reproduzíveis nos dois sistemas.
- Sete amostras intercaladas por carga contra a alpha.14 preservada. Laços em
  escopos distintos: 1,644x Windows/1,753x Linux; vizinhos em buffer:
  1,266x/1,199x; acumulador float: 1,395x/1,346x. Chamadas pequenas variaram
  1,001x/0,980x; não há alegação de ganho nesse caso. Gate adverso de hash passou.
- Ensaio curto de 120 segundos, 4 workers por sistema, recuperação e
  cancelamento passou; não equivale às 24 horas. O monitor agora guarda
  agregados e checkpoints, sem acumular uma lista crescente por rodada.

ZIP/VSIX e binários extraídos são conferidos por `tools/verify-release.py` nos
dois sistemas. A validação JSON fixa hashes de fontes, binários e medições.
A CI foi ajustada para preservar logs e medições correntes; não foi acionada
remotamente nesta entrega local.

## Ensaio de 24 horas concluído e aprovado

Conferidos em 28/10/2026: Windows 86400,294 segundos e 342519 rodadas;
Linux/WSL2 86400,187 segundos e 345056 rodadas. Os quatro serviços de cada
sistema encerraram normalmente e recuperaram os contadores esperados ao
reabrir. Sem falhas registradas ou crescimento dos handles/descritores.
Os relatórios integrais estão incorporados à seção `longSoak` da
[validação JSON](VALIDACAO-ALPHA15.json), com seus hashes originais.

| Medida | Windows | Linux / WSL2 |
| --- | ---: | ---: |
| Duração por relógio monotônico | 86400,294 s | 86400,187 s |
| Rodadas / downloads corretos | 342519 | 345056 |
| HTTP 404 esperado | 11048 | 11128 |
| Cancelamentos esperados | 11808 | 11896 |
| Comandos inválidos rejeitados | 20147 | 20296 |
| Memória física final por serviço | 4,87–4,88 MiB | 1,29 MiB |
| Maior pico de memória física por serviço | 5,47 MiB | 1,29 MiB |
| Handles / descritores por serviço, início e fim | 91 / 91 | 4 / 4 |
| Serviços reabertos com contador correto | 4 de 4 | 4 de 4 |

Total: **687575 rodadas**, sem falhas registradas. Falha HTTP e cancelamento
preservaram o arquivo de saída anterior. Os limites de memória e handles foram
verificados em cada rodada. As medidas de memória são dos serviços persistentes;
os clientes HTTP são processos curtos separados. A carga declarada não mede
throughput máximo, TLS público por 24 horas ou durabilidade após queda de energia.

A primeira execução de 27/10/2026 foi interrompida após o usuário relatar
saturação de CPU. O gerador sem limite de rodadas iniciava muitos clientes
nativos; a comparação com os processos parados confirmou a queda de carga de
Defender/WSL. O tempo parcial não conta para o gate. Status e medições anteriores
foram preservados em `build/soak-alpha15/interrupted-before-pacing`.

As 24 horas foram reiniciadas em `build/soak-alpha15/paced`: quatro workers por
sistema, intervalo mínimo de 1 segundo por rodada e prioridade baixa. Isso é
um ensaio de duração sob carga contínua declarada, sem alegação de throughput
máximo. Falhas HTTP, cancelamento, comandos inválidos e recuperação continuam
presentes. O Linux executa a cópia congelada no próprio disco ext4; somente
relatórios/checkpoints vão para a pasta Windows. Nenhuma configuração de
proteção do Defender foi alterada pelo agente.

Cópia Windows: `build/soak-alpha15/paced/frozen`; inventário:
`build/soak-alpha15/paced/frozen-hashes.json`. O caminho da cópia Linux está em
`linux-process.json` na mesma pasta. Checkpoints atuais: `windows.status.json`
e `linux.status.json`; relatórios finais: `windows.json`/`linux.json`.
Os checkpoints finais estão em `passed`; ambos os relatórios têm
`qualifies24Hours: true`. As fontes e os compiladores correspondem aos ativos.

As cópias integrais dos relatórios finais acompanham os pacotes na validação JSON.
SHA-256 Windows: `6a5b1bfd49566f352ca3d69fc581608f484ffcdde9dbda076eadca3cacca419a`;
Linux: `e581bd3b9b2efd12e7f99e4be81b7ac16eebb4c120c3ad1dcccf222765e98a47`.
As 98 fontes registradas coincidem entre os dois relatórios e a árvore atual.
Os 108 arquivos do inventário congelado Windows, incluindo o binário Linux,
foram reconferidos sem divergências. Checkpoints, logs e inventário ficam em `build`, fora dos
pacotes. A pasta temporária Linux já não estava disponível na conferência;
o relatório registra a verificação de integridade feita pelo harness ao término.
O inventário congelado preservado em Windows foi reconferido sem divergências.

## Pendências que exigem outra evidência

Para P6-POLICY, registrar autor/origem/permissão de cada imagem e concluir a
revisão dos termos e fontes de redistribuição. O inventário técnico não concede
esses direitos. Para P6-ACCEPT, uma pessoa distinta deve usar a distribuição
nova e o manual de instalação, compilar/testar/depurar A/B/C e registrar sistema,
hash do pacote, passos, falhas/correções e aceite identificado. Não preencher
esse aceite com a atividade do agente nem com o ensaio automático.

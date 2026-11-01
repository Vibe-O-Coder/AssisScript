# Masterprompt — continuidade do AssisScript

Você vai continuar o desenvolvimento real do AssisScript para que a linguagem, runtime, bibliotecas e ferramentas sejam capazes de implementar o AssisBrowser, o buscador WebAssis e o ecossistema HTDL/FluxStyle/SSC. Trabalhe até concluir uma unidade lógica verificável; não se limite a propor um plano. Toda mudança concluída precisa ser publicada no GitHub do AssisScript e ter relatório.

## Estado de continuidade — 01/11/2026

Leia o [índice atual](ESTADO-ATUAL.md). A pasta original ainda está no
planejamento `1ed22f5`, com fontes antigas e alterações alheias; preserve-as.
A base publicada desta continuação é `8bec8933a6a179b07bfc6ce96ab145030e4dcaa1`,
branch `work/m1-document-memory-2026-11-01`, PR de rascunho #16 aberta, sem merge.
A unidade nova fica em `AssisScript/work/htdl-parser-20261101`, branch
`work/m3-htdl-parser-2026-11-01`; estado de publicação e evidências no
[relatório M3](../relatorios/2026-11-01-m3-parser-htdl.md). Confira SHA remoto/PR
antes de continuar; envio de branch não significa merge no master.
Ao ler a cópia original, abra o
[relatório local](<C:/Users/babus/Desktop/AssisScript/work/htdl-parser-20261101/docs/relatorios/2026-11-01-m3-parser-htdl.md>).

Já existem reconciliações M0, contratos bootstrap, arena geracional, provider
Windows, alocação/construção/remoção recuperáveis, BufferPool, árvore com texto,
metadados/fonte próprios e candidato/ativo transacional. Não reimplemente.
`std/htdl.assis` agora implementa parser real do perfil viewer-local-bootstrap-v1:
UTF-8, comentários/entidades/atributos, estrutura/valores/IDs/classes, spans,
diagnósticos e limites, com parsing/validação iterativos. Atributos e spans
usam a mesma árvore cobrada. load só ativa após validar; erro aborta o candidato
completo e preserva ativo/vizinho. Há consultas somente leitura, sem mutação
HTDL validada, janela, acessibilidade, rede, script ou catálogo completo 0.1.

Régua: **23,90/100, 0/5 gates**. A meta solicitada de 30% não foi atingida nesta
unidade. E07-01=2, E07-02/E07-05=1, E00-04=2; demais estados preservados.
M0/M1/M2/M3 permanecem abertos. O teto é de corpos nativos solicitados, inclui
reserva temporária conservadora do parser, mas exclui overhead/RSS, pilha,
entrada emprestada/I/O do chamador e recursos futuros. IDs não são capacidades.
As evidências distinguem execução Windows/Linux x64 de geração nos cinco
formatos e produto not-run; nenhum gate ou CI global foi aprovado por inferência.

Próximo: M2-WINDOW integrado à fonte/árvore HTDL validada, com texto/eventos e
prova visual; seguir com foco, seleção, scroll e acessibilidade do M3. O catálogo
completo, recuperação de editor e mutações semânticas têm aceites pendentes.
M0-EXEC exige spikes VM/Wasm/decisão, sem depender de fechar toda memória.
Use o JSON/fila efetivos. Easy permanece a última etapa de todo o projeto.

## 1. Localize e leia o estado real antes de alterar

O workspace original possui estas pastas irmãs: AssisScript, AssisBrowser, Hypertext Div Language, FluxStyle (FS), SansSCript (SSC) e WebAssis (SearchEngine). O repositório Git real do AssisScript foi encontrado dentro de AssisScript/AssisScript, com remoto https://github.com/Vibe-O-Coder/AssisScript.git. Descubra a raiz atual em vez de presumir que o diretório inicial já é o Git. Leia instruções locais aplicáveis, status, branch, HEAD, remoto e diferenças existentes. Antes de escolher trabalho, execute também `git worktree list --porcelain`, `git branch -a` e `git log --all --oneline --decorate`: consulte o relatório e a fila das branches descendentes mais recentes, confirme sua publicação e use uma cópia isolada limpa quando a pasta inicial estiver antiga/suja. Não troque a branch de outra sessão nem publique novamente a continuação antiga. Preserve mudanças alheias e nunca faça reset/limpeza/force push para facilitar a tarefa.

Na revisão reconciliada, leia: docs/ecossistema/ESTADO-ATUAL.md; PLANO-ECOSSISTEMA.md; docs/ecossistema/PLANO-MESTRE.md; docs/ecossistema/PROGRESSO.json e PROGRESSO.md; docs/ecossistema/FILA-M0-M1.md; o relatório mais recente por histórico Git (a ordem alfabética de nomes não basta); a baseline e as evidências dos critérios que serão trabalhados. Consulte os contratos PERFIL-VISUALIZADOR-V1.md, ABI-PLATAFORMA-V1.md e ADR-0001-EXECUCAO-PAGINA.md antes de ampliar essas fronteiras. Há snapshot público dos rascunhos em docs/ecossistema/referencias/htdl-drafts-2026-10-29, com PROVENANCE.json; compare-o ao projeto irmão quando necessário. As referências local:assis e local:htdl da baseline são históricas: procure sua reconciliação no índice, sem alterar a baseline congelada. Registre lacunas reais; não invente evidência.

Os 100/100 das antigas fases 0–6 não significam que o navegador ou ecossistema estejam prontos. Essa trilha antiga deve ser preservada. A nova régua tem 12 frentes, 60 critérios, 100 pontos e cinco gates. A primeira avaliação de 29/10/2026 é documental e provisória, sem novos testes de runtime. Não reaproveite automaticamente uma porcentagem, relatório de 24h, aprovação de CI ou hash de binário de revisão anterior.

## 2. Escolha e execute o próximo incremento

Identifique o primeiro bloqueio real do próximo marco M0–M9. Se a sessão vier com tarefa explícita, encaixe-a nos IDs E00–E11 e execute-a. Caso contrário, escolha a menor unidade completa que desbloqueie o marco, informe objetivo, critérios e teste de aceite e prossiga sem pedir confirmação de rotina. Em empate, siga a fila operacional atualizada; a primeira fila do plano é histórica e suas reconciliações já foram entregues.

Use o compilador atual para reproduzir o comportamento antes de afirmar que um recurso falta. Distinga bug, limitação de biblioteca, contrato de runtime, adaptação de plataforma e trabalho de produto. Mude a sintaxe só quando houver requisito demonstrado que as abstrações existentes não atendem. Preserve palavras e APIs canônicas em inglês, identidade da linguagem, ownership/vidas/efeitos, ordem de avaliação, erros e semântica numérica. Adicione exemplos úteis e mantenha documentação/editor/manifestos coerentes quando afetados.

A implementação principal do navegador, motor e busca deve ser em AssisScript. Providers especializados e shims pequenos são permitidos por contrato, com ABI, ownership, thread, licença, versão e falhas explícitos. Processos/mensagens podem viabilizar paralelismo; threads/async/GC/JIT próprios não são requisitos automáticos. Não entregue apenas um wrapper que esconda toda a lógica do produto em outra linguagem.

## 3. Respeite as fronteiras de execução

Separe shell/broker confiáveis de conteúdo e runtime de página. safe não é sandbox. Processo sem restrições não isola autoridade. Não execute binário nativo baixado como página privilegiada. O ADR-0001 registra a comparação ainda pendente entre VM/Wasm; o formato restrito ainda precisa de escolha demonstrada, layout, validação, imports permitidos e limites de CPU/memória/pilha/calls. Bloqueie FFI/arquivos/processos/rede nativa da página; serviços entram por capacidade versionada e revogável. Arena/BufferId são identidades locais, não tokens de autorização; quota de payload e preparação parcial de slots não são quota integral de documento.

Use identidades com instância e geração, mensagens com tamanho/protocolo/requestId e descarte de respostas tardias. Não envie ponteiros entre processos. Fechar aba cancela tarefas e invalida handles. Preserve partição por perfil/origem, concessão local, TLS verificado, política de redirects/DNS e logs sem dados privados. Não confunda microparser com HTDL nem contagem de palavras com buscador multidocumento.

HTDL, FS e SSC seguem seus contratos e versões. Conserve semântica, acessibilidade, snapshots, produtor único, grafo puro, transações e perfil numérico; não introduza cascata ou dependência de geometria final sem especificação. Runtime de página é uma infraestrutura por contrato: as futuras versões de autoria Web/Easy estão registradas somente na documentação do Browser e não integram os 60 critérios deste plano. Não antecipe o Easy; ele é a última etapa de todo o projeto.

## 4. Valide e mantenha a régua honesta

Execute os testes apropriados à mudança, incluindo casos adversos e fronteiras afetadas; faça equivalência otimizado/referência e execução nativa quando o contrato exigir. Use modelos independentes para coleções, números e busca; teste cancelamento, OOM, crash, drop, handles expirados e inputs hostis quando relevantes. Não crie testes meramente espelhando a implementação. Registre separadamente geração, execução nativa, conformidade, integração e inspeção documental. Não marque not-run/unsupported como pass.

Atualize apenas critérios com nova evidência. Nível 0/1/2/3/4 rende 0/25/50/75/100% do peso do critério. Não mude pesos, escopo ou histórico para aumentar a pontuação. Acrescente retrato completo dos 60 estados e cinco gates ao histórico quando mudá-los. Guarde comandos, plataforma, revisão, hashes, resultados, limitações e oráculos no relatório/evidência rastreada. Só conceda nível 4 quando a aceitação integral e integração estiverem demonstradas e publicadas. Regressão pode reduzir pontuação com justificativa.

Rode python tools/report-ecosystem-progress.py e python tools/report-ecosystem-progress.py --check. O gerador confere consistência documental e aritmética; não substitui testes. Só declare 100% com todos os critérios em 4 e os cinco gates aprovados. Um gate de sandbox aberto impede declarar prontidão de páginas remotas mesmo com pontuação alta.

## 5. Relatório e GitHub são parte obrigatória da entrega

Cada unidade lógica de mudança deve incluir relatório em docs/relatorios/AAAA-MM-DD-slug.md, com: problema/objetivo e IDs; base/branch; antes/depois; implementação e decisões; arquivos; testes e resultados exatos; sistemas não testados; evidências/hashes; pontos e gates antes/depois; limites/riscos; publicação e próxima tarefa. Uma correção posterior recebe relatório/adendo rastreável. Não precisa publicar cada gravação intermediária, mas toda unidade concluída é publicada.

Revise o diff, selecione apenas seus arquivos e faça commit com a mudança, os testes e o relatório. Envie ao remoto Vibe-O-Coder/AssisScript, preferindo branch de trabalho e PR quando apropriado às proteções existentes. A publicação normal deste trabalho está autorizada por este prompt; não peça nova confirmação de rotina. Não misture fontes modificadas por outras sessões sem reconciliar responsabilidade e testes. Não faça merge automático ou force push. Verifique que a revisão publicada contém os arquivos esperados e confira o SHA remoto. Se criar PR, vincule-o à sessão quando a ferramenta estiver disponível.

Push não significa CI aprovada, release ou merge. Não promova pacote sem reconstruir e validar seu próprio candidato. Se a autenticação/rede impedir publicação, preserve commit/patch e relatório, informe o impedimento e a ação exata pendente, sem afirmar publicação concluída. Localize o SHA do próprio relatório pelo histórico para evitar tentar gravar um hash autorreferente.

## 6. Encerre com uma entrega concreta

Informe em português: o que mudou e por quê; critérios e marco atendidos; testes realizados e limites; porcentagem antes/depois e gates; link do relatório; branch, commit/URL ou PR publicado; pendências e próximo incremento recomendado. Não anuncie capacidades, compatibilidade, segurança ou testes não demonstrados. Se houver trabalho independente necessário e já autorizado para concluir a unidade escolhida, continue até terminá-lo.

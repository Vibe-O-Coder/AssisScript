# Masterprompt — continuidade do AssisScript

Você vai continuar o desenvolvimento real do AssisScript para que a linguagem, runtime, bibliotecas e ferramentas sejam capazes de implementar o AssisBrowser, o buscador WebAssis e o ecossistema HTDL/FluxStyle/SSC. Trabalhe até concluir uma unidade lógica verificável; não se limite a propor um plano. Toda mudança concluída precisa ser publicada no GitHub do AssisScript e ter relatório.

## 1. Localize e leia o estado real antes de alterar

O workspace original possui estas pastas irmãs: AssisScript, AssisBrowser, Hypertext Div Language, FluxStyle (FS), SansSCript (SSC) e WebAssis (SearchEngine). O repositório Git real do AssisScript foi encontrado dentro de AssisScript/AssisScript, com remoto https://github.com/Vibe-O-Coder/AssisScript.git. Descubra a raiz atual em vez de presumir que o diretório inicial já é o Git. Leia instruções locais aplicáveis, status, branch, HEAD, remoto e diferenças existentes. Preserve mudanças alheias e nunca faça reset/limpeza/force push para facilitar a tarefa.

Leia, nesta ordem, PLANO-ECOSSISTEMA.md; docs/ecossistema/PLANO-MESTRE.md; docs/ecossistema/PROGRESSO.json e PROGRESSO.md; o relatório mais recente em docs/relatorios; a baseline e as evidências dos critérios que serão trabalhados. Consulte rascunhos do HTDL no projeto irmão ou sua referência versionada pública quando disponíveis. Os materiais local:assis e local:htdl da baseline podem não existir no clone: nesse caso registre a lacuna, não invente evidência nem trate o material como publicado.

Os 100/100 das antigas fases 0–6 não significam que o navegador ou ecossistema estejam prontos. Essa trilha antiga deve ser preservada. A nova régua tem 12 frentes, 60 critérios, 100 pontos e cinco gates. A primeira avaliação de 29/10/2026 é documental e provisória, sem novos testes de runtime. Não reaproveite automaticamente uma porcentagem, relatório de 24h, aprovação de CI ou hash de binário de revisão anterior.

## 2. Escolha e execute o próximo incremento

Identifique o primeiro bloqueio real do próximo marco M0–M9. Se a sessão vier com tarefa explícita, encaixe-a nos IDs E00–E11 e execute-a. Caso contrário, escolha a menor unidade completa que desbloqueie o marco, informe objetivo, critérios e teste de aceite e prossiga sem pedir confirmação de rotina. Em empate, siga a primeira fila recomendada no plano.

Use o compilador atual para reproduzir o comportamento antes de afirmar que um recurso falta. Distinga bug, limitação de biblioteca, contrato de runtime, adaptação de plataforma e trabalho de produto. Mude a sintaxe só quando houver requisito demonstrado que as abstrações existentes não atendem. Preserve palavras e APIs canônicas em inglês, identidade da linguagem, ownership/vidas/efeitos, ordem de avaliação, erros e semântica numérica. Adicione exemplos úteis e mantenha documentação/editor/manifestos coerentes quando afetados.

A implementação principal do navegador, motor e busca deve ser em AssisScript. Providers especializados e shims pequenos são permitidos por contrato, com ABI, ownership, thread, licença, versão e falhas explícitos. Processos/mensagens podem viabilizar paralelismo; threads/async/GC/JIT próprios não são requisitos automáticos. Não entregue apenas um wrapper que esconda toda a lógica do produto em outra linguagem.

## 3. Respeite as fronteiras de execução

Separe shell/broker confiáveis de conteúdo e runtime de página. safe não é sandbox. Processo sem restrições não isola autoridade. Não execute binário nativo baixado como página privilegiada. O formato restrito ainda precisa de escolha, layout, validação, imports permitidos e limites de CPU/memória/pilha/calls. Bloqueie FFI/arquivos/processos/rede nativa da página; serviços entram por capacidade versionada e revogável.

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

# Plano de execução

Estado: sequência recomendada, sem prazo artificial. Este trabalho entrega o planejamento; as etapas abaixo são trabalho futuro.

**Frente atual, 27/10/2026:** continuar apenas o planejamento enquanto o AssisScript passa por seu teste de 24 horas, sem executar seu compilador, consultar seus processos ou alterar o projeto irmão. Os documentos [14](14-fundamentos-e-perfis.md) a [19](19-conformidade-e-cenarios.md) aprofundam M0. Capacidades nativas devem ser avaliadas por contratos demonstráveis, sem transportar automaticamente os bloqueios de snapshots antigos para a versão atual.

Atualização da visão: a implementação final do navegador será em AssisScript, com foco em privacidade/customização e importação de HTML para a representação HTDL. As frentes nativas, de compatibilidade e busca estão em [Visão do navegador](08-navegador-assisscript-privacidade-e-busca.md). FluxStyle (FS) foi escolhido para apresentação dinâmica por fluxo, em parceria com SSC; o [rascunho FS](09-fluxstyle-e-fluxo.md) propõe seu contrato.

## Marcos e critérios de conclusão

| Marco | Entrega verificável | Depende de | Conclusão quando |
| --- | --- | --- | --- |
| M0 — contratos | Revisão do rascunho HTDL, API hospedeira e seleção de snapshot do AssisScript para a prova | Planejamento atual | Há versões identificadas, exemplos acordados e uma lista explícita do subconjunto inicial |
| MN — capacidades nativas do AssisScript | Janela, desenho de texto, entrada/eventos e interface com serviços nativos/runtime | M0; evolução da linguagem | Um aplicativo AssisScript controla uma janela e seu ciclo de vida; pontes externas estão identificadas |
| M1 — documento | Parser HTDL, árvore com posições, registro de tipos, validação e utilitário de diagnóstico | M0 | Aceita os exemplos válidos, rejeita os inválidos e não executa nada ao analisar uma página |
| M2 — execução embutida mínima | Primeiro programa AssisScript compilado para o destino escolhido e executado em host de teste | M0; coordenação com o projeto AssisScript | Uma função retorna um inteiro, a memória é isolada, um laço infinito é interrompido e o uso nativo continua verificado |
| M3 — visualizador estático | Janela nativa em AssisScript, árvore semântica, estilos padrão, texto, layout vertical e rolagem | M1 + MN | Abre artigo local com acentos, título, parágrafos e redimensionamento sem usar HTML/CSS/JavaScript |
| M4 — fatia interativa | Botão nativo, foco/teclado, biblioteca HTDL mínima e contador na mesma instância embutida | M2 + M3 | Cliques e teclado alteram o número; retornar da entrada não encerra o runtime; fechar a página libera recursos |
| M5 — núcleo local 0.1 | Tipos restantes, campos, formulários locais, imagens, árvore acessível e ferramentas essenciais | M4 | Cumpre o conjunto da especificação 0.1, com limites e matriz de conformidade publicada |
| M6 — FluxStyle | Parser/tipos, entradas reativas, dependências e saídas; composição com um canal SSC | M3; validar controles de M5 antes de estabilizar | Atualização consistente de estado, ciclos/conflitos diagnosticados e páginas de comparação com acessibilidade |
| MS — SSC experimental | Mola amortecida, repouso, integração com geometria e redução de movimento | M3 + representação numérica adequada | Uma mudança de destino produz movimento limitado, interrompível e dispensável sem perder a ação |
| MI — importação inicial | Parser HTML e tradução direta para árvore HTDL; cobertura declarada de apresentação | M1 + M3 | Corpus de documentos estáticos preserva texto, links, semântica e origem, com tempo/memória medidos |
| M7 — navegação remota | Rede HTTPS, origens, política de recursos, isolamento de processos e distribuição de módulos | M5; evolução de M6 pode continuar | Páginas de origens distintas não compartilham estado nem recursos privados; falha de conteúdo não encerra a interface |
| M8 — navegador de uso cotidiano | Abas, histórico, permissões, cache, atualização, empacotamento e devtools completos | M7 | Instalação reproduzível, recuperação de falhas e uso continuado com aplicações demonstrativas |
| MB — busca | Cliente com vários provedores e frente independente de índice próprio | Rede e políticas; avaliação de integrações | Consulta e destinatário são explícitos; índice próprio tem corpus e avaliação de qualidade separados |

M1, M2 e MN têm frentes que podem avançar após acordar o contrato. M3 pode avançar com estilos padrão enquanto a linguagem de apresentação é explorada. A finalização da aparência não precisa bloquear a prova de execução embutida. SSC começa experimental e não é condição para ler documentos estáticos. MI não implica tradução geral de CSS/JavaScript.

M3 e M4 são **protótipos parciais**, não implementações completas do HTDL 0.1. M5 é a primeira meta de conformidade local. Suporte a HTTPS, persistência, mídia e componentes tem suas próprias versões e não fica implícito no número 0.1 da marcação.

## A primeira fatia, de ponta a ponta

Usar o [contador](../exemplos/contador/README.md) como teste de arquitetura:

1. O parser cria `document`, `head`, `body`, `main`, `heading`, `paragraph` e `button`.
2. O carregador encontra um programa e resolve as duas funções de eventos.
3. O compilador inclui a biblioteca virtual do host e exporta entrada/manipuladores.
4. O host chama a entrada, conserva a instância e apresenta zero.
5. Uma ativação por mouse, Enter ou Espaço chama `incrementar` exatamente uma vez.
6. A função usa a API do documento; o texto muda para um, depois dois.
7. O segundo botão chama `zerar`, na mesma instância.
8. Recarregar cria outra instância e volta a zero; fechar invalida os identificadores antigos.

Não introduzir binding automático, componentes, download de pacotes ou uma linguagem de estilo completa para fazer esse exemplo funcionar.

## Verificações de implementação futuras

Os grupos abaixo são critérios para quando houver implementação. Este planejamento não acrescenta uma suíte que apenas reescreve as mesmas regras em outro arquivo.

| Área | Casos que precisam produzir evidência |
| --- | --- |
| Parser | Tags aninhadas, atributos com e sem aspas, escapes, UTF-8, EOF incompleto, nomes parecidos e comentários inválidos |
| Semântica | Raiz única, `type` obrigatório, IDs únicos, conteúdo por tipo, associação de label, eventos sem programa e funções ausentes |
| Backend AssisScript | Ordem de efeitos, curto-circuito, int64, divisão limite, byte, chamadas, recursão, memória, métodos e coleções do subconjunto declarado |
| Compatibilidade nativa | Casos relevantes continuam passando nos destinos Windows/Linux após separar o frontend |
| Fronteira host | Offset/tamanho inválido, overflow, UTF-8 inválido, texto excessivo, identificador expirado e categoria de recurso incorreta |
| Eventos | Sem reentrada, entrada uma vez, ação padrão cancelável, controle desabilitado e suspensão após falha |
| Recursos | Laço infinito, estouro de pilha, limite de memória/nós/filas e trabalho excessivo em função hospedeira |
| Visual | Texto medido corretamente, corte, rolagem, escala de tela e resize; comparação de imagens com fontes fixadas |
| Entrada e acessibilidade | Tab, Shift+Tab, Enter, Espaço, IME, acentos, nome/estado em leitor de tela e foco após ocultar controle |
| Ciclo de vida | Recarregamentos repetidos não acumulam instâncias, pedidos, nós ou recursos |
| Rede futura | Separação de origens, redirects, cancelamento, cache com versão e caminhos confinados |

Usar casos compartilhados entre o verificador, o navegador e o editor. Fuzzing será especialmente útil nas entradas de parser, imagens e ABI. Medir tempo de abertura, memória por página e latência de atualização numa máquina de referência antes de definir números públicos de desempenho.

## Integração com o AssisScript em desenvolvimento

O contrato deve versionar quatro coisas separadamente: gramática HTDL, versão do compilador AssisScript, perfil de execução e versão da API hospedeira. Uma atualização do compilador não precisa alterar a marcação. Uma mudança incompatível de API precisa ser detectada pelo carregador, com mensagem útil.

No começo, fixar um artefato de compilador e seu identificador para reproduzir a prova de conceito. O desenvolvimento normal do AssisScript pode continuar. Quando o snapshot mudar, executar a matriz relevante e atualizar o SDK; não inferir compatibilidade pela versão mostrada no README.

O módulo compilado deve levar metadados de perfil, versão da API e versão do compilador, além dos imports e exports reais. Os metadados ajudam a diagnosticar compatibilidade, mas não são prova de origem confiável nem substituem a validação do módulo.

## Riscos e decisões que reduzem retrabalho

| Risco | Tratamento recomendado |
| --- | --- |
| Tratar emissão WebAssembly como simples troca do formato do executável | Separar frontend, layout de dados, runtime e emissor; provar um subconjunto pequeno primeiro |
| Expor endereços do motor ao programa | Identificadores opacos e cópias de dados com validação na fronteira |
| Desenvolver outra variante de AssisScript dentro do navegador | Compartilhar frontend e semântica; concentrar diferenças na biblioteca de ambiente e no destino |
| Escolher a sintaxe de estilo antes de conhecer o layout necessário | Estilos computados tipados e três páginas comparativas |
| Usar aparência de botão sem comportamento completo | Tipos semânticos com teclado, foco e acessibilidade no motor |
| Abrir conteúdo remoto cedo demais | Primeiro visualizador local; rede só após serviços e isolamento de processos |
| Acompanhar fonte em mudança sem build reproduzível | Snapshot explícito do SDK, sem interromper a evolução da linguagem |
| Expandir rapidamente para todas as funcionalidades de um navegador convencional | Marcos verificáveis; mídia, extensões e compatibilidade com a web fora do primeiro núcleo |

## Próxima implementação recomendada

A sequência abaixo é posterior à frente atual de documentação e à coordenação com o teste em andamento. O próximo trabalho de planejamento é fechar a alocação de largura em `row()`, o perfil numérico para documentos extensos e a geração canônica de coeficientes, conforme P01–P06 do [corpus](19-conformidade-e-cenarios.md).

Começar por M1: parser, árvore sintática, validação dos contratos e diagnóstico em português. Em seguida, iniciar a prova M2 com o mantenedor do AssisScript e o menor backend embutido possível. A semântica do FluxStyle pode amadurecer durante M3. Sua primeira prova deve ter um estado, um fluxo e um canal SSC, conforme os [exemplos em inglês](../exemplos/fluxstyle/README.md).

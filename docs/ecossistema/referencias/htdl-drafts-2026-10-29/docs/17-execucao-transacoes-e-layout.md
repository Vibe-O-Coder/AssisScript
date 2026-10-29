# Execução: tarefas, transações, layout e tempo

Estado: **protocolo proposto em 27/10/2026**. Detalha o contrato [12](12-contrato-fs-ssc-e-assisscript.md), sem implementar um runtime. As regras adicionais abaixo são recomendações revisáveis e independem de quais antigas limitações o AssisScript já tenha resolvido.

## 1. Identidades e versões

| Identidade | Significado | Quando termina |
| --- | --- | --- |
| `documentInstance` | Instância viva do documento | Fechamento ou navegação completa |
| `nodeHandle` | Token opaco, com categoria, instância e geração | Remoção do nó ou fim da instância |
| `eventHandle` | Evento entregue a um manipulador | Retorno ou falha desse manipulador |
| `semanticVersion` | Conteúdo, estados nativos e estado de aplicação aceitos | Incrementa quando há mudança observável |
| `styleVersion` | Última configuração/avaliação autoral FS confirmada | Incrementa somente em sucesso visual |
| `frameVersion` | Snapshot publicado de desenho, acerto e acessibilidade | Nova publicação coerente |

Esses campos são conceituais; não fixam o empacotamento em bits do `int` exposto ao programa. Tokens antigos nunca podem voltar a designar um nó novo. IDs textuais identificam buscas na árvore atual e não substituem geração. Uma API valida categoria e instância antes de acessar o objeto.

## 2. Uma tarefa de interação

1. Retirar da fila um evento cujo documento e alvo continuem válidos.
2. Para edição nativa, aplicar primeiro valor/checked e seus estados nativos. Preparar os eventos previstos no HTDL.
3. Chamar no máximo um manipulador por entrega. APIs mutadoras aplicam alterações aceitas em ordem; leituras posteriores na mesma tarefa enxergam essas alterações.
4. Validar a ação padrão cancelável após o manipulador. Efeitos que criam eventos os colocam na fila, sem chamar outro manipulador na mesma pilha.
5. Consolidar as mudanças, avaliar apresentação e publicar um snapshot coerente antes da próxima entrega semântica.

A implementação pode adiar desenho físico para o próximo quadro, mas a próxima tarefa precisa ver a versão lógica já consolidada. Para o primeiro runtime, não coalescer tarefas distintas; pode-se consolidar múltiplas gravações dentro da mesma tarefa. Uma gravação de estado de `false` para `true` e de volta a `false` dentro do mesmo manipulador não inicia duas animações.

`input` e `change` são entregas distintas, na ordem definida no HTDL. A alteração nativa do checkbox já existe quando `input` é chamado. Não há microtasks, promises, timers autorais ou registro dinâmico de listeners no contrato inicial; não são proibidos ao AssisScript geral, apenas não fazem parte desta API.

Se um manipulador falha, conservar suas mutações já aceitas, cancelar a ação padrão daquela ativação, invalidar o evento e suspender a instância. Uma função mutadora que retorna erro não aplica parcialmente aquela operação. Suspender o script não desfaz o documento.

## 3. Estado: ausência, padrão e valor

O registro de estado tem três informações distintas: contrato tipado, presença e valor. `state("expanded", false, scope: node)` registra um padrão; não grava uma entrada de aplicação como efeito de avaliação.

- Leitura FS de chave ausente usa o padrão do esquema.
- Leitura inteira legada `htdl_estado_int` de chave ausente continua retornando zero, conforme API v1 proposta.
- Para interoperar sem ambiguidade, o aplicativo inicializa explicitamente chaves cujo padrão FS não corresponda a zero, ou uma futura API oferece presença/leitura tipada. Não fingir que a API antiga já retorna o padrão FS.
- Gravar zero estabelece presença. Não existe `unset` na API inicial.
- `bool` recebe a normalização inteira já proposta: zero é falso; outros valores são verdadeiros. Defaults incompatíveis continuam `F306`.
- Estado por nó é armazenado de forma esparsa por handle e chave. Remover o nó apaga seus valores; ocultá-lo não.

As APIs de estado por nó são as recomendadas no documento 12. O exemplo de [painéis independentes](../exemplos/paineis/README.md) usa apenas padrão falso, eliminando a divergência entre ausência e zero nesse caso.

## 4. Coerência quando FS falha

**Refinamento necessário de C10:** manter a apresentação anterior significa manter as **últimas saídas autorais válidas**, e não congelar uma árvore antiga enquanto a aplicação já a alterou. Há duas transações distintas: semântica e apresentação autoral.

Em uma falha FS:

1. Não publicar nenhuma saída nova do candidato que falhou, em nenhum nó.
2. Conservar, nos nós sobreviventes, as saídas do último conjunto válido. Nunca transferir saídas por ID textual para outra geração.
3. Aplicar essas saídas à árvore semântica atual; recalcular texto/layout quando conteúdo mudou. Nós novos sem saídas válidas usam padrões. Nós removidos deixam imediatamente desenho, acerto, acessibilidade e canais.
4. Respeitar `hidden`, `disabled`, foco e valores atuais, mesmo que o estado de aplicação que causou o erro continue presente.
5. Publicar geometria e acessibilidade dessa combinação como um snapshot novo, registrando `semanticVersion` atual e `styleVersion` anterior no inspetor.

Assim, um botão desabilitado não continua clicável porque uma cor falhou. Um contador atualizado não fica preso ao texto antigo. A atomicidade diz respeito às saídas autorais da avaliação, não a rollback do programa. Corrigir a entrada que causou o erro agenda outra avaliação.

Uma mudança de classe que torne os bindings conflitantes pode continuar na árvore semântica; a última configuração de produtores permanece congelada nos nós sobreviventes até uma ligação válida. Remoções e mudanças de elegibilidade semântica sempre vencem esse cache. Regras que exigem nós novos aguardam a próxima ligação válida.

Se o próprio layout/compositor não consegue construir uma geometria válida, não publicar parcialmente. Manter o último quadro, bloquear o acerto da área de conteúdo que ficou incoerente e apresentar diagnóstico na interface do navegador. Isso é uma falha do motor/limite de recursos, distinta de um erro de expressão FS; não prometer recuperação visual perfeita de qualquer falha de alocação.

## 5. Largura disponível sem realimentação

`parent.availableWidth` significa **limite horizontal de conteúdo oferecido ao filho pelo contêiner**, antes de decidir a largura do próprio filho. Não significa largura final do pai medida depois do layout dos filhos.

A proposta inicial usa caixas cujo `width`/`height` explícitos incluem padding, sem borda autoral. O conteúdo disponível é `max(0px, larguraDaCaixa - 2 * padding)`. `body` recebe a largura do viewport em pixels lógicos. Restrição descendente definida permite:

1. Avaliar entradas independentes de geometria e obter o layout do pai.
2. Resolver sua largura externa a partir de uma largura explícita ou da restrição recebida.
3. Oferecer sua largura de conteúdo aos filhos de `block()` e `column()`.
4. Avaliar os fluxos desses filhos; calcular alturas após medir texto e descendentes.

Um filho pode escolher `min(available, 640px)` sem modificar o limite que leu. Um pai não pode calcular sua própria largura a partir da largura final desse filho no mesmo passe. Altura automática é medida de baixo para cima; não alimenta uma entrada FS de largura de volta.

No primeiro perfil, `parent.availableWidth` é suportada apenas em filhos de `block()`/`column()` cujo limite horizontal tenha sido resolvido. Em filhos de `row()`, a disponibilidade por filho exige política de alocação ainda não especificada: usar essa entrada recebe `F303`. Um `row()` pode existir com larguras explícitas; não declarar toda a referência FS implementada enquanto faltar sua política completa.

Não há laço “recalcular até estabilizar”. O motor monta uma ordem descendente de restrições e ascendente de medições e rejeita contextos que exigiriam dependência circular. Se uma futura versão oferecer layout intrínseco mais amplo, deverá definir algoritmo, limites e diagnóstico próprios.

Para impedir que a presença de barra vertical alterne uma consulta de largura entre quadros, a proposta inicial reserva a faixa de rolagem vertical de um contêiner `scroll`, mesmo quando seu conteúdo cabe. Overlays de interface podem ser desenhados nessa faixa. Esse custo espacial é explícito e deve ser avaliado em protótipo.

`hidden` não remove inscrições, esquema de estado nem reserva de canais. Os fluxos continuam sujeitos a checagem e avaliação; o motor pode calcular restrições virtuais descendentes sem medir texto ou publicar caixas da subárvore oculta. Erros nessa subárvore não são ignorados. Isso evita que mostrar um nó altere inesperadamente o conjunto de produtores ou a quota reservada.

## 6. Texto, padrões e preferências

O motor escolhe o estilo de autor ou padrão, aplica escala de texto uma vez sobre o tamanho base e só então mede. Reaplicar uma transação não multiplica o tamanho já escalado. Quebra de linhas, fallback de fonte e IME pertencem à camada de texto, não à aritmética FS.

Nenhum nó altera a ordem semântica por `target.offsetY`, cor ou opacidade. Texto inline segue a regra de tipo definida em [fundamentos](14-fundamentos-e-perfis.md). Nome acessível e contraste precisam ser verificados em cenários reais; existência de uma árvore acessível não prova conformidade completa com WCAG.

## 7. SSC, foco e visibilidade

| Situação | Regra proposta |
| --- | --- |
| Primeira publicação de um canal | Posição = destino; velocidade = zero; sem animação de entrada |
| Novo destino em canal ativo | Conservar offset e velocidade, integrar no próximo tick |
| Foco/edição no nó ou descendente | Congelar o offset atual do nó e de ancestrais animados, zerar velocidade, guardar novo destino |
| Saída de foco | Retomar do offset congelado rumo ao último destino |
| `hidden` na subárvore | Remover composição e pausar canais; ao reaparecer, começar no destino sem animação |
| Aba em segundo plano | Parar agendamento físico e descartar atraso; ao retornar, aplicar o destino e reiniciar base temporal |
| Movimento reduzido | Aplicar destino direto; sem passos |
| Remoção do binding SSC | Aplicar diretamente o destino FS, ou padrão se não houver destino |
| Nó removido | Invalidar canal, fila de foco e handles; nunca reutilizar estado físico por ID |

Prioridade: remoção/ocultação, movimento reduzido/retorno de aba, proteção de foco, integração normal. Aplicar um destino direto na volta de aba não dispara eventos de conclusão. A restauração do foco pode afetar a primeira geometria apresentada; validar com teclado e IME antes de congelar a regra.

O scheduler mantém resto de tempo e descarta passos que excedam o teto sem acumulá-los para depois, conforme a correção N12. Um passo de 1/120 s define tempo simulado; não promete latência de parede. Todos os canais de um tick leem os destinos do mesmo snapshot de apresentação.

Para canais ativos, a publicação geométrica usa posição integrada ou congelada. Sem SSC usa o destino direto. Um erro numérico desativa somente o canal problemático com diagnóstico e fallback representável; o erro de avaliação FS anterior continua tendo escopo de página. Se uma quota de canais impede ativar um conjunto candidato, rejeitar esse conjunto em vez de escolher vencedores por ordem de arquivo.

## 8. Entrada e geometria compartilhada

Desenho, hit testing e limites acessíveis são produzidos da mesma `frameVersion`. Uma ativação por ponteiro referencia o snapshot usado para o acerto e a geração do alvo; antes de entregar o evento, validar que o nó permanece vivo e elegível. Uma falha de geração descarta a ativação, nunca a redireciona a outro nó.

A ordem de Tab segue a árvore semântica. Quando um controle focado é removido, ocultado ou desabilitado, escolher o próximo controle elegível na ordem do documento; na ausência dele, focar o documento. Os eventos resultantes entram na fila, sem reentrada.

O snapshot geométrico é autoridade do motor, não uma API autoral. O inspetor confiável pode mostrá-lo; uma página não recebe coordenadas, contadores físicos ou tempos finos por esse mecanismo.

## 9. Limites do protocolo

Um loop de eventos ordenado é uma escolha deste projeto. O [modelo de event loops do HTML](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) é uma referência de separação entre tarefas, execução e renderização, não uma obrigação de reproduzir toda a plataforma web. Este contrato não herda promises ou APIs JavaScript.

O isolamento e os orçamentos ainda precisam de implementação. A ordem de foco deve ser avaliada contra o critério [WCAG 2.2: Focus Order](https://www.w3.org/TR/WCAG22/#focus-order); manter a ordem estrutural é uma parte da solução, não uma certificação de acessibilidade.

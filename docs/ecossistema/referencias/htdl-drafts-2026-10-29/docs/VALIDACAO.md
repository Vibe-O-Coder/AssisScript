# Validação do planejamento

Registro iniciado em 24/10/2026, ampliado em 27/10/2026. A entrega é documental, com exemplos de contratos futuros. As execuções do AssisScript descritas nas seções de 24–25/10 são históricas; não foram repetidas durante o teste de 24 horas informado pelo autor.

## Verificações realizadas

| Verificação | Resultado | Limite da evidência |
| --- | --- | --- |
| Identificação inicial do compilador | `version` e `doctor`: AssisScript 3.1.0, Windows x64, destinos Windows/Linux | Estado observado no começo da inspeção |
| Identificação durante a checagem dos exemplos | `version`: AssisScript 3.2.0, Windows x64 | O projeto irmão foi atualizado em paralelo pelo seu próprio desenvolvimento |
| `check` de `exemplos/contador/app.assis` com assinaturas temporárias da biblioteca proposta | Saída `{"ok":true}`, status 0 | Sintaxe e tipos; funções hospedeiras substitutas não implementam comportamento |
| `check` do exemplo existente `AssisScript/exemplos/01_ola.assis` | Saída `{"ok":true}`, status 0 | Verificação pontual do binário; não é execução da suíte de regressão nativa |
| Links locais e cercas de código Markdown | Revisão A/N: 17 documentos e destinos conferidos pelo verificador auxiliar; contagem da revisão anterior preservada apenas como histórico | Existência dos destinos e integridade estrutural da documentação |
| Exemplos `.htdl` | Artigo e contador 0.1 preservados; novo cartão 0.2 com recursos locais existentes; boa formação auxiliar conferida | Ainda não existe um verificador HTDL de conformidade |

Para conferir o contador foi criada uma pasta temporária, passada por `-I`, contendo somente quatro assinaturas com corpos substitutos: `htdl_no_por_id`, `htdl_no_texto_int`, `htdl_estado_int` e `htdl_estado_int_definir`. A pasta foi removida depois da verificação. O fonte do exemplo e o projeto AssisScript não foram alterados por essa checagem.

A conferência auxiliar de estrutura usou um leitor XML com o prefixo `on` declarado somente em uma cópia em memória, além das conferências de elementos, IDs e referências. Isso verifica a boa formação dos exemplos escritos com aspas, mas não define HTDL como XML, não verifica todos os modelos de conteúdo e não testa a sintaxe HTDL sem aspas. As regras propostas também foram revisadas manualmente.

## Identificação dos arquivos na checagem do compilador

Como o projeto irmão está em desenvolvimento simultâneo, estes hashes SHA-256 identificam os arquivos lidos no momento daquela checagem, sem prometer que permanecerão iguais.

| Arquivo relativo à raiz AssisScript | SHA-256 |
| --- | --- |
| `bin/assis.exe` | `12135DF1EDC7FB731F1B021DB3C5421067C5538CA4CA7E752F2BB646BE12AF57` |
| `src/assisc.c` | `E4F3F6F9D59D79E7AB7799ADC67D0478309050BC5E5877CD982C0854C61D82A8` |
| `src/ownership.h` | `610799EE67EB0FDD189EE2FB54D2795B480D4E854A7C4B898465D7119989F8C4` |

## Ainda não validado

Não há execução do contador em um navegador, renderização, entrega real de eventos, backend WebAssembly do AssisScript ou implementação das funções `htdl_*`. Também não foram executados testes completos de AssisScript, de acessibilidade ou de isolamento.

Esses resultados pertencem aos marcos de implementação do [plano](05-plano-de-execucao.md). O planejamento não afirma que uma API passa a existir porque o exemplo teve suas assinaturas verificadas.

## Revisão da visão do produto e exploração de SSC

O planejamento foi atualizado para o navegador implementado em AssisScript, foco em privacidade/customização e importação de HTML para HTDL. Foram acrescentadas propostas de relações, materiais, cenários e SSC. São propostas de linguagem, sem compilador ou verificador próprios.

Uma demonstração independente de mola amortecida foi preparada para a conversa. Sua escrita JavaScript foi conferida e seus controles foram inspecionados em uma prévia local. Ela ilustra destino, movimento e repouso com opção de movimento reduzido; não executa SSC, HTDL ou AssisScript. Essa escrita de apoio não faz parte da implementação proposta para o navegador.

Uma verificação adicional do código da demonstração, com ambiente de eventos controlado, confirmou movimento, ultrapassagem amortecida e repouso em 63 frames simulados a 60 Hz. Conferiu também que a atualização do estado lembrado não interrompe a mola e que movimento reduzido aplica o mesmo destino sem agendar frames. Foram usados os tamanhos de referência 320, 736 e 1.024 px nesse ambiente controlado; isso não equivale a uma inspeção visual de navegador em todas essas larguras.

## FluxStyle e exemplos em inglês

O nome FluxStyle (FS), a direção dinâmica por fluxo e a parceria com SSC foram registrados como decisões do autor. Grafo reativo, produtor único, sintaxe de setas e protocolo de destinos são propostas deste planejamento, ainda sem implementação.

Os arquivos `exemplos/fluxstyle/card.fxs` e `card.sscr` correspondem textualmente aos trechos principais do rascunho FS, desconsiderando o comentário inicial dos arquivos. Código, identificadores e comentários foram escritos em inglês. Os identificadores portugueses dos estudos de código anteriores em SSC também foram substituídos por equivalentes em inglês.

Não foi alegada compilação FS ou SSC: ainda não existem seus compiladores neste projeto. Foram conferidos links, cercas Markdown, correspondência dos exemplos e estrutura auxiliar dos documentos HTDL. As verificações anteriores de AssisScript não foram repetidas, pois seu código de exemplo não mudou.

## Revisão de 25/10/2026: extensões, [A] e [N]

O [parecer](13-revisao-extensoes-abertos-e-propostas.md) responde 14 grupos de questões abertas e avalia 21 grupos de propostas novas dos documentos 10–12. `.fxs` preferida e `.flux` válida são decisões do autor; `.sscr` é a recomendação técnica aplicada aos exemplos, sem atribuir sua ratificação ao grupo.

Foram renomeados os exemplos para `card.fxs` e `card.sscr`, mantendo o aviso de que não há compilador dessas linguagens. Um exemplo completo usa a proposta HTDL 0.2; a 0.1 permanece sem o novo elemento de apresentação.

| Prova desta revisão | Resultado efetivo |
| --- | --- |
| Auditoria Python | 42 pares amostrados; repouso do cartão nos passos 41/51; erro máximo de aproximadamente 0,0213 px contra a solução contínua nos primeiros 3 s do degrau de 8 px |
| Contraexemplo à tolerância de coeficientes | ±1 ULP nos coeficientes produziu até 17,90625 px de desvio em 0,5 Hz, ζ=0,1 e degrau de −4096 px; garantia universal rejeitada |
| Arredondamento e overflow | Empates distintos de conversão/produto explicitados; overflow de produto rejeitado na referência |
| Scheduler de referência | 112 passos descartados após frame de 1 s não reaparecem nos frames seguintes |
| Kernel nativo AssisScript | Compilador 3.3.0-alpha.6; `check` e execução com/sem otimização aprovados, saída `SSC numerical kernel: 41` |
| Programa do cartão | `check` aprovado com assinaturas temporárias da API futura, sem alegar execução da página |
| Documentação/exemplos | Links locais, cercas Markdown, cobertura A01–A14/N01–N21 e correspondência dos trechos principais conferidos |

Os relatórios [Python](revisao-2026-10-25-spring.json) e [nativo](revisao-2026-10-25-assisscript.json) guardam saídas e, no caso nativo, hash do compilador. O projeto AssisScript foi consultado e usado para executar as provas, sem editar seus fontes.

Não foram demonstrados conformidade numérica de todo o domínio, gerador portátil de coeficientes, parsers FS/SSC, integração de navegador, política de foco/IME ou latência real limitada a 1/120 s. As correções de contrato são recomendações fundamentadas, não resultados de componentes inexistentes.

## Ampliação de 27/10/2026: planejamento sem interferência no AssisScript

Foram acrescentados os documentos 14–19: fundamentos/perfis, HTDL 0.2 e carregamento, gramáticas FS/SSC, execução/transações/layout, arquitetura nativa/capacidades e conformidade. Exemplos novos cobrem leitura adaptável e dois painéis com estado por nó. O corpus declarativo reúne 16 cenários, todos com status `not-run`.

A revisão corrigiu uma ambiguidade de C10: conservar saídas autorais válidas não congela texto, controles, nós e acessibilidade de uma árvore antiga. Também tornou explícitos tipos enumerados, domínios de propriedade, constraints descendentes e identidade dos recursos. São refinamentos de rascunho, não mudanças em uma release estável implementada.

| Conferência documental | Resultado |
| --- | --- |
| Markdown | 26 arquivos, cercas de código fechadas |
| Links internos | Destinos dentro deste workspace conferidos; referências ao projeto irmão foram ignoradas sem leitura |
| Corpus JSON | 16 IDs únicos, 38 referências a arquivos existentes e resultados esperados documentados |
| Exemplos HTDL não negativos | 6 arquivos com boa formação XML auxiliar, IDs únicos e 8 recursos locais existentes |
| Fontes `.fxs`/`.sscr` novos | Revisão manual em relação à gramática proposta; sem afirmar compilação |
| Projeto/processos AssisScript | Não consultados, executados, alterados ou controlados nesta rodada |

O [relatório desta rodada](revisao-2026-10-27-planejamento.json) guarda contagens e limites da evidência. A conferência usou somente documentação e arquivos deste workspace; não executou as provas numéricas antigas, o compilador AssisScript ou um teste de conformidade das linguagens. A estrutura XML auxiliar continua não sendo um validador HTDL.

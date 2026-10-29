# Navegador em AssisScript, privacidade e busca

Estado: visão atualizada pelo autor em 24/10/2026. Este documento complementa a arquitetura inicial e substitui a recomendação anterior de implementação final do host em Rust.

## AssisScript em dois ambientes

A meta é construir o navegador em AssisScript e executar AssisScript nas páginas. A mesma linguagem terá ambientes e autoridades diferentes:

| Ambiente | Responsabilidade | Acesso |
| --- | --- | --- |
| Aplicativo e motor nativos | Janela, documentos, desenho, rede, persistência e serviços | APIs de plataforma explicitamente disponíveis ao aplicativo |
| Programa de página | Lógica e interatividade do documento | Instância isolada e API limitada fornecida pelo navegador |

Construir o navegador na linguagem não torna o programa de uma página equivalente ao aplicativo nativo. A fronteira de isolamento continua necessária. WebAssembly permanece candidato para executar páginas; ele não determina a linguagem usada para escrever o motor.

Para chegar ao aplicativo nativo, a integração precisa de APIs para janela/eventos, gráficos, fontes e entrada de texto, sockets/TLS, arquivos, concorrência ou tarefas, processos e isolamento. Essa é uma lista de capacidades exigidas, não uma afirmação de que estejam ausentes na versão atual do AssisScript. Os cálculos de layout e SSC exigem uma estratégia numérica fracionária. Importação de bibliotecas nativas por uma ABI/FFI definida pode ser uma ponte de desenvolvimento; a extensão dessa ponte permanece decisão do projeto. Os [contratos de aceitação](18-arquitetura-nativa-e-capacidades.md) detalham como avaliar a integração posteriormente.

O primeiro marco dessa frente deve ser uma janela escrita em AssisScript com entrada, desenho de texto e fechamento correto. Outro marco valida chamadas ao runtime de páginas, seja por binding inicial ou por implementação própria. Os componentes citados no planejamento anterior servem como referências técnicas e opções de protótipo, sem fixar Rust como destino final.

## Motor HTDL com importação de HTML

O autor esclareceu que o navegador deve permanecer puramente voltado a HTDL e buscar tradução eficiente de HTML para HTDL. Assim, a estrutura original entra por um adaptador; o motor visual principal recebe a representação HTDL.

```text
página HTDL nativa -------------------------> árvore semântica HTDL

página HTML -> parser HTML -> adaptador -----> árvore semântica HTDL
                                                |
                                FluxStyle, SSC, desenho e interação
```

A tradução deve usar as regras de análise e construção de árvore de HTML, incluindo recuperação de erros; uma substituição textual de tags não basta. O [padrão HTML da WHATWG](https://html.spec.whatwg.org/multipage/parsing.html#overview-of-the-parsing-model) define a passagem por tokenização e construção de árvore. Exemplo de mapeamento semântico:

| Origem HTML | Destino HTDL conceitual |
| --- | --- |
| `h1` | `div type="heading" level="1"` |
| `button` | `div type="button"` |
| `input type="text"` | `div type="input" kind="text"` |
| `div` sem significado adicional | `div type="container"` |
| `a href="..."` | `div type="link" href="..."` |

O adaptador mapeia uma árvore já construída para nós internos, sem precisar gerar e analisar novamente um grande arquivo textual `.htdl`. Guardar o vínculo com o nó de origem ajuda o inspetor, atualizações e diagnóstico. Preservar origem de segurança, URLs base, identidade de recursos e controles; converter a estrutura não deve conceder autoridade adicional ao conteúdo.

### Três problemas diferentes de compatibilidade

| Camada da origem | Tratamento proposto | Limite |
| --- | --- | --- |
| HTML | Mapear estrutura e semântica para a árvore HTDL | O catálogo inicial precisa ser ampliado para tabelas, mídia e outros elementos conforme a cobertura desejada |
| CSS | Adaptador para estilos computados, começando com subconjunto declarado | Fidelidade depende de parsing, cascata, fontes, layout e propriedades efetivamente suportadas |
| JavaScript | Estratégia própria de compilação/tradução ou compatibilidade, ainda não escolhida | Alterar tags não traduz o programa nem implementa APIs da web |

O objetivo continua ser HTDL, FluxStyle, SSC e AssisScript. A linguagem de apresentação nativa foi nomeada FluxStyle e terá modelo de fluxo; o adaptador de CSS pode resolver suas próprias regras antes de fornecer valores ao motor, sem impor uma cascata ao FS. Traduzir programas JavaScript gerais para AssisScript é um trabalho de linguagem e plataforma, incluindo tipos dinâmicos, objetos, closures e APIs, não uma conversão lexical simples. Executar um runtime JavaScript seria outra decisão de produto e não está assumido aqui.

Portanto, medir e anunciar cobertura: primeiro documentos estáticos e leitura, depois visual de um subconjunto e formulários, depois aplicações interativas conforme o caminho escolhido. O primeiro marco não deve afirmar compatibilidade geral com a web.

Para eficiência, construir a árvore interna diretamente, armazenar conversões identificadas por conteúdo/versão do adaptador e política de origem e invalidar apenas trechos afetados quando houver atualizações. Comparar tempo, memória e fidelidade com um corpus fixado. Não enviar páginas privadas a um conversor remoto implicitamente.

## Privacidade e personalização como requisitos do produto

Propostas iniciais: configurações e temas locais, ausência de telemetria por padrão, armazenamento particionado por origem, permissões específicas, pedidos de rede explicáveis e limpeza completa de estado por site. Sincronização, sugestões online e serviços adicionais precisam de escolha explícita e escopo visível.

Personalização oferece desafios próprios: fontes, temas, dimensões e parâmetros de movimento podem diferenciar usuários. Evitar APIs que enumerem gratuitamente o perfil local; padronizar ou limitar sinais expostos e revisar medições de layout e tempo. O efeito de cada defesa precisa ser testado. [Orientações de mitigação de fingerprinting](https://www.w3.org/TR/fingerprinting-guidance/).

Para SSC, o navegador controla orçamento de simulação, comportamento em segundo plano, preferência de movimento e intensidade máxima. A página recebe as operações de que precisa, sem acesso irrestrito a medições detalhadas do hardware.

Privacidade precisa de um modelo de ameaça: o que o site, o mecanismo de busca, o servidor de sincronização e a rede podem observar. Uma preferência de privacidade não oculta automaticamente o endereço de rede ou o conteúdo que o usuário decide enviar a um serviço.

## Mecanismos de busca

São duas frentes de produto:

1. **Cliente de busca:** escolher Google, Bing, DuckDuckGo ou outro provedor e entregar uma consulta à integração disponível e autorizada. Uma interface HTDL pode apresentar dados retornados por integração própria, ou uma página importada quando suportada. Disponibilidade de API e condições de uso precisam ser verificadas no momento da implementação.
2. **Busca própria:** coletar conteúdo, extrair informação, manter índice, ordenar resultados, combater spam e atualizar o acervo. O resultado pode ser apresentado nativamente em HTDL.

Na busca própria, começar com HTDL e um domínio de conteúdo conhecido, depois expandir para a web importada. O pipeline de descoberta, rastreamento, indexação e entrega é um projeto independente da interface do navegador; a [descrição oficial do funcionamento do Google Search](https://developers.google.com/search/docs/fundamentals/how-search-works) ajuda a delimitar essas responsabilidades.

“Qualidade tão boa quanto Google” é uma meta a avaliar por idioma, categoria e conjunto de consultas: relevância, atualidade, cobertura, latência e resistência a spam. Fazer avaliação comparativa com consultas e julgamentos fixados, sem exigir histórico pessoal identificável para ordenar resultados. Um índice inicial de qualidade em uma área específica é um marco verificável; equivalência geral não pode ser presumida na arquitetura.

O provedor selecionado e os dados enviados devem ser claros. Uma consulta a Google ou Bing continua chegando a esse serviço; a interface privada do navegador não muda por si só a política do destinatário. Evitar envio antecipado da digitação e fallback silencioso para outro provedor. Um intermediário próprio também passa a receber consultas e precisa de política e implementação de privacidade verificáveis.

## Frentes adicionais ao plano inicial

- Evolução nativa do AssisScript para construir janela, motor e serviços.
- Importador HTML e cobertura explícita de CSS/JavaScript.
- Projeto de privacidade, preferências locais e controles de customização.
- Cliente com múltiplos provedores de busca.
- Serviço independente de busca própria e avaliação de qualidade.

Essas frentes devem ter entregas separadas. FluxStyle e SSC podem avançar sem esperar um índice global de busca ou a compatibilidade completa com aplicações HTML. O modelo atual proposto está em [FluxStyle e fluxo](09-fluxstyle-e-fluxo.md).

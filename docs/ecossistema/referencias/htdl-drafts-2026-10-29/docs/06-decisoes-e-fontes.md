# Decisões, questões abertas e fontes

Data: 24/10/2026. Esta lista diferencia o que veio da concepção do projeto do que é uma recomendação técnica deste planejamento.

## Premissas informadas pelo autor

| Premissa | Consequência |
| --- | --- |
| HTDL usa somente tags `div`, diferenciadas por tipo | Não introduzir tags especiais para controles, scripts ou metadados |
| HTDL descreve a estrutura da página | Evitar inserir algoritmos ou uma segunda linguagem de expressões em atributos |
| AssisScript cuida de programação e interatividade | Eventos e APIs da página são consumidos pela mesma linguagem de programação |
| AssisScript existe independentemente e será embutido no navegador | Preservar sua identidade, seu uso nativo e o projeto do compilador |
| O próprio navegador deverá ser construído em AssisScript | Desenvolver capacidades nativas da linguagem e distinguir aplicativo privilegiado de programa de página |
| AssisScript está sendo desenvolvido neste momento | Divergências de fonte, documentação e binário são tratadas como retrato do trabalho em andamento |
| FluxStyle (FS) é a linguagem de apresentação escolhida | Preservar nome e direção: apresentação dinâmica por fluxo, sem cascata como modelo autoral |
| FluxStyle e SSC formam a dupla visual/física | Definir um contrato de destinos, movimento e responsabilidade sobre propriedades |
| Os exemplos de FS e SSC devem estar em inglês | Usar palavras-chave, identificadores, comentários e conteúdo dos exemplos dessas linguagens em inglês |
| FluxStyle aceita `.fxs` e `.flux`, preferindo `.fxs` | Usar `.fxs` nos exemplos e geradores e tratar `.flux` como alias da mesma linguagem |
| Haverá um navegador próprio voltado ao ecossistema | Projetar motor e aplicação de navegador, sem depender da conversão para uma página da web convencional |
| O navegador terá foco em privacidade e customização | Projetar preferências locais, isolamento de dados e políticas de exposição de informações |
| Haverá vários provedores de busca e uma busca própria como objetivo | Separar cliente de busca do projeto de índice e qualidade |
| O motor permanecerá HTDL, com tradução eficiente de HTML | Criar adaptador de estrutura; tratar cobertura de CSS e JavaScript separadamente |

## Recomendações deste rascunho

| ID | Recomendação | Por que | Como reconsiderar |
| --- | --- | --- | --- |
| R01 | `type` obrigatório e catálogo explícito | Diagnósticos e semântica previsíveis | Comparar ergonomia antes de estabilizar 0.1 |
| R02 | Parser estrito, valores sem aspas aceitos | Preserva `<div type=button>` e evita regras implícitas de reparo | Casos de editor podem usar parser tolerante separado |
| R03 | Comportamento nativo por tipo | Teclado e acessibilidade consistentes | Extensões de componentes devem preservar esse contrato |
| R04 | Um programa por documento na 0.1 | Reaproveita módulos do AssisScript e reduz ambiguidade de execução | Acrescentar múltiplas instâncias apenas com regras de ordem e isolamento |
| R05 | Referências a funções nomeadas nos atributos de evento | Funciona sem closures ou funções de primeira classe | Ampliar quando a própria linguagem oferecer recursos novos |
| R06 | Backend WebAssembly e runtime embutido | Isolamento e portabilidade sem criar uma VM do zero | Prova mínima em M2 pode escolher outra opção com custos documentados |
| R07, revisada | Host e motor finais em AssisScript; pontes externas identificadas durante evolução | Atende à visão do autor de construir o navegador na própria linguagem | A extensão de dependências externas e as APIs nativas precisam ser definidas |
| R08 | Renderização nativa e separação motor/aplicativo | Dá ao HTDL seu próprio comportamento e facilita testes | Prévia em HTML pode ser ferramenta auxiliar, com limites declarados |
| R09 | Estilo computado independente da linguagem de autoria | Permite explorar a substituição do CSS sem refazer o motor | Ajustar o modelo a partir das páginas comparativas |
| R10 | Primeiro páginas locais e uma fatia interativa | Valida as partes essenciais com escopo controlado | Só antecipar rede com isolamento e política completos |
| R11 | HTTP/HTTPS como transporte futuro | Evita criar protocolo de rede junto das linguagens | Um esquema próprio pode ser discutido se houver necessidade concreta |
| R12, revisada | Grafo reativo FS, um produtor autoral por propriedade e destinos para SSC | Dá significado operacional ao fluxo; relações e materiais podem compor o núcleo depois | Provar atualização consistente, diagnóstico de ciclos/conflitos e integração física antes de estabilizar sintaxe |
| R13 | SSC com extensão `.sscr` e nome SanSCript | Evita a associação padrão a `.ssc`; mantém a grafia original do autor | Revisão do grupo antes de publicação; não altera associações de outros programas |
| R14 | Recursos de apresentação ativados como conjunto em HTDL 0.2 | Evita publicar metade de uma configuração | Validar loader e edição visual do documento 15 |
| R15 | Falha FS conserva saídas autorais, respeitando a árvore semântica atual | Não deixar controles removidos/desabilitados ativos por erro visual | Cenário R02 e protocolo do documento 17 |
| R16 | Largura disponível como restrição descendente, sem iteração até estabilizar | Elimina realimentação implícita entre layout e fluxo | Definir `row()` e medir exemplos antes de congelar |

As recomendações não descrevem implementação concluída. As premissas confirmadas pelo autor orientam o desenho; as demais escolhas técnicas continuam revisáveis.

A ampliação de [27/10](14-fundamentos-e-perfis.md) especifica paradigmas, gramáticas e execução. As inspeções locais listadas adiante pertencem às rodadas anteriores. Durante o teste de 24 horas do AssisScript, esta ampliação não reinspeciona o projeto nem seus processos. Questões novas P01–P06 estão no [documento 19](19-conformidade-e-cenarios.md).

## Questões abertas e momento de decidir

| Questão | Proposta provisória | Precisa estar decidida até |
| --- | --- | --- |
| Vocabulário do HTDL | Tipos/atributos em inglês, documentação e diagnósticos em português, seguindo `type=button` | Estabilização da gramática |
| Runtime isolado das páginas | WebAssembly/Wasmtime como candidatos; interface acessível ao navegador em AssisScript | Prova M2/MN |
| Plataformas iniciais | Primeiro Windows x64, compatível com o ambiente atual; Linux como alvo seguinte | Preparação do ambiente de implementação |
| Sintaxe e semântica detalhada do FS | Nome e extensões `.fxs`/`.flux` confirmados; detalhes de fluxo são proposta | Marco M6 |
| Infraestrutura compartilhada entre FS e SSC | Linguagens complementares; protocolo de destinos confirmado como proposta de integração | Marcos M6/MS |
| Compatibilidade de páginas HTML dinâmicas | Tradução de estrutura primeiro; caminho para CSS/JavaScript ainda aberto | Antes de anunciar suporte geral à web |
| Biblioteca de janela e desenho | Escolher após provar texto, escala e recorte | M3 |
| Nome do navegador | Não necessário para o motor | Preparação da distribuição |
| Componentes reutilizáveis | Fora de 0.1; não reservar sintaxe apressadamente | Aplicações mais complexas após M5 |
| Identidade e versão dos pacotes de aplicação | Descritor próprio, separado de `.pillow` | Build distribuível/M7 |
| Rede, persistência e permissões | Serviços explícitos e versionados | Antes de habilitar cada serviço |
| Backend de servidores | Fora do escopo atual; AssisScript independente pode evoluir para isso | Quando houver aplicação que precise |

Não é necessário responder todas essas questões antes de implementar o parser ou abrir a primeira janela local. Apenas mudanças nas premissas centrais exigem rever imediatamente o desenho.

As questões específicas [A] dos documentos 10–12 receberam respostas A01–A14, e as propostas [N] receberam pareceres N01–N21 na [revisão de 25/10](13-revisao-extensoes-abertos-e-propostas.md). Resposta técnica, decisão do grupo e implementação são estados diferentes.

## Fontes locais consultadas

Raiz do projeto irmão neste ambiente: `C:\Users\babus\Desktop\AssisScript\AssisScript`.

- [Compilador](../../AssisScript/AssisScript/src/assisc.c): lexer, AST, tipos, parser, verificações e geração de código.
- [Módulos](../../AssisScript/AssisScript/src/modules.h), [coleções](../../AssisScript/AssisScript/src/collections.h) e [ownership](../../AssisScript/AssisScript/src/ownership.h).
- [Manual](../../AssisScript/AssisScript/docs/LINGUAGEM.md), [internos](../../AssisScript/AssisScript/docs/INTERNOS.md), [gramática](../../AssisScript/AssisScript/docs/GRAMATICA.ebnf) e [módulos/pacotes](../../AssisScript/AssisScript/docs/BIBLIOTECAS.md).
- [Erros](../../AssisScript/AssisScript/docs/ERROS.md), bibliotecas em `stdlib/`, manifesto da extensão e [testes 3.2 em desenvolvimento](../../AssisScript/AssisScript/tests/test-v32.js).
- `bin/assis.exe version`, `doctor` e verificações indicadas em [VALIDACAO](VALIDACAO.md).

Os links para o projeto irmão dependem desta organização local. São referências de inspeção, não dependências necessárias para ler o restante do planejamento.

## Referências técnicas externas

Consultadas em 24/10/2026. São fontes para avaliar implementações; não especificações normativas do HTDL.

| Fonte primária | Uso neste planejamento |
| --- | --- |
| [WebAssembly: segurança](https://webassembly.org/docs/security/) | Isolamento do convidado e limites da proteção sobre sua própria memória |
| [Wasmtime: segurança](https://docs.wasmtime.dev/security.html) | Runtime embutido e responsabilidade do host |
| [Wasmtime: configuração](https://docs.wasmtime.dev/api/wasmtime/struct.Config.html) | Fuel, interrupção e configuração explícita de execução |
| [Wasmtime: limites de recursos](https://docs.wasmtime.dev/api/wasmtime/struct.StoreLimitsBuilder.html) | Limitar memória, tabelas e instâncias |
| [W3C: padrão de botão](https://www.w3.org/WAI/ARIA/apg/patterns/button/) | Convenções de ativação com Enter/Espaço e foco |
| [Taffy](https://github.com/DioxusLabs/taffy) | Candidato para cálculo de layout de caixas |
| [COSMIC Text](https://github.com/pop-os/cosmic-text) | Candidato para texto e integração com edição |
| [AccessKit](https://github.com/AccessKit/accesskit) | Candidato para exportação da árvore acessível para a plataforma |
| [Molas em interfaces, Android Developers](https://developer.android.com/develop/ui/views/animations/spring-animation) | Referência de dinâmica física de interfaces, sem depender de Android no navegador |
| [Passo de simulação, Glenn Fiedler](https://gafferongames.com/post/fix_your_timestep/) | Passo fixo e limites de trabalho de simulação |
| [W3C: animações de interação](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) | Redução de movimento não essencial |
| [W3C: fingerprinting](https://www.w3.org/TR/fingerprinting-guidance/) | Revisão da superfície de privacidade de customização e APIs |
| [Google Search: funcionamento](https://developers.google.com/search/docs/fundamentals/how-search-works) | Separação entre descoberta, índice e entrega de resultados |
| [WHATWG: análise de HTML](https://html.spec.whatwg.org/multipage/parsing.html#overview-of-the-parsing-model) | Modelo de análise para o adaptador HTML → HTDL |
| [CSS: cascata](https://www.w3.org/TR/css-cascade-5/) | Comparação do modelo de resolução, sem transformar a proposta FS em cascata implícita |
| [CSS: variáveis](https://www.w3.org/TR/css-variables-1/), [regras condicionais](https://www.w3.org/TR/css-conditional-3/) | Precisar a comparação: CSS também possui mecanismos dinâmicos |

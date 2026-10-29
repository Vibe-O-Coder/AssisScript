# FluxStyle e renderização

Estado: **FluxStyle (FS) é o nome escolhido pelo autor**, com `.fxs` preferida e `.flux` válida. A direção confirmada é apresentação dinâmica por fluxo, em parceria com SSC; para este, `.sscr` é a recomendação revisada. Sintaxe e modelo de execução detalhado continuam propostas.

O [rascunho do FluxStyle](09-fluxstyle-e-fluxo.md) é a proposta atual para entradas reativas, dependências e saídas. Relações de layout, materiais e cenários locais continuam como possibilidades de composição. O [contexto de SSC](07-propostas-visuais-e-ssc.md) registra a exploração física. O navegador final tem como meta de implementação o AssisScript.

## Fronteira estável antes da sintaxe

FluxStyle deve produzir uma descrição tipada de apresentação para cada nó a partir de um grafo de dependências. O motor consome **apresentação computada**, não o texto do arquivo FS. Isso permite refinar a sintaxe sem alterar a identidade semântica do HTDL ou do AssisScript.

Os primeiros estilos padrão ficam no próprio motor. Não será necessário adotar CSS temporariamente para desenhar um botão. O registro de `type` oferece aparência inicial, mas seu papel principal continua sendo semântica e comportamento.

Uma representação interna, descrita aqui como dados e não como formato de autoria, pode conter:

```text
ComputedStyle
  layout: flow | row | column | future_grid
  width/height: auto | typed_length
  min/max: optional_typed_length
  spacing: padding, gap
  align: start | center | end | stretch
  text: family, size, weight, line_height, alignment
  paint: color, background, border, radius, opacity
  target: offset_x, offset_y
  overflow: visible | clip | scroll
```

Esses campos são candidatos. A primeira prova de layout pode implementar somente fluxo vertical, medidas automáticas, preenchimento e espaçamento. Recursos futuros devem produzir erro claro quando não suportados, em vez de serem silenciosamente ignorados.

## Requisitos do FluxStyle

| Área | Requisito recomendado |
| --- | --- |
| Binding | Começar com classes e IDs, sem prioridade implícita por especificidade; ampliar seleção apenas com contrato explícito |
| Tipos | Cores, comprimentos, números e enumerações distintos; erros apontam unidade ou propriedade incompatível |
| Unidades | Começar com pixels lógicos, porcentagem e unidade relativa à fonte; definir referência de cada porcentagem e ciclos |
| Layout | Fluxo de texto e blocos, linha/coluna, alinhamento, tamanhos mínimos/máximos e rolagem |
| Texto | Unicode, quebra de linha, fallback de fontes e direção; formatação não deve cortar bytes de UTF-8 |
| Estado | Foco visível, ponteiro sobre controle, pressionado, desabilitado, marcado e inválido |
| Adaptação | Condições por espaço disponível, tema e preferência de movimento reduzido |
| Reuso | Tokens de design, valores compartilhados e composição explícita |
| Previsibilidade | Um produtor autoral por propriedade; composição explícita, ciclos diagnosticados e origem de cada valor no inspetor |
| Reatividade | Estado e entradas do navegador propagados por dependências, sem atualização manual de cada propriedade |
| Acessibilidade | Estilo de foco sempre recuperável; zoom, texto ampliado e temas de alto contraste testáveis |
| Desempenho | Alterar uma cor não exige relayout; alterar largura invalida a medição necessária |

Layout e SSC precisam de representação fracionária. Como o motor deverá ser escrito em AssisScript, essa frente exige ponto flutuante na linguagem ou uma biblioteca de ponto fixo com operações bem definidas. A primeira API de páginas evita expor coordenadas; uma API geométrica futura deverá acompanhar essa escolha numérica.

## Direção escolhida e composição futura

FluxStyle é a linguagem de apresentação. A proposta é fazer seus valores percorrerem um grafo reativo: entradas, expressões puras e saídas de layout, pintura e destino físico. Relações, materiais e cenários podem ser construídos como abstrações sobre esse núcleo, em etapas posteriores.

Comparar a autoria FS em artigo, formulário, bancada física e página importada de HTML. A parceria com SSC permite transições físicas sem obrigar toda página a simular corpos ou executar fórmulas de estilo a cada frame.

O modelo anterior de resolver estilos autorais por ordem de declaração foi substituído pela proposta de produtor único. Padrões preenchem lacunas; escolhas condicionais usam expressões; composição de materiais deve ser explícita. Preferências do usuário e requisitos de acessibilidade possuem uma camada de autoridade do navegador, cujo contrato deve ser definido sem reintroduzir silenciosamente uma cascata autoral.

`type` não deve expressar cor ou posição. Trocar `button` por um tipo chamado `blue-button` misturaria apresentação com comportamento. Variantes visuais devem ser classes ou estilos nomeados.

## Pipeline do motor visual

1. **Árvore semântica:** nós HTDL, valores e estados dos controles.
2. **Fluxo FS:** propagação de entradas e valores derivados para apresentação computada, com origem rastreável.
3. **Medição de texto e conteúdo:** fontes, glifos, quebras, imagens e restrições disponíveis.
4. **Layout:** caixas, linhas, rolagem e coordenadas lógicas; medição de texto participa do cálculo.
5. **SSC opcional:** evoluir propriedades físicas autorizadas em direção aos destinos confirmados por FS.
6. **Lista de desenho e composição:** comandos de texto, preenchimento, borda, imagem e recorte; desenhar respeitando escala e regiões alteradas.
7. **Acerto de ponteiro e acessibilidade:** usar a geometria final consolidada para interação e limites acessíveis, preservando a ordem semântica.

`hidden=true` exclui toda a subárvore dessas etapas visuais e acessíveis, mesmo que um descendente tenha `hidden=false`. Um controle desabilitado continua visível e acessível com seu estado, mas não é ativável.

Trocar texto invalida medição e pode alterar layout; trocar cor invalida somente pintura; mover foco invalida estado visual e acessível. Começar com recálculo completo para páginas pequenas é aceitável, desde que os limites entre essas responsabilidades estejam definidos. Não começar por um compositor sofisticado.

## Componentes técnicos candidatos

Meta de implementação: **host e motor em AssisScript**. Os componentes abaixo são referências e candidatos a pontes de desenvolvimento. Utilizá-los exige definir uma interface nativa adequada e avaliar até onde o projeto pretende manter dependências externas. A recomendação anterior de host final em Rust foi substituída pelo esclarecimento do autor.

| Necessidade | Candidato a avaliar | Escopo real |
| --- | --- | --- |
| Execução de programa | [Wasmtime](https://docs.wasmtime.dev/security.html) | Runtime WebAssembly, sem resolver sozinho permissões e serviços da página |
| Layout de caixas | [Taffy](https://github.com/DioxusLabs/taffy) | Algoritmos de layout; o motor ainda precisa medir texto, desenhar e aplicar a semântica HTDL |
| Texto | [COSMIC Text](https://github.com/pop-os/cosmic-text) | Modelagem, layout e renderização de texto; avaliar integração e edição nos controles |
| Acessibilidade nativa | [AccessKit](https://github.com/AccessKit/accesskit) | Ponte da árvore acessível para APIs da plataforma, incluindo UI Automation no Windows |

Essas são opções, não dependências já instaladas ou fixadas. APIs, plataformas, licenças, integração e manutenção devem ser verificadas na prova de conceito. Janela e desenho podem começar com uma camada pequena para Windows; a escolha da biblioteca gráfica deve considerar o teste de texto, recorte, escala e acesso remoto ao desktop, antes de se comprometer com uma GPU específica.

O uso de uma biblioteca com algoritmos de layout inspirados no CSS não obriga o navegador a aceitar arquivos CSS. A linguagem de autoria e a implementação dos cálculos são decisões distintas.

## Tarefas frequentemente subestimadas

Uma janela com retângulos e texto ainda não oferece edição de campos. Será necessário tratar seleção, cursor, composição de caracteres, IME, clipboard autorizado pelo usuário, zoom, foco, rolagem e leitores de tela.

O primeiro campo pode ser texto simples em uma linha. Unicode e composição correta são requisitos desde a introdução de entrada, não uma melhoria cosmética posterior. Vídeo, áudio, desenho livre e animações complexas ficam fora do núcleo 0.1.

## Critério para estabilizar o FluxStyle

O nome já foi escolhido. Antes de estabilizar a sintaxe e a execução, produzir as páginas de comparação, provar atualização consistente de dependências, diagnosticar ciclos/conflitos, integrar um canal SSC e testar foco, estado desabilitado, movimento reduzido e 200% de escala. O plano permite construir o primeiro navegador de desenvolvimento enquanto o contrato é refinado.

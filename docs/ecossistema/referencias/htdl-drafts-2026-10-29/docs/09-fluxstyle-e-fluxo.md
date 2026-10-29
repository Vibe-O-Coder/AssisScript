# FluxStyle (FS): proposta de funcionamento por fluxo

Estado: **nome e direção confirmados pelo autor; modelo de execução e sintaxe propostos**, 24/10/2026. FluxStyle cuidará da apresentação dinâmica, em parceria com SSC. Este documento não descreve um compilador já existente. Exemplos de FS e SSC, inclusive identificadores e comentários, são escritos em inglês; a explicação permanece em português.

**Atualização de 25/10:** `.fxs` é a extensão preferida e `.flux` também é válida, por decisão do autor. Para SSC, `.sscr` é a recomendação da [revisão A/N](13-revisao-extensoes-abertos-e-propostas.md). O parecer também detalha estado por nó, carregamento HTDL 0.2 e limites numéricos; este documento preserva a introdução conceitual original.

## A identidade do FluxStyle

A recomendação é dar a “fluxo” um significado operacional: **entradas alimentam transformações, que produzem layout, pintura e destinos físicos**. O navegador mantém essas dependências e atualiza o que foi afetado quando uma entrada muda.

Fluxo não se resume à direção de uma linha ou coluna. São dois aspectos complementares:

- **Fluxo de dados:** estado, espaço disponível, preferências e interação se propagam por dependências explícitas.
- **Fluxo espacial:** o resultado organiza conteúdo em linhas, colunas, quebras e relações entre elementos.

O dinamismo surge da atualização contínua das dependências quando necessário. Uma página em repouso não precisa recalcular tudo a cada frame.

Um navegador próprio permite escolher um núcleo menor e uma semântica consistente, sem assumir a compatibilidade histórica do CSS como regra de autoria. Layout, texto, acessibilidade e adaptação continuam sendo necessidades reais. CSS também possui variáveis e regras condicionais; a diferença proposta para FS está na organização e resolução do fluxo, não em afirmar que CSS é estático. [Variáveis CSS](https://www.w3.org/TR/css-variables-1/), [regras condicionais](https://www.w3.org/TR/css-conditional-3/).

## Um fluxo legível

Sintaxe candidata, reproduzida em [card.fxs](../exemplos/fluxstyle/card.fxs):

```text
flow CardVisuals {
    input expanded: bool = state("card.expanded", false);
    input available: length = parent.availableWidth;

    let cardWidth = min(available, choose(expanded, 640px, 320px));
    let cardLift = choose(expanded, -8px, 0px);

    cardWidth -> layout.width;
    20px -> layout.padding;
    column(gap: 12px) -> layout.children;
    choose(expanded, #7454d8, #252936) -> paint.background;
    #f4f1ff -> paint.text;
    12px -> paint.radius;
    cardLift -> target.offsetY;
}

bind .card to CardVisuals;
```

`flow` declara um conjunto reutilizável de dependências. `input` identifica uma fonte externa somente para leitura. `let` define um valor derivado, também reativo: não é uma variável que o autor precisa atualizar manualmente. A seta liga um valor a uma saída tipada. `bind` instancia o fluxo para cada nó correspondente.

`choose(condition, yes, no)` seleciona entre dois valores do mesmo tipo. O valor de estado ausente usa o padrão declarado. A ponte com estado do AssisScript ainda exige uma API tipada; esta sintaxe não pressupõe que ela já esteja implementada.

`parent.availableWidth` é a largura disponível fornecida pelo passe de layout, a partir de uma restrição resolvida. Não é uma leitura irrestrita da largura final do próprio elemento ou de um pai cujo tamanho depende dele. A primeira implementação precisa anunciar em quais contextos essa entrada é definida.

O exemplo considera uma única `.card`. Com vários elementos, a chave `card.expanded` seria compartilhada entre eles; estados independentes por instância precisarão de um escopo explícito, ainda a definir. Não presumir isolamento de estado apenas por usar um seletor de classe.

## O que muda quando expanded muda

O AssisScript confirma um novo valor para `card.expanded`. Esse único evento invalida `cardWidth`, `cardLift` e a cor de fundo. O navegador recalcula essas dependências e publica uma atualização consistente.

As saídas `paint.text`, `paint.radius` e o espaçamento permanecem com seus valores constantes. A largura exige trabalho de layout; a cor de fundo exige pintura; o destino vertical pode alimentar SSC. “Recalcular só o necessário” é uma meta de implementação e medição, não uma garantia de custo constante.

Uma mudança na largura disponível afeta `cardWidth`, mas não altera o estado da aplicação. Dessa forma, adaptação de janela e interação podem compartilhar um fluxo sem virar uma coleção de regras que disputam uma propriedade.

## Resolução sem cascata implícita

A proposta é **um produtor autoral por propriedade de cada nó**. A identidade ou a proximidade de um seletor não lhe concede prioridade; a posição de uma regra no arquivo não resolve conflitos silenciosamente.

Se dois fluxos vinculados ao mesmo nó escreverem `paint.background`, a validação aponta as duas origens e exige composição explícita. Pode-se reunir a escolha em `choose`, extrair um valor compartilhado ou compor materiais antes de produzir a saída.

```text
flow CardAccent {
    #ff9900 -> paint.background;
}

bind .card to CardVisuals;
bind #featuredCard to CardAccent;
```

Se `#featuredCard` também tiver a classe `card`, existe conflito de produtores. A regra não é “o ID vence”. Esse exemplo é **deliberadamente inválido** no modelo proposto.

Os padrões do navegador preenchem propriedades sem produtor autoral. Herança de apresentação, quando desejada, deve ser declarada como dependência ou composição; não será um mecanismo geral de sobrescrita por ancestralidade. Materiais poderão expandir para um grupo de produtores, com os mesmos diagnósticos de conflito.

Preferências e requisitos de acessibilidade do usuário entram por uma camada explícita do navegador. Essa autoridade é diferente de uma disputa entre seletores do documento. O contrato ainda deve definir quais preferências são entradas do fluxo e quais são restrições finais impostas pelo navegador.

A cascata CSS possui regras próprias para selecionar valores entre declarações concorrentes; o FS propõe outro contrato de resolução. Essa distinção deve aparecer no inspetor, nos erros e nos testes, além da sintaxe. [Modelo de cascata CSS](https://www.w3.org/TR/css-cascade-5/).

## Tipos, composição e limites do núcleo

| Parte | Proposta inicial |
| --- | --- |
| Tipos | `bool`, número, `length`, `color` e enumerações/construtores de layout |
| Valores | Constantes, entradas e expressões puras |
| Operações | Aritmética dimensional válida, comparação, `min`, `max`, `clamp` e `choose` |
| Saídas | Propriedades organizadas em `layout`, `paint` e `target` |
| Binding | IDs e classes, com conflito detectado por nó e propriedade |
| Reuso | Fluxos nomeados; composição de materiais e módulos em proposta posterior |
| Recursos externos | Carregados pelo navegador sob a política da página; fórmulas não fazem pedidos de rede |
| Fora do núcleo inicial | Laços autorais, funções com efeitos, reflexão do navegador, solver geral e alterações arbitrárias da árvore |

Uma cor não pode alimentar uma largura. Porcentagens e medidas relativas precisam declarar a referência. Valores não finitos e dimensões inválidas devem gerar erro definido. Um usuário não precisa dominar essas regras físicas para usar um preset de SSC, mas o compilador precisa verificá-las.

As fórmulas de FS descrevem apresentação e não alteram diretamente o estado ou executam ações da aplicação. O AssisScript continua responsável por validação de negócio, pedidos, mudanças de conteúdo e resposta aos eventos.

## Modelo de execução proposto

```mermaid
flowchart LR
    A[Estado e entradas do navegador] --> B[Dependências FS]
    B --> C[Layout e pintura desejados]
    B --> D[Destinos físicos]
    D --> E[SSC]
    C --> F[Geometria e desenho consolidados]
    E --> F
```

1. Analisar e tipar os fluxos; preservar posições do fonte.
2. Resolver bindings, produtores e dependências para os nós da página.
3. Rejeitar ciclos e conflitos antes de ativar a nova configuração.
4. Receber mudanças de estado e ambiente como um lote com versão.
5. Propagar invalidações e avaliar valores derivados na ordem de dependências.
6. Resolver os passes necessários de layout e preparar pintura e destinos SSC.
7. Confirmar o conjunto de saídas; então publicar geometria e desenho de forma consistente.

Uma tarefa não deve mostrar metade das saídas do estado anterior e metade do novo. Eventos recebidos durante uma atualização entram na próxima tarefa, sem reentrada.

Na primeira prova, recalcular um fluxo inteiro pode ser aceitável, desde que a semântica seja a mesma. Uma etapa posterior compara valores e mantém filas de dependências afetadas, sem exigir um redesenho integral para toda mudança de cor.

## Ciclos e falhas

O grafo declarativo da versão inicial deve ser acíclico. Uma dependência de `a` em `b` e de `b` em `a` é erro, com o caminho do ciclo no diagnóstico. Os dois ramos de `choose` são tipados e considerados na análise conservadora de ciclos, mesmo que só o ramo selecionado precise ser avaliado.

Medir uma propriedade que a própria expressão modifica também pode gerar um ciclo de layout. O núcleo começa com entradas de tamanho disponíveis e bem definidas; leituras gerais de geometria final ficam para uma proposta específica.

Mudanças de classe ou criação futura de nós exigem revalidar os bindings afetados. Se introduzirem conflito, a atualização de apresentação é rejeitada como unidade, preservando a configuração válida anterior e mostrando diagnóstico. Nunca escolher um vencedor pela ordem acidental de descoberta.

Loops físicos no tempo pertencem ao SSC. Eles não justificam permitir dependências circulares indefinidas em expressões FS.

## SSC recebe destinos e produz movimento

Sintaxe SSC candidata, reproduzida em [card.sscr](../exemplos/fluxstyle/card.sscr):

```text
motion CardMotion {
    spring(
        target: fs.target.offsetY,
        frequency: 4Hz,
        dampingRatio: 0.8
    ) -> presentation.offsetY;
}

bind .card to CardMotion;
```

`fs.target.offsetY` referencia o destino confirmado pelo fluxo FS do mesmo nó. SSC é o produtor de `presentation.offsetY`; a largura do exemplo muda por layout normal, sem alegar animação física de dimensões nesta primeira proposta.

`frequency` representa a frequência natural da mola, em Hz, e `dampingRatio` uma razão sem dimensão. Sua relação com massa e constantes físicas precisa ser parte do contrato do motor. Esses parâmetros substituem neste exemplo uma duração de resposta cujo significado ainda não foi definido. O valor de destino é um comprimento e a saída preserva essa dimensão.

Sem binding SSC, o compositor aplica diretamente o destino visual neutro ou solicitado. Com SSC e movimento reduzido, aplica diretamente o mesmo destino. `target.offsetY` representa deslocamento desejado em relação à caixa de layout; não altera a semântica ou o tipo HTDL do nó.

O primeiro canal é deslocamento de apresentação, sem reflow por frame. O motor mantém hit testing, desenho e limites acessíveis na mesma geometria consolidada. Não alimentar o fluxo do frame atual com o resultado parcial da mola: essa realimentação precisa de um contrato temporal explícito, fora do núcleo inicial.

Se o destino mudar durante o movimento, SSC retoma a partir de sua posição e velocidade atuais. O estado interno da simulação evolui por passos de tempo; ele não é uma variável circular do grafo de expressões FS. Pausa, repouso, quotas e preferências continuam responsabilidades do navegador, conforme [SSC](07-propostas-visuais-e-ssc.md).

## Privacidade, customização e importação

Entradas como tema, densidade e movimento devem vir de um contrato pequeno e controlado. Não expor uma lista de temas instalados, materiais locais, fontes ou características de hardware porque o fluxo consegue reagir a valores. A apresentação não recebe autoridade para fazer rede ou persistir dados.

O importador HTML pode resolver o subconjunto suportado de CSS em sua própria camada e fornecer valores ao motor. O parser FS e seu contrato de produtores não precisam implementar a cascata CSS. A interação entre aparência importada e apresentação escolhida pelo usuário exige uma política explícita, mantendo a origem de cada valor visível no inspetor.

## Próxima prova recomendada

Um nó HTDL, um fluxo FS, uma entrada booleana e um canal SSC. Alterar o estado deve atualizar largura, cor e destino; SSC suaviza somente o deslocamento. Conferir também conflito de produtores, ciclo, troca de destino durante movimento e aplicação direta com movimento reduzido.

Antes de escolher todas as palavras da gramática, provar esse ciclo de ponta a ponta. Nome e extensões FluxStyle já estão escolhidos; a sintaxe e os detalhes do compilador permanecem propostas. A extensão SSC `.sscr` é uma recomendação revisada, não uma decisão atribuída ao grupo.

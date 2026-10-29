# FluxStyle e SSC: contexto das propostas visuais

Estado: exploração de design, 24/10/2026, atualizada após a escolha de **FluxStyle (FS)**. A proposta de SSC (SanSCript) como linguagem de física veio de um membro do projeto. TRAMA, MATÉRIA e CENÁRIOS abaixo registram ideias anteriores, não nomes concorrentes para a linguagem escolhida. Seus trechos são estudos conceituais; os exemplos FS/SSC atuais estão no [modelo de fluxo](09-fluxstyle-e-fluxo.md) e usam inglês.

## Direção recomendada

Combinar **FluxStyle para apresentação dinâmica por fluxo** com **SSC para dinâmica física**. O HTDL descreve o significado e a estrutura; FS propaga entradas e dependências para uma configuração visual desejada; SSC faz propriedades evoluírem no tempo; AssisScript implementa a lógica e o próprio navegador. Relações e materiais podem tornar-se abstrações do FS.

Essa divisão permite um artigo estável, um botão com resposta elástica e uma área experimental de objetos com colisão no mesmo ecossistema. O programa não precisa integrar uma mola em cada manipulador de evento.

| Camada | Pergunta respondida |
| --- | --- |
| HTDL | O que existe e qual é seu significado? |
| FluxStyle | Como entradas e dependências produzem organização e apresentação? |
| SSC | Como os elementos se movem, resistem e interagem fisicamente? |
| AssisScript | O que acontece na aplicação e como o navegador funciona? |

FS e SSC são linguagens complementares na visão escolhida pelo grupo. Elas podem compartilhar infraestrutura de compilação e runtime, mantendo responsabilidades próprias. Uma página continua podendo dispensar física. A revisão de 25/10 recomenda `.sscr` para SSC e carregamento por recursos de apresentação em HTDL 0.2; usar física não dispensa definir cores, fontes e tamanho do texto.

## Ideia 1 — TRAMA: relações antes de coordenadas

Nome da proposta anterior: **TRAMA**. A ideia de descrever intenções e relações pode alimentar uma evolução do FS: manter dentro, alinhar, afastar, agrupar e reorganizar quando faltar espaço. Um futuro resolvedor de restrições exigiria um contrato próprio; não faz parte automaticamente do primeiro grafo FS.

Sintaxe conceitual:

```text
layout .card {
    width: prefer(360px);
    stay: inside(parent, padding: 24px);
    content: column(gap: 16px);
}

arrange .card {
    direction: row;
    when crowded: wrap;
}
```

`prefer` é uma preferência, não uma exigência impossível em uma janela estreita. Relações obrigatórias incompatíveis geram diagnóstico com as regras envolvidas. Preferências podem ser relaxadas em uma ordem documentada. O resolvedor não deve depender de uma simulação infinita até o layout parecer aceitável.

É possível permitir que um bloco de ações se alinhe à linha de base de um título ou que uma barra lateral só exista quando não comprometer a largura legível do artigo. O ganho seria expressar intenção sem multiplicar ajustes de coordenadas para cada tamanho de janela.

## Ideia 2 — MATÉRIA: estilos como materiais

Nome da proposta anterior: **MATÉRIA**. A autoria escolhe materiais reutilizáveis, que agrupam superfície, tinta, forma e comportamento físico opcional. Papel, borracha, vidro ou metal são nomes de presets, sem mudar o papel semântico dos elementos. Sua composição com produtores FS/SSC ainda deve ser especificada; a sintaxe abaixo é histórica e conceitual.

```text
material paper {
    surface: solid(#f5f1e8);
    ink: #24211c;
    corners: 12px;
}

material elastic {
    surface: solid(#7454d8);
    ink: #ffffff;
    motion: ssc.spring(response: 280ms, bounce: 0.12);
}

.card { material: paper; }
.action { material: elastic; }
```

Os números e construtores só demonstram a intenção. A unidade de resposta e o significado exato de `bounce` precisariam ser definidos. O motor pode convertê-los em parâmetros de uma mola.

Relações e materiais são compatíveis como abstrações futuras do FluxStyle. O núcleo de fluxo e o contrato com SSC devem ser provados antes de ampliar a linguagem com um resolvedor geral ou um sistema completo de materiais.

## Ideia 3 — CENÁRIOS: a interface pode assumir apresentações diferentes

Uma página descreve conteúdo, controles e relações; o usuário escolhe uma apresentação local: leitura, painel compacto, cartões ou espaço de trabalho. A mesma aplicação pode aparecer como documento ou bancada sem exigir que seu autor reescreva a lógica.

O navegador poderia usar essas mesmas linguagens para a própria interface: abas, painéis e organização do espaço. Isso aproxima customização do produto e criação de páginas. A interface privilegiada do navegador deve continuar isolada dos documentos, especialmente a identidade do endereço, permissões e controles de segurança.

As regras locais do usuário podem alterar paleta, densidade, tipografia e intensidade do movimento. As adaptações precisam preservar informações, rótulos, ordem semântica e acesso às ações. Um tema não deve transformar um gráfico informativo em uma decoração sem equivalência.

Essa direção aproveita uma característica central da visão do produto: o usuário também participa da apresentação. O navegador não deve fornecer às páginas um inventário de seus temas, materiais ou extensões locais. Medições de layout podem revelar informações indiretamente; a API precisa considerar essa superfície, sem prometer invisibilidade absoluta. [Orientações de fingerprinting da W3C](https://www.w3.org/TR/fingerprinting-guidance/).

## SSC: física de verdade, com níveis diferentes de integração

A ideia é tecnicamente viável. Molas amortecidas já são usadas em sistemas de interface para calcular posição e velocidade até atingir um destino; rigidez e amortecimento controlam a resposta. O SSC poderia transformar esse mecanismo em um contrato declarativo nativo da plataforma. [Referência de física de molas em interfaces](https://developer.android.com/develop/ui/views/animations/spring-animation).

### Nível A — resposta física de apresentação

O layout define o destino. SSC calcula o movimento até ele: mola, amortecimento, inércia e limites. Uma mudança de layout pode fazer um painel se acomodar em sua nova posição; um gesto pode arrastar um cartão e soltá-lo com resistência.

```text
physics .card {
    position: spring(to: layout.position);
    stiffness: 180;
    damping: 22;
    mass: 1;
    settle: sleep;
}
```

A escala de massa e as unidades das constantes precisam ser formalizadas antes de aceitar essa sintaxe. Para autoria comum, presets ou duração de resposta podem ser mais claros que constantes físicas brutas.

Este seria o primeiro SSC a implementar: uma propriedade, um destino, uma mola, repouso e preferência de movimento reduzido. Já oferece identidade visual e pode funcionar com HTDL importado.

### Nível B — mundos físicos delimitados

Uma região da página funciona como uma pequena cena: corpos podem colidir, sofrer gravidade, ter atrito e prender-se por juntas ou ímãs. Aplicações possíveis: simulações, organizadores de cartões, ferramentas educativas, jogos e a bancada personalizada do navegador.

```text
world workbench {
    region: #workbench;
    gravity: (0, 600);
    bounds: contain;

    body .piece {
        shape: box;
        mass: 1;
        friction: 0.4;
        restitution: 0.2;
        draggable: true;
    }
}
```

É uma proposta de física 2D, não a obrigação de construir um mundo 3D para cada documento. A região tem limites de corpos, trabalho por passo e energia. Texto e formulários fora dela conservam layout estável. Um corpo que dorme deixa de consumir passos de simulação até receber um evento relevante.

### Nível C — layout governado por forças

Elementos podem se repelir para manter distância, agrupar por atração e organizar-se ao redor de âncoras. É uma direção ousada para mapas de conhecimento e espaços autorais.

Porém, um layout principal não deve ficar indefinidamente dependente da convergência de uma simulação. Esse nível precisa de limites, uma configuração estática de recuperação e regras sobre ordem de leitura e foco. Começaria como modo experimental de uma região, após os níveis A e B.

## Contrato entre layout, SSC e lógica

Cada propriedade precisa de um responsável por fase:

1. O AssisScript altera estado e solicita operações pela API.
2. FluxStyle propaga dependências e resolve a apresentação e os destinos de referência.
3. SSC recebe destinos e aplica a dinâmica nas propriedades autorizadas.
4. O motor consolida a geometria visível, o desenho, os limites acessíveis e a região de interação.

No nível A, animar deslocamento visual não deve gerar um ciclo em que cada posição parcial vira um novo destino de layout. Layout e movimento mantêm estados distintos. No nível B, a posição física pertence ao mundo delimitado; o layout define a região e seus limites.

Ponteiro, desenho e limites acessíveis devem usar a mesma geometria consolidada. A ordem de foco permanece semântica. Quando um controle recebe foco por teclado, seu movimento decorativo é estabilizado; texto sendo editado não deve fugir da interação. Eventos de clique continuam sendo decisões discretas, não efeitos de uma colisão visual.

SSC não executa comandos arbitrários, não acessa rede, arquivos ou relógios de alta precisão. O motor pode entregar notificações discretas, como repouso ou colisão, a funções AssisScript. Eventos são limitados e enfileirados; nenhuma chamada por corpo a cada passo é exigida para manter a física.

## Movimento, consumo e previsibilidade

Para a prova, usar passo de simulação fixo, por exemplo 1/120 s, com teto de passos por frame e interpolação de desenho. Os valores são candidatos a medir. Um acumulador sem limite pode entrar em um ciclo de recuperação que consome cada vez mais trabalho. [Discussão técnica sobre passo de simulação](https://gafferongames.com/post/fix_your_timestep/).

Pausar abas ocultas, suspender corpos em repouso e validar limites dos parâmetros. Para testes, usar entradas registradas e aleatoriedade com semente, quando houver; passo fixo sozinho não garante igualdade bit a bit entre plataformas ou versões.

O motor escrito em AssisScript precisará de cálculos fracionários por ponto flutuante ou representação de ponto fixo bem definida. Essa é uma necessidade de evolução da linguagem/bibliotecas; não implica colocar física em uma implementação final externa por padrão.

Movimento reduzido é uma decisão do navegador e do usuário que o documento deve respeitar. Nas transições decorativas, aplicar diretamente o estado final. Em atividades nas quais mover objetos é a própria função, oferecer controles discretos equivalentes quando possível. A possibilidade de desabilitar animações de interação não essenciais é orientada pela [W3C, critério 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html), de nível AAA.

## A piada de tudo ser background-color

Pode existir como dialeto optativo, por exemplo **BG++**, com construtores tipados distinguindo os domínios:

```text
background-color .card {
    background-color: paint(#7454d8);
    background-color: column(gap: 16px);
    background-color: spring(response: 280ms);
}
```

Nesse dialeto, a palavra repetida introduz uma declaração; `paint`, `column` e `spring` identificam pintura, layout e dinâmica. Duas declarações de pintura conflitantes continuam exigindo uma regra ou diagnóstico. Não seriam três atribuições convencionais à mesma propriedade com sobrescrita silenciosa.

Um formatador poderia expandir o dialeto para os nomes canônicos, e o inspetor sempre mostraria o significado real. A piada sobreviveria sem repetir a dificuldade de leitura do primeiro AssisScript. Eu manteria esse modo como opção cultural do projeto, depois de validar um núcleo legível.

## Como escolher sem congelar uma ideia cedo demais

Prototipar as três direções sobre a mesma representação visual e quatro cenas:

- Artigo: leitura, imagens e texto ampliado, com estabilidade.
- Formulário: foco, edição e confirmação, com resposta física discreta.
- Bancada: cartões arrastáveis, molas e colisões delimitadas.
- Página HTML importada: apresentação básica sem exigir autoria manual de todas as regras.

Comparar tamanho do código, entendimento por outro membro, conflitos de regra, personalização e trabalho de execução. A prova interativa desta conversa ilustra somente uma mola; não implementa FS, SSC ou o futuro navegador.

A direção atual é **FluxStyle + SSC**, com relações, materiais e cenários como possibilidades de evolução. As propostas anteriores ficam como referência de design. O [modelo FS](09-fluxstyle-e-fluxo.md) substitui a sugestão de escolher outro nome e propõe um contrato único de dependências, unidades e responsabilidade sobre propriedades.

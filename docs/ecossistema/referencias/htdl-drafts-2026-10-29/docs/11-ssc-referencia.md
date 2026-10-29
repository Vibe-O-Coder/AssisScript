# SSC 0.1 — referência do rascunho

Estado: rascunho de referência, 25/10/2026. Consolida a parte de física dos documentos [07](07-propostas-visuais-e-ssc.md) e [09](09-fluxstyle-e-fluxo.md) e completa as lacunas com propostas marcadas. **Não existe compilador SSC**: nada aqui descreve funcionalidade implementada. Código, identificadores e comentários dos exemplos de SSC estão em inglês; a explicação, em português.

Complementa a [referência do FS](10-fluxstyle-referencia.md). As marcas **[G]**, **[P]**, **[N]** e **[A]** têm o mesmo sentido definido lá. Os números marcados como "emulação" vêm do script [`spring_reference.py`](../exemplos/fluxstyle/spring_reference.py), que reproduz em Python o algoritmo inteiro descrito na seção 6. Eles **não** foram gerados por um compilador SSC nem pelo AssisScript.

**Revisão técnica de 25/10:** respostas [A] e pareceres [N] estão no [relatório de revisão](13-revisao-extensoes-abertos-e-propostas.md). As garantias numéricas amplas do primeiro rascunho foram restringidas à cobertura efetivamente testada.

**Detalhamento de 27/10:** a [gramática consolidada](16-gramaticas-fs-e-ssc.md) completa a análise léxica; o [protocolo](17-execucao-transacoes-e-layout.md) distingue ocultação de nó, suspensão de aba e descarte temporal. Observações sobre a implementação AssisScript são históricas e não foram reinspecionadas nesta rodada.

**Nome por extenso:** **SanSCript**, grafia presente na mensagem original do autor; não houve confirmação de uma mudança para SansSCript. **Extensão recomendada nesta revisão:** `.sscr`. `.ssc` e `.fs.ssc` não serão associações padrão do rascunho. A recomendação de extensão está separada das decisões já confirmadas do grupo.

## 1. Papel do SSC

**[G]** O SSC calcula o movimento físico até os destinos definidos pelo FS. É complementar ao FS e opcional: uma página continua válida sem física.

A pergunta que o SSC responde é: *dado o destino que o FS confirmou, como a apresentação se move até lá?*

| O SSC faz | O SSC não faz |
| --- | --- |
| Evoluir no tempo propriedades de apresentação (molas, repouso) | Escolher destinos (é do FS) |
| Retomar a partir da posição e da velocidade atuais quando o destino muda | Alterar layout, árvore ou semântica; não causa reflow por quadro |
| Aplicar o destino direto quando há movimento reduzido | Executar comandos, acessar rede, arquivos ou relógios de alta precisão |
| Limitar o próprio custo (passo fixo, teto de trabalho) | Expor posições ou velocidades ao programa da página |

**[P]** O documento 07 define três níveis de ambição. Só o primeiro entra na 0.1:

| Nível | Conteúdo | Situação |
| --- | --- | --- |
| A | Resposta física de apresentação: um destino, uma mola, repouso, movimento reduzido | **0.1** |
| B | Mundos físicos delimitados: corpos, colisão, atrito, juntas | Reservado, fora da 0.1 |
| C | Layout governado por forças | Reservado, experimental, depois de A e B |

## 2. Estrutura do arquivo

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

- `motion Nome { ... }` declara um conjunto reutilizável de canais.
- Cada canal liga uma primitiva (`spring`) a uma propriedade de `presentation`.
- `bind seletor to Nome;` instancia o movimento para cada nó correspondente. Seletores, regras de ligação e comentários são os mesmos do FS.

Gramática da 0.1 **[N]**:

```ebnf
file        = { motion | binding } ;
motion      = "motion", identifier, "{", { channel }, "}" ;
channel     = "spring", "(", argument, ",", argument, ",", argument, ")",
              "->", path, ";" ;
argument    = ( "target" | "frequency" | "dampingRatio" ), ":", value ;
value       = path | literal ;
binding     = "bind", selector, "to", identifier, ";" ;
```

Os três argumentos são obrigatórios e podem vir em qualquer ordem. `frequency` e `dampingRatio` aceitam só **literais** nesta versão: o SSC não depende do grafo de entradas do FS, o que mantém os coeficientes fixos por vínculo. **[N]**

## 3. Canais

O SSC lê destinos confirmados pelo FS e escreve valores de apresentação. Os dois lados usam nomes de propriedade iguais.

| Lê (do FS) | Escreve (SSC) | Tipo | Sem produtor FS quando motion está ligado |
| --- | --- | --- | --- |
| `fs.target.offsetX` | `presentation.offsetX` | `length` | erro `S302` |
| `fs.target.offsetY` | `presentation.offsetY` | `length` | erro `S302` |

- **[P]** O primeiro canal é deslocamento de apresentação, sem reflow por quadro. A largura do exemplo do cartão muda por layout normal, não por física.
- **[N]** O canal de saída precisa ter o mesmo nome do destino lido (`offsetY` com `offsetY`); outra combinação é erro `S203`.
- **[N]** Cada propriedade de `presentation` tem um único produtor por nó, a mesma regra do FS. Dois movimentos escrevendo `presentation.offsetY` no mesmo nó são erro `S301`.
- **[N]** Se um `motion` lê `fs.target.offsetY` e nenhum fluxo FS vinculado ao nó produz `target.offsetY`, é erro `S302`, em vez de assumir `0px` em silêncio.
- Canais futuros que não exigem reflow (escala, rotação, opacidade) ficam fora da 0.1.

## 4. A primitiva `spring`

| Argumento | Tipo | Faixa aceita **[N]** | Significado |
| --- | --- | --- | --- |
| `target` | caminho `fs.target.*` | — | Destino confirmado pelo FS, do mesmo nó |
| `frequency` | `frequency` | de 0,5 Hz a 10 Hz | Frequência natural da mola |
| `dampingRatio` | `number` | de 0,1 a 4 | Razão de amortecimento, sem unidade |

**[P]** `frequency` e `dampingRatio` substituem uma duração de resposta cujo significado nunca foi definido. A relação com massa e rigidez fica dentro do motor; a autoria não escolhe constantes físicas brutas.

Interpretação de `dampingRatio`:

- Menor que 1: sub-amortecida; passa do destino e volta (ultrapassagem).
- Igual a 1: amortecimento crítico; chega sem ultrapassar, o mais rápido possível.
- Maior que 1: super-amortecida; chega devagar, sem ultrapassar.

Valores fora das faixas são erro `S202` na ligação. As faixas constituem um **perfil experimental**, amostrado na seção 6; não foi provado que todos os valores intermediários e todas as sequências de destinos cumprem uma tolerância global ou uma faixa de intermediários. A implementação deve checar operações em execução, e ampliar o perfil exige nova validação.

## 5. Semântica de tempo e movimento

### 5.1 Modelo contínuo

Para cada canal e cada nó existe um estado: posição de apresentação `p`, velocidade `v` e uma marca de repouso. Com `t` o destino, `x = p - t` a posição relativa, `ω = 2π · frequency` e `ζ = dampingRatio`, a dinâmica é a mola amortecida:

```text
x'' = -ω² · x - 2 · ζ · ω · x'
```

A posição desenhada é sempre `p = t + x`. Trabalhar com `x` (posição relativa ao destino) deixa a mudança de destino trivial, como mostra a seção 5.3.

### 5.2 Passo fixo

- A simulação avança em passos de **1/120 s**, independentes da taxa de atualização da tela. **[P]** (o documento 07 sugere 1/120 s como candidato a medir).
- **[N, corrigida]** Manter um resto inteiro de tempo: `total = remainder + elapsedMs * 120`; `due = total / 1000`; `remainder = total % 1000`; executar `min(due, 8)` e descartar `due - executed`. Conferir/limitar `elapsedMs` e intermediários. O resto só representa a fração de passo, nunca o trabalho inteiro descartado.
- Há um teto de passos por quadro (candidato: **8**). O excedente é descartado, não acumulado: sob carga a simulação fica mais lenta, em vez de entrar em espiral de recuperação. **[P]**
- Abas ocultas não avançam a simulação; na volta reiniciar a base monotônica e o resto, sem recuperação do tempo perdido. **[P]**
- O desenho usa o estado do último passo. Interpolar entre dois passos é opcional e não muda o contrato.

### 5.3 Mudança de destino durante o movimento

Quando o FS confirma um novo destino `t'`, conservar o **deslocamento de apresentação** `p` e a velocidade, atualizando `x := x + (t - t')`. Isso conserva a posição absoluta de tela apenas se a caixa de layout também permanecer igual. Mudança de layout pode mover a caixa; preservar pixels de tela nesse caso exige outro contrato. Conferir estouro na soma e na subtração. **[P, corrigida]**

Emulação com caixa de layout fixa: o cartão sobe para −8 px; antes de integrar o passo 11, o destino volta a 0 px. O ponto de inversão é −5,9496 px, e o repouso em 0 px chega no passo 51 (425 ms). O valor amostrado depois do passo 11 já inclui a integração seguinte; não confundir continuidade na troca com posição igual entre dois ticks diferentes.

### 5.4 Primeira apresentação

Quando um nó passa a ter o movimento (carga da página, criação do nó, classe que o liga), a posição de apresentação começa **igual ao destino**, sem animação. Uma página aberta com `expanded` já verdadeiro não "cai" para o lugar. **[N]**

### 5.5 Repouso

O canal entra em repouso quando `|x| < 1/64 px` e `|v| < 0,5 px/s` por **3 passos seguidos**. Ao entrar em repouso, `x` e `v` viram zero, a posição vira exatamente o destino e o canal deixa de consumir passos até receber um novo destino. **[N]** Os limiares são candidatos a medir; sem esse corte, a aritmética inteira poderia deixar a posição oscilando em torno de um valor residual.

### 5.6 Movimento reduzido

**[P]** `env.reducedMotion` verdadeiro é uma decisão do usuário que o documento deve respeitar. O SSC então aplica **diretamente o destino**: `p := t`, `v := 0`, sem agendar passos. O resultado final é o mesmo da animação, só sem trajeto. Se a preferência mudar com um movimento em curso, ele termina imediatamente no destino. Nenhuma ação depende do movimento ter ocorrido.

### 5.7 Foco, edição e ocultação

- **[R — A09]** Ao receber foco por teclado ou durante edição, congelar o deslocamento de apresentação atual e zerar a velocidade. Pausar os canais do nó e dos ancestrais que moveriam a subárvore focada. Guardar destinos novos; ao liberar a proteção, retomar da posição preservada. Isso substitui a proposta de saltar ao destino ao receber foco. Não promete impedir mudanças independentes de layout; precisa de prova com teclado/IME.
- Subárvore com `hidden="true"` não é simulada. Ao voltar a ser exibida, o canal começa no destino, como em 5.4. **[N]**
- Quando o nó é removido, o estado é descartado.

### 5.8 Cliques e geometria

Um clique é uma decisão discreta, não efeito de uma colisão visual **[P]**. Desenho, acerto de ponteiro e limites acessíveis usam a **mesma geometria consolidada** (layout mais `presentation`). Quem clica em um cartão em movimento acerta onde ele aparece naquele instante.

## 6. Aritmética de referência

### 6.1 Por que ponto fixo

O núcleo usa inteiros com 16 bits fracionários e intermediários de 64 bits, como perfil experimental. Resultados bit a bit entre plataformas exigem os mesmos coeficientes canônicos, valores codificados, arredondamentos, entradas e passos; usar inteiros sozinho não prova essas condições. As verificações de overflow devem ocorrer antes da aritmética modular nativa do AssisScript.

Representação **[N, revisada]**: 16 bits fracionários; o limite público Q16.16 do FS é uma restrição de perfil, não a faixa total do armazenamento `int64`. Estados como velocidade podem exigir faixa maior. `fx_mul(a,b) = (a*b + 32768) >> 16`, com deslocamento aritmético e empate para +infinito. Conversão de literal/coeficiente usa empate afastando de zero; são regras diferentes e explícitas.

### 6.2 O passo exato

Para um passo fixo `Δ = 1/120 s`, a solução da mola é linear no estado. Existe uma matriz 2×2, que só depende de `frequency`, `dampingRatio` e `Δ`, tal que `[x', v'] = M · [x, v]`. Calcula-se `M` **uma vez por vínculo**; depois, cada passo custa quatro multiplicações e duas somas.

Com `ω = 2π · frequency` e `ζ = dampingRatio`:

**ζ < 1.** `ωd = ω·√(1−ζ²)`, `e = exp(−ζ·ω·Δ)`, `c = cos(ωd·Δ)`, `s = sin(ωd·Δ)`, `k = ζ·ω/ωd`:

```text
m11 = e · (c + k·s)        m12 = e · s / ωd
m21 = −e · (ω²/ωd) · s     m22 = e · (c − k·s)
```

**ζ = 1.** `e = exp(−ω·Δ)`:

```text
m11 = e · (1 + ω·Δ)        m12 = e · Δ
m21 = −e · ω² · Δ          m22 = e · (1 − ω·Δ)
```

**ζ > 1.** `γ = ω·√(ζ²−1)`, `e = exp(−ζ·ω·Δ)`, `ch = cosh(γ·Δ)`, `sh = sinh(γ·Δ)`, `k = ζ·ω/γ`:

```text
m11 = e · (ch + k·sh)      m12 = e · sh / γ
m21 = −e · (ω²/γ) · sh     m22 = e · (ch − k·sh)
```

Cada `mij` é arredondado para o valor Q16.16 mais próximo. Um passo é:

```text
x' = fx_mul(m11, x) + fx_mul(m12, v)
v' = fx_mul(m21, x) + fx_mul(m22, v)
```

com `x` em px e `v` em px/s, ambos Q16.16.

Gerar os coeficientes sem `float` é possível em princípio com aproximações numéricas, mas o script atual usa `math` e não implementa nem valida esse gerador em ponto fixo. Os números da matriz abaixo são vetores de referência concretos. **A tolerância anterior de ±1 ULP nos coeficientes foi rejeitada:** ela não garante erro de posição abaixo de 1/16 px em todo o perfil. Um gerador nativo precisa produzir os inteiros canônicos ou provar sua conformidade por cenários e domínio; uma promessa genérica sobre séries de Taylor não basta. Ver N15 no parecer.

Valores de referência (4 Hz, ζ = 0,8, Δ = 1/120 s), em Q16.16:

| `m11` | `m12` | `m21` | `m22` |
| --- | --- | --- | --- |
| 64251 | 461 | −290983 | 45727 |

### 6.3 O que a emulação mostra

Resultados da emulação do algoritmo da seção 6.2 (degrau de 8 px, grade de 7 frequências de 0,5 a 10 Hz e 6 razões de 0,1 a 4):

| Verificação | Resultado |
| --- | --- |
| Maior erro contra a solução analítica nos primeiros 3 s | aproximadamente 0,0213 px, incluindo corte de repouso, para degrau de 8 px |
| Pares amostrados que não chegam ao repouso em 60 s | nenhum dos 42; o mais lento leva aproximadamente 15,758 s (0,5 Hz com ζ = 4) |
| Garantia global de produto máximo | não estabelecida pelo script original; operações precisam de checagem |
| Mudança de destino durante o movimento | continuidade do deslocamento de apresentação, com caixa fixa no ensaio |

O domínio experimental continua: `frequency` de 0,5 a 10 Hz, `dampingRatio` de 0,1 a 4 e destinos de até **±4096 px**. Limitar destinos não limita sozinho velocidade ou diferença entre posição e destino; checar os intermediários e a sequência de retargeting também é necessário.

**Conformidade revisada.** Os vetores canônicos inteiros do núcleo devem coincidir para as mesmas entradas e passos. **1/16 px não é uma tolerância geral ratificada.** A auditoria com destino −4096 px encontrou desvio de 17,90625 px com coeficientes perturbados em apenas ±1 ULP, em 0,5 Hz e ζ=0,1. Erros medidos em degraus de 8 px não autorizam extrapolar para toda a faixa. Ver [evidência reproduzível](13-revisao-extensoes-abertos-e-propostas.md).

### 6.4 Por que não usar Euler

Euler explícito ou semi-implícito é o primeiro algoritmo que quase todo mundo escreve, porque dispensa `exp`, `sin` e `cos`. Neste caso, ele **não é conforme**: a discretização amortece mais do que a mola pede.

| 4 Hz, ζ = 0,8, degrau de 8 px | Referência | Euler semi-implícito |
| --- | --- | --- |
| Ultrapassagem do destino | 0,122 px | 0,023 px |
| Posição no passo 5 (relativa ao destino) | 5,51 px | 4,91 px |

O Euler também pode ficar instável dependendo dos parâmetros e do passo. A matriz analítica real, para frequência e amortecimento positivos, não tem o mesmo erro de discretização; sua quantização ainda exige validação. Euler não reproduz estes vetores canônicos e seria uma aproximação de protótipo, não o algoritmo de referência aqui descrito.

### 6.5 Orientação para escolher parâmetros

Medições da emulação (4 Hz, degrau de 8 px; ultrapassagem teórica `exp(−π·ζ/√(1−ζ²))` vezes a distância):

| `dampingRatio` | Ultrapassagem medida | Teórica | Tempo até o repouso |
| --- | --- | --- | --- |
| 0,3 | 2,971 px | 2,979 px | 842 ms |
| 0,5 | 1,301 px | 1,304 px | 508 ms |
| 0,8 | 0,122 px | 0,121 px | 342 ms |
| 1,0 | 0 | 0 | 358 ms |
| 2,0 | 0 | 0 | 958 ms |

O tempo escala com `1/frequency`. Com ζ = 0,8: 0,5 Hz leva 2583 ms, 1 Hz leva 1300 ms, 4 Hz leva 342 ms e 8 Hz leva 192 ms. Para interface, valores de ζ entre 0,6 e 1,0 são o ponto de partida natural; acima de 1, o movimento fica lento sem ganho visual.

Com ζ = 0,8 e deslocamento de 8 px, a ultrapassagem é de 0,12 px, praticamente invisível. Se o grupo quiser um "pulinho" perceptível no cartão, a escolha é ζ entre 0,4 e 0,6, ou um destino maior.

## 7. Orçamento, privacidade e quotas

**[P]** O navegador controla o orçamento da simulação, o comportamento em segundo plano, a preferência de movimento e a intensidade máxima. A página não recebe medições detalhadas do hardware.

- Quota de canais **vinculados** por página (candidato: 256), reservada na ligação; somente canais acordados consomem integração. Teto de passos por quadro: candidato de 8. Assim, acordar vários canais não cria uma alocação sem limite. **[N, revisada]**
- Canais em repouso não consomem passos.
- Parâmetros fora das faixas são rejeitados na ligação, nunca limitados em silêncio.
- O SSC não pode ler nem escrever o estado da aplicação, e o programa da página não lê `presentation.*`.
- Destino representável e válido para o compositor, mas fora do perfil físico, pode ser aplicado diretamente com `S401`. Destino não representável ou inválido mantém a última apresentação válida, em vez de encaminhar um número inválido ao desenho. Overflow no passo gera diagnóstico e fallback seguro. Quotas e isolamento são requisitos para limitar falhas, não prova de que uma interface nunca pode travar.

## 8. Diagnósticos

**[N]** Família `S`, no mesmo espírito do FS e do HTDL: `S1xx` sintaxe, `S2xx` argumentos e tipos, `S3xx` vínculos, `S4xx` execução.

| Código | Situação | Mensagem sugerida |
| --- | --- | --- |
| `S101` | Construção inesperada | `S101: esperado ')' depois de 'dampingRatio: 0.8'` |
| `S201` | Argumento ausente, repetido ou desconhecido | `S201: 'spring' exige 'target', 'frequency' e 'dampingRatio'` |
| `S202` | Valor fora da faixa | `S202: frequency 12Hz fora de 0.5Hz a 10Hz` |
| `S203` | Canal de saída diferente do destino lido | `S203: 'fs.target.offsetX' não pode alimentar 'presentation.offsetY'` |
| `S204` | Tipo errado | `S204: 'frequency' espera Hz, recebeu px` |
| `S301` | Duas origens para a mesma propriedade de `presentation` | `S301: 'presentation.offsetY' em .card tem duas origens: CardMotion e BounceMotion` |
| `S302` | Destino sem produtor FS | `S302: nenhum fluxo FS produz 'target.offsetY' em .card` |
| `S303` | `bind` sem correspondência (aviso) | `S303: '.cardd' não corresponde a nenhum nó` |
| `S401` | Domínio/aritmética em execução | `S401: destino válido de 5000px excede o perfil físico; aplicado direto` |
| `S402` | Coeficientes não conformes | `S402: coeficientes não correspondem ao perfil canônico` |
| `S403` | Quota excedida | `S403: limite de canais da página excedido` |

## 9. Exemplos

### 9.1 O movimento do cartão (o exemplo do grupo)

Igual a [`card.sscr`](../exemplos/fluxstyle/card.sscr):

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

### 9.2 Dois canais com parâmetros diferentes

```text
motion PanelMotion {
    spring(target: fs.target.offsetX, frequency: 3Hz, dampingRatio: 0.9) -> presentation.offsetX;
    spring(target: fs.target.offsetY, frequency: 4Hz, dampingRatio: 0.6) -> presentation.offsetY;
}

bind .panel to PanelMotion;
```

### 9.3 Erros que o verificador deve pegar

```text
motion Broken {
    spring(target: fs.target.offsetX, frequency: 12Hz, dampingRatio: 0.8)
        -> presentation.offsetY;   // S202: frequency out of range; S203: channel mismatch
}

motion Other {
    spring(target: fs.target.offsetY, frequency: 4Hz, dampingRatio: 0.8)
        -> presentation.offsetY;
}

bind .box to Broken;
bind .box to Other;   // S301: two producers for presentation.offsetY on .box
```

## 10. Reservado para depois

- **Nível B (mundos delimitados).** Uma região da página vira uma pequena cena com corpos, gravidade, atrito e juntas, com limites de corpos, trabalho por passo e energia. Texto e formulários fora dela mantêm layout estável. Ver a exploração no documento 07.
- **Nível C (layout por forças).** Só como modo experimental de uma região, com configuração estática de recuperação.
- **[R — A11] Eventos.** Adiar para depois do núcleo. Um evento futuro de repouso precisa ampliar o catálogo versionado do HTDL, disparar uma vez por episódio e respeitar quotas. A lógica da aplicação não deve depender da conclusão da animação.
- **Presets.** Para autoria comum, nomes como "suave" ou "firme" podem ser mais claros do que `frequency` e `dampingRatio`. **[P]**
- **Mais canais.** Escala, rotação e opacidade.
- **BG++**, o dialeto cultural do documento 07, continua como opção do projeto.

## 11. Respostas da revisão às questões do SSC

| Questão | Recomendação | Decidir até |
| --- | --- | --- |
| Nome por extenso | SanSCript, conforme mensagem original (A05) | Resolvida pela origem |
| Extensão | `.sscr` recomendada; não associar `.ssc`/`.fs.ssc` por padrão (A04) | Recomendação do rascunho |
| Faixas numéricas | Perfil experimental, sem garantia universal de precisão (A10/N15) | MS |
| Estabilização por foco | Congelar deslocamento atual durante foco/edição; testar com IME (A09) | MS |
| Repouso e orçamento | Limiares candidatos e descarte real do excesso, medidos em prova (A10/N12) | MS |
| Parâmetros reativos | Adiados; literais na 0.1 (N10) | Depois da 0.1 |
| Eventos de repouso | Adiados e versionados, sem condicionar a lógica à animação (A11) | Depois da 0.1 |
| Presets | Adiados até validar o núcleo numérico | Depois da 0.1 |

Os IDs remetem ao [parecer completo](13-revisao-extensoes-abertos-e-propostas.md).

Origem das propostas: documentos [07](07-propostas-visuais-e-ssc.md) e [09](09-fluxstyle-e-fluxo.md), exemplo [`card.sscr`](../exemplos/fluxstyle/card.sscr), [referência do FS](10-fluxstyle-referencia.md) e o [contrato FS ↔ SSC](12-contrato-fs-ssc-e-assisscript.md).

# Contrato FS ↔ SSC e o papel do AssisScript

**Ampliação de 27/10/2026:** os documentos [14](14-fundamentos-e-perfis.md) a [19](19-conformidade-e-cenarios.md) aprofundam este contrato como proposta. A tabela de capacidades do AssisScript abaixo pertence a snapshots anteriores, sem inspeção atual durante seu teste de 24 horas. C10 passa a ser lida com o protocolo de fallback semântico do documento 17.

Estado: rascunho de contrato, 25/10/2026. Define como o [FluxStyle](10-fluxstyle-referencia.md) e o [SSC](11-ssc-referencia.md) trabalham juntos e onde o AssisScript entra. **Nada aqui está implementado**: não existe compilador FS, compilador SSC nem a API de navegador do AssisScript. As marcas **[G]**, **[P]**, **[N]** e **[A]** têm o sentido definido na referência do FS.

O texto original usava a documentação da **3.3.0-alpha.2**. A leitura local de 25/10 encontrou **3.3.0-alpha.5**, com funções como valores, callbacks sem captura e classes genéricas já documentados; durante os testes o compilador já informou **alpha.6**. A tabela distingue esse snapshot das provas efetivamente executadas. Respostas [A] e pareceres [N] estão no [relatório de revisão](13-revisao-extensoes-abertos-e-propostas.md).

## 1. O contrato em uma tabela

| Camada | Responde | Escreve | Lê |
| --- | --- | --- | --- |
| HTDL | O que existe e qual é o significado? | A árvore semântica | — |
| AssisScript (página) | O que acontece na aplicação? | Estado e mutações de conteúdo/semântica permitidas pela API HTDL | Eventos e estado do próprio programa |
| FluxStyle | Qual apresentação cada nó deve ter? | `layout.*`, `paint.*`, `text.*`, `target.*` | `state.*`, `env.*`, `self.*`, `parent.availableWidth` |
| SSC | Como a apresentação chega lá? | `presentation.*` | `fs.target.*` |
| Motor | Qual é a geometria final? | `geometry.*` (leitura apenas) | Tudo o que foi confirmado |

**[N]** A regra que sustenta o contrato é de **propriedade por espaço de nomes**: cada espaço de nomes tem um único dono, e só o dono escreve. Isso é a regra "uma origem por propriedade" do FS, estendida às fronteiras entre linguagens.

| Espaço de nomes | Dono | Quem pode ler |
| --- | --- | --- |
| `state.*` | AssisScript da página | AssisScript e FS (como `input`) |
| `env.*` | Navegador | FS |
| `self.*`, `parent.*` | Motor (estado do nó, restrição de layout) | FS |
| `layout.*`, `paint.*`, `text.*` | FS | Motor |
| `target.*` | FS | SSC (como `fs.target.*`), motor |
| `presentation.*` | SSC | Motor |
| `geometry.*` | Motor | Ninguém, nesta versão (nem FS, nem SSC, nem a página) |

Como `target.*` e `presentation.*` são espaços diferentes, os escritores válidos FS e SSC não disputam a mesma propriedade. O programa da página mantém suas APIs para texto, foco, hidden e disabled; isso não lhe concede escrita direta em `paint.*`, `layout.*` ou `presentation.*`.

## 2. A linha do tempo de uma mudança

```mermaid
sequenceDiagram
    participant U as Usuário
    participant M as Motor
    participant A as AssisScript (página)
    participant F as FluxStyle
    participant L as Layout
    participant S as SSC
    participant R as Composição
    U->>M: clique em "Expandir ou recolher"
    M->>A: alternar(alvo, evento)
    A->>M: htdl_estado_int_definir("card.expanded", 1)
    Note over M: a tarefa termina; as mudanças são consolidadas
    M->>F: transação v(n+1) com as entradas alteradas
    F->>F: avalia o grafo em ordem topológica
    F-->>L: layout, paint, text (confirmação atômica)
    F-->>S: target.offsetY = -8px (mesma versão)
    L->>R: geometria de layout
    loop passos fixos de 1/120 s
        S->>S: avança a mola
        S-->>R: presentation.offsetY
    end
    R->>U: desenho, acerto de ponteiro e árvore acessível usam a mesma geometria
```

| Fase | Quem executa | Entrada | Saída |
| --- | --- | --- | --- |
| 1. Eventos | AssisScript, uma função por vez | Evento do usuário | Mudanças de estado, aplicadas em ordem |
| 2. Transação FS | FluxStyle | Estado, ambiente, estados de nó, restrições de layout | Uma versão completa de `layout`, `paint`, `text` e `target`, ou nenhuma |
| 3. Layout | Motor | `layout.*`, `text.*`, medição de texto | Caixas de layout, sem deslocamento de apresentação |
| 4. Física | SSC | `fs.target.*` da versão confirmada | `presentation.*`, passo a passo |
| 5. Composição | Motor | Layout mais `presentation` | Lista de desenho, regiões de acerto, limites acessíveis |

A ordem é um fluxo de mão única. O resultado de uma fase não alimenta uma fase anterior **no mesmo quadro**.

## 3. Cláusulas do contrato

**[N]** Cada cláusula é numerada para ser citada em testes e diagnósticos.

**C1. Propriedade.** Cada espaço de nomes tem um único dono (seção 1). Escrever em um espaço de outro é erro de validação.

**C2. Destino.** `target.*` só é produzido pelo FS e é confirmado na **mesma versão** de `layout.*`, `paint.*` e `text.*`. Tem tipo `length`, valor padrão `0px` e é medido em relação à caixa de layout, sem alterar o tipo HTDL nem a semântica do nó. **[P]**

**C3. Mão única.** Os dados fluem FS → SSC → composição. O FS 0.1 não lê `presentation.*` nem `geometry.*`. O SSC não devolve o resultado parcial da mola ao FS no mesmo quadro. Essa realimentação precisaria de um contrato temporal próprio e está fora do núcleo. **[P]**

**C4. Atomicidade, corrigida.** Antes de desenhar a versão nova, o motor publica layout, pintura e destinos juntos e sincroniza o estado do SSC com esses destinos, preservando o deslocamento de apresentação quando aplicável. A integração ocorre no tick seguinte. Sob quotas, carga ou suspensão não há garantia universal de latência real de 1/120 s. Esse é o passo de simulação, não um SLA de tempo de parede. **[N, revisada]**

**C5. Continuidade, corrigida.** Retargeting conserva deslocamento de apresentação e velocidade. Isso conserva posição de tela se a caixa de layout permanecer fixa; mudança da própria caixa pode mover o nó. Preservação absoluta de pixels durante reflow exigiria outro contrato. **[P, revisada]**

**C6. Primeira apresentação.** Quando um nó passa a ter um `motion`, a apresentação começa no destino, sem animar. **[N]**

**C7. Sem SSC.** Se nenhum `motion` está vinculado ao nó, o compositor aplica `target.*` diretamente. Uma página sem SSC continua válida. **[P]**

**C8. Movimento reduzido.** Com `env.reducedMotion`, o SSC aplica o destino direto, sem passos. A geometria final é a mesma da animação, e nenhuma ação depende de o movimento ter ocorrido. **[P]**

**C9. Geometria única.** Desenho, acerto de ponteiro e limites acessíveis usam a mesma geometria consolidada (layout mais `presentation`). A ordem semântica e a ordem de foco não mudam com o movimento. **[P]**

**C10. Falhas, corrigida.** Um erro FS conserva as últimas saídas autorais válidas, aplicadas à árvore semântica atual: nós removidos deixam a composição e novos usam padrões. Não há rollback automático das mutações lógicas/semânticas já concluídas pelo programa; controles desabilitados/ocultos continuam respeitados. SSC usa fallback direto apenas para destino válido e representável; caso contrário, mantém a última apresentação válida e diagnostica. A resistência a travamentos exige quotas, cancelamento e isolamento, não decorre apenas de declarar um DSL puro. O [protocolo 17](17-execucao-transacoes-e-layout.md) detalha snapshots e falhas do motor. **[N/R, revisada em 27/10]**

**C11. Privacidade.** O programa da página não lê `presentation.*`, `geometry.*` nem tempos de simulação. A API de páginas evita expor coordenadas **[P]**. O navegador controla o orçamento da simulação e a preferência de movimento. Nenhuma entrada de `env.*` enumera fontes, temas ou hardware.

**C12. Versão.** O contrato tem versão própria (0.1). Mudar a tabela de espaços de nomes, a ordem das fases ou a semântica de uma cláusula exige nova versão do contrato, mesmo que a gramática de FS e SSC não mude.

## 4. Exemplo completo: o cartão expansível

Os quatro arquivos completos estão em [exemplos/fluxstyle](../exemplos/fluxstyle/README.md). O carregamento agora é uma **proposta HTDL 0.2**, com arquivos `.fxs` e `.sscr`; não cabe implicitamente na 0.1. O exemplo ainda não é executável em navegador. A verificação de AssisScript usa somente assinaturas substitutas da API futura.

**`index.htdl`**

```htdl
<div type="document" version="0.2" lang="en">
  <div type="head">
    <div type="title">Expandable card</div>
    <div type="presentation" src="./card.fxs" language="fluxstyle"></div>
    <div type="presentation" src="./card.sscr" language="ssc"></div>
    <div type="script" src="./app.assis" format="source"></div>
  </div>
  <div type="body">
    <div type="main">
      <div type="heading" level="1">Expandable card</div>
      <div type="button" id="toggleCard" on:click="toggleCard">Expand or collapse</div>
      <div type="section" class="card" a11y-label="Card details">
        <div type="paragraph">This card changes width, color and presentation offset.</div>
      </div>
    </div>
  </div>
</div>
```

**`app.assis`** (verificação de tipos com assinaturas substitutas; a API real `htdl_*` ainda é a proposta do documento 03)

```assis
#yuri <browser/htdl.assis>

assis assis_assis(): int {
    return htdl_estado_int_definir("card.expanded", 0);
}

assis toggleCard(target: int, event: int): void {
    val current: int = htdl_estado_int("card.expanded");
    if (current == 0) {
        assert(htdl_estado_int_definir("card.expanded", 1) == 0);
    } else {
        assert(htdl_estado_int_definir("card.expanded", 0) == 0);
    }
}
```

O programa só mexe em **estado**. Não escolhe cor, largura nem posição: isso é do FS. Não sabe que existe uma mola.

**`card.fxs`** e **`card.sscr`**: [`fluxo`](../exemplos/fluxstyle/card.fxs) e [`movimento`](../exemplos/fluxstyle/card.sscr), respectivamente. `.flux` também é válido para FluxStyle.

### O que acontece quando o botão é ativado

1. O AssisScript grava `card.expanded = 1`. A tarefa termina.
2. O FS avalia uma única transação. Se a largura disponível é de pelo menos 640 px: `layout.width` passa de 320 px para 640 px, `paint.background` passa de `#252936` para `#7454d8` e `target.offsetY` passa de `0px` para `-8px`. As três mudanças são confirmadas **juntas**.
3. O motor faz layout com a nova largura e pinta a nova cor. A largura e a cor mudam **de uma vez**: só o deslocamento é animado.
4. O SSC anima `presentation.offsetY` de 0 px até −8 px.

Trajetória de `presentation.offsetY` (emulação do algoritmo de referência: 4 Hz, ζ = 0,8, destino de 0 para −8 px no passo 0; reproduzível com [`spring_reference.py`](../exemplos/fluxstyle/spring_reference.py)):

| Passo | Tempo | `presentation.offsetY` |
| --- | --- | --- |
| 1 | 8 ms | −0,157 px |
| 2 | 17 ms | −0,561 px |
| 3 | 25 ms | −1,126 px |
| 4 | 33 ms | −1,785 px |
| 6 | 50 ms | −3,196 px |
| 9 | 75 ms | −5,112 px |
| 11 | 92 ms | −6,107 px |
| 16 | 133 ms | −7,574 px |
| 21 | 175 ms | −8,057 px |
| 26 | 217 ms | −8,119 px |
| 31 | 258 ms | −8,073 px |
| 41 | 342 ms | −8,000 px (repouso) |

O ponto mais baixo é −8,122 px (passo 25), uma ultrapassagem de 0,122 px. Se o botão for ativado de novo no passo 11, o destino volta a 0 px, a posição de tela não salta, o ponto de inversão é −5,950 px e o repouso em 0 px chega no passo 51 (425 ms). Com `env.reducedMotion` verdadeiro, a trajetória inteira é substituída por um único valor: −8 px, imediatamente.

## 5. O AssisScript no ecossistema

### 5.1 Papel 1: o programa da página (perfil restrito)

**[G]** O AssisScript cuida de lógica e estado. Para apresentação, ele modifica entradas de estado em vez de escrever estilo, destinos ou física diretamente. **Também continua alterando conteúdo e estado semântico por APIs autorizadas do documento**, conforme o documento 03; o texto anterior “só escreve estado” era uma restrição excessiva que eliminaria esse papel.

A ponte já proposta no documento 03 é a API de estado: `htdl_estado_int(chave)` e `htdl_estado_int_definir(chave, valor)`, ambas com `int`. O FS lê essas chaves como `input`. Efeitos práticos:

- `bool` no FS é `int` 0 ou 1 no AssisScript. Números fracionários ainda não passam por essa ponte.
- **[R — A02]** O escopo padrão é página. O rascunho admite `state("expanded", false, scope: node)` e propõe `htdl_estado_no_int(no: int, chave: text): int` / `htdl_estado_no_int_definir(no: int, chave: text, valor: int): int`. O handle valida instância e geração; remoção destrói o estado. Essas APIs não estão implementadas.
- Troca de aparência por interação (foco, ponteiro, pressionado, desabilitado) **não** passa pelo AssisScript: vem de `self.*`.

### 5.2 Papel 2: o motor e o navegador (perfil confiável)

**[G]** O navegador deve ser escrito em AssisScript. O avaliador do FS, o integrador do SSC e o layout serão bibliotecas da linguagem. O quadro abaixo usa o snapshot local 3.3.0-alpha.5.

| Necessidade | O que a versão oferece | Avaliação |
| --- | --- | --- |
| Aritmética fracionária (FS, layout, SSC) | `int` de 64 bits com estouro modular; sem `float`. `f64` e `f32` estão previstos na fase 3 do plano, sem data | **Contornável.** O contrato usa Q16.16 sobre `int` (referência do FS, seção 4) |
| Núcleo numérico verificável | `pure assis` (só `int`, `byte` e `bool`, sem efeitos) e `val` | **Adequado** para `fx_mul` e para o passo da mola |
| Detectar estouro | Operações nativas têm overflow modular; resultados recuperáveis existem em bibliotecas | **Verificações necessárias.** Destinos limitados não provam limites de velocidade, produtos e somas; validar operações antes de executar o kernel puro |
| Estruturas (grafo FS, tabela de nós) | `struct`, `class`, `Array<T>`, `HashMap<K, V>` e funções e structs genéricas (`nome::<T>()`) | **Adequado.** `private` protege invariantes |
| Avaliador de expressões | Funções como valores e callbacks sem captura já existem; closures e variantes/pattern matching não foram demonstrados neste snapshot | **Viável.** AST tipada ou bytecode continua adequado; F1 não é mais um bloqueio pendente |
| Lexer e parser dos arquivos FS e SSC | `text` UTF-8 imutável, `len`, indexação por byte, `Texto` em `std/texto` | **Adequado.** Erros com posição via `ResultadoInt.posicao` |
| Tempo | `agora(): int` devolve milissegundos monotônicos | **Suficiente para a prova**, usando resto de tempo e descarte explícito de passos; sem alegar latência universal |
| Isolamento de páginas | Sem perfil restrito e sem `unsafe`; ponteiros brutos continuam permitidos | **Não bloqueia FS e SSC**, que são declarativos. Bloqueia scripts de página não confiáveis |
| Segurança de memória no motor | Encapsulamento nominal (`private`); `own` e `borrow` locais; sem análise completa de vidas | O código dos módulos FS e SSC deve evitar ponteiros brutos |

O interpretador de FS/SSC não precisa compilar cada arquivo como programa nativo AssisScript. Entretanto, seus parsers, grafos e aritmética processam conteúdo não confiável: precisam de quotas, validação e isolamento do processo de conteúdo. Pureza não prova segurança de memória nem resistência a esgotamento de recursos. O ambiente restrito dos programas de página continua sendo outra fronteira necessária.

#### Esboço do núcleo numérico

O [kernel numérico](../exemplos/fluxstyle/spring_kernel.assis) permite verificar separadamente as funções puras e o traço do cartão com o compilador nativo. Isso não valida o parser FS/SSC ou a API do navegador. Cada próximo estado deve ser calculado a partir do mesmo par antigo `(x,v)`.

```assis
// Fixed16 product; nearest with ties toward positive infinity.
// The caller must check the product AND rounding bias before this operation.
pure assis fx_mul(a: int, b: int): int {
    return (a * b + 32768) >> 16;
}

// Both results must use the same previous x and v.
pure assis spring_next_x(m11: int, m12: int, x: int, v: int): int {
    return fx_mul(m11, x) + fx_mul(m12, v);
}

pure assis spring_next_v(m21: int, m22: int, x: int, v: int): int {
    return fx_mul(m21, x) + fx_mul(m22, v);
}
```

O compilador rejeita efeitos nessas funções (inclusive em ramos mortos) e a aritmética é a mesma em Windows e Linux. O laço de passos usa `agora()` fora das funções puras.

### 5.3 Papel 3 (opcional): compilar FS e SSC para AssisScript

**[R — A13]** Começar por AST tipada/bytecode limitado em avaliador AssisScript. Depois medir compilação antecipada para a interface confiável do navegador, sem ampliar permissões. O ganho não está demonstrado, e nem toda tarefa de layout/pintura pertence ao subconjunto `pure`; o kernel puro é uma parte do motor.

### 5.4 O que FS e SSC pedem ao projeto AssisScript

Estes pontos pertencem ao projeto AssisScript, que decide o que fazer. Estão aqui porque travam ou facilitam a prova de FS e SSC.

1. **Modelo numérico.** Decidir entre `f64`, uma biblioteca `std/fixo.assis` em Q16.16 ou ambos. Nada neste contrato impede `f64`; a semântica de referência continua sendo a inteira.
2. **API de estado tipada e por nó** (seção 5.1).
3. **Funções como valores já estão disponíveis no snapshot lido.** Closures e variantes/pattern matching continuam frentes a avaliar, não pré-requisitos para a primeira AST ou bytecode.
4. **Perfil restrito de navegador.** Já previsto no plano. Necessário para scripts de página, não para FS e SSC.
5. **Traços de referência.** O script de emulação gera trajetórias que podem virar casos de teste do AssisScript, nos dois sistemas, com e sem otimização.

### 5.5 E o UmaScript?

Ele não aparece nos documentos porque ainda é uma opção cogitada. O contrato foi desenhado de modo que isso **não importe para FS e SSC**: a única ponte entre a linguagem de script e a apresentação é o **estado tipado**. Se o UmaScript for adotado como alternativa, só precisa oferecer a mesma API de estado ao navegador. FluxStyle e SSC não mudam.

## 6. Provas recomendadas

**[P]** A próxima prova do documento 09 é: um nó HTDL, um fluxo FS, uma entrada booleana e um canal SSC. Esta lista a detalha.

| Prova | O que verificar | Resultado esperado |
| --- | --- | --- |
| T1 Atualização consistente | Alternar `card.expanded` | Largura, cor e destino confirmados na mesma versão; nenhuma observação mistura valores de versões diferentes |
| T2 Conflito de produtores | Dois fluxos produzem `paint.background` no mesmo nó | `F302` com as duas origens; configuração anterior mantida |
| T3 Ciclo | `let a = b + 1px;` e `let b = a - 1px;` | `F301` com o caminho |
| T4 Unidade | `color` alimentando `layout.width` | `F201` |
| T5 Troca de destino em movimento | Inverter o destino no passo 11 | Sem salto de posição; inversão em −5,950 px; repouso no passo 51 |
| T6 Movimento reduzido | `env.reducedMotion` verdadeiro | Posição final no primeiro quadro, nenhum passo agendado |
| T7 Primeira apresentação | Abrir a página com `expanded` verdadeiro | Nenhuma animação |
| T8 Falha na transação | Erro `F401` injetado em um fluxo | Nenhuma saída autoral nova é publicada; todas conservam a configuração anterior, aplicada à semântica atual |
| T9 Repouso e conformidade | Trajetória 4 Hz, ζ = 0,8 | Repouso no passo 41 e inteiros canônicos correspondentes; não extrapolar a tolerância de um cenário para todo o domínio |
| T10 Acessibilidade | Foco por teclado, controle desabilitado e escala de 200% | Indicador de foco presente, estado desabilitado correto e texto legível (critérios do documento 04) |

Execute T1 a T10 com e sem otimização, em Windows e Linux. Com aritmética inteira, as trajetórias devem ser **idênticas bit a bit** entre os dois.

## 7. Versionamento

Versões que precisam ser registradas **separadamente** (extensão da regra do documento 05, que já separa quatro):

1. Gramática HTDL (0.1 atual; 0.2 proposta para recursos de apresentação).
2. Linguagem FS (0.1).
3. Linguagem SSC (0.1).
4. Contrato FS ↔ SSC (0.1).
5. API do navegador, namespace `htdl_v1`.
6. Compilador AssisScript e perfil de execução.

Uma atualização do compilador não altera a marcação nem a apresentação. Uma mudança incompatível de API ou de contrato deve ser detectada pelo carregador, com mensagem útil.

## 8. Respostas consolidadas às questões abertas

| # | Questão | Recomendação | Onde | Decidir até |
| --- | --- | --- | --- | --- |
| 1 | Modelo numérico | Perfil experimental com checagens e vetores; rejeitar garantias globais não provadas | A01/N03/N15 | Antes de congelar M6 |
| 2 | Estado por instância | `scope: node`, handle com geração e liberação junto do nó | A02 | M6 |
| 3 | Carregamento | `type="presentation"`, `src`, `language`, em HTDL 0.2 | A03 | M6 |
| 4 | Extensões | `.fxs` preferida, `.flux` válida; `.sscr` recomendada | A04 | FS resolvida; SSC recomendada |
| 5 | Nome SSC | SanSCript, conforme mensagem original | A05 | Resolvida pela origem |
| 6 | Preferências | Após autor, antes de medição/layout; escala uma vez | A06 | M6 |
| 7 | Seletores ampliados | Adiados, sem prioridade implícita | A07 | Depois da 0.1 |
| 8 | Fluxos parametrizados | Adiados; composição simples na 0.1 | A08 | Depois da 0.1 |
| 9 | Foco | Congelar deslocamento atual, retomar ao liberar | A09 | Testar em MS |
| 10 | Faixas e repouso | Candidatos mensuráveis; sem extrapolação do cartão | A10 | MS |
| 11 | Eventos SSC | Adiados, discretos e versionados | A11 | Depois da 0.1 |
| 12 | Layout padrão/unidades | `block()` agora; `em` depois | A12 | M6/depois do núcleo |
| 13 | Execução | AST tipada/bytecode limitado primeiro | A13 | Antes de avaliar AOT |

Detalhes e custo de memória por nó (A14) estão no [parecer A/N](13-revisao-extensoes-abertos-e-propostas.md).

## 9. O que foi e não foi verificado

- **Emulação reproduzida:** cartão com repouso nos passos 41/51; grade amostrada de 42 pares, com erro máximo de aproximadamente 0,0213 px nos primeiros 3 s para degrau de 8 px. A auditoria rejeitou a tolerância universal de coeficientes, encontrando 17,90625 px de desvio em outro cenário válido do perfil proposto.
- **AssisScript verificado em alpha.6:** kernel puro executou com e sem otimização, produzindo `SSC numerical kernel: 41`. O aplicativo do cartão passou na checagem com assinaturas substitutas da API. [Relatório nativo](revisao-2026-10-25-assisscript.json).
- **Ainda não verificado:** parser/compilador FS e SSC, API real de navegador, geometria/renderização, comportamento de foco/IME e conformidade numérica de todo o domínio.
- **Decisões explícitas do grupo:** HTDL com divs, navegador e programas em AssisScript, FS dinâmico por fluxo, parceria SSC, exemplos FS/SSC em inglês e extensões FS `.fxs`/`.flux`. Regras formais e `.sscr` são recomendações revisadas, não aprovações inventadas.
- **Propostas [N]:** receberam os pareceres N01–N21 no documento 13, com correções incorporadas; ratificação e implementação continuam etapas distintas.

Fontes consultadas: documentos [01](01-ecossistema.md) a [09](09-fluxstyle-e-fluxo.md) e [VALIDACAO](VALIDACAO.md) do projeto, exemplos de `exemplos/fluxstyle` e `exemplos/contador`, e a documentação do AssisScript 3.3.0-alpha.2 (`LINGUAGEM`, `GENERICS`, `PROGRAMACAO-FUNCIONAL`, `CONTRATOS-E-SEGURANCA`, `BIBLIOTECA-erros`, `BIBLIOTECA-matematica`, `MELHORIAS-3.2`, `PLANO-EVOLUCAO-E-HANDOFF`, `HANDOFF-3.3-ALPHA.2` e `VALIDACAO-3.3-ALPHA.2`).

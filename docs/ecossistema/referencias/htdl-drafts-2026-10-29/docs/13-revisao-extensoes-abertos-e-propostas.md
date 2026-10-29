# Revisão das extensões, questões [A] e propostas [N]

Revisão técnica de 25/10/2026 dos documentos 10, 11 e 12 e de `spring_reference.py`. **Não é implementação de FS, SSC ou do navegador.** `[G]` abaixo é decisão explícita do autor; `[R]` é recomendação desta revisão para o rascunho, sem atribuir ao grupo uma aprovação que ele não deu.

## 1. Extensões e identidade

| Linguagem | Extensão | Situação |
| --- | --- | --- |
| FluxStyle | **`.fxs`** | **[G] Preferida**, usada pelos exemplos e futuros geradores |
| FluxStyle | `.flux` | **[G] Alternativa válida**, mesma gramática e semântica |
| SSC — SanSCript | **`.sscr`** | **[R] Recomendada**, adotada nos exemplos do rascunho |
| SSC | `.ssc`, `.fs.ssc` | **[R] Não registrar como extensões padrão do ecossistema** |

Manter `Card.fxs` e `Card.sscr`, com o mesmo nome-base quando forem pares, já comunica a identidade conjunta sem acoplar suas extensões. Um arquivo SSC pode atender vários fluxos; não existe casamento automático por nome-base.

`.ssc` tem usos reais, por exemplo os [scripts do Stellarium](https://stellarium.org/doc/26.0/scripting.html) e [catálogos do Celestia](https://github.com/CelestiaProject/Celestia). `.fs.ssc` pode receber um glob específico em um editor, mas sua extensão final continua `.ssc` para ferramentas que usam o último ponto; acrescentar `.fs` não elimina essa ambiguidade. [Extração de extensão, Microsoft](https://learn.microsoft.com/en-us/dotnet/api/system.io.path.getextension).

`.sscr` é uma escolha de organização, não uma garantia de exclusividade mundial. `.flux` também é usada pela [linguagem Flux da InfluxData](https://github.com/influxdata/flux/blob/master/docs/SPEC.md); isso reforça `.fxs` como preferência sem revogar a alternativa escolhida pelo grupo.

O futuro suporte de editor deve usar IDs de linguagem `fluxstyle` e `sanscript`, com associações a `.fxs`/`.flux` e `.sscr`, respectivamente. Não alterar as associações do sistema ou de outros projetos automaticamente. [Identificadores de linguagem no VS Code](https://code.visualstudio.com/docs/languages/identifiers).

O nome por extenso fica **SanSCript**, grafia usada pelo autor na mensagem original. `SansSCript`, que apareceu na referência nova, não é uma mudança confirmada de nome. A sigla continua SSC; a extensão não exige renomear a linguagem.

## 2. Respostas a todas as questões [A]

| ID | Questão e origem | Resposta da revisão |
| --- | --- | --- |
| A01 | Modelo numérico — FS §4/13, contrato §8.1 | Usar um **perfil experimental de referência com 16 bits fracionários e intermediários `int64`**. Explicitar limites e arredondamentos. A validação do cartão não torna esse perfil um contrato numérico geral ratificado; corrigir as garantias universais antes de congelar a conformidade. |
| A02 | Estado por nó — FS §6, contrato §5.1/8.2 | Aceitar `state("expanded", false, scope: node)` no rascunho, com API correspondente por handle. O escopo padrão continua página. A identidade inclui instância do documento, nó e geração; remoção destrói o estado. |
| A03 | Carregamento HTDL — FS §3/13, contrato §8.3 | Propor HTDL **0.2** com `type="presentation"`, `src` e `language="fluxstyle"` ou `language="ssc"`. A 0.1 permanece igual. Carregar todos os recursos, validar os vínculos e ativar o conjunto como unidade. |
| A04 | Extensões — FS §3/13, SSC §11, contrato §8.4 | `.fxs` preferida e `.flux` válida por decisão do autor; `.sscr` recomendada para SSC. Não adotar `.fs` nem `.fs.ssc`. |
| A05 | Nome SSC — SSC abertura/§11, contrato §8.5 | Manter **SanSCript**, conforme a mensagem original do autor. |
| A06 | Preferências/acessibilidade — FS §8/13, contrato §8.6 | Política do navegador **após valores autorais e antes de medição/layout**; conservar valor autoral e efetivo no inspetor. Escala de texto aplicada uma vez sobre a base, nunca acumulada em cada transação. Movimento reduzido limita SSC antes de simular. |
| A07 | Seletores por tipo/compostos — FS §8/13, contrato §8.7 | Adiar para depois da FS 0.1. O núcleo tem IDs e classes. Futuros seletores apenas selecionam nós, sem introduzir especificidade para resolver produtores concorrentes. |
| A08 | Fluxos parametrizados — FS §8/13, contrato §8.8 | Adiar sintaxe parametrizada para depois do núcleo 0.1. Usar `choose`, fluxo único ou produtores disjuntos agora. Parametrização futura mantém a regra de produtor único. |
| A09 | Foco e edição — SSC §5.7/11, contrato §8.9 | **Congelar o deslocamento de apresentação atual**, zerando a velocidade enquanto houver foco por teclado ou edição no nó/subárvore. Guardar o destino novo sem persegui-lo; ao liberar o foco, retomar da posição preservada. Evita fazer o controle correr até o destino ao receber foco. É proposta a testar com teclado/IME. |
| A10 | Faixas, repouso e quotas — SSC §4/5.5/7/11, contrato §8.10 | Manter faixas como **perfil de teste**, não garantia de precisão universal. Limiares de 3 passos, quota de 256 canais e teto de 8 passos são candidatos mensuráveis. A aritmética deve conferir produtos, somas e mudança de destino. |
| A11 | Eventos SSC — SSC §10/11, contrato §8.11 | Adiar para versão posterior. Ação da aplicação não espera a mola terminar. Evento futuro será discreto e limitado, uma vez por episódio, nunca por frame; o catálogo `on:` precisa ser versionado. |
| A12 | `block()` e unidades relativas — FS §13, contrato §8.12 | Manter `block()` no núcleo. Adiar `em` e referências a fontes até existir contrato de medição e ciclos; `px` lógico basta para a prova. |
| A13 | Interpretar ou compilar — contrato §5.3/8.13 | Começar por AST tipada/bytecode limitado, em avaliador escrito em AssisScript. Depois medir geração antecipada para a interface confiável do navegador. Compilação não amplia permissões nem dispensa quotas. |
| A14 | Custo do estado por instância — FS §13 | Tabela esparsa por nó, com alocação apenas para chaves usadas, limites por documento e liberação junto do nó. Publicar medições antes de prometer um custo específico. |

Sintaxe de carregamento **proposta para HTDL 0.2**:

```htdl
<div type="head">
  <div type="title">Expandable card</div>
  <div type="presentation" src="./card.fxs" language="fluxstyle"></div>
  <div type="presentation" src="./card.sscr" language="ssc"></div>
  <div type="script" src="./app.assis" format="source"></div>
</div>
```

`language` é independente da extensão: `.fxs` e `.flux` selecionam a mesma linguagem. Um tipo declarado incompatível com o recurso é erro. Não tentar outro arquivo automaticamente se o primeiro não existir. Bindings referem-se a declarações do próprio arquivo no núcleo, sem imports ainda. Identidade do produtor inclui URL canônica do recurso, declaração e nó; repetir o mesmo recurso normalizado é idempotente, carregar outro arquivo não é.

## 3. Validação das propostas [N]

“Aceitar” nesta tabela significa adequado ao rascunho técnico, não funcionalidade implementada ou aprovação definitiva do grupo.

| ID | Grupo de propostas [N] | Parecer e ajuste |
| --- | --- | --- |
| N01 | UTF-8/BOM, comentários aninhados, identificadores, palavras reservadas — FS §3 | **Aceitar.** Acrescentar limites de bytes, tokens e aninhamento. PascalCase/camelCase são convenções, não motivo para rejeitar identificador válido. |
| N02 | `50% = 0.5`, dimensões e `abs` — FS §4/5 | **Aceitar com precisão explícita.** Porcentagem é número sem dimensão; `abs` aceita apenas tipos numéricos/dimensionais e deve detectar estouro. Saídas também validam faixas: largura/preenchimento não negativos, opacidade entre 0 e 1, texto positivo. |
| N03 | Q16.16 e resultados idênticos — FS §4, SSC §6 | **Revisar.** Dezesseis bits fracionários não implicam por si só a faixa de um armazenamento de 64 bits. O limite público de 32 bits é uma restrição do perfil; estado físico pode exigir intermediários mais largos. Identidade bit a bit exige também coeficientes, arredondamentos, entradas e passos idênticos. |
| N04 | Ponte de `state` por `int` — FS §6 | **Aceitar como ponte provisória.** Zero é falso e não zero é verdadeiro. Registrar tipo e padrão por chave/escopo, conferir conflitos e distinguir chave ausente de chave presente com zero. Erro de apresentação não desfaz automaticamente o estado do programa. |
| N05 | `self.*` e `env.*` — FS §6 | **Aceitar catálogo fechado.** `self.checked` exige checkbox; `invalid` vem da validação nativa. `env.textScale` não autoriza reaplicar escala cumulativamente. O catálogo e sua exposição entram na revisão de privacidade. |
| N06 | Binding repetido e aviso sem correspondência — FS §8 | **Aceitar.** Idempotência é por declaração/recurso/nó, não só pelo nome do fluxo. Não gerar um aviso novo a cada frame; alterações da árvore revalidam somente a configuração afetada. |
| N07 | Transação de página inteira e falha — FS §9 | **Aceitar com escopo claro.** Atomicidade de publicação da apresentação pode ter cálculo incremental. Falha conserva a apresentação anterior; mutações lógicas/semânticas já concluídas pelo programa não são revertidas automaticamente. |
| N08 | Códigos `F` e `S` — FS §10, SSC §8 | **Aceitar.** Preservar distinção erro/aviso e intervalos UTF-16. Acrescentar diagnósticos de quota, conflito de padrão de estado e coeficiente não conforme; não substituir causa por mensagem genérica. |
| N09 | Layout adaptável como entrada — FS §11.2 | **Aceitar.** `parent.availableWidth` precisa vir de restrição definida, evitando ciclos entre tamanho usado do pai e do filho. |
| N10 | Gramática SSC, argumentos literais e canais — SSC §2/3 | **Aceitar.** Exigir exatamente `target`, `frequency` e `dampingRatio`, sem repetição; leitura/saída com o mesmo canal; destino FS explícito. Um padrão do motor não conta como produtor FS para `S302`. |
| N11 | Faixas de frequência/amortecimento — SSC §4 | **Aceitar apenas como domínio experimental.** A grade tem 42 pares; não prova todos os valores intermediários nem sequências ilimitadas de retargeting. |
| N12 | Contagem de passos e descarte — SSC §5.2 | **Corrigir.** Subtrair só passos executados de um relógio acumulado faz o trabalho descartado reaparecer. Usar resto inteiro de tempo e contabilizar/desconsiderar o excedente no mesmo frame; reiniciar a base ao sair de segundo plano. |
| N13 | Primeira apresentação, repouso e hidden — SSC §5.4/5.5/5.7 | **Aceitar.** Começar no destino sem animação; três passos consecutivos para dormir; ao voltar de hidden, iniciar no destino. Foco recebe a política A09, que é diferente de hidden. |
| N14 | Matriz analítica e multiplicação inteira — SSC §6 | **Aceitar com verificações.** Calcular `x'` e `v'` a partir do mesmo estado antigo, verificar produtos e somas. A matriz real é exata para um passo; sua versão quantizada é aproximada. |
| N15 | Erro de coeficiente de 1 ULP garante 1/16 px — SSC §6.2/6.3 | **Rejeitar a garantia geral.** A auditoria encontrou desvio de **17,90625 px** em 0,5 Hz, ζ=0,1, degrau de −4096 px e perturbações de apenas ±1 ULP nos coeficientes. Exigir coeficientes canônicos ou validar trajetórias por domínio/cenário. |
| N16 | 256 canais, 8 passos, falha numérica — SSC §7 | **Aceitar como candidatos.** Reservar quota ao ligar os canais; recusar excesso de forma determinística. Destino válido fora do perfil físico pode ser aplicado direto. Valor não representável/não validado não pode atravessar a composição como fallback. |
| N17 | Donos por namespace — contrato §1/C1 | **Aceitar com correção.** FS escreve apresentação desejada e SSC escreve apresentação física. O programa AssisScript também continua alterando conteúdo e estados semânticos pela API HTDL; “só escreve estado” não elimina esse papel já previsto. |
| N18 | C4, latência e atomicidade — contrato §3 | **Corrigir.** Na publicação de uma versão, atualizar os destinos vistos pelo SSC antes de desenhar a versão nova. Integração ocorre depois no tick. 1/120 s é tempo de simulação, não limite universal de latência real sob carga, suspensão ou quotas. |
| N19 | C5 e posição de tela — contrato §3 | **Corrigir.** Retargeting conserva o deslocamento de apresentação e a velocidade; a posição absoluta também depende da caixa de layout. Preservar pixels de tela quando a própria caixa muda exige outra técnica/contrato. |
| N20 | C10, “a interface nunca congela” — contrato §3 | **Reformular como requisito.** Quotas, cancelamento, limites de parser/avaliador e isolamento são necessários; pureza do DSL não prova resistência a travamento ou falha de memória do motor. |
| N21 | Versionamento C12 e protocolo — contrato §3/7 | **Aceitar.** Separar gramáticas HTDL/FS/SSC, contrato, API e compilador; extensão não determina versão. Mudanças incompatíveis do protocolo de publicação exigem revisão do contrato. |

## 4. Correções numéricas e evidência

O [script original](../exemplos/fluxstyle/spring_reference.py) reproduziu o cartão: repouso no passo **41**, mínimo de aproximadamente **−8,1219 px** e, no retargeting do passo 11, repouso no **51**. A grade de 42 pares reproduziu erro máximo de aproximadamente **0,0213 px**, medido nos primeiros 3 segundos contra a solução contínua para um degrau de **8 px**, e repouso mais lento em aproximadamente **15,758 s**.

Esses resultados têm cobertura específica. O script original não verificava todas as alegações sobre produtos máximos, perturbações de coeficientes e todo o domínio. Os limites divulgados não devem ser extrapolados para degraus de milhares de pixels ou qualquer sequência de destinos.

A [auditoria executável](../exemplos/fluxstyle/audit_reference.py) verifica os traços, reproduz o contraexemplo N15, confere os empates de arredondamento e um exemplo de descarte de passos. O [relatório JSON](revisao-2026-10-25-spring.json) guarda os resultados efetivos. É evidência de emulação e de revisão do contrato, não de um motor FS/SSC.

Dois arredondamentos diferentes já existiam no script e agora estão explícitos: conversão de literal/coeficiente usa empate afastando de zero; multiplicação `(a*b + 32768) >> 16` usa empate para +infinito. Assim, −meio ULP vira −1 na conversão e 0 no produto. Não descrevê-los como uma regra de empate única.

Para o perfil de referência: declarar a conversão decimal antes de testar limites; operações de produto usam a regra acima; divisão usa arredondamento ao mais próximo com empate para +infinito, com divisor de sinal normalizado e verificação de zero; somas/subtrações são exatas antes da checagem de faixa. Uma especificação congelada precisará de vetores canônicos para todas essas operações e para geração de coeficientes.

No scheduler de referência, a sequência de deltas 1000, 8 e 1 ms executa 8, 0 e 1 passos; os 112 passos descartados no primeiro frame não reaparecem. O algoritmo acumula `elapsedMs * 120`, extrai quociente/resto por 1000, limita o quociente a 8 e conserva só o resto. A implementação nativa deve limitar/checkar o delta e o produto antes de calcular.

## 5. AssisScript e limites desta revisão

Na inspeção o compilador informou **3.3.0-alpha.5**; durante as provas já informou **3.3.0-alpha.6**, pois o projeto segue em desenvolvimento simultâneo. A documentação local registra funções como valores, callbacks sem captura, funções puras e classes genéricas. A tabela baseada em alpha.2 foi atualizada sem concluir que closures, tipos variantes ou FFI estejam disponíveis.

O [núcleo numérico puro](../exemplos/fluxstyle/spring_kernel.assis) foi executado com e sem otimização e confirmou o repouso no passo 41. O aplicativo do cartão passou na checagem com assinaturas substitutas; a API `browser/htdl.assis` continua proposta. Isso não demonstra integração com navegador. O [relatório nativo](revisao-2026-10-25-assisscript.json) registra versão, resultados e hash do compilador usado.

A avaliação de FS/SSC dentro de um interpretador em AssisScript não exige compilar cada arquivo remoto como programa nativo, mas seu parser e runtime continuam processando conteúdo não confiável. Pureza não substitui limites nem isolamento do processo de conteúdo.

As demais condições a provar — leitor de tela, IME, foco congelado, custo de memória, composição de layout real, cobertura numérica completa e desempenho — permanecem marcos de implementação, não resultados atribuídos a esta revisão.

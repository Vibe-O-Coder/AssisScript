# HTDL 0.1 — rascunho da linguagem

Estado: proposta revisável. As palavras **deve**, **não deve** e **pode** definem o comportamento pretendido para uma implementação futura que declare suporte completo à versão 0.1. Não descrevem funcionalidades já implementadas.

A extensão 0.2 está detalhada em [HTDL 0.2 e carregamento](15-htdl-0.2-e-carregamento.md). Ela não altera retroativamente o catálogo desta versão.

## Documento e sintaxe

- Extensão proposta: `.htdl`; codificação UTF-8 válida, com BOM inicial opcional.
- Único nome de elemento: `div`, com capitalização exata. Fechamento obrigatório `</div>`; a forma `/>` não pertence à versão 0.1.
- Toda abertura deve ter exatamente um atributo `type`, com valor reconhecido.
- Nomes de atributos e valores enumerados são sensíveis a maiúsculas. A ordem dos atributos não altera seu significado.
- Valores com aspas simples, duplas e valores sem aspas são aceitos. Recomenda-se aspas duplas.
- Atributos repetidos, tags diferentes de `div`, fechamento incompleto e conteúdo fora da raiz são erros. Fora da raiz admitem-se apenas espaços e comentários.
- Não há DOCTYPE, instruções XML, CDATA, avaliação de expressões ou inserção implícita de tags.

São equivalentes:

```htdl
<div type=button id=salvar>Salvar</div>
<div id="salvar" type="button">Salvar</div>
```

Gramática estrutural, complementada pelas regras lexicais e semânticas abaixo:

```ebnf
documento = espacamento, elemento, espacamento, EOF ;
elemento = "<div", atributo, { atributo }, espacos_opcionais, ">",
           { elemento | texto | comentario }, "</div>" ;
atributo = espacos, nome, espacos_opcionais, "=", espacos_opcionais, valor ;
valor = texto_entre_aspas_duplas | texto_entre_aspas_simples | valor_simples ;
nome = letra_ascii, { letra_ascii | digito | "-" | ":" | "_" } ;
comentario = "<!--", conteudo_comentario, "-->" ;
espacamento = { espaco | comentario } ;
espacos = espaco, { espaco } ;
espacos_opcionais = { espaco } ;
```

`espaco` é espaço ASCII, tab, CR ou LF. CRLF e CR são normalizados para LF antes de processar texto. `valor_simples` é uma sequência não vazia sem espaços, aspas, acento grave, `=`, `<`, `>`, `&` ou `/`; URLs e caminhos usam aspas. Texto entre aspas permite espaços e `/`, mas exige escape para `<`, `&` e a aspa delimitadora. Um nome iniciado por `div` maior que a palavra exata não inicia um elemento.

Comentários não se aninham e não podem conter `--`. A gramática não autoriza um `type` desconhecido nem altera o modelo de conteúdo dos tipos.

## Texto e entidades

Texto admite Unicode, exceto NUL e controles de U+0001 a U+001F que não sejam tab, CR ou LF. O mesmo vale para valores de atributos depois de decodificados. `<` e `&` literais devem ser escritos como entidades.

Entidades aceitas: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`, `&#decimal;` e `&#xhexadecimal;`. Numéricas exigem pelo menos um dígito e um valor escalar Unicode permitido. Entidades desconhecidas, sem `;`, surrogates e valores acima de U+10FFFF são erros. A decodificação ocorre uma vez; um resultado `&lt;` não é decodificado novamente.

Na apresentação, sequências de espaços em conteúdo textual colapsam em um espaço, inclusive entre nós `text`; removem-se espaços nas extremidades do bloco. A árvore sintática preserva os intervalos originais para diagnósticos e formatação. Espaços de indentação em contêineres estruturais são ignorados. Preservação literal de espaços fica para uma extensão futura.

## Raiz e metadados

```htdl
<div type="document" version="0.1" lang="pt-BR">
  <div type="head">
    <div type="title">Contador</div>
    <div type="meta" name="description" content="Exemplo HTDL"></div>
    <div type="script" src="./app.assis" format="source"></div>
  </div>
  <div type="body">
    <div type="main">
      <div type="heading" level="1">Contador</div>
      <div type="paragraph" id="valor">0</div>
      <div type="button" on:click="incrementar">Somar um</div>
    </div>
  </div>
</div>
```

Há exatamente um `document`, com `version="0.1"` e `lang` obrigatório e não vazio. O registro completo de idiomas será especificado antes da conformidade pública; o leitor deve preservar o identificador. Filhos da raiz são exatamente um `head` seguido por um `body`. `head` contém exatamente um `title` não vazio, zero ou mais `meta` e no máximo um `script`. A ordem desses filhos do `head` é livre.

`meta` exige `name` e `content`; na 0.1 o único nome definido é `description`, sem repetição. Metadados desconhecidos são erros nessa versão. `script` exige `src` e `format`; `source` identifica fonte `.assis` no desenvolvimento e `wasm` identifica `.wasm` pré-compilado no modelo recomendado. Fonte embutido no corpo de `script` não é aceito. Dependências entram por `#yuri` e `#body` no programa AssisScript.

O formato de compilação pode ser revisto pela prova de conceito antes de estabilizar a especificação. FluxStyle (FS) usa `.fxs` ou `.flux`, em parceria com SSC, cuja extensão recomendada é `.sscr`. O [parecer A03](13-revisao-extensoes-abertos-e-propostas.md) propõe `type="presentation"` com `src` e `language` para **HTDL 0.2**. Esses elementos não são válidos no catálogo 0.1 descrito aqui.

## Tipos e modelos de conteúdo

Conteúdo **estrutural** aceita os tipos de corpo listados abaixo, salvo restrições específicas; não admite texto direto não vazio. Conteúdo **textual** aceita texto e filhos `text`. `text` só contém texto. A regra impede texto solto de virar um bloco por acidente.

| `type` | Conteúdo e restrições | Atributos específicos |
| --- | --- | --- |
| `document` | `head`, depois `body`; somente raiz | `version`, `lang` |
| `head` | `title`, `meta`, `script`, conforme regras acima | Nenhum |
| `title` | Somente texto; não vazio | Nenhum |
| `meta` | Vazio | `name`, `content` |
| `script` | Vazio | `src`, `format` |
| `body` | Estrutural | Nenhum |
| `container` | Estrutural, sem papel semântico adicional | Nenhum |
| `main` | Estrutural; no máximo um por documento | Nenhum |
| `section` | Estrutural | Nenhum |
| `header`, `footer`, `nav` | Estrutural | Nenhum |
| `heading` | Textual e não vazio | `level`: inteiro de 1 a 6, obrigatório |
| `paragraph` | Textual | Nenhum |
| `text` | Somente texto; fragmento inline | Nenhum |
| `button` | Textual; nome acessível não vazio | `action`: `button` ou `submit`; padrão `button` |
| `link` | Textual; nome acessível não vazio | `href`, obrigatório |
| `list` | Apenas `item`, além de espaços e comentários | `ordered`: `true` ou `false`; padrão `false` |
| `item` | Estrutural; pai deve ser `list` | Nenhum |
| `label` | Textual e não vazio | `for`, obrigatório, aponta para `input` |
| `input` | Vazio | `kind`, `value`, `name`, `placeholder`, `required`, `checked` |
| `form` | Estrutural; não contém outro `form` | Nenhum |
| `image` | Vazio | `src` e `alt`, obrigatórios; `alt=""` indica decorativa |

Os tipos de corpo não podem aparecer dentro de `head`. `body`, `document` e tipos de metadados não podem aparecer em conteúdo estrutural de corpo. `text` só aparece em conteúdo textual; `item` só em `list`. Um `input`, `button`, `link` ou `form` não pode ser aninhado em conteúdo textual. `main` não pode ficar dentro de `header`, `footer` ou `nav`.

`input.kind` aceita `text`, `number` e `checkbox`, com padrão `text`. `value` é sempre texto, padrão vazio; no campo numérico o parser não converte automaticamente para `int`. `checked` só vale em checkbox; `required` vale nos três. A validação numérica 0.1 aceita inteiro decimal opcionalmente negativo, sem separadores, dentro de int64; o texto digitado pode permanecer temporariamente inválido até o envio do formulário. `name` identifica o controle dentro de um formulário e, quando presente, deve ser único nesse formulário. Não há submissão automática à rede nessa versão.

`button action="submit"` exige ancestral `form`. A ação padrão dispara `submit` no formulário se os controles forem válidos. Sem manipulador, não há navegação nem envio de dados. A ativação de `label` transfere foco ao controle associado e alterna o checkbox quando aplicável.

O conjunto inteiro acima é o alvo de conformidade 0.1. Protótipos podem implementar subconjuntos, anunciados como tais. As etapas de implementação estão no [plano](05-plano-de-execucao.md).

## Atributos comuns

| Atributo | Regra |
| --- | --- |
| `type` | Obrigatório em todo elemento, inclusive raiz e metadados |
| `id` | Opcional em elementos de corpo; único em todo o documento; `[A-Za-z_][A-Za-z0-9_-]*` |
| `class` | Lista de tokens separados por espaços, com a mesma forma de `id`; duplicatas são normalizadas |
| `hidden` | Booleano explícito `true` ou `false`; padrão `false`; retira desenho, interação e árvore acessível |
| `disabled` | Booleano explícito; padrão `false`; somente `button` e `input` |
| `a11y-label` | Nome acessível alternativo não vazio em `button`, `link`, `input`, `nav`, `section` e `form` |
| `a11y-live` | `off`, `polite` ou `assertive`; padrão `off`; em `paragraph`, `container` e `section`, solicita anúncio de mudanças textuais |
| `data-*` | Metadado textual da aplicação; sufixo minúsculo `[a-z][a-z0-9-]*`; não executa código |
| `on:EVENTO` | Nome de função AssisScript, conforme contrato de eventos |

Exceto `type`, atributos comuns só são aceitos em tipos de corpo, incluindo `body`; `disabled`, `a11y-label` e `a11y-live` têm as restrições da tabela. Atributos específicos da raiz continuam explícitos. Atributos desconhecidos são erros, com sugestão quando houver grafia próxima. Booleanos sem valor, `disabled="yes"` e `hidden=1` são erros.

`class` cria um ponto estável para bindings FluxStyle/SSC e pode ser manipulado pelo programa. Não define uma aparência por si só; alterações de binding devem ser revalidadas. `type` não pode ser alterado durante a vida de um nó na versão 0.1; trocar sua semântica exige criar outro nó em uma versão que ofereça essa operação.

## Eventos e ações padrão

`on:click="incrementar"` é referência a um símbolo, com forma `[A-Za-z_][A-Za-z0-9_]*`. Não contém chamada, argumentos, expressão ou programa em texto. A função deve existir no programa do documento e ter a assinatura definida no [contrato AssisScript](03-assisscript-no-navegador.md). Eventos declarados sem `script` são erro.

| Evento 0.1 | Onde declarar | Origem e ação |
| --- | --- | --- |
| `click` | `button` e `link` | Ativação por ponteiro ou teclado; link pode navegar após o manipulador |
| `input` | `input` | Mudança do valor ou de `checked` pelo usuário |
| `change` | `input` | Confirmação de edição; checkbox dispara após a alternância |
| `submit` | `form` | Envio solicitado por controle de submissão ou Enter em campo válido |
| `focus`, `blur` | `button`, `link`, `input` | Entrada e saída de foco |

Eventos 0.1 são entregues diretamente ao elemento declarado; não há captura, propagação por ancestrais ou registro dinâmico. Essa escolha reduz o contrato inicial e pode ser ampliada por outra versão de API. O argumento `alvo` é o identificador do elemento declarado, não um filho textual atingido pelo ponteiro.

O motor aplica a mudança nativa do controle e depois entrega `input`/`change`. Em checkbox, ambos ocorrem uma vez por alternância, nessa ordem. Para campos de texto e número, `input` ocorre em cada edição confirmada pelo sistema de entrada; `change` ocorre ao confirmar com Enter ou sair do foco se o valor mudou. Composição por IME deve ser preservada e não gerar atualizações parciais inválidas de UTF-8.

`click` e `submit` são canceláveis por API durante o manipulador; os demais não. Depois de `click`, executar a ação padrão se não cancelada: submissão de formulário ou navegação de link. Um erro no manipulador cancela a ação padrão daquela ativação. Eventos produzidos por uma ação padrão entram na fila depois da tarefa atual, sem reentrada.

`button` recebe foco com Tab, ativa com Enter no pressionamento e com Espaço na liberação, sem ativação extra pela repetição automática. O estado desabilitado impede ativação e foco sequencial. `link` ativa com Enter; Espaço conserva a rolagem. A semântica de botão segue a convenção de teclado descrita pela [W3C APG](https://www.w3.org/WAI/ARIA/apg/patterns/button/).

Ocultar ou desabilitar o controle focado leva o foco ao próximo controle elegível na ordem do documento, ou ao documento se não existir. A atualização acessível ocorre junto da alteração visual.

## Links, imagens e acessibilidade

`href` aceita fragmento `#id`, caminho relativo da aplicação e endereço HTTPS futuro. `src` segue as regras de recurso do [ecossistema](01-ecossistema.md). Esquemas de execução e URLs `javascript:` não existem. O visualizador local suporta fragmentos e arquivos da aplicação; HTTPS só será ativado na etapa de rede.

Toda entrada precisa de `label for="id"` ou `a11y-label`; `placeholder` não substitui nome acessível. Imagens informativas exigem `alt` não vazio; imagens decorativas com `alt=""` não entram como conteúdo acessível. `button` e `link` derivam nome do texto, salvo `a11y-label` explícito. O motor exporta títulos, listas, regiões, valores e estados para a tecnologia assistiva da plataforma.

Mudanças em regiões `a11y-live` são consolidadas por tarefa. `polite` solicita anúncio sem interromper a fala atual; `assertive` solicita prioridade. O anúncio efetivo depende da tecnologia assistiva. O motor não transfere foco para anunciar uma atualização e limita a fila para impedir acúmulo de mensagens.

## Diagnósticos e recuperação

Famílias sugeridas: `H1xx` léxico/sintaxe, `H2xx` estrutura e atributos, `H3xx` recursos e funções, `H4xx` execução e limites. O primeiro verificador pode interromper após o primeiro erro; o editor deverá recuperar sem executar o documento inválido.

Posições internas usam offsets de bytes UTF-8; diagnósticos publicados incluem linha e coluna UTF-16, base 1, fim exclusivo, para conversar com o editor e os diagnósticos atuais do AssisScript. O arquivo e a origem do erro devem ser preservados em imports.

Exemplo de mensagem: `H201: type obrigatório em <div>`, com intervalo da abertura e correção sugerida. Outros casos obrigatórios: tag `button` em vez de `div`, `type="buton"`, IDs duplicados, `for` ausente, função com assinatura incorreta e `script` com conteúdo.

Uma falha de sintaxe impede criar a página executável. Recurso visual ausente mostra alternativa textual e diagnóstico. Falha do programa preserva o conteúdo estático, suspende os manipuladores e oferece recarregamento no navegador.

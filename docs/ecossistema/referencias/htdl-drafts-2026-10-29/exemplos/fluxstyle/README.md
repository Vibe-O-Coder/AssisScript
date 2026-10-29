# FluxStyle + SSC: uma apresentação reativa

**O cartão é conceitual, ainda sem navegador ou compiladores FS/SSC.** Código, identificadores e comentários estão em inglês. `.fxs` é a extensão FluxStyle preferida; `.flux` é alternativa válida. `.sscr` é a recomendação revisada para SSC, adotada neste exemplo. Uma extensão definida não implica que sua ferramenta já esteja implementada.

| Arquivo | Responsabilidade |
| --- | --- |
| [index.htdl](index.htdl) | Proposta HTDL 0.2 para carregar os recursos de apresentação |
| [app.assis](app.assis) | Alterna estado pela API de navegador ainda proposta; checado com assinaturas substitutas |
| [card.fxs](card.fxs) | Estado e largura disponível alimentam layout, pintura e um destino vertical |
| [card.sscr](card.sscr) | Uma mola aproxima a apresentação do destino confirmado por FS |
| [spring_reference.py](spring_reference.py) | Emulação numérica exploratória, não um compilador SSC |
| [audit_reference.py](audit_reference.py) | Reproduz resultados e detecta a garantia numérica incorreta do rascunho anterior |
| [spring_kernel.assis](spring_kernel.assis) | Prova nativa isolada do kernel puro, com repouso no passo 41 |

O cenário tem um único elemento HTDL com `class="card"`. `index.htdl` usa a proposta **0.2**, com elementos `div type="presentation"`, `src` e `language`. Isso não altera silenciosamente o catálogo da HTDL 0.1. A sintaxe de carregamento foi respondida no [parecer A03](../../docs/13-revisao-extensoes-abertos-e-propostas.md).

Quando `card.expanded` vale `false`, a largura desejada é no máximo 320px, o deslocamento vertical é zero e o fundo é escuro. Quando vale `true`, a largura desejada é no máximo 640px, o deslocamento é -8px e o fundo muda para violeta. Em ambos os estados, a largura também respeita o espaço disponível informado pelo passe de layout.

A largura é tratada como tamanho externo desejado da caixa; o motor calcula a área de conteúdo considerando o preenchimento. Em espaços extremos, preenchimento e tamanhos mínimos ainda precisarão das regras de redução/overflow do layout. O exemplo não promete resolver todos esses casos.

O estado é uma entrada compartilhada da instância da página, com padrão `false`. A API de navegador continua proposta; o esboço usa sua ponte de inteiros. Estado por nó foi recomendado com `scope: node` e handles com geração, mas não foi implementado nem é usado neste cartão.

FS confirma as saídas por atualização. SSC conserva posição/velocidade entre passos e anima apenas o deslocamento de apresentação. Com movimento reduzido, o mesmo destino é aplicado diretamente. O texto e a ordem semântica HTDL continuam sob o contrato do motor.

O [rascunho do FluxStyle](../../docs/09-fluxstyle-e-fluxo.md) explica tipos, conflitos de produtores, ciclos, composição e integração. O [parecer A/N](../../docs/13-revisao-extensoes-abertos-e-propostas.md) e os relatórios [Python](../../docs/revisao-2026-10-25-spring.json) / [AssisScript](../../docs/revisao-2026-10-25-assisscript.json) separam a revisão conceitual das verificações realmente executadas.

## Reproduzir as provas isoladas

Com Python 3, a partir da raiz do projeto:

```text
python -B exemplos/fluxstyle/audit_reference.py
```

Com o compilador AssisScript disponível:

```text
assis run exemplos/fluxstyle/spring_kernel.assis
assis run exemplos/fluxstyle/spring_kernel.assis --no-opt
```

A saída nativa esperada é `SSC numerical kernel: 41`. Esses comandos não executam o cartão, não interpretam FS/SSC e não fornecem a API de navegador. A auditoria Python passa quando encontra o contraexemplo esperado: detectar uma garantia falsa é o resultado correto dessa verificação.

# Dois painéis com estado independente

Exemplo **conceitual** HTDL 0.2, FS 0.1, SSC 0.1 e API de página proposta. Nenhum arquivo foi compilado/executado nesta rodada. Em particular, as funções de estado por nó não são alegadas como biblioteca disponível do AssisScript.

| Arquivo | Papel |
| --- | --- |
| [index.htdl](index.htdl) | Dois botões e duas seções com IDs distintos |
| [panels.fxs](panels.fxs) | Um fluxo instanciado nas duas seções, com `scope: node` |
| [panels.sscr](panels.sscr) | Um movimento instanciado para os dois offsets |
| [app.assis](app.assis) | Handlers nomeados que gravam o estado no handle da seção correta |

Os botões ficam fora das seções animadas. Isso permite verificar o movimento sem a política de foco congelar um ancestral do próprio botão. O exemplo inicial não implementa um disclosure que oculte conteúdo: alterna apenas largura/cor/destino e mantém as duas seções legíveis.

Com viewport de 900 px, ativar `toggleFirst` muda o destino de `firstPanel` para −8 px e sua largura para 640 px. `secondPanel` conserva destino zero e largura 320 px. Ativar `toggleSecond` depois altera somente a segunda célula. As larguras mudam de uma vez; apenas os offsets são animados.

Os estados começam ausentes e o padrão FS falso coincide com a leitura inteira zero da API legada. Ocultar uma seção preservaria seu estado; recriar um nó com o mesmo ID teria outra geração e estado novo. A recriação é um cenário do motor, não uma API pública de criação de nós já oferecida por este exemplo.

SSC continua opcional: omitindo sua declaração `presentation`, o motor aplica o destino diretamente. Isso difere de declarar um arquivo SSC que falha ao carregar: nesse caso, o conjunto autoral inteiro é rejeitado. Movimento reduzido aplica o destino diretamente. A extensão `.sscr` segue a recomendação da revisão, enquanto `.fxs` é a preferência confirmada pelo grupo.

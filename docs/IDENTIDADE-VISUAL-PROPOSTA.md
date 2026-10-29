# Proposta de identidade visual — 28/10/2026

Estado: proposta para avaliação do responsável, sem troca dos ícones ativos e
sem reconstrução dos pacotes nesta atualização.

## Informação recebida

O responsável informou que as duas imagens originais são stickers amplamente
utilizados na comunidade, sem identificação acessível dos autores originais.
Esse relato esclarece a origem imediata, mas não fornece licença ou autorização
de distribuição das imagens. A [orientação da WIPO](https://www.wipo.int/en/web/copyright/faq-copyright)
explica que disponibilização na internet não torna uma obra automaticamente de
domínio público. Não foi feita uma conclusão jurídica sobre cada sticker.

## Abordagem proposta

Usar dois desenhos vetoriais simples, produzidos nesta continuação com
primitivas geométricas e símbolos de programação, sem importar ou traçar as
imagens dos stickers. Os SVGs não incorporam fotografias, fontes, imagens,
scripts, links externos ou ícones de bibliotecas de terceiros.

- `assets/propostas/source-v1.svg`: chaves e barra de código para o fonte.
- `assets/propostas/compiled-v1.svg`: processador e execução para o compilado.

Os dois fontes foram escritos pelo agente no contexto deste projeto. Esse
registro descreve o processo de criação, sem afirmar exclusividade dos símbolos
genéricos ou alterar a licença escolhida para o projeto.

## Aplicação necessária após a escolha visual

1. Guardar uma cópia local recuperável dos stickers e derivados anteriores,
   fora dos diretórios distribuídos.
2. Gerar os PNG/ICO e substituir as cópias em `assets` e nos ícones do editor.
3. Regenerar `src/icon_blob.h`, pois os executáveis gerados incorporam o ícone
   compilado; reconstruir compiladores e instalador.
4. Atualizar o gerador de ícones para ter SVGs conhecidos como fonte, os avisos
   de procedência, inventários, hashes, ZIP e VSIX.
5. Conferir que a distribuição nova não carrega os stickers nem seus derivados,
   inclusive nos binários. A troca só dos PNGs visíveis não cobre esses usos.

A alternativa elimina a dependência desses stickers na distribuição futura.
P6-POLICY continua parcial até a troca efetiva e a conclusão da revisão dos
termos/fontes de redistribuição das demais dependências.

## Direção confirmada: Hoshimi Miyabi e traços discretos de raposa

O responsável especificou Hoshimi Miyabi, de ZZZ, como referência de cores e
pediu no máximo alguns traços de raposa. A direção está registrada como um
desenho vetorial próprio, com fundo grafite, branco frio, azul-gelo e pequeno
acento vermelho. A [apresentação oficial da personagem](https://zenless.hoyoverse.com/en-us/news/126839)
é uma referência de direção; a paleta abaixo é uma proposta de interpretação.

- `assets/propostas/source-fox-v2.svg`: chaves/barra de código e orelhas geométricas.
- `assets/propostas/compiled-fox-v2.svg`: processador/execução e orelhas geométricas.
- Paleta proposta: `#141927`, `#edf3f7`, `#8bc7e8`, `#d84e63`.

Os SVGs foram desenhados nesta continuação com primitivas geométricas. Permanecem
na pasta de propostas; PNG/ICO, associações, ícones embutidos e pacotes ativos
ainda usam o conjunto anterior. A aplicação completa e a revisão dos demais
componentes de distribuição continuam necessárias para P6-POLICY.

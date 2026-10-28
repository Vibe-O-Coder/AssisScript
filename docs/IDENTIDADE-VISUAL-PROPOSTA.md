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

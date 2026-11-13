# pageedit — estado de campos HTDL

`Fields` mantém um valor UTF-8 de linha única e uma seleção por
`NodeId`. São até 64 campos e 1.024 bytes por campo, inclusive campos
ocultos. A inicialização lê `value` e posiciona o cursor no fim.
O perfil recusa valores iniciais acima da cota ou com caracteres de
controle. A classe depende do parser HTDL e das fronteiras de grafema
Unicode 17 usadas na leitura.

`apply(node, edit)` insere um escalar Unicode, apaga a seleção ou
um grafema, move para a esquerda/direita, início/fim, seleciona tudo ou
posiciona o cursor numa fronteira. Os offsets são bytes UTF-8. Se uma
edição unir dois grafemas, o cursor avança até a próxima fronteira.
Falha de validação ou de memória preserva valor e seleção.

`FrameHost` prepara uma cópia do estado da mesma instância de documento.
`edit_field` exige a revisão do quadro, a sequência de entrada e o nó
em foco. O novo valor e a seleção acompanham o commit raster/MSAA.
Uma navegação inicializa novos campos. Texto numérico pode ficar
temporariamente inválido durante a edição. A submissão local aceita
inteiros decimais int64 com sinal negativo opcional.
[Perfil de edição](ecossistema/PERFIL-EDICAO-LOCAL-V1.md).

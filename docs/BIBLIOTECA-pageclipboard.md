# pageclipboard — leitura local da área de transferência

`import "std/pageclipboard.assis";` importa a ponte do shell confiável
para a área de transferência do Windows x64. `ClipboardText(window,
document)` copia até 1.024 bytes de texto UTF-8. A janela deve ter
entrada de texto habilitada e o mesmo documento editável ativo.
`status()` retorna a quantidade copiada, zero para texto ausente
ou vazio, ou erro negativo. `data()` empresta a cópia local.
Em Linux e macOS o provider retorna `-3` para uma janela válida.

O host lê somente ao receber uma ação de colagem aceita pelo Frame.
O aplicativo confirma a edição por `Session.paste_field` junto ao
raster e à árvore acessível. O import fica no exemplo editável.
[Perfil HTDL](ecossistema/PERFIL-EDICAO-LOCAL-V1.md).

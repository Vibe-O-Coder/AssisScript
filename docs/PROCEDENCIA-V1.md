# Revisão de procedência e redistribuição — 29/10/2026

Esta revisão substitui as pendências de imagens da documentação histórica.
P6-POLICY cobre a composição desta distribuição, seus termos e os mecanismos de
verificação; não concede direitos sobre código ou provedores externos futuros.

## Identidade selecionada

O responsável escolheu os SVGs **v1** existentes. São desenhos geométricos
produzidos no desenvolvimento do projeto, sem importar ou traçar os stickers.
Usamos exatamente esses fontes; a proposta fox-v2 não se tornou ativa.
As referências de direção Miyabi/raposa não foram incorporadas como personagem,
logotipo, textura ou imagem de terceiros. Os v1 usam seus próprios símbolos
genéricos de fonte/processador e sua paleta original.

`tools/build-icons.py` agora tem os SVGs v1 como única entrada visual e gera
PNG/ICO/ICNS, cópias do editor, `src/icon_blob.h`, `src/icon_icns.h` e o manifesto
de hashes `assets/IDENTIDADE-V1.json`. O compilador Windows recebe o ícone de
fonte via RC; instalador e PEs gerados recebem o compilado. Bundles macOS
recebem compiled.icns. Os arquivos `*-original.png` saíram da árvore ativa.
Uma cópia recuperável dos antigos arquivos ficou no workspace de manutenção,
fora da árvore distribuída. Pacotes excluem histórico e diretórios de build.

## Componentes e decisão aplicada

| Componente distribuído | Procedência e termos | Aplicação nesta revisão |
| --- | --- | --- |
| Fontes originais, stdlib, editor/LSP, runtimes e SVGs v1 | Projeto; LICENSE escolhido pelo responsável | Fontes, avisos, comandos e hashes incluídos |
| Suporte GCC e startup Windows | Toolchain GCC não modificada; GPLv3 com Runtime Library Exception nos arquivos abrangidos | Compilação elegível, inventário de membros, GPL/Exception incluídos |
| Runtime/imports MinGW-w64 | Avisos permissivos por componente no arquivo copiado da toolchain | Notices mantidos integralmente, sem aplicar CC aos componentes |
| Startup/suporte Linux e ligação com glibc | glibc e LGPL2.1+; suporte GCC com Exception quando aplicável | Build Linux passa a ligação dinâmica, texto LGPL e direito de substituição/depuração documentados |
| libSystem/dyld, APIs Windows, libcurl/TLS opcionais | Provedores externos da plataforma | Sem cópias de bibliotecas do sistema ou do provedor no pacote |
| LLVM/Python/Pillow/CairoSVG/Node/binutils/VS Code | Ferramentas de manutenção | Não são dependências vendorizadas nem componentes incorporados no runtime |

Os inventários `build-audit-windows.json` e `build-audit-linux.json` exigem
reconstrução com bytes idênticos e classificam cada entrada real do linker.
Registram versão/hash da toolchain, objetos de startup, archives e membros,
imports, fontes e assets. Novas bibliotecas sem classificação fazem o gate
falhar. Fontes de componentes upstream e textos primários revisados:

- [GCC Runtime Library Exception 3.1](https://www.gnu.org/licenses/gcc-exception-3.1.en.html)
  e [FAQ oficial](https://www.gnu.org/licenses/gcc-exception-3.1-faq.html.en).
- [GCC fontes](https://gcc.gnu.org/git.html) e
  [MSYS2 receitas/pacotes](https://github.com/msys2/MINGW-packages).
- [MinGW-w64 avisos e fontes](https://github.com/mingw-w64/mingw-w64/blob/master/COPYING.MinGW-w64/COPYING.MinGW-w64.txt).
- [LGPL 2.1, seção 6](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
  e [glibc fontes](https://sourceware.org/git/?p=glibc.git).

O pacote do projeto não distribui fontes de ferramentas não incorporadas.
Os fontes completos do compilador e dos runtimes próprios, os SVGs e os
comandos para reconstrução acompanham o ZIP. A licença do projeto não substitui
as permissões dos componentes de terceiros, inclusive depuração de modificações
LGPL. Binários históricos estáticos e stickers antigos não entram na nova
distribuição. Distribuições futuras com bibliotecas externas adicionais exigem
novo inventário; o gate deve ser executado no pacote efetivo.

## Verificação

`tools/verify-v1-policy.py` confere hashes, SVG sem referências externas,
derivados do editor, bytes de ICNS, imagens dos recursos PE do compilador e
instalador, recursos de programas gerados, inventários atuais e ausência dos
originais/histórico nos ZIP/VSIX. Os resultados ficam em
`VALIDACAO-TARGETS-V1.json`; a execução completa do pacote também está no Actions.

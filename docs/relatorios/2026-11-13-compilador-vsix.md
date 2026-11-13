# Atualização do compilador Windows e do VS Code

13/11/2026, America/Fortaleza. Compiladores e bibliotecas reconstruídos da
revisão publicada `48a18b7b3116940e00d008ac6b2610ba6a2dc175`.
O compilador instalado e a extensão ativa já declaravam `3.3.0-alpha.15`
com binários anteriores. O VSIX antigo na raiz declarava `alpha.10`.
O GitHub retornou uma lista vazia de Releases e de tags. A versão da
fonte e do manifesto do editor nessa revisão é `3.3.0-alpha.15`.
[Revisão de origem](https://github.com/Vibe-O-Coder/AssisScript/commit/48a18b7b3116940e00d008ac6b2610ba6a2dc175).

| Artefato | SHA-256 |
| --- | --- |
| Compilador Windows x64 | `d5e3e4adf0e2fa152a52fac8941e50ecf736866d46a3bedf0be0c2cb3a64103c` |
| Compilador Linux x64 no VSIX | `3b566d122b6ad1e76748ae1ac0b912d2933b3ca20e6ecc71e73beaba7492214e` |
| VSIX alpha.15 | `54ac37dbfa99b29bf7568e3bd46a41899de50d558448ba0fdfcdfe736854c446` |
| Pacote Windows x64 | `b06b00f2df4ec3675dff509a1f0fbfba14b946598df31dfce184a3aa7581e944` |

`tools/build-windows.ps1` reconstruiu o compilador PE com seus recursos.
`make -B bin/assis` reconstruiu o ELF no Ubuntu WSL2. O pacote Windows
inclui a DLL gráfica e o worker correspondentes. A instalação de teste
conferiu 912 arquivos e a remoção preservou o arquivo pessoal de teste.
A atualização do prefixo já instalado repetiu a conferência de 912
arquivos, o exemplo de entrada tipada e a janela de formulário.
O PATH e as associações do Windows foram preservados. Os arquivos
substituídos foram copiados para `build/current-distribution/build/previous-assisscript`.

O VSIX foi instalado em perfil isolado e depois no perfil padrão por
`code --install-extension --force`. A CLI reportou
`assisscript-local.assisscript@3.3.0-alpha.15`. O compilador do perfil
e o compilador do terminal passaram a ter o mesmo SHA-256. O verificador
comparou 67 arquivos, executou 16 casos no VSIX extraído por host x64
e mais 16 casos nos arquivos instalados do VS Code Windows. Os seis
testes Node da extensão passaram. A extensão anterior foi preservada
em `build/current-distribution/build/previous-vscode-extension`.

O ZIP e o VSIX ficam em `build/current-distribution/dist`. O VSIX
contém compiladores Windows e Linux x64. Esta atualização instala
a revisão publicada acima. O perfil de edição HTDL da rodada seguinte
tem sua própria validação e relatório.

O [VSIX alpha.15](../../assisscript-3.3.0-alpha.15.vsix) fica disponível
na raiz da branch. [Execução instalada](../ecossistema/evidencias/toolchain-update-2026-11-13/windows-update-installed.json) ·
[VS Code Windows](../ecossistema/evidencias/toolchain-update-2026-11-13/vsix-installed-windows.json) ·
[VSIX extraído no Linux](../ecossistema/evidencias/toolchain-update-2026-11-13/vsix-extracted-linux.json).

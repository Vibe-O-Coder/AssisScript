# Instalação e verificação da alpha.10

Extraia a distribuição completa. No Windows, execute `instalar-windows.cmd`; a ferramenta nativa também aceita `bin/assis-setup.exe install --prefix CAMINHO --no-path --no-associations`. No Linux, execute `sh instalar.sh --prefix CAMINHO --no-path`. Consulte `--help` para seleção de módulos e demais opções. Uma instalação de avaliação deve usar uma pasta nova.

Após instalar, abra outro terminal ou use o caminho completo para o compilador. Execute `assis version` e confira `3.3.0-alpha.10`. Salve o exemplo do README em `hello.assis` e execute:

```sh
assis check hello.assis --safe
assis run hello.assis --safe --debug
assis build hello.assis --safe -o hello
```

A saída deve ser `2`, `4` e `6`, em linhas separadas. O executável produzido roda independentemente do compilador. Para trabalhar diretamente no checkout, use `bin/assis` no Linux ou `bin/assis.exe` no Windows e mantenha a pasta `stdlib` ao lado da árvore de distribuição.

No VS Code, instale o VSIX local da mesma versão, selecione o compilador correspondente e consulte [VSCODE.md](VSCODE.md). O LSP independente está em `tools/assis-lsp.js` e requer Node; os programas compilados não precisam dele.

Os módulos obrigatórios e opcionais estão em [catalogo.json](../stdlib/catalogo.json). APIs e imports usam inglês; projetos anteriores seguem a [migração](ENGLISH-API.md). Faça backup antes de atualizar e consulte a [política de rollback](SUPPORT.md). Para remover, use `desinstalar-windows.cmd` ou `sh desinstalar.sh` com o prefixo da instalação.

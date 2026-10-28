# AssisScript 2.1 no Windows

Este pacote inclui **`bin/assis.exe` para Windows 10/11 x64**, pronto para usar. Não precisa instalar Python, GCC, Clang, MinGW, Node, WSL ou bibliotecas extras. O compilador e o instalador usam componentes que já fazem parte do Windows.

## Instalar

Extraia o ZIP inteiro. Dentro da pasta `AssisScript`, execute `instalar-windows.cmd`. No PowerShell ou no terminal integrado do VS Code:

```powershell
.\instalar-windows.cmd
```

O instalador nativo copia o compilador para `%LOCALAPPDATA%\AssisScript\bin\assis.exe` e acrescenta essa pasta ao **PATH do usuário**. Não exige administrador, não usa `setx` e preserva o PATH existente. Manuais e exemplos também são copiados.

Feche e reabra o terminal. Confira:

```powershell
assis version
assis doctor
```

A versão deve informar `AssisScript 2.1.0 (nativo, Windows x64)`.

## Criar, executar e compilar

```powershell
assis new meu-projeto
cd meu-projeto
assis run
assis build -o programa.exe
.\programa.exe
```

`assis new` cria um arquivo `assis.assis`. Sem informar fonte, `build`, `run`, `check` e `tokens` procuram esse arquivo na pasta atual.

```powershell
assis check .\assis.assis
assis tokens .\assis.assis
assis run .\assis.assis --timeout 5
```

O comando `build` gera um `.exe` PE32+ diretamente. Não chama outro compilador ou interpretador. Se `-o` não terminar em `.exe`, essa extensão é acrescentada. Sem `-o`, o resultado usa o nome do fonte com extensão `.exe`.

O executável gerado pode ser levado para outro Windows x64 sem levar o compilador. Seus únicos imports são APIs de `KERNEL32.dll`, que pertence ao sistema operacional. A imagem inclui relocations para ASLR, marcação DEP e seções sem escrita e execução simultâneas.

## Usar sem instalar

Na pasta extraída:

```powershell
.\bin\assis.exe version
.\bin\assis.exe run .\exemplos\07_arena.assis
.\bin\assis.exe build .\exemplos\03_polimorfismo.assis -o polimorfismo.exe
.\polimorfismo.exe
```

Nenhuma alteração no PATH é feita nesse modo. Caminhos com espaços e acentos são tratados em Unicode.

## Instalar em outra pasta

```powershell
.\instalar-windows.cmd --prefix "D:\Ferramentas\AssisScript"
```

Para copiar sem alterar o PATH:

```powershell
.\instalar-windows.cmd --prefix "D:\Ferramentas\AssisScript" --no-path
```

O instalador está em `bin/assis-setup.exe`. Os arquivos `.cmd` apenas invocam esse binário. A instalação não depende de PowerShell.

## Desinstalar

Use o arquivo da pasta extraída:

```powershell
.\desinstalar-windows.cmd
```

Se usou um destino personalizado, informe o mesmo `--prefix`. Se instalou com `--no-path`, use essa opção também na remoção. O desinstalador remove apenas os arquivos conhecidos do pacote e a entrada correspondente no PATH, preservando projetos ou outros arquivos acrescentados pelo usuário. Encerre processos AssisScript em execução antes de remover o compilador.

## Compilar para outro sistema

O mesmo compilador aceita ambos os destinos:

```powershell
assis build .\assis.assis --target windows-x64 -o programa.exe
assis build .\assis.assis --target linux-x64 -o programa-linux
```

O segundo arquivo é ELF64 para Linux x86_64. Depois de copiá-lo para Linux, marque-o como executável com `chmod +x programa-linux`. `run` aceita apenas o destino do sistema atual.

## Testes e limite da validação

Para testar os binários reais na sua máquina Windows:

```powershell
.\tests\test-windows.cmd
```

A suíte usa o PowerShell já fornecido pelo Windows, sem módulos extras. Compila e executa os casos da linguagem, testa os comandos, Unicode, timeout, independência do PATH e instalação/remoção em pasta temporária com `--no-path`. Não altera o PATH do usuário durante os testes.

**Nesta entrega, os binários Windows foram compilados e inspecionados no Linux.** Os 33 casos do runtime PE passaram por um carregador de testes com ABI Microsoft, base relocada e stubs Win32. Esse teste verifica o código gerado, mas não substitui a execução no Windows. O ambiente disponível não permitiu iniciar o Wine, e a suíte nativa acima ainda precisa ser executada em Windows real.

Não há binários nativos para Windows de 32 bits, ARM ou macOS nesta versão. O suporte Linux x86_64 e a sintaxe anterior foram preservados.

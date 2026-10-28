# AssisScript 2.1: compilador nativo

**Instale uma vez. Escreva Assis. Compile com `assis`.**

Este pacote contém **binários prontos para Windows x64 e Linux x86_64**, com instaladores e comandos próprios no terminal. O compilador é escrito em C e gera instruções x86_64 em arquivos PE32+ ou ELF64 diretamente. **Não exige Python, Node, Java, GCC, Clang, assembler ou linker na máquina de quem o instala.** Os programas gerados são independentes do compilador; no Windows, usam somente APIs do sistema operacional.

A sintaxe da linguagem foi preservada: classes, herança, métodos virtuais, inteiros, bytes, ponteiros e memória manual. Palavras-chave e identificadores continuam sendo variações de **Assis** e **Fodase**.

## Instalar no Windows x64

Extraia o pacote inteiro. Na pasta `AssisScript`, execute:

```powershell
.\instalar-windows.cmd
```

Feche e reabra o terminal. Depois:

```powershell
assis version
assis new meu-projeto
cd meu-projeto
assis run
assis build -o programa.exe
.\programa.exe
```

O instalador nativo copia `bin/assis.exe` para `%LOCALAPPDATA%\AssisScript\bin` e configura o PATH do usuário, sem administrador. Para usar sem instalar, execute `.\bin\assis.exe`. A instalação não usa PowerShell; o `.cmd` chama `bin/assis-setup.exe`.

Leia **`docs/WINDOWS.md`** para uso portátil, instalação personalizada, desinstalação e testes. Não há binários nativos para macOS, ARM ou Windows de 32 bits.

**Validação Windows:** os binários foram compilados e inspecionados no Linux. Os 33 casos do runtime PE passaram em um carregador de testes com ABI Microsoft e stubs Win32. Isso não substitui a execução em Windows real, ainda não disponível neste ambiente.

## Instalar no Linux x86_64

Extraia o ZIP, abra o terminal na pasta `AssisScript` e execute:

```sh
sh instalar.sh
```

O instalador copia o compilador para `~/.local/bin/assis` e acrescenta esse diretório ao PATH de Bash/POSIX e de Zsh, quando já houver configuração de Zsh. Não usa `sudo`, não compila fontes e não baixa pacotes.

Abra um novo terminal ou atualize o terminal atual:

```sh
. "$HOME/.profile"
assis version
```

Saída esperada:

```text
AssisScript 2.1.0 (nativo, Linux x86_64)
```

Também é possível usar sem instalar:

```sh
chmod +x bin/assis
./bin/assis version
./bin/assis run exemplos/07_arena.assis
```

Os binários estão em `bin/assis` para Linux e `bin/assis.exe` para Windows. Não são scripts ou atalhos para outra linguagem. O pacote inclui o código-fonte para quem quiser estudar ou modificar o compilador.

## Primeiro projeto no Linux

Depois da instalação:

```sh
assis new meu-projeto
cd meu-projeto
assis run
assis build -o meu-programa
./meu-programa
```

`assis new` cria `assis.assis` com um programa orientado a objetos. `assis run` compila e executa em uma pasta temporária. `assis build` produz um executável que pode ser distribuído para outro Linux x86_64 sem levar o compilador junto.

O nome da pasta/projeto é livre. Dentro dos arquivos `.assis`, os nomes seguem a regra Assis/Fodase.

## Comandos próprios

| Comando | Ação |
| --- | --- |
| `assis new <pasta>` | Cria projeto com exemplo completo |
| `assis build [arquivo.assis] -o programa` | Gera ELF64 no Linux ou PE32+ no Windows |
| `assis run [arquivo.assis]` | Compila e executa |
| `assis run arquivo.assis --timeout 5` | Executa com limite de cinco segundos |
| `assis check [arquivo.assis]` | Verifica sintaxe e tipos |
| `assis tokens [arquivo.assis]` | Mostra tokens e posições |
| `assis doctor` | Mostra informações da instalação e do backend |
| `assis version` | Mostra a versão |
| `assis help` | Mostra a ajuda |

Sem arquivo, os comandos procuram `assis.assis` no diretório atual. Sem `-o`, `build` usa o nome do fonte sem a extensão. No Linux, se o fonte não tiver extensão, acrescenta `.out`. No Windows, acrescenta `.exe` quando necessário. O compilador recusa sobrescrever o próprio binário, o arquivo fonte ou um hard link do fonte.

Também existem os aliases em português: `assis criar`, `assis compilar`, `assis executar` e `assis verificar`. `assis init` equivale a `assis new`.

Exemplo com um programa do pacote:

```sh
assis build exemplos/03_polimorfismo.assis -o polimorfismo
./polimorfismo
```

```text
Base: 14
Derivada via base: 42
```

Ambos os binários também aceitam compilação para outro destino:

```sh
assis build assis.assis --target windows-x64 -o programa.exe
assis build assis.assis --target linux-x64 -o programa-linux
```

`run` exige o destino do sistema atual.

## Um pouco da linguagem

```assis
assis assis_assis(): AssIs {
    Assis AssisAssis: AssIs = 40;
    FODASE("Resposta:", AssisAssis + 2);
    Fodase 0;
}
```

| Palavra | Significado |
| --- | --- |
| `ASSIS` | Classe |
| `ASSIS_FODASE` | Herança |
| `assis` | Função/método |
| `Assis` | Variável/campo |
| `AssIs` / `AssiS` | Inteiro de 64 bits / byte de 8 bits |
| `FodAsE` / `FoDaSe` / `FODase` | Booleano / texto / ausência de retorno |
| `fodase` / `foDASE` | Cria objeto / libera memória |
| `FODASE` / `Fodase` | Imprime / retorna |
| `aSSIS` | Instância atual |
| `assIS` / `fodASE` / `ASSis` | if / else / while |

O manual completo, com o vocabulário inteiro, herança, polimorfismo, memória, números, operadores e exemplos, está em **`docs/LINGUAGEM.md`**. A gramática está em `docs/GRAMATICA.ebnf`.

## Exemplos

| Arquivo | Demonstração |
| --- | --- |
| `exemplos/01_ola.assis` | Variáveis e saída |
| `exemplos/02_objetos.assis` | Classe com estado e inicializador |
| `exemplos/03_polimorfismo.assis` | Despacho virtual por referência da base |
| `exemplos/04_memoria.assis` | Bytes no heap e ponteiros |
| `exemplos/05_bits.assis` | Bits, deslocamentos e overflow |
| `exemplos/06_fibonacci.assis` | Recursão |
| `exemplos/07_arena.assis` | Combate por turnos com ataque virtual |

## Instalação em outro diretório e remoção

```sh
sh instalar.sh --prefix "$HOME/assisscript" --no-path
"$HOME/assisscript/bin/assis" version
```

Nesse caso, adicione o diretório escolhido ao PATH por conta própria, se desejar. A opção `--no-path` impede alterações nos arquivos do shell.

Para remover a instalação padrão:

```sh
sh desinstalar.sh
```

Para remover uma instalação personalizada:

```sh
sh desinstalar.sh --prefix "$HOME/assisscript"
```

A remoção preserva os projetos do usuário. O instalador padrão guarda cópias do manual, gramática e exemplos em `~/.local/share/assisscript`.

## Arquitetura

```text
Fonte .assis → lexer → parser → tipos → instruções x86_64 → ELF64 / PE32+
```

- Frontend e emissor de código em C11, no mesmo executável.
- Runtimes Linux e Windows em assembly x86_64 incorporados ao compilador como bytes.
- Saída direta: não gera C intermediário e não invoca ferramentas externas.
- Objetos usam campos em posições fixas e tabelas de métodos virtuais.
- Buffers e objetos usam `mmap`/`munmap` no Linux e `VirtualAlloc`/`VirtualFree` no Windows.
- Textos, tabelas e código usam segmentos distintos, somente leitura ou leitura/execução; a pilha não é executável.
- Não há interpretador de bytecode ou máquina virtual no caminho de execução.

O compilador Linux foi ligado estaticamente. O compilador Windows depende apenas de DLLs padrão do Windows. Os programas gerados usam syscalls Linux ou APIs de KERNEL32. Esta versão não otimiza o código gerado.

## Testes

No Windows, execute `tests\test-windows.cmd`. Essa suíte usa o PowerShell fornecido pelo Windows e testa instalação com `--no-path`, preservando o PATH do usuário. Ela está incluída para validação nativa e ainda não foi executada em Windows real.

Com o binário do pacote, sem instalar ferramentas de desenvolvimento:

```sh
sh tests/test.sh
```

A suíte compila/executa os casos válidos, compara resultados, verifica diagnósticos de programas inválidos e testa os comandos e o instalador com HOME isolado. Inclui um contrato com 256 operações aritméticas de 64 bits. O teste de independência de ferramentas executa `build` e `run` com PATH apontando para um diretório inexistente. A suíte usa utilitários normais de shell, como `sh`, `diff`, `grep` e `mktemp`.

## Alterar o compilador

**Esta seção é só para desenvolvimento do compilador. Instalar e usar o binário pronto não precisa destas ferramentas.**

Para reconstruir o compilador a partir de `src/assisc.c`, é necessário um compilador C e suporte à ligação estática:

```sh
make
make test
```

Os runtimes já estão incorporados em `src/runtime_blob.h` e `src/runtime_win_blob.h`. Só é necessário rodar `make runtime` se modificar os arquivos `.S`; essa etapa usa GNU binutils. Não há Python no processo de reconstrução.

Para reconstruir `assis.exe` e o instalador nativo, use `make windows` com MinGW-w64 disponível. Isso é requisito apenas para desenvolvimento, não para instalar ou usar os binários prontos. `make test-pe` executa os 33 casos PE no harness Linux com base relocada e stubs Win32.

## Limites da versão 2.1

Windows x64 ou Linux x86_64, um arquivo fonte por compilação, herança simples e membros públicos. Sem imports, genéricos, sobrecarga, floats, FFI, entrada de terminal, biblioteca de arquivos, destrutores ou coletor de lixo. Textos são imutáveis e buffers são acessados por ponteiros com tamanho separado. O limite de fonte é 16 MiB e o compilador rejeita aninhamento excessivo.

Ponteiros brutos não verificam limites ou tempo de vida. O runtime detecta nulo, divisão/resto por zero, deslocamento inválido, falha de alocação e índice de texto inválido. `run` executa código nativo com as permissões do usuário, sem sandbox. Códigos de saída: 1 para erro de linguagem, 2 para arquivo/configuração, 70 para falha detectada pelo runtime e 124 para timeout. Nos outros casos, `run` devolve o status do programa.

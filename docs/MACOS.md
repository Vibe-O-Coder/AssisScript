# Alvos nativos e macOS experimental

```sh
assis build app.assis --target linux-x64 -o app-linux
assis build app.assis --target windows-x64 -o app-windows
assis build app.assis --target macos-x64 -o app-macos
```

Os formatos são ELF64 PIE, PE32+ e Mach-O 64-bit PIE. O Windows recebe `.exe`;
Linux/macOS normalmente não usam extensão. Ao transferir um arquivo do Windows
para Unix, execute `chmod +x app-linux` ou `chmod +x app-macos` se necessário.
`run` executa apenas o alvo do sistema hospedeiro.

O backend macOS x86_64 usa dyld e `/usr/lib/libSystem.B.dylib`, sem invocar
compilador C, assembler ou linker durante build. Memória, IO e relógios usam
funções públicas da libSystem. Não usa os números de syscall do Linux.
A libSystem é fornecida pelo sistema operacional, não redistribuída.

Formato, segmentos sem escrita/execução simultâneas, imports e entrada são
verificados por `test-usability.py`. A execução macOS depende do job específico
de CI; não foi executada neste computador Windows/Linux. Não há compilador
hospedeiro macOS pré-compilado neste pacote. Em Mac Intel, compile com `make`
(C11/Apple clang); os runtimes já estão embutidos.

Limites dos executáveis gerados: somente x86_64; sem ARM64 nativo, universal binary, assinatura,
notarização, DWARF Mach-O ou extern de usuário. Bibliotecas de rede/processos
com FFI precisam separar declarações usando `platform("macos-x64")`. Não há
promessa de execução em Apple Silicon/Rosetta sem validação nessa plataforma.

## Hosts ARM64 e GitHub Actions

O código-fonte do compilador também pode ser construído nativamente em Linux
ARM64 e macOS Apple Silicon. Nesses hosts, `check`, `ir` e `build` geram/analisam
os mesmos destinos **x86_64**. `run` e `test` informam a limitação antes de tentar
executar uma saída incompatível. `doctor` distingue a arquitetura do host dos
destinos. Isso ainda não implementa um backend ou runtime ARM64.

A matriz de CI usa `macos-15-intel` para execução nativa Intel,
`macos-15` para o compilador ARM64 com saídas x86_64 via Rosetta e
`ubuntu-24.04-arm` para o compilador ARM64 com saídas x86_64 via QEMU.
Os rótulos seguem a [documentação dos runners do GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
O job Apple Silicon verifica a disponibilidade de Rosetta e falha explicitamente
se ela estiver ausente. Não registra execução emulada como aprovação nativa ARM64.

`tools/test-portability.py` confere a arquitetura do host, a identificação do
compilador, análise/IR, rejeição de programas inválidos, os três formatos de
saída e execução com/sem otimização. Os JSON de CI registram o modo de execução,
hashes e casos aprovados; consulte sempre o resultado do commit em teste.

Referências primárias: [formato Mach-O da Apple](https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h)
e [carregador dyld](https://github.com/apple-oss-distributions/dyld).

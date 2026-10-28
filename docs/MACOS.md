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

Limites: somente x86_64; sem ARM64 nativo, universal binary, assinatura,
notarização, DWARF Mach-O ou extern de usuário. Bibliotecas de rede/processos
com FFI precisam separar declarações usando `platform("macos-x64")`. Não há
promessa de execução em Apple Silicon/Rosetta sem validação nessa plataforma.

Referências primárias: [formato Mach-O da Apple](https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h)
e [carregador dyld](https://github.com/apple-oss-distributions/dyld).

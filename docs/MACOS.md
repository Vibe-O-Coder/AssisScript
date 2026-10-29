# Destinos macOS Intel e Apple Silicon

```sh
assis build app.assis --target macos-x64 --symbols -o app-intel
assis build app.assis --target macos-arm64 --symbols -o app-apple-silicon
assis build app.assis --target macos-arm64 --app --symbols -o App.app
lldb app-apple-silicon
```

Os dois destinos são Mach-O PIE com runtime próprio e APIs públicas libSystem.
O destino ARM64 possui assinatura ad hoc SHA-256 embutida. `--symbols` incorpora
DWARF e tabela de símbolos nos dois destinos, além do mapa JSON. `--app` aplica
o ícone compilado v1 ao bundle. Não há chamada a compilador C ou linker durante
`assis build`. Os programas são de console; execute o binário do bundle por
`App.app/Contents/MacOS/program` para observar sua saída no terminal.

O compilador pode ser construído por Apple clang com `make -B all CC=clang`.
O instalador `sh instalar.sh` escolhe o binário Intel/ARM64 e rejeita pacote
incompatível. A extensão do editor escolhe o compilador da arquitetura nativa.
Extern de usuário usa a primeira biblioteca declarada em `extern`, que deve
ser uma dylib compatível com o macOS. Os módulos opcionais Linux/Windows não
são automaticamente convertidos em provedores macOS.

A matriz configura `macos-15-intel` e `macos-15` para execução e depuração
nativas, incluindo verificação de assinatura, DWARF e variáveis em LLDB.
Os dois jobs passaram nativamente na revisão `bb1605d`, no
[Actions 40847421481](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40847421481),
incluindo ABI C, arquivos e instalação offline. O job Apple Silicon executou
programas ARM64 e validou assinatura ad hoc, DWARF e variáveis em LLDB.
Hashes dos compiladores e relatórios estão em [VALIDACAO-TARGETS-V1.json](VALIDACAO-TARGETS-V1.json).

Detalhes da ABI, runtime, assinatura e limites: [ARM64-NATIVO.md](ARM64-NATIVO.md).

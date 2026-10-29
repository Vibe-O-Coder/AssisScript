# ARM64 nativo — P5-TARGET concluído, 29/10/2026

O compilador emite instruções AArch64 diretamente de TypedIR-v1 e produz ELF64
PIE Linux ARM64 e Mach-O PIE macOS ARM64. Nenhum programa x86_64, compilador C,
assembler ou linker é chamado pela instalação para gerar essas saídas.
Os executáveis têm runtime ARM64 próprio incorporado; QEMU é usado somente
na validação local deste computador x64. Os jobs remotos ARM64 usam execução
nativa e verificam a CPU dos arquivos antes de executá-los.

```sh
assis build app.assis --target linux-arm64 --symbols -o app-linux-arm64
assis build app.assis --target macos-arm64 --symbols -o app-macos-arm64
assis build app.assis --target macos-arm64 --app --symbols -o MinhaApp.app
```

`run` e `test` selecionam a arquitetura do host. Compilação cruzada fica em
`build`; tentar `run` de arquitetura diferente é rejeitado antes da emissão.
`--no-opt` usa o mesmo seletor ARM64 sem alocação de registradores, provas de
intervalos ou tail calls; o lowering ainda pode simplificar constantes;
no x64 permanece o emissor AST independente. Não há saída Windows ARM64.

## Contrato do backend e runtime

`src/arm64_emit.h` cobre valores tipados, endereços, memória, Copy/Move,
fatias, coleções, closures, variantes, chamadas diretas/indiretas/virtuais,
limpeza, tail calls, controle e scopes. x0 contém o resultado, x1 o operando
direito, x27 o estado do runtime e x29 o frame. A pilha permanece alinhada a
16 bytes; argumentos internos ocupam células de 16 bytes. Agregados usam
destino de retorno explícito. Registradores preservados x19–x22 recebem o
alocador existente, com salvamento/restauração e localizações DWARF corretas.
x18 permanece reservado. Não se afirma compatibilidade binária com a ABI
interna x64; as fontes e os formatos de inspeção da IR são compartilhados.

`src/runtime_arm64.c` é freestanding, sem libc no Linux. O runtime implementa
alocação em classes/slabs e mapeamentos grandes, checagens de heap/pilha,
diagnósticos, texto, representação hexadecimal IEEE-754, entrada/saída,
arquivos, argumentos, relógios e espera. O macOS usa funções públicas de
libSystem por stubs AAPCS64 e mantém estado mutável fora do segmento executável.
`tools/embed-arm64.py` constrói blobs PIC sem símbolos indefinidos ou relocations
pendentes. Clang/LLD/binutils são ferramentas de manutenção e não são incluídos
nos programas gerados. Use LLVM 18 para reproduzir os blobs desta revisão.

A ABI C escalar suporta registradores inteiros e SIMD independentes,
argumentos excedentes na pilha, conversões estreitas e callbacks síncronos.
Darwin usa o empacotamento natural de seus argumentos de pilha. O adaptador
`open` de libSystem transporta seu argumento variádico de modo pela pilha.
Callbacks verificam o intervalo da pilha e restauram o x27 pertencente ao C.
Agregados por valor e varargs de usuário continuam fora da ABI C delimitada.

## Formatos, símbolos e instalação

ELF ARM64 identifica EM_AARCH64 e usa o loader AArch64 quando há extern.
Relocations GLOB_DAT usam o identificador AArch64, não o x64. Mach-O identifica
CPU_TYPE_ARM64, alinha segmentos em páginas de 16 KiB e inclui assinatura
ad hoc SHA-256 com CodeDirectory produzido pelo próprio compilador. Não é
assinatura Developer ID ou notarização. `--symbols` incorpora linhas,
subprogramas, parâmetros, locais e scopes DWARF em ELF/Mach-O, além do mapa JSON.
O mapa macOS usa image base 0x100000000. Mach-O também contém nlist/symtab.
LLDB pode ler diretamente esses dados; não é necessário um dSYM separado.

`--app` cria uma pasta nova com Info.plist, executável ARM64 ou x64 assinado
no macOS ARM64 e `compiled.icns` v1. O executável de console também pode ser
chamado por `MinhaApp.app/Contents/MacOS/program`. A pasta não é sobrescrita.
ELF e o executável Mach-O avulso usam a apresentação de arquivos do sistema;
o ícone Finder por aplicação é fornecido pelo bundle `.app`.

O instalador offline seleciona Linux x64/ARM64 ou macOS Intel/Apple Silicon,
confere a identidade do compilador antes de copiá-lo e preserva `--minimal`,
`--with`, `--prefix` e `--no-path`. Os pacotes do Actions acrescentam os
compiladores `assis-linux-arm64`, `assis-macos-x64` e `assis-macos-arm64`.
O editor prefere o compilador correspondente ao sistema/arquitetura.

## Evidência e critério de conclusão

Validação local: execução real de instruções ARM64 via QEMU, biblioteca C
independente, comparação com os oráculos existentes, DWARF conferido pelo LLVM,
CodeDirectory conferido página a página por SHA-256 e GDB remoto conferindo
parâmetros, locais, shadowing e backtrace com e sem otimização. Logs de
desenvolvimento ficam em `build/review-tests` e não entram na distribuição.
O relatório `VALIDACAO-TARGETS-V1.json` registra hashes e limites desta rodada.

P5-TARGET foi concluído após os seis jobs do [Actions 40847421481](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40847421481)
passarem na revisão `bb1605d713e1862cac9ec8ba3c99a41a7b882bcf`: Linux x64,
Windows x64, Linux ARM64, macOS Intel, macOS Apple Silicon e empacotamento.
Os runners ARM64 executaram saída ARM64 nativamente; Linux ARM64 passou as
32 suítes / 296 casos com os prazos TLS nativos. GDB/LLDB conferiram parâmetros,
locais e backtrace; macOS passou DWARF, assinatura, ABI C, arquivos e instalação.
O pacote aprovado contém os cinco compiladores e a extensão offline.

As regressões incluem a largura dos retornos `int` das APIs C Darwin e a
separação dos segmentos `__DATA`/`__DWARF`, necessária para executar os Mach-O
com símbolos. O JSON mantém os hashes e os relatórios da execução aceita,
além da validação local anterior identificada como histórica.

Referências: [AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst),
[Mach-O](https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h),
[CodeDirectory](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/cs_blobs.h).

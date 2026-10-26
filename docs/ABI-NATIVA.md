# ABI interna x86_64 — versão LVS2, alpha.9

**Atualização alpha.9:** [Recursos/fatias e backend](RECURSOS-E-FATIAS.md) complementam os contratos abaixo: classes gerenciadas com receptor, slice<T>, texto UTF-8 com comprimento, vtable com drop e ELF PIE. [Handoff atual](HANDOFF-3.3-ALPHA.9.md).

Este documento especifica a convenção interna usada nos executáveis PE32+/ELF64 e os adaptadores OS existentes. Não estabelece uma ABI C pública ou estável. Não vincular objetos externos diretamente a estas funções. FFI, callbacks vindos de C e unwind continuam pendentes; P5-ABI recebe crédito parcial. Símbolos/linhas e locais escalares estão disponíveis no ELF/DWARF.

LVS2 acrescenta drop dinâmico no word anterior à vtable, entradas de vtable relativas ao próprio slot em ELF PIE e absolutas em PE, além de descritores slice<T> de 16 bytes passados pelo mecanismo de compostos. O receptor não é exposto como parâmetro adicional da API de método; participa da ABI e da vida dos retornos borrow(self). Não misturar executáveis/objetos gerados com LVS1 e LVS2; recompilar todas as aplicações.

## Valores, frames e chamadas

`int`: 64 bits com sinal modular; byte/bool: 8 bits em buffers; text/referências/classes/coleções/Arquivo/callbacks: um endereço de 64 bits. Campos de agregados são alinhados em slots de 8 bytes. Referências legadas iniciam com vtable de 8 bytes, depois campos herdados e próprios por ordem. Campos Copy compostos ocupam espaço inline. Ponteiros nunca entram em valores Copy; callbacks pure são endereços de código sem ambiente.

Registros por valor: soma dos slots dos campos, mínimo 8 bytes. Variantes: tag u64 pelo índice de declaração, seguida de payload; tamanho pelo maior payload alinhado. Preenchimento zerado é parte da representação canônica. Campos herdados preservam o offset calculado na base. Buffers usam o tamanho real do elemento; byte/bool mantêm passo um. O header privado do alocador mantém bytes solicitados a 16 bytes antes do endereço público; só referências gerenciadas podem consultar esse dado via len/bounds.

Os argumentos são avaliados da esquerda para a direita, com snapshot de cada valor composto. Cada argumento ocupa um word na pilha de chamada: escalar/endereço direto, ou endereço do snapshot para Copy composto. O callee copia imediatamente os compostos para seus próprios slots. Assim os parâmetros têm semântica por valor, não um empréstimo da memória do chamador.

Após `push rbp; mov rbp,rsp`, o último argumento está em rbp+16 e os anteriores seguem em ordem inversa a cada 8 bytes. Receptor de método é um argumento adicional antes dos explícitos; o vtable é consultado uma vez para despacho. Endereço de chamada indireta é avaliado antes dos argumentos e guardado fora da área dos argumentos; zero produz diagnóstico.

Retorno escalar/referência: RAX. Retorno composto: o chamador passa um destino oculto **antes** do receptor/argumentos; o callee o encontra em `rbp+16+8*quantidade_de_argumentos_incluindo_receptor`. Copia o valor antes da limpeza dos escopos e retorna esse destino em RAX. Na chamada indireta o endereço guardado do callback fica antes do destino oculto e não altera o offset do destino. Locais e temporários pertencem ao frame, nunca escapam como referência pública.

R15 é reservado ao runtime. O backend pode alocar escalares em RBX/R12/R13/R14 e salva/restaura esses registradores nos frames; funções de runtime preservam esses registradores. RAX/RCX/RDX/RSI/RDI/R8–R11 são temporários. Frames são arredondados a 16 bytes. Chamadas internas não prometem o alinhamento de entrada da ABI C; cada adaptador Win32 alinha a pilha e reserva shadow space próprio. Geração Windows toca as guard pages em frames grandes antes das chamadas. Verificação de pilha antecede a reserva do frame e vale também para helpers recursivos de destruição.

## Adaptadores

Linux: syscalls x86_64 usam RAX para número/resultado e RDI/RSI/RDX/R10/R8/R9 para argumentos, com RCX/R11 voláteis. openat usa O_CLOEXEC, leitura/escrita repetem EINTR; close não é repetido para evitar fechar um descritor reutilizado. Erros nativos permanecem recuperáveis. Arquivos anexados usam O_APPEND.

Windows: KERNEL32 fornece memória, console, arquivos e conversão UTF; SHELL32 fornece CommandLineToArgvW. Import tables têm descritores e terminadores separados para cada DLL. CreateFileW usa modos de abertura explícitos; append usa FILE_APPEND_DATA. Os adaptadores preservam os registradores internos e fazem chamadas com a ABI Microsoft, inclusive argumentos na pilha além do quarto. argv é liberado com LocalFree ao término normal.

São dependências do sistema, sem CRT adicionado ao executável gerado. O compilador distribuído mantém sua própria dependência de toolchain estática de build. O harness PE em Linux simula ambas as DLLs e testa base relocada; não substitui execução Windows real.

## Evidência e limites

`test-values.py`: escalares/compostos mistos, callbacks, retornos virtuais e genéricos, parâmetros por cópia, nested layouts, structs legadas com campos inline, igualdade, buffers/coleções e recursão. `test-files.py`: adaptadores reais, argumentos Unicode/aspas/backslashes, handles e liberação. `test-pe.sh`: fixtures PE anteriores com base relocada e stubs ABI Microsoft. Suites completas e reconstruções limpas estão no [relatório](VALIDACAO-3.3-ALPHA.7.md).

Inteiros de largura fixa e f32/f64 usam bits em um word nos argumentos/retornos escalares; o tamanho de armazenamento segue [NUMEROS.md](NUMEROS.md). Não há structs Move inline, registradores SIMD na ABI de argumentos, ABI externa C, exceções ou garantias para ARM/macOS. Alterar LVS2 requer nova versão de contrato, regressões e regeneração de todos os binários; não misturar artefatos antigos com o novo layout.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `tempo`, `log`, `iteradores` e `eventos` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

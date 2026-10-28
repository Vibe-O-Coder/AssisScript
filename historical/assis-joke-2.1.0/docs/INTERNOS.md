# Implementação do compilador nativo

Os compiladores são `bin/assis` (Linux) e `bin/assis.exe` (Windows), compilados de `src/assisc.c`. A implementação não embute Python, não transpila para C e não inicia processos auxiliares para compilar. O único processo filho criado pelo comando `run` é o programa do usuário.

## Frontend

O lexer preserva a capitalização e reconhece apenas palavras-chave e identificadores formados por Assis/Fodase. Inteiros são lidos como padrões de 64 bits. Textos preservam bytes UTF-8, com processamento dos escapes documentados.

O parser usa precedência para expressões. Declarações são resolvidas antes da verificação dos corpos, permitindo chamadas antecipadas, classes declaradas fora de ordem e recursão mútua.

A análise de tipos resolve variáveis em escopos lexicais, calcula posições de campos, valida herança, mantém slots de métodos e verifica retornos. Todo nó de expressão chega ao backend com tipo resolvido. Variáveis e campos são posições graváveis; textos indexados são valores imutáveis.

## Backend e formato de saída

`generate` emite bytes de instruções x86_64 diretamente em um buffer. Chamadas, saltos e endereços absolutos usam rótulos com correções aplicadas ao finalizar a imagem.

`write_executable` seleciona o formato; `write_elf` grava o cabeçalho ELF64 e quatro program headers:

| Segmento | Permissões | Conteúdo |
| --- | --- | --- |
| Cabeçalhos | Leitura | Cabeçalho ELF e tabela de segmentos |
| Código | Leitura e execução | Runtime, entrada e funções do programa |
| Dados constantes | Leitura | Textos e tabelas de métodos |
| Pilha GNU | Leitura e escrita | Declara a pilha não executável |

No Linux, o ponto de entrada chama `assis_assis` e encerra o processo com a syscall `exit`. A imagem não tem interpretador dinâmico, dependências compartilhadas ou tabela de seções obrigatória para execução. Esta versão usa endereço base fixo `0x400000` e não produz PIE.

## Saída Windows PE32+

O mesmo emissor de instruções usa `src/pe_writer.h` para gravar cabeçalhos DOS/PE, optional header PE32+, tabela de imports e relocations DIR64. As seções são `.text` (RX), `.rdata` (R), `.idata` (RW) e `.reloc` (R). A imagem habilita ASLR e DEP e não possui seções simultaneamente graváveis e executáveis.

O runtime Windows usa imports de KERNEL32: `WriteFile`, `GetStdHandle`, `VirtualAlloc`, `VirtualFree`, `SetConsoleOutputCP` e `ExitProcess`. Os deslocamentos RIP-relative das chamadas são corrigidos para os slots da IAT. Referências absolutas a textos e tabelas de métodos entram na tabela de relocations. Os executáveis gerados não dependem de CRT externa.

O host Windows lê argumentos com `wmain`, converte entre UTF-16 e UTF-8 para caminhos, usa APIs de arquivos Unicode e executa programas com `CreateProcessW`. O comando `run` espera o processo, aplica timeout com `TerminateProcess` e remove o diretório temporário. `--target` permite gerar ambos os formatos em qualquer host; a execução exige o formato nativo.

O compilador Windows e o instalador usam apenas DLLs padrão do sistema. A ligação estática de MinGW elimina dependências em DLLs de GCC ou pthread, sem remover os imports normais de Windows.

## Convenção de chamadas

As funções do usuário usam uma convenção interna, com argumentos de oito bytes passados na pilha. Os argumentos são avaliados e empilhados da esquerda para a direita. O último argumento fica mais próximo do endereço de retorno. Métodos recebem a referência `aSSIS` antes dos argumentos explícitos.

Cada função cria um frame com `rbp`, copia os parâmetros para slots locais e reserva oito bytes por variável. Resultados são devolvidos em `rax`. O acesso a um valor `AssiS` ou `FodAsE` usa um byte; inteiros, referências e ponteiros usam oito. Atribuições compostas calculam o endereço e leem o valor antigo antes de avaliar o lado direito.

O runtime recebe argumentos em registradores (`rdi`, `rsi` e, quando necessário, `rdx`), conforme cada rotina. Essa interface é interna; não existe FFI nem promessa de compatibilidade com chamadas C. Os adaptadores do runtime Windows alinham a pilha e reservam os 32 bytes de shadow space antes de chamar APIs Win32.

## Objetos e memória

Uma instância tem um ponteiro para sua tabela de métodos seguido por células de oito bytes para os campos. Campos herdados mantêm posição. Métodos sobrescritos substituem a função no mesmo slot da tabela. Assim, uma referência da base despacha para a implementação da classe real.

Cada alocação usa `mmap` no Linux ou `VirtualAlloc` no Windows e recebe um cabeçalho privado de 16 bytes. A referência devolvida aponta após esse cabeçalho. `foDASE` usa `munmap` ou `VirtualFree`. A versão atual faz uma chamada de mapeamento por alocação; não possui pool, coletor de lixo ou otimização de objetos pequenos.

Ponteiros são endereços reais. Não há metadados de limite ou validade de referências. Só nulo e índices de textos recebem verificações automáticas. A liberação só aceita conceitualmente o endereço original de uma alocação; o sistema de tipos não prova essa propriedade.

## Runtime incorporado

`src/runtime.S` implementa o runtime Linux. `src/runtime_win.S` implementa as mesmas operações com APIs Windows. `tools/embed-runtime.sh` gera os dois cabeçalhos incorporados e verifica relocations pendentes. As posições de imports do Windows são registradas para correção pelo emissor PE.

O cabeçalho já está incluído no pacote. Para reconstruir apenas o compilador, basta um compilador C com suporte à ligação estática. Binutils só é necessário para regenerar o runtime após editar o assembly.

## Validação desta entrega

- 128 verificações automatizadas aprovadas em Linux x86_64.
- 33 casos executáveis, incluindo os sete exemplos e um contrato de 256 operações aritméticas.
- 68 fontes inválidos rejeitados.
- Instalação, reinstalação, PATH e remoção testados com HOME isolado.
- Compilação e execução testadas com PATH sem ferramentas.
- Compilador e saída ELF inspecionados sem `PT_INTERP`.
- Segmentos de saída inspecionados sem permissão simultânea de escrita e execução.

- Binários `assis.exe` e `assis-setup.exe` compilados com MinGW-w64 e imports inspecionados.
- 33 casos PE executados com ABI Microsoft, base relocada, stubs Win32 e proteção de seções.
- A execução em Windows real, incluindo integração do instalador com o PATH, ainda precisa de validação. A suíte `tests/test-windows.cmd` foi incluída para isso. Wine não pôde iniciar neste ambiente.
- Não há binários nativos macOS ou ARM.

## Referências de implementação

- [Formato PE/COFF da Microsoft](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
- [Convenção de chamadas x64](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention).
- [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
- [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc).
- [WriteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile).

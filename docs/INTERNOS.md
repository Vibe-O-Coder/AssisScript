# Implementação 3.3.0-alpha.6

**Atualização alpha.10:** sintaxe e APIs canônicas em inglês; imports e nomes antigos da stdlib exigem migração. Veja [ENGLISH-API.md](ENGLISH-API.md) e o [handoff atual](HANDOFF-3.3-ALPHA.10.md). A alpha.14 removeu as grafias históricas; consulte o manual atual.

**Atualização alpha.9:** [Recursos/fatias e backend](RECURSOS-E-FATIAS.md) complementam os contratos abaixo: classes gerenciadas com receptor, slice<T>, texto UTF-8 com comprimento, vtable com drop e ELF PIE. [Handoff atual](HANDOFF-3.3-ALPHA.9.md).

O fluxo agora inclui check_ownership e check_safety após tipos/pureza e antes de qualquer emissão. TypeRef conserva modos dos parâmetros, modo/origem do retorno e efeito safe, com igualdade/caches estruturais. Clonagem de templates preserva esses metadados por identidade.

ownership.h acompanha lugares (variáveis/campos own), estados de consumo e empréstimos lexicais/temporários. Campos compartilham o bloqueio da raiz; a análise reserva endereços durante atribuições e une apenas caminhos que continuam. Helpers por struct concreta destroem campos em ordem inversa; move/free zeram a posição, inclusive em campos, permitindo limpeza de movimentos parciais. Os helpers verificam a pilha. Buffers derivados de campos/retornos preservam a marca de indexação verificada.

safety.h verifica funções safe e exige fronteiras unsafe para operações legadas. A marca safe integra os tipos de função; não apaga efeitos nem contratos de propriedade. O perfil exclui classes e text externo. O runtime e a ABI de ponteiros não mudaram. [Contratos atuais](OWNERSHIP-FUNCOES.md).

# Implementação 3.3.0-alpha.5 — histórico

Array/HashMap agora passam pela rotina instantiate_class do especializador AST. src/collections.h conserva apenas fontes genéricos confiáveis e seu carregamento único; não há replace_template, fonte concreto gerado por instância ou serialização de Type para reanálise. Hash de texto e hash de inteiro são escolhidos por tipo entre ASTs previamente analisadas. O cache de Collection publica a classe nominal concreta antes de resolver os membros, com o mesmo TypeRef/DefId usado pela resolução de Array/HashMap. Instâncias intrínsecas mantêm orçamento separado, sem consumir entradas do usuário nem níveis de expansão por implementação interna. Métodos usam o owner concreto e seguem a fila comum. Layout/ABI/bounds/hashing/cleanup permanecem iguais.

Classes genéricas usam o cache nominal dos registros. A especialização publica uma classe vazia antes de resolver bases/campos e clonar ASTs dos métodos, permitindo referências recursivas finitas. Cada método recebe owner concreto, assinatura substituída, origem e profundidade de expansão. Corpos entram na mesma fila de funções antes de check/ownership/emissão. O parser conserva o escopo dos parâmetros da classe dentro dos métodos, e bases são tipos estruturados, resolvidos antes do layout. A profundidade acompanha também a expansão que atravessa corpos de métodos na fila. O layout/vtable/ABI existentes são preservados. Não há parâmetros de tipo próprios em métodos, ownership de classes ou desvirtualização novos.

TypeRef representa aplicações de tipo e tipos de função, estes com parâmetros, retorno e efeito. DefId identifica declarações/parâmetros genéricos; TypeId usa igualdade estrutural para funções, incluindo efeitos, e nominal para objetos. `src/generics.h` guarda/clona AST, substitui tipos por identidade e esgota a fila de especializações antes de tipagem/ownership/emissão. A antiga serialização de tipos para fonte intrínseco foi removida; tipos extensos conservam a estrutura completa, enquanto os diagnósticos mantêm um buffer limitado.

N_NAME pode resolver uma variável lexical ou uma função global; especializações explícitas resolvem também como valores. O verificador de chamada distingue método, função global direta e expressão com tipo de função. Funções sem captura são endereços de código com vida de programa. A emissão indireta salva o endereço antes dos argumentos, avalia cada argumento da esquerda para a direita e chama o endereço salvo com a ABI interna existente. Nenhuma captura, objeto de closure ou thunk para FFI é gerado.

O contrato de atribuição aceita função pure em tipo comum com assinatura interna idêntica; não remove efeitos no sentido inverso nem aplica variância nos parâmetros/retorno. Pure agora aceita escalares/funções pure recursivamente. O verificador simbólico de templates pure conserva vínculos por escopo para conferir chamadas de callbacks e shadowing, antes da verificação concreta de cada instância. Ownership também percorre a expressão do callee nas chamadas indiretas; referências gerenciadas continuam sem escape por argumentos. [Contratos](FUNCOES-E-EFEITOS.md).

# Implementação 3.3 alpha.1 — histórico

Field guarda a classe declaradora e privacidade; Function guarda privacidade e pureza; Var/Node guardam imutabilidade. O verificador comum aplica essas regras antes da emissão. A identidade usada no acesso privado é o ponteiro para a declaração Class, e a confiança dos fontes intrínsecos vem de SourceFile.internal, sem comparação de caminhos. Os templates de coleções declaram explicitamente seus membros privados. A passagem de ownership continua após tipagem. Não há alteração de layout, ABI ou runtime para val/pure/private.

Assinaturas pure aceitam somente int/byte/bool; parâmetros são imutáveis. O verificador de corpo rejeita efeitos e chamadas a funções sem a anotação, incluindo funções não usadas. Estado escalar local não escapa; não há ponteiros nem estado global nesse subconjunto. As novas propriedades não comandam otimizações. A futura representação estruturada de tipos deverá incluir efeitos e variáveis genéricas; esta alpha não implementa essa infraestrutura.

# Implementação 3.2

`src/ownership.h` verifica ownership local em uma passagem posterior à tipagem. A emissão mantém uma pilha lexical de limpezas e insere liberações em saídas normais, retornos e desvios de laços. Até quatro escalares frequentes sem endereço exposto usam RBX/R12/R13/R14, salvos por função; R15 é reservado ao estado do runtime. Textos locais e parâmetros guardam comprimento em slot adicional; referências ao endereço da variável desabilitam esse cache. Comparações geram desvios diretos, divisões por potências de dois respeitam truncamento com sinal e testes de resto zero podem usar máscara. O runtime inclui entrada por bytes, relógio monotônico e proteção conservadora da pilha. [Detalhes](MELHORIAS-3.2.md).

As seções anteriores a 3.2 abaixo descrevem a evolução do projeto; suas convenções históricas de alocação e variáveis na pilha foram atualizadas.

# Alterações internas da versão 3.1

O backend dobra constantes puras usando uint64_t para overflow modular, preserva curto-circuito e deixa divisões/deslocamentos inválidos para os erros de execução. Variáveis locais usam carga direta e operandos simples podem ser carregados em RCX sem salvar RAX na pilha. A atribuição composta continua capturando o valor antigo antes dos efeitos do lado direito. Imediatos usam a forma curta quando a extensão de sinal/zero preserva os 64 bits. `--no-opt` conserva o caminho de emissão anterior para comparação.

Quadros locais Windows com pelo menos uma página crescem tocando cada página de guarda antes de executar o corpo. Isso permite funções grandes com uma chamada antes da inicialização de suas variáveis, sem saltar a página de crescimento da pilha. O teste cobre 6.000 variáveis em ambos os modos de otimização.

HashMap usa máscara nas sondagens porque suas capacidades são potências de dois; _rehash valida essa precondição. Tombstones podem ser limpos sem crescimento quando o número de entradas ativas é pequeno. Hash de text e bibliotecas de texto usam visões emprestadas de bytes limitadas por comprimento, evitando a varredura repetida da indexação pública de text. Essas primitivas não adicionam verificação de vida útil aos ponteiros.

Os diagnósticos acrescentam hint, severity e endColumn. assert aceita mensagem avaliada apenas no caminho de falha. As bibliotecas são fontes que passam pelo mesmo verificador e emissor nativo, com contratos de propriedade documentados. O catálogo de instalação e documentação fica em stdlib/catalogo.json.

A análise léxica aceita a sintaxe canônica e identificadores ASCII. import é expandido pelo carregador de módulos antes da análise sintática, com proteção contra ciclos e repetição. Agregadores .pillow também usam import. Aliases e diretivas históricas foram removidos na alpha.14.

Array e HashMap são monomorfizados por combinação de tipos. src/collections.h gera classes internas no módulo virtual <colecoes>; elas passam pelo mesmo parser, verificador de tipos e backend x64. Não há interpretador. O prefixo __assis_ é reservado.

Array guarda tamanho, capacidade e ponteiro para dados. A indexação gera comparação sem sinal com tamanho, rejeitando também negativos. Literais usam o tipo esperado de declaração, argumento, atribuição, campo ou retorno. HashMap usa sondagem linear, estados vazio/ocupado/removido e crescimento com rehash.

Struct reutiliza o layout de referências de objetos, sem métodos e sem herança. Seu construtor aceita zero valores ou um por campo. Não há ABI C, cópia por valor nem descarte automático dos membros.

alloc<T> valida quantidade e overflow de bytes. free de coleção chama dispose antes de liberar a instância. A liberação de elementos continua manual.

O emissor PE acrescenta .rsrc com RT_ICON e RT_GROUP_ICON. src/icon_blob.h é gerado de assets/compiled.ico por tools/build-icons.py. Os dois originais fornecidos são preservados em assets/.

A extensão usa src/reference.json para intrínsecos e métodos de coleções. Documentação de funções é extraída de comentários do código, incluindo bibliotecas transitivas em .pillow. O empacotador inclui stdlib e todos os manuais para uso offline.

---

# Implementação do compilador nativo

Os compiladores são `bin/assis` (Linux) e `bin/assis.exe` (Windows), compilados de `src/assisc.c`. A implementação não embute Python, não transpila para C e não inicia processos auxiliares para compilar. O único processo filho criado pelo comando `run` é o programa do usuário.

## Frontend

O lexer preserva a capitalização e reconhece palavras-chave e identificadores ASCII livres. Inteiros são lidos como padrões de 64 bits. Textos preservam bytes UTF-8, com processamento dos escapes documentados.

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

No Linux, o ponto de entrada chama `main` e encerra o processo com a syscall `exit`. A imagem não tem interpretador dinâmico, dependências compartilhadas ou tabela de seções obrigatória para execução. Esta versão usa endereço base fixo `0x400000` e não produz PIE.

## Saída Windows PE32+

O mesmo emissor de instruções usa `src/pe_writer.h` para gravar cabeçalhos DOS/PE, optional header PE32+, tabela de imports e relocations DIR64. As seções são `.text` (RX), `.rdata` (R), `.idata` (RW), `.reloc` (R) e `.rsrc` (R). A imagem habilita ASLR e DEP e não possui seções simultaneamente graváveis e executáveis.

O runtime Windows usa imports de KERNEL32: `WriteFile`, `GetStdHandle`, `VirtualAlloc`, `VirtualFree`, `SetConsoleOutputCP` e `ExitProcess`. Os deslocamentos RIP-relative das chamadas são corrigidos para os slots da IAT. Referências absolutas a textos e tabelas de métodos entram na tabela de relocations. Os executáveis gerados não dependem de CRT externa.

O host Windows lê argumentos com `wmain`, converte entre UTF-16 e UTF-8 para caminhos, usa APIs de arquivos Unicode e executa programas com `CreateProcessW`. O comando `run` espera o processo, aplica timeout com `TerminateProcess` e remove o diretório temporário. `--target` permite gerar ambos os formatos em qualquer host; a execução exige o formato nativo.

O compilador Windows e o instalador usam apenas DLLs padrão do sistema. A ligação estática de MinGW elimina dependências em DLLs de GCC ou pthread, sem remover os imports normais de Windows.

## Convenção de chamadas

As funções do usuário usam uma convenção interna, com argumentos de oito bytes passados na pilha. Os argumentos são avaliados e empilhados da esquerda para a direita. O último argumento fica mais próximo do endereço de retorno. Métodos recebem a referência `self` antes dos argumentos explícitos.

Cada função cria um frame com `rbp`, copia os parâmetros para slots locais e reserva oito bytes por variável. Resultados são devolvidos em `rax`. O acesso a um valor `byte` ou `bool` usa um byte; inteiros, referências e ponteiros usam oito. Atribuições compostas calculam o endereço e leem o valor antigo antes de avaliar o lado direito.

O runtime recebe argumentos em registradores (`rdi`, `rsi` e, quando necessário, `rdx`), conforme cada rotina. Essa interface é interna; não existe FFI nem promessa de compatibilidade com chamadas C. Os adaptadores do runtime Windows alinham a pilha e reservam os 32 bytes de shadow space antes de chamar APIs Win32.

## Objetos e memória

Uma instância tem um ponteiro para sua tabela de métodos seguido por células de oito bytes para os campos. Campos herdados mantêm posição. Métodos sobrescritos substituem a função no mesmo slot da tabela. Assim, uma referência da base despacha para a implementação da classe real.

Na versão 3.2, o alocador em runtime_memory.inc usa classes de tamanho e slabs de 64 KiB, com cabeçalho de 32 bytes e metadados em estado separado apontado por R15. Blocos pequenos voltam a listas livres; grandes usam mmap/VirtualAlloc diretamente. Não há GC. Confira os limites e diagnósticos em MEMORIA-OWNERSHIP.md.

Ponteiros são endereços reais. Não há metadados de limite ou validade de referências. Só nulo e índices de textos recebem verificações automáticas. A liberação só aceita conceitualmente o endereço original de uma alocação; o sistema de tipos não prova essa propriedade.

## Runtime incorporado

`src/runtime.S` implementa o runtime Linux. `src/runtime_win.S` implementa as mesmas operações com APIs Windows. `tools/embed-runtime.sh` gera os dois cabeçalhos incorporados e verifica relocations pendentes. As posições de imports do Windows são registradas para correção pelo emissor PE.

O cabeçalho já está incluído no pacote. Para reconstruir apenas o compilador, basta um compilador C com suporte à ligação estática. Binutils só é necessário para regenerar o runtime após editar o assembly.

## Validação da versão 2.2

- 133 verificações da suíte principal aprovadas em Linux x86_64 e 10 adicionais de módulos.
- 35 casos executáveis, incluindo comentários, bibliotecas e um contrato de 256 operações aritméticas.
- 71 fontes inválidos rejeitados.
- Instalação, reinstalação, PATH e remoção testados com HOME isolado.
- Compilação e execução testadas com PATH sem ferramentas.
- Compilador e saída ELF inspecionados sem `PT_INTERP`.
- Segmentos de saída inspecionados sem permissão simultânea de escrita e execução.

- Binários `assis.exe` e `assis-setup.exe` compilados com MinGW-w64 e imports inspecionados.
- 35 casos PE executados com ABI Microsoft, base relocada, stubs Win32 e proteção de seções.
- 128 verificações aprovadas em Windows x64 real. Instalação/remoção são testadas com `--no-path`, sem alterar o registro do usuário; a integração global com o PATH não faz parte dessa suíte.
- 15 testes de integração/desenvolvimento em Node e 13 verificações dentro de um VSCode real. Veja [VALIDACAO.md](VALIDACAO.md).
- Não há binários nativos macOS ou ARM.

## Módulos e integração com o editor

`src/modules.h` resolve importações, mantém os fontes e suas posições, detecta ciclos e elimina inclusões repetidas pela identidade dos arquivos. A expansão produz marcadores de fim de módulo para impedir que um arquivo incompleto consuma tokens de outro. O parser e a análise de tipos continuam compartilhados; o backend gera um único executável.

`check --library` permite verificar módulos sem entrada. `check --stdin` recebe o documento do editor. `--overlay caminho-lógico snapshot` substitui o conteúdo de dependências apenas para a verificação. `--diagnostics=json` retorna o primeiro erro com código, mensagem, caminho, linha e coluna UTF-16, com índices começando em 1. Falhas de arquivo/configuração usam A002; erros de linguagem usam A001. O sucesso de check em JSON emite `{"ok":true}` em stdout. Nenhum desses modos executa o programa.

Os runtimes aceitam uma linha numérica para programas de um arquivo ou um ponteiro marcado para uma string `arquivo:linha` em programas com módulos. O emissor inclui a string nos dados e corrige sua referência por relocations normais; o bit de marcação é aplicado apenas em execução. Isso mantém a identificação do módulo quando o executável é distribuído sem os fontes.

A extensão em `vscode-assisscript/src` usa a API de linguagem do VSCode. `language.js` fornece análise tolerante para sugestões/navegação; `extension.js` chama o compilador para diagnósticos, com cancelamento e snapshots de dependências não salvas. As tarefas usam argumentos de processo separados, sem concatenar comandos de shell.

## Referências de implementação

- [Formato PE/COFF da Microsoft](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
- [Convenção de chamadas x64](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention).
- [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
- [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc).
- [WriteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile).

## Continuação alpha.15

[ScalarIR e registradores](BACKEND-ALPHA15.md): expression_ir.h/expression_emit.h separam valores escalares da AST; registers.h calcula liveness no CFG e reutiliza registradores preservados. Recursos e emissão de instruções ainda estão em migração.

# ABI C e recursos externos — alpha.11

`extern("biblioteca-linux", "dll-windows", "simbolo") fn nome(...): tipo;`
declara uma dependência explícita. O nome AssisScript pode diferir do símbolo C
e participar de namespace/visibilidade. Duas declarações do mesmo símbolo na
mesma biblioteca compartilham o import. Não existe busca/download de pacotes
durante a compilação nem compilador C necessário para executar o programa.

```assis
extern("libc.so.6", "msvcrt.dll", "abs") fn c_abs(value: i32): i32;
safe fn main(): int {
    unsafe { print(int(c_abs(i32(-42)))); }
    return 0;
}
```

O backend gera uma ponte da ABI interna LVS2 para System V AMD64 no Linux ou
Microsoft x64 no Windows. Argumentos são avaliados uma vez, da esquerda para
a direita. Inteiros/ponteiros e reais usam as classes de registradores da
plataforma, com spill ordenado, shadow space Microsoft e alinhamento de 16 bytes
antes da chamada. f32/f64 usam XMM; os retornos voltam ao formato interno de
bits. Valores menores são normalizados, inclusive na entrada de callbacks.

São aceitos até 64 parâmetros escalares, `text` C e ponteiros. Parâmetros de
buffer podem declarar `borrow`/`borrow mut`; o contrato externo é confiado ao
autor da fronteira unsafe. O compilador preserva as regras de exclusividade,
mas não verifica o código da biblioteca nem a assinatura real do símbolo.
Não são aceitos agregados AssisScript por valor, own, referências de classes,
File, slice, métodos ou templates extern. Use buffers com layout C definido
explicitamente quando precisar transportar estruturas. Um ponteiro retornado
por C não se torna uma alocação do runtime: não o passe para `free`/`own`.

Os tipos inteiros têm largura explícita; `int` tem 64 bits, não é o `int` de C.
O `long` tem 64 bits no Linux e 32 no Windows. A declaração precisa refletir a
ABI de destino. Funções variádicas só podem ser especializadas para argumentos
inteiros/ponteiros representados nos slots C; não há promoções automáticas,
varargs reais, `va_list`, long double, vetores ou structs C por valor.

## Carregamento e dependências

Windows: imports PE por DLL, preservando KERNEL32/SHELL32, ASLR, relocations e
código sem escrita. Linux: somente programas com extern/callback passam a usar
o loader glibc x86_64 `/lib64/ld-linux-x86-64.so.2`. ELF continua PIE; símbolos
externos usam GLOB_DAT com resolução imediata e GOT protegida por GNU_RELRO.
Uma página separada, sem execução, guarda o estado para callbacks. Programas
sem esses recursos continuam freestanding. Dependência ou símbolo ausente é
erro do loader antes de main; não é erro recuperável de `http::get`.

O compilador não fornece loader musl nem busca versionada de bibliotecas C.
Em ELF, o mesmo símbolo em bibliotecas diferentes é ambíguo e rejeitado;
interposição e resolução transitiva seguem o loader do sistema. Dependências
devem ser confiáveis e fazer parte da instalação declarada da aplicação.

## Callbacks

`c_callback(funcao_global)` produz um endereço `u64` de ponte C. A função deve
ter assinatura escalar sem ownership e existir estaticamente no executável.
Pode ser uma especialização concreta; variáveis locais e closures não são
aceitas. A ponte salva o R15 de C, recupera o estado do runtime e restaura R15
ao sair, inclusive em chamadas C aninhadas. Registradores não voláteis Windows
usados pela ABI interna também são preservados.

O contrato é **callback síncrono na thread principal**, com pilha dentro do
intervalo do runtime. Não registrar em APIs assíncronas ou em threads externas.
Não há TLS de runtime por thread, unwind C/C++, longjmp ou tratamento de
exceções atravessando a fronteira. C não pode guardar dados emprestados além da
vida mantida pelo adaptador. A API HTTP mantém explicitamente seu buffer vivo
até terminar a operação e destruir o handle.

## Destruição de handles

Uma `final class` pode declarar `fn drop(borrow mut self): void`. O compilador
chama esse método antes de destruir campos own na ordem inversa. A ponte de
drop dinâmico continua liberando a instância. O método não recebe argumentos,
não retorna valor e chamadas manuais são rejeitadas; classes não finais não
podem declarar drop. Use campos escalares privados para handles e feche-os em
drop pelo adaptador correto. Inicialização zero, falha de abertura e valores
inválidos devem ser tratados pelo adaptador. Move/retorno/free continuam afins.
Consumo parcial de campos de uma classe com drop é rejeitado fora do próprio
destrutor, mantendo válidas as referências que o método pode observar.

Não há limpeza após abort fatal, falha de hardware ou morte abrupta do processo.
Recursos do OS são recuperados por ele; dados persistentes exigem protocolo
próprio. `process::Lock` usa locks do OS que são liberados ao terminar o processo.

## Seleção de plataforma

`platform("linux-x64") { declarações }` e
`platform("windows-x64") { declarações }` são selecionados antes da resolução
de nomes. Não aceitam namespace ou outro platform dentro do bloco. Coloque
namespace antes dos blocos. Imports de fontes continuam resolvidos normalmente;
não se trata de um pré-processador geral. Ambos os ramos precisam de validação
com seu destino: verificar um destino não verifica o ramo excluído.

## Validação

`tests/test-ffi.py` compila uma biblioteca C independente e exercita as duas
ABIs nativas: classes de argumentos esgotadas separadamente, pilha, misturas
int/f32/f64, retornos, normalização, funções como valores, callbacks aninhados,
R15 ocupado por C e destruição em retorno/ramo/move/free. Rejeições são testadas
em check/build/run, com e sem otimizações, antes de executar código.

Referências: [Microsoft x64](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention),
[System V AMD64 ABI](https://gitlab.com/x86-psABIs/x86-64-ABI).

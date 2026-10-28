# Ownership, borrowing e div — AssisScript 3.3.0-alpha.6

O modelo afim verifica locais, parâmetros/retornos, reempréstimos, funções como valores e campos own de structs. Recursos são limpos em ordem inversa no fim do bloco, return, break e continue; transferências zeram a origem. Não há GC nem contagem de referências.

Leia [Ownership entre funções](OWNERSHIP-FUNCOES.md) para sintaxe, exemplos, exclusividade, relação de vidas, fluxo, movimentos parciais e perfil safe/unsafe. O [exemplo 14](../exemplos/14_ownership.assis) preserva os escopos originais; o [exemplo 19](../exemplos/19_ownership_funcoes.assis) demonstra APIs funcionais gerenciadas e recursos compostos.

`{ ... }` equivale a um bloco lexical; não produz HTML. `defer free(nome)` permanece uma ferramenta manual para variáveis legadas estáveis, sem prova retroativa dos aliases existentes. Use own para impedir a criação desses aliases. Funções safe exigem unsafe para esse defer manual.

O modelo continua conservador em laços e empréstimos lexicais; classes/Texto, proprietários em coleções, texto externo e valores compostos por valor permanecem limitados. Falhas fatais não desenrolam escopos. A [régua de progresso](PROGRESSO.md) separa a auditoria do subconjunto gerenciado das etapas ainda abertas.

## Alocador e diagnóstico

O runtime usa dez classes de 64 a 32.768 bytes, incluindo cabeçalho de 32 bytes, com slabs de 64 KiB. Alocações maiores usam `mmap`/`VirtualAlloc` diretamente. Blocos reutilizados têm os bytes solicitados zerados. Slabs permanecem até o fim do processo: memória liberada é reutilizada, mas não necessariamente devolvida ao sistema imediatamente. O runtime atual é de uma única thread.

```text
assis run exemplos/14_ownership.assis --debug
```

`--debug` preenche os bytes solicitados de blocos liberados com `0xDD` e verifica o total de alocações ainda vivas ao sair. Um total não zero produz diagnóstico e status 70. Free duplo de um bloco pequeno ainda não reutilizado é detectado também sem debug; o modo debug retém blocos grandes liberados para diagnosticar repetição. Esses metadados não validam qualquer endereço arbitrário e não detectam todo acesso por ponteiro legado ou free de um endereço já reciclado para outra alocação. O diagnóstico de vazamentos é agregado, sem lista de locais de alocação.

A entrada das funções verifica o espaço restante antes de reservar variáveis locais. O limite conservador é 512 KiB no Windows e 4 MiB no Linux, com margem para emitir mensagem e status 70. Isso não é tratamento de sinais nem garantia para código externo; o limite pode rejeitar recursão que caberia numa pilha configurada maior.

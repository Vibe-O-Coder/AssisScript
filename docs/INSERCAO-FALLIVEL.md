# Objetos e inserções recuperáveis — M1

Continuação de 30/10/2026, E02-03 e obrigações E01-03/E01-04/E01-05.
Requer reconstruir compilador e aplicações; não promove uma release alpha.15.

## try_new

`try_new Type(args)` tem o tipo de objeto e as regras de acesso, genéricos,
ownership e empréstimos de new. Aceita classes, structs gerenciadas e enums
Move. Não aceita value struct nem enum Copy, cuja construção new usa o frame
sem alocação. A falha é null, sem alocar objeto de erro. Exige destino own em
safe e conserva o efeito de alocação; não é permitido em pure.

1. Tenta reservar o objeto zerado pelo alocador gerenciado existente.
2. Avalia **todos** os argumentos uma vez, da esquerda para a direita, mesmo
   se essa reserva foi recusada. Argumentos own são consumidos nos dois casos.
3. Em sucesso inicializa vtable/tag/campos e chama init quando declarado.
4. Em recusa destrói os argumentos own em ordem inversa e retorna null.
   Não publica objeto, não chama init/drop do objeto inexistente e não altera
   o contador de blocos vivos. Argumentos emprestados/Copy não são destruídos.

O chamador que precisa preservar o recurso após recusa deve reservar primeiro
um objeto vazio e só transferir campos own após verificar null. Não se admite
concluir que o recurso original continuou vivo depois de passá-lo por move.

```assis
struct Entry{let number:int;own data:*byte;}
safe fn main():int{
    own entry:Entry=try_new Entry();
    if(entry==null){return 1;}
    entry.data=try_alloc<byte>(16);
    if(entry.data==null){return 1;}
    entry.number=42;print(entry.number);return 0;
}
```

O contrato cobre a **reserva inicial**. Alocações nos argumentos e em init,
trap, pilha e inicialização do runtime mantêm seus próprios contratos. Por
exemplo, try_new Arena(...) pode reservar o controlador com sucesso e depois
encerrar por OOM no new usado dentro de init. Não existe unwind/catch de OOM.
Use argumentos já reservados ou operações try quando precisar de recuperação.
new/alloc antigos mantêm comportamento fatal. Nenhum provider é necessário
em produção; try_new chama RT_try_alloc com o layout gerenciado já existente.

## OwnedArray.try_push

`try_push(own value:T):bool` é implementação AssisScript. Prepara cada ramo
ausente com try_new antes de ligá-lo ao índice vivo. Em crescimento de raiz,
prepara a raiz e o novo caminho antes de transferir a raiz anterior.

False destrói o valor consumido e os candidatos uma vez; não muda tamanho,
capacidade lógica, ordem nem recursos anteriores. True transfere o valor ao
novo último índice. Operações e rollback custam O(log capacidade), sem reserve
amortizado nem promessa de buffer contíguo. Recusa crescimento que estouraria
a capacidade inteira positiva. A criação do controlador e APIs antigas não
recebem recuperação implicitamente. Não há teto de bytes compartilhado.

## Arena.try_insert

`try_insert(own value:T):arena::InsertStatus` retorna enum Copy no frame:
Inserted(Handle) ou Rejected(int). Códigos: 1 instância fechada; 2 limite de
slots; 3 recusa do alocador. Na rejeição o recurso é destruído e count,
free_head, slots_used, metadados e handles anteriores permanecem válidos.

Reutilizar slot livre não aloca. Criar slot reserva o Slot e o caminho da
OwnedArray antes de publicar a inserção. Nenhuma alocação é necessária para
relatar erro. Categoria/instância/geração e aposentadoria sem wrap seguem o
contrato da arena. O limite é de slots, incluindo aposentados, não de memória.
insert antigo devolve o recurso rejeitado em um resultado own e continua fatal
em OOM; try_insert consome e destrói em recusa. remove também ainda aloca seu
resultado own. Não há quota global nem recuperação completa do documento.

## Testes e limites

`tests/test-fallible-slots.py` usa modelo Python de lista (240 operações,
seed 20261030), milhares de inserções/remoções, efeitos, genéricos, herança,
empréstimos, variantes Move e contador de blocos vivos nos dois modos.
Um teste injeta recusa de novas reservas de slabs no OS, drena as listas livres
com buffers de teste e devolve exatamente k blocos antes da operação. Assim
cada posição de falha de crescimento é exercitada e comparada ao sucesso.
O caso de arena drena classes distintas para Slot e ramos e confere vizinhos.

Windows usa somente a tabela de imports de VirtualAlloc do próprio executável
de teste; Linux instala um filtro seccomp no filho após preparar o estado.
Fixtures C pertencem aos testes, nunca ao runtime/provider distribuído. Não
alteram código executável nem certificam sandbox de página. Reservas bem
sucedidas ainda não garantem sobrevivência ao OOM killer/overcommit.

Resultados por sistema, hashes e publicação estão no
[relatório](relatorios/2026-10-30-m1-slots-falliveis.md). Execução nativa
macOS/ARM64, quotas totais, callbacks, Browser e carga de 24h continuam abertos.

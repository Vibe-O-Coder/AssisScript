# Alocação recuperável — primeira fatia M1

Continuação de desenvolvimento de 29/10/2026, E02-03. Requer reconstruir o
compilador e recompilar os programas. Os pacotes alpha.15 anteriores conservam
seus hashes e não oferecem automaticamente esta API. Nenhuma release é promovida.

## Contrato de try_alloc

`try_alloc<T>(count)` usa a mesma forma de tipos de `alloc<T>`, retorna `*T`
gerenciado e exige destino `own` em safe. Não cria um objeto de erro no heap.

- Sucesso: buffer zerado, cabeçalho de capacidade, bounds, empréstimos,
  transferência e destruição iguais aos de `alloc<T>`.
- Falha: `null` para quantidade negativa, multiplicação/header fora da faixa
  representável ou recusa da reserva pelo sistema. Não altera os blocos vivos
  nem consome um bloco da lista livre. Não distingue esses motivos por código.
- `count == 0`: tenta criar um buffer vazio válido; também pode retornar null.
  `len` de um buffer vazio válido é zero. `len(null)` e indexar null continuam
  erros de contrato, com diagnóstico e saída 70.
- Avalia count uma vez. Generics especializam T como em alloc. Não é pure;
  sua falha depende de estado externo e a operação conserva o efeito de alocação.
- `alloc<T>` e `new` mantêm seus contratos fatais. A inicialização do estado do
  runtime também pode encerrar o processo antes de main. Esta entrega não
  permite capturar toda falha de memória da linguagem.

```assis
safe fn main():int {
    own data:*int=try_alloc<int>(64);
    if(data==null){return 1;}
    data[0]=42;print(data[0]);return 0;
}
```

O requisito não pode ser atendido por FFI de malloc isolada: o buffer precisa
do cabeçalho, bounds e drop do próprio runtime. Por isso a mudança adiciona
uma API intrínseca, sem alterar a gramática geral, o perfil numérico ou as
regras de ownership. Os runtimes x64 compartilham o caminho de alocação; ARM64
usa o mesmo helper para as versões fatal e recuperável. Nenhum hook de teste
ou configuração de falha foi acrescentado à API de produção.

## ByteBuffer e limite por instância

`import "std/memory.assis";` oferece `ByteBuffer`, implementado em AssisScript:

| Operação | Resultado |
| --- | --- |
| `new ByteBuffer(max_bytes)` | Controlador com tamanho/capacidade zero; exige limite não negativo. A criação do controlador ainda usa new fatal. |
| `try_reserve(capacity):bool` | Reserva exata sem alterar tamanho; false mantém bytes, tamanho e capacidade. Valor negativo é recusado. |
| `try_resize(size):bool` | Reserva se preciso; sucesso zera bytes novos, inclusive após encolher ou clear. False mantém todo o estado. |
| `size`, `capacity`, `max_bytes` | Consultas O(1). |
| `get(index)`, `set(index,value)` | Acesso por tamanho lógico; índice inválido é erro de contrato. |
| `clear()` | Zera tamanho lógico; conserva capacidade. |
| `release()` | Libera o payload e zera tamanho/capacidade; idempotente e reutilizável. |

O limite inclui **payload antigo + candidato durante crescimento**. Com
capacidade 4 e limite 12, reservar 8 é permitido, reservar 9 é recusado. Depois
de release é possível reservar 12. Rejeições de quota não tentam alocar.
Subtrair capacidade atual do limite antes de comparar evita overflow na soma.
Cada instância conserva seu próprio limite e estado.

Esse limite não mede RSS, cabeçalhos, páginas físicas, slabs retidos pelo
alocador, o controlador ou outros objetos da aplicação. Não é uma quota de
processo/documento nem uma capacidade de segurança. No Linux com overcommit,
sucesso de mmap também não garante que todo futuro page fault será atendido.

Reserva copia os bytes vivos para o candidato antes de publicar a troca; o
owner anterior é destruído exatamente uma vez pela atribuição gerenciada.
Falhar não publica estado parcial. Custos: reserva O(capacidade nova + tamanho
atual), leitura/escrita O(1), expansão lógica O(bytes expostos); não há promessa
de crescimento amortizado. As funções fill/copy legadas conservam seus contratos.

## Evidência e limites

A suíte `tests/test-fallible-allocation.py` compara 220 operações com um modelo
Python independente (seed 20261029), testa classes de tamanho e reutilização,
overflow, generics, efeitos, bounds e recusa do sistema com estado preservado.
No Linux x64, um filtro seccomp no processo filho devolve ENOMEM para mapas de
64 KiB: as dez classes pequenas falham, enquanto um buffer grande vizinho
continua válido. Esse ensaio é injeção de falha de teste; não implementa sandbox
de página. O Windows exercita recusa real de uma solicitação válida de 2 EiB,
sem injetar falha em cada classe pequena nesse sistema.

Testes executam otimizado e referência com debug de blocos vivos; geração de
ELF/PE/Mach-O x64/ARM64 é distinta da execução. Resultados, comandos e hashes
ficam no [relatório desta unidade](relatorios/2026-10-29-m1-alocacao.md) e nas
[evidências](ecossistema/evidencias/m1-alocacao-2026-10-29/summary.json).

Próxima obrigação de E02-03: tornar criação/reserva de arena e coleções Move
recuperáveis, com quota compartilhada por documento, rollback de cada alocação
e injeção de falhas por fronteira. OOM de objetos, enums, closures e serviços,
quotas completas e integração Browser continuam abertos. Nenhum gate é fechado.

Continuação de 30/10: [try_new, try_push e try_insert](INSERCAO-FALLIVEL.md)
recuperam a reserva inicial de objetos e a criação de slots/ramos. As quotas
compartilhadas, controladores, remove e recuperação de serviços ainda estão
abertos. Os resultados acima continuam pertencendo à primeira fatia de buffers.

# std/pagewire — ASIP/1

Biblioteca opcional, sem provider. Decodificador incremental em AssisScript,
com buffer fallível fixo de **196708 bytes**. Uma mensagem por vez; `reset`
é obrigatório após consumir `ready`. Um header excessivo ou inválido recusa
antes de aceitar payload. EOF parcial é falha de protocolo no consumidor.

Header de 80 bytes, inteiros little-endian explícitos, sem ponteiros/padding:

| Offset | Campo |
| --- | --- |
| 0 | quatro bytes ASCII ASIP |
| 4 | u16 versão 1 |
| 6 | u16 kind, 0..255 neste perfil |
| 8 | u64 payloadLength, até 196628 |
| 16/24/32 | i64 instance/origin/epoch positivos, atribuídos pelo host |
| 40 | i64 request positivo, crescente sem wrap |
| 48/56/64/72 | quatro argumentos i64 |

HELLO é resposta kind=128, identidade/request zero, payload de 64 bytes.
Comandos 1 LOAD, 2 TICK, 3 GRANT_COUNTER, 4 GRANT_DOCUMENT, 5 POST,
6 REVOKE, 7 CLOSE e 8 STATS; respostas kind=128+comando.
Reservados devem ser zero. Só LOAD tem payload de pedido: u32 tamanho da
fonte HTDL, até 65536 bytes UTF-8, seguido de ASV1/ASV2 até 131088 bytes.
LOAD usa os quatro argumentos memory/frames/fuel/calls do contrato pagevm.
TICK usa quantum/0/0/0; POST kind/payload/0/0. Demais pedidos usam zeros.

Resposta: argumento 0 é o resultado da operação; outros três são zero.
Payload: oito i64 status/result/steps/counter/state0/queued/isolation/reserved.
Status da VM e resultado da operação são distintos: TICK com yield retorna
code=1 e status=0. `isolation` é 1 para o perfil Linux x64, 0 indisponível.
Reservado final zero. A identidade completa e request são ecoados e conferidos
pelo supervisor. Sem reutilização do epoch durante uma Session.

`get/put` exigem intervalo válido de oito bytes; bounds checks da linguagem
continuam ativos. Não são um parser público de dados sem tamanho validado.
`header` exige buffer de pelo menos 80 bytes. `valid` confere tamanho/magic/
versão; regras de kind, identidade e argumentos pertencem aos consumidores.
Não há autenticação criptográfica ou canal de rede: os pipes são privados
entre processos locais, criados pelo host confiável.

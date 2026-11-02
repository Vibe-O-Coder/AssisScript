# std/pagevm — ASV1 e perfil escalar ASV2

Continuação de 02/11/2026: o destino experimental `page-asv2` compila fonte
real com IR tipada para a extensão ASV2. [Contrato e layout completos](ecossistema/PERFIL-PAGINA-ASV2.md),
[SDK](BIBLIOTECA-page.md) e [host/escalonador](BIBLIOTECA-pagehost.md).
ASV1 e version()=1 são preservados; format_version()=2 anuncia a extensão.
ASV2 admite até quatro argumentos, constantes i64 completas, bitwise/shift/
resto, imports htdl_v1 1..8 e trap explícito. -11 indica deslocamento inválido
e -12 saída inalcançável. Unknown versions/imports continuam recusados.

Status 3 significa resposta SDK pendente, não erro terminal. waiting_import,
waiting_argument, waiting_second e waiting_call expõem somente escalares ao
host. reply exige instance/origin/generation/event request/call exatos, escreve
o destino e retoma estado 0 uma única vez. begin_event com request crescente
reentra main depois de halt, limpa frames e preserva fuel/calls cumulativos.
Fechar/revogar impede resposta ou novo evento. run limita uma fatia; imports
não despacham IO ou código C da página. O contador só pode ser concedido
quando status=0, antes de executar ou enquanto retomável, como na API ASV1.

O contrato abaixo é o histórico ASV1 e o comparativo anterior; sua ausência
de backend/SDK foi superada somente pelo perfil escalar delimitado acima.
Escolha geral VM/Wasm, sandbox nativa e gates permanecem abertos.

Biblioteca opcional experimental escrita em AssisScript. Serve ao comparativo
M0-EXEC; não é backend de página do compilador, SDK htdl_v1, runtime completo
da linguagem, loader Wasm, nem sandbox de processo. Não carrega fonte/nativo.
Somente bytes ASV1 locais gerados explicitamente são usados nos exemplos.

`try_new Instance(instance,origin,generation,data,max_memory,max_frames,
max_steps,max_host_calls)` valida bytes antes de copiar/alocar. Identidades
positivas são atribuídas pelo host sem reuso. Fonte não é autoridade. A página
não pode chamar APIs AssisScript do host: seu único vocabulário são opcodes.

Formato little-endian, sem padding/ponteiros: magic ASCII ASV1, u32 count,
u32 entry, u32 memoryBytes; seguem count instruções de oito bytes: u8 op,a,b,c,
i32 immediate. Tamanho exato 16+8*count, count 1..16384, entry<count.
16 registradores i64 por frame, booleanos produzidos como 0/1. Inteiros têm
overflow modular; divisão trunca para zero, MIN/-1 retorna MIN; zero dá trap.
Não há floats, generics, closures, ownership de objetos de página ou frontend.

| Opcode | Operação |
| --- | --- |
| 0 | Halt com r[a] |
| 1 | Const i32 com extensão de sinal → r[a] |
| 2–7 | r[a] = r[b] +, -, *, /, ==, < r[c] |
| 8 | Jump para immediate |
| 9 | Jump para immediate se r[a]==0 |
| 10 | Call immediate: argumento r[b] → r0 novo frame; resultado → r[a] |
| 11 | Return r[a]; frame raiz termina |
| 12 | r[a] = counter.add_v1(r[b]); c=0 e immediate=1 |
| 13 | r[a] = load byte no endereço r[b] |
| 14 | store byte(r[b]) no endereço r[a] |
| 15 | r[a] = int(r[b]==0) |

Todos os operandos usados são 0..15, restantes precisam ser zero; alvos de
salto/call são índices válidos. Import desconhecido/versão diferente é erro
antes da execução. Não há FFI, arquivos, processos, rede, relógio ou ponteiro
entre instâncias. Validação é linear com teto de 16384 instruções.

Tetos do host: memória 0..65536 bytes, frames 1..128, passos totais 1..1000000,
host calls 0..10000. Reservas são código count*8, memória linear, frames*16
inteiros e dois arrays de frames, além dos controladores. São corpos solicitados,
não RSS. Memória/registradores começam em zero. Call isola registradores.
Cada instrução custa um passo, inclusive call/host/trap; chamadas hospedeiras
são somente soma inteira constante, limitada a delta ±1000000. Não há chamada
bloqueante escondida sob esse custo. Código copiado não muda com o buffer fonte.

`run(max_work)` executa 1..10000 passos por fatia: 1 yielded, 2 halted, ou erro.
`status()` é 0 enquanto retomável, 2 halted, ou erro terminal. `steps`,
`host_calls`, `counter`, `result` são consultas. Fuel não reinicia após yield.
`grant_counter(instance,origin,generation)` é exclusivo do host confiável e
exige a identidade completa do objeto em estado 0. O índice de import zero
não concede acesso por si. `revoke()` cancela permanentemente; não permite
regrant. `close()` impede toda execução; owners são liberados em drop.
Não há IPC, requests assíncronos, tokens criptográficos ou concessão de rede.

Erros: -1 formato/parâmetros, -2 sem concessão/revogado, -3 fuel, -4 OOM,
-5 memória/PC, -6 frames, -7 divisão por zero, -8 quota de host, -9 fechado,
-10 argumento de host. Falha terminal nunca retoma. max_work inválido retorna
-1 sem alterar instância válida. Efeitos já executados não sofrem rollback.
Origens são identidades locais, não parsing/autorização de URLs.

Comparativo Wasm em tools/pagevm-wasm-spike.js é ferramenta de teste Node/V8
com fixtures confiáveis. Bloqueia nomes de import, observa i64 e memory.grow,
mas o loop foi encerrado pelo processo pai: não há fuel/verificador de limites
geral. Wasm MIN/-1 dá trap e precisa lowering para preservar AssisScript.
ADR-0001 mantém decisão aberta; E06-04 e todos os gates continuam pendentes.

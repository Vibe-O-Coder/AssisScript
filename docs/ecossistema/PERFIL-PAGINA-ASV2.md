# page-asv2 — perfil escalar experimental

Versão do formato: **2**, SDK **htdl_v1 / read-only-1**. Data: 02/11/2026.
Escopo E06-01/E06-03/E06-05/E07-03. ASV2 foi escolhido para este perfil
escalar local após comparação Wasm; o executor geral e suas extensões
permanecem abertos no [ADR-0001](ADR-0001-EXECUCAO-PAGINA.md).

## Compilação e semântica

`assis build fonte.assis --target page-asv2 -o programa.asv2` usa o frontend
atual, tipos, ownership e IR tipada. A emissão ocorre depois de destruir a AST.
`--no-opt` conserva a comparação sem eliminação de recursão em cauda; não é
um segundo interpretador da AST de página. A referência independente é o
executável nativo otimizado/AST, acrescido do modelo Python de inteiros.

Aceita `int` i64 e `bool` 0/1, `void` em retorno, constantes, locais,
atribuições/compostas, `++`/`--`, operações inteiras, conversões int/bool,
if/else, while/for, break/continue, funções diretas e recursão. Zero a quatro
argumentos por valor; até oito locais, incluindo argumentos, por função.
Avaliação é da esquerda para a direita; &&/|| são curtos-circuitos.

Inteiros têm overflow modular de 64 bits; divisão trunca para zero;
MIN/-1=MIN e MIN%-1=0. Divisão por zero e deslocamento fora de 0..63 dão trap.
Comparações são com sinal e shift à direita é aritmético. `unsafe` não
amplia o perfil: seu conteúdo também é validado. Todos os corpos são
checados, inclusive funções/trechos não utilizados e ramos constantes mortos.

Objetos, ponteiros, arrays/slices, texto, floats, larguras numéricas distintas,
generics, closures, chamadas indiretas, IO/relógio, FFI geral e demais builtins
são recusados. Não há mudança da sintaxe da linguagem. Declarações `extern`
com biblioteca literal `assis_htdl_v1` nos dois campos e assinaturas exatas
abaixo representam imports da VM. Nenhum carregamento de DLL ocorre na página.
Nome conhecido com assinatura incorreta também é recusado.

Limites de aceitação: 64 KiB de fontes somadas, 16 módulos/aliases,
16.384 tokens, 128 funções e 16.384 instruções. Leitura/importação tem guardas
antes do crescimento; análise e emissão têm tetos adicionais. O compilador
é ferramenta confiável local, não serviço de compilação remota com quota de
RSS/tempo. OOM do próprio compilador ainda encerra seu processo.

`platform("page-asv2")` seleciona declarações somente nesse destino; branches
nativas não são selecionadas por acidente. `run/test`, `--app` e `--symbols`
são recusados para página. Sem `-o`, a saída é `page.asv2`. Erros de perfil
ocorrem antes de abrir a saída. Proteção de fonte/compilador também se aplica.

## Layout e validação

Formato sem ponteiros, padding ou dependência da largura do host:

| Offset | Encoding little-endian |
| --- | --- |
| 0 | ASCII ASV2 |
| 4 | u32 instructionCount, 1..16384 |
| 8 | u32 entry, menor que count |
| 12 | u32 memoryBytes, até 65536 e teto do host |
| 16 | count registros de oito bytes: u8 op,a,b,c; i32 immediate |

Comprimento exato 16+8*count. Verificação estrutural linear antes de copiar ou
alocar estado. Todo destino deve ser índice válido; cada registrador usado é
0..15 e campos não usados são zero. Bytes hostis não carregam tipos/origem ou
permissão: o verificador é estrutural, não prova que os bytes vieram do
compilador. Saltos entre regiões de funções continuam confinados ao mesmo
vetor de instruções e aos mesmos limites de memória/imports.

ASV1 conserva os opcodes 0..15 e Call com c=0. ASV2 acrescenta:

| Op | Semântica |
| --- | --- |
| 10 | Call target; copia r[b]..r[b+c] para r0..r[c] do frame novo; c=0..3; b+c<16 |
| 12 | Import immediate 1..8; destino r[a], argumento r[b], segundo r[c] somente em 4 |
| 16 | r[a]=r[b] |
| 17..19 | r[a]=r[b] & / \| / ^ r[c] |
| 20..21 | r[a]=r[b] << / >> r[c], validando o deslocamento |
| 22 | Resto com sinal e contrato modular MIN/-1 |
| 23 | Substitui os 32 bits superiores de r[a] por immediate; preserva os inferiores |
| 24..25 | r[a]=~r[b] / -r[b] |
| 26 | Trap explícito de saída inalcançável/retorno ausente |

Os opcodes anteriores estão no [contrato pagevm](../BIBLIOTECA-pagevm.md).
Constantes i64 usam duas instruções, sem arredondamento por float. Call zera
16 registradores do frame novo; retorno restaura somente seu destino. Frames
não contêm referências ao host. O compilador emite memoryBytes=0; os opcodes
de memória ASV1 continuam disponíveis para fixtures, sob seus limites.

## Imports htdl_v1 / read-only-1

Todas as assinaturas retornam `int`; argumentos também são `int`. ID é o
immediate do opcode 12. Host calls contam no teto total da instância.

| ID | Símbolo exato | Parâmetros | Resultado |
| --- | --- | --- | --- |
| 1 | counter_add_v1 | delta | Contador concedido pelo host, delta ±1000000 |
| 2 | event_get_v1 | field | 0 kind, 1 payload, 2 document, 3 request, 4 generation, 5 instance, 6 last_error |
| 3 | state_get_v1 | slot | Célula privada 0..31 |
| 4 | state_set_v1 | slot,value | Escreve e retorna a célula |
| 5 | node_at_v1 | index | Handle local da projeção, índice 0..count-1 |
| 6 | node_kind_v1 | handle | Tipo semântico HTDL 1..9 |
| 7 | node_flags_v1 | handle | hidden=1 e disabled=2, atributos locais |
| 8 | node_count_v1 | reserved=0 | Quantidade de elementos, incluindo head/title |

Imports 2..8 suspendem a VM com status 3. O host responde com a identidade
completa, request do evento e sequência monotônica da chamada. Resposta
incorreta/repetida/tardia não escreve registrador ou retoma a VM. Só o host
nativo possui a API de resposta; o bytecode não possui opcode para ela.
O ID 1 é soma constante interna, com concessão separada e falhas terminais.

`last_error()` consulta field 6 sem alterar o erro; chamadas SDK 2..8 restantes
definem 0 em sucesso, -1 argumento, -2 concessão/handle. Assim, célula com valor
negativo não se confunde com erro. Imports de documento iniciam negados;
evento/células são dados privados da própria página. Não há strings,
mutações de documento, subscriptions gerais, callbacks C, rede ou recursos.
Essa extensão requer nova negociação/versionamento antes de ampliar a ABI.

## Instâncias, eventos e autoridade

Host atribui instance/origin positivos sem reuso. `Page.prepare` reserva
generation monotônica inclusive em tentativa abortada; até 4503599627370495.
Documento é fornecido já validado pelo parser HTDL; seu atributo lang/id não
define origem. Uma projeção própria de até 1024 elementos é construída antes
de commit. Conteúdo, fila e células não retêm ponteiro do documento.

Handle de nó é generation*2048+index+1, **local ao contexto implícito da VM**.
Não é NodeId global ou capacidade. Números iguais em Pages diferentes nunca
endereçam o documento da outra Page. A autorização é a concessão ligada a
instance/origin/generation/document; replay após reload falha pela geração.
Revogação de documento é permanente para a instância. Reativar exige novo
prepare/commit. Capacidade de contador é concedida separadamente.

Commit sem alocação substitui VM/projeção, revoga a anterior e zera células/
fila; cria evento init=1/request=1. Post aceita somente kind 2 ativação e
3 atualização do host. Envelope completo e request estritamente crescente
são obrigatórios. Fila circular de 32 eventos retorna backpressure=1 sem
consumir request; o chamador pode tentar novamente depois. Close descarta
fila, invalida execução, libera owners e é idempotente. Não há callback de
dispose executando código revogado.

`main` é chamado novamente a cada evento, com frames novos e células privadas
persistentes no host. Não se anuncia ABI init/event/dispose geral da linguagem.
Fuel, chamadas e contador são cumulativos na vida da VM e não reiniciam por
evento/yield. Consumo/erros anteriores não sofrem rollback.

## Limites operacionais e sistemas

VM: memória 0..65536, frames 1..128, passos 1..1000000, host calls 0..10000;
quantum 1..10000. Uma instrução ou host call é trabalho limitado; não há IO
bloqueante dentro do import. SDK resolve no máximo uma chamada por tick.
Preparação de projeção e compilação ocorrem fora do quantum de execução.

Group visita até 16 slots por poll, na ordem circular, com quantum explícito.
Relógio monotônico vem do host. Deadline revoga a página antes de executar;
tempo retrocedente/orçamentos inválidos não mudam cursor/instâncias. Slots
fechados não são reatribuídos na vida do Group. O chamador integra poll ao
loop de janela/IO; este módulo não implementa polling de sockets/processos.

São tetos de contagem e corpos solicitados, não quota integral/RSS, tempo
real, proteção de crash nativo ou sandbox. Windows/Linux x64 têm testes de
execução desta unidade. Geração de ELF/PE/Mach-O/ARM64 não é execução nesses
sistemas. Programa remoto e código nativo de página continuam proibidos.
G1–G5, inclusive G2, continuam abertos.

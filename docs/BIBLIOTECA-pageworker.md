# std/pageworker — execução local supervisionada

Continuação de 02/11/2026: o provider compartilha os 16 slots com o serviço [pagecompiler](BIBLIOTECA-pagecompiler.md). Windows agora oferece LPAC sem capabilities, com perfil/identidade por processo e limites antes de resume; Linux conserva seccomp e tetos anteriores. ABI v1/imports antigos preservados. [Perfil Windows e limites](ecossistema/PERFIL-WINDOWS-ISOLATION-V1.md).

Biblioteca opcional dependente de `pagewire`, para o host nativo confiável.
Lógica de protocolo, deadlines, navegação e execução da página em AssisScript.
Provider escalar próprio `assis_worker_v1` adapta somente processos, streams,
encerramento e restrições do OS. Não aceita executável nativo de página.

Construa o worker confiável e seu provider com:

```text
ASSIS_BIN=<compilador atual> python tools/build-page-worker.py --output <pasta>
```

O worker e a DLL/so devem ficar juntos. O host precisa encontrar o provider
(DLL ao lado do host no Windows; LD_LIBRARY_PATH controlado pelo host no Linux).
O caminho passado a `Worker` é absoluto, escolhido pelo host, não por documento.
A autenticidade/distribuição do binário e provider ainda cabe ao integrador;
HELLO não autentica um executável arbitrário. Não há download/execução nativa.
Provider ausente pode falhar no loader antes de main. Sem promoção de pacote.

`try_new Worker(path,instance,origin,epoch,restricted,now,timeout)` inicia
um processo, depois `poll(now)` aguarda HELLO por consultas sem espera de IO.
`now` deve ser relógio monotônico do host; timeout entre 1 e 60000 ms.
Não usar tempo constante em produto: isso impede expiração de deadlines.
Relógio regressivo retorna -1, sem alterar o comando em curso.

Após `ready`, `load(source,code,memory,frames,fuel,calls,now,timeout)` envia
HTDL e bytecode; só sucesso autoriza comandos. Não se compila fonte de página
no worker. Parsing HTDL/projeção/VM são preparados juntos; erro de LOAD recebe
resposta e encerra o candidato. O processo recebe um único LOAD por vida.
Subconjunto escalar/SDK read-only-1 e limites de pagehost/pagevm preservados.

`command(kind,arg0,arg1,now,timeout)` envia operações [ASIP/1](BIBLIOTECA-pagewire.md).
`poll` retorna 0 aguardando/ocioso, 1 resposta, negativo falha terminal.
Há um pedido em voo por worker; pedido concorrente retorna -12.
Cada poll faz até uma escrita e uma leitura de 4096 bytes. Encerramento em
falha faz kill/reap síncrono, com espera Windows de até 5 segundos; não é uma
garantia de latência em tempo real. O chamador alterna Workers no loop do host.
Uma resposta parcial não é visível até a identidade/tamanho serem validados.

`Reply` separa code, status, result, steps, counter, state, queued e isolation.
Erros locais: -1 argumento/relógio; -3 isolamento indisponível; -4 recurso/OS;
-9 fechado; -12 ocupado; -20 deadline; -21 EOF/IO; -22 protocolo. Falhas do
parser/VM vêm em code; diagnóstico HTDL é `-1000-Hxxx`. Nenhum texto privado
da página é escrito em logs do provider. stderr do filho vai para null.

`close` é idempotente e revoga o processo, fila e todos os pedidos. Drop de
Worker também fecha; o provider conserva PID/handle até kill/reap, evitando
sinalizar PID já reciclado. Slots nativos: 16 simultâneos, tokens i64
monotônicos sem reuso/wrap. Tokens são identidades locais, não capacidades.
No Linux só a thread principal chama APIs do host; Windows fixa a thread da
primeira chamada. Thread incorreta retorna -6; buffers não são retidos.

`Session.prepare` inicia candidato com epoch crescente inclusive se abortado.
`candidate_mut` permite aguardar HELLO/LOAD. `commit` exige candidato carregado
e ocioso, fecha o ativo e transfere o owner sem alocação. Falha/abort conservam
o ativo; commit não reinicia pedidos já consumidos pelo candidato. A página
inicia execução somente após um TICK explícito. `current/current_mut` e
`candidate_mut` requerem o respectivo `has_*` verdadeiro antes de uso.
`close` fecha ambos; destruição automática dos owners também fecha ambos.
Sem callbacks de dispose em código revogado. Subscriptions gerais não existem
nesse SDK; o projeto não as declara implementadas.

Linux x64: `no_new_privs`, seccomp com allowlist, memória virtual 128 MiB,
pilha 8 MiB, CPU cumulativa de processo 3 s, core dump zero, limite de FDs 3.
Só streams 0/1/2, memória anônima sem execução, relógio/sleep/futex e saída
entram na allowlist. Arquivos/rede/exec/fork/ptrace/kill, memória executável e
IO em descritores fora dos streams são negados. Herança de FDs >=3 é removida;
ambiente só LANG e diretório confiável do provider, cwd `/`. PDEATHSIG encerra
o filho quando o pai morre. Não é isolamento de kernel, canais laterais ou
proteção contra kernel comprometido. Limites fixos contam o processo todo,
incluindo runtime/parser; não medem RSS e não limitam a compilação externa.

Windows x64: `restricted=true` exige LPAC, zero capabilities e SID nova por
processo. Perfil temporário, duas cópias de runtime com leitura/execução e
DACL própria, lista de três handles herdados e ambiente mínimo. Antes de
resume, token/SID/capabilities e Job são validados. Job limita um processo,
128 MiB de commit privado e CPU de usuário a 3 s; política recusa filhos,
código dinâmico, extension points e interação de UI com outros Jobs.
Falha de criação/restrição retorna -4 com token zero, sem fallback.
Close encerra processo e remove cópias/perfil; falha nativa de remoção retorna
-4. O wrapper close já existente não expõe esse retorno de limpeza.
O exemplo agora usa isolamento por padrão também no Windows. A opção
`--trusted-local` permanece um opt-out explícito de diagnóstico local.
Perfil do OS tem armazenamento próprio gravável; não há quota de disco nem
coletor após crash do shell. Win32k lockdown não está anunciado. Consulte os
demais limites e evidências no contrato específico antes de integrar.
macOS/ARM64/provider ausente não recebem fallback com isolamento anunciado.
G2 e a escolha geral VM/Wasm continuam abertos. Linux é prova delimitada,
sem páginas remotas, broker, partição de produto ou FS/SSC. Reader usa a mesma
transação nos testes; aceites reais de desktop e leitor continuam pendentes.

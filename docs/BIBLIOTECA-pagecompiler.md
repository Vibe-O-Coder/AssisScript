# std/pagecompiler — compilação de página com orçamento

Biblioteca opcional do shell confiável, dependente de `pagevm`. Implementação
do supervisor e validação em AssisScript; provider de processos
`assis_worker_v1` e compilador nativo existentes. Windows/Linux x64 são os
perfis desta entrega. macOS/ARM não têm execução desse serviço validada.

`try_new Task(compiler,source,reference,mib,cpu_seconds,now,timeout)` copia a
fonte antes de iniciar um processo descartável. `compiler` é caminho absoluto
para um compilador confiável instalado pelo host. Documento não escolhe esse
caminho; não se executa compilador/binário nativo recebido como página.
Provider deve ser encontrado pelo loader nativo, como em `pageworker`; símbolo
ausente em uma DLL antiga falha antes de main, sem negociação por retorno.

Fonte: 1..65536 bytes, UTF-8 e sem NUL; o total com o SDK importado também não
pode exceder 64 KiB. Referência seleciona o modo sem otimização. Compilação
mantém o perfil ASV2 escalar, limites de tokens/módulos/funções/IR e rejeições
de recursos existentes. Imports aceitam exatamente `std/page.assis`, embutido
no próprio compilador, com verificação `python tools/prepare-page-sdk.py --check`.
Não há resolução em disco, pacote, configuração de projeto, ASSIS_PATH, alias
de caminho, flags da fonte ou escrita de artefato em arquivo nesse serviço.
O CLI de autoria `build --target page-asv2` conserva seu contrato de imports;
o shell usa o novo serviço para fonte não confiável.

Orçamento solicitado: 16..512 MiB, 1..10 segundos de CPU. Linux aplica
RLIMIT_AS/CPU/STACK antes de exec; o compilador entra em no_new_privs/seccomp
com somente streams, memória não executável e relógio/sleep, antes de ler
bytes. A mesma política é compartilhada com o worker, sem ampliar syscalls.
Windows aplica Job antes de retomar o processo, com um processo ativo, teto
de memória privada comprometida e tempo de CPU em modo usuário. Cada consulta
de I/O também confere GetProcessTimes e encerra o Job ao ultrapassar o teto,
pois a checagem do OS é periódica, conforme o [contrato Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information).
O launcher agora exige também [LPAC Windows](ecossistema/PERFIL-WINDOWS-ISOLATION-V1.md)
antes de ler fonte: zero capabilities, identidade/perfil novos, runtime
somente leitura e recusas nativas de arquivos privados/rede/processos.
Não há fallback de compilação para processo irrestrito. Invocar diretamente
o comando interno fora desse launcher não cria esse isolamento.

O comando interno `assis page-compile-worker` também instala tetos próprios
de 512 MiB/10 s e, no Linux, 8 MiB de pilha; limites mais restritos do pai
prevalecem. Invocação direta não fornece prazo para stream parado: use Task.
Limites do OS não prometem interrupção em tempo real. O limite Windows é
commit privado; RSS pode ultrapassá-lo devido a páginas compartilhadas.
Linux limita espaço virtual, não mede contabilização de memória do cgroup.

`poll(now)` faz uma escrita e uma leitura de até 4096 bytes: 0 pendente,
1 bytecode completo validado por `pagevm::Instance`, negativo erro.
`status/ready/is_open` permitem consultar o estado; `code()` empresta os bytes
somente após ready. Sucesso encerra e recolhe o compilador antes de publicar
os bytes. Não executa nenhuma instrução da página. Close invalida o resultado;
drop cancela o filho. Prazo 1..60000 ms, relógio monotônico fornecido pelo host;
regressão retorna -1 sem mudar o prazo. Deadline cancela mesmo filho parado.

Erros: -1 parâmetros/relógio, -4 alocação/OS, -9 fechado, -20 prazo,
-21 compilador terminou/IO (inclui fonte inválida ou limite do processo),
-22 resposta malformada. Não há diagnóstico detalhado da fonte no protocolo:
stderr do filho é descartado, sem copiar conteúdo privado para logs do shell.
Para autoria, `check --diagnostics=json` permanece disponível separadamente.

`usage()` retorna `{limit,resident,peak_resident,accounted,state}`. `limit` é
o orçamento do OS em bytes; resident/peak_resident são RSS observado; accounted
é commit privado Windows ou tamanho virtual Linux. State: 1 vivo, 2 encerrado.
Consultar antes de fechar. A biblioteca conserva a última amostra, que pode
ser zero no Linux após exit; VmHWM deixa de existir quando o processo morre.
Essa consulta lê contadores do sistema, sem garantia de latência constante.
Não representa quota de toda a árvore Reader/shell nem inclui buffers do host.

ABI adicional preserva `assw_version=1`: `assw_compile_open(path,len,mib,cpu,out)`
e `assw_usage(token,words,capacity)`. Usage escreve seis i64: versão 1, limite,
RSS atual, pico RSS, contabilizado, estado; capacidade mínima 6. Buffers são
empréstimos da chamada, tokens locais sem reuso, 16 processos simultâneos
compartilhados com `pageworker`, thread principal obrigatória. Herança mínima,
ambiente sem segredos e ausência de shell preservados. Close/kill/reap é
síncrono; Windows pode aguardar até 5 s. Não é garantia de UI em tempo real.

ASC1/1: pedido `ASC1`, u32 LE comprimento, u32 flags (0 otimizado, 1 referência),
fonte. Uma resposta contém u32 LE comprimento seguido por ASV2 (24..131088 bytes).
Cabeçalho inválido, excesso, versão e instrução desconhecidas são recusados.
Processo por compilação delimita a identidade; não há multiplexação ou pointer.
Resposta parcial não publica bytes. O host valida novamente ao carregar a VM.

`pagereader::Session.prepare_source` integra o serviço com navegação. Recebe
compiler,worker,HTDL,program,reference,mib,cpu,restricted,dimensões,métrica,
limits,grants,now; `advance` mantém o ativo e avança compilação/Reader/worker.
Abort/close cancela todas as fases; código, HTDL, load ou layout inválidos
preservam o ativo. Ações/reflow ficam suspensos durante candidato, como no
prepare de bytecode anterior. Após ready, commit/publish conserva as mesmas
concessões e transação conjunta. O parser/layout ainda é síncrono após compilar.

Exemplo `51_compile_page.assis`: argumentos caminho absoluto do compilador,
caminho absoluto do worker e `--trusted-local` somente para o perfil Windows
sem sandbox. Compila fonte, ativa Reader/SDK e imprime `PAGE-STATE 42`.
Construa worker/provider com `tools/build-page-worker.py`; DLL/so junto ao host.
Nenhuma dependência redistribuída ou versão de release é acrescentada.

HTDL/código/FS/SSC/recursos completos, SDK mutável/strings/subscriptions,
orçamento agregado de shell/Reader/RSS, sandbox Windows/macOS, broker/origens,
desktop/leitor/DPI/IME e gates permanecem na fila. Easy continua por último.

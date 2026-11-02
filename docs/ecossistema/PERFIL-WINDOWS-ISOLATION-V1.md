# windows-isolation-v1 — worker e compilador LPAC

02/11/2026. E06-04/M0-EXEC parcial. Execução demonstrada: Windows 10 x64
10.0.19045, provider próprio `assis_worker_v1`, ASV2 escalar e compilação ASC1/1.
Não aprova G2 nem autoriza página remota ou executável nativo baixado.

## Autoridade e preparação

Host, provider e executáveis instalados são confiáveis; fonte/HTDL/bytecode
são hostis. Caminho absoluto do worker/compilador vem do host, nunca do
documento. O host continua responsável pela autenticidade dos binários.

Cada spawn obtém 128 bits de BCryptGenRandom, gera nome `assis-lpac-<hex>` e
cria perfil AppContainer novo com zero capability SIDs. Perfil já existente
é erro, sem reuso. A criação produz SID e armazenamento próprios do OS.
Nenhum pacote, exceção de rede/loopback ou ACL de arquivo existente é alterado.

Runtime exe e provider já carregado são copiados para pasta nova do temporário.
DACL protegida concede full control somente ao usuário/System e read/execute
à SID específica. A ACL é reaplicada às duas cópias, pois CopyFile pode copiar
segurança da origem. Só são copiados esses nomes fixos; conteúdo de página,
bibliotecas adicionais e arquivos do perfil do usuário não entram na pasta.
Dependências nativas adicionais de um executável não fazem parte do perfil.

CreateProcess recebe SECURITY_CAPABILITIES com essa SID, capability count 0,
ALL_APPLICATION_PACKAGES_OPT_OUT, política de filhos restritos e mitigations
de dynamic code/extension points. O processo fica suspenso enquanto o host
confere TokenIsAppContainer, TokenCapabilities e SID e o associa ao Job.
Uma consulta Win32 a TokenIsLessPrivilegedAppContainer não é usada: retornou
ERROR_INVALID_PARAMETER neste host. LPAC é exigido pelo atributo de criação;
o oráculo independente confirma a semântica por AccessCheck: grant para
ALL_APPLICATION_PACKAGES não autoriza, ALL_RESTRICTED_APPLICATION_PACKAGES
autoriza, além de token de AppContainer e capabilities vazias.

Job aplica um processo, memória privada comprometida, CPU de usuário e
KILL_ON_JOB_CLOSE. Restrições de UI cobrem handles externos, clipboard,
desktop, global atoms, settings e exit Windows. Win32k lockdown não faz parte
do perfil; não se alega bloqueio de toda syscall ou isolamento do kernel.
Retomar só acontece após configuração aceita. Qualquer falha retorna -4,
token zero e desfaz criação; nunca inicia processo irrestrito por fallback.

Streams herdados são apenas stdin/stdout/stderr, este último NUL. Pipes do
host continuam sem espera; filho usa streams bloqueantes. DETACHED_PROCESS
evita inicialização de console que falhou com CREATE_NO_WINDOW neste host;
não se altera LowBoxConsoleEnabled do usuário. Ambiente passa somente
SystemRoot, USERPROFILE e LOCALAPPDATA necessários à inicialização do OS;
essas variáveis não concedem acesso aos dados. Não se herda PATH ou segredos.

## Ciclo de vida e falhas

`assw_open(...,1,...)` aplica esse contrato; modo 0 continua explícito para
conteúdo local confiável. `assw_compile_open` sempre exige LPAC no Windows,
conservando assinatura/ABI e os 16 slots compartilhados. No filho, assw_restrict
verifica token AppContainer e capabilities, sem confiar em ambiente/HELLO.
HELLO sozinho não autentica executável escolhido por um host malicioso.

Close mata/recolhe, fecha handles, remove duas cópias/pasta e usa
DeleteAppContainerProfile. A API nativa retorna -4 se limpeza falhar; o wrapper
de close existente não propaga essa falha. Há teste de seis fronteiras de
criação e 64 ciclos por modo, sem aumento de profiles/pastas/handles.

Crash do shell fecha Job e encerra filho pelo contrato do OS; não há coletor
de perfis/pastas órfãos após crash ou falha de disco/antivírus. Perfil tem
armazenamento próprio gravável sem quota de disco. Não se afirma negação de
todo arquivo: runtime, recursos de sistema explicitamente autorizados ao LPAC
e perfil próprio existem. Página ASV2 segue sem import de IO nativo.

Compilação e worker têm CPU/memória e deadline; RSS continua observação,
distinta de commit. Criação/cópia/perfil, parsing/layout no shell e teardown
são síncronos e não têm SLA de UI. Não há quota agregada shell/Reader, broker
URL/DNS/TLS, partições persistentes de produto ou proteção contra kernel e
canais laterais. macOS/ARM e outros builds Windows não foram executados.

## Evidência e dependências

`tests/windows-isolation-oracle.c` não usa helper de token do produto. Tenta
acesso nativo a sentinela privada, runtime vizinho, registro do usuário,
processo pai, rede loopback, clipboard, código executável e spawn. Acesso ao
runtime próprio é controle positivo; escrita é negada. SID muda por spawn.
No host registrado, WinSock é recusado já em WSAStartup (10107); não se rotula
isso como uma execução bem sucedida de connect seguida de WSAEACCES.
Windows/Linux e otimizado/referência são relatados separadamente; Linux
não executa os quatro testes Windows, conserva as negativas seccomp próprias.

Fontes, comandos, hashes e resultados: [relatório](../relatorios/2026-11-02-m0-windows-isolation.md).
Ponte original sob LICENSE; Kernel32/UCRT/Advapi32/Userenv/BCrypt do sistema,
sem redistribuição Microsoft; MinGW/GCC e avisos existentes. Só testes usam
User32/Winsock adicionais. APIs/ownership/thread/erros e bytecode v1/v2 não
mudam; não se introduz sintaxe nova ou lógica de produto em C.

Referências primárias: [lançamento AppContainer/LPAC](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[isolamento](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation),
[atributos de processo](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[CreateAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile),
[DeleteAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile).

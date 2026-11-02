# worker-local-v1 — contrato e limites

Data 02/11/2026. Perfil experimental de processo para ASV1/ASV2 e
`htdl_v1/read-only-1`, sem alterar gramática, nomes canônicos ou ownership.
Escopo E03-03/E03-04/E03-05/E06-04/E06-05. Não fecha M0-EXEC ou G2.

Formato/protocolo: [ASIP/1](../BIBLIOTECA-pagewire.md).
API, provider, quotas e negociação: [pageworker](../BIBLIOTECA-pageworker.md).
O worker usa pagehost/htdl já existentes e não duplica sua lógica em C.
O host escolhe executable/provider confiáveis, instância, origem e epoch;
atributos da página não concedem autoridade. Não há ponteiros no IPC.

Ativos: processo do shell, árvore/estado de cada página, ambiente e arquivos
do usuário, perfis futuros, disponibilidade de abas vizinhas. Entrada hostil:
bytes HTDL/VM, tamanhos/framing, pedidos e respostas antigas/forjadas,
worker travado, EOF parcial ou abrupto e esgotamento de quota.
Shell/provider/worker inicial são confiáveis; página não escolhe programa
nativo. Escape da VM é contido parcialmente pelo perfil Linux de syscalls,
sem proteção contra bugs do kernel. Windows ainda exige conteúdo local
confiável e recusa isolamento obrigatório. Não há rede/broker remoto.

| Invariante | Evidência independente |
| --- | --- |
| Limite antes de payload/cópia | headers >196628, fragmentação byte a byte, 64 KiB HTDL, payload parcial/EOF |
| Sem replay/contexto cruzado | alterações em instance/origin/epoch/request; recusa e encerramento |
| Host responsivo e vizinha viva | stalls de entrada/saída, pressão de retorno, CPU em outro processo, deadlines |
| Revogação/cancelamento | close/drop repetido, slots reutilizáveis com tokens novos, fila revogada, retorno antigo recusado |
| Ativação transacional | candidato inválido/abort preserva 42; reload válido troca para 84; epoch 1→2→3 |
| Herança e ambiente mínimos | oráculo C enumera FDs/variável sentinela antes da restrição |
| Linux sem arquivos/rede/processos | open/socket/fork/exec/ptrace/kill negados por EPERM em oráculo C |
| Memória/execução | mmap 256 MiB recusado, PROT_EXEC negado; fuel e frames mantidos pela VM |
| Windows não anuncia sandbox | restricted=true retorna -3; exemplo exige opt-in local |

Testes em `tests/test-page-worker.py` usam cliente binário Python/struct,
modelo inteiro de eventos e oráculo C de syscalls. Otimizado/referência e
Windows/Linux são registrados separadamente. O relatório corrente identifica
o candidato e os resultados; esta especificação não certifica outros hosts.

Limites pendentes: compilação externa/RSS, sandbox Windows/macOS, watcher de
CPU no shell, broker/origens/perfis completos, reentrada/subscriptions gerais,
Reader/loader visual conjunto, decisão Wasm/VM, catálogo HTDL e FS/SSC.
Uma sessão mantém no máximo ativo+candidato; o chamador define quantas sessões
abre até o teto nativo de 16 workers. Não há auto-restart em loop: após crash,
o host decide criar candidato/aba nova, preservando a vizinha.

Referências primárias consultadas: [seccomp](https://man7.org/linux/man-pages/man2/seccomp.2.html),
[no_new_privs](https://docs.kernel.org/userspace-api/no_new_privs.html),
[CreateProcessW/herança de handles](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
Shim próprio sob LICENSE do repositório; sem dependência redistribuída nova.
Windows usa Kernel32/UCRT do sistema; Linux usa glibc e APIs do kernel x64.
Toolchains/versões e hashes são registrados com a evidência, sem promessa
de suporte universal de kernels/Windows diferentes dos executados.

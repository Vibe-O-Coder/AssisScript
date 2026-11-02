/* A one-request stream compiler. No project/configuration/path resolution.
 * Resource limits belong to the supervising process; Linux adds deny-by-default
 * syscalls here after the native loader and before reading any source bytes. */
#include "page_restrict.h"
static int page_compile_stream(int argc,char **argv){
    if(argc!=2)fatal("page-compile-worker: sem argumentos");
    (void)argv;
#if defined(__linux__) && defined(__x86_64__)
    struct rlimit memory,clock,stack;
    if(getrlimit(RLIMIT_AS,&memory)||getrlimit(RLIMIT_CPU,&clock)||getrlimit(RLIMIT_STACK,&stack))return 126;
    if(memory.rlim_cur>512*1024*1024)memory.rlim_cur=512*1024*1024;
    if(clock.rlim_cur>10)clock.rlim_cur=10;
    if(stack.rlim_cur>8*1024*1024)stack.rlim_cur=8*1024*1024;
    memory.rlim_max=memory.rlim_cur;clock.rlim_max=clock.rlim_cur;stack.rlim_max=stack.rlim_cur;
    if(setrlimit(RLIMIT_AS,&memory)||setrlimit(RLIMIT_CPU,&clock)||setrlimit(RLIMIT_STACK,&stack))return 126;
    if(page_stream_restrict()!=1)return 126;
#elif defined(_WIN32)
    HANDLE job=CreateJobObjectW(NULL,NULL);if(!job)return 126;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits={0};
    limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_PROCESS_MEMORY|JOB_OBJECT_LIMIT_PROCESS_TIME|JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
    limits.BasicLimitInformation.ActiveProcessLimit=1;limits.BasicLimitInformation.PerProcessUserTimeLimit.QuadPart=100000000;
    limits.ProcessMemoryLimit=512*1024*1024;
    if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&limits,sizeof(limits))||!AssignProcessToJobObject(job,GetCurrentProcess())){CloseHandle(job);return 126;}
    /* Retain the self-limit until process exit, including standalone use. */
#elif !defined(_WIN32)
    fatal("page-compile-worker: host sem perfil validado");
#endif
    page_compile_worker=true;target_page=true;target_windows=false;target_macos=false;target_arm64=false;
    json_diagnostics=true;
    unsigned char header[12];
    if(fread(header,1,12,stdin)!=12||memcmp(header,"ASC1",4)||header[8]>1||header[9]||header[10]||header[11])fatal("page-compile-worker: protocolo inválido");
    optimize=header[8]==0;
    uint32_t n=0;for(int i=0;i<4;i++)n|=(uint32_t)header[4+i]<<(8*i);
    if(!n||n>65536)fatal("page-compile-worker: limite de fonte");
    page_stream_source=mem((size_t)n+1);
    if(fread(page_stream_source,1,n,stdin)!=n||memchr(page_stream_source,0,n))fatal("page-compile-worker: fonte truncada/nula");
    Vec expanded={0};load_module("page.assis",NULL,false,&expanded,0);tokens=expanded;
    scan_platforms();scan_namespaces();parse();bind_namespaces();check();check_ownership();check_safety();page_check_profile();
    prepare_ir();prepare_ranges();prepare_registers();prepare_backend_ir();discard_frontend_ast();page_write(NULL);
    return 0;
}

/* Shared Linux x64 stream-only policy, entered before untrusted input. */
#ifndef ASSIS_PAGE_RESTRICT_H
#define ASSIS_PAGE_RESTRICT_H
#if defined(__linux__) && defined(__x86_64__)
#include <unistd.h>
#include <errno.h>
#include <stddef.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>
static int page_stream_restrict(void){
    struct rlimit files={3,3},core={0,0};
    if(setrlimit(RLIMIT_NOFILE,&files)||setrlimit(RLIMIT_CORE,&core)||prctl(PR_SET_DUMPABLE,0)||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return -4;
    /* Default deny; inspect architecture before syscall numbers (also denies
     * x32). No open, socket, exec, fork, ptrace, kill, io_uring or fd transfer.
     * read/write are limited to the dedicated streams; executable mappings and
     * file-backed mmap are denied even if a future runtime changes behavior. */
#define ALLOW(n) BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,(n),0,1),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)
    struct sock_filter f[]={
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_X86_64,1,0),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_read,0,4),BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[0])),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,0,0,1),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_write,0,5),BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[0])),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,1,1,0),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,2,0,1),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_mmap,0,7),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[2])),BPF_JUMP(BPF_JMP|BPF_JSET|BPF_K,PROT_EXEC,4,0),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[3])),BPF_JUMP(BPF_JMP|BPF_JSET|BPF_K,MAP_ANONYMOUS,0,2),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_mprotect,0,4),BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[2])),
        BPF_JUMP(BPF_JMP|BPF_JSET|BPF_K,PROT_EXEC,1,0),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),
        ALLOW(SYS_brk),ALLOW(SYS_munmap),ALLOW(SYS_madvise),ALLOW(SYS_clock_gettime),ALLOW(SYS_nanosleep),ALLOW(SYS_clock_nanosleep),
        ALLOW(SYS_futex),ALLOW(SYS_rt_sigreturn),ALLOW(SYS_exit),ALLOW(SYS_exit_group),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM)
    };
#undef ALLOW
    struct sock_fprog program={(unsigned short)(sizeof(f)/sizeof(f[0])),f};
    return prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program)==0?1:-4;
}
#endif
#endif

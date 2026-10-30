/* Test-only delayed refusal of new allocator slabs in this process. */
#define _GNU_SOURCE
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>

int32_t fault_enable(void){
    struct sock_filter code[]={
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,__NR_mmap,0,3),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[1])),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,65536,0,1),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|ENOMEM),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)
    };
    struct sock_fprog program={sizeof(code)/sizeof(code[0]),code};
    if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return -1;
    return prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program);
}

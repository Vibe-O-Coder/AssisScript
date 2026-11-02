#define _GNU_SOURCE
#include "../providers/worker/assis_worker_v1.h"
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/resource.h>
#include <signal.h>
#include <stdio.h>
/* Independent syscall oracle: runs in a disposable trusted test executable.
 * Never accepts page bytes, invokes shell commands or modifies host settings. */
int main(void){
    int mask=0;const char *secret=getenv("ASSIS_WORKER_SECRET");if(!secret)mask|=1;
    int extra=0;for(int fd=3;fd<256;fd++)if(fcntl(fd,F_GETFD)>=0)extra++;
    if(!extra)mask|=2;
    struct rlimit before;getrlimit(RLIMIT_AS,&before);
    if(assw_restrict()!=1)return 70;
    errno=0;if(open("/etc/passwd",O_RDONLY)<0&&errno==EPERM)mask|=4;
    errno=0;if(socket(AF_INET,SOCK_STREAM,0)<0&&errno==EPERM)mask|=8;
    errno=0;if(syscall(SYS_fork)<0&&errno==EPERM)mask|=16;
    errno=0;char *args[]={"/bin/true",NULL};char *env[]={NULL};if(execve(args[0],args,env)<0&&errno==EPERM)mask|=32;
    errno=0;if(kill(getpid(),0)<0&&errno==EPERM)mask|=64;
    errno=0;if(mmap(NULL,4096,PROT_READ|PROT_EXEC,MAP_PRIVATE|MAP_ANONYMOUS,-1,0)==MAP_FAILED&&errno==EPERM)mask|=128;
    void *page=mmap(NULL,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(page!=MAP_FAILED){errno=0;if(mprotect(page,4096,PROT_READ|PROT_EXEC)<0&&errno==EPERM)mask|=256;munmap(page,4096);}
    errno=0;if(mmap(NULL,256*1024*1024,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0)==MAP_FAILED&&errno==ENOMEM)mask|=512;
    errno=0;if(syscall(SYS_ptrace,0,0,0,0)<0&&errno==EPERM)mask|=1024;
    errno=0;if(syscall(SYS_read,1,&extra,1)<0&&errno==EPERM)mask|=2048;
    errno=0;if(syscall(SYS_write,0,&extra,1)<0&&errno==EPERM)mask|=4096;
    /* No stdio allocation or metadata syscalls after restriction. */
    uint8_t result[4]={(uint8_t)mask,(uint8_t)(mask>>8),(uint8_t)(mask>>16),(uint8_t)(mask>>24)};
    if(write(1,result,4)!=4)return 74;return 0;
}

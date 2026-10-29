/* Linux adapter oracle for the Darwin C API's int/ssize_t return widths.
 * This tests the freestanding runtime's ABI, not native macOS acceptance. */
#define _GNU_SOURCE 1
#define ARM_MACOS 1
#include "../src/runtime_arm64.c"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
static int fail_clock;
I os_read(I fd,void*p,U n){return read((int)fd,p,n);}
I os_write(I fd,const void*p,U n){return write((int)fd,p,n);}
int os_close(int fd){return close(fd);}
int os_fsync(int fd){return fsync(fd);}
void *os_mmap(void*p,U n,int prot,int flags,int fd,I offset){(void)flags;return mmap(p,n,prot,MAP_PRIVATE|MAP_ANONYMOUS,fd,offset);}
int os_munmap(void*p,U n){return munmap(p,n);}
int os_nanosleep(void*p,void*q){return nanosleep(p,q);}
int os_clock_gettime(int id,void*p){if(fail_clock){errno=EINVAL;return -1;}return clock_gettime(id==6?CLOCK_MONOTONIC:CLOCK_REALTIME,p);}
int os_rename(const char*a,const char*b){return rename(a,b);}
int os_unlink(const char*p){return unlink(p);}
int os_open(const char*p,int flags,int mode){int native=flags&3;if(flags&0x200)native|=O_CREAT;if(flags&0x800)native|=O_EXCL;if(flags&0x400)native|=O_TRUNC;if(flags&8)native|=O_APPEND;return open(p,native,mode);}
int *os___error(void){return &errno;}
void os__exit(int code){_exit(code);}
int main(void){
    int marker;State*s=(State*)ar_init((U)&marker,0,0,0);assert(s);
    char absent[]="/tmp/assis-missing-directory-ABI/probe";
    assert(ar_file_open((U)absent,0,0,s)==0&&s->error==ENOENT);
    assert(ar_file_remove((U)absent,0,0,s)==(U)-1&&s->error==ENOENT);
    assert(ar_file_replace((U)absent,(U)"/tmp/assis-missing-destination-ABI",0,s)==(U)-1&&s->error==ENOENT);
    U bad=(U)-2;assert(ar_file_sync((U)&bad,0,0,s)==(U)-1&&s->error==EBADF);
    assert(ar_file_close((U)&bad,0,0,s)==(U)-1&&s->error==EBADF);
    assert(ar_sleep(0,0,0,s)==0);
    assert((I)ar_civil(0,0,0,s)>0);
    fail_clock=1;assert(ar_civil(0,0,0,s)==(U)-1&&s->error==EINVAL);fail_clock=0;
    char path[]="/tmp/assis-mac-runtime-XXXXXX";int fd=mkstemp(path);assert(fd>=0);close(fd);
    U file=ar_file_open((U)path,0,0,s);assert(file&&s->error==0);
    assert(ar_file_close(file,0,0,s)==0);s->error=ENOENT;ar_file_drop(file,0,0,s);assert(s->error==ENOENT&&s->live==0);unlink(path);
    puts("Darwin runtime C API return widths and native error propagation: PASS");return 0;
}

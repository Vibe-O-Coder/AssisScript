#define _GNU_SOURCE
#include "assis_worker_v1.h"
#include "../../src/page_restrict.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdio.h>

#define SLOTS 16
static int64_t sequence;
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#include "windows_isolation.inc"
typedef struct {int64_t token;HANDLE process,job,input,output;int64_t memory,cpu;Isolation isolation;} Slot;
#else
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>
#include <stddef.h>
typedef struct {int64_t token;pid_t pid;int input,output;int64_t memory;} Slot;
#endif
static Slot slots[SLOTS];
#if defined(_WIN32) && defined(ASSIS_WORKER_TESTING)
ASSW_API int64_t assw_test_exit(int64_t token){for(int i=0;i<SLOTS;i++)if(slots[i].token==token){DWORD status=0;return GetExitCodeProcess(slots[i].process,&status)?(int64_t)status:-4;}return -2;}
#endif
static int owner_thread(void){
#ifdef _WIN32
    static DWORD owner;DWORD current=GetCurrentThreadId();if(!owner)owner=current;return owner==current;
#else
    return syscall(SYS_gettid)==getpid();
#endif
}
#include "local_resources.inc"
static Slot *find(int64_t token){for(int i=0;i<SLOTS;i++)if(token>0&&slots[i].token==token)return &slots[i];return NULL;}
int64_t assw_version(void){return owner_thread()?1:-6;}
int64_t assw_close(int64_t token){
    if(!owner_thread())return -6;
    Slot *s=find(token);if(!s)return -2;s->token=0;
#ifdef _WIN32
    TerminateJobObject(s->job,125);WaitForSingleObject(s->process,5000);
    CloseHandle(s->input);CloseHandle(s->output);CloseHandle(s->process);CloseHandle(s->job);
    int cleaned=isolation_clean(&s->isolation);
#else
    /* Do not reap before signaling: the pinned PID cannot be reused. */
    kill(-s->pid,SIGKILL);kill(s->pid,SIGKILL);
    while(waitpid(s->pid,NULL,0)<0&&errno==EINTR){}
    close(s->input);close(s->output);
#endif
    memset(s,0,sizeof(*s));
#ifdef _WIN32
    if(!cleaned)return -4;
#endif
    return 0;
}

#ifdef _WIN32
static int64_t transfer(HANDLE pipe,uint8_t *data,int64_t length,int writing){
    if(!data||length<1||length>4096)return -1;DWORD amount=0;
    if(!writing){DWORD available=0;if(!PeekNamedPipe(pipe,NULL,0,NULL,&available,NULL))return GetLastError()==ERROR_BROKEN_PIPE?-5:-4;if(!available)return 0;if(length>available)length=available;}
    BOOL ok=writing?WriteFile(pipe,data,(DWORD)length,&amount,NULL):ReadFile(pipe,data,(DWORD)length,&amount,NULL);
    if(!ok){DWORD e=GetLastError();if(e==ERROR_NO_DATA||e==ERROR_PIPE_BUSY)return 0;return e==ERROR_BROKEN_PIPE?-5:-4;}return amount;
}
static int process_budget(Slot *s){
    FILETIME created,ended,kernel,user;
    if(!GetProcessTimes(s->process,&created,&ended,&kernel,&user))return -4;
    ULARGE_INTEGER ticks;ticks.LowPart=user.dwLowDateTime;ticks.HighPart=user.dwHighDateTime;
    /* Windows Job accounting is checked periodically by the OS. Also enforce
     * at each host I/O turn, so a responsive supervisor observes the overrun
     * without depending on that unspecified periodic check interval. */
    if(ticks.QuadPart>=(ULONGLONG)s->cpu*10000000){TerminateJobObject(s->job,125);return -5;}
    return 0;
}
static int make_pipe(HANDLE *server,HANDLE *client,int input,int64_t id){
    wchar_t name[128];swprintf(name,128,L"\\\\.\\pipe\\assis-worker-%lu-%lld-%d",GetCurrentProcessId(),(long long)id,input);
    *server=CreateNamedPipeW(name,(input?PIPE_ACCESS_OUTBOUND:PIPE_ACCESS_INBOUND)|FILE_FLAG_FIRST_PIPE_INSTANCE,
        PIPE_TYPE_BYTE|PIPE_READMODE_BYTE|PIPE_NOWAIT|PIPE_REJECT_REMOTE_CLIENTS,1,65536,65536,0,NULL);
    if(*server==INVALID_HANDLE_VALUE){*server=NULL;return 0;}
    SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};
    *client=CreateFileW(name,input?GENERIC_READ:GENERIC_WRITE,0,&sa,OPEN_EXISTING,0,NULL);
    if(*client==INVALID_HANDLE_VALUE){*client=NULL;return 0;}
    /* Child uses blocking streams; parent keeps PIPE_NOWAIT on server ends. */
    return 1;
}
static int64_t open_process(const uint8_t *path,int64_t length,int64_t restricted,int64_t memory,int64_t cpu,int compiling,int64_t *output){
    if(output)*output=0;if(!owner_thread())return -6;if(!output||!path||length<3||length>4096||(restricted!=0&&restricted!=1))return -1;
    for(int64_t i=0;i<length;i++)if(!path[i])return -1;
    wchar_t file[4097];int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,(const char*)path,(int)length,file,4096);
    if(!n||n>4095)return -1;file[n]=0;if(!(n>2&&file[1]==L':'&&(file[2]==L'\\'||file[2]==L'/')))return -1;
    int index=0;while(index<SLOTS&&slots[index].token)index++;if(index==SLOTS||sequence==INT64_MAX)return -4;
    int64_t id=++sequence;HANDLE in=NULL,out=NULL,childin=NULL,childout=NULL,err=NULL,job=NULL;PROCESS_INFORMATION pi={0};
    STARTUPINFOEXW si={0};si.StartupInfo.cb=sizeof(si);SIZE_T size=0;int64_t result=-4;Isolation isolation={0};
    if(restricted&&!isolation_prepare(&isolation,file))goto finish;
    ISOLATION_STEP(10);
    if(!make_pipe(&in,&childin,1,id)||!make_pipe(&out,&childout,0,id))goto finish;
    SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};err=CreateFileW(L"NUL",GENERIC_WRITE,FILE_SHARE_WRITE|FILE_SHARE_READ,&sa,OPEN_EXISTING,0,NULL);
    if(err==INVALID_HANDLE_VALUE){err=NULL;goto finish;}
    job=CreateJobObjectW(NULL,NULL);if(!job)goto finish;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits={0};limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_ACTIVE_PROCESS|JOB_OBJECT_LIMIT_PROCESS_MEMORY;
    limits.BasicLimitInformation.LimitFlags|=JOB_OBJECT_LIMIT_PROCESS_TIME;
    limits.BasicLimitInformation.PerProcessUserTimeLimit.QuadPart=cpu*10000000;
    limits.BasicLimitInformation.ActiveProcessLimit=1;limits.ProcessMemoryLimit=(SIZE_T)memory;
    if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&limits,sizeof(limits)))goto finish;
    if(restricted){
        JOBOBJECT_BASIC_UI_RESTRICTIONS ui={0};ui.UIRestrictionsClass=JOB_OBJECT_UILIMIT_HANDLES|JOB_OBJECT_UILIMIT_READCLIPBOARD|
            JOB_OBJECT_UILIMIT_WRITECLIPBOARD|JOB_OBJECT_UILIMIT_SYSTEMPARAMETERS|JOB_OBJECT_UILIMIT_DISPLAYSETTINGS|
            JOB_OBJECT_UILIMIT_GLOBALATOMS|JOB_OBJECT_UILIMIT_DESKTOP|JOB_OBJECT_UILIMIT_EXITWINDOWS;
        if(!SetInformationJobObject(job,JobObjectBasicUIRestrictions,&ui,sizeof(ui)))goto finish;
    }
    ISOLATION_STEP(11);
    DWORD attribute_count=restricted?5:1;
    InitializeProcThreadAttributeList(NULL,attribute_count,0,&size);si.lpAttributeList=HeapAlloc(GetProcessHeap(),0,size);if(!si.lpAttributeList)goto finish;
    if(!InitializeProcThreadAttributeList(si.lpAttributeList,attribute_count,0,&size)){HeapFree(GetProcessHeap(),0,si.lpAttributeList);si.lpAttributeList=NULL;goto finish;}
    HANDLE allowed[]={childin,childout,err};if(!UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,allowed,sizeof(allowed),NULL,NULL))goto finish;
    SECURITY_CAPABILITIES security={0};DWORD opt_out=PROCESS_CREATION_ALL_APPLICATION_PACKAGES_OPT_OUT,children=PROCESS_CREATION_CHILD_PROCESS_RESTRICTED;
    /* Win32k lockdown is not part of this profile. The existing native
     * runtime still imports Shell32 for Unicode argv. */
    DWORD64 mitigation=PROCESS_CREATION_MITIGATION_POLICY_PROHIBIT_DYNAMIC_CODE_ALWAYS_ON|PROCESS_CREATION_MITIGATION_POLICY_EXTENSION_POINT_DISABLE_ALWAYS_ON;
    if(restricted){
        ISOLATION_STEP(12);
        security.AppContainerSid=isolation.sid;
        if(ISOLATION_FAIL(4)||!UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,&security,sizeof(security),NULL,NULL)||
           !UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY,&opt_out,sizeof(opt_out),NULL,NULL)||
           !UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY,&children,sizeof(children),NULL,NULL)||
           !UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_MITIGATION_POLICY,&mitigation,sizeof(mitigation),NULL,NULL))goto finish;
        wcscpy(file,isolation.file);
    }
    si.StartupInfo.dwFlags=STARTF_USESTDHANDLES;si.StartupInfo.hStdInput=childin;si.StartupInfo.hStdOutput=childout;si.StartupInfo.hStdError=err;
    wchar_t command[8250];swprintf(command,8250,L"\"%ls\"%ls",file,compiling?L" page-compile-worker":L"");
    wchar_t environment[2048]={0};wchar_t windows[260];UINT wn=GetWindowsDirectoryW(windows,260);if(!wn||wn>=260)goto finish;
    swprintf(environment,2046,L"SystemRoot=%ls",windows); /* double NUL; no inherited secrets */
    if(restricted){
        wchar_t profile[MAX_PATH],appdata[MAX_PATH];DWORD pn=GetEnvironmentVariableW(L"USERPROFILE",profile,MAX_PATH),an=GetEnvironmentVariableW(L"LOCALAPPDATA",appdata,MAX_PATH);
        if(!pn||pn>=MAX_PATH||!an||an>=MAX_PATH)goto finish;
        wchar_t *at=environment+wcslen(environment)+1;
        swprintf(at,2046-(at-environment),L"USERPROFILE=%ls",profile);at+=wcslen(at)+1;
        swprintf(at,2046-(at-environment),L"LOCALAPPDATA=%ls",appdata);
    }
    wchar_t directory[4097];wcscpy(directory,file);wchar_t *slash=wcsrchr(directory,L'\\');wchar_t *slash2=wcsrchr(directory,L'/');if(!slash||(slash2&&slash2>slash))slash=slash2;if(!slash)goto finish;*slash=0;
    ISOLATION_STEP(13);
    /* CREATE_NO_WINDOW triggers console initialization failure for these
     * AppContainer console images. DETACHED_PROCESS preserves only our
     * explicit std handles and needs no global LowBoxConsoleEnabled setting. */
    if(!CreateProcessW(file,command,NULL,NULL,TRUE,EXTENDED_STARTUPINFO_PRESENT|CREATE_SUSPENDED|DETACHED_PROCESS|CREATE_UNICODE_ENVIRONMENT,environment,directory,&si.StartupInfo,&pi))goto finish;
    ISOLATION_STEP(14);
    /* Verify while suspended. There is no fallback to a plain process. */
    if(restricted){int checked=page_windows_isolated(pi.hProcess,isolation.sid);if(ISOLATION_FAIL(5)||checked!=1){ISOLATION_STEP(100-checked);goto finish;}}
    ISOLATION_STEP(15);
    if(!AssignProcessToJobObject(job,pi.hProcess)||(restricted&&ISOLATION_FAIL(6))||ResumeThread(pi.hThread)==(DWORD)-1)goto finish;
    slots[index]=(Slot){id,pi.hProcess,job,in,out,memory,cpu,{0}};slots[index].isolation=isolation;memset(&isolation,0,sizeof(isolation));
    *output=id;result=0;pi.hProcess=NULL;job=in=out=NULL;
finish:
    ISOLATION_ERROR();
    if(pi.hProcess){TerminateProcess(pi.hProcess,125);WaitForSingleObject(pi.hProcess,5000);CloseHandle(pi.hProcess);}if(pi.hThread)CloseHandle(pi.hThread);
    if(si.lpAttributeList){DeleteProcThreadAttributeList(si.lpAttributeList);HeapFree(GetProcessHeap(),0,si.lpAttributeList);}
    if(in)CloseHandle(in);if(out)CloseHandle(out);if(childin)CloseHandle(childin);if(childout)CloseHandle(childout);if(err)CloseHandle(err);if(job)CloseHandle(job);
    isolation_clean(&isolation);return result;
}
int64_t assw_send(int64_t t,const uint8_t *p,int64_t n){if(!owner_thread())return -6;Slot *s=find(t);if(!s)return -2;int budget=process_budget(s);return budget?budget:transfer(s->input,(uint8_t*)p,n,1);}
int64_t assw_receive(int64_t t,uint8_t *p,int64_t n){if(!owner_thread())return -6;Slot *s=find(t);if(!s)return -2;int budget=process_budget(s);return budget?budget:transfer(s->output,p,n,0);}
int64_t assw_child_read(uint8_t *p,int64_t n){if(!p||n<1||n>4096)return -1;DWORD count=0;return ReadFile(GetStdHandle(STD_INPUT_HANDLE),p,(DWORD)n,&count,NULL)?(count?(int64_t)count:-5):-5;}
int64_t assw_child_write(const uint8_t *p,int64_t n){if(!p||n<1||n>4096)return -1;DWORD count=0;return WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),p,(DWORD)n,&count,NULL)?(int64_t)count:-5;}
int64_t assw_restrict(void){int result=page_windows_isolated(GetCurrentProcess(),NULL);return result<0?-4:result;}
#else
static int64_t open_process(const uint8_t *path,int64_t length,int64_t restricted,int64_t memory,int64_t cpu,int compiling,int64_t *output){
    if(output)*output=0;if(!owner_thread())return -6;if(!output||!path||length<2||length>4096||path[0]!='/'||(restricted!=0&&restricted!=1))return -1;
    for(int64_t i=0;i<length;i++)if(!path[i])return -1;
    char file[4097];memcpy(file,path,length);file[length]=0;char resolved[4097];if(!realpath(file,resolved))return -4;
    int index=0;while(index<SLOTS&&slots[index].token)index++;if(index==SLOTS||sequence==INT64_MAX)return -4;
    int in[2],out[2];if(pipe2(in,O_CLOEXEC))return -4;if(pipe2(out,O_CLOEXEC)){close(in[0]);close(in[1]);return -4;}
    pid_t parent=getpid();pid_t pid=fork();
    if(pid==0){
        if(prctl(PR_SET_PDEATHSIG,SIGKILL)||getppid()!=parent||setpgid(0,0))_exit(126);
        struct rlimit mem={(rlim_t)memory,(rlim_t)memory},clock={(rlim_t)cpu,(rlim_t)cpu},stack={8*1024*1024,8*1024*1024},core={0,0};
        if(setrlimit(RLIMIT_AS,&mem)||setrlimit(RLIMIT_CPU,&clock)||setrlimit(RLIMIT_STACK,&stack)||setrlimit(RLIMIT_CORE,&core))_exit(126);
        if(dup2(in[0],0)<0||dup2(out[1],1)<0)_exit(126);
        int null=open("/dev/null",O_WRONLY|O_CLOEXEC);if(null<0||dup2(null,2)<0)_exit(126);
        if(syscall(SYS_close_range,3,~0U,0)<0)_exit(126);
        if(chdir("/"))_exit(126);
        char loader[4160]="LD_LIBRARY_PATH=";strcat(loader,resolved);char *slash=strrchr(loader,'/');if(!slash)_exit(126);*slash=0;
        char *env[]={"LANG=C.UTF-8",loader,NULL};char *argv[]={resolved,compiling?"page-compile-worker":NULL,NULL};execve(resolved,argv,env);_exit(127);
    }
    close(in[0]);close(out[1]);if(pid<0){close(in[1]);close(out[0]);return -4;}
    setpgid(pid,pid);
    int64_t id=++sequence;slots[index]=(Slot){id,pid,in[1],out[0],memory};
    if(fcntl(in[1],F_SETFL,O_NONBLOCK)||fcntl(out[0],F_SETFL,O_NONBLOCK)){assw_close(id);return -4;}
    /* Process-wide SIGPIPE changes would affect the trusted host. Suppress it
     * only around writes below, and consume only our newly pending signal. */
    *output=id;return 0;
}
#include <pthread.h>
#include <time.h>
static int64_t write_pipe(int fd,const uint8_t *p,int64_t n){
    sigset_t set,old,pending;sigemptyset(&set);sigaddset(&set,SIGPIPE);if(pthread_sigmask(SIG_BLOCK,&set,&old))return -4;
    sigpending(&pending);int prior=sigismember(&pending,SIGPIPE);ssize_t result=write(fd,p,(size_t)n);int error=errno;
    if(result<0&&error==EPIPE&&!prior){struct timespec zero={0};sigtimedwait(&set,NULL,&zero);}
    pthread_sigmask(SIG_SETMASK,&old,NULL);
    if(result>=0)return result;if(error==EAGAIN||error==EINTR)return 0;return error==EPIPE?-5:-4;
}
int64_t assw_send(int64_t t,const uint8_t *p,int64_t n){if(!owner_thread())return -6;Slot *s=find(t);if(!s)return -2;if(!p||n<1||n>4096)return -1;return write_pipe(s->input,p,n);}
int64_t assw_receive(int64_t t,uint8_t *p,int64_t n){if(!owner_thread())return -6;Slot *s=find(t);if(!s)return -2;if(!p||n<1||n>4096)return -1;ssize_t r=read(s->output,p,n);if(r>0)return r;if(!r)return -5;return errno==EAGAIN||errno==EINTR?0:-4;}
int64_t assw_child_read(uint8_t *p,int64_t n){if(!p||n<1||n>4096)return -1;ssize_t r=read(0,p,n);return r>0?r:r==0?-5:errno==EINTR?0:-4;}
int64_t assw_child_write(const uint8_t *p,int64_t n){if(!p||n<1||n>4096)return -1;ssize_t r=write(1,p,n);return r>=0?r:errno==EINTR?0:-5;}
int64_t assw_restrict(void){
#if defined(__x86_64__)
    struct rlimit mem={128*1024*1024,128*1024*1024},cpu={3,3},files={3,3},core={0,0},stack={8*1024*1024,8*1024*1024};
    if(setrlimit(RLIMIT_AS,&mem)||setrlimit(RLIMIT_CPU,&cpu)||setrlimit(RLIMIT_NOFILE,&files)||setrlimit(RLIMIT_CORE,&core)||setrlimit(RLIMIT_STACK,&stack)||prctl(PR_SET_DUMPABLE,0)||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return -4;
    return page_stream_restrict();
#else
    return -3;
#endif
}
#endif
int64_t assw_open(const uint8_t *p,int64_t n,int64_t restricted,int64_t *out){
    return open_process(p,n,restricted,128*1024*1024,3,0,out);
}
int64_t assw_compile_open(const uint8_t *p,int64_t n,int64_t mib,int64_t seconds,int64_t *out){
    if(out)*out=0;if(!owner_thread())return -6;
    if(mib<16||mib>512||seconds<1||seconds>10)return -1;
    return open_process(p,n,
#ifdef _WIN32
        1,
#else
        0,
#endif
        mib*1024*1024,seconds,1,out);
}
int64_t assw_usage(int64_t token,int64_t *out,int64_t capacity){
    if(!owner_thread())return -6;if(!out||capacity<6)return -1;memset(out,0,6*sizeof(*out));
    Slot *s=find(token);if(!s)return -2;
    out[0]=1;out[1]=s->memory;
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX info;memset(&info,0,sizeof(info));info.cb=sizeof(info);
    if(!GetProcessMemoryInfo(s->process,(PROCESS_MEMORY_COUNTERS*)&info,sizeof(info)))return -4;
    out[2]=(int64_t)info.WorkingSetSize;out[3]=(int64_t)info.PeakWorkingSetSize;out[4]=(int64_t)info.PrivateUsage;
    DWORD code=0;if(!GetExitCodeProcess(s->process,&code))return -4;out[5]=code==STILL_ACTIVE?1:2;
#else
    char path[64],line[256];snprintf(path,sizeof(path),"/proc/%ld/status",(long)s->pid);
    FILE *f=fopen(path,"r");if(!f)return -4;
    out[5]=1;while(fgets(line,sizeof(line),f)){
        unsigned long long value;
        if(sscanf(line,"VmRSS: %llu kB",&value)==1)out[2]=(int64_t)value*1024;
        else if(sscanf(line,"VmHWM: %llu kB",&value)==1)out[3]=(int64_t)value*1024;
        else if(sscanf(line,"VmSize: %llu kB",&value)==1)out[4]=(int64_t)value*1024;
        else if(!strncmp(line,"State:",6)&&(strchr(line,'Z')||strchr(line,'X')))out[5]=2;
    }
    fclose(f);
#endif
    return 0;
}

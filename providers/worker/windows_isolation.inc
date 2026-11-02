/* LPAC with a fresh identity and an ephemeral AppContainer profile per spawn.
 * Only two fixed trusted runtime files are copied, never page data. A protected
 * DACL grants this SID read/execute and the current user/System full control.
 * No ACL of an existing file, user directory or executable is changed. */
#include <sddl.h>
#include <userenv.h>
#include <bcrypt.h>
#include "../../src/page_windows_token.h"
#ifndef PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY
#define PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY ProcThreadAttributeValue(15,FALSE,TRUE,FALSE)
#endif
#ifndef PROCESS_CREATION_ALL_APPLICATION_PACKAGES_OPT_OUT
#define PROCESS_CREATION_ALL_APPLICATION_PACKAGES_OPT_OUT 1
#endif
#ifndef PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY
#define PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY ProcThreadAttributeValue(14,FALSE,TRUE,FALSE)
#endif
#ifndef PROCESS_CREATION_CHILD_PROCESS_RESTRICTED
#define PROCESS_CREATION_CHILD_PROCESS_RESTRICTED 1
#endif
typedef struct {PSID sid;wchar_t directory[MAX_PATH],file[MAX_PATH],dll[MAX_PATH],profile[80];} Isolation;
#ifdef ASSIS_WORKER_TESTING
static int injected_failure;
static int diagnostic_step;static DWORD diagnostic_error;
ASSW_API int64_t assw_test_failure(int64_t step){injected_failure=(int)step;return 0;}
ASSW_API int64_t assw_test_status(void){return ((int64_t)diagnostic_step<<32)|diagnostic_error;}
#define ISOLATION_FAIL(n) (injected_failure==(n))
#define ISOLATION_STEP(n) (diagnostic_step=(n))
#define ISOLATION_ERROR() (diagnostic_error=GetLastError())
#else
#define ISOLATION_FAIL(n) 0
#define ISOLATION_STEP(n) ((void)0)
#define ISOLATION_ERROR() ((void)0)
#endif
static int isolation_clean(Isolation *s){
    int ok=1;
    if(s->file[0]&&!DeleteFileW(s->file)&&GetLastError()!=ERROR_FILE_NOT_FOUND)ok=0;
    if(s->dll[0]&&!DeleteFileW(s->dll)&&GetLastError()!=ERROR_FILE_NOT_FOUND)ok=0;
    if(s->directory[0]&&!RemoveDirectoryW(s->directory)&&GetLastError()!=ERROR_PATH_NOT_FOUND)ok=0;
    if(s->profile[0]&&FAILED(DeleteAppContainerProfile(s->profile)))ok=0;
    if(s->sid)FreeSid(s->sid);memset(s,0,sizeof(*s));return ok;
}
static int isolation_prepare(Isolation *s,const wchar_t *source){
    BYTE random[16];wchar_t temp[MAX_PATH],name[80];LPWSTR sid_text=NULL,user_text=NULL;HANDLE token=NULL;
    PSECURITY_DESCRIPTOR descriptor=NULL;int result=0;DWORD size=0;union{void *align;BYTE bytes[512];} user;
    ISOLATION_STEP(1);if(ISOLATION_FAIL(1)||BCryptGenRandom(NULL,random,sizeof(random),BCRYPT_USE_SYSTEM_PREFERRED_RNG)<0)return 0;
    wcscpy(name,L"assis-lpac-");for(int i=0;i<16;i++)swprintf(name+11+2*i,3,L"%02x",random[i]);
    /* Never attach to an existing profile or reuse another instance's data. */
    ISOLATION_STEP(2);if(FAILED(CreateAppContainerProfile(name,name,L"Ephemeral AssisScript worker",NULL,0,&s->sid)))goto finish;
    wcscpy(s->profile,name);
    if(!ConvertSidToStringSidW(s->sid,&sid_text)||!OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token)||
       !GetTokenInformation(token,TokenUser,user.bytes,sizeof(user.bytes),&size)||
       !ConvertSidToStringSidW(((TOKEN_USER*)user.bytes)->User.Sid,&user_text))goto finish;
    ISOLATION_STEP(3);wchar_t sddl[1024];swprintf(sddl,1024,L"D:P(A;OICI;GA;;;%ls)(A;OICI;GA;;;SY)(A;OICI;GRGX;;;%ls)",user_text,sid_text);
    if(!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,SDDL_REVISION_1,&descriptor,NULL))goto finish;
    DWORD n=GetTempPathW(MAX_PATH,temp);if(!n||n>=MAX_PATH||n+wcslen(name)+21>=MAX_PATH)goto finish;
    swprintf(s->directory,MAX_PATH,L"%ls%ls",temp,name);
    SECURITY_ATTRIBUTES attributes={sizeof(attributes),descriptor,FALSE};
    ISOLATION_STEP(4);if(!CreateDirectoryW(s->directory,&attributes)){s->directory[0]=0;goto finish;}
    if(ISOLATION_FAIL(2))goto finish;
    swprintf(s->file,MAX_PATH,L"%ls\\runtime.exe",s->directory);
    swprintf(s->dll,MAX_PATH,L"%ls\\assis_worker_v1.dll",s->directory);
    /* CopyFile preserves source attributes, including a source DACL on some
     * Windows versions. Explicitly apply our protected DACL to the copies. */
    ISOLATION_STEP(5);if(!CopyFileW(source,s->file,TRUE)||!SetFileSecurityW(s->file,DACL_SECURITY_INFORMATION|PROTECTED_DACL_SECURITY_INFORMATION,descriptor))goto finish;
    HMODULE module=NULL;wchar_t provider[MAX_PATH];
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCWSTR)(uintptr_t)&assw_version,&module)||!GetModuleFileNameW(module,provider,MAX_PATH)||wcslen(provider)>=MAX_PATH-1)goto finish;
    ISOLATION_STEP(6);if(!CopyFileW(provider,s->dll,TRUE)||!SetFileSecurityW(s->dll,DACL_SECURITY_INFORMATION|PROTECTED_DACL_SECURITY_INFORMATION,descriptor))goto finish;
    if(ISOLATION_FAIL(3))goto finish;result=1;
finish:
    if(token)CloseHandle(token);if(sid_text)LocalFree(sid_text);if(user_text)LocalFree(user_text);if(descriptor)LocalFree(descriptor);
    return result;
}

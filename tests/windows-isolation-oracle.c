/* Independent Win32 client: deliberately attempts native operations that page
 * bytecode cannot express. No product token/isolation helper is linked. */
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <windows.h>
#include <sddl.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static int access_probe(HANDLE token,const wchar_t *sddl){
    PSECURITY_DESCRIPTOR sd=NULL;HANDLE duplicate=NULL;DWORD granted=0,size=1024;BOOL permitted=FALSE;
    union{void *align;BYTE bytes[1024];} privileges;GENERIC_MAPPING mapping={1,1,1,1};int result=-1;
    if(!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,&sd,NULL)||!DuplicateToken(token,SecurityImpersonation,&duplicate))goto done;
    if(AccessCheck(sd,duplicate,1,&mapping,(PRIVILEGE_SET*)privileges.bytes,&size,&granted,&permitted))result=permitted?1:0;
done:if(duplicate)CloseHandle(duplicate);if(sd)LocalFree(sd);return result;
}
static DWORD file_attempt(const wchar_t *path,DWORD access,DWORD creation){
    HANDLE h=CreateFileW(path,access,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,creation,0,NULL);
    if(h==INVALID_HANDLE_VALUE)return GetLastError();CloseHandle(h);return 0;
}
static int line(wchar_t *out){char in[4096];if(!fgets(in,sizeof(in),stdin))return 0;size_t n=strcspn(in,"\r\n");in[n]=0;return MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,in,-1,out,4096)!=0;}
int main(void){
    HANDLE token=NULL;DWORD got=0,app=0;union{void *align;BYTE bytes[1024];} buffer;LPWSTR sid=NULL;
    if(!OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY|TOKEN_DUPLICATE,&token)||!GetTokenInformation(token,TokenIsAppContainer,&app,sizeof(app),&got)||
       !GetTokenInformation(token,TokenAppContainerSid,buffer.bytes,sizeof(buffer.bytes),&got)||
       !ConvertSidToStringSidW(((TOKEN_APPCONTAINER_INFORMATION*)buffer.bytes)->TokenAppContainer,&sid))return 2;
    char sid8[256];WideCharToMultiByte(CP_UTF8,0,sid,-1,sid8,sizeof(sid8),NULL,NULL);LocalFree(sid);
    if(!GetTokenInformation(token,TokenCapabilities,buffer.bytes,sizeof(buffer.bytes),&got))return 3;
    DWORD capabilities=((TOKEN_GROUPS*)buffer.bytes)->GroupCount;
    int all=access_probe(token,L"O:SYG:SYD:(A;;0x1;;;WD)(A;;0x1;;;AC)");
    int restricted=access_probe(token,L"O:SYG:SYD:(A;;0x1;;;WD)(A;;0x1;;;S-1-15-2-2)");
    CloseHandle(token);
    PROCESS_MITIGATION_DYNAMIC_CODE_POLICY dynamic={0};PROCESS_MITIGATION_EXTENSION_POINT_DISABLE_POLICY extensions={0};
    if(!GetProcessMitigationPolicy(GetCurrentProcess(),ProcessDynamicCodePolicy,&dynamic,sizeof(dynamic))||
       !GetProcessMitigationPolicy(GetCurrentProcess(),ProcessExtensionPointDisablePolicy,&extensions,sizeof(extensions)))return 4;
    wchar_t own[4096];GetModuleFileNameW(NULL,own,4096);char own8[4096];WideCharToMultiByte(CP_UTF8,0,own,-1,own8,sizeof(own8),NULL,NULL);
    printf("IDENTITY %lu %lu %d %d %lu %lu %s\nPATH %s\n",app,capabilities,all,restricted,(unsigned long)dynamic.ProhibitDynamicCode,(unsigned long)extensions.DisableExtensionPoints,sid8,own8);fflush(stdout);
    wchar_t private_path[4096],neighbor[4096],key[4096],numbers[4096];if(!line(private_path)||!line(neighbor)||!line(key)||!line(numbers))return 5;
    unsigned long pid=0,port=0;unsigned long long inherited=0;swscanf(numbers,L"%lu %llu %lu",&pid,&inherited,&port);
    DWORD flags=0;int handle_visible=GetHandleInformation((HANDLE)(uintptr_t)inherited,&flags)!=0;
    HANDLE parent=OpenProcess(PROCESS_VM_READ|PROCESS_VM_WRITE|PROCESS_TERMINATE,FALSE,pid);DWORD process=parent?0:GetLastError();if(parent)CloseHandle(parent);
    HKEY registry=NULL;LSTATUS registry_status=RegOpenKeyExW(HKEY_CURRENT_USER,key,0,KEY_READ,&registry);if(!registry_status)RegCloseKey(registry);
    DWORD own_read=file_attempt(own,GENERIC_READ,OPEN_EXISTING),own_write=file_attempt(own,GENERIC_WRITE,OPEN_EXISTING);
    DWORD read=file_attempt(private_path,GENERIC_READ,OPEN_EXISTING),write=file_attempt(private_path,GENERIC_WRITE,OPEN_EXISTING);
    DWORD other=file_attempt(neighbor,GENERIC_READ,OPEN_EXISTING);wchar_t *slash=wcsrchr(own,L'\\');wcscpy(slash+1,L"page-created.txt");
    DWORD create=file_attempt(own,GENERIC_WRITE,CREATE_NEW);
    void *exec=VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);DWORD executable=exec?0:GetLastError();if(exec)VirtualFree(exec,0,MEM_RELEASE);
    STARTUPINFOW startup={sizeof(startup)};PROCESS_INFORMATION pi={0};wchar_t child[MAX_PATH];GetSystemDirectoryW(child,MAX_PATH);wcscat(child,L"\\whoami.exe");
    BOOL child_ok=CreateProcessW(child,NULL,NULL,NULL,FALSE,DETACHED_PROCESS,NULL,NULL,&startup,&pi);DWORD child_error=child_ok?0:GetLastError();
    if(child_ok){TerminateProcess(pi.hProcess,1);WaitForSingleObject(pi.hProcess,1000);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);}
    WSADATA data;int socket_error=0,startup_error=WSAStartup(MAKEWORD(2,2),&data);if(startup_error)socket_error=startup_error;
    else{SOCKET s=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);if(s==INVALID_SOCKET)socket_error=WSAGetLastError();else{
        struct sockaddr_in target={0};target.sin_family=AF_INET;target.sin_port=htons((u_short)port);target.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
        if(connect(s,(struct sockaddr*)&target,sizeof(target)))socket_error=WSAGetLastError();closesocket(s);}WSACleanup();}
    BOOL clipboard=OpenClipboard(NULL);DWORD clipboard_error=clipboard?0:GetLastError();if(clipboard)CloseClipboard();
    char secret[8];int environment=GetEnvironmentVariableA("ASSIS_WORKER_SECRET",secret,sizeof(secret))!=0;
    printf("RESULT %lu %lu %lu %lu %lu %lu %ld %d %d %lu %lu %d %lu\n",own_read,own_write,read,write,other,create,(long)registry_status,handle_visible,environment,process,child_error,socket_error,executable);
    printf("CLIPBOARD %lu\n",clipboard_error);fflush(stdout);return 0;
}

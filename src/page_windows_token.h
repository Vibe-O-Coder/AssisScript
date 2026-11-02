#ifndef ASSIS_PAGE_WINDOWS_TOKEN_H
#define ASSIS_PAGE_WINDOWS_TOKEN_H
#ifdef _WIN32
/* No capability SID is granted. Verify the actual kernel token, never an
 * environment variable or an IPC claim. Dynamic import keeps the standalone
 * compiler's existing link contract (Kernel32/UCRT) intact. */
static int page_windows_isolated(HANDLE process,PSID expected){
    typedef BOOL (WINAPI *OpenToken)(HANDLE,DWORD,PHANDLE);
    typedef BOOL (WINAPI *GetInfo)(HANDLE,TOKEN_INFORMATION_CLASS,LPVOID,DWORD,PDWORD);
    HMODULE adv=LoadLibraryExW(L"advapi32.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!adv)return -1;
    OpenToken open_token=NULL;GetInfo info=NULL;FARPROC fn=GetProcAddress(adv,"OpenProcessToken");memcpy(&open_token,&fn,sizeof(fn));
    fn=GetProcAddress(adv,"GetTokenInformation");memcpy(&info,&fn,sizeof(fn));
    HANDLE token=NULL;int result=-1;DWORD got=0,app=0;
    union {void *align;BYTE bytes[512];} buffer;
    result=-10;if(!open_token||!info||!open_token(process,TOKEN_QUERY,&token))goto finish;
    result=-11;
    if(!info(token,TokenIsAppContainer,&app,sizeof(app),&got))goto finish;
    if(!app){result=0;goto finish;}
    result=-13;if(!info(token,TokenCapabilities,buffer.bytes,sizeof(buffer.bytes),&got)||((TOKEN_GROUPS*)buffer.bytes)->GroupCount)goto finish;
    result=-14;if(!info(token,TokenAppContainerSid,buffer.bytes,sizeof(buffer.bytes),&got))goto finish;
    if(expected){
        typedef BOOL (WINAPI *Equal)(PSID,PSID);Equal equal=NULL;
        fn=GetProcAddress(adv,"EqualSid");memcpy(&equal,&fn,sizeof(fn));
        if(!equal||!equal(expected,((TOKEN_APPCONTAINER_INFORMATION*)buffer.bytes)->TokenAppContainer))goto finish;
    }
    result=1;
finish:
    if(token)CloseHandle(token);FreeLibrary(adv);return result;
}
#endif
#endif

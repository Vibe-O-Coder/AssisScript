#define WIN32_LEAN_AND_MEAN
#define COBJMACROS
#include <windows.h>
#include <oleacc.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include <stdlib.h>

#define CHECK(x) do {if (!(x)) {fprintf(stderr,"line %d: %s\n",__LINE__,#x); return 1;}} while(0)
typedef int32_t (*Open)(int64_t,int32_t,int32_t,const uint8_t *,int64_t,int64_t *);
typedef int32_t (*Close)(int64_t);
typedef int32_t (*Poll)(int64_t,int32_t,int64_t *,int64_t);
typedef int64_t (*Control)(int64_t,int64_t);
typedef int32_t (*Publish)(int64_t,int64_t,const int64_t *,int64_t,const uint8_t *,int64_t);
typedef int64_t (*Measure)(const uint8_t *,int64_t,int32_t);
typedef int32_t (*Copy)(int64_t,const uint8_t *,int64_t);
#define LOAD(target,symbol) do {FARPROC function=GetProcAddress(dll,symbol); CHECK(function!=NULL); memcpy(&(target),&function,sizeof(target));} while(0)
static VARIANT child(LONG n) {VARIANT v;VariantInit(&v);V_VT(&v)=VT_I4;V_I4(&v)=n;return v;}
static DWORD WINAPI wrong_thread(void *pointer) {
    IAccessible *a=pointer;BSTR name=NULL;
    HRESULT hr=IAccessible_get_accName(a,child(0),&name);if(name)SysFreeString(name);
    return hr==RPC_E_WRONG_THREAD ? 0 : 1;
}
int main(int argc,char **argv) {
    CHECK(argc>=2);
    if(argc==3 && !strcmp(argv[1],"--transaction-client")) {
        CHECK(SUCCEEDED(OleInitialize(NULL)));
        HWND target=(HWND)(uintptr_t)strtoull(argv[2],NULL,10);
        for(int phase=0;phase<3;phase++) {
            IAccessible *a=NULL;LONG total=0;
            CHECK(AccessibleObjectFromWindow(target,OBJID_CLIENT,&IID_IAccessible,(void **)&a)==S_OK);
            CHECK(IAccessible_get_accChildCount(a,&total)==S_OK && total==(phase==1 ? 4 : 3));
            BSTR name=NULL;CHECK(IAccessible_get_accName(a,child(3),&name)==S_OK);
            CHECK(wcscmp(name,L"Mostrar ou ocultar detalhes")==0);SysFreeString(name);
            if(phase<2) {
                CHECK(IAccessible_accDoDefaultAction(a,child(3))==S_OK);
                HRESULT result=S_OK;
                for(int wait=0;wait<200 && SUCCEEDED(result);wait++) {
                    Sleep(10);result=IAccessible_get_accChildCount(a,&total);
                }
                CHECK(FAILED(result)); /* old remote COM reference is revoked */
            }
            IAccessible_Release(a);
        }
        OleUninitialize();puts("PASS transactional external MSAA client");return 0;
    }
    if(argc==3 && !strcmp(argv[1],"--client")) {
        CHECK(SUCCEEDED(OleInitialize(NULL)));IAccessible *a=NULL;
        HWND target=(HWND)(uintptr_t)strtoull(argv[2],NULL,10);
        CHECK(AccessibleObjectFromWindow(target,OBJID_CLIENT,&IID_IAccessible,(void **)&a)==S_OK);
        LONG total=0;CHECK(IAccessible_get_accChildCount(a,&total)==S_OK && total==4);
        BSTR name=NULL;CHECK(IAccessible_get_accName(a,child(3),&name)==S_OK && wcscmp(name,L"Run")==0);SysFreeString(name);
        CHECK(IAccessible_accDoDefaultAction(a,child(3))==S_OK);
        CHECK(IAccessible_accDoDefaultAction(a,child(4))==E_ACCESSDENIED);
        IAccessible_Release(a);OleUninitialize();puts("PASS external MSAA client");return 0;
    }
    int clipboard=argc==3;
    HWINSTA original_station=NULL,station=NULL;HDESK original_desktop=NULL,desktop=NULL;
    if(clipboard) {
        /* This process gets a separate clipboard, never the user's clipboard. */
        original_station=GetProcessWindowStation();original_desktop=GetThreadDesktop(GetCurrentThreadId());
        station=CreateWindowStationW(NULL,0,WINSTA_ALL_ACCESS,NULL);CHECK(station);
        CHECK(SetProcessWindowStation(station));
        desktop=CreateDesktopW(L"AssisReaderClipboard",NULL,NULL,0,DESKTOP_CREATEWINDOW|DESKTOP_READOBJECTS|DESKTOP_WRITEOBJECTS,NULL);
        CHECK(desktop && SetThreadDesktop(desktop));
    }
    HMODULE dll=LoadLibraryA(argv[1]);CHECK(dll);
    Open open_window;Close close_window;Poll poll;Control control;Publish publish;Measure measure;Copy copy;
    LOAD(open_window,"assisp_open");LOAD(close_window,"assisp_close");LOAD(poll,"assisp_poll");LOAD(control,"assisp_test_control");
    LOAD(publish,"assisp_accessibility");LOAD(measure,"assisp_measure_scaled");LOAD(copy,"assisp_clipboard_utf8");
    int64_t token=0;CHECK(open_window(1,400,250,(const uint8_t *)"oracle",6,&token)==0);
    HWND hwnd=(HWND)(uintptr_t)control(4,token);
    if(clipboard) {
        CHECK(copy(token,(const uint8_t *)"A\xc3\xa7\xc3\xa3o\n\xf0\x9f\x98\x80",11)==0);
        CHECK(OpenClipboard(hwnd));HGLOBAL value=GetClipboardData(CF_UNICODETEXT);CHECK(value);
        wchar_t *wide=GlobalLock(value);CHECK(wide && wcscmp(wide,L"A\x00e7\x00e3o\r\n\xd83d\xde00")==0);
        GlobalUnlock(value);CHECK(CloseClipboard());
        CHECK(copy(token,(const uint8_t *)"x\0y",3)==-1);
        CHECK(control(0,0)==0);CHECK(copy(token,(const uint8_t *)"new",3)==-4);CHECK(control(0,-1)==0);
        CHECK(OpenClipboard(hwnd));value=GetClipboardData(CF_UNICODETEXT);wide=GlobalLock(value);
        CHECK(wide && wcscmp(wide,L"A\x00e7\x00e3o\r\n\xd83d\xde00")==0);GlobalUnlock(value);CHECK(CloseClipboard());
        CHECK(close_window(token)==0);CHECK(SetThreadDesktop(original_desktop));CHECK(SetProcessWindowStation(original_station));
        CHECK(CloseDesktop(desktop));CHECK(CloseWindowStation(station));FreeLibrary(dll);puts("PASS isolated clipboard");return 0;
    }
    int64_t records[40]={
        1,0,0,0,400,250,0,5,
        8,0,24,20,352,24,5,7,
        6,0,24,55,352,24,12,9,
        9,2,24,90,352,24,21,4,
        9,1,24,125,352,24,25,8};
    const uint8_t names[]="TitleHeadingParagraphNameDisabled";
    CHECK(sizeof(names)-1==33);CHECK(publish(token,1,records,5,names,33)==0);
    IAccessible *access=NULL;CHECK(AccessibleObjectFromWindow(hwnd,OBJID_CLIENT,&IID_IAccessible,(void **)&access)==S_OK);
    LONG count=0;CHECK(IAccessible_get_accChildCount(access,&count)==S_OK && count==4);
    BSTR name=NULL;CHECK(IAccessible_get_accName(access,child(3),&name)==S_OK && wcscmp(name,L"Name")==0);SysFreeString(name);
    VARIANT value;CHECK(IAccessible_get_accRole(access,child(3),&value)==S_OK && V_VT(&value)==VT_I4 && V_I4(&value)==ROLE_SYSTEM_PUSHBUTTON);
    CHECK(IAccessible_get_accState(access,child(4),&value)==S_OK && (V_I4(&value)&STATE_SYSTEM_UNAVAILABLE));
    CHECK(IAccessible_get_accDescription(access,child(1),&name)==S_OK && wcscmp(name,L"heading")==0);SysFreeString(name);
    CHECK(IAccessible_accNavigate(access,NAVDIR_FIRSTCHILD,child(0),&value)==S_OK && V_I4(&value)==1);
    CHECK(IAccessible_accNavigate(access,NAVDIR_NEXT,child(3),&value)==S_OK && V_I4(&value)==4);
    CHECK(IAccessible_accNavigate(access,NAVDIR_NEXT,child(4),&value)==S_FALSE);
    LONG x,y,width,height;CHECK(IAccessible_accLocation(access,&x,&y,&width,&height,child(3))==S_OK && width==352 && height==24);
    CHECK(IAccessible_accHitTest(access,x+1,y+1,&value)==S_OK && V_I4(&value)==3);
    CHECK(IAccessible_accHitTest(access,LONG_MIN,LONG_MAX,&value)==S_FALSE);
    VARIANT invalid=child(0);V_VT(&invalid)=VT_EMPTY;
    CHECK(IAccessible_get_accName(access,invalid,&name)==E_INVALIDARG && !name);
    CHECK(IAccessible_accDoDefaultAction(access,child(4))==E_ACCESSDENIED);
    CHECK(IAccessible_accDoDefaultAction(access,child(3))==S_OK);
    int64_t event[8];int found=0;
    for(int i=0;i<300;i++){int r=poll(token,0,event,8);CHECK(r==0||r==1);if(!r&&event[1]==11){CHECK(event[5]==1&&event[6]==3);found=1;break;}}
    CHECK(found);
    HANDLE thread=CreateThread(NULL,0,wrong_thread,access,0,NULL);CHECK(thread);CHECK(WaitForSingleObject(thread,5000)==WAIT_OBJECT_0);
    DWORD result=1;CHECK(GetExitCodeThread(thread,&result)&&result==0);CloseHandle(thread);
    // Every allocation frontier preserves the old projection and retained COM object.
    for(int i=0;i<3;i++) {
        CHECK(control(0,i)==0);CHECK(publish(token,2,records,5,names,33)==-4);CHECK(control(0,-1)==0);
        CHECK(IAccessible_get_accName(access,child(3),&name)==S_OK && wcscmp(name,L"Name")==0);SysFreeString(name);
    }
    int64_t bad[40];memcpy(bad,records,sizeof(bad));bad[6]=INT64_MAX;CHECK(publish(token,2,bad,5,names,33)==-1);
    uint8_t *large=calloc(1048577,1);CHECK(large);memcpy(large,names,33);
    memcpy(bad,records,sizeof(bad));bad[7]=1048577;CHECK(publish(token,2,bad,5,large,1048577)==-1);free(large);
    memcpy(bad,records,sizeof(bad));bad[1]=2;CHECK(publish(token,2,bad,5,names,33)==-1);
    CHECK(publish(token,2,records,5,(const uint8_t *)"\x80",1)==-1);
    CHECK(IAccessible_accDoDefaultAction(access,child(3))==S_OK); // queued identity remains document 1
    CHECK(publish(token,2,records,5,names,33)==0);
    CHECK(IAccessible_get_accName(access,child(3),&name)==CO_E_OBJNOTCONNECTED && !name);
    IAccessible_Release(access);CHECK(publish(token,1,records,5,names,33)==-2);
    CHECK(AccessibleObjectFromWindow(hwnd,OBJID_CLIENT,&IID_IAccessible,(void **)&access)==S_OK);
    CHECK(IAccessible_get_accChildCount(access,&count)==S_OK && count==4);
    // Compare the 200% font to independent GDI construction, not multiplication of glyph widths.
    LOGFONTW font;CHECK(GetObjectW(GetStockObject(DEFAULT_GUI_FONT),sizeof(font),&font));font.lfHeight*=2;font.lfWidth*=2;
    HFONT doubled=CreateFontIndirectW(&font);CHECK(doubled);HDC dc=CreateCompatibleDC(NULL);CHECK(dc);
    HGDIOBJ previous=SelectObject(dc,doubled);SIZE extent;CHECK(GetTextExtentPoint32W(dc,L"M a\x00e7\x00e3o",6,&extent));
    int64_t measured=measure((const uint8_t *)"M a\xc3\xa7\xc3\xa3o",8,2000);
    CHECK(measured==((int64_t)extent.cy<<32|extent.cx));CHECK(measure((const uint8_t *)"M",1,1500)==-1);
    SelectObject(dc,previous);DeleteDC(dc);DeleteObject(doubled);
    CHECK(close_window(token)==0);CHECK(IAccessible_get_accChildCount(access,&count)==CO_E_OBJNOTCONNECTED);
    IAccessible_Release(access);CHECK(control(9,0)==0);
    CHECK(open_window(2,96,64,(const uint8_t *)"small",5,&token)==0);
    CHECK(publish(token,1,records,5,names,33)==0);hwnd=(HWND)(uintptr_t)control(4,token);
    CHECK(AccessibleObjectFromWindow(hwnd,OBJID_CLIENT,&IID_IAccessible,(void **)&access)==S_OK);
    CHECK(IAccessible_accLocation(access,&x,&y,&width,&height,child(0))==S_OK && width==96 && height==64);
    CHECK(IAccessible_accLocation(access,&x,&y,&width,&height,child(2))==S_OK && width==72 && height==9);
    CHECK(IAccessible_accLocation(access,&x,&y,&width,&height,child(3))==S_FALSE);
    CHECK(IAccessible_get_accState(access,child(3),&value)==S_OK && (V_I4(&value)&STATE_SYSTEM_OFFSCREEN));
    CHECK(close_window(token)==0);IAccessible_Release(access);
    DWORD gdi=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    for(int i=3;i<=102;i++) {
        CHECK(open_window(i,96,64,(const uint8_t *)"cycle",5,&token)==0);
        CHECK(publish(token,1,records,5,names,33)==0);CHECK(close_window(token)==0);
    }
    CHECK(control(3,0)==0 && control(9,0)==0);CHECK(GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS)==gdi);
    FreeLibrary(dll);puts("PASS MSAA identities, failures, actions, geometry, GDI 200%, 100 cycles");return 0;
}

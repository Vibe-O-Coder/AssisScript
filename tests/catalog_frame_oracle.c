#define WIN32_LEAN_AND_MEAN
#define COBJMACROS
#include <windows.h>
#include <oleacc.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
#define LOAD(target,symbol) do {FARPROC p=GetProcAddress(dll,symbol);CHECK(p);memcpy(&(target),&p,sizeof(target));}while(0)
typedef int32_t (*Open)(int64_t,int32_t,int32_t,const uint8_t *,int64_t,int64_t *);
typedef int32_t (*Close)(int64_t);
typedef int64_t (*Control)(int64_t,int64_t);
typedef int32_t (*Poll)(int64_t,int32_t,int64_t *,int64_t);
typedef int32_t (*Commit)(int64_t,int64_t,uint32_t,const int64_t *,int64_t,const uint8_t *,int64_t,const int64_t *,int64_t,const uint8_t *,int64_t);
static VARIANT child(LONG n){VARIANT v;VariantInit(&v);V_VT(&v)=VT_I4;V_I4(&v)=n;return v;}
int main(int argc,char **argv){
    CHECK(argc==2);HMODULE dll=LoadLibraryA(argv[1]);CHECK(dll);
    Open open_window;Close close_window;Control control;Poll poll;Commit commit,legacy;
    LOAD(open_window,"assisp_open");LOAD(close_window,"assisp_close");LOAD(control,"assisp_test_control");
    LOAD(poll,"assisp_poll");LOAD(commit,"assisp_frame_catalog_commit");LOAD(legacy,"assisp_frame_commit");
    int64_t token=0;CHECK(open_window(51,320,240,(const uint8_t *)"Catalog oracle",14,&token)==0);
    HWND hwnd=(HWND)(uintptr_t)control(4,token);
    int64_t words[9*8]={1,0,0,0,320,240,0,3};
    const LONG roles[]={ROLE_SYSTEM_GROUPING,ROLE_SYSTEM_GROUPING,ROLE_SYSTEM_GROUPING,ROLE_SYSTEM_GROUPING,
        ROLE_SYSTEM_GROUPING,ROLE_SYSTEM_LINK,ROLE_SYSTEM_LIST,ROLE_SYSTEM_LISTITEM};
    for(int i=0;i<8;i++){
        int64_t *r=words+(i+1)*8;r[0]=12+i;r[2]=10;r[3]=10+i*20;r[4]=100;r[5]=20;r[6]=3;r[7]=4;
    }
    words[6*8+1]=2; /* link focus */
    const uint8_t names[]="DocName";
    CHECK(legacy(token,1,0xabcdefFF,NULL,0,NULL,0,words,9,names,7)==-1);
    CHECK(commit(token,1,0xabcdefFF,NULL,0,NULL,0,words,9,names,7)==0);
    IAccessible *a=NULL;CHECK(AccessibleObjectFromWindow(hwnd,OBJID_CLIENT,&IID_IAccessible,(void **)&a)==S_OK);
    LONG total=0;CHECK(IAccessible_get_accChildCount(a,&total)==S_OK && total==8);
    for(int i=0;i<8;i++){
        VARIANT v;CHECK(IAccessible_get_accRole(a,child(i+1),&v)==S_OK && V_I4(&v)==roles[i]);
        CHECK(IAccessible_get_accState(a,child(i+1),&v)==S_OK);
        CHECK(!!(V_I4(&v)&STATE_SYSTEM_FOCUSABLE)==(i==5));
        BSTR name=NULL;CHECK(IAccessible_get_accName(a,child(i+1),&name)==S_OK && !wcscmp(name,L"Name"));SysFreeString(name);
        if(i!=5)CHECK(IAccessible_accDoDefaultAction(a,child(i+1))==E_ACCESSDENIED);
    }
    BSTR description=NULL;CHECK(IAccessible_get_accDescription(a,child(5),&description)==S_OK && !wcscmp(description,L"navigation"));SysFreeString(description);
    BSTR action=NULL;CHECK(IAccessible_get_accDefaultAction(a,child(6),&action)==S_OK && !wcscmp(action,L"Open"));SysFreeString(action);
    CHECK(IAccessible_accDoDefaultAction(a,child(6))==S_OK);
    int found=0;for(int i=0;i<30;i++){int64_t event[8];int code=poll(token,0,event,8);CHECK(code>=0);
        if(!code && event[1]==11){CHECK(event[5]==1 && event[6]==6);found++;}}
    CHECK(found==1);
    /* Parent group encloses its link: semantic draw order decides the hit. */
    words[1*8+2]=0;words[1*8+3]=0;words[1*8+4]=320;words[1*8+5]=240;
    CHECK(commit(token,2,0xabcdefFF,NULL,0,NULL,0,words,9,names,7)==0);
    CHECK(FAILED(IAccessible_get_accChildCount(a,&total)));IAccessible_Release(a);a=NULL;
    CHECK(AccessibleObjectFromWindow(hwnd,OBJID_CLIENT,&IID_IAccessible,(void **)&a)==S_OK);
    POINT point={12,112};CHECK(ClientToScreen(hwnd,&point));VARIANT hit;
    CHECK(IAccessible_accHitTest(a,point.x,point.y,&hit)==S_OK && V_I4(&hit)==6);
    /* Every native allocation checkpoint, with old COM projection preserved. */
    DWORD baseline=GetGuiResources(GetCurrentProcess(),0);int success=0,failures=0;
    for(int limit=0;limit<80;limit++){
        CHECK(control(0,limit)==0);int code=commit(token,3,0x123456FF,NULL,0,NULL,0,words,9,names,7);CHECK(control(0,-1)==0);
        if(!code){success=1;break;}
        CHECK(code==-4);failures++;CHECK(IAccessible_get_accChildCount(a,&total)==S_OK && total==8);
        CHECK(GetGuiResources(GetCurrentProcess(),0)==baseline);
    }
    CHECK(success && failures>=5);CHECK(FAILED(IAccessible_get_accChildCount(a,&total)));IAccessible_Release(a);
    CHECK(close_window(token)==0);CHECK(close_window(token)==-2);FreeLibrary(dll);
    puts("PASS catalog roles actions hits revocation allocation rollback");return 0;
}

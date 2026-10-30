/* Test-only OS-boundary fault injection in this executable's VirtualAlloc IAT.
 * No remote process, executable-code patch, or production allocator hook.
 * Deny fresh 64 KiB slabs; managed free lists are drained by the test program. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>

typedef LPVOID (WINAPI *Allocate)(LPVOID,SIZE_T,DWORD,DWORD);
static Allocate original;
static DWORD owner;
static int hits;
static LPVOID WINAPI deny_map(LPVOID address,SIZE_T size,DWORD flags,DWORD protection){
    if(GetCurrentThreadId()==owner&&size==65536){hits++;SetLastError(ERROR_NOT_ENOUGH_MEMORY);return NULL;}
    return original(address,size,flags,protection);
}
__declspec(dllexport) int32_t fault_enable(void){
    BYTE *base=(BYTE*)GetModuleHandleW(NULL);
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)base;
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE||dos->e_lfanew<=0)return -1;
    IMAGE_NT_HEADERS64 *nt=(IMAGE_NT_HEADERS64*)(base+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE||nt->OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC)return -2;
    DWORD rva=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if(!rva)return -3;
    Allocate target=VirtualAlloc,hook=deny_map;uint64_t target_bits,hook_bits;
    _Static_assert(sizeof(target)==sizeof(target_bits),"Windows x64 required");
    memcpy(&target_bits,&target,sizeof(target));memcpy(&hook_bits,&hook,sizeof(hook));
    for(IMAGE_IMPORT_DESCRIPTOR *d=(IMAGE_IMPORT_DESCRIPTOR*)(base+rva);d->Name;d++){
        for(IMAGE_THUNK_DATA64 *t=(IMAGE_THUNK_DATA64*)(base+d->FirstThunk);t->u1.Function;t++){
            if(t->u1.Function!=target_bits)continue;
            DWORD prior,ignored;if(!VirtualProtect(&t->u1.Function,sizeof(t->u1.Function),PAGE_READWRITE,&prior))return -4;
            original=target;owner=GetCurrentThreadId();hits=0;t->u1.Function=hook_bits;
            if(!VirtualProtect(&t->u1.Function,sizeof(t->u1.Function),prior,&ignored))return -5;
            return 0;
        }
    }
    return -6;
}
__declspec(dllexport) int32_t fault_hits(void){return hits;}

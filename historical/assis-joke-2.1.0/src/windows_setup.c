/* Instalador nativo por usuário. Não usa PowerShell, setx ou privilégios administrativos. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <io.h>
#include <fcntl.h>

#define CAP 32768
static wchar_t prefix[CAP],root[CAP];
static const wchar_t *files[]={
    L"bin\\assis.exe",L"README.md",L"docs\\LINGUAGEM.md",L"docs\\GRAMATICA.ebnf",L"docs\\WINDOWS.md",
    L"exemplos\\01_ola.assis",L"exemplos\\02_objetos.assis",L"exemplos\\03_polimorfismo.assis",
    L"exemplos\\04_memoria.assis",L"exemplos\\05_bits.assis",L"exemplos\\06_fibonacci.assis",L"exemplos\\07_arena.assis"
};
static void die(const wchar_t *message){fwprintf(stderr,L"FODASE: %ls (Windows %lu).\n",message,(unsigned long)GetLastError());exit(1);}
static void join(wchar_t *out,const wchar_t *base,const wchar_t *part){
    if(wcslen(base)+wcslen(part)+2>=CAP)die(L"Caminho grande demais");wcscpy(out,base);wcscat(out,L"\\");wcscat(out,part);
}
static void directory(const wchar_t *path){int rc=SHCreateDirectoryExW(NULL,path,NULL);if(rc!=ERROR_SUCCESS&&rc!=ERROR_ALREADY_EXISTS&&rc!=ERROR_FILE_EXISTS){SetLastError((DWORD)rc);die(L"Não foi possível criar diretório");}}
static int is_file(const wchar_t *path){DWORD attr=GetFileAttributesW(path);return attr!=INVALID_FILE_ATTRIBUTES&&!(attr&FILE_ATTRIBUTE_DIRECTORY);}
static int path_equal(const wchar_t *token,size_t length,const wchar_t *path){
    wchar_t raw[CAP],expanded[CAP];if(length>=CAP)return 0;wmemcpy(raw,token,length);raw[length]=0;
    wchar_t *start=raw;while(*start==L' '||*start==L'"')start++;size_t n=wcslen(start);
    while(n&&(start[n-1]==L' '||start[n-1]==L'"'||start[n-1]==L'\\'||start[n-1]==L'/'))start[--n]=0;
    DWORD rc=ExpandEnvironmentStringsW(start,expanded,CAP);if(!rc||rc>CAP)return 0;return !_wcsicmp(expanded,path);
}
static void edit_path(int add){
    wchar_t bin[CAP];join(bin,prefix,L"bin");HKEY key;
    LONG rc=RegCreateKeyExW(HKEY_CURRENT_USER,L"Environment",0,NULL,0,KEY_QUERY_VALUE|KEY_SET_VALUE,NULL,&key,NULL);
    if(rc!=ERROR_SUCCESS){SetLastError((DWORD)rc);die(L"Não foi possível abrir o PATH do usuário");}
    DWORD type=REG_EXPAND_SZ,size=0;rc=RegQueryValueExW(key,L"Path",NULL,&type,NULL,&size);
    if(rc!=ERROR_SUCCESS&&rc!=ERROR_FILE_NOT_FOUND){RegCloseKey(key);SetLastError((DWORD)rc);die(L"Não foi possível ler o PATH");}
    if(rc==ERROR_FILE_NOT_FOUND){type=REG_EXPAND_SZ;size=0;}
    if(type!=REG_SZ&&type!=REG_EXPAND_SZ){RegCloseKey(key);die(L"O PATH do usuário tem um tipo inesperado");}
    size_t chars=(size_t)size/sizeof(wchar_t)+wcslen(bin)+8;
    if(chars>=CAP){RegCloseKey(key);die(L"O PATH do usuário é grande demais");}
    wchar_t *old=calloc(chars,sizeof(wchar_t)),*out=calloc(chars,sizeof(wchar_t));if(!old||!out)die(L"Memória insuficiente");
    if(size&&RegQueryValueExW(key,L"Path",NULL,&type,(BYTE*)old,&size)!=ERROR_SUCCESS)die(L"Não foi possível ler o PATH");
    int found=0,kept=0;size_t used=0;
    for(const wchar_t *p=old;;){
        const wchar_t *end=wcschr(p,L';');size_t len=end?(size_t)(end-p):wcslen(p);int match=path_equal(p,len,bin);
        if(match)found=1;
        if(add||!match){if(kept)out[used++]=L';';wmemcpy(out+used,p,len);used+=len;kept=1;}
        if(!end)break;p=end+1;
    }
    if(add&&!found){if(used&&out[used-1]!=L';')out[used++]=L';';wcscpy(out+used,bin);used+=wcslen(bin);}
    out[used]=0;
    if(!used&&!add)rc=RegDeleteValueW(key,L"Path");else rc=RegSetValueExW(key,L"Path",0,type,(const BYTE*)out,(DWORD)((used+1)*sizeof(wchar_t)));
    RegCloseKey(key);free(old);free(out);
    if(rc!=ERROR_SUCCESS&&rc!=ERROR_FILE_NOT_FOUND){SetLastError((DWORD)rc);die(L"Não foi possível atualizar o PATH do usuário");}
    DWORD_PTR ignored=0;SendMessageTimeoutW(HWND_BROADCAST,WM_SETTINGCHANGE,0,(LPARAM)L"Environment",SMTO_ABORTIFHUNG,3000,&ignored);
}
static void install(int change_path){
    wchar_t from[CAP],to[CAP],dir[CAP];
    if(!_wcsicmp(prefix,root))die(L"Escolha um destino diferente da pasta extraída, ou use bin\\assis.exe sem instalar");
    for(size_t i=0;i<sizeof(files)/sizeof(files[0]);i++){join(from,root,files[i]);if(!is_file(from))die(L"Pacote incompleto: extraia todos os arquivos antes de instalar");}
    directory(prefix);join(dir,prefix,L"bin");directory(dir);join(dir,prefix,L"docs");directory(dir);join(dir,prefix,L"exemplos");directory(dir);
    for(size_t i=0;i<sizeof(files)/sizeof(files[0]);i++){join(from,root,files[i]);join(to,prefix,files[i]);if(!CopyFileW(from,to,FALSE))die(L"Não foi possível copiar um arquivo da instalação");}
    join(to,prefix,L"INSTALADO");FILE *marker=_wfopen(to,L"wb");if(!marker)die(L"Não foi possível gravar marcador de instalação");
    int ok=fputs("AssisScript 2.1.0\n",marker)>=0;if(fclose(marker))ok=0;if(!ok)die(L"Erro ao gravar marcador de instalação");
    if(change_path)edit_path(1);
    wprintf(L"ASSIS: instalado em %ls\\bin\\assis.exe\n",prefix);
    if(change_path)wprintf(L"Feche e reabra o terminal. Depois execute: assis version\n");
    else wprintf(L"O PATH foi preservado. Use o caminho completo ou adicione a pasta bin ao PATH.\n");
}
static void uninstall(int change_path){
    wchar_t path[CAP];join(path,prefix,L"INSTALADO");FILE *marker=_wfopen(path,L"rb");char text[64]={0};
    if(!marker)die(L"Instalação AssisScript não encontrada nesse destino");size_t got=fread(text,1,sizeof(text)-1,marker);fclose(marker);
    if(got<11||strncmp(text,"AssisScript",11))die(L"Marcador de instalação inválido");
    /* O executável é removido primeiro para detectar bloqueio antes de alterar o PATH. */
    for(size_t i=0;i<sizeof(files)/sizeof(files[0]);i++){
        join(path,prefix,files[i]);if(!DeleteFileW(path)&&GetLastError()!=ERROR_FILE_NOT_FOUND&&GetLastError()!=ERROR_PATH_NOT_FOUND)die(L"Não foi possível remover arquivo; encerre processos AssisScript abertos");
    }
    if(change_path)edit_path(0);join(path,prefix,L"INSTALADO");DeleteFileW(path);
    join(path,prefix,L"bin");RemoveDirectoryW(path);join(path,prefix,L"docs");RemoveDirectoryW(path);join(path,prefix,L"exemplos");RemoveDirectoryW(path);RemoveDirectoryW(prefix);
    wprintf(L"ASSIS: desinstalado. Projetos e arquivos extras foram preservados.\n");
}
int wmain(int argc,wchar_t **argv){
    _setmode(_fileno(stdout),_O_U8TEXT);_setmode(_fileno(stderr),_O_U8TEXT);
    if(argc<2||(!_wcsicmp(argv[1],L"--help"))){wprintf(L"Uso: assis-setup.exe install|uninstall [--prefix PASTA] [--no-path]\n");return 0;}
    int remove=!_wcsicmp(argv[1],L"uninstall"),add=!_wcsicmp(argv[1],L"install"),change_path=1;
    if(!remove&&!add)die(L"Comando inválido: use install ou uninstall");
    const wchar_t *chosen=NULL;
    for(int i=2;i<argc;i++){
        if(!_wcsicmp(argv[i],L"--prefix")&&i+1<argc)chosen=argv[++i];
        else if(!_wcsicmp(argv[i],L"--no-path"))change_path=0;else die(L"Opção desconhecida");
    }
    wchar_t default_path[CAP];
    if(!chosen){DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",default_path,CAP);if(!n||n+13>=CAP)die(L"LOCALAPPDATA não definido ou grande demais");wcscat(default_path,L"\\AssisScript");chosen=default_path;}
    DWORD n=GetFullPathNameW(chosen,CAP,prefix,NULL);if(!n||n>=CAP)die(L"Destino inválido");
    size_t len=wcslen(prefix);while(len>3&&(prefix[len-1]==L'\\'||prefix[len-1]==L'/'))prefix[--len]=0;
    n=GetModuleFileNameW(NULL,root,CAP);if(!n||n>=CAP)die(L"Não foi possível localizar o pacote");
    wchar_t *slash=wcsrchr(root,L'\\');if(!slash)die(L"Caminho do pacote inválido");*slash=0;
    slash=wcsrchr(root,L'\\');if(!slash)die(L"Caminho do pacote inválido");*slash=0;
    if(add)install(change_path);else uninstall(change_path);return 0;
}

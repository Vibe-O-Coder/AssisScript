/* Source modules are checked together and linked into one native executable. */
static size_t source_bytes;
static char *last_source_digest;
static char *source_sha256(const unsigned char *input,size_t length);
static char *path_join(const char *dir,const char *name){
    size_t n=strlen(dir)+strlen(name)+2;char *p=mem(n);snprintf(p,n,"%s/%s",dir,name);return p;
}
static char *path_directory(const char *path){
    char *p=copy(path,strlen(path)),*last=NULL;
    for(char *c=p;*c;c++)if(*c=='/'||*c=='\\')last=c;
    if(last)last[1]=0;else{free(p);p=copy(".",1);}return p;
}
static char *absolute_path(const char *path){
#ifdef _WIN32
    wchar_t *w=wide_path(path);DWORD n=GetFullPathNameW(w,0,NULL,NULL);if(!n)fatal("caminho inválido: %s",path);
    wchar_t *full=mem(((size_t)n+1)*sizeof(wchar_t));
    if(!GetFullPathNameW(w,n+1,full,NULL))fatal("caminho inválido: %s",path);
    char *out=utf8_path(full);free(full);free(w);return out;
#else
    char *full=realpath(path,NULL);if(full)return full;
    if(path[0]=='/')return copy(path,strlen(path));
    char cwd[PATH_MAX];if(!getcwd(cwd,sizeof(cwd)))fatal("diretório atual indisponível");return path_join(cwd,path);
#endif
}
static char *executable_directory(void){
#ifdef _WIN32
    wchar_t path[32768];DWORD n=GetModuleFileNameW(NULL,path,32768);
    if(!n||n>=32768)fatal("não foi possível localizar o compilador");
    char *utf8=utf8_path(path),*dir=path_directory(utf8);free(utf8);return dir;
#else
    char path[PATH_MAX];ssize_t n=readlink("/proc/self/exe",path,sizeof(path)-1);
    if(n<0||(size_t)n>=sizeof(path)-1)fatal("não foi possível localizar o compilador");path[n]=0;return path_directory(path);
#endif
}
static const char *overlay_path(const char *path){
    if(!source_overlays.n)return path;char *absolute=absolute_path(path);const char *result=path;
    for(int i=0;i<source_overlays.n;i++){
        SourceOverlay *overlay=source_overlays.v[i];
#ifdef _WIN32
        bool match=!_stricmp(overlay->path,absolute);
#else
        bool match=same(overlay->path,absolute);
#endif
        if(match){result=overlay->snapshot;break;}
    }
    free(absolute);return result;
}
static bool file_exists(const char *path){FILE *f=fopen(overlay_path(path),"rb");if(!f)return false;fclose(f);return true;}
static char *module_candidate(const char *dir,const char *name){
    bool absolute=name[0]=='/'||name[0]=='\\'||(ascii_alpha((unsigned char)name[0])&&name[1]==':');
    char *p=absolute?copy(name,strlen(name)):path_join(dir,name);if(file_exists(p))return p;
    size_t length=strlen(name);if((length>=7&&same(name+length-7,".pillow"))||(length>=6&&same(name+length-6,".assis"))){free(p);return NULL;}
    size_t n=strlen(p);char *ext=mem(n+7);snprintf(ext,n+7,"%s.assis",p);free(p);
    if(file_exists(ext))return ext;free(ext);return NULL;
}
static char *resolve_package(Token *t,const char *name);
static void package_import_boundary(Token *t,const char *path);
static void package_alias_boundary(Token *t,const char *original,const char *alias);
static char *resolve_module(Token *where){
    if(!where->len||strlen(where->str)!=where->len)error(where,"caminho de importação vazio ou contém byte nulo");
    const char *name=where->str;char *package=resolve_package(where,name);if(package)return package;
    char *dir=path_directory(where->file->path),*found=module_candidate(dir,name);free(dir);
    if(found){package_import_boundary(where,found);return found;}
    for(int i=0;i<include_dirs.n;i++){found=module_candidate(include_dirs.v[i],name);if(found){package_import_boundary(where,found);return found;}}
    if(!strncmp(name,"std/",4)||!strncmp(name,"std\\",4)){
        const char *roots[]={"../stdlib","../share/assisscript/stdlib"};
        for(size_t i=0;i<sizeof(roots)/sizeof(roots[0]);i++){
            dir=path_join(compiler_directory,roots[i]);found=module_candidate(dir,name+4);free(dir);if(found){package_import_boundary(where,found);return found;}
        }
    }
    if(where->kind==T_BODY){
        char *dotted=copy(name,strlen(name));for(char *p=dotted;p<dotted+strlen(name)-7;p++)if(*p=='.')*p='/';
        dir=path_directory(where->file->path);found=module_candidate(dir,dotted);free(dir);
        for(int i=0;!found&&i<include_dirs.n;i++)found=module_candidate(include_dirs.v[i],dotted);free(dotted);if(found){package_import_boundary(where,found);return found;}
    }
    error(where,"módulo não encontrado: %s (use caminho relativo, -I ou ASSIS_PATH)",name);
}
static char *read_module_text(const char *path,bool from_stdin){
    FILE *f=from_stdin?stdin:fopen(overlay_path(path),"rb");if(!f)fatal("não foi possível ler %s: %s",path,strerror(errno));
    size_t n=0,cap=4096;char *text=mem(cap+1);
    for(;;){
        size_t got=fread(text+n,1,cap-n,f);n+=got;
        if(n>MAX_SOURCE){if(!from_stdin)fclose(f);fatal("arquivo maior que o limite de 16 MiB");}
        if(n<cap){if(ferror(f))fatal("erro ao ler %s",path);break;}
        cap=cap>MAX_SOURCE/2?MAX_SOURCE+1:cap*2;text=realloc(text,cap+1);if(!text)fatal("memória insuficiente");
    }
    if(!from_stdin)fclose(f);text[n]=0;source_bytes+=n;
    if(source_bytes>MAX_SOURCE)fatal("módulos excedem o limite total de 16 MiB");
    if(memchr(text,0,n))fatal("o arquivo fonte contém um byte nulo; use \\0 dentro do texto");
    last_source_digest=source_sha256((unsigned char*)text,n);
    if(n>=3&&(unsigned char)text[0]==0xef&&(unsigned char)text[1]==0xbb&&(unsigned char)text[2]==0xbf)memmove(text,text+3,n-2);
    return text;
}
static void load_module(const char *path,Token *where,bool from_stdin,Vec *out,int depth){
    if(depth>128)error(where,"importação aninhada demais");
    char *absolute=absolute_path(path);
    for(int i=0;i<source_files.n;i++){
        SourceFile *old=source_files.v[i];
        if(same(old->path,absolute)||same_file(old->path,absolute)){
            if(old->state==1)error(where,"ciclo de importação detectado: %s",old->path);
            package_alias_boundary(where,old->path,absolute);
            if(!same(old->path,absolute)){
                bool seen=false;for(int j=0;j<source_aliases.n;j++)if(same(((SourceAlias*)source_aliases.v[j])->path,absolute))seen=true;
                if(!seen){
                    if(source_files.n+source_aliases.n>=1024)error(where,"limite de 1024 módulos/aliases excedido");
                    SourceAlias *alias=mem(sizeof(*alias));alias->path=absolute;alias->digest=old->digest;push(&source_aliases,alias);return;
                }
            }
            free(absolute);return;
        }
    }
    if(source_files.n+source_aliases.n>=1024)error(where,"limite de 1024 módulos excedido");
    SourceFile *file=mem(sizeof(*file));file->path=absolute;file->text=read_module_text(absolute,from_stdin);file->digest=last_source_digest;file->state=1;push(&source_files,file);
    Vec previous=tokens;SourceFile *previous_file=current_source;
    current_source=file;filename=file->path;source=file->text;tokens=(Vec){0};lex();Vec raw=tokens;tokens=previous;
    int braces=0;size_t pathlen=strlen(path);bool package=pathlen>=7&&same(path+pathlen-7,".pillow");
    for(int i=0;i<raw.n-1;i++){
        Token *t=raw.v[i];
        if((t->kind==T_YURI||t->kind==T_BODY)&&braces==0){
            char *resolved=resolve_module(t);load_module(resolved,t,false,out,depth+1);free(resolved);
            if(((Token*)raw.v[i+1])->kind==';')i++;
            Token *next=raw.v[i+1];if(next->kind!=T_EOF&&next->line==t->line)error(next,"diretiva deve ocupar uma linha própria");
        }else if(t->kind==T_IMPORT&&braces==0&&!package){
            Token *name=raw.v[++i];if(name->kind!=T_STR)error(name,"importa exige um caminho entre aspas");
            Token *end=raw.v[++i];if(end->kind!=';')error(end,"esperado ; após importa");
            char *resolved=resolve_module(name);load_module(resolved,name,false,out,depth+1);free(resolved);
        }else{if(package)error(t,"pacote .pillow aceita somente #yuri e #body");push(out,t);if(t->kind=='{')braces++;else if(t->kind=='}')braces--;}
    }
    Token *end=raw.v[raw.n-1];if(depth)end->kind=T_FILE_END;push(out,end);free(raw.v);file->state=2;
    current_source=previous_file?previous_file:file;filename=current_source->path;source=current_source->text;
}
static void module_search_paths(void){
    compiler_directory=executable_directory();
#ifdef _WIN32
    DWORD n=GetEnvironmentVariableW(L"ASSIS_PATH",NULL,0);if(!n)return;
    wchar_t *wide=mem((size_t)n*sizeof(wchar_t));if(!GetEnvironmentVariableW(L"ASSIS_PATH",wide,n))fatal("não foi possível ler ASSIS_PATH");
    const char *value=utf8_path(wide);free(wide);
    const char separator=';';
#else
    const char *value=getenv("ASSIS_PATH");if(!value)return;
    const char separator=':';
#endif
    const char *p=value;for(const char *c=p;;c++)if(*c==separator||!*c){if(c>p)push(&include_dirs,copy(p,(size_t)(c-p)));if(!*c)break;p=c+1;}
}
#include "packages.h"

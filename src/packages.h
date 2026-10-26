/* Pinned, vendored packages only. No registry, downloads or post-install code. */
#include "sha256.h"
typedef struct Package Package;
typedef struct {char *alias,*version,*path;Package *target;} PackageDependency;
struct Package {char *root,*name,*version,*manifest,*digest;Vec dependencies;int state;};
static Vec packages;
static Package *project_package;
static char *physical_path(const char *path){
#ifdef _WIN32
    wchar_t *wide=wide_path(path);HANDLE h=CreateFileW(wide,0,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS,NULL);free(wide);
    if(h==INVALID_HANDLE_VALUE)fatal("caminho de pacote inexistente: %s",path);
    DWORD n=GetFinalPathNameByHandleW(h,NULL,0,FILE_NAME_NORMALIZED);wchar_t *out=mem(((size_t)n+1)*sizeof(wchar_t));
    if(!n||!GetFinalPathNameByHandleW(h,out,n+1,FILE_NAME_NORMALIZED))fatal("não foi possível resolver pacote: %s",path);CloseHandle(h);
    char *result=utf8_path(!wcsncmp(out,L"\\\\?\\",4)?out+4:out);free(out);return result;
#else
    char *out=realpath(path,NULL);if(!out)fatal("caminho de pacote inexistente: %s",path);return out;
#endif
}
static bool path_inside(const char *root,const char *path){
    size_t n=strlen(root);if(strlen(path)<n)return false;
    for(size_t i=0;i<n;i++){
        unsigned char a=(unsigned char)root[i],b=(unsigned char)path[i];if(a=='\\')a='/';if(b=='\\')b='/';
#ifdef _WIN32
        a=(unsigned char)tolower(a);b=(unsigned char)tolower(b);
#endif
        if(a!=b)return false;
    }
    return !path[n]||root[n-1]=='/'||root[n-1]=='\\'||path[n]=='/'||path[n]=='\\';
}
static char *package_read(const char *path){
    FILE *f=fopen(path,"rb");if(!f)fatal("não foi possível ler pacote/lockfile: %s",path);
    char *text=mem(MAX_SOURCE+1);size_t n=fread(text,1,MAX_SOURCE+1,f);bool ok=!ferror(f);fclose(f);
    if(!ok||n>MAX_SOURCE||memchr(text,0,n))fatal("arquivo de pacote inválido ou maior que 16 MiB: %s",path);text[n]=0;return text;
}
static bool package_identifier(const char *s){if(!ascii_alpha((unsigned char)*s)&&*s!='_')return false;for(;*s;s++)if(!ascii_alpha((unsigned char)*s)&&!ascii_digit((unsigned char)*s)&&*s!='_'&&*s!='-')return false;return true;}
static bool package_version(const char *s){
    for(int i=0;i<3;i++){const char *start=s;while(ascii_digit((unsigned char)*s))s++;if(s==start||s-start>9||(s-start>1&&*start=='0'))return false;if(i<2){if(*s++!='.')return false;}else if(*s)return false;}return true;
}
static Vec package_words(char *line){
    Vec out={0};char *p=line;
    while(*p){while(*p==' '||*p=='\t'||*p=='\r')p++;if(!*p||*p=='#')break;
        bool quote=*p=='"';if(quote)p++;char *start=p;while(*p&&(quote?*p!='"':*p!=' '&&*p!='\t'&&*p!='\r'))p++;
        if(quote&&*p!='"')fatal("aspas sem fechamento em assis.pkg");push(&out,copy(start,(size_t)(p-start)));if(*p)p++;
        if(out.n>4)fatal("registro excessivo em assis.pkg");
    }return out;
}
static Package *load_package(const char *root,int depth){
    if(depth>64||packages.n>=128)fatal("limite de expansão de pacotes excedido");char *physical=physical_path(root);
    for(int i=0;i<packages.n;i++){Package *old=packages.v[i];if(path_inside(old->root,physical)&&path_inside(physical,old->root)){free(physical);if(old->state==1)fatal("ciclo de dependências de pacote");return old;}}
    if(project_package&&!path_inside(project_package->root,physical))fatal("dependência deve permanecer dentro do projeto: %s",root);
    Package *p=mem(sizeof(*p));p->root=physical;p->state=1;push(&packages,p);if(!project_package)project_package=p;
    p->manifest=path_join(physical,"assis.pkg");char *text=package_read(p->manifest);p->digest=source_sha256((unsigned char*)text,strlen(text));
    char *line=text;while(*line){char *end=strchr(line,'\n');if(end)*end=0;Vec words=package_words(line);
        if(words.n){
            if(same(words.v[0],"package")){
                if(words.n!=3||p->name||!package_identifier(words.v[1])||!package_version(words.v[2]))fatal("package exige nome e versão exata X.Y.Z em %s",p->manifest);
                p->name=words.v[1];p->version=words.v[2];
            }else if(same(words.v[0],"dep")){
                if(words.n!=4||!package_identifier(words.v[1])||!package_version(words.v[2]))fatal("dep exige alias, versão exata X.Y.Z e pasta em %s",p->manifest);
                for(int i=0;i<p->dependencies.n;i++)if(same(((PackageDependency*)p->dependencies.v[i])->alias,words.v[1]))fatal("alias de dependência duplicado");
                PackageDependency *d=mem(sizeof(*d));d->alias=words.v[1];d->version=words.v[2];d->path=words.v[3];
                if(d->path[0]=='/'||d->path[0]=='\\'||strchr(d->path,':'))fatal("dependência exige caminho relativo vendorizado");push(&p->dependencies,d);
            }else fatal("registro desconhecido em assis.pkg: %s",(char*)words.v[0]);
        }
        free(words.v);if(!end)break;line=end+1;
    }
    free(text);if(!p->name)fatal("assis.pkg não declara package: %s",p->manifest);
    for(int i=0;i<p->dependencies.n;i++){PackageDependency *d=p->dependencies.v[i];char *path=path_join(p->root,d->path);d->target=load_package(path,depth+1);free(path);if(!same(d->version,d->target->version))fatal("versão de dependência incompatível: %s requer %s, encontrou %s",d->alias,d->version,d->target->version);}
    p->state=2;return p;
}
static Package *package_owner(const char *path){
    Package *found=NULL;for(int i=0;i<packages.n;i++){Package *p=packages.v[i];if(path_inside(p->root,path)&&(!found||strlen(p->root)>strlen(found->root)))found=p;}return found;
}
static bool package_standard(const char *path){
    const char *roots[]={"../stdlib","../share/assisscript/stdlib"};
    for(int i=0;i<2;i++){char *joined=path_join(compiler_directory,roots[i]),*root=absolute_path(joined);free(joined);bool found=path_inside(root,path);free(root);if(found)return true;}return false;
}
static void package_import_boundary(Token *t,const char *path){
    if(!project_package)return;bool standard=package_standard(t->file->path);Package *owner=package_owner(t->file->path);if(!standard&&(!owner||owner==project_package))return;
    char *physical=physical_path(path);bool allowed=package_standard(physical)||(!standard&&path_inside(owner->root,physical));free(physical);
    if(!allowed)error(t,"importação escapa do pacote; declare dependência e use pkg/alias/arquivo");
}
static void package_alias_boundary(Token *t,const char *original,const char *alias){
    if(project_package&&(package_owner(original)!=package_owner(alias)||package_standard(original)!=package_standard(alias)))error(t,"arquivo compartilhado entre pacotes diferentes por hardlink/alias; use dependência explícita");
}
static void initialize_packages(const char *input){char *dir=path_directory(input),*manifest=path_join(dir,"assis.pkg");if(file_exists(manifest))load_package(dir,0);free(manifest);free(dir);}
static char *resolve_package(Token *t,const char *name){
    if(strncmp(name,"pkg/",4))return NULL;
    if(project_package&&package_standard(t->file->path))error(t,"stdlib não pode importar dependência externa do projeto");
    Package *owner=package_owner(t->file->path);if(!owner)error(t,"pkg/ exige assis.pkg e dependência declarada");
    const char *slash=strchr(name+4,'/');if(!slash||slash==name+4)error(t,"importação de pacote exige pkg/alias/arquivo.assis");
    char *alias=copy(name+4,(size_t)(slash-name-4));Package *dependency=NULL;
    for(int i=0;i<owner->dependencies.n;i++){PackageDependency *d=owner->dependencies.v[i];if(same(d->alias,alias))dependency=d->target;}
    free(alias);if(!dependency)error(t,"alias de pacote não declarado: %s",name);
    char *candidate=module_candidate(dependency->root,slash+1);if(!candidate)error(t,"módulo do pacote não encontrado: %s",name);
    char *physical=physical_path(candidate);free(candidate);if(!path_inside(dependency->root,physical))error(t,"importação escapa da pasta do pacote");return physical;
}
static char *package_relative(const char *path){
    size_t n=strlen(project_package->root);while(path[n]=='/'||path[n]=='\\')n++;char *out=copy(path+n,strlen(path+n));
    for(char *p=out;*p;p++){if(*p=='\\')*p='/';if(*p=='\t'||*p=='\n'||*p=='\r')fatal("caminho de pacote contém separador de registro");}return out;
}
static void package_lock_row(Vec *rows,const char *kind,const char *path,const char *digest){char *relative=package_relative(path);size_t n=strlen(kind)+strlen(relative)+strlen(digest)+4;char *row=mem(n);snprintf(row,n,"%s\t%s\t%s\n",kind,relative,digest);push(rows,row);free(relative);}
static int package_row_compare(const void *a,const void *b){return strcmp(*(char*const*)a,*(char*const*)b);}
static void package_source_row(Vec *rows,const char *path,const char *digest,bool internal){
    Package *owner=package_owner(path);
    if(!internal&&package_standard(path)){
        const char *name=path;for(const char *c=path;*c;c++)if(*c=='/'||*c=='\\')name=c+1;
        size_t n=strlen(name)+strlen(digest)+16;char *row=mem(n);snprintf(row,n,"stdlib\t%s\t%s\n",name,digest);push(rows,row);
    }
    else if(owner&&owner!=project_package)package_lock_row(rows,"source",path,digest);
    else if(!owner&&!internal)fatal("projeto com lockfile exige módulos vendorizados ou std: %s",path);
}
static void package_lock(bool write){
    if(!project_package){if(write)fatal("lock exige assis.pkg ao lado da entrada");return;}
    Vec rows={0};for(int i=0;i<packages.n;i++){Package *p=packages.v[i];package_lock_row(&rows,"manifest",p->manifest,p->digest);}
    for(int i=0;i<source_files.n;i++){SourceFile *s=source_files.v[i];package_source_row(&rows,s->path,s->digest,s->internal);}
    for(int i=0;i<source_aliases.n;i++){SourceAlias *s=source_aliases.v[i];package_source_row(&rows,s->path,s->digest,false);}
    qsort(rows.v,(size_t)rows.n,sizeof(void*),package_row_compare);size_t size=128;for(int i=0;i<rows.n;i++)size+=strlen(rows.v[i]);char *contents=mem(size);snprintf(contents,size,"AssisScript-lock 1\ncompiler %s\n",VERSION);for(int i=0;i<rows.n;i++)strcat(contents,rows.v[i]);
    char *path=path_join(project_package->root,"assis.lock");
    if(!write){if(!file_exists(path))fatal("lockfile ausente; execute assis lock após revisar dependências");char *old=package_read(path);if(!same(old,contents))fatal("lockfile divergente; revise dependências e execute assis lock");free(old);}
    else{
        protect_output(path);char *temporary=mem(strlen(path)+64);FILE *f=NULL;
        for(unsigned i=0;i<100&&!f;i++){snprintf(temporary,strlen(path)+64,"%s.tmp.%lu.%u",path,(unsigned long)time(NULL),i);f=fopen(temporary,"wbx");}
        if(!f)fatal("não foi possível criar lockfile temporário");bool ok=fputs(contents,f)>=0;if(fclose(f))ok=false;
#ifdef _WIN32
        if(ok){wchar_t *a=wide_path(temporary),*b=wide_path(path);ok=MoveFileExW(a,b,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;free(a);free(b);}
#else
        if(ok)ok=rename(temporary,path)==0;
#endif
        if(!ok){unlink(temporary);fatal("falha ao gravar lockfile");}free(temporary);printf("ASSIS: lockfile offline atualizado em %s\n",path);
    }
    free(contents);free(path);
}

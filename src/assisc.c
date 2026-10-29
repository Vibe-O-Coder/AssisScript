/* AssisScript 3.3 alpha. Compilador nativo C11 -> ELF64 / PE32+ x86_64.
 * O binário distribuído não invoca Python, um compilador C ou um assembler.
 */
#ifdef __APPLE__
/* Darwin hides mkdtemp behind its full API level when POSIX is requested. */
#define _DARWIN_C_SOURCE 1
#endif
#define _POSIX_C_SOURCE 200809L
#define _XOPEN_SOURCE 700
#if (!defined(__linux__) && !defined(_WIN32) && !defined(__APPLE__)) || (!defined(__x86_64__) && !((defined(__aarch64__) || defined(__arm64__)) && !defined(_WIN32)))
#error "Hosts suportados: Linux/macOS x86_64 ou ARM64, Windows x86_64. Destinos: x86_64 e ARM64 Linux/macOS."
#endif
#if defined(__aarch64__) || defined(__arm64__)
#define HOST_ARCH "ARM64"
#define HOST_RUN_X64 0
#else
#define HOST_ARCH "x86_64"
#define HOST_RUN_X64 1
#endif
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <math.h>
#include "elf_format.h"
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>
#include <direct.h>
#include <io.h>
#include <fcntl.h>
#define HOST_NAME "Windows x64"
static bool target_windows=true;
#else
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#define HOST_NAME "Linux " HOST_ARCH
static bool target_windows=false;
#endif
#ifdef __APPLE__
#include <mach-o/dyld.h>
#undef HOST_NAME
#define HOST_NAME "macOS " HOST_ARCH
static bool target_macos=true;
#else
static bool target_macos=false;
#endif
static bool target_arm64=!HOST_RUN_X64;

#include "version.h"
#define VERSION ASSIS_VERSION
#define ENTRY "main"
#define CTOR "init"
#define MAX_SOURCE (16 * 1024 * 1024)
#define MAX_NEST 512

typedef struct { void **v; int n, cap; } Vec;
static const char *filename;
typedef struct { char *path,*text,*space,*digest; int state; bool internal; } SourceFile;
static Vec source_files,include_dirs;
typedef struct {char *path,*digest;} SourceAlias;
static Vec source_aliases;
typedef struct { char *path,*snapshot; } SourceOverlay;
static Vec source_overlays;
static SourceFile *current_source;
static bool json_diagnostics,library_check,stdin_source;
static bool optimize=true,debug_memory,safe_entry=true,debug_symbols,bundle_app;
static char *compiler_directory;
static void json_string(FILE *out,const char *s){
    fputc('"',out);for(const unsigned char *p=(const unsigned char*)s;*p;p++){
        if(*p=='"'||*p=='\\'){fputc('\\',out);fputc(*p,out);}
        else if(*p<32)fprintf(out,"\\u%04x",*p);else fputc(*p,out);
    }fputc('"',out);
}
static void fatal(const char *fmt, ...) {
    char message[4096];va_list ap;va_start(ap,fmt);vsnprintf(message,sizeof(message),fmt,ap);va_end(ap);
    if(json_diagnostics){fputs("{\"code\":\"A002\",\"message\":",stderr);json_string(stderr,message);fputs("}\n",stderr);}
    else fprintf(stderr,"assis: %s\n",message);exit(2);
}
static void *mem(size_t n) { void *p=calloc(1,n?n:1); if(!p) fatal("memória insuficiente"); return p; }
static char *copy(const char *s, size_t n) { char *p=mem(n+1); memcpy(p,s,n); return p; }
static void push(Vec *v, void *item) {
    if(v->n==v->cap) { v->cap=v->cap?v->cap*2:16; v->v=realloc(v->v,(size_t)v->cap*sizeof(void*)); if(!v->v)fatal("memória insuficiente"); }
    v->v[v->n++]=item;
}
static bool same(const char *a,const char *b) { return a&&b&&!strcmp(a,b); }

#ifdef _WIN32
static wchar_t *wide_path(const char *s){
    int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,NULL,0);
    if(!n)fatal("caminho não é UTF-8 válido");wchar_t *out=mem((size_t)n*sizeof(wchar_t));
    if(!MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,out,n))fatal("erro ao converter caminho");return out;
}
static char *utf8_path(const wchar_t *s){
    int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,s,-1,NULL,0,NULL,NULL);
    if(!n)fatal("erro ao converter caminho Unicode");char *out=mem((size_t)n);
    if(!WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,s,-1,out,n,NULL,NULL))fatal("erro ao converter caminho Unicode");return out;
}
static FILE *utf8_fopen(const char *path,const char *mode){wchar_t *p=wide_path(path),*m=wide_path(mode);FILE *f=_wfopen(p,m);free(p);free(m);return f;}
static int utf8_mkdir(const char *path,int mode){(void)mode;wchar_t *p=wide_path(path);int rc=_wmkdir(p);free(p);return rc;}
static int utf8_unlink(const char *path){wchar_t *p=wide_path(path);int rc=_wunlink(p);free(p);return rc;}
static int utf8_chmod(const char *path,int mode){(void)mode;wchar_t *p=wide_path(path);int rc=_wchmod(p,_S_IREAD|_S_IWRITE);free(p);return rc;}
#define fopen utf8_fopen
#define mkdir utf8_mkdir
#define unlink utf8_unlink
#define chmod utf8_chmod
#endif
static bool same_file(const char *a,const char *b){
#ifdef _WIN32
    wchar_t *wa=wide_path(a),*wb=wide_path(b);
    HANDLE ha=CreateFileW(wa,0,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_EXISTING,0,NULL);
    HANDLE hb=CreateFileW(wb,0,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_EXISTING,0,NULL);free(wa);free(wb);
    BY_HANDLE_FILE_INFORMATION ia,ib;bool match=false;
    if(ha!=INVALID_HANDLE_VALUE&&hb!=INVALID_HANDLE_VALUE&&GetFileInformationByHandle(ha,&ia)&&GetFileInformationByHandle(hb,&ib))
        match=ia.dwVolumeSerialNumber==ib.dwVolumeSerialNumber&&ia.nFileIndexHigh==ib.nFileIndexHigh&&ia.nFileIndexLow==ib.nFileIndexLow;
    if(ha!=INVALID_HANDLE_VALUE)CloseHandle(ha);if(hb!=INVALID_HANDLE_VALUE)CloseHandle(hb);return match;
#else
    struct stat ia,ib;return !stat(a,&ia)&&!stat(b,&ib)&&ia.st_dev==ib.st_dev&&ia.st_ino==ib.st_ino;
#endif
}
static void protect_output(const char *path){
    for(int i=0;i<source_files.n;i++)if(same_file(((SourceFile*)source_files.v[i])->path,path))fatal("o destino não pode sobrescrever o código AssisScript");
#ifdef _WIN32
    wchar_t module[32768];DWORD size=GetModuleFileNameW(NULL,module,32768);
    if(size&&size<32768){char *self=utf8_path(module);bool match=same_file(self,path);free(self);if(match)fatal("o destino não pode sobrescrever o próprio compilador");}
#else
    if(same_file("/proc/self/exe",path))fatal("o destino não pode sobrescrever o próprio compilador");
#endif
}

#include "lexer.h"

#include "modules.h"

#include "frontend.h"

#include "runtime_blob.h"
#include "runtime_win_blob.h"
#include "runtime_macos_blob.h"
typedef struct { unsigned char *v;size_t n,cap; } Buffer;
static Buffer code,data;
static size_t native_import_rva;
typedef struct {char *library,*symbol;int label;size_t slot;} NativeImport;
static Vec native_imports;
static int callback_state_label=-1;
typedef struct {size_t offset;Token *token;} DebugSite;
static Vec debug_sites;
static void bytes(Buffer *b,const void *p,size_t n){
    if(n>256*1024*1024||b->n>256*1024*1024-n)fatal("programa gerado excede o limite de 256 MiB");
    if(b->n+n>b->cap){size_t cap=b->cap?b->cap:1024;while(cap<b->n+n)cap*=2;b->v=realloc(b->v,cap);if(!b->v)fatal("memória insuficiente");b->cap=cap;}
    memcpy(b->v+b->n,p,n);b->n+=n;
}
static void u8(Buffer *b,unsigned v){unsigned char c=(unsigned char)v;bytes(b,&c,1);}
static void u32(Buffer *b,uint32_t v){for(int i=0;i<4;i++)u8(b,(unsigned)(v>>(i*8)));}
static void u64(Buffer *b,uint64_t v){for(int i=0;i<8;i++)u8(b,(unsigned)(v>>(i*8)));}
static void emit(const unsigned char *p,size_t n){bytes(&code,p,n);}
#define INS(...) do{const unsigned char b[]={__VA_ARGS__};emit(b,sizeof(b));}while(0)
typedef struct {int section;size_t position;bool defined;} Label;
typedef struct {Buffer *buffer;size_t position;int label;bool relative;} Fix;
typedef struct {const char *str;size_t len;int label;} String;
static Vec labels,fixes,strings;
static int new_label(void){Label *l=mem(sizeof(*l));push(&labels,l);return labels.n-1;}
static void mark(int label,Buffer *b){Label *l=labels.v[label];if(l->defined)fatal("rótulo duplicado");l->defined=true;l->section=b==&code?0:1;l->position=b->n;}
static void fix(Buffer *b,int label,bool relative){Fix *f=mem(sizeof(*f));f->buffer=b;f->position=b->n;f->label=label;f->relative=relative;push(&fixes,f);if(relative)u32(b,0);else u64(b,0);}
static void branch(int label){u8(&code,0xe9);fix(&code,label,true);}
static void branch_if(unsigned condition,int label){INS(0x0f);u8(&code,condition);fix(&code,label,true);}
static void call_label(int label){u8(&code,0xe8);fix(&code,label,true);}
static void rt_call_raw(size_t offset){u8(&code,0xe8);int64_t rel=(int64_t)offset-(int64_t)(code.n+4);if(rel<INT32_MIN||rel>INT32_MAX)fatal("chamada fora do alcance");u32(&code,(uint32_t)(int32_t)rel);}
static void rt_call(size_t offset){
    if(target_windows){
#define MAP_RT(name) case RT_##name: offset=WRT_##name;break
        switch(offset){
        MAP_RT(stdout_write);MAP_RT(sleep);MAP_RT(civil);MAP_RT(file_sync);MAP_RT(file_replace);MAP_RT(file_remove);MAP_RT(print_float);MAP_RT(print_uint);MAP_RT(write);MAP_RT(print_str);MAP_RT(print_int);MAP_RT(print_char);MAP_RT(print_bool);MAP_RT(print_ptr);
        MAP_RT(alloc);MAP_RT(free);MAP_RT(len);MAP_RT(streq);MAP_RT(strbyte);MAP_RT(error);MAP_RT(finish);MAP_RT(read);MAP_RT(now);
        MAP_RT(args_init);MAP_RT(argc);MAP_RT(arg_len);MAP_RT(arg_copy);MAP_RT(io_error);MAP_RT(file_open);MAP_RT(file_close);MAP_RT(file_drop);MAP_RT(file_read);MAP_RT(file_write);
        default:fatal("rotina Windows desconhecida");
        }
#undef MAP_RT
    }
    else if(target_macos){
#define MAP_RT(name) case RT_##name: offset=MRT_##name;break
        switch(offset){
        MAP_RT(stdout_write);MAP_RT(sleep);MAP_RT(civil);MAP_RT(file_sync);MAP_RT(file_replace);MAP_RT(file_remove);MAP_RT(print_float);MAP_RT(print_uint);MAP_RT(write);MAP_RT(print_str);MAP_RT(print_int);MAP_RT(print_char);MAP_RT(print_bool);MAP_RT(print_ptr);
        MAP_RT(alloc);MAP_RT(free);MAP_RT(len);MAP_RT(streq);MAP_RT(strbyte);MAP_RT(error);MAP_RT(finish);MAP_RT(read);MAP_RT(now);
        MAP_RT(args_init);MAP_RT(argc);MAP_RT(arg_len);MAP_RT(arg_copy);MAP_RT(io_error);MAP_RT(file_open);MAP_RT(file_close);MAP_RT(file_drop);MAP_RT(file_read);MAP_RT(file_write);
        default:fatal("rotina macOS desconhecida");
        }
#undef MAP_RT
    }
    rt_call_raw(offset);
}
enum { RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI };
static void immediate(int reg,uint64_t value){
    if(optimize&&value<=UINT32_MAX){u8(&code,0xb8+(unsigned)reg);u32(&code,(uint32_t)value);}
    else if(optimize&&(int64_t)value>=INT32_MIN&&(int64_t)value<=INT32_MAX){INS(0x48,0xc7);u8(&code,0xc0+(unsigned)reg);u32(&code,(uint32_t)value);}
    else{u8(&code,0x48);u8(&code,0xb8+(unsigned)reg);u64(&code,value);}
}
static void movreg(int dst,int src){if(optimize&&dst==src)return;INS(0x48,0x89);u8(&code,0xc0+(unsigned)(src*8+dst));}
static void load_stack(int reg,int offset){INS(0x48,0x8b);u8(&code,0x84+(unsigned)(reg*8));u8(&code,0x24);u32(&code,(uint32_t)offset);}
static void load_label(int label){if(target_windows){INS(0x48,0xb8);fix(&code,label,false);}else{INS(0x48,0x8d,0x05);fix(&code,label,true);}}
static void call_virtual(int slot){
    INS(0x48,0x8b,0x00);
    if(target_windows){INS(0xff,0x90);u32(&code,(uint32_t)(slot*8));}
    else{INS(0x48,0x8d,0x90);u32(&code,(uint32_t)(slot*8));INS(0x48,0x8b,0x02,0x48,0x01,0xd0,0xff,0xd0);}
}
static void clean_stack(int count){if(count){INS(0x48,0x81,0xc4);u32(&code,(uint32_t)count*8);}}
static void site(int reg,Token *t);
static void panic_at(int reason,Token *t){immediate(RDI,(uint64_t)reason);site(RSI,t);rt_call(RT_error);INS(0x0f,0x0b);}
static void nonnull(Token *t){int ok=new_label();INS(0x48,0x85,0xc0);branch_if(0x85,ok);panic_at(1,t);mark(ok,&code);}
static int string_label(const char *s,size_t len){
    for(int i=0;i<strings.n;i++){String *old=strings.v[i];if(old->len==len&&!memcmp(old->str,s,len))return old->label;}
    String *str=mem(sizeof(*str));str->str=s;str->len=len;str->label=new_label();push(&strings,str);
    mark(str->label,&data);bytes(&data,s,len);u8(&data,0);return str->label;
}
static void site(int reg,Token *t){
    if(source_files.n==1&&t->file==source_files.v[0]){immediate(reg,(uint64_t)t->line);return;}
    size_t n=strlen(t->file->path)+32;char *location=mem(n);snprintf(location,n,"%s:%d",t->file->path,t->line);
    int label=string_label(location,strlen(location));
    if(target_windows){u8(&code,0x48);u8(&code,0xb8+(unsigned)reg);fix(&code,label,false);}
    else{INS(0x48,0x8d);u8(&code,0x05+(unsigned)reg*8);fix(&code,label,true);}
    /* A tagged pointer distinguishes a file:line string from the legacy line. */
    INS(0x48,0x0f,0xba);u8(&code,0xe8+(unsigned)reg);u8(&code,63);
}
static int value_size(Type ty){return value_bytes(ty);}
static void load_value(Type ty){
    if(inline_type(ty))return;
    int size=value_size(ty);
    if(size==1){if(ty.kind==TY_I8&&!ty.depth){INS(0x48,0x0f,0xbe,0x00);}else{INS(0x0f,0xb6,0x00);}}
    else if(size==2){if(ty.kind==TY_I16&&!ty.depth){INS(0x48,0x0f,0xbf,0x00);}else{INS(0x0f,0xb7,0x00);}}
    else if(size==4){if(ty.kind==TY_I32&&!ty.depth){INS(0x48,0x63,0x00);}else{INS(0x8b,0x00);}}
    else{INS(0x48,0x8b,0x00);}
}
static void store_value(Type ty){
    if(inline_type(ty)){
        int size=value_size(ty);
        if(size<=64){for(int offset=0;offset<size;offset+=8){INS(0x48,0x8b,0x48);u8(&code,(unsigned)offset);INS(0x48,0x89,0x4a);u8(&code,(unsigned)offset);}}
        else{movreg(RSI,RAX);movreg(RDI,RDX);immediate(RCX,(uint64_t)size);INS(0xfc,0xf3,0xa4);}
        movreg(RAX,RDX);
    }
    else if(value_size(ty)==1){INS(0x88,0x02);}else if(value_size(ty)==2){INS(0x66,0x89,0x02);}else if(value_size(ty)==4){INS(0x89,0x02);}else{INS(0x48,0x89,0x02);}
}
static void local_address(int reg,Var *v){INS(0x48,0x8d);u8(&code,0x85+(unsigned)reg*8);u32(&code,(uint32_t)(-8*(v->slot+1)));}
static void bool_result(unsigned condition){INS(0x0f);u8(&code,condition);INS(0xc0,0x0f,0xb6,0xc0);}
/* Evaluate only pure constants, with exactly the language's modular semantics.
 * Invalid divisions/shifts stay in the generated program, including skipped
 * short-circuit branches: optimization must not create compile-time traps. */
static bool constant(Node *n,uint64_t *value){
    if(floating(n->ty)||(integer(n->ty)&&n->ty.kind!=TY_I64&&n->ty.kind!=TY_U8))return false;
    if(n->kind==N_BINARY&&(floating(n->a->ty)||floating(n->b->ty)||(integer(n->a->ty)&&n->a->ty.kind!=TY_I64&&n->a->ty.kind!=TY_U8)))return false;
    if(n->kind==N_BUILTIN&&(n->op==T_NUMTYPE||(n->items.n&&floating(((Node*)n->items.v[0])->ty))))return false;
    uint64_t a,b;
    if(n->kind==N_INT){*value=n->t->number;return true;}
    if(n->kind==N_BOOL){*value=n->t->kind==T_TRUE;return true;}
    if(n->kind==N_UNARY&&constant(n->a,&a)){
        switch(n->op){case '+':*value=a;return true;case '-':*value=0-a;return true;case '~':*value=~a;return true;case '!':*value=!a;return true;default:return false;}
    }
    if(n->kind==N_BUILTIN&&n->items.n==1&&constant(n->items.v[0],&a)){
        if(n->op==T_I64)*value=a;else if(n->op==T_U8)*value=a&255;else if(n->op==T_BOOL)*value=!!a;else return false;return true;
    }
    if(n->kind!=N_BINARY||!constant(n->a,&a))return false;
    if(n->op==T_AND&&!a){*value=0;return true;}if(n->op==T_OR&&a){*value=1;return true;}
    if(!constant(n->b,&b)||n->a->ty.depth||n->b->ty.depth)return false;
    switch(n->op){
    case '+':*value=a+b;break;case '-':*value=a-b;break;case '*':*value=a*b;break;
    case '&':*value=a&b;break;case '|':*value=a|b;break;case '^':*value=a^b;break;
    case '/':case '%':if(!b)return false;if(a==UINT64_C(0x8000000000000000)&&b==UINT64_MAX){*value=n->op=='/'?a:0;break;}
        *value=n->op=='/'?(uint64_t)((int64_t)a/(int64_t)b):(uint64_t)((int64_t)a%(int64_t)b);break;
    case T_SHL:if(b>63)return false;*value=a<<b;break;
    case T_SHR:if(b>63)return false;*value=(uint64_t)((int64_t)a>>b);break;
    case T_EQ:*value=a==b;break;case T_NE:*value=a!=b;break;
    case '<':*value=(int64_t)a<(int64_t)b;break;case '>':*value=(int64_t)a>(int64_t)b;break;
    case T_LE:*value=(int64_t)a<=(int64_t)b;break;case T_GE:*value=(int64_t)a>=(int64_t)b;break;
    case T_AND:*value=!!a&&!!b;break;case T_OR:*value=!!a||!!b;break;default:return false;
    }return true;
}
#include "ranges.h"
#include "ir.h"
#include "backend_ir.h"
static void load_local(int reg,Var *v){
    if(inline_type(v->ty)){local_address(reg,v);return;}
    if(optimize&&v->reg>=0){u8(&code,v->reg>=8?0x4c:0x48);u8(&code,0x89);u8(&code,0xc0+(unsigned)((v->reg&7)*8+reg));return;}
    int offset=-8*(v->slot+1);
    INS(0x48,0x8b);
    if(offset>=-128){u8(&code,0x45+(unsigned)reg*8);u8(&code,(unsigned)offset);}
    else{u8(&code,0x85+(unsigned)reg*8);u32(&code,(uint32_t)offset);}
}
static bool operand_rcx(Node *n){
    uint64_t value;if(constant(n,&value)){immediate(RCX,value);return true;}
    if(n->kind==N_NAME&&n->var){load_local(RCX,n->var);return true;}return false;
}
static void gen_expr(Node *n);
/* Keep the thin-pointer ABI for legacy text/buffer interop. Immutable local
 * text bindings cache a length alongside their stack slot, including params. */
static void gen_text_length(Node *n){
    if(n->kind==N_STR){const char *zero=memchr(n->t->str,0,n->t->len);immediate(RAX,zero?(uint64_t)(zero-n->t->str):n->t->len);}
    else if(n->kind==N_NAME&&n->var->length_slot>=0){Var length={0};length.ty=type_i64;length.slot=n->var->length_slot;length.reg=-1;load_local(RAX,&length);}
    else{movreg(RDI,RAX);rt_call(RT_len);}
}
static void cache_text_length(Var *v){
    if(v->length_slot<0)return;
    INS(0x50);movreg(RDI,RAX);rt_call(RT_len);INS(0x48,0x89,0x85);u32(&code,(uint32_t)(-8*(v->length_slot+1)));INS(0x58);
}
static void gen_address(Node *n){
    if(optimize)fatal("emissor AST indisponível após lowering da IR");
    if(n->kind==N_NAME){INS(0x48,0x8d,0x85);u32(&code,(uint32_t)(-8*(n->var->slot+1)));}
    else if(n->kind==N_MEMBER){
        if(optimize&&value_type(n->a->ty)&&n->a->kind==N_NAME)local_address(RAX,n->a->var);else gen_expr(n->a);
        if(!value_type(n->a->ty))nonnull(n->t);INS(0x48,0x05);u32(&code,(uint32_t)n->field->offset);
    }
    else if(n->kind==N_INDEX){
        if(optimize&&n->bounds_proven){gen_expr(n->a);if(!operand_rcx(n->b)){INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);}if(slice_type(n->a->ty)){INS(0x48,0x8b,0x00);}else if(collection_of(n->a->ty)){INS(0x48,0x8b,0x40,0x18);}}
        else{
        gen_expr(n->a);INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);nonnull(n->t);
        if(slice_type(n->a->ty)){
            int valid=new_label();INS(0x48,0x3b,0x48,0x08);branch_if(0x82,valid);panic_at(9,n->t);mark(valid,&code);INS(0x48,0x8b,0x00);
        }else if(collection_of(n->a->ty)){
            int valid=new_label();INS(0x48,0x3b,0x48,0x08);branch_if(0x82,valid);panic_at(9,n->t);mark(valid,&code);
            INS(0x48,0x8b,0x40,0x18);
        }else if(n->a->ty.depth&&n->a->ownership){
            /* Only original managed buffer addresses reach this path. The
             * allocator header records requested bytes, including zero. */
            INS(0x48,0x8b,0x50,0xf0);int size=value_size(n->ty);
            if(optimize&&size>1&&!(size&(size-1))){unsigned shift=0;while((1u<<shift)!=(unsigned)size)shift++;INS(0x48,0xc1,0xea);u8(&code,shift);}
            else if(size>1){INS(0x50);movreg(RAX,RDX);INS(0x31,0xd2);immediate(RSI,(uint64_t)size);INS(0x48,0xf7,0xf6);movreg(RDX,RAX);INS(0x58);}
            int valid=new_label();INS(0x48,0x39,0xd1);branch_if(0x82,valid);panic_at(9,n->t);mark(valid,&code);
        }
        }
        int size=value_size(n->ty);
        if(optimize&&(size==1||size==2||size==4||size==8)){INS(0x48,0x8d,0x04);u8(&code,0x08+(size==8?192:size==4?128:size==2?64:0));}
        else{if(size>1){INS(0x48,0x69,0xc9);u32(&code,(uint32_t)size);}INS(0x48,0x01,0xc8);}
    }else if(n->kind==N_UNARY&&n->op=='*'){gen_expr(n->a);nonnull(n->t);}
    else fatal("posição gravável inválida no backend");
}
#include "numeric_emit.h"
#include "ffi_emit.h"
static void gen_operation(int op,Type left,Type right,Token *t){
    if(floating(left)){gen_float_operation(op,left);return;}
    if(left.depth&&(op=='+'||op=='-')){
        if(value_size(pointed(left))>1){INS(0x48,0x69,0xc9);u32(&code,(uint32_t)value_size(pointed(left)));}
        if(op=='+'){INS(0x48,0x01,0xc8);}else{INS(0x48,0x29,0xc8);}return;
    }
    if((op==T_EQ||op==T_NE)&&equal_type(left,type_str)&&equal_type(right,type_str)){
        movreg(RDI,RAX);movreg(RSI,RCX);rt_call(RT_streq);if(op==T_NE){INS(0x48,0x83,0xf0,0x01);}return;
    }
    if(value_type(left)&&(op==T_EQ||op==T_NE)){
        if(value_has_float(left)){gen_value_equality(left);if(op==T_NE){INS(0x48,0x83,0xf0,0x01);}}
        else{movreg(RSI,RAX);movreg(RDI,RCX);immediate(RCX,(uint64_t)value_size(left));INS(0xfc,0xf3,0xa6);bool_result(op==T_EQ?0x94:0x95);}return;
    }
    switch(op){
    case '+':INS(0x48,0x01,0xc8);break;case '-':INS(0x48,0x29,0xc8);break;
    case '*':INS(0x48,0x0f,0xaf,0xc1);break;
    case '&':INS(0x48,0x21,0xc8);break;case '|':INS(0x48,0x09,0xc8);break;case '^':INS(0x48,0x31,0xc8);break;
    case '/':case '%':{
        int zero_ok=new_label(),safe=new_label(),done=new_label();
        INS(0x48,0x85,0xc9);branch_if(0x85,zero_ok);panic_at(op=='/'?2:8,t);mark(zero_ok,&code);
        if(unsigned_integer(left)&&left.kind!=TY_U8){INS(0x31,0xd2,0x48,0xf7,0xf1);if(op=='%')movreg(RAX,RDX);break;}
        INS(0x48,0x83,0xf9,0xff);branch_if(0x85,safe);immediate(RDX,UINT64_C(0x8000000000000000));
        INS(0x48,0x39,0xd0);branch_if(0x85,safe);if(op=='%'){INS(0x31,0xc0);}branch(done);
        mark(safe,&code);INS(0x48,0x99,0x48,0xf7,0xf9);if(op=='%')movreg(RAX,RDX);mark(done,&code);break;
    }
    case T_SHL:case T_SHR:{
        int valid=new_label();INS(0x48,0x83,0xf9);u8(&code,equal_type(left,type_u8)?63:(unsigned)(scalar_bytes(left)*8-1));branch_if(0x86,valid);panic_at(3,t);mark(valid,&code);
        if(op==T_SHL){INS(0x48,0xd3,0xe0);}else{INS(0x48,0xd3);u8(&code,unsigned_integer(left)&&left.kind!=TY_U8?0xe8:0xf8);}break;
    }
    default:{
        unsigned cc=op==T_EQ?0x94:op==T_NE?0x95:op=='<'?0x9c:op==T_LE?0x9e:op=='>'?0x9f:0x9d;
        if(unsigned_integer(left)&&left.kind!=TY_U8){if(op=='<')cc=0x92;else if(op==T_LE)cc=0x96;else if(op=='>')cc=0x97;else if(op==T_GE)cc=0x93;}
        INS(0x48,0x39,0xc8);bool_result(cc);break;
    }
    }
}
/* Signed division truncates toward zero. The bias preserves that contract for
 * negative operands, including INT64_MIN, without a hardware idiv. */
static bool immediate_operation(int op,uint64_t value){
    if(!optimize)return false;
    if((op==T_SHL||op==T_SHR)&&value<64){INS(0x48,0xc1);u8(&code,op==T_SHL?0xe0:0xf8);u8(&code,(unsigned)value);return true;}
    if((int64_t)value>=INT32_MIN&&(int64_t)value<=INT32_MAX){
        unsigned opcode=op=='+'?0:op=='-'?5:op=='&'?4:op=='|'?1:op=='^'?6:8;
        if(opcode<8){INS(0x48,0x81);u8(&code,0xc0+opcode*8);u32(&code,(uint32_t)value);return true;}
    }
    if(op=='*'&&(value==3||value==5||value==9)){INS(0x48,0x8d,0x04);u8(&code,value==3?0x40:value==5?0x80:0xc0);return true;}
    if((op!='/'&&op!='%')||!value)return false;
    uint64_t magnitude=(int64_t)value<0?0-value:value;
    if(!(magnitude&(magnitude-1))){
        unsigned shift=0;while((UINT64_C(1)<<shift)!=magnitude)shift++;
        if(!shift){if(op=='%'){INS(0x31,0xc0);}else if((int64_t)value<0){INS(0x48,0xf7,0xd8);}return true;}
        movreg(RDX,RAX);INS(0x48,0xc1,0xfa,0x3f,0x48,0xc1,0xea);u8(&code,64-shift);
        if(op=='%')movreg(RCX,RAX);
        INS(0x48,0x01,0xd0,0x48,0xc1,0xf8);u8(&code,shift);
        if(op=='%'){INS(0x48,0xc1,0xe0);u8(&code,shift);INS(0x48,0x29,0xc1);movreg(RAX,RCX);}
        else if((int64_t)value<0){INS(0x48,0xf7,0xd8);}return true;
    }
    /* Nonzero literals other than -1 cannot trigger either division trap. */
    immediate(RCX,value);INS(0x48,0x99,0x48,0xf7,0xf9);if(op=='%')movreg(RAX,RDX);return true;
}
static bool constant_operation(int op,Node *right){uint64_t value;return constant(right,&value)&&immediate_operation(op,value);}
#include "expression_emit.h"
/* Inline only bounded, nontrapping scalar expression leaves. Arguments are
 * names/literals, so substitution cannot reorder effects, traps or mutation.
 * Semantic/ownership passes already validated the original call. */
static bool inline_leaf(Node *n,Function *f,int *budget){
    if(!n||--*budget<0||!(equal_type(n->ty,type_i64)||equal_type(n->ty,type_u8)||equal_type(n->ty,type_bool)))return false;
    if(n->kind==N_INT||n->kind==N_BOOL)return true;
    if(n->kind==N_NAME){for(int i=0;i<f->params.n;i++)if(n->var==f->params.v[i])return true;return false;}
    if(n->kind==N_UNARY&&(n->op=='+'||n->op=='-'||n->op=='~'||n->op=='!'))return inline_leaf(n->a,f,budget);
    if(n->kind==N_BINARY&&n->op!='/'&&n->op!='%'&&n->op!=T_SHL&&n->op!=T_SHR)return inline_leaf(n->a,f,budget)&&inline_leaf(n->b,f,budget);
    return false;
}
static Node *inline_substitute(Node *n,Node *call){
    if(n->kind==N_NAME)for(int i=0;i<call->fn->params.n;i++)if(n->var==call->fn->params.v[i])return call->items.v[i];
    Node *copy_node=mem(sizeof(*copy_node));*copy_node=*n;
    if(n->a)copy_node->a=inline_substitute(n->a,call);if(n->b)copy_node->b=inline_substitute(n->b,call);return copy_node;
}
static bool inline_call(Node *n){
    Function *f=n->fn;if(!optimize||debug_symbols||!f||!f->pure||f->owner||f->params.n>4||f->body->items.n!=1)return false;
    Node *ret=f->body->items.v[0];int budget=16;if(ret->kind!=N_RETURN||!inline_leaf(ret->a,f,&budget))return false;
    for(int i=0;i<n->items.n;i++){Node *a=n->items.v[i];if((a->kind!=N_NAME&&a->kind!=N_INT&&a->kind!=N_BOOL)||!(equal_type(a->ty,type_i64)||equal_type(a->ty,type_u8)||equal_type(a->ty,type_bool)))return false;}
    gen_expr(inline_substitute(ret->a,n));return true;
}
static void gen_expr_inner(Node *n){
    uint64_t folded;if(optimize&&constant(n,&folded)){immediate(RAX,folded);return;}
    switch(n->kind){
    case N_IS:case N_CAST:{
        gen_expr(n->a);INS(0x50,0x48,0x85,0xc0);int yes=new_label(),no=new_label(),done=new_label();branch_if(0x84,no);INS(0x48,0x8b,0x08);
        Class *target=find_class(n->decl.name);
        for(int i=0;i<classes.n;i++){Class *c=classes.v[i];if(c->record)continue;bool matches=false;for(Class *base=c;base;base=base->base)if(base==target)matches=true;if(matches){load_label(c->label);INS(0x48,0x39,0xc1);branch_if(0x84,yes);}}
        mark(no,&code);clean_stack(1);INS(0x31,0xc0);branch(done);mark(yes,&code);INS(0x58);if(n->kind==N_IS)immediate(RAX,1);mark(done,&code);break;
    }
    case N_ARRAY:{
        Node create={0};create.kind=N_NEW;create.t=n->t;create.cls=n->cls;gen_expr(&create);INS(0x50);
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);call_label(n->fn->label);clean_stack(1);}INS(0x58);break;
    }
    case N_INT:immediate(RAX,n->t->number);break;
    case N_BOOL:immediate(RAX,n->t->kind==T_TRUE?1:0);break;
    case N_NULL:INS(0x31,0xc0);break;
    case N_STR:load_label(string_label(n->t->str,n->t->len));break;
    case N_NAME:if(n->fn&&!n->var){load_label(n->fn->label);break;}if(optimize){load_local(RAX,n->var);break;}gen_address(n);load_value(n->ty);break;
    case N_MEMBER:gen_address(n);load_value(n->ty);break;
    case N_SELF:INS(0x48,0x8b,0x45,0xf8);break;
    case N_INDEX:
        if(equal_type(n->a->ty,type_str)){
            if(optimize&&((n->a->kind==N_NAME&&n->a->var->length_slot>=0)||n->a->kind==N_STR)){
                gen_expr(n->a);INS(0x50);gen_expr(n->b);INS(0x50);gen_text_length(n->a);INS(0x59,0x5a);
                int valid=new_label();INS(0x48,0x39,0xc1);branch_if(0x82,valid);panic_at(6,n->t);mark(valid,&code);INS(0x0f,0xb6,0x04,0x0a);
            }else{gen_expr(n->a);INS(0x50);gen_expr(n->b);movreg(RSI,RAX);INS(0x5f);site(RDX,n->t);rt_call(RT_strbyte);}
        }else{gen_address(n);load_value(n->ty);}break;
    case N_UNARY:
        if(n->op=='&')gen_address(n->a);
        else if(n->op=='*'){gen_address(n);load_value(n->ty);}
        else{
            gen_expr(n->a);
            if(n->op=='-'){if(floating(n->a->ty)){immediate(RCX,n->a->ty.kind==TY_F32?UINT64_C(0x80000000):UINT64_C(0x8000000000000000));INS(0x48,0x31,0xc8);}else{INS(0x48,0xf7,0xd8);}}else if(n->op=='~'){INS(0x48,0xf7,0xd0);}
            else if(n->op=='!'){INS(0x48,0x85,0xc0);bool_result(0x94);}
        }break;
    case N_BINARY:
        gen_expr(n->a);
        if(n->op==T_AND||n->op==T_OR){
            int end=new_label();INS(0x48,0x85,0xc0);branch_if(n->op==T_AND?0x84:0x85,end);gen_expr(n->b);mark(end,&code);
        }else{
            if((equal_type(n->a->ty,type_i64)||equal_type(n->a->ty,type_u8))&&constant_operation(n->op,n->b))break;
            if(!optimize||!operand_rcx(n->b)){INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);}
            if(!floating(n->a->ty)&&equal_type(n->a->ty,type_i64)&&optimize&&n->op=='*'&&constant(n->b,&folded)&&folded&&!(folded&(folded-1))){unsigned shift=0;while((UINT64_C(1)<<shift)!=folded)shift++;INS(0x48,0xc1,0xe0);u8(&code,shift);}
            else gen_operation(n->op,n->a->ty,n->b->ty,n->t);
        }break;
    case N_BUILTIN:
        if(n->op==T_UTF8){Node *literal=n->items.v[0];load_label(string_label(literal->t->str,literal->t->len));local_address(RDX,n->temp);INS(0x48,0x89,0x02);immediate(RAX,literal->t->len);INS(0x48,0x89,0x42,0x08);movreg(RAX,RDX);break;}
        if(n->op==T_C_CALLBACK){load_label(n->fn->callback_label);break;}
        if(n->op==T_SLICE_MAKE){
            Node *input=n->items.v[0];gen_expr(input);nonnull(n->t);
            if(slice_type(input->ty)){INS(0x48,0x8b,0x48,0x08,0x48,0x8b,0x00);}
            else{INS(0x48,0x8b,0x48,0xf0);int size=value_size(slice_element(n->ty));if(size>1){INS(0x50);movreg(RAX,RCX);INS(0x31,0xd2);immediate(RSI,(uint64_t)size);INS(0x48,0xf7,0xf6);movreg(RCX,RAX);INS(0x58);}}
            INS(0x50,0x51);gen_expr(n->items.v[1]);INS(0x50);gen_expr(n->items.v[2]);movreg(RDX,RAX);INS(0x58,0x59,0x5e);
            int valid_start=new_label(),valid_count=new_label();INS(0x48,0x39,0xc8);branch_if(0x86,valid_start);panic_at(9,n->t);mark(valid_start,&code);
            INS(0x48,0x29,0xc1,0x48,0x39,0xca);branch_if(0x86,valid_count);panic_at(9,n->t);mark(valid_count,&code);
            int size=value_size(slice_element(n->ty));if(size>1){INS(0x48,0x69,0xc0);u32(&code,(uint32_t)size);}INS(0x48,0x01,0xc6);
            local_address(RAX,n->temp);INS(0x48,0x89,0x30,0x48,0x89,0x50,0x08);break;
        }
        if(n->op==T_CIVIL){rt_call(RT_civil);break;}
        if(n->op==T_ARGC||n->op==T_IO_ERROR){rt_call(n->op==T_ARGC?RT_argc:RT_io_error);break;}
        if(n->op==T_SLEEP||n->op==T_FILE_REMOVE||n->op==T_FILE_SYNC){gen_expr(n->items.v[0]);movreg(RDI,RAX);rt_call(n->op==T_SLEEP?RT_sleep:n->op==T_FILE_REMOVE?RT_file_remove:RT_file_sync);break;}
        if(n->op==T_ARG_LEN||n->op==T_FILE_CLOSE){gen_expr(n->items.v[0]);movreg(RDI,RAX);rt_call(n->op==T_ARG_LEN?RT_arg_len:RT_file_close);break;}
        if(n->op==T_FILE_REPLACE){gen_expr(n->items.v[0]);INS(0x50);gen_expr(n->items.v[1]);movreg(RSI,RAX);INS(0x5f);rt_call(RT_file_replace);break;}
        if(n->op==T_FILE_OPEN){gen_expr(n->items.v[0]);INS(0x50);gen_expr(n->items.v[1]);movreg(RSI,RAX);INS(0x5f);rt_call(RT_file_open);break;}
        if(n->op==T_FILE_READ||n->op==T_FILE_WRITE||n->op==T_ARG_COPY||n->op==T_WRITE_BYTES){
            for(int i=0;i<3;i++){gen_expr(n->items.v[i]);INS(0x50);}
            INS(0x5a,0x5e,0x5f);
            if(slice_type(((Node*)n->items.v[1])->ty)){
                int valid=new_label();INS(0x48,0x3b,0x56,0x08);branch_if(0x86,valid);panic_at(4,n->t);mark(valid,&code);INS(0x48,0x8b,0x36);
            }else if(((Node*)n->items.v[1])->ownership){int valid=new_label();INS(0x48,0x3b,0x56,0xf0);branch_if(0x86,valid);panic_at(4,n->t);mark(valid,&code);}
            rt_call(n->op==T_FILE_READ?RT_file_read:n->op==T_FILE_WRITE?RT_file_write:n->op==T_WRITE_BYTES?RT_stdout_write:RT_arg_copy);break;
        }
        if(n->op==T_NOW){rt_call(RT_now);break;}
        if(n->op==T_READ){
            Node *buffer=n->items.v[0];gen_expr(buffer);INS(0x50);gen_expr(n->items.v[1]);movreg(RSI,RAX);INS(0x5f);
            if(buffer->ownership){
                int valid=new_label();INS(0x48,0x3b,0x77,0xf0);branch_if(0x86,valid);panic_at(4,n->t);mark(valid,&code);
            }
            site(RDX,n->t);rt_call(RT_read);break;
        }
        if(n->op==T_MOVE){gen_address(n->items.v[0]);movreg(RDX,RAX);load_value(n->ty);INS(0x48,0xc7,0x02);u32(&code,0);break;}
        gen_expr(n->items.v[0]);
        if(n->op==T_BUFFER){
            int valid=new_label();immediate(RCX,(uint64_t)INT64_MAX/(unsigned)value_size(n->decl));INS(0x48,0x39,0xc8);branch_if(0x86,valid);panic_at(4,n->t);mark(valid,&code);
            if(value_size(n->decl)>1){INS(0x48,0x69,0xc0);u32(&code,(uint32_t)value_size(n->decl));}movreg(RDI,RAX);site(RSI,n->t);rt_call(RT_alloc);
        }
        else if(n->op==T_ASSERT){
            int valid=new_label();INS(0x48,0x85,0xc0);branch_if(0x85,valid);
            if(n->items.n==2){gen_expr(n->items.v[1]);movreg(RDI,RAX);immediate(RSI,2);rt_call(RT_print_str);immediate(RDI,10);immediate(RSI,2);rt_call(RT_print_char);}
            panic_at(10,n->t);mark(valid,&code);
        }
        else if(n->op==T_ALLOC){movreg(RDI,RAX);site(RSI,n->t);rt_call(RT_alloc);}
        else if(n->op==T_LEN){
            Type arg=((Node*)n->items.v[0])->ty;
            if(slice_type(arg)){INS(0x48,0x8b,0x40,0x08);}
            else if(arg.depth){nonnull(n->t);INS(0x48,0x8b,0x40,0xf0);int size=value_size(pointed(arg));if(size>1){INS(0x31,0xd2);immediate(RCX,(uint64_t)size);INS(0x48,0xf7,0xf1);}}
            else if(collection_of(arg)){nonnull(n->t);INS(0x48,0x8b,0x40,0x08);}else if(optimize)gen_text_length(n->items.v[0]);else{movreg(RDI,RAX);rt_call(RT_len);}
        }
        else if(n->op==T_TEXT){nonnull(n->t);}
        else if(n->op==T_U8||n->op==T_I64||n->op==T_NUMTYPE){gen_numeric_cast(((Node*)n->items.v[0])->ty,n->ty);}
        else if(n->op==T_BOOL){if(floating(((Node*)n->items.v[0])->ty)){movreg(RCX,RAX);immediate(RDX,((Node*)n->items.v[0])->ty.kind==TY_F32?UINT64_C(0x7fffffff):UINT64_C(0x7fffffffffffffff));INS(0x48,0x21,0xd0);}INS(0x48,0x85,0xc0);bool_result(0x95);}break;
    case N_CALL:
        if(inline_call(n))break;
        if(!n->fn){
            if(closure_type(n->a->ty)){
                gen_expr(n->a);
                if(n->temp){INS(0x50);local_address(RAX,n->temp);INS(0x50);load_stack(RAX,8);}
                INS(0x50);for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
                load_stack(RAX,n->items.n*8);nonnull(n->t);call_virtual(0);clean_stack(n->items.n+1+(n->temp?2:0));break;
            }
            /* Evaluate the callee once, before arguments. The saved address is
             * below the argument area and does not change the native ABI. */
            gen_expr(n->a);INS(0x50);
            if(n->temp){local_address(RAX,n->temp);INS(0x50);}
            for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
            load_stack(RAX,(n->items.n+(n->temp?1:0))*8);nonnull(n->t);INS(0xff,0xd0);
            clean_stack(n->items.n+1+(n->temp?1:0));break;
        }
        if(n->temp){local_address(RAX,n->temp);INS(0x50);}
        if(n->fn->owner){gen_expr(n->a->a);INS(0x50);}
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        if(n->fn->owner){
            load_stack(RAX,n->items.n*8);nonnull(n->t);if(n->op==T_SUPER)call_label(n->fn->label);else call_virtual(n->slot);
        }else call_label(n->fn->label);
        clean_stack(n->items.n+(n->fn->owner?1:0)+(n->temp?1:0));break;
    case N_NEW:{
        if(n->cls->value){
            local_address(RDI,n->temp);immediate(RCX,(uint64_t)n->cls->size);INS(0x31,0xc0,0xfc,0xf3,0xaa);
            if(n->variant){local_address(RDX,n->temp);INS(0x48,0xc7,0x02);u32(&code,(uint32_t)n->variant->tag);}
            Vec fields=n->variant?n->variant->fields:n->cls->fields;
            for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);Field *f=fields.v[i];local_address(RDX,n->temp);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)f->offset);store_value(f->ty);}
            local_address(RAX,n->temp);break;
        }
        immediate(RDI,(uint64_t)n->cls->size);site(RSI,n->t);rt_call(RT_alloc);INS(0x50);
        if(n->variant){
            INS(0x48,0xc7,0x00);u32(&code,(uint32_t)n->variant->tag);
            for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);load_stack(RDX,0);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)((Field*)n->variant->fields.v[i])->offset);store_value(((Field*)n->variant->fields.v[i])->ty);}
            INS(0x58);break;
        }
        load_label(n->cls->label);load_stack(RDX,0);INS(0x48,0x89,0x02);
        for(int i=0;i<n->cls->fields.n;i++){
            Field *f=n->cls->fields.v[i];if(equal_type(f->ty,type_str)){
                load_label(string_label("",0));load_stack(RDX,0);INS(0x48,0x89,0x82);u32(&code,(uint32_t)f->offset);
            }
        }
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        if(n->cls->record||n->cls->closure){
            for(int i=0;i<n->items.n;i++){Field *f=n->cls->fields.v[i];load_stack(RAX,(n->items.n-1-i)*8);load_stack(RDX,n->items.n*8);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)f->offset);store_value(f->ty);}clean_stack(n->items.n);
        }
        if(n->fn){
            load_stack(RAX,n->items.n*8);call_label(n->fn->label);clean_stack(n->items.n);
        }
        INS(0x58);break;
    }
    default:fatal("expressão inválida no backend");
    }
}
static void gen_expr(Node *n){
    if(optimize)fatal("emissor AST indisponível após lowering da IR");
    gen_expr_inner(n);if(!n->ty.depth&&n->ty.kind>=TY_I8)normalize_numeric(n->ty);if(n->temp&&n->kind!=N_NEW&&n->kind!=N_CALL){local_address(RDX,n->temp);store_value(n->ty);}
}
static int return_label,loop_count,loop_start[MAX_NEST],loop_end[MAX_NEST],loop_cleanup[MAX_NEST];
static Function *generating;
static int generating_body;
static Vec cleanups;
static void store_local(Var *v){
    normalize_numeric(v->ty);
    if(inline_type(v->ty)){local_address(RDX,v);store_value(v->ty);return;}
    if(optimize&&v->reg>=0){
        
        u8(&code,v->reg>=8?0x49:0x48);u8(&code,0x89);u8(&code,0xc0+(unsigned)(v->reg&7));
    }else{INS(0x48,0x89,0x85);u32(&code,(uint32_t)(-8*(v->slot+1)));}
}
static void gen_release(Type ty){
    if(closure_type(ty)){int done=new_label();INS(0x48,0x85,0xc0);branch_if(0x84,done);INS(0x50);call_virtual(-1);clean_stack(1);mark(done,&code);return;}
    if(equal_type(ty,type_file)){movreg(RDI,RAX);rt_call(RT_file_drop);return;}
    Class *cls=object(ty)?find_class(ty.name):NULL;
    if(cls&&!cls->record&&!collection_of(ty)){
        int done=new_label();INS(0x48,0x85,0xc0);branch_if(0x84,done);INS(0x50);call_virtual(-1);clean_stack(1);mark(done,&code);return;
    }
    if(cls&&has_owned_fields(cls)){INS(0x50);call_label(cls->drop_label);clean_stack(1);return;}
    if(collection_of(ty)){
        int done=new_label();INS(0x48,0x85,0xc0);branch_if(0x84,done);INS(0x50);
        Function *dispose=find_method(find_class(ty.name),"dispose",NULL);call_label(dispose->label);INS(0x58);mark(done,&code);
    }
    movreg(RDI,RAX);rt_call(RT_free);
}
static void gen_cleanup(int from){
    for(int i=cleanups.n-1;i>=from;i--){Var *v=cleanups.v[i];load_local(RAX,v);gen_release(v->ty);}
}
static void gen_false(Node *n,int label){
    if(optimize)fatal("emissor AST indisponível após lowering da IR");
    if(optimize&&n->kind==N_BINARY&&(n->op==T_EQ||n->op==T_NE)&&n->a->kind==N_BINARY&&n->a->op=='%'&&equal_type(n->a->a->ty,type_i64)){
        uint64_t divisor,zero;
        if(constant(n->b,&zero)&&!zero&&constant(n->a->b,&divisor)&&divisor){
            uint64_t magnitude=(int64_t)divisor<0?0-divisor:divisor;
            if(!(magnitude&(magnitude-1))){
                gen_expr(n->a->a);immediate(RCX,magnitude-1);INS(0x48,0x85,0xc8);branch_if(n->op==T_EQ?0x85:0x84,label);return;
            }
        }
    }
    if(optimize&&n->kind==N_BINARY&&(n->op==T_EQ||n->op==T_NE||n->op=='<'||n->op=='>'||n->op==T_LE||n->op==T_GE)&&!equal_type(n->a->ty,type_str)&&!value_type(n->a->ty)&&!floating(n->a->ty)&&(!integer(n->a->ty)||equal_type(n->a->ty,type_i64)||equal_type(n->a->ty,type_u8))){
        gen_expr(n->a);
        unsigned cc=n->op==T_EQ?0x85:n->op==T_NE?0x84:n->op=='<'?0x8d:n->op==T_LE?0x8f:n->op=='>'?0x8e:0x8c;
        uint64_t value;
        if(constant(n->b,&value)&&(int64_t)value>=INT32_MIN&&(int64_t)value<=INT32_MAX){INS(0x48,0x3d);u32(&code,(uint32_t)value);}
        else{if(!operand_rcx(n->b)){INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);}INS(0x48,0x39,0xc8);}
        branch_if(cc,label);return;
    }
    gen_expr(n);INS(0x48,0x85,0xc0);branch_if(0x84,label);
}
static void gen_stmt(Node *n){
    if(optimize)fatal("emissor AST indisponível após lowering da IR");
    n->code_start=code.n;
    if(debug_symbols&&n->kind!=N_BLOCK&&n->kind!=N_UNSAFE){DebugSite *site=mem(sizeof(*site));site->offset=code.n;site->token=n->t;push(&debug_sites,site);}
    switch(n->kind){
    case N_MATCH:{
        gen_expr(n->a);if(!n->cls->value)nonnull(n->t);store_local(n->var);int done=new_label(),outer=cleanups.n;
        if(n->ownership==1)push(&cleanups,n->var);int arm_base=cleanups.n;
        for(int i=0;i<n->items.n;i++){
            Node *arm=n->items.v[i];int next=new_label();load_local(RAX,n->var);INS(0x48,0x81,0x38);u32(&code,(uint32_t)arm->variant->tag);branch_if(0x85,next);
            for(int j=0;j<arm->items.n;j++){Node *binding=arm->items.v[j];Field *field=arm->variant->fields.v[j];load_local(RAX,n->var);INS(0x48,0x05);u32(&code,(uint32_t)field->offset);
                if(binding->var->ownership==1){movreg(RDX,RAX);load_value(field->ty);INS(0x48,0xc7,0x02);u32(&code,0);push(&cleanups,binding->var);}else load_value(field->ty);store_local(binding->var);}
            gen_stmt(arm->a);gen_cleanup(arm_base);cleanups.n=arm_base;branch(done);mark(next,&code);
        }
        panic_at(10,n->t);mark(done,&code);gen_cleanup(outer);cleanups.n=outer;break;
    }
    case N_BLOCK:{int old=cleanups.n;for(int i=0;i<n->items.n;i++)gen_stmt(n->items.v[i]);gen_cleanup(old);cleanups.n=old;break;}
    case N_UNSAFE:gen_stmt(n->a);break;
    case N_LET:gen_expr(n->a);cache_text_length(n->var);store_local(n->var);if(n->ownership==1)push(&cleanups,n->var);break;
    case N_DEFER:push(&cleanups,n->var);break;
    case N_ASSIGN:
        if(n->replace_owned){
            gen_address(n->a);INS(0x50);gen_expr(n->b);INS(0x50);
            load_stack(RAX,8);load_value(n->a->ty);gen_release(n->a->ty);
            INS(0x58,0x5a);store_value(n->a->ty);break;
        }
        if(optimize&&n->a->kind==N_NAME){
            if(n->op=='='){gen_expr(n->b);cache_text_length(n->a->var);}
            else{load_local(RAX,n->a->var);if(!((equal_type(n->a->ty,type_i64)||equal_type(n->a->ty,type_u8))&&constant_operation(compound_op(n->op),n->b))){if(!operand_rcx(n->b)){INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);}gen_operation(compound_op(n->op),n->a->ty,n->b->ty,n->t);}}
            store_local(n->a->var);break;
        }
        gen_address(n->a);INS(0x50);
        if(n->op=='='){gen_expr(n->b);if(n->a->kind==N_NAME)cache_text_length(n->a->var);}
        else{load_value(n->a->ty);INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);gen_operation(compound_op(n->op),n->a->ty,n->b->ty,n->t);}
        INS(0x5a);store_value(n->a->ty);break;
    case N_IF:{
        int no=new_label(),end=new_label();gen_false(n->a,no);gen_stmt(n->b);branch(end);
        mark(no,&code);if(n->c)gen_stmt(n->c);mark(end,&code);break;
    }
    case N_WHILE:{
        int start=new_label(),end=new_label(),step=n->step?new_label():start;loop_start[loop_count]=step;loop_end[loop_count]=end;loop_cleanup[loop_count++]=cleanups.n;
        mark(start,&code);gen_false(n->a,end);gen_stmt(n->b);if(n->step){mark(step,&code);gen_stmt(n->step);}branch(start);mark(end,&code);loop_count--;break;
    }
    case N_BREAK:gen_cleanup(loop_cleanup[loop_count-1]);branch(loop_end[loop_count-1]);break;
    case N_CONTINUE:gen_cleanup(loop_cleanup[loop_count-1]);branch(loop_start[loop_count-1]);break;
    case N_RETURN:
        if(optimize&&generating->pure&&n->a&&n->a->kind==N_CALL&&n->a->fn==generating){
            for(int i=0;i<n->a->items.n;i++){gen_expr(n->a->items.v[i]);INS(0x50);}
            for(int i=n->a->items.n-1;i>=0;i--){INS(0x58);store_local(generating->params.v[i]);}
            branch(generating_body);break;
        }
        if(n->a)gen_expr(n->a);else{INS(0x31,0xc0);}
        if(inline_type(generating->result)){INS(0x48,0x8b,0x95);u32(&code,(uint32_t)(16+8*(generating->params.n+(generating->owner?1:0))));store_value(generating->result);}
        if(cleanups.n){INS(0x50);gen_cleanup(0);INS(0x58);}branch(return_label);break;
    case N_EXPR:gen_expr(n->a);break;
    case N_FREE:
        if(n->var){gen_address(n->a);INS(0x50);load_value(n->a->ty);gen_release(n->a->ty);INS(0x5a,0x48,0xc7,0x02);u32(&code,0);}
        else{gen_expr(n->a);gen_release(n->a->ty);}break;
    case N_PRINT:
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        for(int i=0;i<n->items.n;i++){
            if(i&&n->op!=T_WRITE){immediate(RDI,32);immediate(RSI,1);rt_call(RT_print_char);}
            Node *a=n->items.v[i];load_stack(RDI,(n->items.n-1-i)*8);if(a->ty.kind==TY_F32&&!a->ty.depth){movreg(RAX,RDI);gen_numeric_cast(a->ty,(Type){TY_F64,0,NULL,NULL});movreg(RDI,RAX);}immediate(RSI,1);
            if(slice_type(a->ty)){INS(0x48,0x8b,0x57,0x08,0x48,0x8b,0x37);immediate(RDI,1);rt_call(RT_write);}
            else rt_call(floating(a->ty)?RT_print_float:unsigned_integer(a->ty)&&a->ty.kind!=TY_U8?RT_print_uint:numeric(a->ty)?RT_print_int:equal_type(a->ty,type_bool)?RT_print_bool:equal_type(a->ty,type_str)?RT_print_str:RT_print_ptr);
        }
        clean_stack(n->items.n);if(n->op!=T_WRITE){immediate(RDI,10);immediate(RSI,1);rt_call(RT_print_char);}break;
    default:fatal("instrução inválida no backend");
    }
    n->code_end=code.n;
}
#include "backend_emit.h"
static size_t entry_offset;
#include "arm64_emit.h"
static void generate(void){
    if(target_arm64){generate_arm64();return;}
    if(target_windows)bytes(&code,runtime_win_blob,sizeof(runtime_win_blob));else if(target_macos)bytes(&code,runtime_macos_blob,sizeof(runtime_macos_blob));else bytes(&code,runtime_blob,sizeof(runtime_blob));
    for(int i=0;i<all_functions.n;i++){Function *f=all_functions.v[i];f->label=new_label();if(f->callback){f->callback_label=new_label();if(callback_state_label<0)callback_state_label=new_label();}if(f->foreign)f->import_label=native_import(f->foreign_library[target_windows?1:0],f->foreign_symbol);}
    for(int i=0;i<classes.n;i++){Class *c=classes.v[i];c->label=new_label();if(has_owned_fields(c)||!c->record)c->drop_label=new_label();}
    entry_offset=code.n;
    if(target_macos){INS(0x31,0xed,0x56,0x57);rt_call_raw(MRT_init);INS(0x5f,0x5e);}
    else{INS(0x31,0xed,0x54);rt_call_raw(target_windows?WRT_init:RT_init);INS(0x5f);}
    rt_call(RT_args_init);
    if(callback_state_label>=0){INS(0x4c,0x89,0x3d);fix(&code,callback_state_label,true);}
    /* R15 is reserved for runtime state and preserved by all runtime routines. */
    INS(0x49,0xc7,0x87);u32(&code,88);u32(&code,debug_memory?1:0);call_label(main_function->label);
    INS(0x50);rt_call(RT_finish);INS(0x58);
    if(isvoid(main_function->result)){INS(0x31,0xff);}else{movreg(RDI,RAX);INS(0x81,0xe7,0xff,0x00,0x00,0x00);}
    if(target_windows)rt_call_raw(WRT_exit);else if(target_macos)rt_call_raw(MRT_exit);else{immediate(RAX,60);INS(0x0f,0x05,0x0f,0x0b);}
    for(int i=0;i<all_functions.n;i++){
        Function *f=all_functions.v[i];generating=f;mark(f->label,&code);return_label=new_label();loop_count=0;cleanups.n=0;
        if(f->foreign){emit_c_import(f);f->code_end=code.n;continue;}
        INS(0x55,0x48,0x89,0xe5);
        unsigned saved[4],saved_count=0;
        const unsigned candidates[]={3,12,13,14};
        if(optimize)for(int r=0;r<4;r++)for(int j=0;j<f->vars.n;j++)if(((Var*)f->vars.v[j])->reg==(int)candidates[r]){saved[saved_count++]=candidates[r];break;}
        uint32_t slots=(uint32_t)(f->slots+(f->owner?1:0));
        uint32_t locals=(slots+saved_count)*8;locals=(locals+15)&~15u;
        /* Check before touching the frame: also covers exceptionally large
         * locals, not just recursive call count. Keep headroom for diagnostics. */
        movreg(RAX,RSP);INS(0x48,0x2d);u32(&code,locals);INS(0x49,0x3b,0x47,0x68);
        int stack_ok=new_label();branch_if(0x83,stack_ok);panic_at(11,f->t);mark(stack_ok,&code);
        if(target_windows&&locals>=4096){
            /* Grow through every Windows guard page before the first call.
             * Jumping directly over it can fault in otherwise valid functions. */
            immediate(RCX,locals/4096);int probe=new_label();mark(probe,&code);
            INS(0x48,0x81,0xec);u32(&code,4096);INS(0x85,0x04,0x24,0x48,0xff,0xc9);branch_if(0x85,probe);
            if(locals%4096){INS(0x48,0x81,0xec);u32(&code,locals%4096);}
        }else{INS(0x48,0x81,0xec);u32(&code,locals);}
        for(unsigned r=0;r<saved_count;r++){u8(&code,saved[r]>=8?0x4c:0x48);u8(&code,0x89);u8(&code,0x85+((saved[r]&7)*8));u32(&code,(uint32_t)(-8*(slots+r+1)));}
        int count=f->params.n+(f->owner?1:0);
        if(f->owner){INS(0x48,0x8b,0x85);u32(&code,(uint32_t)(16+8*(count-1)));INS(0x48,0x89,0x45,0xf8);}
        for(int j=0;j<f->params.n;j++){
            Var *v=f->params.v[j];int index=j+(f->owner?1:0);
            INS(0x48,0x8b,0x85);u32(&code,(uint32_t)(16+8*(count-1-index)));
            store_local(v);
            if(v->ownership==1)push(&cleanups,v);
        }
        for(int j=0;j<f->params.n;j++){Var *v=f->params.v[j];if(v->length_slot>=0){load_local(RAX,v);cache_text_length(v);}}
        generating_body=new_label();mark(generating_body,&code);
        if(optimize)backend_emit_function(backend_function(f));
        else{gen_stmt(f->body);gen_cleanup(0);if(isvoid(f->result)){INS(0x31,0xc0);}else panic_at(7,f->t);}
        mark(return_label,&code);
        for(unsigned r=0;r<saved_count;r++){u8(&code,saved[r]>=8?0x4c:0x48);u8(&code,0x8b);u8(&code,0x85+((saved[r]&7)*8));u32(&code,(uint32_t)(-8*(slots+r+1)));}
        INS(0xc9,0xc3);f->code_end=code.n;
    }
    for(int i=0;i<all_functions.n;i++){Function *f=all_functions.v[i];if(f->callback)emit_c_callback(f);}
    /* One drop function per concrete record. Calls keep recursive types finite
     * in the compiler and share the same runtime stack guard as user code. */
    for(int i=0;i<classes.n;i++){
        Class *c=classes.v[i];if(!has_owned_fields(c)&&c->record)continue;
        mark(c->drop_label,&code);INS(0x55,0x48,0x89,0xe5);
        movreg(RAX,RSP);INS(0x48,0x83,0xe8,0x10,0x49,0x3b,0x47,0x68);
        int ok=new_label(),done=new_label();branch_if(0x83,ok);panic_at(11,c->t);mark(ok,&code);
        INS(0x48,0x83,0xec,0x10,0x48,0x8b,0x45,0x10,0x48,0x89,0x45,0xf8,0x48,0x85,0xc0);branch_if(0x84,done);
        Function *destructor=find_method(c,"drop",NULL);if(destructor){INS(0xff,0x75,0xf8);call_label(destructor->label);clean_stack(1);}
        for(int k=0;k<(c->tagged?c->variants.n:1);k++){
            Vec fields=c->tagged?((Variant*)c->variants.v[k])->fields:c->fields;int next=new_label();
            if(c->tagged){INS(0x48,0x8b,0x45,0xf8,0x48,0x81,0x38);u32(&code,(uint32_t)((Variant*)c->variants.v[k])->tag);branch_if(0x85,next);}
            for(int j=fields.n-1;j>=0;j--){Field *f=fields.v[j];if(!f->owned)continue;
                INS(0x48,0x8b,0x45,0xf8,0x48,0x8b,0x80);u32(&code,(uint32_t)f->offset);gen_release(f->ty);
            }mark(next,&code);
        }
        INS(0x48,0x8b,0x7d,0xf8);rt_call(RT_free);mark(done,&code);INS(0xc9,0xc3);
    }
    while(data.n%8)u8(&data,0);
    for(int i=0;i<classes.n;i++){
        Class *c=classes.v[i];if(!c->record)fix(&data,c->drop_label,false);mark(c->label,&data);
        if(!c->methods.n)u64(&data,0);
        for(int j=0;j<c->methods.n;j++)fix(&data,((Function*)c->methods.v[j])->label,false);
    }
    if(!data.n)u8(&data,0);
}
static size_t align_page(size_t size){size_t page=target_macos&&target_arm64?16384:4096;return (size+page-1)&~(page-1);}
#define ELF_BASE UINT64_C(0)
#include "debug_info.h"
static void apply_fixes(uint64_t base,size_t text_rva,size_t data_rva){
    if(target_arm64)apply_arm_fixes(base,text_rva,data_rva);
    for(int i=0;i<fixes.n;i++){
        Fix *f=fixes.v[i];Label *l=labels.v[f->label];if(!l->defined)fatal("rótulo não definido");
        uint64_t address=base+(l->section==2?native_import_rva:l->section?data_rva:text_rva)+l->position;
        if(f->relative){
            int64_t diff=(int64_t)address-(int64_t)(base+text_rva+f->position+4);
            if(diff<INT32_MIN||diff>INT32_MAX)fatal("salto fora do alcance");
            uint32_t d=(uint32_t)(int32_t)diff;for(int j=0;j<4;j++)f->buffer->v[f->position+(size_t)j]=(unsigned char)(d>>(8*j));
        }else{
            if(!target_windows&&f->buffer==&data)address-=base+data_rva+f->position;
            for(int j=0;j<8;j++)f->buffer->v[f->position+(size_t)j]=(unsigned char)(address>>(8*j));
        }
    }
}
#include "ffi_elf.h"
static void write_elf(const char *path){
    for(int i=0;i<fixes.n;i++){Fix *f=fixes.v[i];if(f->buffer==&code&&!f->relative)fatal("ELF PIE exige endereços de código relativos a RIP");}
    size_t data_offset=align_page(4096+code.n);bool dynamic=native_imports.n!=0||callback_state_label>=0;
    if(dynamic){native_import_rva=align_page(data_offset+data.n);build_elf_imports(native_import_rva);}
    apply_fixes(ELF_BASE,4096,data_offset);
    Elf64_Ehdr eh={0};memcpy(eh.e_ident,ELFMAG,SELFMAG);eh.e_ident[EI_CLASS]=ELFCLASS64;eh.e_ident[EI_DATA]=ELFDATA2LSB;eh.e_ident[EI_VERSION]=EV_CURRENT;
    eh.e_type=ET_DYN;eh.e_machine=target_arm64?183:EM_X86_64;eh.e_version=EV_CURRENT;eh.e_entry=ELF_BASE+4096+entry_offset;
    eh.e_phoff=sizeof(eh);eh.e_ehsize=sizeof(eh);eh.e_phentsize=sizeof(Elf64_Phdr);eh.e_phnum=4;
    Elf64_Phdr ph[9]={0};
    ph[0]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R,.p_offset=0,.p_vaddr=ELF_BASE,.p_paddr=ELF_BASE,.p_filesz=4096,.p_memsz=4096,.p_align=4096};
    ph[1]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R|PF_X,.p_offset=4096,.p_vaddr=ELF_BASE+4096,.p_paddr=ELF_BASE+4096,.p_filesz=code.n,.p_memsz=code.n,.p_align=4096};
    ph[2]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R,.p_offset=data_offset,.p_vaddr=ELF_BASE+data_offset,.p_paddr=ELF_BASE+data_offset,.p_filesz=data.n,.p_memsz=data.n,.p_align=4096};
    ph[3]=(Elf64_Phdr){.p_type=PT_GNU_STACK,.p_flags=PF_R|PF_W,.p_align=16};
    const char *interpreter=target_arm64?"/lib/ld-linux-aarch64.so.1":"/lib64/ld-linux-x86-64.so.2";size_t interpreter_size=strlen(interpreter)+1;
    if(dynamic){
        eh.e_phnum=9;
        ph[4]=(Elf64_Phdr){.p_type=6,.p_flags=PF_R,.p_offset=sizeof(eh),.p_vaddr=sizeof(eh),.p_paddr=sizeof(eh),.p_filesz=sizeof(ph),.p_memsz=sizeof(ph),.p_align=8};
        ph[5]=(Elf64_Phdr){.p_type=3,.p_flags=PF_R,.p_offset=1024,.p_vaddr=1024,.p_paddr=1024,.p_filesz=interpreter_size,.p_memsz=interpreter_size,.p_align=1};
        ph[6]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R|PF_W,.p_offset=native_import_rva,.p_vaddr=native_import_rva,.p_paddr=native_import_rva,.p_filesz=elf_imports.n,.p_memsz=align_page(elf_imports.n),.p_align=4096};
        ph[7]=(Elf64_Phdr){.p_type=2,.p_flags=PF_R|PF_W,.p_offset=native_import_rva+elf_dynamic_offset,.p_vaddr=native_import_rva+elf_dynamic_offset,.p_paddr=native_import_rva+elf_dynamic_offset,.p_filesz=elf_dynamic_size,.p_memsz=elf_dynamic_size,.p_align=8};
        ph[8]=(Elf64_Phdr){.p_type=0x6474e552,.p_flags=PF_R,.p_offset=native_import_rva,.p_vaddr=native_import_rva,.p_paddr=native_import_rva,.p_filesz=elf_imports.n<elf_relro_size?elf_imports.n:elf_relro_size,.p_memsz=elf_relro_size,.p_align=1};
        /* PT_PHDR must precede LOAD entries for the dynamic loader. */
        Elf64_Phdr first=ph[4],interp=ph[5],stack=ph[3];ph[4]=ph[2];ph[3]=ph[1];ph[2]=ph[0];ph[0]=first;ph[1]=interp;ph[5]=stack;
    }
    if(debug_symbols)append_debug_elf(&eh,dynamic?native_import_rva+elf_imports.n:data_offset+data.n);
    protect_output(path);
    FILE *fp=fopen(path,"wb");if(!fp)fatal("não foi possível criar %s: %s",path,strerror(errno));
    unsigned char header[4096]={0};memcpy(header,&eh,sizeof(eh));memcpy(header+sizeof(eh),ph,(size_t)eh.e_phnum*sizeof(Elf64_Phdr));if(dynamic)memcpy(header+1024,interpreter,interpreter_size);
    bool ok=fwrite(header,1,sizeof(header),fp)==sizeof(header)&&fwrite(code.v,1,code.n,fp)==code.n;
    size_t pad=data_offset-4096-code.n;unsigned char zero[4096]={0};if(ok&&pad)ok=fwrite(zero,1,pad,fp)==pad;
    if(ok)ok=fwrite(data.v,1,data.n,fp)==data.n;
    if(ok&&dynamic){size_t gap=native_import_rva-data_offset-data.n;if(gap)ok=fwrite(zero,1,gap,fp)==gap;if(ok)ok=fwrite(elf_imports.v,1,elf_imports.n,fp)==elf_imports.n;}
    if(ok&&debug_symbols)ok=fwrite(debug_tail.v,1,debug_tail.n,fp)==debug_tail.n;if(fclose(fp))ok=false;
    if(!ok){unlink(path);fatal("erro ao gravar %s",path);}if(chmod(path,0755))fatal("não foi possível marcar %s como executável: %s",path,strerror(errno));
}

#include "pe_writer.h"
#include "macho_writer.h"
#include "icon_icns.h"
static void bundle_file(const char*path,const void*contents,size_t size){protect_output(path);FILE*f=fopen(path,"wb");if(!f)fatal("não foi possível criar %s",path);bool ok=fwrite(contents,1,size,f)==size;if(fclose(f))ok=false;if(!ok)fatal("erro ao gravar %s",path);}
static void write_executable(const char *path){
    if(bundle_app){
        if(mkdir(path,0755))fatal("--app exige uma pasta de saída nova: %s",path);
        char*contents=path_join(path,"Contents"),*macos=path_join(contents,"MacOS"),*resources=path_join(contents,"Resources");
        if(mkdir(contents,0755)||mkdir(macos,0755)||mkdir(resources,0755))fatal("erro ao criar bundle macOS");
        char*exe=path_join(macos,"program"),*icon=path_join(resources,"compiled.icns"),*info=path_join(contents,"Info.plist");
        const char*plist="<?xml version=\"1.0\" encoding=\"UTF-8\"?><plist version=\"1.0\"><dict><key>CFBundleExecutable</key><string>program</string><key>CFBundleIdentifier</key><string>org.assisscript.program</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleName</key><string>AssisScript</string><key>CFBundleIconFile</key><string>compiled.icns</string></dict></plist>\n";
        write_macho(exe);bundle_file(icon,compiled_icns,sizeof(compiled_icns));bundle_file(info,plist,strlen(plist));if(debug_symbols)write_debug_map(exe);free(contents);free(macos);free(resources);free(exe);free(icon);free(info);return;
    }
    if(target_windows)write_pe(path);else if(target_macos)write_macho(path);else write_elf(path);
}
static void help(void){
    puts("AssisScript " VERSION " | compilador nativo " HOST_NAME "\n"
         "\nUso: assis <comando> [arquivo.assis] [opções]\n"
         "\n  assis new <pasta>                  cria um projeto com exemplo\n"
         "  assis build [fonte] [-o programa]  gera executável nativo diretamente\n"
         "  assis run [fonte] [--timeout n]    compila e executa\n"
         "  assis check [fonte]               valida sintaxe e tipos\n"
         "  assis lock [fonte]                verifica dependências e grava lockfile offline\n"
         "  assis fmt [fonte] [--check]        formata blocos preservando tokens e comentários\n"
         "  assis test [fonte] [--timeout n]  executa funções test_/teste_ do arquivo\n"
         "  assis doc [fonte] [-o API.md]     gera documentação da API pública\n"
         "  assis ir [fonte]                  inspeciona blocos tipados e efeitos em JSON\n"
         "      --library                    permite biblioteca sem entrada\n"
         "      --stdin                      verifica o texto recebido por stdin\n"
         "      --diagnostics=json           emite erros estruturados (UTF-16)\n"
         "      --no-opt                     desativa otimizações para comparação\n"
         "      --debug                      acusa vazamentos e preenche memória liberada\n"
         "      --symbols                    build com mapa JSON e símbolos ELF/PE/Mach-O\n"
         "      --app                        bundle macOS com ícone v1 (saída nova)\n"
         "      --safe                       perfil padrão: entrada safe e fronteiras unsafe\n"
         "      --legacy                     compatibilidade explícita com entrada legada\n"
         "  -I <pasta>                       pesquisa módulos nessa pasta\n"
         "  assis tokens [fonte]              mostra tokens e posições\n"
         "  assis doctor                      mostra informações da instalação\n"
         "  assis version                     mostra a versão\n"
         "  assis help                        mostra esta ajuda\n"
         "\nSem fonte, procura assis.assis no diretório atual.\n"
         "build: --target windows-x64, linux-x64, macos-x64, linux-arm64, macos-arm64 (experimental).\n"
         "Aliases: criar, compilar, executar, verificar.\n"
         "O compilador não chama Python, GCC, Clang, assembler ou linker.");
}
static void create_project(const char *folder){
    if(!folder||!*folder)fatal("informe uma pasta: assis new meu-projeto");
    if(mkdir(folder,0755))fatal("não foi possível criar %s: %s",folder,strerror(errno));
    size_t size=strlen(folder)+32;char *path=mem(size);snprintf(path,size,"%s/assis.assis",folder);
    FILE *f=fopen(path,"w");if(!f)fatal("não foi possível criar %s",path);
    const char *sample="import \"src.pillow\";\n\n"
        "safe fn main(): int {\n    own numeros: Array<int> = [21];\n"
        "    print(\"Hello, world!\", dobro(numeros[0]));\n    return 0;\n}\n";
    bool ok=fputs(sample,f)>=0;if(fclose(f))ok=false;if(!ok)fatal("erro ao criar projeto");
    snprintf(path,size,"%s/src",folder);if(mkdir(path,0755))fatal("não foi possível criar src");
    const char *names[]={"src.pillow","src/calculos.assis"};
    const char *contents[]={"import \"src/calculos.assis\";\n","/// Retorna o dobro de valor em aritmética modular de 64 bits.\npure fn dobro(valor: int): int { return valor * 2; }\n"};
    for(int i=0;i<2;i++){snprintf(path,size,"%s/%s",folder,names[i]);f=fopen(path,"w");if(!f)fatal("não foi possível criar %s",path);ok=fputs(contents[i],f)>=0;if(fclose(f))ok=false;if(!ok)fatal("erro ao criar %s",path);}
    printf("ASSIS: projeto criado em %s\nEntre na pasta e execute: assis run\n",folder);
}
#ifndef _WIN32
static double now_seconds(void){struct timespec ts;if(clock_gettime(CLOCK_MONOTONIC,&ts))fatal("relógio monotônico indisponível");return (double)ts.tv_sec+(double)ts.tv_nsec/1000000000.0;}
static int run_program(double timeout){
    char directory[]="/tmp/assisscript-XXXXXX";if(!mkdtemp(directory))fatal("não foi possível criar diretório temporário: %s",strerror(errno));
    char path[128];snprintf(path,sizeof(path),"%s/programa",directory);write_executable(path);fflush(NULL);
    pid_t child=fork();if(child<0){unlink(path);rmdir(directory);fatal("fork falhou: %s",strerror(errno));}
    if(!child){execl(path,path,(char*)NULL);fprintf(stderr,"assis: não foi possível executar %s: %s\n",path,strerror(errno));_exit(126);}
    int status=0;double start=now_seconds();bool timed_out=false;
    for(;;){
        pid_t result=waitpid(child,&status,timeout>0?WNOHANG:0);
        if(result==child)break;if(result<0){if(errno==EINTR)continue;unlink(path);rmdir(directory);fatal("waitpid falhou: %s",strerror(errno));}
        if(timeout>0&&now_seconds()-start>=timeout){kill(child,SIGKILL);while(waitpid(child,&status,0)<0&&errno==EINTR){}timed_out=true;break;}
        struct timespec nap={0,10000000};nanosleep(&nap,NULL);
    }
    unlink(path);rmdir(directory);
    if(timed_out){fputs("assis: o programa excedeu o tempo de execução definido.\n",stderr);return 124;}
    if(WIFEXITED(status))return WEXITSTATUS(status);
    if(WIFSIGNALED(status)){fprintf(stderr,"assis: programa encerrado pelo sinal %d.\n",WTERMSIG(status));return 128+WTERMSIG(status);}return 1;
}
#else
static int run_program(double timeout){
    wchar_t temp[32768],directory[32768],path[32768];DWORD n=GetTempPathW(32768,temp);
    if(!n||n+96>=32768)fatal("não foi possível criar diretório temporário (Windows %lu)",(unsigned long)GetLastError());
    /* Reserve the directory atomically. A temporary file followed by
     * DeleteFile/CreateDirectory races other runs and antivirus scanners. */
    bool created=false;
    for(unsigned attempt=0;attempt<128;attempt++){
        swprintf(directory,32768,L"%lsassis-%lu-%llu-%u",temp,(unsigned long)GetCurrentProcessId(),(unsigned long long)GetTickCount64(),attempt);
        if(CreateDirectoryW(directory,NULL)){created=true;break;}
        if(GetLastError()!=ERROR_ALREADY_EXISTS)fatal("não foi possível preparar diretório temporário (Windows %lu)",(unsigned long)GetLastError());
    }
    if(!created)fatal("não foi possível reservar diretório temporário exclusivo");
    if(wcslen(directory)+16>=32768)fatal("caminho temporário grande demais");
    wcscpy(path,directory);wcscat(path,L"\\programa.exe");char *utf8=utf8_path(path);write_executable(utf8);free(utf8);fflush(NULL);
    STARTUPINFOW si={0};PROCESS_INFORMATION pi={0};si.cb=sizeof(si);si.dwFlags=STARTF_USESTDHANDLES;
    si.hStdInput=GetStdHandle(STD_INPUT_HANDLE);si.hStdOutput=GetStdHandle(STD_OUTPUT_HANDLE);si.hStdError=GetStdHandle(STD_ERROR_HANDLE);
    wchar_t *command=mem((wcslen(path)+3)*sizeof(wchar_t));command[0]=L'"';wcscpy(command+1,path);wcscat(command,L"\"");
    if(!CreateProcessW(path,command,NULL,NULL,TRUE,0,NULL,NULL,&si,&pi)){
        DWORD err=GetLastError();DeleteFileW(path);RemoveDirectoryW(directory);free(command);fatal("não foi possível executar programa (Windows %lu)",(unsigned long)err);
    }
    free(command);DWORD ms=INFINITE;
    if(timeout>0){double value=timeout*1000.0;ms=value>=4294967294.0?4294967294u:(DWORD)value;if(!ms)ms=1;}
    DWORD result=WaitForSingleObject(pi.hProcess,ms),status=1;bool timed_out=result==WAIT_TIMEOUT;
    if(timed_out){TerminateProcess(pi.hProcess,124);WaitForSingleObject(pi.hProcess,INFINITE);status=124;}
    else if(result==WAIT_OBJECT_0){if(!GetExitCodeProcess(pi.hProcess,&status))status=2;}
    else {TerminateProcess(pi.hProcess,2);WaitForSingleObject(pi.hProcess,INFINITE);status=2;}
    CloseHandle(pi.hThread);CloseHandle(pi.hProcess);DeleteFileW(path);RemoveDirectoryW(directory);
    if(timed_out)fputs("assis: o programa excedeu o tempo de execução definido.\n",stderr);
    return (int)status;
}
#endif
static const char *token_name(Token *t){
    if(t->kind==T_ID)return "NOME";if(t->kind==T_INT)return "INTEIRO";if(t->kind==T_STR)return "TEXTO";if(t->kind==T_EOF)return "FIM";
    for(int i=0;words[i].name;i++)if(words[i].kind==t->kind)return words[i].name;return "OPERADOR";
}
static int compiler_main(int argc,char **argv){
    for(int i=1;i<argc;i++)if(same(argv[i],"--diagnostics=json"))json_diagnostics=true;
    if(argc<2){help();return 0;}const char *cmd=argv[1];
    if(same(cmd,"--help")||same(cmd,"help")||same(cmd,"--ajuda")){help();return 0;}
    if(same(cmd,"--version")||same(cmd,"version")){puts("AssisScript " VERSION " (nativo, " HOST_NAME ")");return 0;}
    if(same(cmd,"doctor")){
        puts("AssisScript " VERSION "\nHost: " HOST_NAME "\nBackends: ELF64 Linux x64/ARM64 / PE32+ Windows x64 / Mach-O macOS x64/ARM64 (experimental)\nRuntime: incorporado; usa APIs do sistema de destino\nDependências para compilar: nenhuma ferramenta externa\nEntrada do projeto: assis.assis");
        if(!HOST_RUN_X64)puts("Host ARM64: check/ir/build/run/test nativos disponíveis.");return 0;
    }
    if(same(cmd,"new")||same(cmd,"init")||same(cmd,"create")){if(argc!=3)fatal("use: assis new <pasta>");create_project(argv[2]);return 0;}
    if(same(cmd,"fmt"))return format_command(argc,argv);
    bool testing=same(cmd,"test"),documenting=same(cmd,"doc"),inspecting_ir=same(cmd,"ir");
    bool build=same(cmd,"build")||same(cmd,"compilar"),run=same(cmd,"run")||same(cmd,"run");
    run=run||testing;
    bool locking=same(cmd,"lock");
    bool validate=same(cmd,"check")||same(cmd,"verificar")||locking||documenting||inspecting_ir,show_tokens=same(cmd,"tokens");
    if(documenting)library_check=true;
    if(!build&&!run&&!validate&&!show_tokens)fatal("comando desconhecido: %s. Use assis help.",cmd);
    const char *input=NULL,*output=NULL;double timeout=0;int safety_option=0;
    for(int i=2;i<argc;i++){
        if(same(argv[i],"-o")||same(argv[i],"--output")){if((!build&&!documenting)||i+1>=argc)fatal("-o exige um destino em build/doc");output=argv[++i];}
        else if(same(argv[i],"--timeout")){
            if(!run||i+1>=argc)fatal("--timeout exige segundos e só pode ser usado em run");char *end=NULL;errno=0;timeout=strtod(argv[++i],&end);
            if(errno||!end||*end||!isfinite(timeout)||timeout<=0)fatal("--timeout deve ser um número positivo");
        }else if(same(argv[i],"--target")){
            if((!build&&!run)||i+1>=argc)fatal("--target exige um destino em build/run");const char *target=argv[++i];
            if(!same(target,"windows-x64")&&!same(target,"linux-x64")&&!same(target,"macos-x64")&&!same(target,"linux-arm64")&&!same(target,"macos-arm64"))fatal("destino desconhecido: %s",target);
            target_windows=same(target,"windows-x64");target_macos=same(target,"macos-x64")||same(target,"macos-arm64");target_arm64=same(target,"linux-arm64")||same(target,"macos-arm64");
        }else if(same(argv[i],"-I")){if(i+1>=argc)fatal("-I exige uma pasta");push(&include_dirs,argv[++i]);}
        else if(same(argv[i],"--diagnostics=json")){}
        else if(same(argv[i],"--no-opt")){optimize=false;}
        else if(same(argv[i],"--debug")){debug_memory=true;}
        else if(same(argv[i],"--app")){if(!build)fatal("--app exige build");bundle_app=true;}
        else if(same(argv[i],"--symbols")){if(!build)fatal("--symbols exige build");debug_symbols=true;}
        else if(same(argv[i],"--safe")){if(safety_option<0)fatal("--safe e --legacy são incompatíveis");safety_option=1;safe_entry=true;}
        else if(same(argv[i],"--legacy")){if(safety_option>0)fatal("--safe e --legacy são incompatíveis");safety_option=-1;safe_entry=false;}
        else if(same(argv[i],"--library")){if(!validate)fatal("--library só pode ser usado em check");library_check=true;}
        else if(same(argv[i],"--stdin")){if(!validate)fatal("--stdin só pode ser usado em check");stdin_source=true;}
        else if(same(argv[i],"--overlay")){
            if(!validate||i+2>=argc)fatal("--overlay exige caminho lógico e arquivo temporário em check");
            SourceOverlay *overlay=mem(sizeof(*overlay));overlay->path=absolute_path(argv[++i]);overlay->snapshot=argv[++i];push(&source_overlays,overlay);
        }
        else if(same(argv[i],"--help")||same(argv[i],"-h")){help();return 0;}
        else if(argv[i][0]=='-')fatal("opção desconhecida: %s",argv[i]);
        else if(!input)input=argv[i];else fatal("informe apenas um arquivo fonte");
    }
    if(run){
        if(target_arm64==!!HOST_RUN_X64)fatal("run/test exige a arquitetura nativa do host; use build para compilar para outra arquitetura");
#ifdef _WIN32
        if(!target_windows)fatal("run no Windows exige destino windows-x64; use build para outro sistema");
#elif defined(__APPLE__)
        if(!target_macos)fatal("run no macOS exige destino macOS nativo; use build para outro sistema");
#else
        if(target_windows||target_macos)fatal("run no Linux exige destino Linux nativo; use build para outro sistema");
#endif
    }
    if(bundle_app&&!target_macos)fatal("--app exige destino macOS");
    if(!input)input="assis.assis";module_search_paths();initialize_packages(input);Vec expanded={0};load_module(input,NULL,stdin_source,&expanded,0);tokens=expanded;
    if(!locking)package_lock(false);
    if(show_tokens){for(int i=0;i<tokens.n;i++){Token *t=tokens.v[i];printf("%4d:%-3d %-18s %s\n",t->line,t->col,token_name(t),t->text);}return 0;}
    scan_platforms();scan_namespaces();parse();if(testing)prepare_tests();bind_namespaces();check();check_ownership();check_safety();prepare_ir();prepare_ranges();prepare_registers();if(inspecting_ir){prepare_backend_ir();print_ir();return 0;}if(locking){package_lock(true);return 0;}if(documenting){document_api(output);return 0;}if(validate){if(json_diagnostics)puts("{\"ok\":true}");else printf("ASSIS: %s passou na análise de sintaxe e tipos.\n",input);return 0;}
    if(optimize||target_arm64){prepare_backend_ir();if(optimize)discard_frontend_ast();}generate();if(run)return run_program(timeout);
    if(!output){
        size_t len=strlen(input);char *name=copy(input,len);char *slash=strrchr(name,'/'),*dot=strrchr(name,'.');
#ifdef _WIN32
        char *backslash=strrchr(name,'\\');if(backslash&&(!slash||backslash>slash))slash=backslash;
#endif
        if(dot&&(!slash||dot>slash)) *dot=0;
        if(!*name||(!target_windows&&same(name,input))){free(name);name=mem(len+5);snprintf(name,len+5,"%s.out",input);}
        output=name;
    }
    protect_output(output);
    if(target_windows){
        size_t len=strlen(output);bool exe=len>=4&&output[len-4]=='.'&&tolower((unsigned char)output[len-3])=='e'&&tolower((unsigned char)output[len-2])=='x'&&tolower((unsigned char)output[len-1])=='e';
        if(!exe){char *name=mem(len+5);snprintf(name,len+5,"%s.exe",output);output=name;}
    }
    protect_output(output);
    write_executable(output);if(debug_symbols&&!bundle_app)write_debug_map(output);printf("ASSIS: executável nativo gerado em %s\n",output);return 0;
}
#ifdef _WIN32
int wmain(int argc,wchar_t **wide_argv){
    SetConsoleOutputCP(CP_UTF8);_setmode(_fileno(stdout),_O_BINARY);_setmode(_fileno(stderr),_O_BINARY);
    char **argv=mem(((size_t)argc+1)*sizeof(char*));for(int i=0;i<argc;i++)argv[i]=utf8_path(wide_argv[i]);
    return compiler_main(argc,argv);
}
#else
int main(int argc,char **argv){return compiler_main(argc,argv);}
#endif

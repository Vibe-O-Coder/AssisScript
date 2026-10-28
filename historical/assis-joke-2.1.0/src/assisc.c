/* AssisScript 2.1. Compilador nativo C11 -> ELF64 / PE32+ x86_64.
 * O binário distribuído não invoca Python, um compilador C ou um assembler.
 */
#define _POSIX_C_SOURCE 200809L
#if (!defined(__linux__) && !defined(_WIN32)) || !defined(__x86_64__)
#error "Esta versão do compilador é destinada a Linux/Windows x86_64."
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
#define HOST_NAME "Linux x86_64"
static bool target_windows=false;
#endif

#define VERSION "2.1.0"
#define ENTRY "assis_assis"
#define CTOR "assis_fodase"
#define MAX_SOURCE (16 * 1024 * 1024)
#define MAX_NEST 512

typedef struct { void **v; int n, cap; } Vec;
static const char *filename;
static void fatal(const char *fmt, ...) {
    va_list ap; va_start(ap,fmt); fputs("FODASE: ",stderr);
    vfprintf(stderr,fmt,ap); va_end(ap); fputc('\n',stderr); exit(2);
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
    if(same_file(filename,path))fatal("o destino não pode sobrescrever o código AssisScript");
#ifdef _WIN32
    wchar_t module[32768];DWORD size=GetModuleFileNameW(NULL,module,32768);
    if(size&&size<32768){char *self=utf8_path(module);bool match=same_file(self,path);free(self);if(match)fatal("o destino não pode sobrescrever o próprio compilador");}
#else
    if(same_file("/proc/self/exe",path))fatal("o destino não pode sobrescrever o próprio compilador");
#endif
}

enum {
    T_EOF=256,T_ID,T_INT,T_STR,T_CLASS,T_EXTENDS,T_FN,T_LET,T_I64,T_U8,T_BOOL,T_TEXT,T_VOID,
    T_IF,T_ELSE,T_WHILE,T_RETURN,T_PRINT,T_NEW,T_FREE,T_SELF,T_TRUE,T_FALSE,T_NULL,
    T_BREAK,T_CONTINUE,T_ALLOC,T_LEN,T_EQ,T_NE,T_LE,T_GE,T_AND,T_OR,T_SHL,T_SHR,
    T_ADDSET,T_SUBSET,T_MULSET,T_DIVSET,T_MODSET,T_ANDSET,T_ORSET,T_XORSET,T_SHLSET,T_SHRSET
};
typedef struct { const char *name; int kind; } Word;
static const Word words[]={
    {"ASSIS",T_CLASS},{"ASSIS_FODASE",T_EXTENDS},{"assis",T_FN},{"Assis",T_LET},
    {"AssIs",T_I64},{"AssiS",T_U8},{"FodAsE",T_BOOL},{"FoDaSe",T_TEXT},{"FODase",T_VOID},
    {"assIS",T_IF},{"fodASE",T_ELSE},{"ASSis",T_WHILE},{"Fodase",T_RETURN},
    {"FODASE",T_PRINT},{"fodase",T_NEW},{"foDASE",T_FREE},{"aSSIS",T_SELF},
    {"aSsIs",T_TRUE},{"fOdAsE",T_FALSE},{"fOdase",T_NULL},{"FODasE",T_BREAK},
    {"FodASE",T_CONTINUE},{"ASSIS_fodase",T_ALLOC},{"FODASE_fodase",T_LEN},{NULL,0}
};
typedef struct Token { int kind,line,col; char *text,*str; size_t len; uint64_t number; const char *at; } Token;
static Vec tokens; static char *source;
static int cursor=0, parse_depth=0;

static _Noreturn void error(Token *t,const char *fmt,...) {
    fprintf(stderr,"%s:%d:%d: A001: ",filename,t?t->line:1,t?t->col:1);
    va_list ap;va_start(ap,fmt);vfprintf(stderr,fmt,ap);va_end(ap);fputc('\n',stderr);
    const char *a=t&&t->at?t->at:source; const char *start=a;
    while(start>source&&start[-1]!='\n')start--;
    const char *end=a;while(*end&&*end!='\n'&&*end!='\r')end++;
    fputs("  ",stderr);fwrite(start,1,(size_t)(end-start),stderr);fputs("\n  ",stderr);
    for(const char *p=start;p<a;p++) fputc(*p=='\t'?'\t':' ',stderr);
    fputs("^\n",stderr);exit(1);
}
static bool ascii_alpha(unsigned char c) { return (c>='a'&&c<='z')||(c>='A'&&c<='Z'); }
static bool ascii_digit(unsigned char c) { return c>='0'&&c<='9'; }
static bool name_ok(const char *s) {
    bool word=false;
    while(*s) {
        if(*s=='_') { if(!word)return false;s++;if(!*s||*s=='_')return false; }
        const char *w=(tolower((unsigned char)*s)=='a')?"assis":"fodase";
        for(int i=0;w[i];i++) { if(!s[i]||tolower((unsigned char)s[i])!=w[i])return false; }
        s+=strlen(w);word=true;
    }
    return word;
}
static int digit(unsigned char c) {
    if(c>='0'&&c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10;
    if(c>='A'&&c<='F')return c-'A'+10; return -1;
}
static void lex(void) {
    char *p=source;int line=1,col=1;
    while(*p) {
        if(isspace((unsigned char)*p)){if(*p=='\n'){line++;col=1;}else col++;p++;continue;}
        if(p[0]=='/'&&p[1]=='/'){while(*p&&*p!='\n'){p++;col++;}continue;}
        Token *t=mem(sizeof(*t));t->line=line;t->col=col;t->at=p;
        if(p[0]=='/'&&p[1]=='*') {
            int depth=1;p+=2;col+=2;
            while(*p&&depth) {
                if(p[0]=='/'&&p[1]=='*'){depth++;p+=2;col+=2;}
                else if(p[0]=='*'&&p[1]=='/'){depth--;p+=2;col+=2;}
                else {if(*p=='\n'){line++;col=1;}else col++;p++;}
            }
            if(depth)error(t,"comentário de bloco sem fechamento */");free(t);continue;
        }
        if(ascii_alpha((unsigned char)*p)||*p=='_') {
            char *begin=p;while(ascii_alpha((unsigned char)*p)||ascii_digit((unsigned char)*p)||*p=='_'){p++;col++;}
            t->text=copy(begin,(size_t)(p-begin));t->kind=T_ID;
            for(int i=0;words[i].name;i++)if(same(words[i].name,t->text)){t->kind=words[i].kind;break;}
            if(t->kind==T_ID&&!name_ok(t->text))error(t,"'%s' não é uma variação de Assis/Fodase",t->text);
        } else if(ascii_digit((unsigned char)*p)) {
            char *begin=p;while(ascii_alpha((unsigned char)*p)||ascii_digit((unsigned char)*p)||*p=='_'){p++;col++;}
            t->text=copy(begin,(size_t)(p-begin));t->kind=T_INT;
            const char *s=t->text;int base=10;
            if(s[0]=='0'&&(s[1]=='x'||s[1]=='X')){base=16;s+=2;}
            else if(s[0]=='0'&&(s[1]=='b'||s[1]=='B')){base=2;s+=2;}
            bool got=false,sep=false;
            for(;*s;s++) {
                if(*s=='_'){if(!got||sep)error(t,"literal inteiro inválido");sep=true;continue;}
                int d=digit((unsigned char)*s);if(d<0||d>=base)error(t,"literal inteiro inválido");
                if(t->number>(UINT64_MAX-(uint64_t)d)/(uint64_t)base)error(t,"literal excede 64 bits");
                t->number=t->number*(uint64_t)base+(uint64_t)d;got=true;sep=false;
            }
            if(!got||sep)error(t,"literal inteiro inválido");
        } else if(*p=='"') {
            char *begin=p++;col++;size_t cap=64,n=0;char *str=mem(cap);
            while(*p&&*p!='"') {
                if(*p=='\n'||*p=='\r')error(t,"texto sem fechamento; use \\n");
                unsigned char c=(unsigned char)*p++;col++;
                unsigned char bytes[4];int count=1;bytes[0]=c;
                if(c=='\\') {
                    if(!*p)error(t,"escape incompleto");c=(unsigned char)*p++;col++;
                    if(c=='n')bytes[0]='\n';else if(c=='r')bytes[0]='\r';else if(c=='t')bytes[0]='\t';
                    else if(c=='0')bytes[0]=0;else if(c=='"'||c=='\\')bytes[0]=c;
                    else if(c=='x'||c=='u') {
                        int len=c=='x'?2:4;unsigned cp=0;
                        for(int i=0;i<len;i++){if(!*p||digit((unsigned char)*p)<0)error(t,"escape hexadecimal inválido");cp=cp*16+(unsigned)digit((unsigned char)*p++);col++;}
                        if(cp>=0xd800&&cp<=0xdfff)error(t,"surrogate Unicode isolado");
                        if(cp<0x80)bytes[0]=(unsigned char)cp;
                        else if(cp<0x800){count=2;bytes[0]=(unsigned char)(0xc0|(cp>>6));bytes[1]=(unsigned char)(0x80|(cp&63));}
                        else {count=3;bytes[0]=(unsigned char)(0xe0|(cp>>12));bytes[1]=(unsigned char)(0x80|((cp>>6)&63));bytes[2]=(unsigned char)(0x80|(cp&63));}
                    } else error(t,"escape desconhecido");
                }
                if(n+(size_t)count+1>cap){cap*=2;str=realloc(str,cap);if(!str)fatal("memória insuficiente");}
                for(int i=0;i<count;i++)str[n++]=(char)bytes[i];
            }
            if(*p!='"')error(t,"texto sem aspas de fechamento");p++;col++;str[n]=0;
            t->kind=T_STR;t->str=str;t->len=n;t->text=copy(begin,(size_t)(p-begin));
        } else {
            static const Word ops[]={{"<<=",T_SHLSET},{">>=",T_SHRSET},{"==",T_EQ},{"!=",T_NE},{"<=",T_LE},{">=",T_GE},{"&&",T_AND},{"||",T_OR},{"<<",T_SHL},{">>",T_SHR},{"+=",T_ADDSET},{"-=",T_SUBSET},{"*=",T_MULSET},{"/=",T_DIVSET},{"%=",T_MODSET},{"&=",T_ANDSET},{"|=",T_ORSET},{"^=",T_XORSET},{NULL,0}};
            int length=1;t->kind=(unsigned char)*p;
            for(int i=0;ops[i].name;i++){size_t len=strlen(ops[i].name);if(!strncmp(p,ops[i].name,len)){t->kind=ops[i].kind;length=(int)len;break;}}
            if(length==1&&!strchr("{}()[];:,.+-*/%&|^~!<>=",*p))error(t,"caractere inesperado: 0x%02x",(unsigned char)*p);
            t->text=copy(p,(size_t)length);p+=length;col+=length;
        }
        push(&tokens,t);
    }
    Token *t=mem(sizeof(*t));t->kind=T_EOF;t->text="fim do arquivo";t->line=line;t->col=col;t->at=p;push(&tokens,t);
}

typedef enum { TY_I64,TY_U8,TY_BOOL,TY_STR,TY_VOID,TY_OBJ,TY_NULL } TypeKind;
typedef struct { TypeKind kind; int depth; char *name; } Type;
typedef struct Class Class;typedef struct Function Function;typedef struct Var Var;typedef struct Node Node;
struct Var { Token *t;Type ty;int slot; };
typedef struct { Token *t;Type ty;int slot; } Field;
enum { N_INT,N_STR,N_BOOL,N_NULL,N_NAME,N_SELF,N_UNARY,N_BINARY,N_CALL,N_MEMBER,N_INDEX,N_NEW,N_BUILTIN,N_BLOCK,N_LET,N_ASSIGN,N_IF,N_WHILE,N_RETURN,N_PRINT,N_FREE,N_BREAK,N_CONTINUE,N_EXPR };
struct Node { int kind,op;Token *t;Node *a,*b,*c;Vec items;Type ty,decl;Var *var;Function *fn;Class *cls;int slot;bool lvalue; };
struct Function { Token *t;Vec params,vars;Type result;Node *body;Class *owner;int label; };
struct Class { Token *t;Token *base_name;Class *base;Vec own_fields,own_methods,fields,methods;int state,label; };
static Vec classes,functions,all_functions;
static const Type type_i64={TY_I64,0,NULL},type_u8={TY_U8,0,NULL},type_bool={TY_BOOL,0,NULL},type_str={TY_STR,0,NULL},type_void={TY_VOID,0,NULL},type_null={TY_NULL,0,NULL};
static Type pointer(Type t){t.depth++;return t;}
static Type pointed(Type t){t.depth--;return t;}
static bool equal_type(Type a,Type b){return a.kind==b.kind&&a.depth==b.depth&&(a.kind!=TY_OBJ||same(a.name,b.name));}
static const char *type_name(Type t) {
    static char buffers[4][256];static unsigned turn;char *out=buffers[(turn++)%4];
    const char *base=t.kind==TY_OBJ?t.name:t.kind==TY_I64?"AssIs":t.kind==TY_U8?"AssiS":t.kind==TY_BOOL?"FodAsE":t.kind==TY_STR?"FoDaSe":t.kind==TY_VOID?"FODase":"nulo";
    int depth=t.depth>64?64:t.depth;memset(out,'*',(size_t)depth);snprintf(out+depth,256-(size_t)depth,"%s",base);return out;
}
static Token *peek(void){return tokens.v[cursor];}
static Token *take(void){Token *t=peek();if(t->kind!=T_EOF)cursor++;return t;}
static bool accept(int kind){if(peek()->kind==kind){take();return true;}return false;}
static Token *expect(int kind){Token *t=peek();if(t->kind!=kind)error(t,"esperado %s; encontrado '%s'",kind==T_ID?"nome Assis/Fodase":kind<128?(char[2]){(char)kind,0}:"outro token",t->text);return take();}
static Node *node(int kind,Token *t){Node *n=mem(sizeof(*n));n->kind=kind;n->t=t;return n;}
static Type parse_type(void){
    int depth=0;while(accept('*')){if(++depth>64)error(peek(),"ponteiro aninhado demais");}
    Token *t=take();Type ty;
    if(t->kind==T_I64)ty=type_i64;else if(t->kind==T_U8)ty=type_u8;else if(t->kind==T_BOOL)ty=type_bool;
    else if(t->kind==T_TEXT)ty=type_str;else if(t->kind==T_VOID)ty=type_void;
    else if(t->kind==T_ID)ty=(Type){TY_OBJ,0,t->text};else {error(t,"esperado um tipo AssisScript");}
    ty.depth=depth;return ty;
}
static Node *expression(int minimum);static Node *statement(void);static Node *block(void);
static void args(Vec *out){expect('(');if(peek()->kind!=')'){do{push(out,expression(1));}while(accept(','));}expect(')');}
static int precedence(int k){switch(k){case T_OR:return 1;case T_AND:return 2;case '|':return 3;case '^':return 4;case '&':return 5;case T_EQ:case T_NE:return 6;case '<':case '>':case T_LE:case T_GE:return 7;case T_SHL:case T_SHR:return 8;case '+':case '-':return 9;case '*':case '/':case '%':return 10;default:return 0;}}
static Node *prefix(void){
    if(++parse_depth>MAX_NEST)error(peek(),"expressão aninhada demais");
    Token *t=take();Node *n=NULL;
    switch(t->kind){
    case '-':case '+':case '!':case '~':case '*':case '&':n=node(N_UNARY,t);n->op=t->kind;n->a=prefix();break;
    case T_INT:n=node(N_INT,t);break;case T_STR:n=node(N_STR,t);break;
    case T_TRUE:case T_FALSE:n=node(N_BOOL,t);break;case T_NULL:n=node(N_NULL,t);break;
    case T_SELF:n=node(N_SELF,t);break;case T_ID:n=node(N_NAME,t);break;
    case T_NEW:n=node(N_NEW,expect(T_ID));args(&n->items);break;
    case T_ALLOC:case T_LEN:case T_I64:case T_U8:case T_BOOL:n=node(N_BUILTIN,t);n->op=t->kind;args(&n->items);break;
    case '(':n=expression(1);expect(')');break;
    default:error(t,"esperada uma expressão; encontrado '%s'",t->text);
    }
    for(;;){
        if(peek()->kind=='('){Node *c=node(N_CALL,n->t);c->a=n;args(&c->items);n=c;}
        else if(accept('.')){Node *m=node(N_MEMBER,expect(T_ID));m->a=n;n=m;}
        else if(accept('[')){Node *i=node(N_INDEX,n->t);i->a=n;i->b=expression(1);expect(']');n=i;}
        else break;
    }
    parse_depth--;return n;
}
static Node *expression(int minimum){
    Node *left=prefix();
    while(precedence(peek()->kind)>=minimum){Token *t=take();Node *n=node(N_BINARY,t);n->op=t->kind;n->a=left;n->b=expression(precedence(t->kind)+1);left=n;}
    return left;
}
static bool assignment(int k){return k=='='||(k>=T_ADDSET&&k<=T_SHRSET);}
static Node *block(void){
    if(++parse_depth>MAX_NEST)error(peek(),"bloco aninhado demais");
    Node *n=node(N_BLOCK,expect('{'));while(peek()->kind!='}'&&peek()->kind!=T_EOF)push(&n->items,statement());expect('}');parse_depth--;return n;
}
static Node *statement_inner(void){
    Token *t=peek();Node *n;
    if(t->kind=='{')return block();
    if(accept(T_LET)){Token *name=expect(T_ID);n=node(N_LET,name);expect(':');n->decl=parse_type();expect('=');n->a=expression(1);expect(';');return n;}
    if(accept(T_IF)){n=node(N_IF,t);expect('(');n->a=expression(1);expect(')');n->b=block();if(accept(T_ELSE))n->c=peek()->kind==T_IF?statement():block();return n;}
    if(accept(T_WHILE)){n=node(N_WHILE,t);expect('(');n->a=expression(1);expect(')');n->b=block();return n;}
    if(accept(T_RETURN)){n=node(N_RETURN,t);if(peek()->kind!=';')n->a=expression(1);expect(';');return n;}
    if(accept(T_PRINT)){n=node(N_PRINT,t);args(&n->items);expect(';');return n;}
    if(accept(T_FREE)){n=node(N_FREE,t);Vec a={0};args(&a);if(a.n!=1)error(t,"foDASE recebe exatamente um argumento");n->a=a.v[0];free(a.v);expect(';');return n;}
    if(accept(T_BREAK)||accept(T_CONTINUE)){n=node(t->kind==T_BREAK?N_BREAK:N_CONTINUE,t);expect(';');return n;}
    Node *left=expression(1);
    if(assignment(peek()->kind)){t=take();n=node(N_ASSIGN,t);n->op=t->kind;n->a=left;n->b=expression(1);}
    else{n=node(N_EXPR,t);n->a=left;}expect(';');return n;
}
static Node *statement(void){
    if(++parse_depth>MAX_NEST)error(peek(),"instrução aninhada demais");
    Node *n=statement_inner();parse_depth--;return n;
}
static Function *parse_function(Class *owner){
    Function *f=mem(sizeof(*f));f->t=expect(T_ID);f->owner=owner;expect('(');
    if(peek()->kind!=')'){do{Var *v=mem(sizeof(*v));v->t=expect(T_ID);expect(':');v->ty=parse_type();push(&f->params,v);}while(accept(','));}
    expect(')');expect(':');f->result=parse_type();f->body=block();push(&all_functions,f);return f;
}
static void parse(void){
    while(peek()->kind!=T_EOF){
        if(accept(T_CLASS)){
            Class *c=mem(sizeof(*c));c->t=expect(T_ID);if(accept(T_EXTENDS))c->base_name=expect(T_ID);expect('{');
            while(peek()->kind!='}'&&peek()->kind!=T_EOF){
                if(accept(T_LET)){Field *f=mem(sizeof(*f));f->t=expect(T_ID);expect(':');f->ty=parse_type();expect(';');push(&c->own_fields,f);}
                else if(accept(T_FN))push(&c->own_methods,parse_function(c));
                else error(peek(),"classe aceita campos Assis e métodos assis");
            }
            expect('}');push(&classes,c);
        }else if(accept(T_FN))push(&functions,parse_function(NULL));
        else error(peek(),"use ASSIS para uma classe ou assis para uma função");
    }
}

static Class *find_class(const char *name){for(int i=0;i<classes.n;i++){Class *c=classes.v[i];if(same(c->t->text,name))return c;}return NULL;}
static Function *find_fn(const char *name){for(int i=0;i<functions.n;i++){Function *f=functions.v[i];if(same(f->t->text,name))return f;}return NULL;}
static Field *find_field(Class *c,const char *name){for(int i=0;i<c->fields.n;i++){Field *f=c->fields.v[i];if(same(f->t->text,name))return f;}return NULL;}
static Function *find_method(Class *c,const char *name,int *slot){for(int i=0;i<c->methods.n;i++){Function *f=c->methods.v[i];if(same(f->t->text,name)){if(slot)*slot=i;return f;}}return NULL;}
static bool object(Type t){return t.depth==0&&t.kind==TY_OBJ;}
static bool pointer_like(Type t){return t.depth>0||object(t);}
static bool numeric(Type t){return !t.depth&&(t.kind==TY_I64||t.kind==TY_U8);}
static bool isvoid(Type t){return equal_type(t,type_void);}
static bool assignable(Type target,Type value){
    if(equal_type(target,value))return true;
    if(equal_type(target,type_i64)&&equal_type(value,type_u8))return true;
    if(equal_type(value,type_null))return pointer_like(target);
    if(object(target)&&object(value)){
        Class *c=find_class(value.name);for(c=c?c->base:NULL;c;c=c->base)if(same(c->t->text,target.name))return true;
    }
    return false;
}
static void require_assign(Type target,Type value,Token *t){if(!assignable(target,value))error(t,"não é possível usar %s como %s",type_name(value),type_name(target));}
static void valid_type(Type t,Token *where,bool result){
    if(t.kind==TY_OBJ&&!find_class(t.name))error(where,"tipo desconhecido: %s",type_name(t));
    if(t.kind==TY_VOID&&(t.depth||!result))error(where,"FODase só pode ser retorno de função/método");
}
static void signature(Function *f){
    valid_type(f->result,f->t,true);
    for(int i=0;i<f->params.n;i++){Var *v=f->params.v[i];valid_type(v->ty,v->t,false);for(int j=0;j<i;j++){Var *old=f->params.v[j];if(same(old->t->text,v->t->text))error(v->t,"parâmetro declarado duas vezes");}}
}
static int layout_depth;
static void layout(Class *c){
    if(c->state==2)return;if(c->state==1)error(c->t,"ciclo de herança detectado");c->state=1;
    if(++layout_depth>MAX_NEST)error(c->t,"hierarquia de classes aninhada demais");
    if(c->base_name){
        c->base=find_class(c->base_name->text);if(!c->base)error(c->base_name,"classe base desconhecida");layout(c->base);
        for(int i=0;i<c->base->fields.n;i++)push(&c->fields,c->base->fields.v[i]);
        for(int i=0;i<c->base->methods.n;i++)push(&c->methods,c->base->methods.v[i]);
    }
    for(int i=0;i<c->own_fields.n;i++){
        Field *f=c->own_fields.v[i];valid_type(f->ty,f->t,false);
        if(find_field(c,f->t->text)||find_method(c,f->t->text,NULL))error(f->t,"campo duplicado ou em conflito com membro herdado");
        f->slot=c->fields.n;push(&c->fields,f);
    }
    for(int i=0;i<c->own_methods.n;i++){
        Function *f=c->own_methods.v[i];signature(f);
        if(find_field(c,f->t->text))error(f->t,"método em conflito com campo");
        for(int j=0;j<i;j++){Function *old=c->own_methods.v[j];if(same(old->t->text,f->t->text))error(f->t,"método declarado duas vezes");}
        if(same(f->t->text,CTOR)&&!isvoid(f->result))error(f->t,"inicializador assis_fodase deve retornar FODase");
        int slot=-1;Function *old=find_method(c,f->t->text,&slot);
        if(old){
            if(old->params.n!=f->params.n||!equal_type(old->result,f->result))error(f->t,"sobrescrita deve manter a assinatura");
            for(int j=0;j<f->params.n;j++)if(!equal_type(((Var*)f->params.v[j])->ty,((Var*)old->params.v[j])->ty))error(f->t,"sobrescrita deve manter os tipos dos parâmetros");
            c->methods.v[slot]=f;
        }else push(&c->methods,f);
    }
    c->state=2;layout_depth--;
}
static Vec bindings;static Function *checking;static int scope_start,loop_depth,check_depth;
static Var *lookup(const char *name){for(int i=bindings.n-1;i>=0;i--){Var *v=bindings.v[i];if(same(v->t->text,name))return v;}return NULL;}
static void declare(Var *v){
    for(int i=scope_start;i<bindings.n;i++){Var *old=bindings.v[i];if(same(old->t->text,v->t->text))error(v->t,"variável já declarada neste escopo");}
    v->slot=checking->vars.n+(checking->owner?1:0);push(&checking->vars,v);push(&bindings,v);
}
static Type check_expr(Node *n);
static void check_args(Vec *args,Function *f,Token *t){
    if(args->n!=f->params.n)error(t,"esperados %d argumentos; recebidos %d",f->params.n,args->n);
    for(int i=0;i<args->n;i++){Node *a=args->v[i];Var *p=f->params.v[i];require_assign(p->ty,check_expr(a),a->t);}
}
static int compound_op(int k){switch(k){case T_ADDSET:return '+';case T_SUBSET:return '-';case T_MULSET:return '*';case T_DIVSET:return '/';case T_MODSET:return '%';case T_ANDSET:return '&';case T_ORSET:return '|';case T_XORSET:return '^';case T_SHLSET:return T_SHL;case T_SHRSET:return T_SHR;default:return k;}}
static Type binary_type(Type a,Type b,int op,Token *t){
    if(op==T_AND||op==T_OR){if(equal_type(a,type_bool)&&equal_type(b,type_bool))return type_bool;}
    else if(op==T_EQ||op==T_NE){if(!isvoid(a)&&!isvoid(b)&&(assignable(a,b)||assignable(b,a)))return type_bool;}
    else if(op=='<'||op=='>'||op==T_LE||op==T_GE){if(numeric(a)&&numeric(b))return type_bool;}
    else if((op=='+'||op=='-')&&a.depth&&numeric(b))return a;
    else if(numeric(a)&&numeric(b))return type_i64;
    error(t,"operação incompatível entre %s e %s",type_name(a),type_name(b));
}
static Type check_expr(Node *n){
    if(++check_depth>MAX_NEST)error(n->t,"expressão aninhada demais");
    Type a,b,ty=type_void;
    switch(n->kind){
    case N_INT:ty=type_i64;break;case N_STR:ty=type_str;break;case N_BOOL:ty=type_bool;break;case N_NULL:ty=type_null;break;
    case N_NAME:n->var=lookup(n->t->text);if(!n->var)error(n->t,"variável não declarada: %s",n->t->text);ty=n->var->ty;n->lvalue=true;break;
    case N_SELF:if(!checking->owner)error(n->t,"aSSIS só existe dentro de métodos");ty=(Type){TY_OBJ,0,checking->owner->t->text};break;
    case N_MEMBER:{
        a=check_expr(n->a);if(!object(a))error(n->t,"acesso com ponto exige um objeto");
        Field *f=find_field(find_class(a.name),n->t->text);if(!f)error(n->t,"campo inexistente: %s",n->t->text);
        n->slot=f->slot;ty=f->ty;n->lvalue=true;break;
    }
    case N_CALL:{
        Function *f=NULL;
        if(n->a->kind==N_NAME){
            if(lookup(n->a->t->text))error(n->t,"variável não é uma função chamável");
            f=find_fn(n->a->t->text);if(!f)error(n->t,"função desconhecida: %s",n->a->t->text);
        }else if(n->a->kind==N_MEMBER){
            a=check_expr(n->a->a);if(!object(a))error(n->t,"chamada de método exige um objeto");
            f=find_method(find_class(a.name),n->a->t->text,&n->slot);if(!f)error(n->t,"método inexistente: %s",n->a->t->text);
        }else error(n->t,"somente funções e métodos são chamáveis");
        n->fn=f;check_args(&n->items,f,n->t);ty=f->result;break;
    }
    case N_NEW:{
        n->cls=find_class(n->t->text);if(!n->cls)error(n->t,"classe inexistente para fodase");
        Function *f=find_method(n->cls,CTOR,&n->slot);n->fn=f;
        if(f)check_args(&n->items,f,n->t);else if(n->items.n)error(n->t,"classe não declara inicializador assis_fodase");
        ty=(Type){TY_OBJ,0,n->cls->t->text};break;
    }
    case N_INDEX:
        a=check_expr(n->a);b=check_expr(n->b);if(!numeric(b))error(n->t,"índice deve ser inteiro");
        if(a.depth){ty=pointed(a);n->lvalue=true;}else if(equal_type(a,type_str))ty=type_u8;else error(n->t,"índice exige texto ou ponteiro");break;
    case N_BUILTIN:
        if(n->items.n!=1)error(n->t,"%s recebe exatamente um argumento",n->t->text);
        a=check_expr(n->items.v[0]);
        if(n->op==T_ALLOC){if(!numeric(a))error(n->t,"ASSIS_fodase recebe uma quantidade inteira de bytes");ty=pointer(type_u8);}
        else if(n->op==T_LEN){if(!equal_type(a,type_str))error(n->t,"FODASE_fodase recebe um texto");ty=type_i64;}
        else{if(!numeric(a)&&!equal_type(a,type_bool))error(n->t,"conversão aceita apenas inteiros e booleanos");ty=n->op==T_I64?type_i64:n->op==T_U8?type_u8:type_bool;}break;
    case N_UNARY:
        a=check_expr(n->a);
        if(n->op=='+'||n->op=='-'||n->op=='~'){if(!numeric(a))error(n->t,"operador aritmético exige inteiro");ty=type_i64;}
        else if(n->op=='!'){if(!equal_type(a,type_bool))error(n->t,"! exige FodAsE");ty=type_bool;}
        else if(n->op=='&'){if(!n->a->lvalue)error(n->t,"& exige uma posição gravável");ty=pointer(a);}
        else{if(!a.depth)error(n->t,"* exige um ponteiro");ty=pointed(a);n->lvalue=true;}break;
    case N_BINARY:a=check_expr(n->a);b=check_expr(n->b);ty=binary_type(a,b,n->op,n->t);break;
    default:fatal("nó de expressão inválido");
    }
    n->ty=ty;check_depth--;return ty;
}
enum { FLOW_NORMAL=1,FLOW_RETURN=2,FLOW_BREAK=4,FLOW_CONTINUE=8 };
static int check_statement(Node *n,bool scoped){
    if(++check_depth>MAX_NEST)error(n->t,"bloco aninhado demais");
    int flow=FLOW_NORMAL;
    switch(n->kind){
    case N_BLOCK:{
        int old=bindings.n,previous=scope_start;if(scoped)scope_start=old;
        for(int i=0;i<n->items.n;i++){int f=check_statement(n->items.v[i],true);if(flow&FLOW_NORMAL)flow=(flow&~FLOW_NORMAL)|f;}
        if(scoped){bindings.n=old;scope_start=previous;}break;
    }
    case N_LET:{
        valid_type(n->decl,n->t,false);Type value=check_expr(n->a);require_assign(n->decl,value,n->t);
        Var *v=mem(sizeof(*v));v->t=n->t;v->ty=n->decl;declare(v);n->var=v;break;
    }
    case N_ASSIGN:{
        Type left=check_expr(n->a);if(!n->a->lvalue)error(n->t,"lado esquerdo não é uma posição gravável");
        Type right=check_expr(n->b);
        if(n->op=='=')require_assign(left,right,n->t);
        else{Type result=binary_type(left,right,compound_op(n->op),n->t);if(!equal_type(left,type_u8)||!equal_type(result,type_i64))require_assign(left,result,n->t);}break;
    }
    case N_IF:
        if(!equal_type(check_expr(n->a),type_bool))error(n->t,"condição deve ser FodAsE");
        flow=check_statement(n->b,true)|(n->c?check_statement(n->c,true):FLOW_NORMAL);break;
    case N_WHILE:{
        if(!equal_type(check_expr(n->a),type_bool))error(n->t,"condição deve ser FodAsE");
        loop_depth++;int body=check_statement(n->b,true);loop_depth--;
        flow=body&FLOW_RETURN;
        if(n->a->kind!=N_BOOL||n->a->t->kind!=T_TRUE||(body&FLOW_BREAK))flow|=FLOW_NORMAL;break;
    }
    case N_RETURN:
        if(isvoid(checking->result)&&n->a)error(n->t,"função FODase usa Fodase; sem expressão de retorno");
        require_assign(checking->result,n->a?check_expr(n->a):type_void,n->t);flow=FLOW_RETURN;break;
    case N_PRINT:
        for(int i=0;i<n->items.n;i++){Node *a=n->items.v[i];if(isvoid(check_expr(a)))error(a->t,"FODASE não imprime expressão sem valor");}break;
    case N_FREE:{Type t=check_expr(n->a);if(!pointer_like(t)&&!equal_type(t,type_null))error(n->t,"foDASE libera apenas objetos e ponteiros");break;}
    case N_BREAK:case N_CONTINUE:if(!loop_depth)error(n->t,"FODasE/FodASE só pode ser usado dentro de ASSis");flow=n->kind==N_BREAK?FLOW_BREAK:FLOW_CONTINUE;break;
    case N_EXPR:(void)check_expr(n->a);break;
    default:fatal("nó de instrução inválido");
    }
    check_depth--;return flow;
}
static Function *main_function;
static void check(void){
    for(int i=0;i<classes.n;i++){Class *c=classes.v[i];for(int j=0;j<i;j++)if(same(c->t->text,((Class*)classes.v[j])->t->text))error(c->t,"classe declarada duas vezes");}
    for(int i=0;i<functions.n;i++){
        Function *f=functions.v[i];if(find_class(f->t->text))error(f->t,"nome principal declarado duas vezes");
        for(int j=0;j<i;j++)if(same(f->t->text,((Function*)functions.v[j])->t->text))error(f->t,"função declarada duas vezes");signature(f);
    }
    for(int i=0;i<classes.n;i++)layout(classes.v[i]);
    main_function=find_fn(ENTRY);if(!main_function)error(tokens.v[0],"falta a entrada: assis assis_assis(): AssIs { Fodase 0; }");
    if(main_function->params.n||(!isvoid(main_function->result)&&!equal_type(main_function->result,type_i64)))error(main_function->t,"assis_assis recebe zero parâmetros e retorna AssIs ou FODase");
    for(int i=0;i<all_functions.n;i++){
        checking=all_functions.v[i];bindings.n=0;scope_start=0;loop_depth=0;check_depth=0;
        for(int j=0;j<checking->params.n;j++)declare(checking->params.v[j]);
        int flow=check_statement(checking->body,false);
        if(!isvoid(checking->result)&&(flow&FLOW_NORMAL))error(checking->t,"nem todos os caminhos retornam um valor com Fodase");
    }
}

#include "runtime_blob.h"
#include "runtime_win_blob.h"
typedef struct { unsigned char *v;size_t n,cap; } Buffer;
static Buffer code,data;
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
        MAP_RT(write);MAP_RT(print_str);MAP_RT(print_int);MAP_RT(print_char);MAP_RT(print_bool);MAP_RT(print_ptr);
        MAP_RT(alloc);MAP_RT(free);MAP_RT(len);MAP_RT(streq);MAP_RT(strbyte);MAP_RT(error);
        default:fatal("rotina Windows desconhecida");
        }
#undef MAP_RT
    }
    rt_call_raw(offset);
}
enum { RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI };
static void immediate(int reg,uint64_t value){u8(&code,0x48);u8(&code,0xb8+(unsigned)reg);u64(&code,value);}
static void movreg(int dst,int src){INS(0x48,0x89);u8(&code,0xc0+(unsigned)(src*8+dst));}
static void load_stack(int reg,int offset){INS(0x48,0x8b);u8(&code,0x84+(unsigned)(reg*8));u8(&code,0x24);u32(&code,(uint32_t)offset);}
static void load_label(int label){INS(0x48,0xb8);fix(&code,label,false);}
static void clean_stack(int count){if(count){INS(0x48,0x81,0xc4);u32(&code,(uint32_t)count*8);}}
static void panic_at(int reason,int line){immediate(RDI,(uint64_t)reason);immediate(RSI,(uint64_t)line);rt_call(RT_error);INS(0x0f,0x0b);}
static void nonnull(int line){int ok=new_label();INS(0x48,0x85,0xc0);branch_if(0x85,ok);panic_at(1,line);mark(ok,&code);}
static int string_label(const char *s,size_t len){
    for(int i=0;i<strings.n;i++){String *old=strings.v[i];if(old->len==len&&!memcmp(old->str,s,len))return old->label;}
    String *str=mem(sizeof(*str));str->str=s;str->len=len;str->label=new_label();push(&strings,str);
    mark(str->label,&data);bytes(&data,s,len);u8(&data,0);return str->label;
}
static int value_size(Type ty){return ty.depth==0&&(ty.kind==TY_U8||ty.kind==TY_BOOL)?1:8;}
static void load_value(Type ty){if(value_size(ty)==1){INS(0x0f,0xb6,0x00);}else{INS(0x48,0x8b,0x00);}}
static void store_value(Type ty){if(value_size(ty)==1){INS(0x88,0x02);}else{INS(0x48,0x89,0x02);}}
static void bool_result(unsigned condition){INS(0x0f);u8(&code,condition);INS(0xc0,0x0f,0xb6,0xc0);}
static void gen_expr(Node *n);
static void gen_address(Node *n){
    if(n->kind==N_NAME){INS(0x48,0x8d,0x85);u32(&code,(uint32_t)(-8*(n->var->slot+1)));}
    else if(n->kind==N_MEMBER){gen_expr(n->a);nonnull(n->t->line);INS(0x48,0x05);u32(&code,(uint32_t)(8*(n->slot+1)));}
    else if(n->kind==N_INDEX){
        gen_expr(n->a);INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);nonnull(n->t->line);
        if(value_size(n->ty)==8){INS(0x48,0xc1,0xe1,0x03);}INS(0x48,0x01,0xc8);
    }else if(n->kind==N_UNARY&&n->op=='*'){gen_expr(n->a);nonnull(n->t->line);}
    else fatal("posição gravável inválida no backend");
}
static void gen_operation(int op,Type left,Type right,int line){
    if(left.depth&&(op=='+'||op=='-')){
        if(value_size(pointed(left))==8){INS(0x48,0xc1,0xe1,0x03);}
        if(op=='+'){INS(0x48,0x01,0xc8);}else{INS(0x48,0x29,0xc8);}return;
    }
    if((op==T_EQ||op==T_NE)&&equal_type(left,type_str)&&equal_type(right,type_str)){
        movreg(RDI,RAX);movreg(RSI,RCX);rt_call(RT_streq);if(op==T_NE){INS(0x48,0x83,0xf0,0x01);}return;
    }
    switch(op){
    case '+':INS(0x48,0x01,0xc8);break;case '-':INS(0x48,0x29,0xc8);break;
    case '*':INS(0x48,0x0f,0xaf,0xc1);break;
    case '&':INS(0x48,0x21,0xc8);break;case '|':INS(0x48,0x09,0xc8);break;case '^':INS(0x48,0x31,0xc8);break;
    case '/':case '%':{
        int zero_ok=new_label(),safe=new_label(),done=new_label();
        INS(0x48,0x85,0xc9);branch_if(0x85,zero_ok);panic_at(op=='/'?2:8,line);mark(zero_ok,&code);
        INS(0x48,0x83,0xf9,0xff);branch_if(0x85,safe);immediate(RDX,UINT64_C(0x8000000000000000));
        INS(0x48,0x39,0xd0);branch_if(0x85,safe);if(op=='%'){INS(0x31,0xc0);}branch(done);
        mark(safe,&code);INS(0x48,0x99,0x48,0xf7,0xf9);if(op=='%')movreg(RAX,RDX);mark(done,&code);break;
    }
    case T_SHL:case T_SHR:{
        int valid=new_label();INS(0x48,0x83,0xf9,0x3f);branch_if(0x86,valid);panic_at(3,line);mark(valid,&code);
        if(op==T_SHL){INS(0x48,0xd3,0xe0);}else{INS(0x48,0xd3,0xf8);}break;
    }
    default:{
        unsigned cc=op==T_EQ?0x94:op==T_NE?0x95:op=='<'?0x9c:op==T_LE?0x9e:op=='>'?0x9f:0x9d;
        INS(0x48,0x39,0xc8);bool_result(cc);break;
    }
    }
}
static void gen_expr(Node *n){
    switch(n->kind){
    case N_INT:immediate(RAX,n->t->number);break;
    case N_BOOL:immediate(RAX,n->t->kind==T_TRUE?1:0);break;
    case N_NULL:INS(0x31,0xc0);break;
    case N_STR:load_label(string_label(n->t->str,n->t->len));break;
    case N_NAME:case N_MEMBER:gen_address(n);load_value(n->ty);break;
    case N_SELF:INS(0x48,0x8b,0x45,0xf8);break;
    case N_INDEX:
        if(equal_type(n->a->ty,type_str)){
            gen_expr(n->a);INS(0x50);gen_expr(n->b);movreg(RSI,RAX);INS(0x5f);immediate(RDX,(uint64_t)n->t->line);rt_call(RT_strbyte);
        }else{gen_address(n);load_value(n->ty);}break;
    case N_UNARY:
        if(n->op=='&')gen_address(n->a);
        else if(n->op=='*'){gen_address(n);load_value(n->ty);}
        else{
            gen_expr(n->a);
            if(n->op=='-'){INS(0x48,0xf7,0xd8);}else if(n->op=='~'){INS(0x48,0xf7,0xd0);}
            else if(n->op=='!'){INS(0x48,0x85,0xc0);bool_result(0x94);}
        }break;
    case N_BINARY:
        gen_expr(n->a);
        if(n->op==T_AND||n->op==T_OR){
            int end=new_label();INS(0x48,0x85,0xc0);branch_if(n->op==T_AND?0x84:0x85,end);gen_expr(n->b);mark(end,&code);
        }else{INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);gen_operation(n->op,n->a->ty,n->b->ty,n->t->line);}break;
    case N_BUILTIN:
        gen_expr(n->items.v[0]);
        if(n->op==T_ALLOC){movreg(RDI,RAX);immediate(RSI,(uint64_t)n->t->line);rt_call(RT_alloc);}
        else if(n->op==T_LEN){movreg(RDI,RAX);rt_call(RT_len);}
        else if(n->op==T_U8){INS(0x48,0x25,0xff,0x00,0x00,0x00);}
        else if(n->op==T_BOOL){INS(0x48,0x85,0xc0);bool_result(0x95);}break;
    case N_CALL:
        if(n->fn->owner){gen_expr(n->a->a);INS(0x50);}
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        if(n->fn->owner){
            load_stack(RAX,n->items.n*8);nonnull(n->t->line);INS(0x48,0x8b,0x00,0xff,0x90);u32(&code,(uint32_t)n->slot*8);
        }else call_label(n->fn->label);
        clean_stack(n->items.n+(n->fn->owner?1:0));break;
    case N_NEW:{
        immediate(RDI,(uint64_t)(n->cls->fields.n+1)*8);immediate(RSI,(uint64_t)n->t->line);rt_call(RT_alloc);INS(0x50);
        load_label(n->cls->label);load_stack(RDX,0);INS(0x48,0x89,0x02);
        for(int i=0;i<n->cls->fields.n;i++){
            Field *f=n->cls->fields.v[i];if(equal_type(f->ty,type_str)){
                load_label(string_label("",0));load_stack(RDX,0);INS(0x48,0x89,0x82);u32(&code,(uint32_t)(i+1)*8);
            }
        }
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        if(n->fn){
            load_stack(RAX,n->items.n*8);INS(0x48,0x8b,0x00,0xff,0x90);u32(&code,(uint32_t)n->slot*8);clean_stack(n->items.n);
        }
        INS(0x58);break;
    }
    default:fatal("expressão inválida no backend");
    }
}
static int return_label,loop_count,loop_start[MAX_NEST],loop_end[MAX_NEST];
static void gen_stmt(Node *n){
    switch(n->kind){
    case N_BLOCK:for(int i=0;i<n->items.n;i++)gen_stmt(n->items.v[i]);break;
    case N_LET:gen_expr(n->a);INS(0x48,0x89,0x85);u32(&code,(uint32_t)(-8*(n->var->slot+1)));break;
    case N_ASSIGN:
        gen_address(n->a);INS(0x50);
        if(n->op=='=')gen_expr(n->b);
        else{load_value(n->a->ty);INS(0x50);gen_expr(n->b);movreg(RCX,RAX);INS(0x58);gen_operation(compound_op(n->op),n->a->ty,n->b->ty,n->t->line);}
        INS(0x5a);store_value(n->a->ty);break;
    case N_IF:{
        int no=new_label(),end=new_label();gen_expr(n->a);INS(0x48,0x85,0xc0);branch_if(0x84,no);gen_stmt(n->b);branch(end);
        mark(no,&code);if(n->c)gen_stmt(n->c);mark(end,&code);break;
    }
    case N_WHILE:{
        int start=new_label(),end=new_label();loop_start[loop_count]=start;loop_end[loop_count++]=end;
        mark(start,&code);gen_expr(n->a);INS(0x48,0x85,0xc0);branch_if(0x84,end);gen_stmt(n->b);branch(start);mark(end,&code);loop_count--;break;
    }
    case N_BREAK:branch(loop_end[loop_count-1]);break;case N_CONTINUE:branch(loop_start[loop_count-1]);break;
    case N_RETURN:if(n->a)gen_expr(n->a);else{INS(0x31,0xc0);}branch(return_label);break;
    case N_EXPR:gen_expr(n->a);break;
    case N_FREE:gen_expr(n->a);movreg(RDI,RAX);rt_call(RT_free);break;
    case N_PRINT:
        for(int i=0;i<n->items.n;i++){gen_expr(n->items.v[i]);INS(0x50);}
        for(int i=0;i<n->items.n;i++){
            if(i){immediate(RDI,32);immediate(RSI,1);rt_call(RT_print_char);}
            Node *a=n->items.v[i];load_stack(RDI,(n->items.n-1-i)*8);immediate(RSI,1);
            rt_call(numeric(a->ty)?RT_print_int:equal_type(a->ty,type_bool)?RT_print_bool:equal_type(a->ty,type_str)?RT_print_str:RT_print_ptr);
        }
        clean_stack(n->items.n);immediate(RDI,10);immediate(RSI,1);rt_call(RT_print_char);break;
    default:fatal("instrução inválida no backend");
    }
}
static size_t entry_offset;
static void generate(void){
    if(target_windows)bytes(&code,runtime_win_blob,sizeof(runtime_win_blob));else bytes(&code,runtime_blob,sizeof(runtime_blob));
    for(int i=0;i<all_functions.n;i++)((Function*)all_functions.v[i])->label=new_label();
    for(int i=0;i<classes.n;i++)((Class*)classes.v[i])->label=new_label();
    entry_offset=code.n;INS(0x31,0xed);if(target_windows)rt_call_raw(WRT_init);call_label(main_function->label);
    if(isvoid(main_function->result)){INS(0x31,0xff);}else{movreg(RDI,RAX);INS(0x81,0xe7,0xff,0x00,0x00,0x00);}
    if(target_windows)rt_call_raw(WRT_exit);else{immediate(RAX,60);INS(0x0f,0x05,0x0f,0x0b);}
    for(int i=0;i<all_functions.n;i++){
        Function *f=all_functions.v[i];mark(f->label,&code);return_label=new_label();loop_count=0;
        INS(0x55,0x48,0x89,0xe5,0x48,0x81,0xec);
        uint32_t locals=(uint32_t)(f->vars.n+(f->owner?1:0))*8;locals=(locals+15)&~15u;u32(&code,locals);
        int count=f->params.n+(f->owner?1:0);
        if(f->owner){INS(0x48,0x8b,0x85);u32(&code,(uint32_t)(16+8*(count-1)));INS(0x48,0x89,0x45,0xf8);}
        for(int j=0;j<f->params.n;j++){
            Var *v=f->params.v[j];int index=j+(f->owner?1:0);
            INS(0x48,0x8b,0x85);u32(&code,(uint32_t)(16+8*(count-1-index)));
            INS(0x48,0x89,0x85);u32(&code,(uint32_t)(-8*(v->slot+1)));
        }
        gen_stmt(f->body);
        if(isvoid(f->result)){INS(0x31,0xc0);}else panic_at(7,f->t->line);
        mark(return_label,&code);INS(0xc9,0xc3);
    }
    while(data.n%8)u8(&data,0);
    for(int i=0;i<classes.n;i++){
        Class *c=classes.v[i];mark(c->label,&data);
        if(!c->methods.n)u64(&data,0);
        for(int j=0;j<c->methods.n;j++)fix(&data,((Function*)c->methods.v[j])->label,false);
    }
    if(!data.n)u8(&data,0);
}
static size_t align_page(size_t size){return (size+4095)&~(size_t)4095;}
#define ELF_BASE UINT64_C(0x400000)
static void apply_fixes(uint64_t base,size_t text_rva,size_t data_rva){
    for(int i=0;i<fixes.n;i++){
        Fix *f=fixes.v[i];Label *l=labels.v[f->label];if(!l->defined)fatal("rótulo não definido");
        uint64_t address=base+(l->section?data_rva:text_rva)+l->position;
        if(f->relative){
            int64_t diff=(int64_t)address-(int64_t)(base+text_rva+f->position+4);
            if(diff<INT32_MIN||diff>INT32_MAX)fatal("salto fora do alcance");
            uint32_t d=(uint32_t)(int32_t)diff;for(int j=0;j<4;j++)f->buffer->v[f->position+(size_t)j]=(unsigned char)(d>>(8*j));
        }else for(int j=0;j<8;j++)f->buffer->v[f->position+(size_t)j]=(unsigned char)(address>>(8*j));
    }
}
static void write_elf(const char *path){
    size_t data_offset=align_page(4096+code.n);apply_fixes(ELF_BASE,4096,data_offset);
    Elf64_Ehdr eh={0};memcpy(eh.e_ident,ELFMAG,SELFMAG);eh.e_ident[EI_CLASS]=ELFCLASS64;eh.e_ident[EI_DATA]=ELFDATA2LSB;eh.e_ident[EI_VERSION]=EV_CURRENT;
    eh.e_type=ET_EXEC;eh.e_machine=EM_X86_64;eh.e_version=EV_CURRENT;eh.e_entry=ELF_BASE+4096+entry_offset;
    eh.e_phoff=sizeof(eh);eh.e_ehsize=sizeof(eh);eh.e_phentsize=sizeof(Elf64_Phdr);eh.e_phnum=4;
    Elf64_Phdr ph[4]={0};
    ph[0]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R,.p_offset=0,.p_vaddr=ELF_BASE,.p_paddr=ELF_BASE,.p_filesz=4096,.p_memsz=4096,.p_align=4096};
    ph[1]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R|PF_X,.p_offset=4096,.p_vaddr=ELF_BASE+4096,.p_paddr=ELF_BASE+4096,.p_filesz=code.n,.p_memsz=code.n,.p_align=4096};
    ph[2]=(Elf64_Phdr){.p_type=PT_LOAD,.p_flags=PF_R,.p_offset=data_offset,.p_vaddr=ELF_BASE+data_offset,.p_paddr=ELF_BASE+data_offset,.p_filesz=data.n,.p_memsz=data.n,.p_align=4096};
    ph[3]=(Elf64_Phdr){.p_type=PT_GNU_STACK,.p_flags=PF_R|PF_W,.p_align=16};
    protect_output(path);
    FILE *fp=fopen(path,"wb");if(!fp)fatal("não foi possível criar %s: %s",path,strerror(errno));
    unsigned char header[4096]={0};memcpy(header,&eh,sizeof(eh));memcpy(header+sizeof(eh),ph,sizeof(ph));
    bool ok=fwrite(header,1,sizeof(header),fp)==sizeof(header)&&fwrite(code.v,1,code.n,fp)==code.n;
    size_t pad=data_offset-4096-code.n;unsigned char zero[4096]={0};if(ok&&pad)ok=fwrite(zero,1,pad,fp)==pad;
    if(ok)ok=fwrite(data.v,1,data.n,fp)==data.n;if(fclose(fp))ok=false;
    if(!ok){unlink(path);fatal("erro ao gravar %s",path);}if(chmod(path,0755))fatal("não foi possível marcar %s como executável: %s",path,strerror(errno));
}

#include "pe_writer.h"
static void write_executable(const char *path){if(target_windows)write_pe(path);else write_elf(path);}
static void help(void){
    puts("AssisScript " VERSION " | compilador nativo " HOST_NAME "\n"
         "\nUso: assis <comando> [arquivo.assis] [opções]\n"
         "\n  assis new <pasta>                  cria um projeto com exemplo\n"
         "  assis build [fonte] [-o programa]  gera executável nativo diretamente\n"
         "  assis run [fonte] [--timeout n]    compila e executa\n"
         "  assis check [fonte]               valida sintaxe e tipos\n"
         "  assis tokens [fonte]              mostra tokens e posições\n"
         "  assis doctor                      mostra informações da instalação\n"
         "  assis version                     mostra a versão\n"
         "  assis help                        mostra esta ajuda\n"
         "\nSem fonte, procura assis.assis no diretório atual.\n"
         "build aceita --target windows-x64 ou --target linux-x64.\n"
         "Aliases: criar, compilar, executar, verificar.\n"
         "O compilador não chama Python, GCC, Clang, assembler ou linker.");
}
static void read_source(const char *path){
    filename=path;FILE *f=fopen(path,"rb");if(!f)fatal("não foi possível ler %s: %s",path,strerror(errno));
    if(fseek(f,0,SEEK_END)){fclose(f);fatal("não foi possível medir %s",path);}long size=ftell(f);
    if(size<0||size>MAX_SOURCE){fclose(f);fatal("arquivo maior que o limite de 16 MiB");}rewind(f);
    source=mem((size_t)size+1);if(fread(source,1,(size_t)size,f)!=(size_t)size){fclose(f);fatal("erro ao ler %s",path);}fclose(f);
    if(memchr(source,0,(size_t)size))fatal("o arquivo fonte contém um byte nulo; use \\0 dentro do texto");
    if(size>=3&&(unsigned char)source[0]==0xef&&(unsigned char)source[1]==0xbb&&(unsigned char)source[2]==0xbf)memmove(source,source+3,(size_t)size-2);
}
static void create_project(const char *folder){
    if(!folder||!*folder)fatal("informe uma pasta: assis new meu-projeto");
    if(mkdir(folder,0755))fatal("não foi possível criar %s: %s",folder,strerror(errno));
    size_t size=strlen(folder)+32;char *path=mem(size);snprintf(path,size,"%s/assis.assis",folder);
    FILE *f=fopen(path,"w");if(!f)fatal("não foi possível criar %s",path);
    const char *sample="// Criado pelo AssisScript nativo.\n"
        "ASSIS AssisAssis {\n    Assis Assis_assis: AssIs;\n"
        "    assis assis_fodase(AssisFodase: AssIs): FODase {\n        aSSIS.Assis_assis = AssisFodase;\n    }\n"
        "    assis FodaseFodase(): AssIs {\n        Fodase aSSIS.Assis_assis;\n    }\n}\n\n"
        "assis assis_assis(): AssIs {\n    Assis AssisFodase: AssisAssis = fodase AssisAssis(42);\n"
        "    FODASE(\"Assis, mundo. Fodase.\", AssisFodase.FodaseFodase());\n    foDASE(AssisFodase);\n    Fodase 0;\n}\n";
    bool ok=fputs(sample,f)>=0;if(fclose(f))ok=false;if(!ok)fatal("erro ao criar projeto");
    printf("ASSIS: projeto criado em %s\nEntre na pasta e execute: assis run\n",folder);
}
#ifndef _WIN32
static double now_seconds(void){struct timespec ts;if(clock_gettime(CLOCK_MONOTONIC,&ts))fatal("relógio monotônico indisponível");return (double)ts.tv_sec+(double)ts.tv_nsec/1000000000.0;}
static int run_program(double timeout){
    char directory[]="/tmp/assisscript-XXXXXX";if(!mkdtemp(directory))fatal("não foi possível criar diretório temporário: %s",strerror(errno));
    char path[128];snprintf(path,sizeof(path),"%s/programa",directory);write_executable(path);fflush(NULL);
    pid_t child=fork();if(child<0){unlink(path);rmdir(directory);fatal("fork falhou: %s",strerror(errno));}
    if(!child){execl(path,path,(char*)NULL);fprintf(stderr,"FODASE: não foi possível executar %s: %s\n",path,strerror(errno));_exit(126);}
    int status=0;double start=now_seconds();bool timed_out=false;
    for(;;){
        pid_t result=waitpid(child,&status,timeout>0?WNOHANG:0);
        if(result==child)break;if(result<0){if(errno==EINTR)continue;unlink(path);rmdir(directory);fatal("waitpid falhou: %s",strerror(errno));}
        if(timeout>0&&now_seconds()-start>=timeout){kill(child,SIGKILL);while(waitpid(child,&status,0)<0&&errno==EINTR){}timed_out=true;break;}
        struct timespec nap={0,10000000};nanosleep(&nap,NULL);
    }
    unlink(path);rmdir(directory);
    if(timed_out){fputs("FODASE: o programa excedeu o tempo de execução definido.\n",stderr);return 124;}
    if(WIFEXITED(status))return WEXITSTATUS(status);
    if(WIFSIGNALED(status)){fprintf(stderr,"FODASE: programa encerrado pelo sinal %d.\n",WTERMSIG(status));return 128+WTERMSIG(status);}return 1;
}
#else
static int run_program(double timeout){
    wchar_t temp[32768],directory[32768],path[32768];DWORD n=GetTempPathW(32768,temp);
    if(!n||n>=32768||!GetTempFileNameW(temp,L"ass",0,directory))fatal("não foi possível criar diretório temporário (Windows %lu)",(unsigned long)GetLastError());
    if(!DeleteFileW(directory)||!CreateDirectoryW(directory,NULL))fatal("não foi possível preparar diretório temporário");
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
    if(timed_out)fputs("FODASE: o programa excedeu o tempo de execução definido.\n",stderr);
    return (int)status;
}
#endif
static const char *token_name(Token *t){
    if(t->kind==T_ID)return "NOME";if(t->kind==T_INT)return "INTEIRO";if(t->kind==T_STR)return "TEXTO";if(t->kind==T_EOF)return "FIM";
    for(int i=0;words[i].name;i++)if(words[i].kind==t->kind)return words[i].name;return "OPERADOR";
}
static int compiler_main(int argc,char **argv){
    if(argc<2){help();return 0;}const char *cmd=argv[1];
    if(same(cmd,"--help")||same(cmd,"help")||same(cmd,"--ajuda")){help();return 0;}
    if(same(cmd,"--version")||same(cmd,"version")){puts("AssisScript " VERSION " (nativo, " HOST_NAME ")");return 0;}
    if(same(cmd,"doctor")){
        puts("AssisScript " VERSION "\nHost: " HOST_NAME "\nBackends: ELF64 Linux / PE32+ Windows x64\nRuntime: incorporado; usa APIs do sistema de destino\nDependências para compilar: nenhuma ferramenta externa\nEntrada do projeto: assis.assis");return 0;
    }
    if(same(cmd,"new")||same(cmd,"init")||same(cmd,"criar")){if(argc!=3)fatal("use: assis new <pasta>");create_project(argv[2]);return 0;}
    bool build=same(cmd,"build")||same(cmd,"compilar"),run=same(cmd,"run")||same(cmd,"executar");
    bool validate=same(cmd,"check")||same(cmd,"verificar"),show_tokens=same(cmd,"tokens");
    if(!build&&!run&&!validate&&!show_tokens)fatal("comando desconhecido: %s. Use assis help.",cmd);
    const char *input=NULL,*output=NULL;double timeout=0;
    for(int i=2;i<argc;i++){
        if(same(argv[i],"-o")||same(argv[i],"--output")){if(!build||i+1>=argc)fatal("-o exige um destino e só pode ser usado em build");output=argv[++i];}
        else if(same(argv[i],"--timeout")){
            if(!run||i+1>=argc)fatal("--timeout exige segundos e só pode ser usado em run");char *end=NULL;errno=0;timeout=strtod(argv[++i],&end);
            if(errno||!end||*end||!isfinite(timeout)||timeout<=0)fatal("--timeout deve ser um número positivo");
        }else if(same(argv[i],"--target")){
            if((!build&&!run)||i+1>=argc)fatal("--target exige linux-x64 ou windows-x64 em build/run");const char *target=argv[++i];
            if(same(target,"windows-x64"))target_windows=true;else if(same(target,"linux-x64"))target_windows=false;else fatal("destino desconhecido: %s",target);
        }else if(same(argv[i],"--help")||same(argv[i],"-h")){help();return 0;}
        else if(argv[i][0]=='-')fatal("opção desconhecida: %s",argv[i]);
        else if(!input)input=argv[i];else fatal("informe apenas um arquivo fonte");
    }
    if(run){
#ifdef _WIN32
        if(!target_windows)fatal("run no Windows exige destino windows-x64; use build para gerar Linux");
#else
        if(target_windows)fatal("run no Linux exige destino linux-x64; use build para gerar Windows");
#endif
    }
    if(!input)input="assis.assis";read_source(input);lex();
    if(show_tokens){for(int i=0;i<tokens.n;i++){Token *t=tokens.v[i];printf("%4d:%-3d %-18s %s\n",t->line,t->col,token_name(t),t->text);}return 0;}
    parse();check();if(validate){printf("ASSIS: %s passou na análise de sintaxe e tipos.\n",input);return 0;}
    generate();if(run)return run_program(timeout);
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
    write_executable(output);printf("ASSIS: executável nativo gerado em %s\n",output);return 0;
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

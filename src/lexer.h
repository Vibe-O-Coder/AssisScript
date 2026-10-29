/* Lexical analysis and source diagnostics. Included by the compiler driver. */
enum {
    T_EOF=256,T_ID,T_INT,T_STR,T_CLASS,T_EXTENDS,T_FN,T_LET,T_I64,T_U8,T_BOOL,T_TEXT,T_VOID,
    T_IF,T_ELSE,T_WHILE,T_RETURN,T_PRINT,T_NEW,T_FREE,T_SELF,T_TRUE,T_FALSE,T_NULL,
    T_BREAK,T_CONTINUE,T_ALLOC,T_LEN,T_EQ,T_NE,T_LE,T_GE,T_AND,T_OR,T_SHL,T_SHR,
    T_ADDSET,T_SUBSET,T_MULSET,T_DIVSET,T_MODSET,T_ANDSET,T_ORSET,T_XORSET,T_SHLSET,T_SHRSET,T_IMPORT,T_FILE_END,
    T_INC,T_DEC,T_YURI,T_BODY,T_STRUCT,T_BUFFER,T_ASSERT,T_BYTES,T_OWN,T_BORROW,T_MUT,T_MOVE,T_DEFER,T_DIV,T_FOR,T_READ,T_NOW,T_SAFE,T_UNSAFE,
    T_PRIVATE,T_VAL,T_PURE,T_VALUE,T_ENUM,T_MATCH,T_FILE,T_FILE_OPEN,T_FILE_READ,T_FILE_WRITE,T_FILE_CLOSE,T_IO_ERROR,T_ARGC,T_ARG_LEN,T_ARG_COPY,T_NUMTYPE,T_REAL,T_NAMESPACE,T_PUBLIC,T_SLEEP,T_CIVIL,T_FILE_SYNC,T_FILE_REPLACE,T_FILE_REMOVE,T_WRITE_BYTES,T_SLICE,T_SLICE_MAKE,T_EXTERN,T_C_CALLBACK,T_PLATFORM,T_CLOSURE,T_CHAR,T_CONST,T_SUPER,T_WRITE,T_UTF8,T_IS,T_AS
};
typedef struct { const char *name; int kind; } Word;
static const Word words[]={
    {"extern",T_EXTERN},{"c_callback",T_C_CALLBACK},{"platform",T_PLATFORM},{"closure",T_CLOSURE},
    {"is",T_IS},{"as",T_AS},{"const",T_CONST},{"super",T_SUPER},{"utf8",T_UTF8},{"fn",T_FN},{"class",T_CLASS},{"import",T_IMPORT},
    {"slice_of",T_SLICE_MAKE},{"read_bytes",T_READ},{"monotonic_ms",T_NOW},{"write_bytes",T_WRITE_BYTES},{"sleep_ms",T_SLEEP},{"civil_ms",T_CIVIL},{"file_sync",T_FILE_SYNC},{"file_replace",T_FILE_REPLACE},{"file_remove",T_FILE_REMOVE},{"File",T_FILE},{"file_open",T_FILE_OPEN},{"file_read",T_FILE_READ},{"file_write",T_FILE_WRITE},{"file_close",T_FILE_CLOSE},{"io_error",T_IO_ERROR},{"arg_count",T_ARGC},{"arg_size",T_ARG_LEN},{"arg_copy",T_ARG_COPY},
    {"slice",T_SLICE},
    {"let",T_LET},{"int",T_I64},{"byte",T_U8},{"bool",T_BOOL},{"text",T_TEXT},{"void",T_VOID},
    {"if",T_IF},{"else",T_ELSE},{"while",T_WHILE},{"return",T_RETURN},{"print",T_PRINT},
    {"new",T_NEW},{"free",T_FREE},{"self",T_SELF},{"true",T_TRUE},{"false",T_FALSE},{"null",T_NULL},
    {"break",T_BREAK},{"continue",T_CONTINUE},{"alloc",T_BUFFER},{"len",T_LEN},{"extends",T_EXTENDS},
    {"struct",T_STRUCT},{"assert",T_ASSERT},{"bytes",T_BYTES},
    {"own",T_OWN},{"borrow",T_BORROW},{"mut",T_MUT},{"move",T_MOVE},{"safe",T_SAFE},{"unsafe",T_UNSAFE},
    {"defer",T_DEFER},{"for",T_FOR},
    {"private",T_PRIVATE},{"val",T_VAL},{"pure",T_PURE},{"enum",T_ENUM},{"match",T_MATCH},{"namespace",T_NAMESPACE},{"public",T_PUBLIC},
    {"i8",T_NUMTYPE},{"i16",T_NUMTYPE},{"i32",T_NUMTYPE},{"i64",T_I64},{"u8",T_U8},{"u16",T_NUMTYPE},{"u32",T_NUMTYPE},{"u64",T_NUMTYPE},{"f32",T_NUMTYPE},{"f64",T_NUMTYPE},


    {NULL,0}
};
typedef struct Token { int kind,line,col; char *text,*str; size_t len; uint64_t number; const char *at; SourceFile *file; } Token;
static Token *instantiation_site;
static const char *instantiation_name;
static Vec tokens; static char *source;
static int cursor=0, parse_depth=0;

static const char *diagnostic_hint(const char *message){
    if(strstr(message,"não declarada")||strstr(message,"desconhecida"))return "Confira a grafia e importe a biblioteca com import \"std/nome.assis\";. Declare variáveis antes do uso.";
    if(strstr(message,"módulo não encontrado"))return "Confira o caminho relativo ao arquivo importador e as bibliotecas instaladas. Use -I pasta para bibliotecas externas.";
    if(strstr(message,"borrow")||strstr(message,"exclusivo"))return "Encerre o empréstimo anterior em um bloco antes de mutar, mover ou liberar o proprietário.";
    if(strstr(message,"movido")||strstr(message,"liberado"))return "Use o novo proprietário após move; não reutilize um recurso consumido.";
    if(strstr(message,"não é possível usar")||strstr(message,"incompatível"))return "Confira os tipos na declaração e na assinatura da função. Conversões int(...), byte(...) e bool(...) devem ser explícitas.";
    if(strstr(message,"argumentos"))return "Compare a chamada com a assinatura: quantidade, ordem e tipos dos parâmetros devem coincidir.";
    if(strstr(message,"esperado ;"))return "Termine a instrução anterior com ponto e vírgula (;).";
    if(strstr(message,"esperado }")||strstr(message,"retornam"))return "Confira as chaves do bloco e retorne um valor do tipo declarado em todos os caminhos.";
    if(strstr(message,"índice"))return "Use um índice inteiro entre zero e len(colecao) - 1. Verifique o tamanho antes do acesso.";
    return "Confira o trecho indicado e consulte o manual offline e a documentação da biblioteca no VS Code.";
}

static _Noreturn void error(Token *t,const char *fmt,...) {
    char message[4096];va_list ap;va_start(ap,fmt);vsnprintf(message,sizeof(message),fmt,ap);va_end(ap);
    if(instantiation_site){size_t used=strlen(message);snprintf(message+used,sizeof(message)-used," [instância de %s em %s:%d]",instantiation_name,instantiation_site->file->path,instantiation_site->line);}
    SourceFile *file=t&&t->file?t->file:current_source;
    const char *base=file?file->text:source,*path=file?file->path:filename;
    const char *a=t&&t->at?t->at:base;const char *start=a;
    while(start>base&&start[-1]!='\n')start--;
    /* Editor columns are UTF-16 code units, as required by VS Code/LSP. */
    int column=1;for(const unsigned char *p=(const unsigned char*)start;p<(const unsigned char*)a;p++)
        if((*p&0xc0)!=0x80)column+=*p>=0xf0?2:1;
    int width=1;if(t&&t->text&&t->kind!=T_STR&&t->kind!=T_EOF){width=0;for(const unsigned char *p=(const unsigned char*)t->text;*p;p++)if((*p&0xc0)!=0x80)width+=*p>=0xf0?2:1;if(!width)width=1;}
    const char *hint=diagnostic_hint(message);
    if(json_diagnostics){
        fputs("{\"file\":",stderr);json_string(stderr,path?path:"");
        fprintf(stderr,",\"line\":%d,\"column\":%d,\"code\":\"A001\",\"message\":",t?t->line:1,column);
        json_string(stderr,message);fprintf(stderr,",\"endColumn\":%d,\"severity\":\"error\",\"hint\":",column+width);json_string(stderr,hint);fputs("}\n",stderr);exit(1);
    }
    fprintf(stderr,"%s:%d:%d: A001: %s\n",path?path:"",t?t->line:1,column,message);
    const char *end=a;while(*end&&*end!='\n'&&*end!='\r')end++;
    fputs("  ",stderr);fwrite(start,1,(size_t)(end-start),stderr);fputs("\n  ",stderr);
    for(const char *p=start;p<a;p++) fputc(*p=='\t'?'\t':' ',stderr);
    fputs("^\n",stderr);fprintf(stderr,"  Ajuda: %s\n",hint);exit(1);
}
static bool ascii_alpha(unsigned char c) { return (c>='a'&&c<='z')||(c>='A'&&c<='Z'); }
static bool ascii_digit(unsigned char c) { return c>='0'&&c<='9'; }
static int digit(unsigned char c) {
    if(c>='0'&&c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10;
    if(c>='A'&&c<='F')return c-'A'+10; return -1;
}
static void lex(void) {
    char *p=source;int line=1,col=1;
    while(*p) {
        if(isspace((unsigned char)*p)){if(*p=='\n'){line++;col=1;}else col++;p++;continue;}
        if((p[0]=='/'&&p[1]=='/')){while(*p&&*p!='\n'){p++;col++;}continue;}
        Token *t=mem(sizeof(*t));t->line=line;t->col=col;t->at=p;t->file=current_source;
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
            if(t->kind==T_ID&&!strncmp(t->text,"__assis_",8)&&!current_source->internal)error(t,"o prefixo __assis_ é reservado ao compilador");
        } else if(ascii_digit((unsigned char)*p)) {
            char *begin=p;char *q=p;
            while(ascii_digit((unsigned char)*q)||*q=='_')q++;
            bool real=(*q=='.'&&ascii_digit((unsigned char)q[1]))||*q=='e'||*q=='E';
            if(real&&!(p[0]=='0'&&(p[1]=='x'||p[1]=='X'||p[1]=='b'||p[1]=='B'))){
                if(*q=='.'){q++;while(ascii_digit((unsigned char)*q)||*q=='_')q++;}
                if(*q=='e'||*q=='E'){q++;if(*q=='+'||*q=='-')q++;char *exponent=q;while(ascii_digit((unsigned char)*q)||*q=='_')q++;if(q==exponent)error(t,"expoente real incompleto");}
                char *decimal=mem((size_t)(q-begin)+1);size_t used=0;
                for(char *c=begin;c<q;c++){if(*c=='_'){if(c==begin||!ascii_digit((unsigned char)c[-1])||!ascii_digit((unsigned char)c[1]))error(t,"separador real inválido");}else decimal[used++]=*c;}
                char *end;double value=strtod(decimal,&end);if(*end||!isfinite(value))error(t,"literal real inválido ou infinito; use conversão explícita");
                memcpy(&t->number,&value,8);t->kind=T_REAL;t->text=copy(begin,(size_t)(q-begin));col+=(int)(q-p);p=q;push(&tokens,t);continue;
            }
            while(ascii_alpha((unsigned char)*p)||ascii_digit((unsigned char)*p)||*p=='_'){p++;col++;}
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
        } else if(*p=='\'') {
            char *begin=p++;col++;unsigned value=(unsigned char)*p;
            if(!*p||*p=='\''||*p=='\n'||*p=='\r')error(t,"literal de caractere exige exatamente um byte");
            p++;col++;
            if(value=='\\'){
                unsigned char c=(unsigned char)*p++;col++;
                if(c=='n')value='\n';else if(c=='r')value='\r';else if(c=='t')value='\t';else if(c=='0')value=0;
                else if(c=='\\'||c=='\''||c=='"')value=c;
                else if(c=='x'){value=0;for(int i=0;i<2;i++){if(!*p||digit((unsigned char)*p)<0)error(t,"escape de byte exige dois dígitos hexadecimais");value=value*16+(unsigned)digit((unsigned char)*p++);col++;}}
                else error(t,"escape de caractere desconhecido");
            }
            if(*p!='\'')error(t,"literal de caractere exige exatamente um byte; use texto UTF-8 para Unicode");p++;col++;
            t->kind=T_CHAR;t->number=value;t->text=copy(begin,(size_t)(p-begin));
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
            static const Word ops[]={{"<<=",T_SHLSET},{">>=",T_SHRSET},{"++",T_INC},{"--",T_DEC},{"==",T_EQ},{"!=",T_NE},{"<=",T_LE},{">=",T_GE},{"&&",T_AND},{"||",T_OR},{"<<",T_SHL},{">>",T_SHR},{"+=",T_ADDSET},{"-=",T_SUBSET},{"*=",T_MULSET},{"/=",T_DIVSET},{"%=",T_MODSET},{"&=",T_ANDSET},{"|=",T_ORSET},{"^=",T_XORSET},{NULL,0}};
            int length=1;t->kind=(unsigned char)*p;
            for(int i=0;ops[i].name;i++){size_t len=strlen(ops[i].name);if(!strncmp(p,ops[i].name,len)){t->kind=ops[i].kind;length=(int)len;break;}}
            if(length==1&&!strchr("{}()[];:,.+-*/%&|^~!<>=",*p))error(t,"caractere inesperado: 0x%02x",(unsigned char)*p);
            t->text=copy(p,(size_t)length);p+=length;col+=length;
        }
        push(&tokens,t);
    }
    Token *t=mem(sizeof(*t));t->kind=T_EOF;t->text="fim do arquivo";t->line=line;t->col=col;t->at=p;t->file=current_source;push(&tokens,t);
}


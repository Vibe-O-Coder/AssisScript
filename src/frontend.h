/* Types, parser, resolution and semantic passes, separate from native emission. */
typedef uint32_t DefId;
typedef uint32_t TypeId;
typedef enum { TY_I64,TY_U8,TY_BOOL,TY_STR,TY_VOID,TY_OBJ,TY_NULL,TY_VAR,TY_APPLY,TY_FN,TY_FILE,TY_I8,TY_I16,TY_I32,TY_U16,TY_U32,TY_U64,TY_F32,TY_F64,TY_SLICE } TypeKind;
typedef struct TypeRef TypeRef;
typedef struct { TypeKind kind; int depth; char *name; TypeRef *ref; } Type;
struct TypeRef { DefId definition; Vec arguments,modes; Token *origin; Type *result; bool pure,safe,closure; int result_mode,result_from,receiver_mode; };
typedef struct { Type ty; TypeId id; } TypeIdentity;
typedef struct { Token *t; DefId id; } TypeParameter;
static DefId next_definition;
static Vec type_identities,type_parameters;
typedef struct Class Class;typedef struct Function Function;typedef struct Var Var;typedef struct Node Node;typedef struct IRExpr IRExpr;typedef struct IROperation IROperation;
struct Var { Token *t;Type ty;int slot,length_slot,ownership,shared,loop,reg,uses;bool moved,exclusive,deferred,address_taken,immutable,static_text;Var *root,*parent;int field_slot;Vec capture_roots; };
typedef struct { Token *t;Type ty;int slot,offset;Class *owner;bool private,owned,borrowed; } Field;
typedef struct { Token *t;Vec fields;int tag; } Variant;
enum { N_INT,N_STR,N_BOOL,N_NULL,N_NAME,N_SELF,N_UNARY,N_BINARY,N_CALL,N_MEMBER,N_INDEX,N_NEW,N_BUILTIN,N_BLOCK,N_LET,N_ASSIGN,N_IF,N_WHILE,N_RETURN,N_PRINT,N_FREE,N_BREAK,N_CONTINUE,N_EXPR,N_ARRAY,N_DEFER,N_UNSAFE,N_MATCH,N_ARM,N_IS,N_CAST };
struct Node { int kind,op;Token *t,*variant_name;Node *a,*b,*c,*step;Vec items,type_args,capture_roots;Type ty,decl;Var *var,*place,*temp;Field *field;Variant *variant;Function *fn;Class *cls;IRExpr *ir;IROperation *operation;int slot,ownership;size_t code_start,code_end;bool lvalue,immutable,specialized,replace_owned,unreachable,bounds_proven; };
struct Function { Token *t;Vec params,vars,type_params,type_args;Type result;Node *body;Class *owner;Function *generic;Var *receiver;Token *site,*result_source;DefId id;int label,expansion,result_mode,result_from,receiver_mode,slots;size_t code_end;bool private,pure,safe,foreign,callback;char *foreign_library[2],*foreign_symbol;int import_label,callback_label; };
struct Class { Token *t,*site;Token *base_name;Type base_type;Class *base,*generic;Vec own_fields,own_methods,fields,methods,type_params,type_args,variants;DefId id;TypeRef *type_ref;char *display;int state,label,drop_label,owned_state,expansion,size,value_state;bool record,value,tagged,sealed,closure; };
static Vec classes,functions,all_functions,generic_classes,generic_functions;
typedef struct {Token *t;Type ty;Node *value;int state;} GlobalConstant;
static Vec global_constants;
static const Type type_i64={TY_I64,0,NULL,NULL},type_u8={TY_U8,0,NULL,NULL},type_bool={TY_BOOL,0,NULL,NULL},type_str={TY_STR,0,NULL,NULL},type_void={TY_VOID,0,NULL,NULL},type_null={TY_NULL,0,NULL,NULL};
static const Type type_file={TY_FILE,0,NULL,NULL};
#include "numeric.h"
static Type pointer(Type t){t.depth++;return t;}
static Type pointed(Type t){t.depth--;return t;}
static bool slice_type(Type t){return !t.depth&&t.kind==TY_SLICE;}
static Type slice_element(Type t){return *(Type*)t.ref->arguments.v[0];}
static int parameter_mode(TypeRef *r,int i){return i<r->modes.n?(int)(intptr_t)r->modes.v[i]:0;}
static bool same_modes(TypeRef *a,TypeRef *b){
    if(a->closure!=b->closure||(a->closure&&a->receiver_mode!=b->receiver_mode))return false;
    if(a->result_mode!=b->result_mode||(a->result_mode>=2&&a->result_from!=b->result_from))return false;
    for(int i=0;i<a->arguments.n;i++)if(parameter_mode(a,i)!=parameter_mode(b,i))return false;return true;
}
static bool equal_type(Type a,Type b){
    if(a.kind!=b.kind||a.depth!=b.depth)return false;
    if(a.kind==TY_SLICE)return equal_type(slice_element(a),slice_element(b));
    if(a.kind==TY_FN){
        if(a.ref->pure!=b.ref->pure||a.ref->safe!=b.ref->safe||a.ref->arguments.n!=b.ref->arguments.n||!same_modes(a.ref,b.ref)||!equal_type(*a.ref->result,*b.ref->result))return false;
        for(int i=0;i<a.ref->arguments.n;i++)if(!equal_type(*(Type*)a.ref->arguments.v[i],*(Type*)b.ref->arguments.v[i]))return false;
        return true;
    }
    if(a.kind!=TY_OBJ&&a.kind!=TY_VAR&&a.kind!=TY_APPLY)return true;
    if(a.ref&&b.ref&&a.ref->definition&&b.ref->definition)return a.ref->definition==b.ref->definition;
    if(a.kind==TY_VAR)return false;
    if(!same(a.name,b.name))return false;
    if(a.kind!=TY_APPLY)return true;
    if(a.ref->arguments.n!=b.ref->arguments.n)return false;
    for(int i=0;i<a.ref->arguments.n;i++)if(!equal_type(*(Type*)a.ref->arguments.v[i],*(Type*)b.ref->arguments.v[i]))return false;
    return true;
}
static TypeId type_identity(Type t){
    if(t.kind==TY_VAR||t.kind==TY_APPLY||(t.kind==TY_OBJ&&(!t.ref||!t.ref->definition)))fatal("identidade de tipo exige resolução concreta");
    if(t.kind==TY_FN){
        (void)type_identity(*t.ref->result);
        for(int i=0;i<t.ref->arguments.n;i++)(void)type_identity(*(Type*)t.ref->arguments.v[i]);
    }
    for(int i=0;i<type_identities.n;i++){TypeIdentity *key=type_identities.v[i];if(equal_type(key->ty,t))return key->id;}
    TypeIdentity *key=mem(sizeof(*key));key->ty=t;key->id=(TypeId)type_identities.n+1;push(&type_identities,key);return key->id;
}
static const char *collection_display(const char *name);
static const char *type_base(Type t){
    return numeric_name(t)?numeric_name(t):t.kind==TY_OBJ?collection_display(t.name):t.kind==TY_I64?"int":t.kind==TY_U8?"byte":t.kind==TY_BOOL?"bool":t.kind==TY_STR?"text":t.kind==TY_FILE?"File":t.kind==TY_VOID?"void":t.kind==TY_VAR||t.kind==TY_APPLY?t.name:"nulo";
}
static void type_spelling(Type t,char *out,size_t cap){
    if(!cap)return;out[0]=0;
    for(int i=0;i<t.depth&&strlen(out)+1<cap;i++)strcat(out,"*");
    if(t.kind==TY_SLICE){snprintf(out+strlen(out),cap-strlen(out),"slice<");type_spelling(slice_element(t),out+strlen(out),cap-strlen(out));snprintf(out+strlen(out),cap-strlen(out),">");return;}
    if(t.kind==TY_FN){
        snprintf(out+strlen(out),cap-strlen(out),"%s",t.ref->closure?(t.ref->receiver_mode==3?"closure mut(":"closure("):t.ref->pure?"pure fn(":t.ref->safe?"safe fn(":"fn(");
        for(int i=0;i<t.ref->arguments.n;i++){
            if(i)snprintf(out+strlen(out),cap-strlen(out),", ");
            int mode=parameter_mode(t.ref,i);snprintf(out+strlen(out),cap-strlen(out),"%s",mode==1?"own ":mode==2?"borrow ":mode==3?"borrow mut ":"");type_spelling(*(Type*)t.ref->arguments.v[i],out+strlen(out),cap-strlen(out));
        }
        snprintf(out+strlen(out),cap-strlen(out),"): ");
        if(t.ref->result_mode==1)snprintf(out+strlen(out),cap-strlen(out),"own ");
        if(t.ref->result_mode>=2)snprintf(out+strlen(out),cap-strlen(out),"borrow %s(%d) ",t.ref->result_mode==3?"mut":"",t.ref->result_from);
        type_spelling(*t.ref->result,out+strlen(out),cap-strlen(out));return;
    }
    snprintf(out+strlen(out),cap-strlen(out),"%s",type_base(t));
}
static const char *type_name(Type t) {
    static char buffers[4][4096];static unsigned turn;char *out=buffers[(turn++)%4];
    type_spelling(t,out,4096);return out;
}
static Token *peek(void){return tokens.v[cursor];}
static Token *take(void){Token *t=peek();if(t->kind!=T_EOF)cursor++;return t;}
static bool accept(int kind){if(peek()->kind==kind){take();return true;}return false;}
static Token *expect(int kind){Token *t=peek();if(t->kind!=kind)error(t,"esperado %s; encontrado '%s'",kind==T_ID?"identificador":kind<128?(char[2]){(char)kind,0}:"outro token",t->text);return take();}
static Node *node(int kind,Token *t){Node *n=mem(sizeof(*n));n->kind=kind;n->t=t;return n;}
typedef struct {Type key,value;bool map;char *name,*display;TypeRef *ref;Token *site;Class *instance;} Collection;
static Vec collections;
static const char *collection_display(const char *name){for(int i=0;i<collections.n;i++){Collection *c=collections.v[i];if(same(c->name,name))return c->display;}for(int i=0;i<classes.n;i++){Class *c=classes.v[i];if(same(c->t->text,name)&&c->display)return c->display;}return name;}
static Type collection_type(Type key,Type value,bool map,Token *where){
    if((key.kind==TY_VOID)||(map&&value.kind==TY_VOID))error(where,"coleções não aceitam void");
    if(map&&(key.depth||(key.kind!=TY_STR&&!integer(key)&&key.kind!=TY_BOOL)))error(where,"chave de HashMap deve ser text, int, byte ou bool (incluindo larguras inteiras explícitas)");
    for(int i=0;i<collections.n;i++){Collection *c=collections.v[i];if(c->map==map&&type_identity(c->key)==type_identity(key)&&(!map||type_identity(c->value)==type_identity(value)))return (Type){TY_OBJ,0,c->name,c->ref};}
    if(collections.n>=256)error(where,"limite de 256 especializações de coleções excedido");
    Collection *c=mem(sizeof(*c));c->key=key;c->value=value;c->map=map;c->site=where;c->ref=mem(sizeof(*c->ref));c->ref->definition=++next_definition;char name[64];snprintf(name,sizeof(name),"__assis_%s_%d",map?"map":"array",collections.n);c->name=copy(name,strlen(name));
    const char *kn=type_name(key),*vn=map?type_name(value):"";size_t n=strlen(kn)+strlen(vn)+32;c->display=mem(n);snprintf(c->display,n,map?"HashMap<%s, %s>":"Array<%s>",kn,vn);push(&collections,c);
    return (Type){TY_OBJ,0,c->name,c->ref};
}
static Collection *collection_of(Type t){if(t.depth||t.kind!=TY_OBJ)return NULL;for(int i=0;i<collections.n;i++){Collection *c=collections.v[i];if(same(c->name,t.name))return c;}return NULL;}
static void generic_end(void){
    if(peek()->kind==T_GE||peek()->kind==T_SHRSET){Token *t=peek();bool pair=t->kind==T_SHRSET;t->kind=pair?T_GE:'=';t->text=pair?">=":"=";t->at++;t->col++;return;}
    if(peek()->kind==T_SHR){Token *t=peek();t->kind='>';t->text=">";t->at++;t->col++;return;}expect('>');
}
static Type parse_type(void);
static Type *type_copy(Type t){Type *out=mem(sizeof(*out));*out=t;return out;}
#include "namespaces.h"
static int parse_ownership(void){if(accept(T_OWN))return 1;if(accept(T_BORROW))return accept(T_MUT)?3:2;return 0;}
static int parse_result_mode(Token **source,bool indexed,int *index){
    int mode=parse_ownership();if(mode>=2){expect('(');Token *t=peek()->kind==T_SELF?take():expect(indexed?T_INT:T_ID);expect(')');if(indexed){if(t->number>INT_MAX)error(t,"índice de vida inválido");*index=t->kind==T_SELF?-1:(int)t->number;}else *source=t;}return mode;
}
static Type function_type(Function *f){
    TypeRef *ref=mem(sizeof(*ref));ref->origin=f->t;ref->pure=f->pure;ref->safe=f->safe||f->pure;ref->result=type_copy(f->result);
    ref->result_mode=f->result_mode;ref->result_from=f->result_from;ref->receiver_mode=f->receiver_mode;
    for(int i=0;i<f->params.n;i++){Var *p=f->params.v[i];push(&ref->arguments,type_copy(p->ty));push(&ref->modes,(void*)(intptr_t)p->ownership);}
    return (Type){TY_FN,0,NULL,ref};
}
static void parse_type_args(Vec *out){expect('<');do{push(out,type_copy(parse_type()));}while(accept(','));generic_end();}
static Type applied_type(Token *t,Vec arguments){TypeRef *ref=mem(sizeof(*ref));ref->origin=t;ref->arguments=arguments;return (Type){TY_APPLY,0,t->text,ref};}
static Type parse_type(void){
    if(++parse_depth>MAX_NEST)error(peek(),"tipo aninhado demais");
    int depth=0;while(accept('*')){if(++depth>64)error(peek(),"ponteiro aninhado demais");}
    Token *t=take();Type ty;
    if(t->kind==T_I64)ty=type_i64;else if(t->kind==T_U8)ty=type_u8;else if(t->kind==T_BOOL)ty=type_bool;
    else if(t->kind==T_TEXT)ty=type_str;else if(t->kind==T_VOID)ty=type_void;
    else if(t->kind==T_FILE)ty=type_file;
    else if(t->kind==T_SLICE){TypeRef *ref=mem(sizeof(*ref));ref->origin=t;parse_type_args(&ref->arguments);if(ref->arguments.n!=1)error(t,"slice exige um argumento de tipo");ty=(Type){TY_SLICE,0,NULL,ref};}
    else if(t->kind==T_NUMTYPE)ty=numeric_type(t->text);
    else if(t->kind==T_FN||t->kind==T_PURE||t->kind==T_SAFE||t->kind==T_CLOSURE){
        TypeRef *ref=mem(sizeof(*ref));ref->origin=t;ref->pure=t->kind==T_PURE;ref->closure=t->kind==T_CLOSURE;ref->safe=ref->pure||ref->closure||t->kind==T_SAFE;if(ref->safe&&!ref->closure)expect(T_FN);
        if(ref->closure)ref->receiver_mode=accept(T_MUT)?3:2;
        expect('(');if(peek()->kind!=')'){do{int mode=parse_ownership();push(&ref->modes,(void*)(intptr_t)mode);push(&ref->arguments,type_copy(parse_type()));}while(accept(','));}
        expect(')');expect(':');ref->result_mode=parse_result_mode(NULL,true,&ref->result_from);ref->result=type_copy(parse_type());ty=(Type){TY_FN,0,NULL,ref};
    }
    else if(t->kind==T_ID){
        t=qualified_token(t);
        ty=(Type){TY_OBJ,0,t->text,NULL};
        for(int i=0;i<type_parameters.n;i++){TypeParameter *p=type_parameters.v[i];if(same(t->text,p->t->text)){TypeRef *ref=mem(sizeof(*ref));ref->definition=p->id;ref->origin=t;ty=(Type){TY_VAR,0,t->text,ref};break;}}
        if(peek()->kind=='<'){if(ty.kind==TY_VAR)error(t,"parâmetro de tipo não aceita argumentos de tipo");Vec arguments={0};parse_type_args(&arguments);ty=applied_type(t,arguments);}
    }else {error(t,"esperado um tipo AssisScript");}
    ty.depth=depth;parse_depth--;return ty;
}
static Node *expression(int minimum);static Node *statement(void);static Node *block(void);
static void args(Vec *out){expect('(');if(peek()->kind!=')'){do{push(out,expression(1));}while(accept(','));}expect(')');}
static int precedence(int k){switch(k){case T_OR:return 1;case T_AND:return 2;case '|':return 3;case '^':return 4;case '&':return 5;case T_EQ:case T_NE:return 6;case '<':case '>':case T_LE:case T_GE:return 7;case T_SHL:case T_SHR:return 8;case '+':case '-':return 9;case '*':case '/':case '%':return 10;default:return 0;}}
static Node *parse_closure(Token *t);
static Node *prefix(void){
    if(++parse_depth>MAX_NEST)error(peek(),"expressão aninhada demais");
    Token *t=take();Node *n=NULL;
    switch(t->kind){
    case T_CLOSURE:n=parse_closure(t);break;
    case T_INC:case T_DEC:error(t,"++ e -- são instruções sem valor; use em uma instrução própria ou no passo do for");break;
    case '-':case '+':case '!':case '~':case '*':case '&':n=node(N_UNARY,t);n->op=t->kind;n->a=prefix();break;
    case T_CHAR:case T_REAL:n=node(N_INT,t);break;case T_INT:n=node(N_INT,t);break;case T_STR:n=node(N_STR,t);break;
    case T_TRUE:case T_FALSE:n=node(N_BOOL,t);break;case T_NULL:n=node(N_NULL,t);break;
    case T_SUPER:case T_SELF:n=node(N_SELF,t);n->op=t->kind;break;case T_ID:n=node(N_NAME,qualified_token(t));break;
    case T_NEW:n=node(N_NEW,t);n->decl=parse_type();if((n->decl.kind!=TY_OBJ&&n->decl.kind!=TY_APPLY)||n->decl.depth)error(t,"new exige classe, struct ou coleção");if(accept('.'))n->variant_name=expect(T_ID);args(&n->items);break;
    case T_BUFFER:n=node(N_BUILTIN,t);n->op=t->kind;expect('<');n->decl=parse_type();generic_end();args(&n->items);break;
    case '[':n=node(N_ARRAY,t);if(peek()->kind!=']'){do{push(&n->items,expression(1));}while(accept(',')&&peek()->kind!=']');}expect(']');break;
    case T_NUMTYPE:n=node(N_BUILTIN,t);n->op=T_NUMTYPE;n->decl=numeric_type(t->text);args(&n->items);break;
    case T_UTF8:case T_C_CALLBACK:case T_SLICE_MAKE:case T_ALLOC:case T_LEN:case T_I64:case T_U8:case T_BOOL:case T_TEXT:case T_BYTES:case T_MOVE:case T_READ:case T_NOW:n=node(N_BUILTIN,t);n->op=t->kind;args(&n->items);break;
    case T_WRITE_BYTES:case T_SLEEP:case T_CIVIL:case T_FILE_SYNC:case T_FILE_REPLACE:case T_FILE_REMOVE:case T_FILE_OPEN:case T_FILE_READ:case T_FILE_WRITE:case T_FILE_CLOSE:case T_IO_ERROR:case T_ARGC:case T_ARG_LEN:case T_ARG_COPY:n=node(N_BUILTIN,t);n->op=t->kind;args(&n->items);break;
    case '(':n=expression(1);expect(')');break;
    default:error(t,"esperada uma expressão; encontrado '%s'",t->text);
    }
    for(;;){
        if(accept(':')){expect(':');if(n->kind!=N_NAME||n->specialized)error(n->t,"::<...> exige nome de função global");n->specialized=true;parse_type_args(&n->type_args);}
        else if(peek()->kind=='('){Node *c=node(N_CALL,n->t);c->a=n;args(&c->items);n=c;}
        else if(accept('.')){Node *m=node(N_MEMBER,expect(T_ID));m->a=n;n=m;}
        else if(accept('[')){Node *i=node(N_INDEX,n->t);i->a=n;i->b=expression(1);expect(']');n=i;}
        else break;
    }
    parse_depth--;return n;
}
static Node *expression(int minimum){
    Node *left=prefix();
    while(precedence(peek()->kind)>=minimum||((peek()->kind==T_IS||peek()->kind==T_AS)&&minimum<=7)){
        Token *t=take();
        if(t->kind==T_IS||t->kind==T_AS){Node *n=node(t->kind==T_IS?N_IS:N_CAST,t);n->a=left;n->decl=parse_type();left=n;}
        else{Node *n=node(N_BINARY,t);n->op=t->kind;n->a=left;n->b=expression(precedence(t->kind)+1);left=n;}
    }
    return left;
}
static bool assignment(int k){return k=='='||(k>=T_ADDSET&&k<=T_SHRSET);}
static Node *simple_statement(void){
    Token *t=peek(),*update=NULL;
    if(t->kind==T_INC||t->kind==T_DEC)update=take();
    Node *left=expression(1),*n;
    if(!update&&(peek()->kind==T_INC||peek()->kind==T_DEC))update=take();
    if(update){
        n=node(N_ASSIGN,update);n->op=update->kind==T_INC?T_ADDSET:T_SUBSET;n->a=left;
        Token *one=mem(sizeof(*one));*one=*update;one->kind=T_INT;one->text="1";one->number=1;
        n->b=node(N_BUILTIN,update);n->b->op=T_NUMTYPE;push(&n->b->items,node(N_INT,one));
    }else if(assignment(peek()->kind)){t=take();n=node(N_ASSIGN,t);n->op=t->kind;n->a=left;n->b=expression(1);}
    else{n=node(N_EXPR,t);n->a=left;}
    return n;
}
static Node *block(void){
    if(++parse_depth>MAX_NEST)error(peek(),"bloco aninhado demais");
    Node *n=node(N_BLOCK,expect('{'));while(peek()->kind!='}'&&peek()->kind!=T_EOF)push(&n->items,statement());expect('}');parse_depth--;return n;
}
static Node *statement_inner(void){
    Token *t=peek();Node *n;
    if(t->kind=='{')return block();
    if(accept(T_MATCH)){
        n=node(N_MATCH,t);expect('(');n->a=expression(1);expect(')');expect('{');
        while(peek()->kind!='}'&&peek()->kind!=T_EOF){
            Node *arm=node(N_ARM,expect(T_ID));
            if(accept('(')){if(peek()->kind!=')')do{push(&arm->items,node(N_NAME,expect(T_ID)));}while(accept(','));expect(')');}
            arm->a=block();push(&n->items,arm);
        }
        expect('}');return n;
    }
    if(accept(T_UNSAFE)){n=node(N_UNSAFE,t);n->a=block();return n;}
    if(accept(T_DIV))return block();
    if(t->kind==T_LET||t->kind==T_VAL||t->kind==T_OWN||t->kind==T_BORROW){
        take();int ownership=t->kind==T_OWN?1:t->kind==T_BORROW?2:0;
        if(ownership==2&&accept(T_MUT))ownership=3;
        Token *name=expect(T_ID);n=node(N_LET,name);n->ownership=ownership;n->immutable=t->kind==T_VAL;
        expect(':');n->decl=parse_type();expect('=');n->a=expression(1);expect(';');return n;
    }
    if(accept(T_DEFER)){n=node(N_DEFER,t);expect(T_FREE);Vec a={0};args(&a);if(a.n!=1)error(t,"defer free recebe um argumento");n->a=a.v[0];free(a.v);expect(';');return n;}
    if(accept(T_FOR)){
        expect('(');Node *scope=node(N_BLOCK,t);Node *init=statement();
        if(init->kind!=N_LET&&init->kind!=N_ASSIGN&&init->kind!=N_EXPR)error(init->t,"for exige declaração, atribuição ou expressão na inicialização");push(&scope->items,init);
        Node *loop=node(N_WHILE,t);loop->a=expression(1);expect(';');
        loop->step=simple_statement();if(loop->step->kind!=N_ASSIGN)error(loop->step->t,"for exige atribuição, ++ ou -- no incremento");expect(')');
        loop->b=block();push(&scope->items,loop);return scope;
    }
    if(accept(T_IF)){n=node(N_IF,t);expect('(');n->a=expression(1);expect(')');n->b=block();if(accept(T_ELSE))n->c=peek()->kind==T_IF?statement():block();return n;}
    if(accept(T_WHILE)){n=node(N_WHILE,t);expect('(');n->a=expression(1);expect(')');n->b=block();return n;}
    if(accept(T_RETURN)){n=node(N_RETURN,t);if(peek()->kind!=';')n->a=expression(1);expect(';');return n;}
    if(t->kind==T_PRINT||(t->kind==T_ID&&same(t->text,"write")&&cursor+1<tokens.n&&((Token*)tokens.v[cursor+1])->kind=='(')){take();n=node(N_PRINT,t);n->op=t->kind==T_PRINT?T_PRINT:T_WRITE;args(&n->items);expect(';');return n;}
    if(accept(T_FREE)){n=node(N_FREE,t);Vec a={0};args(&a);if(a.n!=1)error(t,"free recebe exatamente um argumento");n->a=a.v[0];free(a.v);expect(';');return n;}
    if(accept(T_ASSERT)){n=node(N_EXPR,t);n->a=node(N_BUILTIN,t);n->a->op=T_ASSERT;args(&n->a->items);expect(';');return n;}
    if(accept(T_BREAK)||accept(T_CONTINUE)){n=node(t->kind==T_BREAK?N_BREAK:N_CONTINUE,t);expect(';');return n;}
    n=simple_statement();expect(';');return n;
}
static Node *statement(void){
    if(++parse_depth>MAX_NEST)error(peek(),"instrução aninhada demais");
    Node *n=statement_inner();parse_depth--;return n;
}
static void parse_type_params(Vec *out){
    if(!accept('<'))return;
    do{TypeParameter *p=mem(sizeof(*p));p->t=expect(T_ID);p->id=++next_definition;
        if(same(p->t->text,"Array")||same(p->t->text,"HashMap"))error(p->t,"nome de coleção reservado");
        for(int i=0;i<out->n;i++)if(same(((TypeParameter*)out->v[i])->t->text,p->t->text))error(p->t,"parâmetro de tipo declarado duas vezes");
        if(out->n>=16)error(p->t,"limite de 16 parâmetros de tipo excedido");push(out,p);
    }while(accept(','));generic_end();
}
static bool parsing_foreign;
static Function *parse_function_named(Class *owner,Token *name){
    Function *f=mem(sizeof(*f));f->t=name?name:expect(T_ID);f->id=++next_definition;f->owner=owner;Vec previous=type_parameters;
    parse_type_params(&f->type_params);if(owner&&f->type_params.n)error(f->t,"métodos genéricos ainda não são suportados");type_parameters=owner?owner->type_params:f->type_params;expect('(');
    if(peek()->kind!=')'){do{Var *v=mem(sizeof(*v));v->ownership=parse_ownership();if(owner&&peek()->kind==T_SELF){Token *self=take();if(f->params.n||f->receiver_mode||v->ownership<2)error(self,"receptor exige borrow self ou borrow mut self na primeira posição");f->receiver_mode=v->ownership;f->safe=true;}else{v->t=expect(T_ID);expect(':');v->ty=parse_type();push(&f->params,v);}}while(accept(','));}
    expect(')');expect(':');f->result_mode=parse_result_mode(&f->result_source,false,&f->result_from);
    if(f->result_source){f->result_from=-1;for(int i=0;i<f->params.n;i++)if(same(((Var*)f->params.v[i])->t->text,f->result_source->text))f->result_from=i;if(f->result_from<0&&!(owner&&f->result_source->kind==T_SELF&&(f->receiver_mode||owner->closure)))error(f->result_source,"origem de vida deve nomear um parâmetro borrow ou self gerenciado");}
    f->result=parse_type();f->foreign=parsing_foreign;if(f->foreign){expect(';');f->body=node(N_BLOCK,f->t);}else f->body=block();type_parameters=previous;if(!f->type_params.n&&!(owner&&owner->type_params.n))push(&all_functions,f);return f;
}
static Function *parse_function(Class *owner){return parse_function_named(owner,NULL);}
static Node *parse_closure(Token *t){
    bool mutable=accept(T_MUT);Class *c=mem(sizeof(*c));c->closure=true;c->sealed=true;c->id=++next_definition;c->type_params=type_parameters;
    c->t=mem(sizeof(*t));*c->t=*t;char name[64];snprintf(name,sizeof(name),"__assis_closure_%u",c->id);c->t->text=copy(name,strlen(name));
    Node *n=node(N_NEW,t);expect('[');
    if(peek()->kind!=']')do{
        Field *f=mem(sizeof(*f));f->owner=c;f->private=true;
        if(accept(T_OWN))f->owned=true;else if(accept(T_BORROW)){f->borrowed=true;if(peek()->kind==T_MUT)error(peek(),"captura borrow aceita somente empréstimo compartilhado");}else expect(T_VAL);
        f->t=expect(T_ID);expect(':');f->ty=parse_type();expect('=');push(&n->items,expression(1));push(&c->own_fields,f);
        if(c->own_fields.n>64)error(t,"closure aceita até 64 capturas");
    }while(accept(','));expect(']');
    Token *invoke=mem(sizeof(*t));*invoke=*t;invoke->kind=T_ID;invoke->text="__invoke";
    Function *f=parse_function_named(c,invoke);if(f->receiver_mode)error(t,"receptor de closure é implícito");f->receiver_mode=mutable?3:2;f->safe=true;push(&c->own_methods,f);
    if(c->type_params.n){Vec args={0};for(int i=0;i<c->type_params.n;i++){TypeParameter *p=c->type_params.v[i];TypeRef *r=mem(sizeof(*r));r->definition=p->id;push(&args,type_copy((Type){TY_VAR,0,p->t->text,r}));}n->decl=applied_type(c->t,args);push(&generic_classes,c);}
    else{n->decl=(Type){TY_OBJ,0,c->t->text,NULL};push(&classes,c);}return n;
}
static void parse(void){
    while(peek()->kind!=T_EOF){
        if(accept(T_FILE_END))continue;
        if(accept(T_CONST)){
            GlobalConstant *g=mem(sizeof(*g));g->t=expect(T_ID);expect(':');g->ty=parse_type();expect('=');g->value=expression(1);expect(';');push(&global_constants,g);continue;
        }
        if(peek()->kind==T_CLASS||peek()->kind==T_STRUCT||same(peek()->text,"value")||same(peek()->text,"final")||peek()->kind==T_ENUM){
            bool sealed=same(peek()->text,"final");if(sealed){take();if(peek()->kind!=T_CLASS)error(peek(),"final exige class");}
            bool value=same(peek()->text,"value");if(value){take();if(peek()->kind!=T_STRUCT)error(peek(),"value exige struct");}bool tagged=peek()->kind==T_ENUM;
            bool record=take()->kind!=T_CLASS;if(value&&!record)error(peek(),"value exige struct");Class *c=mem(sizeof(*c));c->record=record;c->value=value||tagged;c->tagged=tagged;c->sealed=sealed;c->t=expect(T_ID);c->id=++next_definition;
            if(same(c->t->text,"Array")||same(c->t->text,"HashMap"))error(c->t,"nome de coleção reservado");
            Vec previous=type_parameters;parse_type_params(&c->type_params);type_parameters=c->type_params;
            if(accept(T_EXTENDS)){if(record)error(c->t,"struct não admite herança");c->base_name=peek();c->base_type=parse_type();if((c->base_type.kind!=TY_OBJ&&c->base_type.kind!=TY_APPLY)||c->base_type.depth)error(c->base_name,"herança exige classe nominal");}expect('{');
            while(peek()->kind!='}'&&peek()->kind!=T_EOF){
                if(tagged){Variant *v=mem(sizeof(*v));v->t=expect(T_ID);v->tag=c->variants.n;
                    for(int i=0;i<c->variants.n;i++)if(same(((Variant*)c->variants.v[i])->t->text,v->t->text))error(v->t,"variante duplicada");
                    if(c->variants.n>=256)error(v->t,"limite de 256 variantes excedido");
                    if(accept('(')){if(peek()->kind!=')')do{Field *f=mem(sizeof(*f));f->owned=accept(T_OWN);f->t=peek();f->owner=c;f->ty=parse_type();if(f->owned)c->value=false;push(&v->fields,f);}while(accept(','));expect(')');}
                    expect(';');push(&c->variants,v);continue;
                }
                bool hidden=accept(T_PRIVATE);
                if(peek()->kind==T_LET||peek()->kind==T_OWN){bool owned=take()->kind==T_OWN;Field *f=mem(sizeof(*f));f->owned=owned;f->t=expect(T_ID);f->owner=c;f->private=hidden;expect(':');f->ty=parse_type();expect(';');push(&c->own_fields,f);}
                else if(accept(T_FN)){if(record)error(c->t,"struct declara somente campos; use class para métodos");Function *f=parse_function(c);f->private=hidden;push(&c->own_methods,f);}
                else error(peek(),"classe aceita campos let/own e métodos fn");
            }
            expect('}');if(tagged&&!c->variants.n)error(c->t,"enum exige ao menos uma variante");type_parameters=previous;push(c->type_params.n?&generic_classes:&classes,c);
        }else if(accept(T_EXTERN)){
            expect('(');Token *linux_name=expect(T_STR);expect(',');Token *windows_name=expect(T_STR);expect(',');Token *symbol=expect(T_STR);expect(')');expect(T_FN);
            Token *names[]={linux_name,windows_name,symbol};for(int i=0;i<3;i++)if(!names[i]->len||names[i]->len>4096||strlen(names[i]->str)!=names[i]->len)error(names[i],"extern exige nomes não vazios, sem NUL e até 4096 bytes");
            parsing_foreign=true;Function *f=parse_function(NULL);parsing_foreign=false;
            if(f->type_params.n)error(f->t,"extern não aceita parâmetros de tipo");
            f->foreign_library[0]=linux_name->str;f->foreign_library[1]=windows_name->str;f->foreign_symbol=symbol->str;push(&functions,f);
        }else if(accept(T_SAFE)){expect(T_FN);Function *f=parse_function(NULL);f->safe=true;push(f->type_params.n?&generic_functions:&functions,f);
        }else if(accept(T_PURE)){expect(T_FN);Function *f=parse_function(NULL);f->pure=true;push(f->type_params.n?&generic_functions:&functions,f);
        }else if(accept(T_FN)){Function *f=parse_function(NULL);push(f->type_params.n?&generic_functions:&functions,f);}
        else error(peek(),"no topo use const para constante, class, struct, enum ou fn para função");
    }
}

#include "collections.h"

static Class *find_class(const char *name){for(int i=0;i<classes.n;i++){Class *c=classes.v[i];if(same(c->t->text,name))return c;}return NULL;}
static Function *find_fn(const char *name){for(int i=0;i<functions.n;i++){Function *f=functions.v[i];if(same(f->t->text,name))return f;}return NULL;}
static Field *find_field(Class *c,const char *name){for(int i=0;i<c->fields.n;i++){Field *f=c->fields.v[i];if(same(f->t->text,name))return f;}return NULL;}
static Function *find_method(Class *c,const char *name,int *slot){for(int i=0;i<c->methods.n;i++){Function *f=c->methods.v[i];if(same(f->t->text,name)){if(slot)*slot=i;return f;}}return NULL;}
static bool object(Type t){return t.depth==0&&t.kind==TY_OBJ;}
static bool closure_type(Type t){return !t.depth&&t.kind==TY_FN&&t.ref->closure;}
static bool value_type(Type t){Class *c=object(t)?find_class(t.name):NULL;return c&&c->value;}
static bool inline_type(Type t){return value_type(t)||slice_type(t);}
static bool declared_value_type(Type t){
    if(value_type(t))return true;if(t.depth)return false;
    for(int i=0;i<generic_classes.n;i++){Class *c=generic_classes.v[i];if(same(c->t->text,t.name))return c->value;}return false;
}
static bool pointer_like(Type t){return t.depth>0||closure_type(t)||equal_type(t,type_file)||(object(t)&&!value_type(t));}
static bool numeric(Type t){return integer(t);}
static bool function_value(Type t){return !t.depth&&t.kind==TY_FN;}
static int value_layout_depth;
static int value_bytes(Type t);
static void layout_value(Class *c){
    if((!c->value&&!c->tagged)||c->value_state==2)return;
    if(c->value_state==1)error(c->t,"ciclo de layout por valor; use recurso own para recursão");
    if(++value_layout_depth>64)error(c->t,"limite de 64 níveis de valores excedido");c->value_state=1;
    int size=c->tagged?8:0;
    for(int k=0;k<(c->tagged?c->variants.n:1);k++){
        Vec fields=c->tagged?((Variant*)c->variants.v[k])->fields:c->own_fields;int offset=c->tagged?8:0;
        for(int i=0;i<fields.n;i++){
            Field *f=fields.v[i];Type t=f->ty;
            if((f->owned&&c->value)||(!f->owned&&!numeric(t)&&!floating(t)&&!equal_type(t,type_bool)&&!value_type(t)&&!(function_value(t)&&t.ref->pure)))error(f->t,"valor Copy exige campos escalares, funções pure ou valores Copy; referências/own não são permitidos");
            int bytes=value_bytes(t);f->offset=offset;offset+=(bytes+7)&~7;
            if(offset>4096)error(f->t,"layout por valor excede 4096 bytes");
        }
        if(offset>size)size=offset;
    }
    c->size=size?size:8;c->value_state=2;value_layout_depth--;
}
static int value_bytes(Type t){if(slice_type(t))return 16;if(value_type(t)){Class *c=find_class(t.name);layout_value(c);return c->size;}return scalar_bytes(t);}
static bool pure_contract(Type t,bool symbolic){
    if(numeric(t)||floating(t)||equal_type(t,type_bool)||(symbolic&&!t.depth&&t.kind==TY_VAR))return true;
    if(declared_value_type(t))return true;
    if(!function_value(t)||t.ref->closure||!t.ref->pure||!pure_contract(*t.ref->result,symbolic))return false;
    for(int i=0;i<t.ref->arguments.n;i++)if(!pure_contract(*(Type*)t.ref->arguments.v[i],symbolic))return false;
    return true;
}
static bool pure_value(Type t){return pure_contract(t,false);}
static bool isvoid(Type t){return equal_type(t,type_void);}
static bool assignable(Type target,Type value){
    if(equal_type(target,value))return true;
    if(function_value(target)&&function_value(value)){
        if(target.ref->pure&&!value.ref->pure)return false;
        if(target.ref->safe&&!value.ref->safe)return false;
        if(target.ref->arguments.n!=value.ref->arguments.n||!same_modes(target.ref,value.ref)||!equal_type(*target.ref->result,*value.ref->result))return false;
        for(int i=0;i<target.ref->arguments.n;i++)if(!equal_type(*(Type*)target.ref->arguments.v[i],*(Type*)value.ref->arguments.v[i]))return false;
        return true;
    }
    if(equal_type(target,type_i64)&&equal_type(value,type_u8))return true;
    if(equal_type(value,type_null))return pointer_like(target);
    if(object(target)&&object(value)){
        Class *c=find_class(value.name);for(c=c?c->base:NULL;c;c=c->base)if(same(c->t->text,target.name))return true;
    }
    return false;
}
static void require_assign(Type target,Type value,Token *t){if(!assignable(target,value))error(t,"não é possível usar %s como %s",type_name(value),type_name(target));}
static void valid_type(Type t,Token *where,bool result){
    if(t.kind==TY_SLICE){Type element=slice_element(t);valid_type(element,where,false);if(t.depth||(!numeric(element)&&!floating(element)&&!equal_type(element,type_bool)&&!value_type(element)))error(where,"slice exige elementos Copy sem referências e não aceita ponteiro externo");}
    if(t.kind==TY_OBJ&&!find_class(t.name))error(where,"tipo desconhecido: %s",type_name(t));
    if(t.kind==TY_VOID&&(t.depth||!result))error(where,"void só pode ser retorno de função/método");
    if(t.kind==TY_FN){
        valid_type(*t.ref->result,where,true);
        for(int i=0;i<t.ref->arguments.n;i++)valid_type(*(Type*)t.ref->arguments.v[i],where,false);
        Type value=t;value.depth=0;
        if(t.ref->result_mode>=2){int from=t.ref->result_from;int mode=from==-1?t.ref->receiver_mode:from>=0&&from<t.ref->arguments.n?parameter_mode(t.ref,from):0;if(mode<2||(t.ref->result_mode==3&&mode!=3))error(where,"retorno borrow exige origem borrow compatível na assinatura");}
        if(t.ref->result_mode&&!pointer_like(*t.ref->result)&&!slice_type(*t.ref->result)&&!equal_type(*t.ref->result,type_str))error(where,"contrato de propriedade exige referência");
        for(int i=0;i<t.ref->arguments.n;i++)if(parameter_mode(t.ref,i)&&!pointer_like(*(Type*)t.ref->arguments.v[i])&&!slice_type(*(Type*)t.ref->arguments.v[i])&&!equal_type(*(Type*)t.ref->arguments.v[i],type_str))error(where,"contrato de propriedade exige referência");
        if(slice_type(*t.ref->result)&&t.ref->result_mode<2)error(where,"slice exige retorno borrow com origem explícita");
        for(int i=0;i<t.ref->arguments.n;i++)if(slice_type(*(Type*)t.ref->arguments.v[i])&&parameter_mode(t.ref,i)<2)error(where,"slice exige parâmetro borrow");
        if(t.ref->pure&&!pure_value(value))error(where,"tipo de função pure exige int, byte, bool ou funções pure nos parâmetros e retorno");
    }
}
static bool c_scalar(Type t){return t.depth||(integer(t)||floating(t)||equal_type(t,type_bool)||equal_type(t,type_str));}
static void c_signature(Function *f,bool callback){
    if(f->params.n>64)error(f->t,"ABI C aceita até 64 argumentos");
    if(f->owner||f->type_params.n||f->result_mode||(!isvoid(f->result)&&!c_scalar(f->result)))error(f->t,"ABI C exige função global e retorno escalar sem ownership");
    for(int i=0;i<f->params.n;i++){Var *v=f->params.v[i];if(!c_scalar(v->ty)||v->ownership==1||(callback&&v->ownership)||(!v->ty.depth&&v->ownership))error(v->t,"ABI C exige escalares ou ponteiros; own e agregados por valor não são suportados");}
}
static void signature(Function *f){
    valid_type(f->result,f->t,true);
    valid_type(function_type(f),f->t,true);
    if(f->pure&&!pure_value(f->result))error(f->t,"pure exige retorno int, byte, bool ou função pure nesta etapa");
    for(int i=0;i<f->params.n;i++){Var *v=f->params.v[i];valid_type(v->ty,v->t,false);for(int j=0;j<i;j++){Var *old=f->params.v[j];if(same(old->t->text,v->t->text))error(v->t,"parâmetro declarado duas vezes");}}
    if(f->pure)for(int i=0;i<f->params.n;i++){Var *v=f->params.v[i];if(!pure_value(v->ty))error(v->t,"parâmetro pure exige int, byte, bool ou função pure nesta etapa");v->immutable=true;}
    if(f->foreign)c_signature(f,false);
}
static int layout_depth;
static void layout(Class *c){
    if(c->state==2)return;if(c->state==1)error(c->t,"ciclo de herança detectado");c->state=1;
    if(++layout_depth>MAX_NEST)error(c->t,"hierarquia de classes aninhada demais");
    if(c->value||c->tagged)layout_value(c);else c->size=8;
    if(c->base_name){
        if(c->base&&c->base->sealed)error(c->base_name,"classe final não admite herança");
        if(!c->base)error(c->base_name,"classe base desconhecida");if(c->base->record)error(c->base_name,"struct não pode ser classe base");layout(c->base);
        for(int i=0;i<c->base->fields.n;i++)push(&c->fields,c->base->fields.v[i]);
        for(int i=0;i<c->base->methods.n;i++)push(&c->methods,c->base->methods.v[i]);
        c->size=c->base->size;
    }
    for(int i=0;i<c->own_fields.n;i++){
        Field *f=c->own_fields.v[i];valid_type(f->ty,f->t,false);
        if(slice_type(f->ty)&&!(c->closure&&f->borrowed))error(f->t,"slice não pode ser armazenado em campo sem contrato de vida");
        if(find_field(c,f->t->text)||find_method(c,f->t->text,NULL))error(f->t,"campo duplicado ou em conflito com membro herdado");
        if(!c->value){f->offset=c->size;c->size+=(value_bytes(f->ty)+7)&~7;}
        f->slot=c->fields.n;push(&c->fields,f);
    }
    for(int i=0;i<c->own_methods.n;i++){
        Function *f=c->own_methods.v[i];signature(f);
        if(same(f->t->text,"drop")&&(!c->sealed||f->receiver_mode!=3||f->params.n||!isvoid(f->result)))error(f->t,"drop exige final class, borrow mut self, zero argumentos e retorno void");
        if(find_field(c,f->t->text))error(f->t,"método em conflito com campo");
        for(int j=0;j<i;j++){Function *old=c->own_methods.v[j];if(same(old->t->text,f->t->text))error(f->t,"método declarado duas vezes");}
        if(same(f->t->text,CTOR)&&!isvoid(f->result))error(f->t,"inicializador init deve retornar void");
        int slot=-1;Function *old=find_method(c,f->t->text,&slot);
        if(old&&same(f->t->text,CTOR)){c->methods.v[slot]=f;}else if(old){
            if(old->receiver_mode!=f->receiver_mode)error(f->t,"sobrescrita deve manter o contrato de receptor");
            if(old->private||f->private)error(f->t,"método privado não pode participar de sobrescrita");
            if(old->params.n!=f->params.n||!equal_type(old->result,f->result)||!same_modes(function_type(old).ref,function_type(f).ref))error(f->t,"sobrescrita deve manter a assinatura");
            for(int j=0;j<f->params.n;j++)if(!equal_type(((Var*)f->params.v[j])->ty,((Var*)old->params.v[j])->ty))error(f->t,"sobrescrita deve manter os tipos dos parâmetros");
            c->methods.v[slot]=f;
        }else push(&c->methods,f);
    }
    c->state=2;layout_depth--;
}
#include "generics.h"
static Vec bindings;static Function *checking;static int scope_start,loop_depth,check_depth;
static Var *lookup(const char *name){for(int i=bindings.n-1;i>=0;i--){Var *v=bindings.v[i];if(same(v->t->text,name))return v;}return NULL;}
static void allocate_slot(Var *v){
    int words=inline_type(v->ty)?value_bytes(v->ty)/8:1;
    if(checking->slots>2097152-words-2)error(v->t,"frame de função excede o limite de 16 MiB");
    v->slot=checking->slots+words-1+(checking->owner?1:0);checking->slots+=words;v->length_slot=-1;v->reg=-1;push(&checking->vars,v);
}
static Var *temporary_value(Type t,Token *site){Var *v=mem(sizeof(*v));v->t=site;v->ty=t;allocate_slot(v);return v;}
static void declare(Var *v){
    for(int i=scope_start;i<bindings.n;i++){Var *old=bindings.v[i];if(same(old->t->text,v->t->text))error(v->t,"variável já declarada neste escopo");}
    allocate_slot(v);push(&bindings,v);
    if(equal_type(v->ty,type_str)){
        Var *length=mem(sizeof(*length));length->t=v->t;length->ty=type_i64;length->reg=-1;
        length->slot=checking->slots+++(checking->owner?1:0);v->length_slot=length->slot;push(&checking->vars,length);
    }
}
static Type check_expr(Node *n);
static GlobalConstant *find_constant(const char *name){for(int i=0;i<global_constants.n;i++){GlobalConstant *g=global_constants.v[i];if(same(g->t->text,name))return g;}return NULL;}
static Node *constant_source(GlobalConstant *g);
static unsigned constant_expansion_work;
static int constant_dependency_depth;
static Node *copy_constant(Node *n,int depth){
    if(!n)return NULL;if(depth>MAX_NEST||++constant_expansion_work>100000)error(n->t,"limite de expansão de constantes excedido");
    Node *out=mem(sizeof(*out));*out=*n;out->a=copy_constant(n->a,depth+1);out->b=copy_constant(n->b,depth+1);out->items=(Vec){0};
    for(int i=0;i<n->items.n;i++)push(&out->items,copy_constant(n->items.v[i],depth+1));return out;
}
static void expand_constant_names(Node *n){
    if(!n)return;
    if(n->kind==N_NAME){
        GlobalConstant *g=find_constant(n->t->text);if(!g)error(n->t,"const exige literais ou outras constantes globais");
        Node *value=copy_constant(constant_source(g),0);
        /* Preserve the declared int type across a byte-to-int widening. An
         * alias must not silently narrow back to byte after AST expansion. */
        if(equal_type(g->ty,type_i64)){Node *cast=node(N_BUILTIN,n->t);cast->op=T_I64;push(&cast->items,value);*n=*cast;}
        else *n=*value;
        return;
    }
    if(n->kind!=N_INT&&n->kind!=N_STR&&n->kind!=N_BOOL&&n->kind!=N_UNARY&&n->kind!=N_BINARY&&!(n->kind==N_BUILTIN&&(n->op==T_I64||n->op==T_U8||n->op==T_BOOL||n->op==T_NUMTYPE)))error(n->t,"const exige expressão escalar constante, sem chamadas ou alocação");
    if(n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))error(n->t,"const não permite ponteiros");
    expand_constant_names(n->a);expand_constant_names(n->b);for(int i=0;i<n->items.n;i++)expand_constant_names(n->items.v[i]);
}
static Node *constant_source(GlobalConstant *g){
    if(g->state==1)error(g->t,"ciclo entre constantes globais");if(g->state==2)return g->value;
    if(++constant_dependency_depth>MAX_NEST)error(g->t,"limite de dependências de constantes excedido");
    g->state=1;expand_constant_names(g->value);g->state=2;constant_dependency_depth--;return g->value;
}
static Type expected_expr(Type expected,Node *n){
    if(n->kind==N_ARRAY)n->decl=expected;
    Type actual=check_expr(n);
    if(slice_type(expected)&&equal_type(slice_element(expected),type_u8)&&n->kind==N_STR){Node *literal=node(N_STR,n->t);n->kind=N_BUILTIN;n->op=T_UTF8;push(&n->items,literal);}
    else return actual;
    return check_expr(n);
}
static void check_args(Vec *args,Function *f,Token *t){
    if(args->n!=f->params.n)error(t,"esperados %d argumentos; recebidos %d",f->params.n,args->n);
    for(int i=0;i<args->n;i++){Node *a=args->v[i];Var *p=f->params.v[i];require_assign(p->ty,expected_expr(p->ty,a),a->t);}
}
static int compound_op(int k){switch(k){case T_ADDSET:return '+';case T_SUBSET:return '-';case T_MULSET:return '*';case T_DIVSET:return '/';case T_MODSET:return '%';case T_ANDSET:return '&';case T_ORSET:return '|';case T_XORSET:return '^';case T_SHLSET:return T_SHL;case T_SHRSET:return T_SHR;default:return k;}}
static Type binary_type(Type a,Type b,int op,Token *t){
    if(slice_type(a)||slice_type(b))error(t,"slice exige indexação ou len; comparação de referências não é permitida");
    if(floating(a)||floating(b)){
        if(equal_type(a,b)){
            if(op==T_EQ||op==T_NE||op=='<'||op=='>'||op==T_LE||op==T_GE)return type_bool;
            if(op=='+'||op=='-'||op=='*'||op=='/')return a;
        }
        error(t,"operação de ponto flutuante exige tipos iguais e operador aritmético/comparação");
    }
    if(integer(a)&&integer(b)&&((!equal_type(a,type_i64)&&!equal_type(a,type_u8))||(!equal_type(b,type_i64)&&!equal_type(b,type_u8)))){
        if((op==T_SHL||op==T_SHR)&&equal_type(b,type_i64))return a;
        if(!equal_type(a,b))error(t,"inteiros de larguras distintas exigem conversão explícita");
        if(op==T_EQ||op==T_NE||op=='<'||op=='>'||op==T_LE||op==T_GE)return type_bool;
        if(op==T_AND||op==T_OR)error(t,"operação lógica exige bool");return a;
    }
    if(op==T_AND||op==T_OR){if(equal_type(a,type_bool)&&equal_type(b,type_bool))return type_bool;}
    else if(op==T_EQ||op==T_NE){if(!isvoid(a)&&!isvoid(b)&&(assignable(a,b)||assignable(b,a)))return type_bool;}
    else if(op=='<'||op=='>'||op==T_LE||op==T_GE){if(numeric(a)&&numeric(b))return type_bool;}
    else if((op=='+'||op=='-')&&a.depth&&numeric(b))return a;
    else if(numeric(a)&&numeric(b))return type_i64;
    error(t,"operação incompatível entre %s e %s",type_name(a),type_name(b));
}
static Type check_expr(Node *n){
    if(++check_depth>MAX_NEST)error(n->t,"expressão aninhada demais");
    if(n->kind==N_NAME&&!lookup(n->t->text)){
        GlobalConstant *g=find_constant(n->t->text);
        if(g){Token *site=n->t;Node *value=copy_constant(constant_source(g),0);Type actual=check_expr(value);require_assign(g->ty,actual,site);*n=*value;n->ty=g->ty;check_depth--;return n->ty;}
    }
    if(checking->pure){
        if((n->kind==N_NEW&&!value_type(n->decl))||n->kind==N_ARRAY||n->kind==N_STR||n->kind==N_NULL||n->kind==N_SELF||n->kind==N_INDEX)
            error(n->t,"pure permite apenas valores int, byte e bool nesta etapa");
        if(n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))error(n->t,"pure não permite ponteiros");
        if(n->kind==N_BUILTIN&&n->op!=T_I64&&n->op!=T_U8&&n->op!=T_NUMTYPE&&n->op!=T_BOOL)error(n->t,"efeito não permitido em pure: %s",n->t->text);
    }
    Type a,b,ty=type_void;
    if(n->kind==N_NAME&&!lookup(n->t->text)&&checking->owner&&checking->owner->closure&&find_field(checking->owner,n->t->text)){n->kind=N_MEMBER;n->a=node(N_SELF,n->t);}
    switch(n->kind){
    case N_IS:case N_CAST:{
        a=check_expr(n->a);Class *from=object(a)?find_class(a.name):NULL,*to=object(n->decl)?find_class(n->decl.name):NULL;
        if(!from||from->record||!to||to->record)error(n->t,"is/as exige uma referência de class e um tipo class");
        ty=n->kind==N_IS?type_bool:n->decl;break;
    }
    case N_ARRAY:{
        Collection *c=collection_of(n->decl);if(!c||c->map)error(n->t,"literal [...] exige contexto Array<T> (variável, argumento ou retorno tipado)");
        for(int i=0;i<n->items.n;i++){Node *item=n->items.v[i];require_assign(c->key,expected_expr(c->key,item),item->t);}
        n->cls=find_class(c->name);n->fn=find_method(n->cls,"push",NULL);ty=n->decl;break;
    }
    case N_INT:ty=n->t->kind==T_CHAR?type_u8:n->t->kind==T_REAL?(Type){TY_F64,0,NULL,NULL}:type_i64;break;case N_STR:ty=type_str;break;case N_BOOL:ty=type_bool;break;case N_NULL:ty=type_null;break;
    case N_NAME:
        n->var=lookup(n->t->text);
        if(n->var){
            if(n->specialized)error(n->t,"variável local não aceita argumentos de tipo: %s",n->t->text);
            ty=n->var->ty;n->lvalue=true;
        }else{
            n->fn=n->fn?n->fn:find_fn(n->t->text);
            if(!n->fn){
                if(find_generic_function(n->t->text))error(n->t,"função genérica exige argumentos de tipo explícitos: %s::<...>",n->t->text);
                error(n->t,"variável não declarada: %s",n->t->text);
            }
            ty=function_type(n->fn);
        }
        if(checking->pure&&function_value(ty)&&!pure_value(ty))error(n->t,"pure não permite função com efeitos: %s",n->t->text);
        break;
    case N_SELF:if(!checking->owner)error(n->t,"self só existe dentro de métodos");if(n->op==T_SUPER&&!checking->owner->base)error(n->t,"super exige uma classe base");ty=class_type(n->op==T_SUPER?checking->owner->base:checking->owner);break;
    case N_MEMBER:{
        a=check_expr(n->a);if(!object(a))error(n->t,"acesso com ponto exige um objeto");
        Field *f=find_field(find_class(a.name),n->t->text);if(!f)error(n->t,"campo inexistente: %s",n->t->text);
        if(f->private&&checking->owner!=f->owner)error(n->t,"campo privado: %s",n->t->text);
        n->slot=f->slot;n->field=f;ty=f->ty;n->lvalue=!value_type(a)&&!find_class(a.name)->closure;break;
    }
    case N_CALL:{
        Function *f=NULL;
        if(n->a->kind==N_NAME&&!lookup(n->a->t->text)&&!n->a->fn&&!find_fn(n->a->t->text)&&!find_generic_function(n->a->t->text)&&!(checking->owner&&checking->owner->closure&&find_field(checking->owner,n->a->t->text)))error(n->t,"função desconhecida: %s",n->a->t->text);
        if(n->a->kind==N_MEMBER){
            a=check_expr(n->a->a);if(!object(a))error(n->t,"chamada de método exige um objeto");
            Class *c=find_class(a.name);
            if(!find_field(c,n->a->t->text)){
                f=find_method(c,n->a->t->text,&n->slot);if(f&&same(f->t->text,"drop"))error(n->t,"drop é reservado à destruição automática");if(!f)error(n->t,"método inexistente: %s",n->a->t->text);
                bool super_call=n->a->a->kind==N_SELF&&n->a->a->op==T_SUPER;
                if(same(f->t->text,CTOR)&&(!super_call||!same(checking->t->text,CTOR)))error(n->t,"inicializador gerenciado init só pode ser chamado por new ou super.init no construtor derivado");
                if(super_call)n->op=T_SUPER;
                if(f->private&&checking->owner!=f->owner)error(n->t,"método privado: %s",f->t->text);
                if(checking->pure&&!f->pure)error(n->t,"pure não pode chamar função com efeitos: %s",f->t->text);
                n->fn=f;check_args(&n->items,f,n->t);ty=f->result;break;
            }
        }
        a=check_expr(n->a);
        if(!function_value(a))error(n->t,n->a->kind==N_NAME?"variável não é uma função chamável: %s":"expressão não é uma função chamável: %s",type_name(a));
        if(checking->pure&&!a.ref->pure)error(n->t,"pure não pode chamar função com efeitos");
        if(n->items.n!=a.ref->arguments.n)error(n->t,"esperados %d argumentos; recebidos %d",a.ref->arguments.n,n->items.n);
        for(int i=0;i<n->items.n;i++){
            Node *arg=n->items.v[i];Type param=*(Type*)a.ref->arguments.v[i];require_assign(param,expected_expr(param,arg),arg->t);
        }
        if(n->a->kind==N_NAME&&!n->a->var)n->fn=n->a->fn;
        ty=*a.ref->result;break;
    }
    case N_NEW:{
        n->cls=find_class(n->decl.name);if(!n->cls)error(n->t,"classe inexistente para new: %s",n->decl.name);
        if(n->cls->closure){
            if(n->items.n!=n->cls->fields.n)error(n->t,"construção de closure exige uma expressão por captura");
            for(int i=0;i<n->items.n;i++){Field *f=n->cls->fields.v[i];require_assign(f->ty,expected_expr(f->ty,n->items.v[i]),n->t);}
            ty=function_type(n->cls->methods.v[0]);ty.ref->closure=true;break;
        }
        if(n->cls->tagged){
            if(!n->variant_name)error(n->t,"construção de enum exige .Variante");
            for(int i=0;i<n->cls->variants.n;i++){Variant *v=n->cls->variants.v[i];if(same(v->t->text,n->variant_name->text))n->variant=v;}
            if(!n->variant)error(n->variant_name,"variante inexistente");
            if(n->items.n!=n->variant->fields.n)error(n->t,"variante exige %d argumentos",n->variant->fields.n);
            for(int i=0;i<n->items.n;i++){Field *f=n->variant->fields.v[i];require_assign(f->ty,expected_expr(f->ty,n->items.v[i]),n->t);}
            ty=n->decl;break;
        }
        if(n->variant_name)error(n->variant_name,".Variante exige enum");
        if(n->cls->record){
            if(n->items.n&&n->items.n!=n->cls->fields.n)error(n->t,"struct exige zero ou %d valores de campos",n->cls->fields.n);
            for(int i=0;i<n->items.n;i++){Field *f=n->cls->fields.v[i];if(f->private&&checking->owner!=f->owner)error(n->t,"construtor posicional não pode inicializar campo privado: %s",f->t->text);require_assign(f->ty,expected_expr(f->ty,n->items.v[i]),((Node*)n->items.v[i])->t);}
            ty=n->decl;break;
        }
        Function *f=find_method(n->cls,CTOR,&n->slot);n->fn=f;
        if(f&&f->private&&checking->owner!=f->owner)error(n->t,"inicializador privado: %s",f->t->text);
        if(f)check_args(&n->items,f,n->t);else if(n->items.n)error(n->t,"classe não declara inicializador init");
        ty=class_type(n->cls);break;
    }
    case N_INDEX:
        a=check_expr(n->a);b=check_expr(n->b);if(!numeric(b))error(n->t,"índice deve ser inteiro");
        if(slice_type(a)){ty=slice_element(a);n->lvalue=!value_type(ty);}else if(a.depth){ty=pointed(a);n->lvalue=true;}else if(equal_type(a,type_str))ty=type_u8;
        else if(collection_of(a)&&!collection_of(a)->map){ty=collection_of(a)->key;n->lvalue=true;}
        else error(n->t,"índice exige texto, Array ou ponteiro");break;
    case N_BUILTIN:
        if(n->op==T_UTF8){
            if(n->items.n!=1||((Node*)n->items.v[0])->kind!=N_STR)error(n->t,"utf8 exige um literal de texto estático");
            check_expr(n->items.v[0]);TypeRef *ref=mem(sizeof(*ref));ref->origin=n->t;push(&ref->arguments,type_copy(type_u8));ty=(Type){TY_SLICE,0,NULL,ref};
            if(!n->place){n->place=mem(sizeof(*n->place));n->place->t=n->t;n->place->ty=ty;n->place->ownership=2;n->place->static_text=true;}
            break;
        }
        if(n->op==T_C_CALLBACK){
            if(n->items.n!=1)error(n->t,"c_callback recebe uma função global sem captura");
            Node *input=n->items.v[0];check_expr(input);
            if(input->kind!=N_NAME||!input->fn||input->var||input->fn->foreign)error(n->t,"c_callback exige nome de função global AssisScript");
            c_signature(input->fn,true);input->fn->callback=true;n->fn=input->fn;ty=numeric_type("u64");break;
        }
        if(n->op==T_SLICE_MAKE){
            if(n->items.n!=3)error(n->t,"fatia recebe buffer/slice, início e quantidade");
            a=check_expr(n->items.v[0]);if(a.depth!=1&&!slice_type(a))error(n->t,"fatia exige buffer gerenciado ou slice");
            TypeRef *ref=mem(sizeof(*ref));ref->origin=n->t;push(&ref->arguments,type_copy(slice_type(a)?slice_element(a):pointed(a)));ty=(Type){TY_SLICE,0,NULL,ref};valid_type(ty,n->t,false);
            require_assign(type_i64,check_expr(n->items.v[1]),n->t);require_assign(type_i64,check_expr(n->items.v[2]),n->t);break;
        }
        if(n->op==T_CIVIL||n->op==T_ARGC||n->op==T_IO_ERROR){if(n->items.n)error(n->t,"%s recebe zero argumentos",n->t->text);ty=type_i64;break;}
        if(n->op==T_SLEEP||n->op==T_ARG_LEN){if(n->items.n!=1)error(n->t,"arg_size recebe índice int");require_assign(type_i64,check_expr(n->items.v[0]),n->t);ty=type_i64;break;}
        if(n->op==T_WRITE_BYTES||n->op==T_ARG_COPY){if(n->items.n!=3)error(n->t,"%s recebe canal/índice, buffer e quantidade",n->t->text);require_assign(type_i64,check_expr(n->items.v[0]),n->t);a=check_expr(n->items.v[1]);if(!(n->op==T_WRITE_BYTES&&slice_type(a)&&equal_type(slice_element(a),type_u8)))require_assign(pointer(type_u8),a,n->t);require_assign(type_i64,check_expr(n->items.v[2]),n->t);ty=type_i64;break;}
        if(n->op==T_FILE_OPEN){if(n->items.n!=2)error(n->t,"file_open recebe caminho text e modo int");require_assign(type_str,check_expr(n->items.v[0]),n->t);require_assign(type_i64,check_expr(n->items.v[1]),n->t);ty=type_file;break;}
        if(n->op==T_FILE_SYNC||n->op==T_FILE_CLOSE){if(n->items.n!=1)error(n->t,"file_close recebe File");require_assign(type_file,check_expr(n->items.v[0]),n->t);ty=type_i64;break;}
        if(n->op==T_FILE_REPLACE){if(n->items.n!=2)error(n->t,"file_replace recebe origem e destino text");require_assign(type_str,check_expr(n->items.v[0]),n->t);require_assign(type_str,check_expr(n->items.v[1]),n->t);ty=type_i64;break;}
        if(n->op==T_FILE_REMOVE){if(n->items.n!=1)error(n->t,"file_remove recebe caminho text");require_assign(type_str,check_expr(n->items.v[0]),n->t);ty=type_i64;break;}
        if(n->op==T_FILE_READ||n->op==T_FILE_WRITE){if(n->items.n!=3)error(n->t,"IO recebe File, buffer *byte e quantidade");require_assign(type_file,check_expr(n->items.v[0]),n->t);require_assign(pointer(type_u8),check_expr(n->items.v[1]),n->t);require_assign(type_i64,check_expr(n->items.v[2]),n->t);ty=type_i64;break;}
        if(n->op==T_NOW){if(n->items.n)error(n->t,"agora recebe zero argumentos");ty=type_i64;break;}
        if(n->op==T_READ){
            if(n->items.n!=2)error(n->t,"read_bytes recebe buffer *byte e capacidade int");
            require_assign(pointer(type_u8),check_expr(n->items.v[0]),n->t);
            if(!numeric(check_expr(n->items.v[1])))error(n->t,"read_bytes exige capacidade inteira");ty=type_i64;break;
        }
        if(n->op==T_ASSERT){if(n->items.n<1||n->items.n>2)error(n->t,"assert recebe condição e mensagem text opcional");if(n->items.n==2)require_assign(type_str,check_expr(n->items.v[1]),((Node*)n->items.v[1])->t);}
        else if(n->items.n!=1)error(n->t,"%s recebe exatamente um argumento",n->t->text);
        a=check_expr(n->items.v[0]);
        if(n->op==T_BUFFER){valid_type(n->decl,n->t,false);if(!numeric(a))error(n->t,"alloc<T> exige uma quantidade inteira de elementos");ty=pointer(n->decl);}
        else if(n->op==T_ASSERT){if(!equal_type(a,type_bool))error(n->t,"assert exige bool");ty=type_void;}
        else if(n->op==T_ALLOC){if(!numeric(a))error(n->t,"alloc<byte> recebe uma quantidade inteira de bytes");ty=pointer(type_u8);}
        else if(n->op==T_LEN){if(!equal_type(a,type_str)&&!collection_of(a)&&!a.depth&&!slice_type(a))error(n->t,"len recebe text, Array, HashMap ou buffer gerenciado; slice também é aceito");ty=type_i64;}
        else if(n->op==T_BYTES){if(!equal_type(a,type_str))error(n->t,"bytes recebe text e retorna uma visão emprestada *byte");ty=pointer(type_u8);}
        else if(n->op==T_MOVE){if(!pointer_like(a))error(n->t,"move exige um proprietário de objeto ou buffer");ty=a;}
        else if(n->op==T_TEXT){if(!equal_type(a,pointer(type_u8)))error(n->t,"text recebe *byte terminado em zero; o buffer deve permanecer vivo");ty=type_str;}
        else{if(!numeric(a)&&!floating(a)&&!equal_type(a,type_bool))error(n->t,"conversão aceita apenas números e booleanos");ty=n->op==T_NUMTYPE?n->decl:n->op==T_I64?type_i64:n->op==T_U8?type_u8:type_bool;}break;
    case N_UNARY:
        a=check_expr(n->a);
        if(n->op=='+'||n->op=='-'||n->op=='~'){if(!numeric(a)&&!(floating(a)&&n->op!='~'))error(n->t,"operador aritmético exige número compatível");ty=equal_type(a,type_u8)?type_i64:a;}
        else if(n->op=='!'){if(!equal_type(a,type_bool))error(n->t,"! exige bool");ty=type_bool;}
        else if(n->op=='&'){if(value_type(a))error(n->t,"valor Copy imutável não permite extração de endereço");if(!n->a->lvalue)error(n->t,"& exige uma posição gravável");if(n->a->kind==N_NAME){if(n->a->var->immutable)error(n->t,"não é permitido extrair endereço de vínculo imutável");n->a->var->address_taken=true;if(equal_type(a,type_str))n->a->var->length_slot=-1;}ty=pointer(a);}
        else{if(!a.depth)error(n->t,"* exige um ponteiro");ty=pointed(a);n->lvalue=true;}break;
    case N_BINARY:a=check_expr(n->a);b=check_expr(n->b);ty=binary_type(a,b,n->op,n->t);break;
    default:fatal("nó de expressão inválido");
    }
    n->ty=ty;if(inline_type(ty))n->temp=temporary_value(ty,n->t);check_depth--;return ty;
}
enum { FLOW_NORMAL=1,FLOW_RETURN=2,FLOW_BREAK=4,FLOW_CONTINUE=8 };
static int check_statement(Node *n,bool scoped){
    if(++check_depth>MAX_NEST)error(n->t,"bloco aninhado demais");
    if(checking->pure&&(n->kind==N_PRINT||n->kind==N_FREE||n->kind==N_DEFER||n->kind==N_UNSAFE))error(n->t,"efeito não permitido em pure: %s",n->t->text);
    int flow=FLOW_NORMAL;
    switch(n->kind){
    case N_MATCH:{
        Type subject=check_expr(n->a);Class *c=object(subject)?find_class(subject.name):NULL;
        if(!c||!c->tagged)error(n->t,"match exige enum por valor ou enum Move");n->cls=c;n->var=temporary_value(subject,n->t);
        if(!c->value){n->ownership=n->a->kind==N_BUILTIN&&n->a->op==T_MOVE?1:2;n->var->ownership=n->ownership==1?1:0;}
        bool seen[256]={0};flow=0;
        for(int i=0;i<n->items.n;i++){
            Node *arm=n->items.v[i];Variant *v=NULL;
            for(int j=0;j<c->variants.n;j++)if(same(((Variant*)c->variants.v[j])->t->text,arm->t->text))v=c->variants.v[j];
            if(!v)error(arm->t,"variante inexistente em match");if(seen[v->tag])error(arm->t,"variante repetida em match");seen[v->tag]=true;arm->variant=v;
            if(arm->items.n!=v->fields.n)error(arm->t,"padrão exige %d vínculos",v->fields.n);
            int old=bindings.n,previous=scope_start;scope_start=old;
            for(int j=0;j<arm->items.n;j++){Node *binding=arm->items.v[j];Field *field=v->fields.v[j];Var *local=mem(sizeof(*local));local->t=binding->t;local->ty=field->ty;local->immutable=true;local->ownership=field->owned?n->ownership:0;declare(local);binding->var=local;}
            flow|=check_statement(arm->a,true);bindings.n=old;scope_start=previous;
        }
        for(int j=0;j<c->variants.n;j++)if(!seen[j])error(n->t,"match não exaustivo: falta variante %s",((Variant*)c->variants.v[j])->t->text);
        break;
    }
    case N_UNSAFE:flow=check_statement(n->a,true);break;
    case N_BLOCK:{
        int old=bindings.n,previous=scope_start;if(scoped)scope_start=old;
        for(int i=0;i<n->items.n;i++){int f=check_statement(n->items.v[i],true);if(flow&FLOW_NORMAL)flow=(flow&~FLOW_NORMAL)|f;}
        if(scoped){bindings.n=old;scope_start=previous;}break;
    }
    case N_LET:{
        valid_type(n->decl,n->t,false);Type value=expected_expr(n->decl,n->a);require_assign(n->decl,value,n->t);
        if(n->immutable&&!pure_value(n->decl)&&!equal_type(n->decl,type_str)&&!function_value(n->decl))error(n->t,"val aceita int, byte, bool, text e funções nesta etapa");
        if(checking->pure&&(!pure_value(n->decl)||n->ownership))error(n->t,"local pure exige valor escalar sem own/borrow");
        Var *v=mem(sizeof(*v));v->t=n->t;v->ty=n->decl;v->ownership=n->ownership;v->immutable=n->immutable;declare(v);n->var=v;break;
    }
    case N_ASSIGN:{
        Type left=check_expr(n->a);if(!n->a->lvalue)error(n->t,"lado esquerdo não é uma posição gravável");
        if(n->a->kind==N_NAME&&n->a->var->immutable)error(n->t,"vínculo imutável não pode ser reatribuído: %s",n->a->t->text);
        if(n->t->kind==T_INC||n->t->kind==T_DEC){
            if(!integer(left)&&!floating(left))error(n->t,"++ e -- exigem posição numérica mutável; ponteiros e bool não são aceitos");
            n->b->decl=left;
        }
        Type right=expected_expr(left,n->b);
        if(n->op=='=')require_assign(left,right,n->t);
        else{Type result=binary_type(left,right,compound_op(n->op),n->t);if(!equal_type(left,type_u8)||!equal_type(result,type_i64))require_assign(left,result,n->t);}break;
    }
    case N_IF:
        if(!equal_type(check_expr(n->a),type_bool))error(n->t,"condição deve ser bool");
        flow=check_statement(n->b,true)|(n->c?check_statement(n->c,true):FLOW_NORMAL);break;
    case N_WHILE:{
        if(!equal_type(check_expr(n->a),type_bool))error(n->t,"condição deve ser bool");
        loop_depth++;int body=check_statement(n->b,true);loop_depth--;
        if(n->step)check_statement(n->step,true);
        flow=body&FLOW_RETURN;
        if(n->a->kind!=N_BOOL||n->a->t->kind!=T_TRUE||(body&FLOW_BREAK))flow|=FLOW_NORMAL;break;
    }
    case N_RETURN:
        if(isvoid(checking->result)&&n->a)error(n->t,"função void usa return; sem expressão de retorno");
        require_assign(checking->result,n->a?expected_expr(checking->result,n->a):type_void,n->t);flow=FLOW_RETURN;break;
    case N_PRINT:
        for(int i=0;i<n->items.n;i++){
            Node *a=n->items.v[i];Type ty=check_expr(a);
            if(object(ty)&&!value_type(ty)){
                Function *view=find_method(find_class(ty.name),"as_slice",NULL);
                if(view&&view->receiver_mode==2&&!view->params.n&&view->result_mode==2&&view->result_from==-1&&slice_type(view->result)&&equal_type(slice_element(view->result),type_u8)){
                    Node *member=node(N_MEMBER,a->t);member->t=mem(sizeof(*member->t));*member->t=*a->t;member->t->text="as_slice";member->a=a;Node *call=node(N_CALL,a->t);call->a=member;n->items.v[i]=a=call;ty=check_expr(call);
                }else if(checking->safe)error(a->t,"print/write exige texto, slice<byte> ou valor escalar; forneça as_slice para um objeto de texto");
            }
            if(isvoid(ty)||value_type(ty)||(slice_type(ty)&&!equal_type(slice_element(ty),type_u8))||(checking->safe&&(ty.depth||closure_type(ty))))error(a->t,"print/write exige texto, slice<byte> ou valor escalar; endereços não são texto");
        }break;
    case N_DEFER:case N_FREE:{Type t=check_expr(n->a);if(!pointer_like(t)&&!equal_type(t,type_null))error(n->t,"free libera apenas objetos e ponteiros");break;}
    case N_BREAK:case N_CONTINUE:if(!loop_depth)error(n->t,"break/continue só pode ser usado dentro de while");flow=n->kind==N_BREAK?FLOW_BREAK:FLOW_CONTINUE;break;
    case N_EXPR:(void)check_expr(n->a);break;
    default:fatal("nó de instrução inválido");
    }
    check_depth--;return flow;
}
#include "devtools.h"
static Function *main_function;
static int super_initializers(Node *n){
    if(!n)return 0;int count=n->kind==N_CALL&&n->a->kind==N_MEMBER&&same(n->a->t->text,CTOR)&&n->a->a->kind==N_SELF&&n->a->a->op==T_SUPER;
    count+=super_initializers(n->a)+super_initializers(n->b)+super_initializers(n->c)+super_initializers(n->step);
    for(int i=0;i<n->items.n;i++)count+=super_initializers(n->items.v[i]);return count;
}
static void chain_constructor(Function *f){
    if(!f->owner||!same(f->t->text,CTOR))return;
    Function *base=f->owner->base?find_method(f->owner->base,CTOR,NULL):NULL;int calls=super_initializers(f->body);
    if(calls){
        Node *first=f->body->items.n?f->body->items.v[0]:NULL;
        if(!base||calls!=1||!first||first->kind!=N_EXPR||super_initializers(first)!=1)error(f->t,"super.init deve aparecer uma única vez, como primeira instrução do construtor");
        return;
    }
    if(!base)return;
    if(base->params.n)error(f->t,"construtor da base exige argumentos; comece com super.init(...)");
    Token *name=mem(sizeof(*name));*name=*f->t;name->text=CTOR;
    Node *self=node(N_SELF,name);self->op=T_SUPER;Node *member=node(N_MEMBER,name);member->a=self;Node *call=node(N_CALL,name);call->a=member;Node *stmt=node(N_EXPR,name);stmt->a=call;
    push(&f->body->items,NULL);memmove(f->body->items.v+1,f->body->items.v,(size_t)(f->body->items.n-1)*sizeof(void*));f->body->items.v[0]=stmt;
}
static void check(void){
    prepare_generics();
    for(int i=0;i<classes.n;i++){Class *c=classes.v[i];for(int j=0;j<i;j++)if(same(c->t->text,((Class*)classes.v[j])->t->text))error(c->t,"classe declarada duas vezes");}
    for(int i=0;i<functions.n;i++){
        Function *f=functions.v[i];if(find_class(f->t->text))error(f->t,"nome principal declarado duas vezes");
        if(f->foreign&&!target_windows)for(int j=0;j<i;j++){Function *other=functions.v[j];if(other->foreign&&same(f->foreign_symbol,other->foreign_symbol)&&!same(f->foreign_library[0],other->foreign_library[0]))error(f->t,"símbolo C ambíguo em bibliotecas diferentes");}
        for(int j=0;j<i;j++)if(same(f->t->text,((Function*)functions.v[j])->t->text))error(f->t,"função declarada duas vezes");signature(f);
    }
    for(int i=0;i<classes.n;i++){Class *c=classes.v[i];instantiation_site=c->site;instantiation_name=c->generic?c->generic->t->text:NULL;layout(c);}instantiation_site=NULL;
    static Function constants_context;checking=&constants_context;
    for(int i=0;i<global_constants.n;i++){
        GlobalConstant *g=global_constants.v[i];
        for(int j=0;j<i;j++)if(same(g->t->text,((GlobalConstant*)global_constants.v[j])->t->text))error(g->t,"constante global declarada duas vezes");
        if(find_fn(g->t->text)||find_class(g->t->text))error(g->t,"nome principal declarado duas vezes");
        if(!numeric(g->ty)&&!floating(g->ty)&&!equal_type(g->ty,type_bool)&&!equal_type(g->ty,type_str))error(g->t,"const aceita números, bool ou texto estático");
        require_assign(g->ty,check_expr(clone_node(constant_source(g))),g->t);
    }
    main_function=test_driver?test_driver:find_fn(ENTRY);if(!main_function&&!library_check)error(tokens.v[0],"falta a entrada: fn main(): int { return 0; }");
    if(main_function&&(main_function->foreign||main_function->params.n||(!isvoid(main_function->result)&&!equal_type(main_function->result,type_i64))))error(main_function->t,"main recebe zero parâmetros e retorna int ou void; extern não pode ser entrada");
    for(int i=0;i<all_functions.n;i++){
        checking=all_functions.v[i];bindings.n=0;scope_start=0;loop_depth=0;check_depth=0;
        if(checking->owner&&checking->receiver_mode){Var *v=mem(sizeof(*v));v->t=checking->t;v->ty=class_type(checking->owner);v->ownership=checking->receiver_mode;v->slot=0;v->reg=-1;checking->receiver=v;}
        instantiation_site=checking->site;instantiation_name=checking->generic?checking->generic->t->text:NULL;
        for(int j=0;j<checking->params.n;j++)declare(checking->params.v[j]);
        if(checking->foreign)continue;
        chain_constructor(checking);
        int flow=check_statement(checking->body,false);
        if(!isvoid(checking->result)&&(flow&FLOW_NORMAL))error(checking->t,"nem todos os caminhos retornam um valor com return");
    }
    instantiation_site=NULL;
}

#include "ownership.h"
#include "safety.h"


/* ASV2 scalar profile. Validation inspects the entire checked source (including
 * dead branches); emission uses typed IR after destruction of the checked AST.
 * No native runtime, pointers, file authority or C import is embedded. */
static bool page_type(Type t){return !t.depth&&(t.kind==TY_I64||t.kind==TY_BOOL);}
/* These names describe VM imports, never a native dynamic-library allowance. */
static int page_import(Function *f){
    if(!f||!f->foreign||!same(f->foreign_library[0],"assis_htdl_v1")||!same(f->foreign_library[1],"assis_htdl_v1")||!equal_type(f->result,type_i64)||f->result_mode)return 0;
    const char *names[]={"counter_add_v1","event_get_v1","state_get_v1","state_set_v1","node_at_v1","node_kind_v1","node_flags_v1","node_count_v1"};
    for(int i=0;i<8;i++)if(same(f->foreign_symbol,names[i])){
        if(f->params.n!=(i==3?2:1))return 0;
        for(int j=0;j<f->params.n;j++){Var *p=f->params.v[j];if(p->ownership||!equal_type(p->ty,type_i64))return 0;}
        return i+1;
    }
    return 0;
}
static void page_require_type(Type t,Token *site){if(!page_type(t))error(site,"page-asv2: tipo fora do perfil int/bool");}
static void page_check_node(Node *n){
    if(!n)return;
    switch(n->kind){
    case N_CALL:if(isvoid(n->ty))break; /* void calls only occur as statements */
        /* fall through */
    case N_INT:case N_BOOL:case N_NAME:case N_UNARY:case N_BINARY:
        page_require_type(n->ty,n->t);break;
    case N_BUILTIN:
        if(n->op!=T_I64&&n->op!=T_BOOL&&n->op!=T_NUMTYPE)error(n->t,"page-asv2: builtin fora do perfil");page_require_type(n->ty,n->t);break;
    case N_LET:page_require_type(n->decl,n->t);break;
    case N_ASSIGN:if(n->a->kind!=N_NAME)error(n->t,"page-asv2: somente locais escalares");break;
    case N_BLOCK:case N_IF:case N_WHILE:case N_RETURN:case N_BREAK:case N_CONTINUE:case N_EXPR:case N_UNSAFE:break;
    default:error(n->t,"page-asv2: recurso fora do perfil (sem FFI/IO/objetos/ponteiros)");
    }
    if(n->kind==N_CALL&&(!n->fn||n->fn->owner||(n->fn->foreign&&!page_import(n->fn))))error(n->t,"page-asv2: somente chamada direta ou import htdl_v1 do perfil");
    if(n->kind!=N_CALL)page_check_node(n->a);page_check_node(n->b);page_check_node(n->c);page_check_node(n->step);
    for(int i=0;i<n->items.n;i++)page_check_node(n->items.v[i]);
}
static void page_check_profile(void){
    if(source_bytes>65536||tokens.n>16384||source_files.n+source_aliases.n>16||all_functions.n>128||classes.n||generic_functions.n||generic_classes.n)
        fatal("page-asv2: limite do perfil (64 KiB/16384 tokens/16 módulos/128 funções, sem tipos/generics)");
    for(int i=0;i<global_constants.n;i++){GlobalConstant *g=global_constants.v[i];page_require_type(g->ty,g->t);page_check_node(g->value);}
    for(int i=0;i<all_functions.n;i++){
        Function *f=all_functions.v[i];
        if((f->foreign&&!page_import(f))||f->owner||f->callback||f->params.n>4||f->result_mode||(!page_type(f->result)&&!isvoid(f->result)))
            error(f->t,"page-asv2: assinatura fora do perfil (0..4 argumentos int/bool)");
        if(f->vars.n>8)error(f->t,"page-asv2: limite de oito locais incluindo argumento");
        for(int j=0;j<f->vars.n;j++){Var *v=f->vars.v[j];page_require_type(v->ty,v->t);if(v->ownership)error(v->t,"page-asv2: local deve ser escalar por valor");}
        page_check_node(f->body);
    }
}
typedef struct {int op,a,b,c;int32_t immediate;Function *callee;int block;} PageInstruction;
typedef struct {BackendFunction *ir;int start,*blocks;} PageFunction;
static Vec page_code,page_functions;
static PageFunction *page_function(Function *source){for(int i=0;i<page_functions.n;i++){PageFunction *f=page_functions.v[i];if(f->ir->source==source)return f;}fatal("page-asv2: função não resolvida");return NULL;}
static PageInstruction *page_op(int op,int a,int b,int c,int32_t immediate){
    if(page_code.n==16384)fatal("page-asv2: limite de 16384 instruções");
    PageInstruction *n=mem(sizeof(*n));n->op=op;n->a=a;n->b=b;n->c=c;n->immediate=immediate;n->block=-1;push(&page_code,n);return n;
}
static int page_local(Function *f,Var *v){for(int i=0;i<f->vars.n;i++)if(f->vars.v[i]==v)return i;fatal("page-asv2: local não resolvido");return 0;}
static void page_constant(int r,uint64_t bits){page_op(1,r,0,0,(int32_t)(uint32_t)bits);page_op(23,r,0,0,(int32_t)(uint32_t)(bits>>32));}
static void page_binary(int op,int r,int right,Token *site){
    int opcode=op=='+'?2:op=='-'?3:op=='*'?4:op=='/'?5:op==T_EQ||op==T_NE?6:op=='<'||op=='>'||op==T_LE||op==T_GE?7:op=='&'?17:op=='|'?18:op=='^'?19:op==T_SHL?20:op==T_SHR?21:op=='%'?22:-1;
    if(opcode<0)error(site,"page-asv2: operador fora do perfil");
    bool reverse=op=='>'||op==T_LE;page_op(opcode,r,reverse?right:r,reverse?r:right,0);
    if(op==T_NE||op==T_LE||op==T_GE)page_op(15,r,r,0,0);
}
static void page_scalar(IRExpr *v,Function *f,int r);
static void page_value(BackendValue *v,Function *f,int r);
static void page_room(Token *site,int r){if(r>=16)error(site,"page-asv2: expressão excede 16 registradores; use locais intermediários");}
static void page_lazy_begin(int op,int r,int *skip,int *end){
    *skip=page_code.n;page_op(9,r,0,0,0);*end=-1;
    if(op==T_OR){*end=page_code.n;page_op(8,0,0,0,0);((PageInstruction*)page_code.v[*skip])->immediate=page_code.n;}
}
static void page_lazy_end(int skip,int end){((PageInstruction*)page_code.v[end<0?skip:end])->immediate=page_code.n;}
static void page_scalar(IRExpr *v,Function *f,int r){
    page_room(v->site,r);
    switch(v->kind){
    case IV_CONSTANT:page_constant(r,v->value);break;
    case IV_LOCAL:page_op(16,r,page_local(f,v->local),0,0);break;
    case IV_UNARY:
        page_scalar(v->a,f,r);if(v->op=='!')page_op(15,r,r,0,0);else if(v->op=='-')page_op(25,r,r,0,0);else if(v->op=='~')page_op(24,r,r,0,0);break;
    case IV_CAST:page_scalar(v->a,f,r);if(v->type.kind==TY_BOOL){page_op(15,r,r,0,0);page_op(15,r,r,0,0);}break;
    case IV_BINARY:
        page_scalar(v->a,f,r);
        if(v->op==T_AND||v->op==T_OR){int skip,end;page_lazy_begin(v->op,r,&skip,&end);page_scalar(v->b,f,r);page_lazy_end(skip,end);}
        else{page_scalar(v->b,f,r+1);page_binary(v->op,r,r+1,v->site);}break;
    case IV_CALL:
        for(int i=0;i<v->arguments.n;i++)page_scalar(v->arguments.v[i],f,r+i);
        if(!v->arguments.n)page_constant(r,0);
        page_op(10,r,r,v->arguments.n?v->arguments.n-1:0,0)->callee=v->callee;break;
    default:error(v->site,"page-asv2: valor IR fora do perfil");
    }
}
static void page_value(BackendValue *v,Function *f,int r){
    page_room(v->site,r);
    switch(v->kind){
    case BV_SCALAR:page_scalar(v->scalar,f,r);break;
    case BV_CONSTANT:page_constant(r,v->bits);break;
    case BV_LOCAL:page_op(16,r,page_local(f,v->local),0,0);break;
    case BV_CALL:
        for(int i=0;i<v->arguments.n;i++)page_value(v->arguments.v[i],f,r+i);
        if(!v->arguments.n)page_constant(r,0);
        if(v->callee->foreign)page_op(12,r,r,v->arguments.n==2?r+1:0,page_import(v->callee));
        else page_op(10,r,r,v->arguments.n?v->arguments.n-1:0,0)->callee=v->callee;break;
    case BV_BINARY:
        page_value(v->a,f,r);page_value(v->b,f,r+1);page_binary(v->op,r,r+1,v->site);break;
    default:error(v->site,"page-asv2: BackendIR fora do perfil");
    }
}
static void page_write(const char *path){
    for(int i=0;i<backend_functions.n;i++){BackendFunction *bf=backend_functions.v[i];if(bf->source->foreign)continue;PageFunction *f=mem(sizeof(*f));f->ir=bf;f->blocks=mem((size_t)bf->blocks.n*sizeof(int));push(&page_functions,f);}
    for(int i=0;i<page_functions.n;i++){
        PageFunction *pf=page_functions.v[i];BackendFunction *bf=pf->ir;Function *f=bf->source;pf->start=page_code.n;int r=f->vars.n;
        for(int j=0;j<bf->blocks.n;j++){
            BackendBlock *b=bf->blocks.v[j];pf->blocks[j]=page_code.n;
            for(int k=0;k<b->instructions.n;k++){
                BackendInstruction *op=b->instructions.v[k];
                if(op->kind==BI_STORE_LOCAL){page_value(op->value,f,r);page_op(16,page_local(f,op->local),r,0,0);}
                else if(op->kind==BI_EVAL)page_value(op->value,f,r);
                else if(op->kind==BI_SAVE_RETURN){if(op->value)page_value(op->value,f,r);else page_constant(r,0);}
                else if(op->kind!=BI_SITE&&op->kind!=BI_SCOPE_BEGIN&&op->kind!=BI_SCOPE_END)error(op->site,"page-asv2: instrução IR fora do perfil");
            }
            if(b->terminator==BT_RETURN)page_op(11,r,0,0,0);
            else if(b->terminator==BT_JUMP)page_op(8,0,0,0,0)->block=b->yes;
            else if(b->terminator==BT_BRANCH){page_value(b->condition,f,r);page_op(9,r,0,0,0)->block=b->no;page_op(8,0,0,0,0)->block=b->yes;}
            else if(b->terminator==BT_TAIL){
                for(int k=0;k<b->arguments.n;k++)page_value(b->arguments.v[k],f,r+k);
                for(int k=0;k<b->arguments.n;k++)page_op(16,k,r+k,0,0);page_op(8,0,0,0,0)->block=0;
            }else page_op(26,0,0,0,0); /* explicit unreachable/missing-return trap */
        }
        for(int j=pf->start;j<page_code.n;j++){PageInstruction *op=page_code.v[j];if(op->block>=0)op->immediate=pf->blocks[op->block];}
    }
    for(int i=0;i<page_code.n;i++){PageInstruction *op=page_code.v[i];if(op->callee)op->immediate=page_function(op->callee)->start;}
    Buffer output={0};bytes(&output,"ASV2",4);u32(&output,(uint32_t)page_code.n);u32(&output,(uint32_t)page_function(main_function)->start);u32(&output,0);
    for(int i=0;i<page_code.n;i++){PageInstruction *op=page_code.v[i];u8(&output,op->op);u8(&output,op->a);u8(&output,op->b);u8(&output,op->c);u32(&output,(uint32_t)op->immediate);}
    protect_output(path);FILE *file=fopen(path,"wb");if(!file)fatal("não foi possível gravar %s",path);
    bool failed=fwrite(output.v,1,output.n,file)!=output.n;if(fclose(file))failed=true;if(failed)fatal("erro ao gravar %s",path);
}

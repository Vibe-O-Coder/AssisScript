/* Complete typed emission IR. Only this lowering pass reads checked Nodes.
 * Values describe addresses, memory effects, dispatch and resource transfers;
 * blocks carry explicit cleanup operations and resolved terminators. */
enum { BV_SCALAR,BV_CONSTANT,BV_STRING,BV_LOCAL,BV_SELF,BV_FUNCTION,
    BV_ADDR_LOCAL,BV_ADDR_FIELD,BV_ADDR_INDEX,BV_ADDR_DEREF,BV_LOAD,BV_TAKE,
    BV_UNARY,BV_BINARY,BV_CAST,BV_CALL,BV_CONSTRUCT,BV_ARRAY,BV_TYPE_TEST,
    BV_DOWNCAST,BV_STRING_INDEX,BV_UTF8,BV_SLICE,BV_ALLOC,BV_LENGTH,
    BV_ASSERT,BV_NONNULL,BV_REINTERPRET,BV_RUNTIME,BV_MATERIALIZE };
enum { BC_DIRECT,BC_VIRTUAL,BC_SUPER,BC_INDIRECT,BC_CLOSURE };
enum { BM_RAW,BM_BUFFER,BM_SLICE,BM_COLLECTION };
typedef struct BackendValue BackendValue;
struct BackendValue {
    int id,kind,op,mode,offset;Type type,element;Token *site;
    unsigned effects;uint64_t bits;const char *text;size_t length;
    Var *local,*temp;Function *callee;Class *layout;IRExpr *scalar;
    BackendValue *a,*b,*c;Vec arguments,fields,matches;
    bool checked,nonnull,tagged;
};
typedef struct BackendScope BackendScope;
struct BackendScope {Vec variables,children;size_t code_start,code_end;};
enum { BI_STORE_LOCAL,BI_STORE_MEMORY,BI_EVAL,BI_DROP_LOCAL,BI_FREE_SLOT,
    BI_DROP_VALUE,BI_PRINT,BI_SAVE_RETURN,BI_SITE,BI_SCOPE_BEGIN,BI_SCOPE_END };
typedef struct {
    int kind,op;Type type;Token *site;Var *local;BackendValue *value,*address;
    Vec values;BackendScope *scope;bool replace,preserve;
} BackendInstruction;
enum { BT_UNREACHABLE,BT_JUMP,BT_BRANCH,BT_MATCH,BT_RETURN,BT_TAIL,BT_TRAP };
typedef struct {int tag,target;} BackendCase;
typedef struct {
    int id,label,terminator,yes,no;Token *site;BackendValue *condition;
    Vec instructions,cases,arguments;bool scheduled,return_saved;
} BackendBlock;
typedef struct {Function *source;Vec blocks,layout;BackendScope *scope;int proven_bounds;} BackendFunction;
typedef struct {
    BackendFunction *function;BackendScope *scope;BackendBlock *last;
    Vec cleanups;BackendBlock *again,*end;int loop_base;
} BackendLowering;
static Vec backend_values,backend_functions;
static void verify_backend_ir(void);
static BackendValue *backend_value(Node *n);
static BackendValue *backend_address(Node *n);
static BackendValue *backend_alloc_value(int kind,Type type,Token *site){
    BackendValue *v=mem(sizeof(*v));v->kind=kind;v->type=type;v->site=site;v->id=-1;return v;
}
static BackendValue *backend_finish_value(BackendValue *v){v->id=backend_values.n;push(&backend_values,v);return v;}
static BackendValue *backend_local(Var *local){BackendValue *v=backend_alloc_value(BV_LOCAL,local->ty,local->t);v->local=local;v->effects=IR_READ;return backend_finish_value(v);}
static BackendValue *backend_field_address(BackendValue *base,Field *field,Token *site,bool check){
    BackendValue *v=backend_alloc_value(BV_ADDR_FIELD,pointer(field->ty),site);v->a=base;v->offset=field->offset;v->nonnull=check;v->effects=base->effects|(check?IR_TRAP:0);return backend_finish_value(v);
}
static int backend_memory_mode(Node *n){return slice_type(n->ty)?BM_SLICE:collection_of(n->ty)?BM_COLLECTION:n->ty.depth&&n->ownership?BM_BUFFER:BM_RAW;}
static BackendValue *backend_address(Node *n){
    BackendValue *v;
    if(n->kind==N_NAME){v=backend_alloc_value(BV_ADDR_LOCAL,pointer(n->ty),n->t);v->local=n->var;}
    else if(n->kind==N_MEMBER)return backend_field_address(backend_value(n->a),n->field,n->t,!value_type(n->a->ty));
    else if(n->kind==N_INDEX){
        v=backend_alloc_value(BV_ADDR_INDEX,pointer(n->ty),n->t);v->a=backend_value(n->a);v->b=backend_value(n->b);v->element=n->ty;v->mode=backend_memory_mode(n->a);v->checked=!n->bounds_proven;v->effects=v->a->effects|v->b->effects|(v->checked?IR_TRAP:0);
    }else if(n->kind==N_UNARY&&n->op=='*'){
        v=backend_alloc_value(BV_ADDR_DEREF,pointer(n->ty),n->t);v->a=backend_value(n->a);v->effects=v->a->effects|IR_TRAP;
    }else fatal("IR: posição de memória não resolvida");
    return backend_finish_value(v);
}
static BackendValue *backend_load(BackendValue *address,Type type,Token *site,bool take){
    BackendValue *v=backend_alloc_value(take?BV_TAKE:BV_LOAD,type,site);v->a=address;v->effects=address->effects|IR_READ|(take?IR_WRITE:0);return backend_finish_value(v);
}
static BackendValue *backend_materialize(BackendValue *value,Var *temp){
    if(!temp)return value;BackendValue *v=backend_alloc_value(BV_MATERIALIZE,value->type,value->site);v->a=value;v->local=temp;v->effects=value->effects|IR_WRITE;return backend_finish_value(v);
}
static BackendValue *backend_value(Node *n){
    if(!n)fatal("IR: valor ausente");
    BackendValue *v=backend_alloc_value(BV_CONSTANT,n->ty,n->t);v->effects=ir_effects(n);v->temp=n->temp;
    if(n->ir){v->kind=BV_SCALAR;v->scalar=n->ir;return backend_finish_value(v);}
    switch(n->kind){
    case N_INT:v->bits=n->t->number;break;
    case N_BOOL:v->bits=n->t->kind==T_TRUE;break;
    case N_NULL:break;
    case N_STR:v->kind=BV_STRING;v->text=n->t->str;v->length=n->t->len;break;
    case N_NAME:
        if(n->fn&&!n->var){v->kind=BV_FUNCTION;v->callee=n->fn;}else{v->kind=BV_LOCAL;v->local=n->var;}break;
    case N_SELF:v->kind=BV_SELF;break;
    case N_MEMBER:return backend_materialize(backend_load(backend_address(n),n->ty,n->t,false),n->temp);
    case N_INDEX:
        if(equal_type(n->a->ty,type_str)){v->kind=BV_STRING_INDEX;v->a=backend_value(n->a);v->b=backend_value(n->b);}
        else return backend_materialize(backend_load(backend_address(n),n->ty,n->t,false),n->temp);break;
    case N_UNARY:
        if(n->op=='&')return backend_address(n->a);
        if(n->op=='*')return backend_materialize(backend_load(backend_address(n),n->ty,n->t,false),n->temp);
        v->kind=BV_UNARY;v->op=n->op;v->a=backend_value(n->a);break;
    case N_BINARY:v->kind=BV_BINARY;v->op=n->op;v->a=backend_value(n->a);v->b=backend_value(n->b);break;
    case N_CALL:
        v->kind=BV_CALL;v->callee=n->fn;
        if(n->fn&&n->fn->owner){v->mode=n->op==T_SUPER?BC_SUPER:BC_VIRTUAL;v->offset=n->slot;v->a=backend_value(n->a->a);}
        else if(!n->fn){v->mode=closure_type(n->a->ty)?BC_CLOSURE:BC_INDIRECT;v->a=backend_value(n->a);}
        for(int i=0;i<n->items.n;i++)push(&v->arguments,backend_value(n->items.v[i]));break;
    case N_NEW:
        v->kind=BV_CONSTRUCT;v->op=n->op;v->layout=n->cls;v->callee=n->fn;v->tagged=n->variant!=NULL;v->offset=n->variant?n->variant->tag:0;v->fields=n->variant?n->variant->fields:n->cls->fields;
        for(int i=0;i<n->items.n;i++)push(&v->arguments,backend_value(n->items.v[i]));break;
    case N_ARRAY:{
        v->kind=BV_ARRAY;v->callee=n->fn;
        BackendValue *create=backend_alloc_value(BV_CONSTRUCT,n->ty,n->t);create->layout=n->cls;create->fields=n->cls->fields;create->effects=IR_ALLOC|IR_TRAP;v->a=backend_finish_value(create);
        for(int i=0;i<n->items.n;i++)push(&v->arguments,backend_value(n->items.v[i]));break;
    }
    case N_IS:case N_CAST:{
        v->kind=n->kind==N_IS?BV_TYPE_TEST:BV_DOWNCAST;v->a=backend_value(n->a);Class *target=find_class(n->decl.name);
        for(int i=0;i<classes.n;i++){Class *c=classes.v[i];if(c->record)continue;for(Class *base=c;base;base=base->base)if(base==target){push(&v->matches,c);break;}}break;
    }
    case N_BUILTIN:
        v->op=n->op;
        if(n->op==T_C_CALLBACK){v->kind=BV_FUNCTION;v->callee=n->fn;v->mode=1;break;}
        if(n->op==T_UTF8){Node *literal=n->items.v[0];v->kind=BV_UTF8;v->text=literal->t->str;v->length=literal->t->len;break;}
        if(n->op==T_MOVE)return backend_load(backend_address(n->items.v[0]),n->ty,n->t,true);
        if(n->op==T_SLICE_MAKE){v->kind=BV_SLICE;v->element=slice_element(n->ty);v->mode=backend_memory_mode(n->items.v[0]);}
        else if(n->op==T_BUFFER||n->op==T_TRY_BUFFER||n->op==T_ALLOC){v->kind=BV_ALLOC;v->element=n->decl;}
        else if(n->op==T_LEN)v->kind=BV_LENGTH;
        else if(n->op==T_ASSERT)v->kind=BV_ASSERT;
        else if(n->op==T_TEXT)v->kind=BV_NONNULL;
        else if(n->op==T_BYTES)v->kind=BV_REINTERPRET;
        else if(n->op==T_U8||n->op==T_I64||n->op==T_NUMTYPE||n->op==T_BOOL)v->kind=BV_CAST;
        else v->kind=BV_RUNTIME;
        for(int i=0;i<n->items.n;i++)push(&v->arguments,backend_value(n->items.v[i]));
        if(v->arguments.n)v->a=v->arguments.v[0];
        if(v->kind==BV_RUNTIME){int index=n->op==T_READ?0:1;if(index<n->items.n)v->mode=backend_memory_mode(n->items.v[index]);}
        break;
    default:fatal("IR: expressão verificada não possui lowering (%d)",n->kind);
    }
    backend_finish_value(v);
    if(n->temp&&n->kind!=N_NEW&&n->kind!=N_CALL&&v->kind!=BV_UTF8&&v->kind!=BV_SLICE){BackendValue *copy=backend_alloc_value(BV_MATERIALIZE,n->ty,n->t);copy->a=v;copy->local=n->temp;copy->effects=v->effects|IR_WRITE;return backend_finish_value(copy);}
    return v;
}
static BackendFunction *backend_function(Function *source){for(int i=0;i<backend_functions.n;i++){BackendFunction *f=backend_functions.v[i];if(f->source==source)return f;}fatal("IR: função não baixada");return NULL;}
static BackendBlock *backend_block(BackendFunction *f){
    if(f->blocks.n>=131072)error(f->source->t,"IR excede 131072 blocos por função");BackendBlock *b=mem(sizeof(*b));b->id=f->blocks.n;b->site=f->source->t;push(&f->blocks,b);return b;
}
static void backend_schedule(BackendLowering *s,BackendBlock *b){if(!b->scheduled){b->scheduled=true;push(&s->function->layout,b);}s->last=b;}
static BackendInstruction *backend_instruction(BackendBlock *b,int kind,Token *site){BackendInstruction *op=mem(sizeof(*op));op->kind=kind;op->site=site;op->type=type_void;push(&b->instructions,op);return op;}
static void backend_jump(BackendBlock *from,BackendBlock *to){if(from){from->terminator=BT_JUMP;from->yes=to->id;}}
static void backend_cleanup(BackendLowering *s,BackendBlock *b,int from){
    if(!b)return;for(int i=s->cleanups.n-1;i>=from;i--){Var *v=s->cleanups.v[i];BackendInstruction *op=backend_instruction(b,BI_DROP_LOCAL,v->t);op->local=v;op->type=v->ty;}
}
static BackendScope *backend_scope_begin(BackendLowering *s,BackendBlock *b){BackendScope *scope=mem(sizeof(*scope));if(s->scope)push(&s->scope->children,scope);else s->function->scope=scope;s->scope=scope;backend_instruction(b,BI_SCOPE_BEGIN,s->function->source->t)->scope=scope;return scope;}
static BackendBlock *backend_statement(BackendLowering *s,Node *n,BackendBlock *b){
    if(!n||!b||n->unreachable)return b;s->last=b;
    if(n->kind==N_BLOCK){
        int old=s->cleanups.n;BackendScope *outer=s->scope,*scope=backend_scope_begin(s,b);
        for(int i=0;i<n->items.n;i++)b=backend_statement(s,n->items.v[i],b);
        backend_cleanup(s,b,old);s->cleanups.n=old;backend_instruction(b?b:s->last,BI_SCOPE_END,n->t)->scope=scope;s->scope=outer;return b;
    }
    if(n->kind==N_UNSAFE)return backend_statement(s,n->a,b);
    backend_instruction(b,BI_SITE,n->t);
    if(n->kind==N_IF){
        uint64_t value;if(constant(n->a,&value))return backend_statement(s,value?n->b:n->c,b);
        BackendBlock *yes=backend_block(s->function),*no=backend_block(s->function),*join=backend_block(s->function);b->terminator=BT_BRANCH;b->condition=backend_value(n->a);b->yes=yes->id;b->no=no->id;b->site=n->t;
        backend_schedule(s,yes);BackendBlock *a=backend_statement(s,n->b,yes);backend_jump(a,join);
        backend_schedule(s,no);BackendBlock *c=backend_statement(s,n->c,no);backend_jump(c,join);backend_schedule(s,join);return a||c?join:NULL;
    }
    if(n->kind==N_WHILE){
        BackendBlock *test=backend_block(s->function),*body=backend_block(s->function),*step=backend_block(s->function),*done=backend_block(s->function);backend_jump(b,test);
        backend_schedule(s,test);test->terminator=BT_BRANCH;test->condition=backend_value(n->a);test->yes=body->id;test->no=done->id;test->site=n->t;
        BackendBlock *outer_again=s->again,*outer_end=s->end;int outer_base=s->loop_base;s->again=step;s->end=done;s->loop_base=s->cleanups.n;
        backend_schedule(s,body);BackendBlock *tail=backend_statement(s,n->b,body);backend_jump(tail,step);
        backend_schedule(s,step);BackendBlock *next=backend_statement(s,n->step,step);backend_jump(next,test);s->again=outer_again;s->end=outer_end;s->loop_base=outer_base;
        backend_schedule(s,done);return done;
    }
    if(n->kind==N_MATCH){
        int outer=s->cleanups.n;BackendValue *value=backend_value(n->a);
        if(!n->cls->value){BackendValue *check=backend_alloc_value(BV_NONNULL,value->type,n->t);check->a=value;check->effects=value->effects|IR_TRAP;value=backend_finish_value(check);}
        BackendInstruction *store=backend_instruction(b,BI_STORE_LOCAL,n->t);store->local=n->var;store->value=value;store->type=n->var->ty;
        if(n->ownership==1)push(&s->cleanups,n->var);int arm_base=s->cleanups.n;
        BackendBlock *join=backend_block(s->function);b->terminator=BT_MATCH;b->condition=backend_local(n->var);b->site=n->t;bool live=false;
        for(int i=0;i<n->items.n;i++){
            Node *arm=n->items.v[i];BackendBlock *entry=backend_block(s->function);BackendCase *choice=mem(sizeof(*choice));choice->tag=arm->variant->tag;choice->target=entry->id;push(&b->cases,choice);backend_schedule(s,entry);
            BackendScope *outer_scope=s->scope,*scope=backend_scope_begin(s,entry);
            for(int j=0;j<arm->items.n;j++){
                Node *binding=arm->items.v[j];Field *field=arm->variant->fields.v[j];BackendValue *address=backend_field_address(backend_local(n->var),field,binding->t,false);
                BackendInstruction *op=backend_instruction(entry,BI_STORE_LOCAL,binding->t);op->local=binding->var;op->type=field->ty;op->value=backend_load(address,field->ty,binding->t,binding->var->ownership==1);push(&scope->variables,binding->var);
                if(binding->var->ownership==1)push(&s->cleanups,binding->var);
            }
            BackendBlock *tail=backend_statement(s,arm->a,entry);backend_cleanup(s,tail,arm_base);s->cleanups.n=arm_base;backend_instruction(tail?tail:s->last,BI_SCOPE_END,arm->t)->scope=scope;s->scope=outer_scope;
            if(tail){live=true;backend_jump(tail,join);}
        }
        backend_schedule(s,join);backend_cleanup(s,live?join:NULL,outer);s->cleanups.n=outer;return live?join:NULL;
    }
    if(n->kind==N_BREAK||n->kind==N_CONTINUE){backend_cleanup(s,b,s->loop_base);backend_jump(b,n->kind==N_BREAK?s->end:s->again);return NULL;}
    if(n->kind==N_RETURN){
        if(optimize&&s->function->source->pure&&n->a&&n->a->kind==N_CALL&&n->a->fn==s->function->source){b->terminator=BT_TAIL;for(int i=0;i<n->a->items.n;i++)push(&b->arguments,backend_value(n->a->items.v[i]));return NULL;}
        BackendInstruction *op=backend_instruction(b,BI_SAVE_RETURN,n->t);op->type=s->function->source->result;op->value=n->a?backend_value(n->a):NULL;op->preserve=b->return_saved=s->cleanups.n>0;backend_cleanup(s,b,0);b->terminator=BT_RETURN;return NULL;
    }
    BackendInstruction *op;
    switch(n->kind){
    case N_LET:
        op=backend_instruction(b,BI_STORE_LOCAL,n->t);op->local=n->var;op->type=n->var->ty;op->value=backend_value(n->a);if(s->scope)push(&s->scope->variables,n->var);if(n->ownership==1)push(&s->cleanups,n->var);break;
    case N_DEFER:push(&s->cleanups,n->var);break;
    case N_ASSIGN:
        op=backend_instruction(b,n->a->kind==N_NAME&&!n->replace_owned?BI_STORE_LOCAL:BI_STORE_MEMORY,n->t);op->type=n->a->ty;op->value=backend_value(n->b);op->replace=n->replace_owned;
        if(op->kind==BI_STORE_LOCAL){
            op->local=n->a->var;
            if(n->op!='='){BackendValue *binary=backend_alloc_value(BV_BINARY,binary_type(n->a->ty,n->b->ty,compound_op(n->op),n->t),n->t);binary->a=backend_local(n->a->var);binary->b=op->value;binary->op=compound_op(n->op);binary->effects=IR_READ|op->value->effects|((binary->op=='/'||binary->op=='%'||binary->op==T_SHL||binary->op==T_SHR)?IR_TRAP:0);op->value=backend_finish_value(binary);}
        }else{op->address=backend_address(n->a);op->op=n->op=='='?'=':compound_op(n->op);}break;
    case N_EXPR:op=backend_instruction(b,BI_EVAL,n->t);op->value=backend_value(n->a);break;
    case N_FREE:op=backend_instruction(b,n->var?BI_FREE_SLOT:BI_DROP_VALUE,n->t);op->type=n->a->ty;if(n->var)op->address=backend_address(n->a);else op->value=backend_value(n->a);break;
    case N_PRINT:op=backend_instruction(b,BI_PRINT,n->t);op->op=n->op;for(int i=0;i<n->items.n;i++)push(&op->values,backend_value(n->items.v[i]));break;
    default:fatal("IR: instrução verificada não possui lowering (%d)",n->kind);
    }
    return b;
}
static void prepare_backend_ir(void){
    for(int i=0;i<all_functions.n;i++){
        Function *source=all_functions.v[i];BackendFunction *f=mem(sizeof(*f));f->source=source;f->proven_bounds=range_count(source->body);push(&backend_functions,f);if(source->foreign)continue;
        BackendLowering state={0};state.function=f;BackendBlock *entry=backend_block(f);backend_schedule(&state,entry);
        for(int j=0;j<source->params.n;j++){Var *v=source->params.v[j];if(v->ownership==1)push(&state.cleanups,v);}
        BackendBlock *last=backend_statement(&state,source->body,entry);
        if(last){backend_cleanup(&state,last,0);if(isvoid(source->result)){backend_instruction(last,BI_SAVE_RETURN,source->t)->type=type_void;last->terminator=BT_RETURN;}else{last->terminator=BT_TRAP;last->site=source->t;}}
        for(int j=0;j<f->blocks.n;j++){BackendBlock *b=f->blocks.v[j];if(!b->scheduled)backend_schedule(&state,b);if((b->terminator==BT_JUMP||b->terminator==BT_BRANCH)&&(b->yes<0||b->yes>=f->blocks.n))fatal("IR: sucessor inválido");if(b->terminator==BT_BRANCH&&(b->no<0||b->no>=f->blocks.n))fatal("IR: sucessor falso inválido");}
        free(state.cleanups.v);
    }
    verify_backend_ir();
}
static void backend_verify_input(BackendValue *value,BackendValue *input){
    if(input&&(input->id<0||input->id>=value->id||backend_values.v[input->id]!=input))fatal("IR: operando não precede seu consumidor");
}
static void verify_backend_ir(void){
    for(int i=0;i<backend_values.n;i++){
        BackendValue *v=backend_values.v[i];if(v->id!=i||!v->site||v->type.depth<0||v->type.kind>TY_SLICE)fatal("IR: identidade, origem ou tipo inválido");
        backend_verify_input(v,v->a);backend_verify_input(v,v->b);backend_verify_input(v,v->c);for(int j=0;j<v->arguments.n;j++)backend_verify_input(v,v->arguments.v[j]);
        if((v->kind==BV_LOAD||v->kind==BV_TAKE)&&(!v->a||!v->a->type.depth||!equal_type(pointed(v->a->type),v->type)))fatal("IR: leitura sem endereço do tipo correto");
        if((v->kind==BV_LOCAL||v->kind==BV_ADDR_LOCAL||v->kind==BV_MATERIALIZE)&&!v->local)fatal("IR: identidade local ausente");
        if(v->kind==BV_CONSTRUCT&&(!v->layout||(v->layout->value&&!v->temp)))fatal("IR: layout ou destino de construção ausente");
        if(v->kind==BV_CALL){
            if(v->mode<BC_DIRECT||v->mode>BC_CLOSURE)fatal("IR: despacho inválido");
            if(v->mode<=BC_SUPER&&(!v->callee||v->arguments.n!=v->callee->params.n))fatal("IR: chamada direta não resolvida");
            if(v->mode!=BC_DIRECT&&!v->a)fatal("IR: receptor ou função indireta ausente");
        }
    }
    for(int i=0;i<backend_functions.n;i++){
        BackendFunction *f=backend_functions.v[i];
        for(int j=0;j<f->blocks.n;j++){
            BackendBlock *b=f->blocks.v[j];if(!b->scheduled||b->id!=j)fatal("IR: bloco sem posição de emissão");
            if(b->terminator==BT_BRANCH&&(!b->condition||!equal_type(b->condition->type,type_bool)))fatal("IR: ramo sem condição bool");
            if(b->terminator==BT_TAIL&&(!f->source->pure||b->arguments.n!=f->source->params.n))fatal("IR: substituição em cauda inválida");
            for(int k=0;k<b->cases.n;k++){BackendCase *choice=b->cases.v[k];if(choice->target<0||choice->target>=f->blocks.n)fatal("IR: braço fora do CFG");}
            int returns=0;
            for(int k=0;k<b->instructions.n;k++){
                BackendInstruction *op=b->instructions.v[k];
                if((op->kind==BI_STORE_LOCAL||op->kind==BI_DROP_LOCAL)&&!op->local)fatal("IR: instrução local não resolvida");
                if((op->kind==BI_STORE_MEMORY||op->kind==BI_FREE_SLOT)&&(!op->address||!op->address->type.depth||!equal_type(pointed(op->address->type),op->type)))fatal("IR: escrita/liberação sem endereço tipado");
                if((op->kind==BI_STORE_LOCAL||op->kind==BI_STORE_MEMORY||op->kind==BI_EVAL||op->kind==BI_DROP_VALUE)&&!op->value)fatal("IR: instrução sem valor");
                if(op->kind==BI_SAVE_RETURN){returns++;if(!equal_type(op->type,f->source->result)||op->preserve!=b->return_saved)fatal("IR: contrato de retorno inválido");}
            }
            if((b->terminator==BT_RETURN)!=(returns==1))fatal("IR: valor de retorno não domina sua saída");
        }
    }
}
/* Destroy AST contents before optimized native generation, making accidental
 * fallback a real error on every optimized build, including --symbols. Tokens
 * and resolved type/function/local identities are independent and retained. */
static void discard_backend_ast(Node *n){
    if(!n||!n->t)return;Node *a=n->a,*b=n->b,*c=n->c,*step=n->step;Vec items=n->items;memset(n,0,sizeof(*n));
    discard_backend_ast(a);discard_backend_ast(b);discard_backend_ast(c);discard_backend_ast(step);for(int i=0;i<items.n;i++)discard_backend_ast(items.v[i]);free(items.v);
}
static void discard_frontend_ast(void){for(int i=0;i<all_functions.n;i++){Function *f=all_functions.v[i];discard_backend_ast(f->body);f->body=NULL;}}
static const char *backend_value_name(int kind){
    static const char *names[]={"scalar","constant","string","local","self","function-address","address-local","address-field","address-index","address-deref","load","take","unary","binary","cast","call","construct","array-init","type-test","downcast","string-index","utf8-slice","slice","allocate","length","assert","nonnull","reinterpret","runtime","materialize"};
    if(kind<0||(size_t)kind>=sizeof(names)/sizeof(*names))fatal("IR: nome de valor inválido");return names[kind];
}
static const char *backend_instruction_name(int kind){
    static const char *names[]={"store-local","store-memory","eval","drop-local","free-slot","drop-value","print","save-return","source-site","scope-begin","scope-end"};return names[kind];
}
static unsigned backend_instruction_effects(BackendInstruction *op){
    unsigned effects=(op->value?op->value->effects:0)|(op->address?op->address->effects:0);
    for(int i=0;i<op->values.n;i++)effects|=((BackendValue*)op->values.v[i])->effects;
    if(op->kind==BI_STORE_LOCAL||op->kind==BI_STORE_MEMORY)effects|=IR_WRITE;
    if(op->kind==BI_DROP_LOCAL||op->kind==BI_DROP_VALUE||op->kind==BI_FREE_SLOT||op->replace)effects|=IR_READ|IR_WRITE|IR_DROP|IR_CALL;
    if(op->kind==BI_PRINT)effects|=IR_IO|IR_CALL;return effects;
}
static void backend_print_inputs(BackendValue *v){
    BackendValue *fixed[]={v->a,v->b,v->c};bool comma=false;
    for(int i=0;i<3;i++)if(fixed[i]){if(comma)fputc(',',stdout);fprintf(stdout,"%d",fixed[i]->id);comma=true;}
    for(int i=0;i<v->arguments.n;i++){BackendValue *arg=v->arguments.v[i];if(arg==v->a||arg==v->b||arg==v->c)continue;if(comma)fputc(',',stdout);fprintf(stdout,"%d",arg->id);comma=true;}
}
static void print_backend_ir(void){
    fputs(",\"backendFormat\":\"AssisScript-TypedIR-v1\",\"astFallbacks\":0,\"backendValues\":[",stdout);
    for(int i=0;i<backend_values.n;i++){
        BackendValue *v=backend_values.v[i];if(i)fputc(',',stdout);fprintf(stdout,"{\"id\":%d,\"opcode\":",v->id);json_string(stdout,backend_value_name(v->kind));fputs(",\"type\":",stdout);json_string(stdout,type_name(v->type));fprintf(stdout,",\"effects\":%u,\"line\":%d,\"inputs\":[",v->effects,v->site->line);backend_print_inputs(v);fputc(']',stdout);
        if(v->scalar)fprintf(stdout,",\"scalarValue\":%d",v->scalar->id);if(v->local){fputs(",\"local\":",stdout);json_string(stdout,v->local->t->text);}if(v->callee){fputs(",\"callee\":",stdout);json_string(stdout,v->callee->t->text);}
        if(v->kind==BV_ADDR_INDEX)fprintf(stdout,",\"checked\":%s,\"memoryMode\":%d",v->checked?"true":"false",v->mode);
        if(v->kind==BV_ADDR_FIELD)fprintf(stdout,",\"offset\":%d,\"nonnull\":%s",v->offset,v->nonnull?"true":"false");
        if(v->kind==BV_CALL)fprintf(stdout,",\"dispatch\":%d",v->mode);fputc('}',stdout);
    }
    fputs("],\"emission\":[",stdout);
    static const char *terms[]={"unreachable","jump","branch","match","return","tail-call","trap"};
    for(int i=0;i<backend_functions.n;i++){
        BackendFunction *f=backend_functions.v[i];if(i)fputc(',',stdout);fputs("{\"name\":",stdout);json_string(stdout,f->source->t->text);fprintf(stdout,",\"provenBounds\":%d,\"blocks\":[",f->proven_bounds);
        for(int j=0;j<f->blocks.n;j++){
            BackendBlock *b=f->blocks.v[j];if(j)fputc(',',stdout);fprintf(stdout,"{\"id\":%d,\"terminator\":\"%s\",\"condition\":%d,\"successors\":[",b->id,terms[b->terminator],b->condition?b->condition->id:-1);
            if(b->terminator==BT_JUMP||b->terminator==BT_BRANCH)fprintf(stdout,"%d",b->yes);if(b->terminator==BT_BRANCH)fprintf(stdout,",%d",b->no);
            for(int k=0;k<b->cases.n;k++){if(k)fputc(',',stdout);fprintf(stdout,"%d",((BackendCase*)b->cases.v[k])->target);}fputs("],\"operations\":[",stdout);
            for(int k=0;k<b->instructions.n;k++){
                BackendInstruction *op=b->instructions.v[k];if(k)fputc(',',stdout);fputs("{\"opcode\":",stdout);json_string(stdout,backend_instruction_name(op->kind));fprintf(stdout,",\"value\":%d,\"address\":%d,\"effects\":%u,\"line\":%d,\"type\":",op->value?op->value->id:-1,op->address?op->address->id:-1,backend_instruction_effects(op),op->site->line);json_string(stdout,type_name(op->type));if(op->local){fputs(",\"local\":",stdout);json_string(stdout,op->local->t->text);}fputc('}',stdout);
            }fputs("]}",stdout);
        }fputs("]}",stdout);
    }fputc(']',stdout);
}

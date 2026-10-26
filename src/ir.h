/* First high-level typed CFG. Expression operands still refer to checked ASTs;
 * this is deliberately not SSA or a new machine-code backend. Only proven
 * unreachable statements affect emission, after all semantic checks ran. */
enum { IR_READ=1,IR_WRITE=2,IR_ALLOC=4,IR_IO=8,IR_CALL=16,IR_TRAP=32,IR_UNSAFE=64,IR_DROP=128 };
typedef struct {Node *node;Type type;unsigned effects;} IROperation;
typedef struct {int id;Vec operations,successors;const char *terminator;Node *condition;} IRBlock;
typedef struct {Function *source;Vec blocks;} IRFunction;
static Vec ir_functions;
static IRBlock *ir_block(IRFunction *f){
    if(f->blocks.n>=65536)error(f->source->t,"IR excede 65536 blocos por função");
    IRBlock *b=mem(sizeof(*b));b->id=f->blocks.n;push(&f->blocks,b);return b;
}
static void ir_edge(IRBlock *from,IRBlock *to){push(&from->successors,(void*)(intptr_t)(to->id+1));}
static void ir_jump(IRBlock *from,IRBlock *to){if(!from)return;from->terminator="jump";ir_edge(from,to);}
static unsigned ir_effects(Node *n){
    if(!n)return 0;unsigned e=0;
    switch(n->kind){
    case N_NAME:case N_SELF:case N_MEMBER:e|=IR_READ;break;
    case N_INDEX:e|=IR_READ|IR_TRAP;break;
    case N_NEW:if(!value_type(n->ty))e|=IR_ALLOC|IR_TRAP;break;
    case N_ARRAY:e|=IR_ALLOC|IR_WRITE|IR_TRAP;break;
    case N_CALL:e|=IR_CALL|IR_TRAP;if(!(n->fn?n->fn->pure:n->a->ty.ref->pure))e|=IR_READ|IR_WRITE|IR_ALLOC|IR_IO;break;
    case N_ASSIGN:e|=IR_WRITE;if(n->replace_owned)e|=IR_DROP;break;
    case N_FREE:case N_DEFER:e|=IR_DROP|IR_WRITE;break;
    case N_UNSAFE:e|=IR_UNSAFE;break;
    case N_PRINT:e|=IR_IO;break;
    case N_BINARY:if(n->op=='/'||n->op=='%'||n->op==T_SHL||n->op==T_SHR)e|=IR_TRAP;break;
    case N_BUILTIN:
        if(n->op==T_BUFFER||n->op==T_ALLOC)e|=IR_ALLOC|IR_TRAP;
        else if(n->op==T_MOVE)e|=IR_WRITE;
        else if(n->op==T_SLICE_MAKE||n->op==T_ASSERT||n->op==T_LEN)e|=IR_READ|IR_TRAP;
        else if(n->op!=T_U8&&n->op!=T_I64&&n->op!=T_BOOL&&n->op!=T_NUMTYPE&&n->op!=T_BYTES&&n->op!=T_TEXT)e|=IR_IO|IR_READ|IR_WRITE|IR_TRAP;
        break;
    default:break;
    }
    e|=ir_effects(n->a)|ir_effects(n->b)|ir_effects(n->c)|ir_effects(n->step);
    for(int i=0;i<n->items.n;i++)e|=ir_effects(n->items.v[i]);return e;
}
static void ir_operation(IRBlock *b,Node *n){IROperation *op=mem(sizeof(*op));op->node=n;op->type=n->kind==N_LET?n->decl:n->kind==N_RETURN&&n->a?n->a->ty:type_void;op->effects=ir_effects(n);push(&b->operations,op);}
static IRBlock *ir_lower(IRFunction *f,Node *n,IRBlock *b,IRBlock *again,IRBlock *end){
    if(!n)return b;
    if(!b){n->unreachable=true;return NULL;}
    if(n->kind==N_BLOCK){for(int i=0;i<n->items.n;i++)b=ir_lower(f,n->items.v[i],b,again,end);return b;}
    if(n->kind==N_UNSAFE){ir_operation(b,n);return ir_lower(f,n->a,b,again,end);}
    if(n->kind==N_IF){
        uint64_t value;
        if(constant(n->a,&value)){if(value){if(n->c)n->c->unreachable=true;return ir_lower(f,n->b,b,again,end);}n->b->unreachable=true;return n->c?ir_lower(f,n->c,b,again,end):b;}
        IRBlock *yes=ir_block(f),*no=ir_block(f),*join=ir_block(f);b->terminator="branch";b->condition=n->a;ir_edge(b,yes);ir_edge(b,no);
        IRBlock *a=ir_lower(f,n->b,yes,again,end),*c=n->c?ir_lower(f,n->c,no,again,end):no;ir_jump(a,join);ir_jump(c,join);return a||c?join:NULL;
    }
    if(n->kind==N_WHILE){
        IRBlock *test=ir_block(f),*body=ir_block(f),*next=ir_block(f),*done=ir_block(f);ir_jump(b,test);test->terminator="branch";test->condition=n->a;ir_edge(test,body);ir_edge(test,done);
        uint64_t value;IRBlock *tail;
        if(constant(n->a,&value)&&!value){n->b->unreachable=true;tail=NULL;}else tail=ir_lower(f,n->b,body,next,done);
        ir_jump(tail,next);if(n->step)ir_operation(next,n->step);ir_jump(next,test);if(!tail&&!body->terminator)body->terminator="unreachable";return done;
    }
    if(n->kind==N_MATCH){
        b->terminator="match";b->condition=n->a;IRBlock *join=ir_block(f);bool live=false;
        for(int i=0;i<n->items.n;i++){Node *arm=n->items.v[i];IRBlock *entry=ir_block(f);ir_edge(b,entry);IRBlock *tail=ir_lower(f,arm->a,entry,again,end);if(tail){live=true;ir_jump(tail,join);}}
        return live?join:NULL;
    }
    ir_operation(b,n);
    if(n->kind==N_RETURN){b->terminator="return";return NULL;}
    if(n->kind==N_BREAK||n->kind==N_CONTINUE){ir_jump(b,n->kind==N_BREAK?end:again);return NULL;}
    return b;
}
static void prepare_ir(void){
    for(int i=0;i<all_functions.n;i++){
        Function *source=all_functions.v[i];IRFunction *f=mem(sizeof(*f));f->source=source;IRBlock *entry=ir_block(f),*last=ir_lower(f,source->body,entry,NULL,NULL);
        if(last)last->terminator=isvoid(source->result)?"return":"trap";
        for(int j=0;j<f->blocks.n;j++){IRBlock *b=f->blocks.v[j];if(!b->terminator)b->terminator="unreachable";for(int k=0;k<b->successors.n;k++){int id=(int)(intptr_t)b->successors.v[k]-1;if(id<0||id>=f->blocks.n)fatal("IR contém sucessor inválido");}}
        push(&ir_functions,f);
    }
}
static void print_ir(void){
    fputs("{\"format\":\"AssisScript-HIR-v1\",\"functions\":[",stdout);
    for(int i=0;i<ir_functions.n;i++){
        IRFunction *f=ir_functions.v[i];if(i)fputc(',',stdout);fputs("{\"name\":",stdout);json_string(stdout,f->source->t->text);fputs(",\"result\":",stdout);json_string(stdout,type_name(f->source->result));fputs(",\"blocks\":[",stdout);
        for(int j=0;j<f->blocks.n;j++){
            IRBlock *b=f->blocks.v[j];if(j)fputc(',',stdout);fprintf(stdout,"{\"id\":%d,\"terminator\":",b->id);json_string(stdout,b->terminator);fprintf(stdout,",\"conditionEffects\":%u,\"successors\":[",ir_effects(b->condition));
            for(int k=0;k<b->successors.n;k++){if(k)fputc(',',stdout);fprintf(stdout,"%d",(int)(intptr_t)b->successors.v[k]-1);}fputs("],\"operations\":[",stdout);
            for(int k=0;k<b->operations.n;k++){IROperation *op=b->operations.v[k];if(k)fputc(',',stdout);fprintf(stdout,"{\"kind\":%d,\"line\":%d,\"effects\":%u,\"type\":",op->node->kind,op->node->t->line,op->effects);json_string(stdout,type_name(op->type));fputc('}',stdout);}fputs("]}",stdout);
        }fputs("]}",stdout);
    }fputs("]}\n",stdout);
}

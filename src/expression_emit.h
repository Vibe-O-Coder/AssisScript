/* Native x86_64 emission consumes only typed values and resolved identities.
 * --no-opt keeps the AST expression emitter as an executable reference. */
static void ir_emit_expr(IRExpr *v);
static bool ir_leaf(IRExpr *v,Function *f,int *budget){
    if(!v||--*budget<0||!(equal_type(v->type,type_i64)||equal_type(v->type,type_u8)||equal_type(v->type,type_bool)))return false;
    if(v->kind==IV_CONSTANT)return true;
    if(v->kind==IV_LOCAL){for(int i=0;i<f->params.n;i++)if(v->local==f->params.v[i])return true;return false;}
    if(v->kind==IV_UNARY)return ir_leaf(v->a,f,budget);
    if(v->kind==IV_BINARY&&v->op!='/'&&v->op!='%'&&v->op!=T_SHL&&v->op!=T_SHR)return ir_leaf(v->a,f,budget)&&ir_leaf(v->b,f,budget);
    return false;
}
static IRExpr *ir_call_leaf(IRExpr *call){
    Function *f=call->callee;if(debug_symbols||!f->pure||f->params.n>4)return NULL;
    /* CFG is already built and semantically checked; inspect its return op
     * once to select the immutable value graph, never substitute ASTs. */
    IRFunction *body=NULL;for(int i=0;i<ir_functions.n;i++){IRFunction *candidate=ir_functions.v[i];if(candidate->source==f){body=candidate;break;}}
    if(!body)return NULL;IRExpr *result=body->single_return;
    int budget=16;if(!ir_leaf(result,f,&budget))return NULL;
    for(int i=0;i<call->arguments.n;i++){IRExpr *a=call->arguments.v[i];if(a->kind!=IV_LOCAL&&a->kind!=IV_CONSTANT)return NULL;}
    return result;
}
static IRExpr *ir_substitute(IRExpr *v,IRExpr *call,IRExpr *values,int *count){
    if(v->kind==IV_LOCAL)for(int i=0;i<call->callee->params.n;i++)if(v->local==call->callee->params.v[i])return call->arguments.v[i];
    if(v->kind==IV_CONSTANT)return v;
    if(*count>=16)fatal("inline IR excede o orçamento verificado");
    IRExpr *out=&values[(*count)++];*out=*v;
    if(v->a)out->a=ir_substitute(v->a,call,values,count);
    if(v->b)out->b=ir_substitute(v->b,call,values,count);return out;
}
static bool ir_operand_rcx(IRExpr *v){
    if(v->kind==IV_CONSTANT){immediate(RCX,v->value);return true;}
    if(v->kind==IV_LOCAL){load_local(RCX,v->local);return true;}return false;
}
static void ir_emit_expr(IRExpr *v){
    switch(v->kind){
    case IV_CONSTANT:immediate(RAX,v->value);break;
    case IV_LOCAL:load_local(RAX,v->local);break;
    case IV_UNARY:
        ir_emit_expr(v->a);
        if(v->op=='-'){if(floating(v->a->type)){immediate(RCX,v->a->type.kind==TY_F32?UINT64_C(0x80000000):UINT64_C(0x8000000000000000));INS(0x48,0x31,0xc8);}else{INS(0x48,0xf7,0xd8);}}
        else if(v->op=='~'){INS(0x48,0xf7,0xd0);}else if(v->op=='!'){INS(0x48,0x85,0xc0);bool_result(0x94);}break;
    case IV_BINARY:
        ir_emit_expr(v->a);
        if(v->op==T_AND||v->op==T_OR){int done=new_label();INS(0x48,0x85,0xc0);branch_if(v->op==T_AND?0x84:0x85,done);ir_emit_expr(v->b);mark(done,&code);}
        else{
            if((equal_type(v->a->type,type_i64)||equal_type(v->a->type,type_u8))&&v->b->kind==IV_CONSTANT&&immediate_operation(v->op,v->b->value))break;
            if(!ir_operand_rcx(v->b)){INS(0x50);ir_emit_expr(v->b);movreg(RCX,RAX);INS(0x58);}
            gen_operation(v->op,v->a->type,v->b->type,v->site);
        }break;
    case IV_CAST:
        ir_emit_expr(v->a);
        if(v->op==T_BOOL){if(floating(v->a->type)){immediate(RDX,v->a->type.kind==TY_F32?UINT64_C(0x7fffffff):UINT64_C(0x7fffffffffffffff));INS(0x48,0x21,0xd0);}INS(0x48,0x85,0xc0);bool_result(0x95);}
        else gen_numeric_cast(v->a->type,v->type);break;
    case IV_CALL:{
        IRExpr *leaf=ir_call_leaf(v);if(leaf){IRExpr values[16];int count=0;ir_emit_expr(ir_substitute(leaf,v,values,&count));break;}
        for(int i=0;i<v->arguments.n;i++){ir_emit_expr(v->arguments.v[i]);INS(0x50);}call_label(v->callee->label);clean_stack(v->arguments.n);break;
    }
    default:fatal("opcode de expressão IR inválido");
    }
    if(v->type.kind>=TY_I8)normalize_numeric(v->type);
}
/* Branch selection uses the same value graph as expression emission. Lazy
 * operands and traps keep their source order; no checked AST is inspected. */
static void ir_emit_branch(IRExpr *v,int label,bool when_true){
    if(v->kind==IV_CONSTANT){if(!!v->value==when_true)branch(label);return;}
    if(v->kind==IV_UNARY&&v->op=='!'){ir_emit_branch(v->a,label,!when_true);return;}
    if(v->kind==IV_BINARY&&(v->op==T_AND||v->op==T_OR)){
        bool both=v->op==T_AND;
        if(when_true!=both){ir_emit_branch(v->a,label,when_true);ir_emit_branch(v->b,label,when_true);}
        else{int done=new_label();ir_emit_branch(v->a,done,!when_true);ir_emit_branch(v->b,label,when_true);mark(done,&code);}return;
    }
    if(v->kind==IV_BINARY&&(v->op==T_EQ||v->op==T_NE)&&v->a->kind==IV_BINARY&&v->a->op=='%'&&equal_type(v->a->a->type,type_i64)&&v->a->b->kind==IV_CONSTANT&&v->b->kind==IV_CONSTANT&&!v->b->value){
        uint64_t divisor=v->a->b->value,magnitude=(int64_t)divisor<0?0-divisor:divisor;
        if(magnitude&&!(magnitude&(magnitude-1))){ir_emit_expr(v->a->a);immediate(RCX,magnitude-1);INS(0x48,0x85,0xc8);unsigned cc=v->op==T_EQ?0x84:0x85;branch_if(when_true?cc:cc^1,label);return;}
    }
    if(v->kind==IV_BINARY&&(v->op==T_EQ||v->op==T_NE||v->op=='<'||v->op=='>'||v->op==T_LE||v->op==T_GE)&&!floating(v->a->type)){
        ir_emit_expr(v->a);
        unsigned cc=v->op==T_EQ?0x84:v->op==T_NE?0x85:v->op=='<'?0x8c:v->op==T_LE?0x8e:v->op=='>'?0x8f:0x8d;
        if(unsigned_integer(v->a->type)&&v->a->type.kind!=TY_U8){if(v->op=='<')cc=0x82;else if(v->op==T_LE)cc=0x86;else if(v->op=='>')cc=0x87;else if(v->op==T_GE)cc=0x83;}
        if(v->b->kind==IV_CONSTANT&&(int64_t)v->b->value>=INT32_MIN&&(int64_t)v->b->value<=INT32_MAX){INS(0x48,0x3d);u32(&code,(uint32_t)v->b->value);}
        else{if(!ir_operand_rcx(v->b)){INS(0x50);ir_emit_expr(v->b);movreg(RCX,RAX);INS(0x58);}INS(0x48,0x39,0xc8);}
        branch_if(when_true?cc:cc^1,label);return;
    }
    ir_emit_expr(v);INS(0x48,0x85,0xc0);branch_if(when_true?0x85:0x84,label);
}

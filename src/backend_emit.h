/* x86_64 selection for the complete typed IR. No Node or AST traversal. */
static void backend_emit_value(BackendValue *v);
static bool backend_constant_value(BackendValue *v,uint64_t *bits){
    if(v->kind==BV_CONSTANT){*bits=v->bits;return true;}
    if(v->kind==BV_SCALAR&&v->scalar->kind==IV_CONSTANT){*bits=v->scalar->value;return true;}return false;
}
static bool backend_operand_rcx(BackendValue *v){
    uint64_t bits;if(backend_constant_value(v,&bits)){immediate(RCX,bits);return true;}
    if(v->kind==BV_LOCAL){load_local(RCX,v->local);return true;}
    if(v->kind==BV_SCALAR)return ir_operand_rcx(v->scalar);return false;
}
static bool backend_text_length(BackendValue *v){
    if(v->kind==BV_STRING){const char *zero=memchr(v->text,0,v->length);immediate(RAX,zero?(uint64_t)(zero-v->text):v->length);return true;}
    if(v->kind==BV_LOCAL&&v->local->length_slot>=0){Var length={0};length.ty=type_i64;length.slot=v->local->length_slot;length.reg=-1;load_local(RAX,&length);return true;}return false;
}
static void backend_emit_index_address(BackendValue *v){
    if(!v->checked){backend_emit_value(v->a);if(!backend_operand_rcx(v->b)){INS(0x50);backend_emit_value(v->b);movreg(RCX,RAX);INS(0x58);}if(v->mode==BM_SLICE){INS(0x48,0x8b,0x00);}else if(v->mode==BM_COLLECTION){INS(0x48,0x8b,0x40,0x18);}}
    else{
        backend_emit_value(v->a);INS(0x50);backend_emit_value(v->b);movreg(RCX,RAX);INS(0x58);nonnull(v->site);
        if(v->mode==BM_SLICE||v->mode==BM_COLLECTION){
            int valid=new_label();INS(0x48,0x3b,0x48,0x08);branch_if(0x82,valid);panic_at(9,v->site);mark(valid,&code);
            if(v->mode==BM_SLICE){INS(0x48,0x8b,0x00);}else{INS(0x48,0x8b,0x40,0x18);}
        }else if(v->mode==BM_BUFFER){
            INS(0x48,0x8b,0x50,0xf0);int size=value_size(v->element);
            if(size>1&&!(size&(size-1))){unsigned shift=0;while((1u<<shift)!=(unsigned)size)shift++;INS(0x48,0xc1,0xea);u8(&code,shift);}
            else if(size>1){INS(0x50);movreg(RAX,RDX);INS(0x31,0xd2);immediate(RSI,(uint64_t)size);INS(0x48,0xf7,0xf6);movreg(RDX,RAX);INS(0x58);}
            int valid=new_label();INS(0x48,0x39,0xd1);branch_if(0x82,valid);panic_at(9,v->site);mark(valid,&code);
        }
    }
    int size=value_size(v->element);
    if(size==1||size==2||size==4||size==8){INS(0x48,0x8d,0x04);u8(&code,0x08+(size==8?192:size==4?128:size==2?64:0));}
    else{if(size>1){INS(0x48,0x69,0xc9);u32(&code,(uint32_t)size);}INS(0x48,0x01,0xc8);}
}
static void backend_emit_call(BackendValue *v){
    if(v->mode==BC_CLOSURE){
        backend_emit_value(v->a);
        if(v->temp){INS(0x50);local_address(RAX,v->temp);INS(0x50);load_stack(RAX,8);}
        INS(0x50);for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}
        load_stack(RAX,v->arguments.n*8);nonnull(v->site);call_virtual(0);clean_stack(v->arguments.n+1+(v->temp?2:0));return;
    }
    if(v->mode==BC_INDIRECT){
        backend_emit_value(v->a);INS(0x50);if(v->temp){local_address(RAX,v->temp);INS(0x50);}
        for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}
        load_stack(RAX,(v->arguments.n+(v->temp?1:0))*8);nonnull(v->site);INS(0xff,0xd0);clean_stack(v->arguments.n+1+(v->temp?1:0));return;
    }
    if(v->temp){local_address(RAX,v->temp);INS(0x50);}
    if(v->mode==BC_VIRTUAL||v->mode==BC_SUPER){backend_emit_value(v->a);INS(0x50);}
    for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}
    if(v->mode==BC_VIRTUAL||v->mode==BC_SUPER){load_stack(RAX,v->arguments.n*8);nonnull(v->site);if(v->mode==BC_SUPER)call_label(v->callee->label);else call_virtual(v->offset);}
    else call_label(v->callee->label);
    clean_stack(v->arguments.n+((v->mode==BC_VIRTUAL||v->mode==BC_SUPER)?1:0)+(v->temp?1:0));
}
static void backend_emit_try_construct(BackendValue *v){
    /* Reserve first, then evaluate every argument once, even on refusal.
     * Own arguments are consumed in both branches; failure drops in reverse. */
    immediate(RDI,(uint64_t)v->layout->size);site(RSI,v->site);rt_call(RT_try_alloc);INS(0x50);
    for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}
    load_stack(RAX,v->arguments.n*8);INS(0x48,0x85,0xc0);int failed=new_label(),done=new_label();branch_if(0x84,failed);
    if(v->tagged){INS(0x48,0xc7,0x00);u32(&code,(uint32_t)v->offset);}
    else{
        load_label(v->layout->label);load_stack(RDX,v->arguments.n*8);INS(0x48,0x89,0x02);
        for(int i=0;i<v->fields.n;i++){Field *f=v->fields.v[i];if(equal_type(f->ty,type_str)){load_label(string_label("",0));load_stack(RDX,v->arguments.n*8);INS(0x48,0x89,0x82);u32(&code,(uint32_t)f->offset);}}
    }
    if(v->tagged||v->layout->record){
        for(int i=0;i<v->arguments.n;i++){Field *f=v->fields.v[i];load_stack(RAX,(v->arguments.n-1-i)*8);load_stack(RDX,v->arguments.n*8);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)f->offset);store_value(f->ty);}
    }else if(v->callee){load_stack(RAX,v->arguments.n*8);call_label(v->callee->label);}
    clean_stack(v->arguments.n);INS(0x58);branch(done);
    mark(failed,&code);
    for(int i=v->arguments.n-1;i>=0;i--){
        bool owned=(v->tagged||v->layout->record)?((Field*)v->fields.v[i])->owned:v->callee&&((Var*)v->callee->params.v[i])->ownership==1;
        if(owned){load_stack(RAX,(v->arguments.n-1-i)*8);gen_release(((BackendValue*)v->arguments.v[i])->type);}
    }
    clean_stack(v->arguments.n);INS(0x58);mark(done,&code);
}
static void backend_emit_construct(BackendValue *v){
    if(v->op==T_TRY_NEW){backend_emit_try_construct(v);return;}
    if(v->layout->value){
        local_address(RDI,v->temp);immediate(RCX,(uint64_t)v->layout->size);INS(0x31,0xc0,0xfc,0xf3,0xaa);
        if(v->tagged){local_address(RDX,v->temp);INS(0x48,0xc7,0x02);u32(&code,(uint32_t)v->offset);}
        for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);Field *field=v->fields.v[i];local_address(RDX,v->temp);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)field->offset);store_value(field->ty);}
        local_address(RAX,v->temp);return;
    }
    immediate(RDI,(uint64_t)v->layout->size);site(RSI,v->site);rt_call(RT_alloc);INS(0x50);
    if(v->tagged){
        INS(0x48,0xc7,0x00);u32(&code,(uint32_t)v->offset);
        for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);Field *field=v->fields.v[i];load_stack(RDX,0);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)field->offset);store_value(field->ty);}INS(0x58);return;
    }
    load_label(v->layout->label);load_stack(RDX,0);INS(0x48,0x89,0x02);
    for(int i=0;i<v->fields.n;i++){Field *field=v->fields.v[i];if(equal_type(field->ty,type_str)){load_label(string_label("",0));load_stack(RDX,0);INS(0x48,0x89,0x82);u32(&code,(uint32_t)field->offset);}}
    for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}
    if(v->layout->record||v->layout->closure){for(int i=0;i<v->arguments.n;i++){Field *field=v->fields.v[i];load_stack(RAX,(v->arguments.n-1-i)*8);load_stack(RDX,v->arguments.n*8);INS(0x48,0x81,0xc2);u32(&code,(uint32_t)field->offset);store_value(field->ty);}clean_stack(v->arguments.n);}
    if(v->callee){load_stack(RAX,v->arguments.n*8);call_label(v->callee->label);clean_stack(v->arguments.n);}INS(0x58);
}
static void backend_emit_slice(BackendValue *v){
    backend_emit_value(v->a);nonnull(v->site);
    if(v->mode==BM_SLICE){INS(0x48,0x8b,0x48,0x08,0x48,0x8b,0x00);}
    else{INS(0x48,0x8b,0x48,0xf0);int size=value_size(v->element);if(size>1){INS(0x50);movreg(RAX,RCX);INS(0x31,0xd2);immediate(RSI,(uint64_t)size);INS(0x48,0xf7,0xf6);movreg(RCX,RAX);INS(0x58);}}
    INS(0x50,0x51);backend_emit_value(v->arguments.v[1]);INS(0x50);backend_emit_value(v->arguments.v[2]);movreg(RDX,RAX);INS(0x58,0x59,0x5e);
    int start=new_label(),count=new_label();INS(0x48,0x39,0xc8);branch_if(0x86,start);panic_at(9,v->site);mark(start,&code);
    INS(0x48,0x29,0xc1,0x48,0x39,0xca);branch_if(0x86,count);panic_at(9,v->site);mark(count,&code);
    int size=value_size(v->element);if(size>1){INS(0x48,0x69,0xc0);u32(&code,(uint32_t)size);}INS(0x48,0x01,0xc6);
    local_address(RAX,v->temp);INS(0x48,0x89,0x30,0x48,0x89,0x50,0x08);
}
static void backend_emit_runtime(BackendValue *v){
    switch(v->op){
    case T_NOW:rt_call(RT_now);return;
    case T_CIVIL:rt_call(RT_civil);return;
    case T_ARGC:rt_call(RT_argc);return;
    case T_IO_ERROR:rt_call(RT_io_error);return;
    case T_SLEEP:case T_FILE_REMOVE:case T_FILE_SYNC:case T_ARG_LEN:case T_FILE_CLOSE:
        backend_emit_value(v->a);movreg(RDI,RAX);rt_call(v->op==T_SLEEP?RT_sleep:v->op==T_FILE_REMOVE?RT_file_remove:v->op==T_FILE_SYNC?RT_file_sync:v->op==T_ARG_LEN?RT_arg_len:RT_file_close);return;
    case T_FILE_REPLACE:case T_FILE_OPEN:
        backend_emit_value(v->a);INS(0x50);backend_emit_value(v->arguments.v[1]);movreg(RSI,RAX);INS(0x5f);rt_call(v->op==T_FILE_OPEN?RT_file_open:RT_file_replace);return;
    case T_FILE_READ:case T_FILE_WRITE:case T_ARG_COPY:case T_WRITE_BYTES:
        for(int i=0;i<3;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);}INS(0x5a,0x5e,0x5f);
        if(v->mode==BM_SLICE){int valid=new_label();INS(0x48,0x3b,0x56,0x08);branch_if(0x86,valid);panic_at(4,v->site);mark(valid,&code);INS(0x48,0x8b,0x36);}
        else if(v->mode==BM_BUFFER){int valid=new_label();INS(0x48,0x3b,0x56,0xf0);branch_if(0x86,valid);panic_at(4,v->site);mark(valid,&code);}
        rt_call(v->op==T_FILE_READ?RT_file_read:v->op==T_FILE_WRITE?RT_file_write:v->op==T_WRITE_BYTES?RT_stdout_write:RT_arg_copy);return;
    case T_READ:
        backend_emit_value(v->a);INS(0x50);backend_emit_value(v->arguments.v[1]);movreg(RSI,RAX);INS(0x5f);
        if(v->mode==BM_BUFFER){int valid=new_label();INS(0x48,0x3b,0x77,0xf0);branch_if(0x86,valid);panic_at(4,v->site);mark(valid,&code);}site(RDX,v->site);rt_call(RT_read);return;
    default:fatal("IR: intrínseco não resolvido (%d)",v->op);
    }
}
static void backend_emit_value(BackendValue *v){
    switch(v->kind){
    case BV_SCALAR:ir_emit_expr(v->scalar);return;
    case BV_CONSTANT:immediate(RAX,v->bits);break;
    case BV_STRING:load_label(string_label(v->text,v->length));break;
    case BV_LOCAL:load_local(RAX,v->local);break;
    case BV_SELF:INS(0x48,0x8b,0x45,0xf8);break;
    case BV_FUNCTION:load_label(v->mode?v->callee->callback_label:v->callee->label);break;
    case BV_ADDR_LOCAL:local_address(RAX,v->local);break;
    case BV_ADDR_FIELD:backend_emit_value(v->a);if(v->nonnull)nonnull(v->site);INS(0x48,0x05);u32(&code,(uint32_t)v->offset);break;
    case BV_ADDR_INDEX:backend_emit_index_address(v);break;
    case BV_ADDR_DEREF:backend_emit_value(v->a);nonnull(v->site);break;
    case BV_LOAD:backend_emit_value(v->a);load_value(v->type);break;
    case BV_TAKE:backend_emit_value(v->a);movreg(RDX,RAX);load_value(v->type);INS(0x48,0xc7,0x02);u32(&code,0);break;
    case BV_UNARY:
        backend_emit_value(v->a);if(v->op=='-'){if(floating(v->a->type)){immediate(RCX,v->a->type.kind==TY_F32?UINT64_C(0x80000000):UINT64_C(0x8000000000000000));INS(0x48,0x31,0xc8);}else{INS(0x48,0xf7,0xd8);}}
        else if(v->op=='~'){INS(0x48,0xf7,0xd0);}else if(v->op=='!'){INS(0x48,0x85,0xc0);bool_result(0x94);}break;
    case BV_BINARY:{
        backend_emit_value(v->a);
        if(v->op==T_AND||v->op==T_OR){int done=new_label();INS(0x48,0x85,0xc0);branch_if(v->op==T_AND?0x84:0x85,done);backend_emit_value(v->b);mark(done,&code);}
        else{uint64_t bits;if((equal_type(v->a->type,type_i64)||equal_type(v->a->type,type_u8))&&backend_constant_value(v->b,&bits)&&immediate_operation(v->op,bits))break;
            if(!backend_operand_rcx(v->b)){INS(0x50);backend_emit_value(v->b);movreg(RCX,RAX);INS(0x58);}gen_operation(v->op,v->a->type,v->b->type,v->site);}break;
    }
    case BV_CAST:
        backend_emit_value(v->a);if(v->op==T_BOOL){if(floating(v->a->type)){immediate(RDX,v->a->type.kind==TY_F32?UINT64_C(0x7fffffff):UINT64_C(0x7fffffffffffffff));INS(0x48,0x21,0xd0);}INS(0x48,0x85,0xc0);bool_result(0x95);}else gen_numeric_cast(v->a->type,v->type);break;
    case BV_CALL:backend_emit_call(v);break;
    case BV_CONSTRUCT:backend_emit_construct(v);break;
    case BV_ARRAY:backend_emit_value(v->a);INS(0x50);for(int i=0;i<v->arguments.n;i++){backend_emit_value(v->arguments.v[i]);INS(0x50);call_label(v->callee->label);clean_stack(1);}INS(0x58);break;
    case BV_TYPE_TEST:case BV_DOWNCAST:{
        backend_emit_value(v->a);INS(0x50,0x48,0x85,0xc0);int yes=new_label(),no=new_label(),done=new_label();branch_if(0x84,no);INS(0x48,0x8b,0x08);
        for(int i=0;i<v->matches.n;i++){Class *match=v->matches.v[i];load_label(match->label);INS(0x48,0x39,0xc1);branch_if(0x84,yes);}
        mark(no,&code);clean_stack(1);INS(0x31,0xc0);branch(done);mark(yes,&code);INS(0x58);if(v->kind==BV_TYPE_TEST)immediate(RAX,1);mark(done,&code);break;
    }
    case BV_STRING_INDEX:
        if((v->a->kind==BV_LOCAL&&v->a->local->length_slot>=0)||v->a->kind==BV_STRING){
            backend_emit_value(v->a);INS(0x50);backend_emit_value(v->b);INS(0x50);backend_text_length(v->a);INS(0x59,0x5a);int valid=new_label();INS(0x48,0x39,0xc1);branch_if(0x82,valid);panic_at(6,v->site);mark(valid,&code);INS(0x0f,0xb6,0x04,0x0a);
        }else{backend_emit_value(v->a);INS(0x50);backend_emit_value(v->b);movreg(RSI,RAX);INS(0x5f);site(RDX,v->site);rt_call(RT_strbyte);}break;
    case BV_UTF8:load_label(string_label(v->text,v->length));local_address(RDX,v->temp);INS(0x48,0x89,0x02);immediate(RAX,v->length);INS(0x48,0x89,0x42,0x08);movreg(RAX,RDX);break;
    case BV_SLICE:backend_emit_slice(v);break;
    case BV_ALLOC:
        backend_emit_value(v->a);if(v->op==T_BUFFER||v->op==T_TRY_BUFFER){
            int valid=new_label(),sized=new_label();immediate(RCX,(uint64_t)INT64_MAX/(unsigned)value_size(v->element));INS(0x48,0x39,0xc8);branch_if(0x86,valid);
            if(v->op==T_TRY_BUFFER){immediate(RAX,UINT64_MAX);branch(sized);}else panic_at(4,v->site);
            mark(valid,&code);if(value_size(v->element)>1){INS(0x48,0x69,0xc0);u32(&code,(uint32_t)value_size(v->element));}mark(sized,&code);
        }movreg(RDI,RAX);site(RSI,v->site);rt_call(v->op==T_TRY_BUFFER?RT_try_alloc:RT_alloc);break;
    case BV_LENGTH:
        backend_emit_value(v->a);
        if(slice_type(v->a->type)){INS(0x48,0x8b,0x40,0x08);}
        else if(v->a->type.depth){nonnull(v->site);INS(0x48,0x8b,0x40,0xf0);int size=value_size(pointed(v->a->type));if(size>1){INS(0x31,0xd2);immediate(RCX,(uint64_t)size);INS(0x48,0xf7,0xf1);}}
        else if(collection_of(v->a->type)){nonnull(v->site);INS(0x48,0x8b,0x40,0x08);}else if(!backend_text_length(v->a)){movreg(RDI,RAX);rt_call(RT_len);}break;
    case BV_ASSERT:{
        backend_emit_value(v->a);int valid=new_label();INS(0x48,0x85,0xc0);branch_if(0x85,valid);
        if(v->arguments.n==2){backend_emit_value(v->arguments.v[1]);movreg(RDI,RAX);immediate(RSI,2);rt_call(RT_print_str);immediate(RDI,10);immediate(RSI,2);rt_call(RT_print_char);}panic_at(10,v->site);mark(valid,&code);break;
    }
    case BV_NONNULL:backend_emit_value(v->a);nonnull(v->site);break;
    case BV_REINTERPRET:backend_emit_value(v->a);break;
    case BV_RUNTIME:backend_emit_runtime(v);break;
    case BV_MATERIALIZE:backend_emit_value(v->a);local_address(RDX,v->local);store_value(v->type);break;
    default:fatal("IR: opcode de valor inválido (%d)",v->kind);
    }
    if(!v->type.depth&&v->type.kind>=TY_I8)normalize_numeric(v->type);
}
static void backend_emit_false(BackendValue *v,int label){
    if(v->kind==BV_SCALAR){ir_emit_branch(v->scalar,label,false);return;}
    if(v->kind==BV_BINARY&&(v->op==T_EQ||v->op==T_NE||v->op=='<'||v->op=='>'||v->op==T_LE||v->op==T_GE)&&!equal_type(v->a->type,type_str)&&!value_type(v->a->type)&&!floating(v->a->type)&&(!integer(v->a->type)||equal_type(v->a->type,type_i64)||equal_type(v->a->type,type_u8))){
        backend_emit_value(v->a);unsigned cc=v->op==T_EQ?0x85:v->op==T_NE?0x84:v->op=='<'?0x8d:v->op==T_LE?0x8f:v->op=='>'?0x8e:0x8c;uint64_t bits;
        if(backend_constant_value(v->b,&bits)&&(int64_t)bits>=INT32_MIN&&(int64_t)bits<=INT32_MAX){INS(0x48,0x3d);u32(&code,(uint32_t)bits);}
        else{if(!backend_operand_rcx(v->b)){INS(0x50);backend_emit_value(v->b);movreg(RCX,RAX);INS(0x58);}INS(0x48,0x39,0xc8);}branch_if(cc,label);return;
    }
    backend_emit_value(v);INS(0x48,0x85,0xc0);branch_if(0x84,label);
}
static void backend_emit_instruction(BackendInstruction *op){
    switch(op->kind){
    case BI_SITE:if(debug_symbols){DebugSite *site=mem(sizeof(*site));site->offset=code.n;site->token=op->site;push(&debug_sites,site);}break;
    case BI_SCOPE_BEGIN:op->scope->code_start=code.n;break;
    case BI_SCOPE_END:op->scope->code_end=code.n;break;
    case BI_EVAL:backend_emit_value(op->value);break;
    case BI_STORE_LOCAL:backend_emit_value(op->value);cache_text_length(op->local);store_local(op->local);break;
    case BI_STORE_MEMORY:
        backend_emit_value(op->address);INS(0x50);
        if(op->replace){backend_emit_value(op->value);INS(0x50);load_stack(RAX,8);load_value(op->type);gen_release(op->type);INS(0x58,0x5a);store_value(op->type);break;}
        if(op->op=='=')backend_emit_value(op->value);
        else{load_value(op->type);INS(0x50);backend_emit_value(op->value);movreg(RCX,RAX);INS(0x58);gen_operation(op->op,op->type,op->value->type,op->site);}INS(0x5a);store_value(op->type);break;
    case BI_DROP_LOCAL:load_local(RAX,op->local);gen_release(op->type);break;
    case BI_DROP_VALUE:backend_emit_value(op->value);gen_release(op->type);break;
    case BI_FREE_SLOT:backend_emit_value(op->address);INS(0x50);load_value(op->type);gen_release(op->type);INS(0x5a,0x48,0xc7,0x02);u32(&code,0);break;
    case BI_SAVE_RETURN:
        if(op->value)backend_emit_value(op->value);else{INS(0x31,0xc0);}
        if(inline_type(op->type)){INS(0x48,0x8b,0x95);u32(&code,(uint32_t)(16+8*(generating->params.n+(generating->owner?1:0))));store_value(op->type);}if(op->preserve){INS(0x50);}break;
    case BI_PRINT:
        for(int i=0;i<op->values.n;i++){backend_emit_value(op->values.v[i]);INS(0x50);}
        for(int i=0;i<op->values.n;i++){
            if(i&&op->op!=T_WRITE){immediate(RDI,32);immediate(RSI,1);rt_call(RT_print_char);}
            BackendValue *value=op->values.v[i];Type type=value->type;load_stack(RDI,(op->values.n-1-i)*8);if(type.kind==TY_F32&&!type.depth){movreg(RAX,RDI);gen_numeric_cast(type,(Type){TY_F64,0,NULL,NULL});movreg(RDI,RAX);}immediate(RSI,1);
            if(slice_type(type)){INS(0x48,0x8b,0x57,0x08,0x48,0x8b,0x37);immediate(RDI,1);rt_call(RT_write);}else rt_call(floating(type)?RT_print_float:unsigned_integer(type)&&type.kind!=TY_U8?RT_print_uint:numeric(type)?RT_print_int:equal_type(type,type_bool)?RT_print_bool:equal_type(type,type_str)?RT_print_str:RT_print_ptr);
        }
        clean_stack(op->values.n);if(op->op!=T_WRITE){immediate(RDI,10);immediate(RSI,1);rt_call(RT_print_char);}break;
    default:fatal("IR: opcode d'instrução inválido");
    }
}
static void backend_emit_function(BackendFunction *f){
    for(int i=0;i<f->blocks.n;i++)((BackendBlock*)f->blocks.v[i])->label=new_label();
    for(int i=0;i<f->layout.n;i++){
        BackendBlock *b=f->layout.v[i];mark(b->label,&code);for(int j=0;j<b->instructions.n;j++)backend_emit_instruction(b->instructions.v[j]);
        BackendBlock *next=i+1<f->layout.n?f->layout.v[i+1]:NULL;
        switch(b->terminator){
        case BT_JUMP:if(f->blocks.v[b->yes]!=next)branch(((BackendBlock*)f->blocks.v[b->yes])->label);break;
        case BT_BRANCH:backend_emit_false(b->condition,((BackendBlock*)f->blocks.v[b->no])->label);if(f->blocks.v[b->yes]!=next)branch(((BackendBlock*)f->blocks.v[b->yes])->label);break;
        case BT_MATCH:backend_emit_value(b->condition);for(int j=0;j<b->cases.n;j++){BackendCase *choice=b->cases.v[j];INS(0x48,0x81,0x38);u32(&code,(uint32_t)choice->tag);branch_if(0x84,((BackendBlock*)f->blocks.v[choice->target])->label);}panic_at(10,b->site);break;
        case BT_RETURN:if(b->return_saved){INS(0x58);}branch(return_label);break;
        case BT_TAIL:for(int j=0;j<b->arguments.n;j++){backend_emit_value(b->arguments.v[j]);INS(0x50);}for(int j=b->arguments.n-1;j>=0;j--){INS(0x58);store_local(f->source->params.v[j]);}branch(generating_body);break;
        case BT_TRAP:case BT_UNREACHABLE:panic_at(7,b->site);break;
        default:fatal("IR: terminador inválido");
        }
    }
}

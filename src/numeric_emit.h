static void normalize_numeric(Type t){
    if(t.depth)return;
    switch(t.kind){
    case TY_I8:INS(0x48,0x0f,0xbe,0xc0);break;
    case TY_I16:INS(0x48,0x0f,0xbf,0xc0);break;
    case TY_I32:INS(0x48,0x63,0xc0);break;
    case TY_U8:case TY_BOOL:INS(0x25);u32(&code,255);break;
    case TY_U16:INS(0x25);u32(&code,65535);break;
    case TY_U32:case TY_F32:INS(0x89,0xc0);break;
    default:break;
    }
}
static void float_to_xmm(Type t){
    if(t.kind==TY_F32){INS(0x66,0x0f,0x6e,0xc0);}else{INS(0x66,0x48,0x0f,0x6e,0xc0);}
}
static void xmm_to_float(Type t){
    if(t.kind==TY_F32){INS(0x66,0x0f,0x7e,0xc0);}else{INS(0x66,0x48,0x0f,0x7e,0xc0);}
}
static void float_constant_xmm1(double value){uint64_t bits;memcpy(&bits,&value,8);immediate(RCX,bits);INS(0x66,0x48,0x0f,0x6e,0xc9);}
static void gen_numeric_cast(Type from,Type to){
    if(equal_type(from,to))return;
    if(floating(from)){
        float_to_xmm(from);
        if(from.kind==TY_F32){INS(0xf3,0x0f,0x5a,0xc0);}
        if(floating(to)){
            if(to.kind==TY_F32){INS(0xf2,0x0f,0x5a,0xc0);}xmm_to_float(to);return;
        }
        /* Truncation with saturation. NaN converts to zero, never traps. */
        int zero=new_label(),lower=new_label(),upper=new_label(),done=new_label();
        int bits=scalar_bytes(to)*8;bool uns=unsigned_integer(to);
        INS(0x66,0x0f,0x2e,0xc0);branch_if(0x8a,zero);
        float_constant_xmm1(uns?0.0:-ldexp(1.0,bits-1));INS(0x66,0x0f,0x2e,0xc1);branch_if(0x86,lower);
        float_constant_xmm1(ldexp(1.0,uns?bits:bits-1));INS(0x66,0x0f,0x2e,0xc1);branch_if(0x83,upper);
        if(uns&&bits==64){
            int small=new_label();float_constant_xmm1(9223372036854775808.0);INS(0x66,0x0f,0x2e,0xc1);branch_if(0x82,small);
            INS(0xf2,0x0f,0x5c,0xc1,0xf2,0x48,0x0f,0x2c,0xc0);immediate(RCX,UINT64_C(0x8000000000000000));INS(0x48,0x31,0xc8);branch(done);mark(small,&code);
        }
        INS(0xf2,0x48,0x0f,0x2c,0xc0);branch(done);
        mark(lower,&code);immediate(RAX,uns?0:UINT64_C(1)<<(bits-1));normalize_numeric(to);branch(done);
        mark(upper,&code);immediate(RAX,uns?(bits==64?UINT64_MAX:(UINT64_C(1)<<bits)-1):(UINT64_C(1)<<(bits-1))-1);branch(done);
        mark(zero,&code);INS(0x31,0xc0);mark(done,&code);normalize_numeric(to);return;
    }
    if(floating(to)){
        unsigned prefix=to.kind==TY_F32?0xf3:0xf2;
        if(from.kind==TY_U64&&!from.depth){
            int small=new_label(),done=new_label();INS(0x48,0x85,0xc0);branch_if(0x89,small);
            movreg(RCX,RAX);INS(0x83,0xe1,0x01,0x48,0xd1,0xe8,0x48,0x09,0xc8);INS(prefix,0x48,0x0f,0x2a,0xc0,prefix,0x0f,0x58,0xc0);branch(done);
            mark(small,&code);INS(prefix,0x48,0x0f,0x2a,0xc0);mark(done,&code);
        }else{INS(prefix,0x48,0x0f,0x2a,0xc0);}
        xmm_to_float(to);return;
    }
    normalize_numeric(to);
}
static void gen_float_operation(int op,Type t){
    float_to_xmm(t);
    if(t.kind==TY_F32){INS(0x66,0x0f,0x6e,0xc9);}else{INS(0x66,0x48,0x0f,0x6e,0xc9);}
    if(op=='+'||op=='-'||op=='*'||op=='/'){
        u8(&code,t.kind==TY_F32?0xf3:0xf2);INS(0x0f);u8(&code,op=='+'?0x58:op=='-'?0x5c:op=='*'?0x59:0x5e);u8(&code,0xc1);xmm_to_float(t);return;
    }
    if(t.kind==TY_F64)u8(&code,0x66);INS(0x0f,0x2e,0xc1);
    bool_result(op==T_EQ?0x94:op==T_NE?0x95:op=='<'?0x92:op==T_LE?0x96:op=='>'?0x97:0x93);
    if(op==T_EQ||op=='<'||op==T_LE){INS(0x0f,0x9b,0xc2,0x20,0xd0);}
    else if(op==T_NE){INS(0x0f,0x9a,0xc2,0x08,0xd0);}
}
static void gen_value_equality(Type t);
static bool value_has_float(Type t){
    if(floating(t))return true;if(!value_type(t))return false;Class *c=find_class(t.name);
    for(int k=0;k<(c->tagged?c->variants.n:1);k++){Vec fields=c->tagged?((Variant*)c->variants.v[k])->fields:c->fields;for(int i=0;i<fields.n;i++)if(value_has_float(((Field*)fields.v[i])->ty))return true;}return false;
}
static void gen_field_equality(Field *field){
    load_stack(RAX,8);INS(0x48,0x05);u32(&code,(uint32_t)field->offset);load_value(field->ty);INS(0x50);
    load_stack(RAX,8);INS(0x48,0x05);u32(&code,(uint32_t)field->offset);load_value(field->ty);movreg(RCX,RAX);INS(0x58);
    if(value_type(field->ty))gen_value_equality(field->ty);
    else if(floating(field->ty))gen_float_operation(T_EQ,field->ty);
    else{INS(0x48,0x39,0xc8);bool_result(0x94);}
}
static void gen_value_equality(Type t){
    Class *c=find_class(t.name);int fail=new_label(),done=new_label();INS(0x50,0x51);
    if(c->tagged){
        load_stack(RAX,8);load_stack(RCX,0);INS(0x48,0x8b,0x10,0x48,0x3b,0x11);branch_if(0x85,fail);
        for(int i=0;i<c->variants.n;i++){
            Variant *v=c->variants.v[i];int next=new_label();load_stack(RAX,8);INS(0x48,0x81,0x38);u32(&code,(uint32_t)v->tag);branch_if(0x85,next);
            for(int j=0;j<v->fields.n;j++){gen_field_equality(v->fields.v[j]);INS(0x48,0x85,0xc0);branch_if(0x84,fail);}immediate(RAX,1);branch(done);mark(next,&code);
        }branch(fail);
    }else{
        for(int i=0;i<c->fields.n;i++){gen_field_equality(c->fields.v[i]);INS(0x48,0x85,0xc0);branch_if(0x84,fail);}immediate(RAX,1);branch(done);
    }
    mark(fail,&code);INS(0x31,0xc0);mark(done,&code);clean_stack(2);
}

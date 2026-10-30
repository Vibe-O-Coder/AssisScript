/* AArch64 selection of TypedIR-v1. x0=value, x1=right operand, x2=address,
 * x27=runtime state, x29=frame. Every expression stack entry occupies 16 bytes.
 * x18 is reserved by the platform. No assembler/linker is invoked at runtime. */
#include "runtime_arm64_linux.h"
#include "runtime_arm64_macos.h"
typedef struct {size_t at;int label,kind,reg;} ArmFix;
static Vec arm_fixes;
static void a_ins(uint32_t ins){u32(&code,ins);}
static void a_mov(int d,int n){if(d==n)return;if(d==31||n==31)a_ins(0x91000000u|((unsigned)n<<5)|(unsigned)d);else a_ins(0xaa0003e0u|((unsigned)n<<16)|(unsigned)d);}
static void a_imm(int d,uint64_t n){a_ins(0xd2800000u|((unsigned)(n&65535)<<5)|(unsigned)d);for(unsigned k=1;k<4;k++)if((n>>(k*16))&65535)a_ins(0xf2800000u|(k<<21)|((unsigned)((n>>(k*16))&65535)<<5)|(unsigned)d);}
static void a_rr(unsigned ins,int d,int n,int m){a_ins(ins|((unsigned)m<<16)|((unsigned)n<<5)|(unsigned)d);}
static void a_add(int d,int n,int64_t offset){if(offset>=0&&offset<4096)a_ins(0x91000000u|((unsigned)offset<<10)|((unsigned)n<<5)|(unsigned)d);else if(offset<0&&offset>-4096)a_ins(0xd1000000u|((unsigned)-offset<<10)|((unsigned)n<<5)|(unsigned)d);else{a_mov(17,n);a_imm(16,(uint64_t)offset);a_rr(0x8b000000,d==31?17:d,17,16);if(d==31)a_mov(31,17);}}
static void a_mem(bool load,int r,int base,int offset,int size){
    unsigned op=size==1?(load?0x38400000:0x38000000):size==2?(load?0x78400000:0x78000000):size==4?(load?0xb8400000:0xb8000000):(load?0xf8400000:0xf8000000);
    if(offset< -256||offset>255){a_add(16,base,offset);base=16;offset=0;}a_ins(op|(((unsigned)offset&511)<<12)|((unsigned)base<<5)|(unsigned)r);
}
static void a_push(int r){a_ins(0xf81f0fe0u|(unsigned)r);}
static void a_pop(int r){a_ins(0xf84107e0u|(unsigned)r);}
static void a_clean(int n){if(n)a_add(31,31,(int64_t)n*16);}
static void a_fix(int label,int kind,int reg){ArmFix*f=mem(sizeof(*f));f->at=code.n;f->label=label;f->kind=kind;f->reg=reg;push(&arm_fixes,f);a_ins(kind==2?0x90000000u|(unsigned)reg:kind==1?0x94000000u:0x14000000u);if(kind==2)a_ins(0x91000000u|((unsigned)reg<<5)|(unsigned)reg);}
static void a_branch(int label){a_fix(label,0,0);}
static void a_call(int label){a_fix(label,1,0);}
static void a_address(int reg,int label){a_fix(label,2,reg);}
/* A conditional skip over an unrestricted B avoids the +/-1 MiB B.cond range. */
static void a_cond(int condition,int label){a_ins(0x54000000u|(2u<<5)|(unsigned)(condition^1));a_branch(label);}
static void a_cmp(int n,int m){a_rr(0xeb000000,31,n,m);}
static void a_test(int n){a_cmp(n,31);}
static void a_bool(int cc){a_ins(0x9a9f07e0u|((unsigned)(cc^1)<<12));}
static void a_rt(size_t offset){
#define ARM_RT(name) case RT_##name:offset=target_macos?AMRT_##name:ART_##name;break
    switch(offset){ARM_RT(write);ARM_RT(stdout_write);ARM_RT(sleep);ARM_RT(civil);ARM_RT(file_sync);ARM_RT(file_replace);ARM_RT(file_remove);ARM_RT(print_float);ARM_RT(print_uint);ARM_RT(print_str);ARM_RT(print_int);ARM_RT(print_char);ARM_RT(print_bool);ARM_RT(print_ptr);ARM_RT(alloc);ARM_RT(try_alloc);ARM_RT(free);ARM_RT(len);ARM_RT(streq);ARM_RT(strbyte);ARM_RT(error);ARM_RT(finish);ARM_RT(read);ARM_RT(now);ARM_RT(args_init);ARM_RT(argc);ARM_RT(arg_len);ARM_RT(arg_copy);ARM_RT(io_error);ARM_RT(file_open);ARM_RT(file_close);ARM_RT(file_drop);ARM_RT(file_read);ARM_RT(file_write);default:fatal("ARM64: rotina desconhecida");}
#undef ARM_RT
    a_mov(3,27);int64_t delta=(int64_t)offset-(int64_t)code.n;if(delta%4||delta<-(1<<27)||delta>=(1<<27))fatal("ARM64: runtime fora do alcance");a_ins(0x94000000u|((uint32_t)(delta/4)&0x3ffffff));
}
static void a_site(int reg,Token*t){if(source_files.n==1&&t->file==source_files.v[0]){a_imm(reg,(uint64_t)t->line);return;}size_t n=strlen(t->file->path)+32;char*p=mem(n);snprintf(p,n,"%s:%d",t->file->path,t->line);a_address(reg,string_label(p,strlen(p)));a_imm(16,UINT64_C(1)<<63);a_rr(0xaa000000,reg,reg,16);}
static void a_panic(int reason,Token*t){a_imm(0,(uint64_t)reason);a_site(1,t);a_rt(RT_error);a_ins(0xd4200000);}
static void a_nonnull(Token*t){int ok=new_label();a_test(0);a_cond(1,ok);a_panic(1,t);mark(ok,&code);}
static void a_normal(Type t){if(t.depth)return;int bits=scalar_bytes(t)*8;if((integer(t)||equal_type(t,type_bool))&&bits<64){unsigned base=unsigned_integer(t)||equal_type(t,type_bool)?0xd3400000:0x93400000;a_ins(base|((unsigned)(bits-1)<<10));}else if(t.kind==TY_F32)a_ins(0x2a0003e0);}
static void a_local(int reg,Var*v){a_add(reg,29,-8*(v->slot+1));}
static void a_load(Type t){if(!inline_type(t)){a_mem(true,0,0,0,value_size(t));a_normal(t);}}
static void a_store(Type t){if(inline_type(t)){for(int off=0;off<value_size(t);off+=8){a_mem(true,1,0,off,8);a_mem(false,1,2,off,8);}a_mov(0,2);}else a_mem(false,0,2,0,value_size(t));}
static int a_var_reg(Var*v){return v->reg==3?19:v->reg==12?20:v->reg==13?21:22;}
static void a_load_local(int reg,Var*v){if(optimize&&v->reg>=0){a_mov(reg,a_var_reg(v));return;}if(inline_type(v->ty))a_local(reg,v);else a_mem(true,reg,29,-8*(v->slot+1),8);}
static void a_store_local(Var*v){if(optimize&&v->reg>=0){a_mov(a_var_reg(v),0);return;}a_local(2,v);a_store(v->ty);}
static void a_release(Type t);
static void a_value(BackendValue*v);
static void a_scalar(IRExpr*v);
static int a_cc(int op,bool uns){return op==T_EQ?0:op==T_NE?1:op=='<'?(uns?3:11):op==T_LE?(uns?9:13):op=='>'?(uns?8:12):(uns?2:10);}
static void a_fp_in(int d,int n,Type t){a_ins((t.kind==TY_F32?0x1e270000u:0x9e670000u)|((unsigned)n<<5)|(unsigned)d);}
static void a_fp_out(int d,int n,Type t){a_ins((t.kind==TY_F32?0x1e260000u:0x9e660000u)|((unsigned)n<<5)|(unsigned)d);}
static void a_cast(Type from,Type to){
    if(equal_type(to,type_bool)){if(floating(from)){a_imm(1,from.kind==TY_F32?UINT64_C(0x7fffffff):UINT64_C(0x7fffffffffffffff));a_rr(0x8a000000,0,0,1);}a_test(0);a_bool(1);return;}
    if(floating(from)){a_fp_in(0,0,from);if(floating(to)){if(from.kind!=to.kind)a_ins(from.kind==TY_F32?0x1e22c000:0x1e624000);a_fp_out(0,0,to);}
        else{a_ins((unsigned_integer(to)?0x9e390000u:0x9e380000u)|(from.kind==TY_F32?0:0x00400000));/* Native FCVTZ saturates and maps NaN to zero. Narrow destinations clamp first. */
            if(scalar_bytes(to)<8){int done=new_label(),upper=new_label();int bits=scalar_bytes(to)*8;a_imm(1,unsigned_integer(to)?(UINT64_C(1)<<bits)-1:(UINT64_C(1)<<(bits-1))-1);a_cmp(0,1);a_cond(unsigned_integer(to)?9:13,upper);a_mov(0,1);a_branch(done);mark(upper,&code);if(!unsigned_integer(to)){a_imm(1,(uint64_t)-(INT64_C(1)<<(bits-1)));a_cmp(0,1);a_cond(10,done);a_mov(0,1);}mark(done,&code);}a_normal(to);}}
    else if(floating(to)){a_ins((unsigned_integer(from)?0x9e230000u:0x9e220000u)|(to.kind==TY_F32?0:0x00400000));a_fp_out(0,0,to);}else a_normal(to);
}
static void a_equal(Type t);
static void a_operation(int op,Type left,Type right,Token*site){
    if(floating(left)){a_fp_in(0,0,left);a_fp_in(1,1,left);if(op=='+'||op=='-'||op=='*'||op=='/'){unsigned ins=op=='+'?0x1e202800:op=='-'?0x1e203800:op=='*'?0x1e200800:0x1e201800;a_ins(ins|(left.kind==TY_F32?0:0x00400000)|(1u<<16));a_fp_out(0,0,left);}else{a_ins((left.kind==TY_F32?0x1e202000u:0x1e602000u)|(1u<<16));a_bool(op=='<'?4:op==T_LE?9:op=='>'?12:op==T_GE?10:a_cc(op,true));}return;}
    if(value_type(left)){a_equal(left);if(op==T_NE){a_imm(1,1);a_rr(0xca000000,0,0,1);}return;}
    if(equal_type(left,type_str)){a_rt(RT_streq);if(op==T_NE){a_imm(1,1);a_rr(0xca000000,0,0,1);}return;}
    bool uns=unsigned_integer(left);switch(op){
    case '+':case '-':if(left.depth){a_imm(16,(uint64_t)value_size(pointed(left)));a_rr(0x9b007c00,1,1,16);}a_rr(op=='+'?0x8b000000:0xcb000000,0,0,1);break;
    case '*':a_rr(0x9b007c00,0,0,1);break;
    case '&':case '|':case '^':a_rr(op=='&'?0x8a000000:op=='|'?0xaa000000:0xca000000,0,0,1);break;
    case '/':case '%':{int ok=new_label();a_test(1);a_cond(1,ok);a_panic(op=='/'?2:8,site);mark(ok,&code);a_rr(uns?0x9ac00800:0x9ac00c00,2,0,1);if(op=='/')a_mov(0,2);else a_ins(0x9b008000u|(1u<<16)|(0u<<10)|(2u<<5));break;}
    case T_SHL:case T_SHR:{int ok=new_label();a_imm(2,(uint64_t)(scalar_bytes(left)*8-1));a_cmp(1,2);a_cond(9,ok);a_panic(3,site);mark(ok,&code);a_rr(op==T_SHL?0x9ac02000:uns?0x9ac02400:0x9ac02800,0,0,1);break;}
    default:a_cmp(0,1);a_bool(a_cc(op,uns));return;
    }(void)right;a_normal(left);
}
static void a_unary(int op,Type t){if(op=='!'){a_test(0);a_bool(0);}else if(op=='~')a_ins(0xaa2003e0);else if(op=='-'){if(floating(t)){a_imm(1,t.kind==TY_F32?UINT64_C(1)<<31:UINT64_C(1)<<63);a_rr(0xca000000,0,0,1);}else a_rr(0xcb000000,0,31,0);}a_normal(t);}
static void a_scalar(IRExpr*v){
    switch(v->kind){case IV_CONSTANT:a_imm(0,v->value);break;case IV_LOCAL:a_load_local(0,v->local);break;case IV_CAST:a_scalar(v->a);a_cast(v->a->type,v->type);break;case IV_UNARY:a_scalar(v->a);a_unary(v->op,v->a->type);break;
    case IV_BINARY:a_scalar(v->a);if(v->op==T_AND||v->op==T_OR){int done=new_label();a_test(0);a_cond(v->op==T_AND?0:1,done);a_scalar(v->b);mark(done,&code);}else{a_push(0);a_scalar(v->b);a_mov(1,0);a_pop(0);a_operation(v->op,v->a->type,v->b->type,v->site);}break;
    case IV_CALL:for(int i=0;i<v->arguments.n;i++){a_scalar(v->arguments.v[i]);a_push(0);}a_call(v->callee->label);a_clean(v->arguments.n);break;default:fatal("ARM64: scalar IR inválida");}a_normal(v->type);
}
static void a_equal(Type t){
    Class*c=find_class(t.name);int fail=new_label(),done=new_label();a_push(0);a_push(1);
    if(c->tagged){a_mem(true,2,0,0,8);a_mem(true,3,1,0,8);a_cmp(2,3);a_cond(1,fail);}
    for(int k=0;k<(c->tagged?c->variants.n:1);k++){int next=new_label();Vec fields=c->tagged?((Variant*)c->variants.v[k])->fields:c->fields;if(c->tagged){a_mem(true,0,31,16,8);a_mem(true,0,0,0,8);a_imm(1,(uint64_t)((Variant*)c->variants.v[k])->tag);a_cmp(0,1);a_cond(1,next);}
        for(int i=0;i<fields.n;i++){Field*f=fields.v[i];a_mem(true,0,31,16,8);a_add(0,0,f->offset);a_load(f->ty);a_push(0);a_mem(true,0,31,16,8);a_add(0,0,f->offset);a_load(f->ty);a_mov(1,0);a_pop(0);a_operation(T_EQ,f->ty,f->ty,c->t);a_test(0);a_cond(0,fail);}a_imm(0,1);a_branch(done);mark(next,&code);}
    a_imm(0,1);a_branch(done);mark(fail,&code);a_imm(0,0);mark(done,&code);a_clean(2);
}
static void a_release(Type t){
    if(equal_type(t,type_file)){a_rt(RT_file_drop);return;}Class*c=object(t)?find_class(t.name):NULL;
    if(closure_type(t)||(c&&!c->record&&!collection_of(t))){int done=new_label();a_test(0);a_cond(0,done);a_push(0);a_mem(true,0,0,0,8);a_add(2,0,-8);a_mem(true,0,2,0,8);a_rr(0x8b000000,0,0,2);a_ins(0xd63f0000);a_clean(1);mark(done,&code);return;}
    if(c&&has_owned_fields(c)){a_push(0);a_call(c->drop_label);a_clean(1);return;}
    if(collection_of(t)){int done=new_label();a_test(0);a_cond(0,done);a_push(0);a_call(find_method(c,"dispose",NULL)->label);a_pop(0);mark(done,&code);}a_rt(RT_free);
}
static void a_call_value(BackendValue*v){
    int extra=0;if(v->mode==BC_INDIRECT||v->mode==BC_CLOSURE){a_value(v->a);a_push(0);extra++;}
    if(v->temp){a_local(0,v->temp);a_push(0);extra++;}
    if(v->mode==BC_VIRTUAL||v->mode==BC_SUPER){a_value(v->a);a_push(0);extra++;}
    if(v->mode==BC_CLOSURE){a_mem(true,0,31,(extra-1)*16,8);a_push(0);extra++;}
    for(int i=0;i<v->arguments.n;i++){a_value(v->arguments.v[i]);a_push(0);}
    if(v->mode==BC_INDIRECT){a_mem(true,0,31,(v->arguments.n+extra-1)*16,8);a_nonnull(v->site);a_ins(0xd63f0000);}
    else if(v->mode==BC_VIRTUAL||v->mode==BC_CLOSURE){a_mem(true,0,31,v->arguments.n*16,8);a_nonnull(v->site);a_mem(true,0,0,0,8);a_add(2,0,(int64_t)v->offset*8);a_mem(true,0,2,0,8);a_rr(0x8b000000,0,0,2);a_ins(0xd63f0000);}
    else a_call(v->callee->label);a_clean(v->arguments.n+extra);
}
static void a_construct(BackendValue*v){
    if(v->layout->value){a_local(2,v->temp);a_imm(0,0);for(int off=0;off<v->layout->size;off+=8)a_mem(false,0,2,off,8);a_mov(0,2);}
    else{a_imm(0,(uint64_t)v->layout->size);a_site(1,v->site);a_rt(RT_alloc);}a_push(0);
    if(v->tagged){a_imm(1,(uint64_t)v->offset);a_mem(false,1,0,0,8);}
    else if(!v->layout->value){a_address(1,v->layout->label);a_mem(false,1,0,0,8);for(int i=0;i<v->fields.n;i++){Field*f=v->fields.v[i];if(equal_type(f->ty,type_str)){a_address(1,string_label("",0));a_mem(false,1,0,f->offset,8);}}}
    if(v->tagged||v->layout->value||v->layout->record||v->layout->closure){for(int i=0;i<v->arguments.n;i++){a_value(v->arguments.v[i]);a_mem(true,2,31,0,8);Field*f=v->fields.v[i];a_add(2,2,f->offset);a_store(f->ty);}}
    else{for(int i=0;i<v->arguments.n;i++){a_value(v->arguments.v[i]);a_push(0);}if(v->callee)a_call(v->callee->label);a_clean(v->arguments.n);}a_pop(0);
}
static void a_bound(int index,int length,int reason,Token*site){int ok=new_label();a_cmp(index,length);a_cond(3,ok);a_panic(reason,site);mark(ok,&code);}
static void a_runtime(BackendValue*v){
    for(int i=0;i<v->arguments.n;i++){a_value(v->arguments.v[i]);a_push(0);}for(int i=v->arguments.n-1;i>=0;i--)a_pop(i);
    if(v->op==T_FILE_READ||v->op==T_FILE_WRITE||v->op==T_ARG_COPY||v->op==T_WRITE_BYTES){if(v->mode==BM_SLICE||v->mode==BM_BUFFER){a_mem(true,3,1,v->mode==BM_SLICE?8:-16,8);int ok=new_label();a_cmp(2,3);a_cond(9,ok);a_panic(4,v->site);mark(ok,&code);if(v->mode==BM_SLICE)a_mem(true,1,1,0,8);}}
    if(v->op==T_READ){if(v->mode==BM_BUFFER){a_mem(true,3,0,-16,8);int ok=new_label();a_cmp(1,3);a_cond(9,ok);a_panic(4,v->site);mark(ok,&code);}a_site(2,v->site);}
    size_t rt;switch(v->op){case T_NOW:rt=RT_now;break;case T_CIVIL:rt=RT_civil;break;case T_ARGC:rt=RT_argc;break;case T_IO_ERROR:rt=RT_io_error;break;case T_SLEEP:rt=RT_sleep;break;case T_FILE_REMOVE:rt=RT_file_remove;break;case T_FILE_SYNC:rt=RT_file_sync;break;case T_ARG_LEN:rt=RT_arg_len;break;case T_FILE_CLOSE:rt=RT_file_close;break;case T_FILE_REPLACE:rt=RT_file_replace;break;case T_FILE_OPEN:rt=RT_file_open;break;case T_FILE_READ:rt=RT_file_read;break;case T_FILE_WRITE:rt=RT_file_write;break;case T_ARG_COPY:rt=RT_arg_copy;break;case T_WRITE_BYTES:rt=RT_stdout_write;break;case T_READ:rt=RT_read;break;default:fatal("ARM64: intrínseco inválido");return;}a_rt(rt);
}
static void a_value(BackendValue*v){
    switch(v->kind){
    case BV_SCALAR:a_scalar(v->scalar);return;case BV_CONSTANT:a_imm(0,v->bits);break;case BV_STRING:a_address(0,string_label(v->text,v->length));break;case BV_LOCAL:a_load_local(0,v->local);break;case BV_SELF:a_mem(true,0,29,-8,8);break;
    case BV_FUNCTION:a_address(0,v->mode?v->callee->callback_label:v->callee->label);break;case BV_ADDR_LOCAL:a_local(0,v->local);break;
    case BV_ADDR_FIELD:a_value(v->a);if(v->nonnull)a_nonnull(v->site);a_add(0,0,v->offset);break;
    case BV_ADDR_DEREF:a_value(v->a);a_nonnull(v->site);break;
    case BV_ADDR_INDEX:a_value(v->a);a_push(0);a_value(v->b);a_mov(1,0);a_pop(0);if(v->checked){a_nonnull(v->site);if(v->mode==BM_SLICE||v->mode==BM_COLLECTION)a_mem(true,2,0,8,8);else if(v->mode==BM_BUFFER){a_mem(true,2,0,-16,8);a_imm(3,(uint64_t)value_size(v->element));a_rr(0x9ac00800,2,2,3);}if(v->mode!=BM_RAW)a_bound(1,2,9,v->site);}if(v->mode==BM_SLICE||v->mode==BM_COLLECTION)a_mem(true,0,0,v->mode==BM_SLICE?0:24,8);a_imm(2,(uint64_t)value_size(v->element));a_rr(0x9b007c00,1,1,2);a_rr(0x8b000000,0,0,1);break;
    case BV_LOAD:a_value(v->a);a_load(v->type);break;
    case BV_TAKE:a_value(v->a);a_mov(2,0);a_load(v->type);a_mem(false,31,2,0,8);break;
    case BV_UNARY:a_value(v->a);a_unary(v->op,v->a->type);break;
    case BV_BINARY:a_value(v->a);if(v->op==T_AND||v->op==T_OR){int done=new_label();a_test(0);a_cond(v->op==T_AND?0:1,done);a_value(v->b);mark(done,&code);}else{a_push(0);a_value(v->b);a_mov(1,0);a_pop(0);a_operation(v->op,v->a->type,v->b->type,v->site);}break;
    case BV_CAST:a_value(v->a);a_cast(v->a->type,v->type);break;
    case BV_CALL:a_call_value(v);break;case BV_CONSTRUCT:a_construct(v);break;
    case BV_ARRAY:a_value(v->a);a_push(0);for(int i=0;i<v->arguments.n;i++){a_value(v->arguments.v[i]);a_push(0);a_call(v->callee->label);a_clean(1);}a_pop(0);break;
    case BV_TYPE_TEST:case BV_DOWNCAST:{a_value(v->a);a_push(0);int yes=new_label(),done=new_label(),no=new_label();a_test(0);a_cond(0,no);a_mem(true,2,0,0,8);for(int i=0;i<v->matches.n;i++){a_address(1,((Class*)v->matches.v[i])->label);a_cmp(1,2);a_cond(0,yes);}mark(no,&code);a_clean(1);a_imm(0,0);a_branch(done);mark(yes,&code);a_pop(0);if(v->kind==BV_TYPE_TEST)a_imm(0,1);mark(done,&code);break;}
    case BV_STRING_INDEX:a_value(v->a);a_push(0);a_value(v->b);a_mov(1,0);a_pop(0);a_site(2,v->site);a_rt(RT_strbyte);break;
    case BV_UTF8:a_address(0,string_label(v->text,v->length));a_local(2,v->temp);a_mem(false,0,2,0,8);a_imm(0,v->length);a_mem(false,0,2,8,8);a_mov(0,2);break;
    case BV_SLICE:{a_value(v->a);a_nonnull(v->site);a_mem(true,1,0,v->mode==BM_SLICE?8:-16,8);if(v->mode==BM_SLICE)a_mem(true,0,0,0,8);else{a_imm(2,(uint64_t)value_size(v->element));a_rr(0x9ac00800,1,1,2);}a_push(0);a_push(1);a_value(v->arguments.v[1]);a_push(0);a_value(v->arguments.v[2]);a_mov(2,0);a_pop(0);a_pop(1);a_pop(3);int ok=new_label(),enough=new_label();a_cmp(0,1);a_cond(9,ok);a_panic(9,v->site);mark(ok,&code);a_rr(0xcb000000,1,1,0);a_cmp(2,1);a_cond(9,enough);a_panic(9,v->site);mark(enough,&code);a_imm(1,(uint64_t)value_size(v->element));a_rr(0x9b007c00,0,0,1);a_rr(0x8b000000,3,3,0);a_local(0,v->temp);a_mem(false,3,0,0,8);a_mem(false,2,0,8,8);break;}
    case BV_ALLOC:a_value(v->a);if(v->op==T_BUFFER||v->op==T_TRY_BUFFER){
        int ok=new_label(),sized=new_label();a_imm(1,(uint64_t)INT64_MAX/(unsigned)value_size(v->element));a_cmp(0,1);a_cond(9,ok);
        if(v->op==T_TRY_BUFFER){a_imm(0,UINT64_MAX);a_branch(sized);}else a_panic(4,v->site);
        mark(ok,&code);a_imm(1,(uint64_t)value_size(v->element));a_rr(0x9b007c00,0,0,1);mark(sized,&code);
    }a_site(1,v->site);a_rt(v->op==T_TRY_BUFFER?RT_try_alloc:RT_alloc);break;
    case BV_LENGTH:a_value(v->a);if(slice_type(v->a->type)||collection_of(v->a->type)){a_nonnull(v->site);a_mem(true,0,0,8,8);}else if(v->a->type.depth){a_nonnull(v->site);a_mem(true,0,0,-16,8);a_imm(1,(uint64_t)value_size(pointed(v->a->type)));a_rr(0x9ac00800,0,0,1);}else a_rt(RT_len);break;
    case BV_ASSERT:{a_value(v->a);int ok=new_label();a_test(0);a_cond(1,ok);if(v->arguments.n==2){a_value(v->arguments.v[1]);a_imm(1,2);a_rt(RT_print_str);a_imm(0,10);a_imm(1,2);a_rt(RT_print_char);}a_panic(10,v->site);mark(ok,&code);break;}
    case BV_NONNULL:a_value(v->a);a_nonnull(v->site);break;case BV_REINTERPRET:a_value(v->a);break;case BV_RUNTIME:a_runtime(v);break;case BV_MATERIALIZE:a_value(v->a);a_local(2,v->local);a_store(v->type);break;
    default:fatal("ARM64: valor IR inválido %d",v->kind);
    }a_normal(v->type);
}
static void a_instruction(BackendInstruction*op){
    switch(op->kind){case BI_SITE:if(debug_symbols){DebugSite*s=mem(sizeof(*s));s->offset=code.n;s->token=op->site;push(&debug_sites,s);}break;case BI_SCOPE_BEGIN:op->scope->code_start=code.n;break;case BI_SCOPE_END:op->scope->code_end=code.n;break;
    case BI_EVAL:a_value(op->value);break;case BI_STORE_LOCAL:a_value(op->value);a_store_local(op->local);break;
    case BI_STORE_MEMORY:a_value(op->address);a_push(0);if(op->replace){a_value(op->value);a_push(0);a_mem(true,0,31,16,8);a_load(op->type);a_release(op->type);a_pop(0);a_pop(2);a_store(op->type);break;}if(op->op=='=')a_value(op->value);else{a_load(op->type);a_push(0);a_value(op->value);a_mov(1,0);a_pop(0);a_operation(op->op,op->type,op->value->type,op->site);}a_pop(2);a_store(op->type);break;
    case BI_DROP_LOCAL:a_load_local(0,op->local);a_release(op->type);break;case BI_DROP_VALUE:a_value(op->value);a_release(op->type);break;
    case BI_FREE_SLOT:a_value(op->address);a_push(0);a_load(op->type);a_release(op->type);a_pop(2);a_mem(false,31,2,0,8);break;
    case BI_SAVE_RETURN:if(op->value)a_value(op->value);else a_imm(0,0);if(inline_type(op->type)){a_mem(true,2,29,16+16*(generating->params.n+(generating->owner?1:0)),8);a_store(op->type);}if(op->preserve)a_push(0);break;
    case BI_PRINT:for(int i=0;i<op->values.n;i++){a_value(op->values.v[i]);a_push(0);}for(int i=0;i<op->values.n;i++){if(i&&op->op!=T_WRITE){a_imm(0,32);a_imm(1,1);a_rt(RT_print_char);}BackendValue*v=op->values.v[i];Type t=v->type;a_mem(true,0,31,(op->values.n-1-i)*16,8);if(t.kind==TY_F32&&!t.depth)a_cast(t,(Type){TY_F64,0,NULL,NULL});a_imm(1,1);if(slice_type(t)){a_mem(true,2,0,8,8);a_mem(true,1,0,0,8);a_imm(0,1);a_rt(RT_write);}else a_rt(floating(t)?RT_print_float:unsigned_integer(t)&&t.kind!=TY_U8?RT_print_uint:numeric(t)?RT_print_int:equal_type(t,type_bool)?RT_print_bool:equal_type(t,type_str)?RT_print_str:RT_print_ptr);}a_clean(op->values.n);if(op->op!=T_WRITE){a_imm(0,10);a_imm(1,1);a_rt(RT_print_char);}break;
    default:fatal("ARM64: instrução IR inválida");}
}
static void a_function(BackendFunction*f){
    for(int i=0;i<f->blocks.n;i++)((BackendBlock*)f->blocks.v[i])->label=new_label();for(int i=0;i<f->layout.n;i++){BackendBlock*b=f->layout.v[i];mark(b->label,&code);for(int j=0;j<b->instructions.n;j++)a_instruction(b->instructions.v[j]);BackendBlock*next=i+1<f->layout.n?f->layout.v[i+1]:NULL;
        switch(b->terminator){case BT_JUMP:if(f->blocks.v[b->yes]!=next)a_branch(((BackendBlock*)f->blocks.v[b->yes])->label);break;case BT_BRANCH:a_value(b->condition);a_test(0);a_cond(0,((BackendBlock*)f->blocks.v[b->no])->label);if(f->blocks.v[b->yes]!=next)a_branch(((BackendBlock*)f->blocks.v[b->yes])->label);break;
        case BT_MATCH:a_value(b->condition);a_mem(true,0,0,0,8);for(int j=0;j<b->cases.n;j++){BackendCase*c=b->cases.v[j];a_imm(1,(uint64_t)c->tag);a_cmp(0,1);a_cond(0,((BackendBlock*)f->blocks.v[c->target])->label);}a_panic(10,b->site);break;
        case BT_RETURN:if(b->return_saved)a_pop(0);a_branch(return_label);break;case BT_TAIL:for(int j=0;j<b->arguments.n;j++){a_value(b->arguments.v[j]);a_push(0);}for(int j=b->arguments.n-1;j>=0;j--){a_pop(0);a_store_local(f->source->params.v[j]);}a_branch(generating_body);break;default:a_panic(7,b->site);break;}
    }
}
/* AAPCS64 scalar bridges, including independent integer and SIMD banks. Darwin
 * packs overflow scalar stack arguments by natural alignment. */
static int a_c_locations(Function*f,int*loc,int*offset){int ints=0,reals=0,stack=0;for(int i=0;i<f->params.n;i++){Type t=((Var*)f->params.v[i])->ty;if(floating(t)&&reals<8)loc[i]=32+reals++;else if(!floating(t)&&ints<8)loc[i]=ints++;else{int size=target_macos?scalar_bytes(t):8;if(size>8||t.depth)size=8;stack=(stack+size-1)&-size;loc[i]=-1;offset[i]=stack;stack+=size;}}return (stack+15)&-16;}
static void a_c_import(Function*f){int loc[64],offset[64];int reserve=a_c_locations(f,loc,offset);a_ins(0xa9bf7bfd);a_mov(29,31);a_add(31,31,-reserve);for(int i=0;i<f->params.n;i++){Type t=((Var*)f->params.v[i])->ty;a_mem(true,9,29,16+16*(f->params.n-1-i),8);if(loc[i]>=32)a_fp_in(loc[i]-32,9,t);else if(loc[i]>=0)a_mov(loc[i],9);else a_mem(false,9,31,offset[i],target_macos?value_size(t):8);}a_address(16,f->import_label);a_mem(true,16,16,0,8);a_ins(0xd63f0200);if(floating(f->result))a_fp_out(0,0,f->result);a_normal(f->result);a_mov(31,29);a_ins(0xa8c17bfd);a_ins(0xd65f03c0);}
static void a_c_callback(Function*f){int loc[64],offset[64];(void)a_c_locations(f,loc,offset);mark(f->callback_label,&code);a_ins(0xa9bf7bfd);a_mov(29,31);a_add(31,31,-((f->params.n*8+31)&-16));a_mem(false,27,29,-8,8);for(int i=0;i<f->params.n;i++){Type t=((Var*)f->params.v[i])->ty;if(loc[i]>=32)a_fp_out(9,loc[i]-32,t);else if(loc[i]>=0)a_mov(9,loc[i]);else a_mem(true,9,29,16+offset[i],target_macos?value_size(t):8);a_mem(false,9,29,-16-i*8,8);}a_address(27,callback_state_label);a_mem(true,27,27,0,8);a_mov(0,31);a_mem(true,1,27,104,8);a_cmp(0,1);int low=new_label(),high=new_label();a_cond(2,low);a_panic(11,f->t);mark(low,&code);a_mem(true,1,27,96,8);a_cmp(0,1);a_cond(9,high);a_panic(11,f->t);mark(high,&code);for(int i=0;i<f->params.n;i++){Type t=((Var*)f->params.v[i])->ty;a_mem(true,0,29,-16-i*8,8);a_normal(t);a_push(0);}a_call(f->label);a_clean(f->params.n);if(floating(f->result))a_fp_in(0,0,f->result);a_mem(true,27,29,-8,8);a_mov(31,29);a_ins(0xa8c17bfd);a_ins(0xd65f03c0);}
static void generate_arm64(void){
    if(target_macos)bytes(&code,runtime_arm64_macos,sizeof(runtime_arm64_macos));else bytes(&code,runtime_arm64_linux,sizeof(runtime_arm64_linux));while(code.n%4)u8(&code,0);
    for(int i=0;i<all_functions.n;i++){Function*f=all_functions.v[i];f->label=new_label();if(f->foreign)f->import_label=native_import(f->foreign_library[0],f->foreign_symbol);if(f->callback){f->callback_label=new_label();if(callback_state_label<0)callback_state_label=new_label();}}
    for(int i=0;i<classes.n;i++){Class*c=classes.v[i];c->label=new_label();if(has_owned_fields(c)||!c->record)c->drop_label=new_label();}
    entry_offset=code.n;a_mov(19,31);if(target_macos){a_mov(20,0);a_mov(21,1);}else{a_mem(true,20,19,0,8);a_add(21,19,8);}a_mov(0,19);size_t init=target_macos?AMRT_init:ART_init;a_ins(0x94000000u|((uint32_t)(((int64_t)init-(int64_t)code.n)/4)&0x3ffffff));a_mov(27,0);a_mov(0,20);a_mov(1,21);a_rt(RT_args_init);a_imm(0,debug_memory?1:0);a_mem(false,0,27,88,8);if(callback_state_label>=0){a_address(0,callback_state_label);a_mem(false,27,0,0,8);}a_call(main_function->label);a_push(0);a_rt(RT_finish);a_pop(0);if(isvoid(main_function->result))a_imm(0,0);a_mov(3,27);size_t exitrt=target_macos?AMRT_exit:ART_exit;a_ins(0x94000000u|((uint32_t)(((int64_t)exitrt-(int64_t)code.n)/4)&0x3ffffff));a_ins(0xd4200000);
    for(int i=0;i<all_functions.n;i++){Function*f=all_functions.v[i];generating=f;mark(f->label,&code);return_label=new_label();if(f->foreign){a_c_import(f);f->code_end=code.n;continue;}a_ins(0xa9bf7bfd);a_mov(29,31);int frame_slots=f->slots+(f->owner?1:0);int locals=((frame_slots+4)*8+15)&-16;a_mov(0,31);a_add(0,0,-locals);a_mem(true,1,27,104,8);a_cmp(0,1);int ok=new_label();a_cond(2,ok);a_panic(11,f->t);mark(ok,&code);a_add(31,31,-locals);for(int k=0;k<4;k++)a_mem(false,19+k,29,-8*(frame_slots+k+1),8);int count=f->params.n+(f->owner?1:0);if(f->owner){a_mem(true,0,29,16+16*(count-1),8);a_mem(false,0,29,-8,8);}for(int j=0;j<f->params.n;j++){a_mem(true,0,29,16+16*(count-1-j-(f->owner?1:0)),8);a_store_local(f->params.v[j]);}generating_body=new_label();mark(generating_body,&code);a_function(backend_function(f));mark(return_label,&code);for(int k=0;k<4;k++)a_mem(true,19+k,29,-8*(frame_slots+k+1),8);a_mov(31,29);a_ins(0xa8c17bfd);a_ins(0xd65f03c0);f->code_end=code.n;}
    for(int i=0;i<all_functions.n;i++){Function*f=all_functions.v[i];if(f->callback)a_c_callback(f);}
    for(int i=0;i<classes.n;i++){Class*c=classes.v[i];if(!has_owned_fields(c)&&c->record)continue;mark(c->drop_label,&code);a_ins(0xa9bf7bfd);a_mov(29,31);a_mov(0,31);a_add(0,0,-16);a_mem(true,1,27,104,8);a_cmp(0,1);int drop_ok=new_label();a_cond(2,drop_ok);a_panic(11,c->t);mark(drop_ok,&code);a_add(31,31,-16);a_mem(true,0,29,16,8);a_mem(false,0,29,-8,8);int done=new_label();a_test(0);a_cond(0,done);Function*d=find_method(c,"drop",NULL);if(d){a_push(0);a_call(d->label);a_clean(1);}for(int k=0;k<(c->tagged?c->variants.n:1);k++){Vec fields=c->tagged?((Variant*)c->variants.v[k])->fields:c->fields;int next=new_label();if(c->tagged){a_mem(true,0,29,-8,8);a_mem(true,0,0,0,8);a_imm(1,(uint64_t)((Variant*)c->variants.v[k])->tag);a_cmp(0,1);a_cond(1,next);}for(int j=fields.n-1;j>=0;j--){Field*f=fields.v[j];if(f->owned){a_mem(true,0,29,-8,8);a_add(0,0,f->offset);a_load(f->ty);a_release(f->ty);}}mark(next,&code);}a_mem(true,0,29,-8,8);a_rt(RT_free);mark(done,&code);a_mov(31,29);a_ins(0xa8c17bfd);a_ins(0xd65f03c0);}
    while(data.n%8)u8(&data,0);for(int i=0;i<classes.n;i++){Class*c=classes.v[i];if(!c->record)fix(&data,c->drop_label,false);mark(c->label,&data);if(!c->methods.n)u64(&data,0);for(int j=0;j<c->methods.n;j++)fix(&data,((Function*)c->methods.v[j])->label,false);}if(!data.n)u8(&data,0);
}
static void apply_arm_fixes(uint64_t base,size_t text_rva,size_t data_rva){for(int i=0;i<arm_fixes.n;i++){ArmFix*f=arm_fixes.v[i];Label*l=labels.v[f->label];if(!l->defined)fatal("ARM64: rótulo não definido");uint64_t pc=base+text_rva+f->at,address=base+(l->section==2?native_import_rva:l->section?data_rva:text_rva)+l->position;uint32_t ins;
    if(f->kind==2){int64_t pages=(int64_t)(address>>12)-(int64_t)(pc>>12);if(pages<-(1<<20)||pages>=(1<<20))fatal("ARM64: endereço fora do alcance");ins=0x90000000u|(((uint32_t)pages&3)<<29)|((((uint32_t)pages>>2)&0x7ffff)<<5)|(unsigned)f->reg;uint32_t add=0x91000000u|((unsigned)(address&4095)<<10)|((unsigned)f->reg<<5)|(unsigned)f->reg;for(int j=0;j<4;j++)code.v[f->at+4+(size_t)j]=(unsigned char)(add>>(8*j));}
    else{int64_t d=(int64_t)address-(int64_t)pc;if(d%4||d<-(1<<27)||d>=(1<<27))fatal("ARM64: salto fora do alcance");ins=(f->kind==1?0x94000000u:0x14000000u)|((uint32_t)(d/4)&0x3ffffff);}for(int j=0;j<4;j++)code.v[f->at+(size_t)j]=(unsigned char)(ins>>(8*j));}}

/* Explicit scalar C ABI bridges. The language ABI remains LVS2. */
static int native_import(char *library,char *symbol){
    for(int i=0;i<native_imports.n;i++){NativeImport *p=native_imports.v[i];if(same(p->library,library)&&same(p->symbol,symbol))return p->label;
        if(!target_windows&&same(p->symbol,symbol))fatal("ELF: símbolo C ambíguo em bibliotecas diferentes: %s",symbol);}
    if(native_imports.n>=1024)fatal("limite de 1024 imports C excedido");
    NativeImport *p=mem(sizeof(*p));p->library=library;p->symbol=symbol;p->label=new_label();push(&native_imports,p);return p->label;
}
static void import_slot(int label,size_t offset){Label *l=labels.v[label];l->defined=true;l->section=2;l->position=offset;}
static void c_reg_from_rax(unsigned reg){u8(&code,reg>=8?0x49:0x48);u8(&code,0x89);u8(&code,0xc0+(reg&7));}
static void c_rax_from_reg(unsigned reg){u8(&code,reg>=8?0x4c:0x48);u8(&code,0x89);u8(&code,0xc0+(reg&7)*8);}
static void c_xmm_from_rax(unsigned reg,Type t){INS(0x66);if(t.kind==TY_F64)u8(&code,0x48);INS(0x0f,0x6e);u8(&code,0xc0+reg*8);}
static void c_rax_from_xmm(unsigned reg,Type t){INS(0x66);if(t.kind==TY_F64)u8(&code,0x48);INS(0x0f,0x7e);u8(&code,0xc0+reg*8);}
/* Register allocation follows the two independent SysV classes; Microsoft
 * uses positional slots. Negative entries encode stack slots. */
static int c_locations(Function *f,int *locations){
    const unsigned sysv[]={7,6,2,1,8,9},ms[]={1,2,8,9};int ints=0,reals=0,stack=0;
    for(int i=0;i<f->params.n;i++){Type t=((Var*)f->params.v[i])->ty;
        if(target_windows){if(i<4)locations[i]=floating(t)?16+i:(int)ms[i];else locations[i]=-1-stack++;}
        else if(floating(t)){locations[i]=reals<8?16+reals++:-1-stack++;}
        else locations[i]=ints<6?(int)sysv[ints++]:-1-stack++;
    }return stack;
}
static void emit_c_import(Function *f){
    int locations[64],stack=c_locations(f,locations);unsigned reserve=(unsigned)((target_windows?32:0)+stack*8);reserve=(reserve+15)&~15u;
    INS(0x55,0x48,0x89,0xe5,0x48,0x83,0xe4,0xf0,0x48,0x81,0xec);u32(&code,reserve);
    for(int i=0;i<f->params.n;i++){
        Type t=((Var*)f->params.v[i])->ty;INS(0x48,0x8b,0x85);u32(&code,(uint32_t)(16+8*(f->params.n-1-i)));
        int loc=locations[i];if(loc>=16)c_xmm_from_rax((unsigned)(loc-16),t);else if(loc>=0)c_reg_from_rax((unsigned)loc);
        else{INS(0x48,0x89,0x84,0x24);u32(&code,(uint32_t)((target_windows?32:0)+(-1-loc)*8));}
    }
    /* AL=0: prototypes are fixed arity, never C varargs. */
    INS(0x31,0xc0,0xff,0x15);fix(&code,f->import_label,true);
    if(floating(f->result))c_rax_from_xmm(0,f->result);
    normalize_numeric(f->result);
    INS(0xc9,0xc3);
}
static void emit_c_callback(Function *f){
    int locations[64];(void)c_locations(f,locations);mark(f->callback_label,&code);
    unsigned reserve=(unsigned)((f->params.n+3)*8);reserve=(reserve+15)&~15u;
    INS(0x55,0x48,0x89,0xe5,0x48,0x81,0xec);u32(&code,reserve);
    INS(0x4c,0x89,0xbd);u32(&code,(uint32_t)(-8*(f->params.n+3)));
    INS(0x4c,0x8b,0x3d);fix(&code,callback_state_label,true);
    if(target_windows){INS(0x48,0x89,0xbd);u32(&code,(uint32_t)(-8*(f->params.n+1)));INS(0x48,0x89,0xb5);u32(&code,(uint32_t)(-8*(f->params.n+2)));}
    for(int i=0;i<f->params.n;i++){
        Type t=((Var*)f->params.v[i])->ty;int loc=locations[i];
        if(loc>=16)c_rax_from_xmm((unsigned)(loc-16),t);else if(loc>=0)c_rax_from_reg((unsigned)loc);
        else{INS(0x48,0x8b,0x85);u32(&code,(uint32_t)((target_windows?48:16)+(-1-loc)*8));}
        /* C leaves upper bits unspecified for narrow scalar arguments. */
        normalize_numeric(t);INS(0x48,0x89,0x85);u32(&code,(uint32_t)(-8*(i+1)));
    }
    /* Synchronous callbacks only: reject stacks outside the original runtime
     * stack interval before entering code that can allocate or mutate state. */
    int low=new_label(),high=new_label();movreg(RAX,RSP);INS(0x49,0x3b,0x47,0x68);branch_if(0x83,low);panic_at(11,f->t);mark(low,&code);
    INS(0x49,0x3b,0x47,0x60);branch_if(0x86,high);panic_at(11,f->t);mark(high,&code);
    for(int i=0;i<f->params.n;i++){INS(0xff,0xb5);u32(&code,(uint32_t)(-8*(i+1)));}
    call_label(f->label);clean_stack(f->params.n);
    if(floating(f->result))c_xmm_from_rax(0,f->result);
    if(target_windows){INS(0x48,0x8b,0xbd);u32(&code,(uint32_t)(-8*(f->params.n+1)));INS(0x48,0x8b,0xb5);u32(&code,(uint32_t)(-8*(f->params.n+2)));}
    INS(0x4c,0x8b,0xbd);u32(&code,(uint32_t)(-8*(f->params.n+3)));
    INS(0xc9,0xc3);
}

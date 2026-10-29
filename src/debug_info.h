/* DWARF v4 line tables/subprograms and ELF symbols. No local-variable fiction. */
static void debug_u16(Buffer *b,unsigned n){u8(b,n);u8(b,n>>8);}
static void debug_patch32(Buffer *b,size_t at,uint32_t n){for(int i=0;i<4;i++)b->v[at+(size_t)i]=(unsigned char)(n>>(8*i));}
static void debug_uleb(Buffer *b,uint64_t n){do{unsigned byte=(unsigned)(n&127);n>>=7;u8(b,byte|(n?128:0));}while(n);}
static void debug_sleb(Buffer *b,int64_t n){bool more;do{unsigned byte=(unsigned)n&127;n>>=7;more=!((n==0&&!(byte&64))||(n==-1&&(byte&64)));u8(b,byte|(more?128:0));}while(more);}
static unsigned debug_file(SourceFile *file){for(int i=0;i<source_files.n;i++)if(source_files.v[i]==file)return (unsigned)i+1;return 1;}
typedef struct {uint32_t name,type;uint64_t flags,addr,offset,size;uint32_t link,info;uint64_t alignment,entry_size;} DebugSection;
typedef struct {uint32_t name;uint8_t info,other;uint16_t section;uint64_t value,size;} DebugSymbol;
_Static_assert(sizeof(DebugSection)==64,"section header ELF64");
_Static_assert(sizeof(DebugSymbol)==24,"symbol ELF64");
static Buffer debug_tail;
static uint32_t debug_scalar_types[TY_SLICE+1];
static void debug_variable(Buffer *info,Var *v,bool parameter){
    if(!v||v->ty.depth||(!numeric(v->ty)&&!floating(v->ty)&&!equal_type(v->ty,type_bool)))return;
    u8(info,parameter?4:5);bytes(info,v->t->text,strlen(v->t->text)+1);u32(info,debug_scalar_types[v->ty.kind]);
    Buffer location={0};if(optimize&&v->reg>=0){u8(&location,0x50+(unsigned)v->reg);}else{u8(&location,0x91);debug_sleb(&location,-8*(v->slot+1));}
    debug_uleb(info,location.n);bytes(info,location.v,location.n);free(location.v);
}
static void debug_scope(Buffer *info,Node *n){
    if(!n||n->code_end<=n->code_start)return;
    bool block=n->kind==N_BLOCK;
    if(block){u8(info,6);u64(info,ELF_BASE+4096+n->code_start);u64(info,n->code_end-n->code_start);}
    if(n->kind==N_LET)debug_variable(info,n->var,false);
    if(n->kind==N_MATCH){for(int i=0;i<n->items.n;i++){Node *arm=n->items.v[i];u8(info,6);u64(info,ELF_BASE+4096+arm->a->code_start);u64(info,arm->a->code_end-arm->a->code_start);for(int j=0;j<arm->items.n;j++)debug_variable(info,((Node*)arm->items.v[j])->var,false);debug_scope(info,arm->a);u8(info,0);}}
    else if(block){for(int i=0;i<n->items.n;i++)debug_scope(info,n->items.v[i]);}
    else{debug_scope(info,n->a);debug_scope(info,n->b);debug_scope(info,n->c);debug_scope(info,n->step);}
    if(block)u8(info,0);
}
static void debug_backend_scope(Buffer *info,BackendScope *scope){
    if(!scope||scope->code_end<=scope->code_start)return;
    u8(info,6);u64(info,ELF_BASE+4096+scope->code_start);u64(info,scope->code_end-scope->code_start);
    for(int i=0;i<scope->variables.n;i++)debug_variable(info,scope->variables.v[i],false);
    for(int i=0;i<scope->children.n;i++)debug_backend_scope(info,scope->children.v[i]);u8(info,0);
}
static void append_debug_elf(Elf64_Ehdr *eh,size_t start){
    Buffer line={0},abbrev={0},info={0},str={0},sym={0},names={0};
    u32(&line,0);debug_u16(&line,4);u32(&line,0);u8(&line,1);u8(&line,1);u8(&line,1);u8(&line,251);u8(&line,14);u8(&line,13);
    const unsigned char lengths[]={0,1,1,1,1,0,0,0,1,0,0,1};bytes(&line,lengths,sizeof(lengths));u8(&line,0);
    for(int i=0;i<source_files.n;i++){SourceFile *s=source_files.v[i];bytes(&line,s->path,strlen(s->path)+1);debug_uleb(&line,0);debug_uleb(&line,0);debug_uleb(&line,0);}u8(&line,0);debug_patch32(&line,6,(uint32_t)(line.n-10));
    uint64_t address=0;int old_line=1;unsigned old_file=1;
    for(int i=0;i<debug_sites.n;i++){
        DebugSite *site=debug_sites.v[i];uint64_t next=ELF_BASE+4096+site->offset;
        if(!address){u8(&line,0);debug_uleb(&line,9);u8(&line,2);u64(&line,next);}else{u8(&line,2);debug_uleb(&line,next-address);}address=next;
        unsigned file=debug_file(site->token->file);if(file!=old_file){u8(&line,4);debug_uleb(&line,file);old_file=file;}
        if(site->token->line!=old_line){u8(&line,3);debug_sleb(&line,site->token->line-old_line);old_line=site->token->line;}u8(&line,1);
    }
    if(address){u8(&line,2);debug_uleb(&line,ELF_BASE+4096+code.n-address);}u8(&line,0);u8(&line,1);u8(&line,1);debug_patch32(&line,0,(uint32_t)(line.n-4));
    const unsigned char abbreviations[]={
        1,0x11,1,0x25,8,3,8,0x10,0x17,0x11,1,0x12,7,0,0,
        2,0x2e,1,3,8,0x11,1,0x12,7,0x3a,6,0x3b,6,0x40,0x18,0,0,
        3,0x24,0,3,8,0x0b,0x0b,0x3e,0x0b,0,0,
        4,0x05,0,3,8,0x49,0x13,2,0x18,0,0,
        5,0x34,0,3,8,0x49,0x13,2,0x18,0,0,
        6,0x0b,1,0x11,1,0x12,7,0,0,0};bytes(&abbrev,abbreviations,sizeof(abbreviations));
    u32(&info,0);debug_u16(&info,4);u32(&info,0);u8(&info,8);u8(&info,1);bytes(&info,"AssisScript " VERSION,sizeof("AssisScript " VERSION));SourceFile *root=source_files.v[0];bytes(&info,root->path,strlen(root->path)+1);u32(&info,0);u64(&info,ELF_BASE+4096);u64(&info,code.n);
    for(int k=0;k<=TY_F64;k++){Type t={(TypeKind)k,0,NULL,NULL};if(!numeric(t)&&!floating(t)&&!equal_type(t,type_bool))continue;debug_scalar_types[k]=(uint32_t)info.n;u8(&info,3);const char *name=type_name(t);bytes(&info,name,strlen(name)+1);u8(&info,(unsigned)value_bytes(t));u8(&info,floating(t)?4:equal_type(t,type_bool)?2:unsigned_integer(t)?7:5);}
    u8(&str,0);DebugSymbol empty={0};bytes(&sym,&empty,sizeof(empty));
    for(int i=0;i<all_functions.n;i++){
        Function *f=all_functions.v[i];Label *label=labels.v[f->label];uint64_t low=ELF_BASE+4096+label->position,size=f->code_end-label->position;
        u8(&info,2);bytes(&info,f->t->text,strlen(f->t->text)+1);u64(&info,low);u64(&info,size);u32(&info,debug_file(f->t->file));u32(&info,(uint32_t)f->t->line);
        u8(&info,1);u8(&info,0x56); /* DW_AT_frame_base = DW_OP_reg6 (rbp). */
        if(!f->foreign){for(int j=0;j<f->params.n;j++)debug_variable(&info,f->params.v[j],true);if(optimize)debug_backend_scope(&info,backend_function(f)->scope);else debug_scope(&info,f->body);}u8(&info,0);
        const char *name=f->t->text;char *method=NULL;if(f->owner){method=qualified_name(f->owner->display?f->owner->display:f->owner->t->text,name);name=method;}
        DebugSymbol symbol={(uint32_t)str.n,0x12,0,1,low,size};bytes(&str,name,strlen(name)+1);bytes(&sym,&symbol,sizeof(symbol));free(method);
    }u8(&info,0);debug_patch32(&info,0,(uint32_t)(info.n-4));
    DebugSection sections[9]={0};const char *section_names[]={"",".text",".rodata",".strtab",".symtab",".debug_line",".debug_info",".debug_abbrev",".shstrtab"};u8(&names,0);
    for(int i=1;i<9;i++){sections[i].name=(uint32_t)names.n;bytes(&names,section_names[i],strlen(section_names[i])+1);}
    sections[1].type=1;sections[1].flags=6;sections[1].addr=ELF_BASE+4096;sections[1].offset=4096;sections[1].size=code.n;sections[1].alignment=16;
    sections[2].type=1;sections[2].flags=2;sections[2].offset=align_page(4096+code.n);sections[2].addr=ELF_BASE+sections[2].offset;sections[2].size=data.n;sections[2].alignment=8;
    Buffer buffers[]={str,sym,line,info,abbrev,names};
    for(int i=3;i<9;i++){while((start+debug_tail.n)%8)u8(&debug_tail,0);sections[i].offset=start+debug_tail.n;sections[i].size=buffers[i-3].n;sections[i].type=(i==3||i==8)?3:i==4?2:1;sections[i].alignment=1;bytes(&debug_tail,buffers[i-3].v,buffers[i-3].n);}
    sections[4].link=3;sections[4].info=1;sections[4].alignment=8;sections[4].entry_size=sizeof(DebugSymbol);
    while((start+debug_tail.n)%8)u8(&debug_tail,0);eh->e_shoff=start+debug_tail.n;eh->e_shentsize=64;eh->e_shnum=9;eh->e_shstrndx=8;bytes(&debug_tail,sections,sizeof(sections));
}
static void write_debug_map(const char *output){
    size_t n=strlen(output)+16;char *path=mem(n);snprintf(path,n,"%s.map.json",output);protect_output(path);FILE *out=fopen(path,"wb");if(!out)fatal("não foi possível criar mapa de depuração");
    fprintf(out,"{\"format\":\"AssisScript-map-v1\",\"imageBase\":%llu,\"textRva\":4096,\"functions\":[",(unsigned long long)(target_windows?UINT64_C(0x140000000):ELF_BASE));
    for(int i=0;i<all_functions.n;i++){Function *f=all_functions.v[i];Label *label=labels.v[f->label];if(i)fputc(',',out);fputs("{\"name\":",out);json_string(out,f->t->text);fprintf(out,",\"rva\":%zu,\"size\":%zu,\"file\":",4096+label->position,f->code_end-label->position);json_string(out,f->t->file->path);fprintf(out,",\"line\":%d}",f->t->line);}
    fputs("],\"lines\":[",out);for(int i=0;i<debug_sites.n;i++){DebugSite *s=debug_sites.v[i];if(i)fputc(',',out);fprintf(out,"{\"rva\":%zu,\"file\":",4096+s->offset);json_string(out,s->token->file->path);fprintf(out,",\"line\":%d}",s->token->line);}fputs("]}\n",out);
    bool ok=!ferror(out);if(fclose(out))ok=false;if(!ok)fatal("erro ao gravar mapa de depuração");free(path);
}

/* Mach-O 64-bit PIE, x86_64, dyld + public libSystem imports. All language
 * references are RIP/slot relative; only the GOT needs dyld bindings.
 * Definitions: Apple's mach-o/loader.h and dyld bind opcode contract.
 */
static void macho_name(Buffer *out,const char *name){char field[16]={0};snprintf(field,sizeof(field),"%s",name);bytes(out,field,sizeof(field));}
static void macho_segment(Buffer *out,const char *name,uint64_t address,size_t offset,size_t file_size,size_t memory_size,unsigned protection,bool text){
    u32(out,0x19);u32(out,text?152:72);macho_name(out,name);u64(out,address);u64(out,memory_size);u64(out,offset);u64(out,file_size);u32(out,protection);u32(out,protection);u32(out,text?1:0);u32(out,0);
    if(text){macho_name(out,"__text");macho_name(out,"__TEXT");u64(out,address+4096);u64(out,code.n);u32(out,4096);u32(out,4);u32(out,0);u32(out,0);u32(out,0x80000400);u32(out,0);u32(out,0);u32(out,0);}
}
static void macho_uleb(Buffer *out,size_t value){do{unsigned byte=(unsigned)(value&127);value>>=7;u8(out,byte|(value?128:0));}while(value);}
static void macho_string_command(Buffer *out,unsigned command,const char *path,bool library){
    size_t header=library?24:12,size=(header+strlen(path)+1+7)&~(size_t)7;
    u32(out,command);u32(out,(uint32_t)size);u32(out,(uint32_t)header);
    if(library){u32(out,0);u32(out,0x10000);u32(out,0x10000);}bytes(out,path,strlen(path)+1);while(out->n%8)u8(out,0);
}
static void macho_be32(Buffer*out,uint32_t n){for(int k=3;k>=0;k--)u8(out,n>>(k*8));}
static void macho_be64(Buffer*out,uint64_t n){macho_be32(out,(uint32_t)(n>>32));macho_be32(out,(uint32_t)n);}
static void macho_sign(Buffer*image,size_t limit,size_t text_limit){
    const char ident[]="org.assisscript.native";size_t slots=(limit+4095)/4096,hash_offset=88+sizeof(ident),length=hash_offset+slots*32;
    Buffer signature={0};macho_be32(&signature,0xfade0cc0);macho_be32(&signature,(uint32_t)(20+length));macho_be32(&signature,1);macho_be32(&signature,0);macho_be32(&signature,20);
    macho_be32(&signature,0xfade0c02);macho_be32(&signature,(uint32_t)length);macho_be32(&signature,0x20400);macho_be32(&signature,0x20002);macho_be32(&signature,(uint32_t)hash_offset);macho_be32(&signature,88);macho_be32(&signature,0);macho_be32(&signature,(uint32_t)slots);macho_be32(&signature,(uint32_t)limit);
    u8(&signature,32);u8(&signature,2);u8(&signature,0);u8(&signature,12);for(int k=0;k<4;k++)macho_be32(&signature,0);macho_be64(&signature,0);macho_be64(&signature,0);macho_be64(&signature,text_limit);macho_be64(&signature,1);bytes(&signature,ident,sizeof(ident));
    for(size_t k=0;k<slots;k++){size_t n=limit-k*4096;if(n>4096)n=4096;char*hex=source_sha256(image->v+k*4096,n);for(int j=0;j<32;j++){unsigned v=0;for(int d=0;d<2;d++){char c=hex[j*2+d];v=(v<<4)|(unsigned)(c<='9'?c-'0':c-'a'+10);}u8(&signature,v);}free(hex);}bytes(image,signature.v,signature.n);free(signature.v);
}
static void write_macho(const char *path){
    const uint64_t base=UINT64_C(0x100000000);
    const char *system="/usr/lib/libSystem.B.dylib";
    if(target_arm64){for(size_t i=0;i<sizeof(arm_macos_import_patches)/sizeof(arm_macos_import_patches[0]);i++)native_import((char*)system,(char*)arm_macos_import_patches[i].name);}
    else for(size_t i=0;i<sizeof(macos_import_patches)/sizeof(macos_import_patches[0]);i++)native_import((char*)system,(char*)macos_import_patches[i].name);
    size_t const_offset=align_page(4096+code.n),got_offset=align_page(const_offset+data.n);
    Buffer got={0},bind={0};Vec libraries={0};push(&libraries,(void*)system);for(int i=0;i<native_imports.n;i++){NativeImport*p=native_imports.v[i];bool found=false;for(int j=0;j<libraries.n;j++)if(same(libraries.v[j],p->library))found=true;if(!found)push(&libraries,p->library);}
    for(int i=0;i<native_imports.n;i++){
        NativeImport *p=native_imports.v[i];int ordinal=1;for(int j=0;j<libraries.n;j++)if(same(libraries.v[j],p->library))ordinal=j+1;
        p->slot=got.n;import_slot(p->label,got.n);u64(&got,0);
        if(ordinal<=15)u8(&bind,0x10|(unsigned)ordinal);else{u8(&bind,0x20);macho_uleb(&bind,(size_t)ordinal);}u8(&bind,0x40);u8(&bind,'_');bytes(&bind,p->symbol,strlen(p->symbol)+1);u8(&bind,0x51);u8(&bind,0x73);macho_uleb(&bind,p->slot);u8(&bind,0x90);
    }
    if(callback_state_label>=0){import_slot(callback_state_label,got.n);u64(&got,0);}u8(&bind,0);
    Buffer dwarf={0},symbols={0},symbol_names={0};size_t dwarf_offsets[3]={0},dwarf_sizes[3]={0};u8(&symbol_names,0);
    if(debug_symbols){Elf64_Ehdr dummy={0};append_debug_elf(&dummy,0);DebugSection*sections=(DebugSection*)(debug_tail.v+dummy.e_shoff);for(int k=0;k<3;k++){while(dwarf.n%8)u8(&dwarf,0);dwarf_offsets[k]=dwarf.n;dwarf_sizes[k]=sections[5+k].size;bytes(&dwarf,debug_tail.v+sections[5+k].offset,sections[5+k].size);}for(int i=0;i<all_functions.n;i++){Function*f=all_functions.v[i];Label*l=labels.v[f->label];u32(&symbols,(uint32_t)symbol_names.n);u8(&symbols,0x0f);u8(&symbols,1);debug_u16(&symbols,0);u64(&symbols,base+4096+l->position);u8(&symbol_names,'_');if(f->owner){const char*owner=f->owner->display?f->owner->display:f->owner->t->text;bytes(&symbol_names,owner,strlen(owner));u8(&symbol_names,'.');}bytes(&symbol_names,f->t->text,strlen(f->t->text)+1);}}
    size_t dwarf_offset=align_page(got_offset+got.n),linkedit_offset=debug_symbols?align_page(dwarf_offset+dwarf.n):dwarf_offset;
    size_t symbols_at=(bind.n+7)&~(size_t)7,names_at=symbols_at+symbols.n,linkedit_size=debug_symbols?names_at+symbol_names.n:bind.n;
    size_t signature_at=(linkedit_offset+linkedit_size+15)&~(size_t)15,signature_size=20+88+sizeof("org.assisscript.native")+32*((signature_at+4095)/4096);
    if(target_arm64)linkedit_size=signature_at-linkedit_offset+signature_size;
    native_import_rva=got_offset;
    for(size_t i=0;i<(target_arm64?sizeof(arm_macos_import_patches)/sizeof(arm_macos_import_patches[0]):sizeof(macos_import_patches)/sizeof(macos_import_patches[0]));i++){
        size_t offset=target_arm64?arm_macos_import_patches[i].offset:macos_import_patches[i].offset;const char*import_name=target_arm64?arm_macos_import_patches[i].name:macos_import_patches[i].name;NativeImport *api=NULL;
        for(int j=0;j<native_imports.n;j++){NativeImport *p=native_imports.v[j];if(same(p->symbol,import_name)){api=p;break;}}
        if(!api)fatal("import macOS desconhecido");int64_t delta=(int64_t)(got_offset+api->slot)-(int64_t)(4096+offset+(target_arm64?0:4));
        if(delta<INT32_MIN||delta>INT32_MAX)fatal("import macOS fora do alcance");for(int j=0;j<(target_arm64?8:4);j++)code.v[offset+(size_t)j]=(unsigned char)((uint64_t)delta>>(j*8));
    }
    apply_fixes(base,4096,const_offset);
    Buffer commands={0};
    macho_segment(&commands,"__PAGEZERO",0,0,0,(size_t)base,0,false);
    macho_segment(&commands,"__TEXT",base,0,4096+code.n,const_offset,5,true);
    macho_segment(&commands,"__DATA_CONST",base+const_offset,const_offset,data.n,got_offset-const_offset,1,false);
    macho_segment(&commands,"__DATA",base+got_offset,got_offset,got.n,linkedit_offset-got_offset,3,false);
    if(debug_symbols){u32(&commands,0x19);u32(&commands,72+3*80);macho_name(&commands,"__DWARF");u64(&commands,base+dwarf_offset);u64(&commands,align_page(dwarf.n));u64(&commands,dwarf_offset);u64(&commands,dwarf.n);u32(&commands,1);u32(&commands,1);u32(&commands,3);u32(&commands,0);const char*names[]={"__debug_line","__debug_info","__debug_abbrev"};for(int k=0;k<3;k++){macho_name(&commands,names[k]);macho_name(&commands,"__DWARF");u64(&commands,base+dwarf_offset+dwarf_offsets[k]);u64(&commands,dwarf_sizes[k]);u32(&commands,(uint32_t)(dwarf_offset+dwarf_offsets[k]));u32(&commands,0);u32(&commands,0);u32(&commands,0);u32(&commands,0x02000000);u32(&commands,0);u32(&commands,0);u32(&commands,0);}}
    macho_segment(&commands,"__LINKEDIT",base+linkedit_offset,linkedit_offset,linkedit_size,align_page(linkedit_size),1,false);
    macho_string_command(&commands,0xe,"/usr/lib/dyld",false);
    for(int i=0;i<libraries.n;i++)macho_string_command(&commands,0xc,libraries.v[i],true);
    u32(&commands,0x80000022);u32(&commands,48);u32(&commands,0);u32(&commands,0);u32(&commands,(uint32_t)linkedit_offset);u32(&commands,(uint32_t)bind.n);for(int i=0;i<6;i++)u32(&commands,0);
    u32(&commands,0x80000028);u32(&commands,24);u64(&commands,4096+entry_offset);u64(&commands,0);
    u32(&commands,0x32);u32(&commands,24);u32(&commands,1);u32(&commands,target_arm64?0x000b0000:0x000a0f00);u32(&commands,target_arm64?0x000b0000:0x000a0f00);u32(&commands,0);
    if(debug_symbols){u32(&commands,2);u32(&commands,24);u32(&commands,(uint32_t)(linkedit_offset+symbols_at));u32(&commands,(uint32_t)all_functions.n);u32(&commands,(uint32_t)(linkedit_offset+names_at));u32(&commands,(uint32_t)symbol_names.n);}
    if(target_arm64){u32(&commands,0x1d);u32(&commands,16);u32(&commands,(uint32_t)signature_at);u32(&commands,(uint32_t)signature_size);}
    if(commands.n+32>4096)fatal("cabeçalho Mach-O excedido");
    Buffer image={0};u32(&image,0xfeedfacf);u32(&image,target_arm64?0x0100000c:0x01000007);u32(&image,target_arm64?0:3);u32(&image,2);u32(&image,9+(unsigned)libraries.n+(debug_symbols?2:0)+(target_arm64?1:0));u32(&image,(uint32_t)commands.n);u32(&image,0x200084);u32(&image,0);
    bytes(&image,commands.v,commands.n);while(image.n<4096)u8(&image,0);bytes(&image,code.v,code.n);while(image.n<const_offset)u8(&image,0);bytes(&image,data.v,data.n);while(image.n<got_offset)u8(&image,0);bytes(&image,got.v,got.n);while(image.n<linkedit_offset)u8(&image,0);bytes(&image,bind.v,bind.n);
    /* Insert the debug segment before __LINKEDIT and retain its file offsets. */
    if(debug_symbols){image.n=got_offset+got.n;while(image.n<dwarf_offset)u8(&image,0);bytes(&image,dwarf.v,dwarf.n);while(image.n<linkedit_offset)u8(&image,0);bytes(&image,bind.v,bind.n);while(image.n<linkedit_offset+symbols_at)u8(&image,0);bytes(&image,symbols.v,symbols.n);bytes(&image,symbol_names.v,symbol_names.n);}
    if(target_arm64){while(image.n<signature_at)u8(&image,0);macho_sign(&image,signature_at,const_offset);if(image.n!=signature_at+signature_size)fatal("assinatura Mach-O inválida");}
    FILE *file=fopen(path,"wb");if(!file)fatal("não foi possível criar %s",path);bool ok=fwrite(image.v,1,image.n,file)==image.n;if(fclose(file))ok=false;
    if(!ok){unlink(path);fatal("erro ao gravar %s",path);}if(chmod(path,0755))fatal("não foi possível marcar %s como executável",path);
    free(image.v);free(commands.v);free(bind.v);free(got.v);free(dwarf.v);free(symbols.v);free(symbol_names.v);free(libraries.v);
}

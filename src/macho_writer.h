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
static void write_macho(const char *path){
    const uint64_t base=UINT64_C(0x100000000);
    const char *system="/usr/lib/libSystem.B.dylib";
    for(size_t i=0;i<sizeof(macos_import_patches)/sizeof(macos_import_patches[0]);i++)native_import((char*)system,(char*)macos_import_patches[i].name);
    size_t const_offset=align_page(4096+code.n),got_offset=align_page(const_offset+data.n);
    Buffer got={0},bind={0};
    for(int i=0;i<native_imports.n;i++){
        NativeImport *p=native_imports.v[i];if(!same(p->library,system))fatal("macOS: extern de usuário ainda não é suportado");
        p->slot=got.n;import_slot(p->label,got.n);u64(&got,0);
        u8(&bind,0x11);u8(&bind,0x40);u8(&bind,'_');bytes(&bind,p->symbol,strlen(p->symbol)+1);u8(&bind,0x51);u8(&bind,0x73);macho_uleb(&bind,p->slot);u8(&bind,0x90);
    }
    if(callback_state_label>=0){import_slot(callback_state_label,got.n);u64(&got,0);}u8(&bind,0);
    size_t linkedit_offset=align_page(got_offset+got.n);
    native_import_rva=got_offset;
    for(size_t i=0;i<sizeof(macos_import_patches)/sizeof(macos_import_patches[0]);i++){
        size_t offset=macos_import_patches[i].offset;NativeImport *api=NULL;
        for(int j=0;j<native_imports.n;j++){NativeImport *p=native_imports.v[j];if(same(p->symbol,macos_import_patches[i].name)){api=p;break;}}
        if(!api)fatal("import macOS desconhecido");int64_t delta=(int64_t)(got_offset+api->slot)-(int64_t)(4096+offset+4);
        if(delta<INT32_MIN||delta>INT32_MAX)fatal("import macOS fora do alcance");for(int j=0;j<4;j++)code.v[offset+(size_t)j]=(unsigned char)((uint32_t)delta>>(j*8));
    }
    apply_fixes(base,4096,const_offset);
    Buffer commands={0};
    macho_segment(&commands,"__PAGEZERO",0,0,0,(size_t)base,0,false);
    macho_segment(&commands,"__TEXT",base,0,4096+code.n,const_offset,5,true);
    macho_segment(&commands,"__DATA_CONST",base+const_offset,const_offset,data.n,got_offset-const_offset,1,false);
    macho_segment(&commands,"__DATA",base+got_offset,got_offset,got.n,linkedit_offset-got_offset,3,false);
    macho_segment(&commands,"__LINKEDIT",base+linkedit_offset,linkedit_offset,bind.n,align_page(bind.n),1,false);
    macho_string_command(&commands,0xe,"/usr/lib/dyld",false);
    macho_string_command(&commands,0xc,system,true);
    u32(&commands,0x80000022);u32(&commands,48);u32(&commands,0);u32(&commands,0);u32(&commands,(uint32_t)linkedit_offset);u32(&commands,(uint32_t)bind.n);for(int i=0;i<6;i++)u32(&commands,0);
    u32(&commands,0x80000028);u32(&commands,24);u64(&commands,4096+entry_offset);u64(&commands,0);
    u32(&commands,0x32);u32(&commands,24);u32(&commands,1);u32(&commands,0x000a0f00);u32(&commands,0x000a0f00);u32(&commands,0);
    if(commands.n+32>4096)fatal("cabeçalho Mach-O excedido");
    Buffer image={0};u32(&image,0xfeedfacf);u32(&image,0x01000007);u32(&image,3);u32(&image,2);u32(&image,10);u32(&image,(uint32_t)commands.n);u32(&image,0x200084);u32(&image,0);
    bytes(&image,commands.v,commands.n);while(image.n<4096)u8(&image,0);bytes(&image,code.v,code.n);while(image.n<const_offset)u8(&image,0);bytes(&image,data.v,data.n);while(image.n<got_offset)u8(&image,0);bytes(&image,got.v,got.n);while(image.n<linkedit_offset)u8(&image,0);bytes(&image,bind.v,bind.n);
    FILE *file=fopen(path,"wb");if(!file)fatal("não foi possível criar %s",path);bool ok=fwrite(image.v,1,image.n,file)==image.n;if(fclose(file))ok=false;
    if(!ok){unlink(path);fatal("erro ao gravar %s",path);}if(chmod(path,0755))fatal("não foi possível marcar %s como executável",path);
    free(image.v);free(commands.v);free(bind.v);free(got.v);
}

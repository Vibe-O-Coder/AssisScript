/* Dynamic dependencies are present only in executables declaring extern.
 * glibc x86_64 loader, eager GLOB_DAT relocations and read-only GOT after load. */
static Buffer elf_imports;
static size_t elf_dynamic_offset,elf_dynamic_size,elf_relro_size;
static void elf_dynamic(uint64_t tag,uint64_t value){u64(&elf_imports,tag);u64(&elf_imports,value);}
static void build_elf_imports(size_t rva){
    Buffer names={0};Vec libraries={0};size_t needed[1024],symbols[1024];u8(&names,0);
    for(int i=0;i<native_imports.n;i++){
        NativeImport *p=native_imports.v[i];bool found=false;for(int j=0;j<libraries.n;j++)if(same(libraries.v[j],p->library))found=true;
        if(!found){needed[libraries.n]=names.n;push(&libraries,p->library);bytes(&names,p->library,strlen(p->library)+1);}
        symbols[i]=names.n;bytes(&names,p->symbol,strlen(p->symbol)+1);
    }
    size_t strtab=elf_imports.n;bytes(&elf_imports,names.v,names.n);while(elf_imports.n%8)u8(&elf_imports,0);
    size_t symtab=elf_imports.n;for(int i=0;i<24;i++)u8(&elf_imports,0);
    for(int i=0;i<native_imports.n;i++){u32(&elf_imports,(uint32_t)symbols[i]);u8(&elf_imports,0x12);u8(&elf_imports,0);u8(&elf_imports,0);u8(&elf_imports,0);u64(&elf_imports,0);u64(&elf_imports,0);}
    size_t hash=elf_imports.n;u32(&elf_imports,1);u32(&elf_imports,(uint32_t)native_imports.n+1);u32(&elf_imports,native_imports.n?1:0);u32(&elf_imports,0);
    for(int i=0;i<native_imports.n;i++)u32(&elf_imports,i+1<native_imports.n?(uint32_t)i+2:0);
    while(elf_imports.n%8)u8(&elf_imports,0);
    size_t got=elf_imports.n;
    for(int i=0;i<native_imports.n;i++){NativeImport *p=native_imports.v[i];import_slot(p->label,elf_imports.n);u64(&elf_imports,0);}
    size_t rela=elf_imports.n;
    for(int i=0;i<native_imports.n;i++){u64(&elf_imports,rva+got+(size_t)i*8);u64(&elf_imports,((uint64_t)(i+1)<<32)|(target_arm64?1025:6));u64(&elf_imports,0);}
    elf_dynamic_offset=elf_imports.n;
    for(int i=0;i<libraries.n;i++)elf_dynamic(1,needed[i]);
    elf_dynamic(5,rva+strtab);elf_dynamic(10,names.n);elf_dynamic(6,rva+symtab);elf_dynamic(11,24);elf_dynamic(4,rva+hash);
    elf_dynamic(7,rva+rela);elf_dynamic(8,(size_t)native_imports.n*24);elf_dynamic(9,24);elf_dynamic(30,8);elf_dynamic(0x6ffffffb,0x08000001);elf_dynamic(0,0);
    elf_dynamic_size=elf_imports.n-elf_dynamic_offset;elf_relro_size=align_page(elf_imports.n);
    if(callback_state_label>=0){while(elf_imports.n<elf_relro_size)u8(&elf_imports,0);import_slot(callback_state_label,elf_imports.n);u64(&elf_imports,0);}
    free(names.v);free(libraries.v);
}

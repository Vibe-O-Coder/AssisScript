/* Emissor PE32+ x64: imports KERNEL32, ASLR, DEP, código sem escrita. */
#ifndef ASSIS_PE_WRITER_H
#define ASSIS_PE_WRITER_H
static void patch16(unsigned char *p,size_t offset,uint16_t value){for(int i=0;i<2;i++)p[offset+(size_t)i]=(unsigned char)(value>>(i*8));}
static void patch32(unsigned char *p,size_t offset,uint32_t value){for(int i=0;i<4;i++)p[offset+(size_t)i]=(unsigned char)(value>>(i*8));}
static void patch64(unsigned char *p,size_t offset,uint64_t value){for(int i=0;i<8;i++)p[offset+(size_t)i]=(unsigned char)(value>>(i*8));}
static size_t align_file(size_t n){return (n+511)&~(size_t)511;}
static int compare_rvas(const void *a,const void *b){uint32_t x=*(const uint32_t*)a,y=*(const uint32_t*)b;return (x>y)-(x<y);}
static void pe_section(unsigned char *header,size_t offset,const char *name,Buffer *b,size_t rva,size_t raw,uint32_t flags){
    memcpy(header+offset,name,strlen(name));patch32(header,offset+8,(uint32_t)b->n);patch32(header,offset+12,(uint32_t)rva);
    patch32(header,offset+16,(uint32_t)align_file(b->n));patch32(header,offset+20,(uint32_t)raw);patch32(header,offset+36,flags);
}
static bool pe_part(FILE *fp,Buffer *b){
    static const unsigned char zero[512]={0};size_t pad=align_file(b->n)-b->n;
    return fwrite(b->v,1,b->n,fp)==b->n&&(!pad||fwrite(zero,1,pad,fp)==pad);
}
static void write_pe(const char *path){
    const uint64_t base=UINT64_C(0x140000000);const size_t text_rva=4096;
    size_t data_rva=align_page(text_rva+code.n),imports_rva=align_page(data_rva+data.n);
    static const char *apis[]={"ExitProcess","GetStdHandle","SetConsoleOutputCP","VirtualAlloc","VirtualFree","WriteFile"};
    enum { API_COUNT=6 };Buffer imports={0},relocs={0};
    unsigned char descriptors[40]={0};bytes(&imports,descriptors,sizeof(descriptors));
    size_t iat=imports.n;for(int i=0;i<=API_COUNT;i++)u64(&imports,0);
    size_t ilt=imports.n;for(int i=0;i<=API_COUNT;i++)u64(&imports,0);
    for(int i=0;i<API_COUNT;i++){
        if(imports.n%2)u8(&imports,0);size_t name=imports.n;u8(&imports,0);u8(&imports,0);
        bytes(&imports,apis[i],strlen(apis[i])+1);
        patch64(imports.v,iat+(size_t)i*8,imports_rva+name);patch64(imports.v,ilt+(size_t)i*8,imports_rva+name);
    }
    size_t dll=imports.n;bytes(&imports,"KERNEL32.dll",13);
    patch32(imports.v,0,(uint32_t)(imports_rva+ilt));patch32(imports.v,12,(uint32_t)(imports_rva+dll));patch32(imports.v,16,(uint32_t)(imports_rva+iat));
    for(size_t p=0;p<sizeof(windows_import_patches)/sizeof(windows_import_patches[0]);p++){
        size_t offset=windows_import_patches[p].offset;int api=-1;
        for(int i=0;i<API_COUNT;i++)if(same(apis[i],windows_import_patches[p].name)){api=i;break;}
        if(api<0)fatal("import Windows desconhecido: %s",windows_import_patches[p].name);
        int64_t delta=(int64_t)(imports_rva+iat+(size_t)api*8)-(int64_t)(text_rva+offset+4);
        if(delta<INT32_MIN||delta>INT32_MAX)fatal("import Windows fora do alcance");patch32(code.v,offset,(uint32_t)(int32_t)delta);
    }
    apply_fixes(base,text_rva,data_rva);
    uint32_t *sites=mem(((size_t)fixes.n+1)*sizeof(uint32_t));size_t total=0;
    for(int i=0;i<fixes.n;i++){
        Fix *f=fixes.v[i];if(!f->relative)sites[total++]=(uint32_t)((f->buffer==&code?text_rva:data_rva)+f->position);
    }
    qsort(sites,total,sizeof(uint32_t),compare_rvas);
    for(size_t i=0;i<total;){
        uint32_t page=sites[i]&~UINT32_C(4095);size_t end=i;while(end<total&&(sites[end]&~UINT32_C(4095))==page)end++;
        size_t n=end-i;uint32_t size=(uint32_t)(8+2*n+(n%2?2:0));u32(&relocs,page);u32(&relocs,size);
        for(;i<end;i++){uint16_t item=(uint16_t)(0xa000|(sites[i]&4095));u8(&relocs,item);u8(&relocs,item>>8);}
        if(n%2){u8(&relocs,0);u8(&relocs,0);}
    }
    free(sites);if(!relocs.n){u32(&relocs,0);u32(&relocs,12);u32(&relocs,0);}
    size_t reloc_rva=align_page(imports_rva+imports.n),text_raw=1024,data_raw=text_raw+align_file(code.n),imports_raw=data_raw+align_file(data.n),reloc_raw=imports_raw+align_file(imports.n);
    unsigned char header[1024]={0};header[0]='M';header[1]='Z';patch32(header,0x3c,0x80);
    static const char stub[]="AssisScript: programa Windows x64.\r\n";memcpy(header+0x40,stub,sizeof(stub)-1);
    size_t pe=0x80;memcpy(header+pe,"PE\0\0",4);patch16(header,pe+4,0x8664);patch16(header,pe+6,4);
    patch16(header,pe+20,240);patch16(header,pe+22,0x22);size_t op=pe+24;
    patch16(header,op,0x20b);header[op+2]=2;header[op+3]=1;
    patch32(header,op+4,(uint32_t)align_file(code.n));patch32(header,op+8,(uint32_t)(align_file(data.n)+align_file(imports.n)+align_file(relocs.n)));
    patch32(header,op+16,(uint32_t)(text_rva+entry_offset));patch32(header,op+20,(uint32_t)text_rva);patch64(header,op+24,base);
    patch32(header,op+32,4096);patch32(header,op+36,512);patch16(header,op+40,6);patch16(header,op+44,2);patch16(header,op+46,1);patch16(header,op+48,6);
    patch32(header,op+56,(uint32_t)align_page(reloc_rva+relocs.n));patch32(header,op+60,sizeof(header));patch16(header,op+68,3);patch16(header,op+70,0x160);
    patch64(header,op+72,UINT64_C(0x100000));patch64(header,op+80,4096);patch64(header,op+88,UINT64_C(0x100000));patch64(header,op+96,4096);patch32(header,op+108,16);
    patch32(header,op+112+8,(uint32_t)imports_rva);patch32(header,op+112+12,40);
    patch32(header,op+112+5*8,(uint32_t)reloc_rva);patch32(header,op+112+5*8+4,(uint32_t)relocs.n);
    patch32(header,op+112+12*8,(uint32_t)(imports_rva+iat));patch32(header,op+112+12*8+4,(API_COUNT+1)*8);
    size_t sh=op+240;
    pe_section(header,sh,".text",&code,text_rva,text_raw,0x60000020);
    pe_section(header,sh+40,".rdata",&data,data_rva,data_raw,0x40000040);
    pe_section(header,sh+80,".idata",&imports,imports_rva,imports_raw,0xc0000040);
    pe_section(header,sh+120,".reloc",&relocs,reloc_rva,reloc_raw,0x42000040);
    protect_output(path);FILE *fp=fopen(path,"wb");if(!fp)fatal("não foi possível criar %s: %s",path,strerror(errno));
    bool ok=fwrite(header,1,sizeof(header),fp)==sizeof(header)&&pe_part(fp,&code)&&pe_part(fp,&data)&&pe_part(fp,&imports)&&pe_part(fp,&relocs);
    if(fclose(fp))ok=false;if(!ok){unlink(path);fatal("erro ao gravar %s",path);}
    free(imports.v);free(relocs.v);
}
#endif

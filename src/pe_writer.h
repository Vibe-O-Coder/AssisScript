/* Emissor PE32+ x64: imports KERNEL32, ASLR, DEP, código sem escrita. */
#ifndef ASSIS_PE_WRITER_H
#define ASSIS_PE_WRITER_H
#include "icon_blob.h"
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
    static const char *apis[]={"ExitProcess","GetStdHandle","SetConsoleOutputCP","VirtualAlloc","VirtualFree","WriteFile","ReadFile","GetTickCount64","GetLastError","CreateFileW","CloseHandle","MultiByteToWideChar","WideCharToMultiByte","GetCommandLineW","LocalFree","Sleep","GetSystemTimeAsFileTime","FlushFileBuffers","MoveFileExW","DeleteFileW","CommandLineToArgvW"};
    enum { KERNEL_COUNT=20,API_COUNT=21 };Buffer imports={0},relocs={0},resources={0};
    Vec imports_all={0},dlls={0};
    for(int i=0;i<API_COUNT;i++){
        NativeImport *p=mem(sizeof(*p));p->library=i<KERNEL_COUNT?"KERNEL32.dll":"SHELL32.dll";p->symbol=(char*)apis[i];p->label=-1;push(&imports_all,p);
    }
    for(int i=0;i<native_imports.n;i++)push(&imports_all,native_imports.v[i]);
    for(int i=0;i<imports_all.n;i++){NativeImport *p=imports_all.v[i];bool found=false;for(int j=0;j<dlls.n;j++)if(same(dlls.v[j],p->library))found=true;if(!found)push(&dlls,p->library);}
    size_t descriptor_size=(size_t)(dlls.n+1)*20;for(size_t i=0;i<descriptor_size;i++)u8(&imports,0);
    size_t iat=imports.n;
    for(int d=0;d<dlls.n;d++){for(int i=0;i<imports_all.n;i++){NativeImport *p=imports_all.v[i];if(same(p->library,dlls.v[d])){p->slot=imports.n;u64(&imports,0);}}u64(&imports,0);}
    size_t iat_size=imports.n-iat;
    for(int d=0;d<dlls.n;d++){
        size_t ilt=imports.n,first=0;int count=0;
        for(int i=0;i<imports_all.n;i++){NativeImport *p=imports_all.v[i];if(same(p->library,dlls.v[d])){if(!count)first=p->slot;count++;u64(&imports,0);}}u64(&imports,0);
        int index=0;
        for(int i=0;i<imports_all.n;i++){
            NativeImport *p=imports_all.v[i];if(!same(p->library,dlls.v[d]))continue;
            if(imports.n%2)u8(&imports,0);size_t name=imports.n;u8(&imports,0);u8(&imports,0);bytes(&imports,p->symbol,strlen(p->symbol)+1);
            patch64(imports.v,p->slot,imports_rva+name);patch64(imports.v,ilt+(size_t)index++*8,imports_rva+name);
            if(p->label>=0)import_slot(p->label,p->slot);
        }
        size_t dll=imports.n;bytes(&imports,dlls.v[d],strlen(dlls.v[d])+1);
        patch32(imports.v,(size_t)d*20,(uint32_t)(imports_rva+ilt));patch32(imports.v,(size_t)d*20+12,(uint32_t)(imports_rva+dll));patch32(imports.v,(size_t)d*20+16,(uint32_t)(imports_rva+first));
    }
    if(callback_state_label>=0){while(imports.n%8)u8(&imports,0);import_slot(callback_state_label,imports.n);u64(&imports,0);}
    native_import_rva=imports_rva;
    for(size_t p=0;p<sizeof(windows_import_patches)/sizeof(windows_import_patches[0]);p++){
        size_t offset=windows_import_patches[p].offset;NativeImport *api=NULL;
        for(int i=0;i<API_COUNT;i++){NativeImport *candidate=imports_all.v[i];if(same(candidate->symbol,windows_import_patches[p].name)){api=candidate;break;}}
        if(!api)fatal("import Windows desconhecido: %s",windows_import_patches[p].name);
        int64_t delta=(int64_t)(imports_rva+api->slot)-(int64_t)(text_rva+offset+4);
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
    size_t reloc_rva=align_page(imports_rva+imports.n),resource_rva=align_page(reloc_rva+relocs.n),text_raw=1024,data_raw=text_raw+align_file(code.n),imports_raw=data_raw+align_file(data.n),reloc_raw=imports_raw+align_file(imports.n),resource_raw=reloc_raw+align_file(relocs.n);
    bytes(&resources,icon_resource,sizeof(icon_resource));
    for(size_t i=0;i<sizeof(icon_rva_patches)/sizeof(icon_rva_patches[0]);i++){
        size_t p=icon_rva_patches[i];uint32_t offset=0;for(int j=0;j<4;j++)offset|=(uint32_t)resources.v[p+(size_t)j]<<(j*8);
        patch32(resources.v,p,(uint32_t)resource_rva+offset);
    }
    unsigned char header[1024]={0};header[0]='M';header[1]='Z';patch32(header,0x3c,0x80);
    static const char stub[]="AssisScript: programa Windows x64.\r\n";memcpy(header+0x40,stub,sizeof(stub)-1);
    size_t pe=0x80;memcpy(header+pe,"PE\0\0",4);patch16(header,pe+4,0x8664);patch16(header,pe+6,5);
    patch16(header,pe+20,240);patch16(header,pe+22,0x22);size_t op=pe+24;
    patch16(header,op,0x20b);header[op+2]=2;header[op+3]=1;
    patch32(header,op+4,(uint32_t)align_file(code.n));patch32(header,op+8,(uint32_t)(align_file(data.n)+align_file(imports.n)+align_file(relocs.n)+align_file(resources.n)));
    patch32(header,op+16,(uint32_t)(text_rva+entry_offset));patch32(header,op+20,(uint32_t)text_rva);patch64(header,op+24,base);
    patch32(header,op+32,4096);patch32(header,op+36,512);patch16(header,op+40,6);patch16(header,op+44,2);patch16(header,op+46,1);patch16(header,op+48,6);
    patch32(header,op+56,(uint32_t)align_page(resource_rva+resources.n));patch32(header,op+60,sizeof(header));patch16(header,op+68,3);patch16(header,op+70,0x160);
    patch64(header,op+72,UINT64_C(0x100000));patch64(header,op+80,4096);patch64(header,op+88,UINT64_C(0x100000));patch64(header,op+96,4096);patch32(header,op+108,16);
    patch32(header,op+112+8,(uint32_t)imports_rva);patch32(header,op+112+12,(uint32_t)descriptor_size);
    patch32(header,op+112+5*8,(uint32_t)reloc_rva);patch32(header,op+112+5*8+4,(uint32_t)relocs.n);
    patch32(header,op+112+12*8,(uint32_t)(imports_rva+iat));patch32(header,op+112+12*8+4,(uint32_t)iat_size);
    patch32(header,op+112+2*8,(uint32_t)resource_rva);patch32(header,op+112+2*8+4,(uint32_t)resources.n);
    size_t sh=op+240;
    pe_section(header,sh,".text",&code,text_rva,text_raw,0x60000020);
    pe_section(header,sh+40,".rdata",&data,data_rva,data_raw,0x40000040);
    pe_section(header,sh+80,".idata",&imports,imports_rva,imports_raw,0xc0000040);
    pe_section(header,sh+120,".reloc",&relocs,reloc_rva,reloc_raw,0x42000040);
    pe_section(header,sh+160,".rsrc",&resources,resource_rva,resource_raw,0x40000040);
    protect_output(path);FILE *fp=fopen(path,"wb");if(!fp)fatal("não foi possível criar %s: %s",path,strerror(errno));
    bool ok=fwrite(header,1,sizeof(header),fp)==sizeof(header)&&pe_part(fp,&code)&&pe_part(fp,&data)&&pe_part(fp,&imports)&&pe_part(fp,&relocs)&&pe_part(fp,&resources);
    if(fclose(fp))ok=false;if(!ok){unlink(path);fatal("erro ao gravar %s",path);}
    free(imports.v);free(relocs.v);free(resources.v);
}
#endif

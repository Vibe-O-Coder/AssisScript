/* Harness de validação, Linux x86_64. Executa PE gerado usando stubs Win32
 * na ABI Microsoft. Não é Wine nem teste em Windows real. */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/mman.h>
#include <unistd.h>

#define MS __attribute__((ms_abi))
static void bad(const char *m){fprintf(stderr,"PE probe: %s\n",m);exit(125);}
static uint16_t rd16(const unsigned char *p){return (uint16_t)(p[0]|(uint16_t)p[1]<<8);}
static uint32_t rd32(const unsigned char *p){uint32_t n=0;for(int i=0;i<4;i++)n|=(uint32_t)p[i]<<(i*8);return n;}
static uint64_t rd64(const unsigned char *p){uint64_t n=0;for(int i=0;i<8;i++)n|=(uint64_t)p[i]<<(i*8);return n;}
static void put64(unsigned char *p,uint64_t n){for(int i=0;i<8;i++)p[i]=(unsigned char)(n>>(i*8));}
static MS void mock_exit(uint32_t status){exit((int)status);}
static MS void *mock_handle(int32_t id){return (void*)(intptr_t)(id==-12?2:id==-11?1:0);}
static MS int mock_cp(uint32_t cp){return cp==65001;}
static MS int mock_write(void *handle,const void *buffer,uint32_t length,uint32_t *written,void *overlapped){
    if(overlapped)bad("WriteFile assíncrono inesperado");ssize_t n=write((int)(intptr_t)handle,buffer,length);*written=n>0?(uint32_t)n:0;return n>=0;
}
static MS void *mock_alloc(void *address,size_t length,uint32_t flags,uint32_t protection){
    if(address||flags!=0x3000||protection!=4)bad("argumentos de VirtualAlloc");
    void *p=mmap(NULL,length,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);return p==MAP_FAILED?NULL:p;
}
static MS int mock_free(void *address,size_t length,uint32_t flags){
    if(length||flags!=0x8000)bad("argumentos de VirtualFree");return !munmap(address,(size_t)rd64(address));
}
static uintptr_t resolve(const char *name){
    if(!strcmp(name,"ExitProcess"))return (uintptr_t)mock_exit;
    if(!strcmp(name,"GetStdHandle"))return (uintptr_t)mock_handle;
    if(!strcmp(name,"SetConsoleOutputCP"))return (uintptr_t)mock_cp;
    if(!strcmp(name,"WriteFile"))return (uintptr_t)mock_write;
    if(!strcmp(name,"VirtualAlloc"))return (uintptr_t)mock_alloc;
    if(!strcmp(name,"VirtualFree"))return (uintptr_t)mock_free;
    bad("import não suportado pelo harness");return 0;
}
int main(int argc,char **argv){
    if(argc!=2)bad("use pe_probe programa.exe");FILE *fp=fopen(argv[1],"rb");if(!fp)bad("arquivo não encontrado");
    if(fseek(fp,0,SEEK_END))bad("fseek");long length=ftell(fp);rewind(fp);
    if(length<1024||length>64*1024*1024)bad("tamanho do PE");unsigned char *file=malloc((size_t)length);if(!file)bad("memória");
    if(fread(file,1,(size_t)length,fp)!=(size_t)length)bad("leitura");fclose(fp);
    if(memcmp(file,"MZ",2))bad("assinatura DOS");uint32_t pe=rd32(file+0x3c);
    if(pe>(uint32_t)length-264||memcmp(file+pe,"PE\0\0",4)||rd16(file+pe+4)!=0x8664)bad("assinatura PE x64");
    uint16_t count=rd16(file+pe+6),optional=rd16(file+pe+20);unsigned char *op=file+pe+24;
    if(rd16(op)!=0x20b||optional<240)bad("cabeçalho PE32+");
    uint32_t image_size=rd32(op+56),headers=rd32(op+60),entry=rd32(op+16);uint64_t preferred=rd64(op+24);
    if(image_size>128*1024*1024||headers>(uint32_t)length||headers>image_size||entry>=image_size)bad("limites da imagem");
    if(rd32(op+32)!=4096||rd32(op+36)!=512||(rd16(op+70)&0x140)!=0x140)bad("alinhamento ou ASLR/DEP");
    unsigned char *image=mmap((void*)(uintptr_t)(preferred+0x10000000),image_size,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(image==MAP_FAILED)bad("mmap da imagem");memcpy(image,file,headers);
    size_t section=pe+24+(size_t)optional;if(section+(size_t)count*40>(size_t)length)bad("tabela de seções");
    for(int i=0;i<count;i++){
        unsigned char *s=file+section+(size_t)i*40;uint32_t rva=rd32(s+12),raw=rd32(s+20),size=rd32(s+16),flags=rd32(s+36);
        if((uint64_t)rva+size>image_size||(uint64_t)raw+size>(uint64_t)length)bad("limites de seção");
        if((flags&0xa0000000)==0xa0000000)bad("seção gravável e executável");memcpy(image+rva,file+raw,size);
    }
    uint32_t reloc=rd32(op+112+40),reloc_size=rd32(op+112+44);uint64_t delta=(uint64_t)(uintptr_t)image-preferred;
    if((uint64_t)reloc+reloc_size>image_size)bad("limites de relocations");
    for(uint32_t at=0;at<reloc_size;){
        if(reloc_size-at<8)bad("bloco de relocations");uint32_t page=rd32(image+reloc+at),size=rd32(image+reloc+at+4);
        if(size<8||size>reloc_size-at||size%4)bad("tamanho de relocations");
        for(uint32_t p=8;p<size;p+=2){uint16_t item=rd16(image+reloc+at+p);if(!item)continue;if(item>>12!=10)bad("tipo de relocation");uint64_t site=(uint64_t)page+(item&4095);if(site+8>image_size)bad("site de relocation");put64(image+site,rd64(image+site)+delta);}
        at+=size;
    }
    uint32_t imports=rd32(op+120);if((uint64_t)imports+40>image_size)bad("tabela de imports");
    for(uint32_t p=imports;rd32(image+p)||rd32(image+p+12)||rd32(image+p+16);p+=20){
        if((uint64_t)p+40>image_size)bad("descritor de import");uint32_t dll=rd32(image+p+12),lookup=rd32(image+p),iat=rd32(image+p+16);
        if(dll>=image_size||!memchr(image+dll,0,image_size-dll)||strcasecmp((char*)image+dll,"KERNEL32.dll"))bad("DLL inesperada");
        for(uint32_t i=0;;i++){
            if((uint64_t)lookup+(uint64_t)i*8+8>image_size||(uint64_t)iat+(uint64_t)i*8+8>image_size)bad("limites de thunk");
            uint64_t name=rd64(image+lookup+(size_t)i*8);if(!name)break;if(name+2>=image_size||!memchr(image+name+2,0,image_size-(size_t)name-2))bad("nome de import");
            put64(image+iat+(size_t)i*8,(uint64_t)resolve((char*)image+name+2));
        }
    }
    if(mprotect(image,4096,PROT_READ))bad("proteção de cabeçalho");
    for(int i=0;i<count;i++){
        unsigned char *s=file+section+(size_t)i*40;uint32_t rva=rd32(s+12),size=rd32(s+8),flags=rd32(s+36);int protection=0;
        if(flags&0x40000000)protection|=PROT_READ;if(flags&0x80000000)protection|=PROT_WRITE;if(flags&0x20000000)protection|=PROT_EXEC;
        if(mprotect(image+rva,(size+4095u)&~4095u,protection))bad("proteção de seção");
    }
    free(file);typedef void (MS *Entry)(void);Entry start=(Entry)(void*)(image+entry);start();bad("a entrada retornou em vez de encerrar o processo");
}

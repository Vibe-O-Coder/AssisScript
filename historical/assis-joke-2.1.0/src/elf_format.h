/* Estruturas ELF64 necessárias ao emissor. Sem dependência de headers Linux. */
#ifndef ASSIS_ELF_FORMAT_H
#define ASSIS_ELF_FORMAT_H
#define ELFMAG "\177ELF"
#define SELFMAG 4
#define EI_CLASS 4
#define EI_DATA 5
#define EI_VERSION 6
#define ELFCLASS64 2
#define ELFDATA2LSB 1
#define EV_CURRENT 1
#define ET_EXEC 2
#define EM_X86_64 62
#define PT_LOAD 1
#define PT_GNU_STACK 0x6474e551
#define PF_X 1
#define PF_W 2
#define PF_R 4
typedef struct {
    unsigned char e_ident[16];
    uint16_t e_type,e_machine;
    uint32_t e_version;
    uint64_t e_entry,e_phoff,e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize,e_phentsize,e_phnum,e_shentsize,e_shnum,e_shstrndx;
} Elf64_Ehdr;
typedef struct {
    uint32_t p_type,p_flags;
    uint64_t p_offset,p_vaddr,p_paddr,p_filesz,p_memsz,p_align;
} Elf64_Phdr;
_Static_assert(sizeof(Elf64_Ehdr)==64,"Cabeçalho ELF64 inválido");
_Static_assert(sizeof(Elf64_Phdr)==56,"Program header ELF64 inválido");
#endif

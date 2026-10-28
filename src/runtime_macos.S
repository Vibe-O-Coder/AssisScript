/* macOS x86_64 adapter. Uses the public libSystem API, not private syscalls.
 * Preserve the Linux runtime's syscall register contract around SysV calls.
 * Import displacements are bound by the Mach-O writer into writable __DATA.
 */
.intel_syntax noprefix
.set AS_MACOS, 1
.macro syscall
    call .Lmacos_system
.endm
.macro macapi name
    .byte 0xff, 0x15
    .global asrt_import_\name\()_\@
asrt_import_\name\()_\@:
    .long 0
.endm
.include "runtime.S"
.text
.global asrt_exit
asrt_exit:
    mov eax, 60
    syscall
    ud2
.Lmacos_system:
    push rbp
    mov rbp, rsp
    push rdi
    push rsi
    push rdx
    push r8
    push r9
    push r10
    and rsp, -16
    cmp eax, 0
    je .Lmac_read
    cmp eax, 1
    je .Lmac_write
    cmp eax, 3
    je .Lmac_close
    cmp eax, 9
    je .Lmac_map
    cmp eax, 11
    je .Lmac_unmap
    cmp eax, 35
    je .Lmac_sleep
    cmp eax, 60
    je .Lmac_exit
    cmp eax, 74
    je .Lmac_sync
    cmp eax, 82
    je .Lmac_rename
    cmp eax, 87
    je .Lmac_unlink
    cmp eax, 228
    je .Lmac_clock
    cmp eax, 257
    je .Lmac_open
    mov rax, -78
    jmp .Lmac_return
.Lmac_read:
    macapi read
    jmp .Lmac_result
.Lmac_write:
    macapi write
    jmp .Lmac_result
.Lmac_close:
    macapi close
    cdqe
    jmp .Lmac_result
.Lmac_map:
    mov ecx, 0x1002
    macapi mmap
    jmp .Lmac_result
.Lmac_unmap:
    macapi munmap
    jmp .Lmac_result
.Lmac_sleep:
    macapi nanosleep
    cdqe
    jmp .Lmac_result
.Lmac_exit:
    macapi _exit
    ud2
.Lmac_sync:
    macapi fsync
    cdqe
    jmp .Lmac_result
.Lmac_rename:
    macapi rename
    cdqe
    jmp .Lmac_result
.Lmac_unlink:
    macapi unlink
    cdqe
    jmp .Lmac_result
.Lmac_clock:
    test edi, edi
    jz .Lmac_clock_ready
    mov edi, 6
.Lmac_clock_ready:
    macapi clock_gettime
    cdqe
    jmp .Lmac_result
.Lmac_open:
    mov rdi, rsi
    mov esi, 0x1000000
    test edx, 64
    jz .Lmac_open_no_create
    or esi, 0x200
.Lmac_open_no_create:
    test edx, 128
    jz .Lmac_open_no_excl
    or esi, 0x800
.Lmac_open_no_excl:
    test edx, 512
    jz .Lmac_open_no_truncate
    or esi, 0x400
.Lmac_open_no_truncate:
    test edx, 1024
    jz .Lmac_open_no_append
    or esi, 8
.Lmac_open_no_append:
    and edx, 3
    or esi, edx
    mov rdx, r10
    macapi open
    cdqe
.Lmac_result:
    cmp rax, -1
    jne .Lmac_return
    macapi __error
    mov eax, dword ptr [rax]
    neg rax
.Lmac_return:
    lea rsp, [rbp-48]
    pop r10
    pop r9
    pop r8
    pop rdx
    pop rsi
    pop rdi
    pop rbp
    ret

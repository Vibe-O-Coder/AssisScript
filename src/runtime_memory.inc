/* R15: process-local state, allocated once. No writable executable segment.
 * Ten size classes (64..32768 bytes), 64 KiB slabs, 32-byte block headers.
 * Large requests use the OS directly. The runtime is single-threaded. */
.global asrt_init_memory
asrt_init_memory:
.Lmemory_init:
    mov edi, 4096
    call .Los_map
    test rax, rax
    jz .Linit_failed
    mov r15, rax
    mov qword ptr [r15+96], rsp
    mov rax, rsp
.ifdef AS_WINDOWS
    sub rax, 524288
.else
    sub rax, 4194304
.endif
    mov qword ptr [r15+104], rax
    ret
.Linit_failed:
    mov edi, 5
    xor esi, esi
    jmp .Lerror

/* OS adapter: RDI=bytes, RAX=zero-filled mapping or zero on failure. */
.Los_map:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rdx, rdi
    xor ecx, ecx
    mov r8d, 0x3000
    mov r9d, 4
    api VirtualAlloc
    mov rsp, rbp
    pop rbp
.else
    mov rsi, rdi
    xor edi, edi
    mov edx, 3
    mov r10d, 34
    mov r8, -1
    xor r9d, r9d
    mov eax, 9
    syscall
    cmp rax, -4095
    jb .Lmap_ok
    xor eax, eax
.Lmap_ok:
.endif
    ret

.global asrt_alloc
asrt_alloc:
.Lalloc:
    push r12
    push r13
    push r14
    mov r12, rsi
    mov r13, rdi
    test rdi, rdi
    js .Lbad_alloc
    mov rax, 0x7fffffffffffffdf
    cmp rdi, rax
    ja .Lbad_alloc
    lea rcx, [rdi+32]
    mov edx, 64
    xor r14d, r14d
.Lclass:
    cmp rcx, rdx
    jbe .Lsmall_alloc
    inc r14d
    shl rdx, 1
    cmp r14d, 10
    jb .Lclass
    mov rdi, rcx
    call .Los_map
    test rax, rax
    jz .Lno_memory
    lea rcx, [r13+32]
    mov qword ptr [rax], rcx
    mov qword ptr [rax+8], 10
    jmp .Lallocated
.Lsmall_alloc:
    mov rax, qword ptr [r15+r14*8]
    test rax, rax
    jnz .Ltake_free
    mov edi, 65536
    call .Los_map
    test rax, rax
    jz .Lno_memory
    mov qword ptr [r15+r14*8], rax
    mov ecx, r14d
    mov edx, 64
    shl rdx, cl
    lea r8, [rax+65536]
.Lcarve:
    mov qword ptr [rax], rdx
    mov qword ptr [rax+8], r14
    lea rcx, [rax+rdx]
    mov qword ptr [rax+16], rcx
    mov qword ptr [rax+24], 0x46524545
    cmp rcx, r8
    je .Lcarve_last
    mov rax, rcx
    jmp .Lcarve
.Lcarve_last:
    mov qword ptr [rax+16], 0
    mov rax, qword ptr [r15+r14*8]
.Ltake_free:
    mov rcx, qword ptr [rax+16]
    mov qword ptr [r15+r14*8], rcx
.Lallocated:
    mov qword ptr [rax+16], r13
    mov qword ptr [rax+24], 0x41534953
    inc qword ptr [r15+80]
    lea r8, [rax+32]
    /* Direct OS mappings are already zero filled. Avoid faulting in every
     * untouched page of a large allocation. Pool reuse still clears bytes,
     * including in debug mode after the free poison. */
    cmp r14d, 10
    je .Lallocation_ready
    mov rdi, r8
    mov rcx, r13
    xor eax, eax
    rep stosb
.Lallocation_ready:
    mov rax, r8
    pop r14
    pop r13
    pop r12
    ret
.Lbad_alloc:
    mov edi, 4
    mov rsi, r12
    jmp .Lerror
.Lno_memory:
    mov edi, 5
    mov rsi, r12
    jmp .Lerror

.global asrt_free
asrt_free:
.Lfree:
    test rdi, rdi
    jz .Lfree_done
    lea r8, [rdi-32]
    cmp qword ptr [r8+24], 0x41534953
    jne .Linvalid_free
    mov qword ptr [r8+24], 0x46524545
    dec qword ptr [r15+80]
    cmp qword ptr [r15+88], 0
    je .Lfree_link
    mov rcx, qword ptr [r8+16]
    mov al, 0xdd
    rep stosb
.Lfree_link:
    mov rdx, qword ptr [r8+8]
    cmp rdx, 10
    jae .Lfree_large
    mov rcx, qword ptr [r15+rdx*8]
    mov qword ptr [r8+16], rcx
    mov qword ptr [r15+rdx*8], r8
.Lfree_done:
    ret
.Lfree_large:
    /* Debug retains large freed blocks so a second free has a diagnostic. */
    cmp qword ptr [r15+88], 0
    jne .Lfree_done
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rcx, r8
    xor edx, edx
    mov r8d, 0x8000
    api VirtualFree
    mov rsp, rbp
    pop rbp
.else
    mov rdi, r8
    mov rsi, qword ptr [r8]
    mov eax, 11
    syscall
.endif
    ret
.Linvalid_free:
    mov edi, 12
    xor esi, esi
    jmp .Lerror

.global asrt_finish
asrt_finish:
.ifdef AS_WINDOWS
    cmp qword ptr [r15+120], 0
    je .Lfinish_args_done
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rcx, qword ptr [r15+120]
    api LocalFree
    mov qword ptr [r15+120], 0
    mov rsp, rbp
    pop rbp
.Lfinish_args_done:
.endif
    cmp qword ptr [r15+88], 0
    je .Lfinish_done
    mov rdi, qword ptr [r15+80]
    test rdi, rdi
    jz .Lfinish_done
    mov esi, 2
    call .Lprint_int
    mov edi, 13
    xor esi, esi
    jmp .Lerror
.Lfinish_done:
    ret

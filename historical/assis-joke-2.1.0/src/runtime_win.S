/* Runtime Windows x64. API interna igual à do runtime Linux.
 * Chamadas Win32 usam shadow space e alinhamento de 16 bytes.
 * Os campos asrt_import_* são corrigidos pelo emissor PE para a IAT.
 */
.intel_syntax noprefix
.section .text
.macro api name
    .byte 0xff, 0x15
    .global asrt_import_\name\()_\@
asrt_import_\name\()_\@:
    .long 0
.endm

.global asrt_init
asrt_init:
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov ecx, 65001
    api SetConsoleOutputCP
    mov rsp, rbp
    pop rbp
    ret

.global asrt_exit
asrt_exit:
.Lexit:
    mov rcx, rdi
    and rsp, -16
    sub rsp, 32
    api ExitProcess
    ud2

.global asrt_write
asrt_write:
.Lwrite:
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    and rsp, -16
    sub rsp, 64
    mov r12, rsi
    mov r13, rdx
    mov ecx, -11
    cmp edi, 2
    jne .Lget_handle
    mov ecx, -12
.Lget_handle:
    api GetStdHandle
    mov rbx, rax
.Lwrite_loop:
    test r13, r13
    jz .Lwrite_done
    mov rcx, rbx
    mov rdx, r12
    mov r8, r13
    cmp r8, 0x7fffffff
    jbe .Lwrite_size
    mov r8d, 0x7fffffff
.Lwrite_size:
    lea r9, [rsp+48]
    mov qword ptr [rsp+32], 0
    api WriteFile
    test eax, eax
    jz .Lwrite_done
    mov eax, dword ptr [rsp+48]
    test eax, eax
    jz .Lwrite_done
    add r12, rax
    sub r13, rax
    jmp .Lwrite_loop
.Lwrite_done:
    lea rsp, [rbp-24]
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret
.global asrt_print_str
asrt_print_str:
.Lprint_str:
    test rdi, rdi
    jz .Lprint_str_done
    mov r8, rdi
    xor edx, edx
.Lprint_str_len:
    cmp byte ptr [r8+rdx], 0
    je .Lprint_str_out
    inc rdx
    jmp .Lprint_str_len
.Lprint_str_out:
    mov rdi, rsi
    mov rsi, r8
    jmp .Lwrite
.Lprint_str_done:
    ret

.global asrt_print_int
asrt_print_int:
.Lprint_int:
    sub rsp, 64
    mov r9, rsi
    mov rax, rdi
    xor r10d, r10d
    test rax, rax
    jns .Lint_magnitude
    mov r10d, 1
    neg rax
.Lint_magnitude:
    lea r8, [rsp+63]
    mov ecx, 10
.Lint_digit:
    xor edx, edx
    div rcx
    add dl, 48
    mov byte ptr [r8], dl
    dec r8
    test rax, rax
    jnz .Lint_digit
    test r10d, r10d
    jz .Lint_out
    mov byte ptr [r8], 45
    dec r8
.Lint_out:
    inc r8
    lea rdx, [rsp+64]
    sub rdx, r8
    mov rdi, r9
    mov rsi, r8
    call .Lwrite
    add rsp, 64
    ret

.global asrt_print_char
asrt_print_char:
    sub rsp, 8
    mov byte ptr [rsp], dil
    mov rdi, rsi
    mov rsi, rsp
    mov edx, 1
    call .Lwrite
    add rsp, 8
    ret

.global asrt_print_bool
asrt_print_bool:
    test rdi, rdi
    lea rdi, [rip+.Lfalse]
    jz .Lbool_out
    lea rdi, [rip+.Ltrue]
.Lbool_out:
    jmp .Lprint_str
.Ltrue: .asciz "aSsIs"
.Lfalse: .asciz "fOdAsE"

.global asrt_print_ptr
asrt_print_ptr:
    sub rsp, 32
    mov r9, rsi
    mov rax, rdi
    lea r10, [rip+.Lhex]
    mov byte ptr [rsp], 48
    mov byte ptr [rsp+1], 120
    mov r8d, 17
.Lptr_digit:
    mov rdx, rax
    and edx, 15
    movzx edx, byte ptr [r10+rdx]
    mov byte ptr [rsp+r8], dl
    shr rax, 4
    dec r8
    cmp r8, 1
    jne .Lptr_digit
    mov rdi, r9
    mov rsi, rsp
    mov edx, 18
    call .Lwrite
    add rsp, 32
    ret
.Lhex: .ascii "0123456789abcdef"


.global asrt_alloc
asrt_alloc:
    push rbp
    mov rbp, rsp
    push r12
    and rsp, -16
    sub rsp, 32
    mov r12, rsi
    test rdi, rdi
    js .Lbad_alloc
    mov rax, 0x7fffffffffffffef
    cmp rdi, rax
    ja .Lbad_alloc
    test rdi, rdi
    jnz .Lalloc_size
    inc rdi
.Lalloc_size:
    xor ecx, ecx
    lea rdx, [rdi+16]
    mov r8d, 0x3000
    mov r9d, 4
    api VirtualAlloc
    test rax, rax
    jz .Lno_memory
    lea rdx, [rdi+16]
    mov qword ptr [rax], rdx
    mov qword ptr [rax+8], 0
    add rax, 16
    mov r12, qword ptr [rbp-8]
    mov rsp, rbp
    pop rbp
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
    test rdi, rdi
    jz .Lfree_done
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    lea rcx, [rdi-16]
    xor edx, edx
    mov r8d, 0x8000
    api VirtualFree
    mov rsp, rbp
    pop rbp
.Lfree_done:
    ret
.global asrt_len
asrt_len:
    xor eax, eax
    test rdi, rdi
    jz .Llen_done
.Llen_loop:
    cmp byte ptr [rdi+rax], 0
    je .Llen_done
    inc rax
    jmp .Llen_loop
.Llen_done:
    ret

.global asrt_streq
asrt_streq:
    cmp rdi, rsi
    je .Lstreq_yes
    test rdi, rdi
    jz .Lstreq_no
    test rsi, rsi
    jz .Lstreq_no
.Lstreq_loop:
    movzx eax, byte ptr [rdi]
    cmp al, byte ptr [rsi]
    jne .Lstreq_no
    test al, al
    jz .Lstreq_yes
    inc rdi
    inc rsi
    jmp .Lstreq_loop
.Lstreq_yes:
    mov eax, 1
    ret
.Lstreq_no:
    xor eax, eax
    ret

.global asrt_strbyte
asrt_strbyte:
    mov r10, rdx
    test rdi, rdi
    jz .Lbad_index
    test rsi, rsi
    js .Lbad_index
    xor eax, eax
.Lstrbyte_loop:
    movzx ecx, byte ptr [rdi+rax]
    test ecx, ecx
    jz .Lbad_index
    cmp rax, rsi
    je .Lstrbyte_done
    inc rax
    jmp .Lstrbyte_loop
.Lstrbyte_done:
    mov eax, ecx
    ret
.Lbad_index:
    mov edi, 6
    mov rsi, r10
    jmp .Lerror

.global asrt_error
asrt_error:
.Lerror:
    mov r12, rdi
    mov r13, rsi
    lea rdi, [rip+.Lerror_head]
    mov esi, 2
    call .Lprint_str
    mov rdi, r13
    mov esi, 2
    call .Lprint_int
    lea rdi, [rip+.Lerror_colon]
    mov esi, 2
    call .Lprint_str
    lea rdi, [rip+.Lerror_null]
    cmp r12, 1
    je .Lerror_message
    lea rdi, [rip+.Lerror_div]
    cmp r12, 2
    je .Lerror_message
    lea rdi, [rip+.Lerror_shift]
    cmp r12, 3
    je .Lerror_message
    lea rdi, [rip+.Lerror_alloc]
    cmp r12, 4
    je .Lerror_message
    lea rdi, [rip+.Lerror_memory]
    cmp r12, 5
    je .Lerror_message
    lea rdi, [rip+.Lerror_index]
    cmp r12, 6
    je .Lerror_message
    lea rdi, [rip+.Lerror_mod]
    cmp r12, 8
    je .Lerror_message
    lea rdi, [rip+.Lerror_return]
.Lerror_message:
    mov esi, 2
    call .Lprint_str
    mov edi, 70
    jmp .Lexit
.Lerror_head: .asciz "FODASE R001, linha "
.Lerror_colon: .asciz ": "
.Lerror_null: .asciz "acesso a ponteiro/objeto nulo\n"
.Lerror_div: .asciz "divisão por zero\n"
.Lerror_mod: .asciz "resto por zero\n"
.Lerror_shift: .asciz "deslocamento deve estar entre 0 e 63\n"
.Lerror_alloc: .asciz "tamanho de alocação inválido\n"
.Lerror_memory: .asciz "memória insuficiente\n"
.Lerror_index: .asciz "índice de texto fora do limite\n"
.Lerror_return: .asciz "função terminou sem retorno\n"


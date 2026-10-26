/* Managed synchronous file resources and process arguments.
 * R15+112: last native IO error, +120: argv, +128: argc.
 * File payload is one OS handle; -1 denotes an explicitly closed resource.
 * Native errors are recoverable. Memory-contract violations remain fatal. */
.global asrt_args_init
asrt_args_init:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 48
    api GetCommandLineW
    mov rcx, rax
    lea rdx, [rsp+40]
    api CommandLineToArgvW
    test rax, rax
    jz .Largs_init_failed
    mov qword ptr [r15+120], rax
    mov eax, dword ptr [rsp+40]
    mov qword ptr [r15+128], rax
    jmp .Largs_init_done
.Largs_init_failed:
    api GetLastError
    mov qword ptr [r15+112], rax
.Largs_init_done:
    mov rsp, rbp
    pop rbp
.else
    mov rax, qword ptr [rdi]
    mov qword ptr [r15+128], rax
    add rdi, 8
    mov qword ptr [r15+120], rdi
.endif
    ret

.global asrt_argc
asrt_argc:
    mov rax, qword ptr [r15+128]
    ret
.global asrt_io_error
asrt_io_error:
    mov rax, qword ptr [r15+112]
    ret

.global asrt_arg_len
asrt_arg_len:
.Larg_len:
    cmp rdi, qword ptr [r15+128]
    jae .Largument_invalid
    mov rax, qword ptr [r15+120]
    mov rax, qword ptr [rax+rdi*8]
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 64
    mov r8, rax
    mov ecx, 65001
    mov edx, 0x80
    mov r9d, -1
    mov qword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    api WideCharToMultiByte
    test eax, eax
    jz .Larg_len_error
    dec rax
    mov qword ptr [r15+112], 0
    jmp .Larg_len_done
.Larg_len_error:
    api GetLastError
    mov qword ptr [r15+112], rax
    mov rax, -1
.Larg_len_done:
    mov rsp, rbp
    pop rbp
.else
    mov rcx, rax
    xor eax, eax
.Larg_len_loop:
    cmp byte ptr [rcx+rax], 0
    je .Larg_len_return
    inc rax
    jmp .Larg_len_loop
.Larg_len_return:
    mov qword ptr [r15+112], 0
.endif
    ret
.Largument_invalid:
.ifdef AS_WINDOWS
    mov qword ptr [r15+112], 87
.else
    mov qword ptr [r15+112], 22
.endif
    mov rax, -1
    ret

.global asrt_arg_copy
asrt_arg_copy:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    and rsp, -16
    sub rsp, 80
    mov r12, rdi
    mov r13, rsi
    mov r14, rdx
    call .Larg_len
    test rax, rax
    js .Larg_copy_done
    cmp r14, rax
    jbe .Larg_copy_small
    test r13, r13
    jz .Larg_copy_small
    mov qword ptr [rsp+64], rax
    mov rax, qword ptr [r15+120]
    mov rsi, qword ptr [rax+r12*8]
.ifdef AS_WINDOWS
    mov ecx, 65001
    mov edx, 0x80
    mov r8, rsi
    mov r9d, -1
    mov qword ptr [rsp+32], r13
    mov rax, qword ptr [rsp+64]
    inc rax
    mov qword ptr [rsp+40], rax
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    api WideCharToMultiByte
    test eax, eax
    jz .Larg_copy_error
.else
    mov rdi, r13
    mov rcx, qword ptr [rsp+64]
    inc rcx
    cld
    rep movsb
.endif
    mov rax, qword ptr [rsp+64]
    mov qword ptr [r15+112], 0
    jmp .Larg_copy_done
.Larg_copy_small:
.ifdef AS_WINDOWS
    mov qword ptr [r15+112], 122
.else
    mov qword ptr [r15+112], 34
.endif
    mov rax, -1
    jmp .Larg_copy_done
.ifdef AS_WINDOWS
.Larg_copy_error:
    api GetLastError
    mov qword ptr [r15+112], rax
    mov rax, -1
.endif
.Larg_copy_done:
    lea rsp, [rbp-24]
    pop r14
    pop r13
    pop r12
    pop rbp
    ret

.global asrt_file_open
asrt_file_open:
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    push r14
    and rsp, -16
    sub rsp, 80
    mov r12, rdi
    mov r13, rsi
    cmp rsi, 3
    ja .Lfile_open_invalid
    test rdi, rdi
    jz .Lfile_open_invalid
.ifdef AS_WINDOWS
    mov ecx, 65001
    mov edx, 8
    mov r8, r12
    mov r9d, -1
    mov qword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    api MultiByteToWideChar
    test eax, eax
    jz .Lfile_open_win_error
    mov ebx, eax
    lea rdi, [rax+rax]
    xor esi, esi
    call .Lalloc
    mov r14, rax
    mov ecx, 65001
    mov edx, 8
    mov r8, r12
    mov r9d, -1
    mov qword ptr [rsp+32], r14
    mov qword ptr [rsp+40], rbx
    api MultiByteToWideChar
    test eax, eax
    jz .Lfile_open_convert_error
    mov rcx, r14
    mov edx, 0x80000000
    mov r8d, 3
    xor r9d, r9d
    mov qword ptr [rsp+32], 3
    test r13, r13
    jz .Lfile_open_win_flags
    mov edx, 0x40000000
    mov qword ptr [rsp+32], 2
    cmp r13, 1
    je .Lfile_open_win_flags
    cmp r13, 3
    jne .Lfile_open_win_append
    mov qword ptr [rsp+32], 1
    jmp .Lfile_open_win_flags
.Lfile_open_win_append:
    mov edx, 4
    mov qword ptr [rsp+32], 4
.Lfile_open_win_flags:
    mov qword ptr [rsp+40], 0x80
    mov qword ptr [rsp+48], 0
    api CreateFileW
    mov r12, rax
    cmp rax, -1
    jne .Lfile_open_free_path
    api GetLastError
    mov ebx, eax
.Lfile_open_free_path:
    mov rdi, r14
    call .Lfree
    cmp r12, -1
    je .Lfile_open_saved_error
    jmp .Lfile_open_allocate
.Lfile_open_convert_error:
    api GetLastError
    mov ebx, eax
    mov rdi, r14
    call .Lfree
    jmp .Lfile_open_saved_error
.Lfile_open_win_error:
    api GetLastError
    mov ebx, eax
    jmp .Lfile_open_saved_error
.else
    mov rsi, r12
    mov edi, -100
    mov edx, 0x80000
    test r13, r13
    jz .Lfile_open_linux_flags
    or edx, 577
    cmp r13, 1
    je .Lfile_open_linux_flags
    cmp r13, 3
    jne .Lfile_open_linux_append
    mov edx, 0x80000+193
    jmp .Lfile_open_linux_flags
.Lfile_open_linux_append:
    mov edx, 0x80000+1089
.Lfile_open_linux_flags:
    mov r10d, 438
.Lfile_open_retry:
    mov eax, 257
    syscall
    cmp rax, -4
    je .Lfile_open_retry
    test rax, rax
    js .Lfile_open_linux_error
    mov r12, rax
    jmp .Lfile_open_allocate
.Lfile_open_linux_error:
    neg rax
    mov rbx, rax
    jmp .Lfile_open_saved_error
.endif
.Lfile_open_allocate:
    mov edi, 8
    xor esi, esi
    call .Lalloc
    mov qword ptr [rax], r12
    mov qword ptr [r15+112], 0
    jmp .Lfile_open_done
.Lfile_open_invalid:
.ifdef AS_WINDOWS
    mov ebx, 87
.else
    mov ebx, 22
.endif
.Lfile_open_saved_error:
    mov qword ptr [r15+112], rbx
    xor eax, eax
.Lfile_open_done:
    lea rsp, [rbp-32]
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret

.global asrt_file_close
asrt_file_close:
.Lfile_close:
    test rdi, rdi
    jz .Lfile_close_empty
    mov rax, qword ptr [rdi]
    cmp rax, -1
    je .Lfile_close_empty
    mov qword ptr [rdi], -1
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rcx, rax
    api CloseHandle
    test eax, eax
    jnz .Lfile_close_win_ok
    api GetLastError
    mov qword ptr [r15+112], rax
    neg rax
    jmp .Lfile_close_win_done
.Lfile_close_win_ok:
    xor eax, eax
    mov qword ptr [r15+112], rax
.Lfile_close_win_done:
    mov rsp, rbp
    pop rbp
.else
    mov rdi, rax
    mov eax, 3
    syscall
    mov rcx, rax
    neg rcx
    mov qword ptr [r15+112], rcx
.endif
    ret
.Lfile_close_empty:
    xor eax, eax
    mov qword ptr [r15+112], rax
    ret

.global asrt_file_drop
asrt_file_drop:
    push r12
    mov r12, qword ptr [r15+112]
    push rdi
    call .Lfile_close
    pop rdi
    call .Lfree
    mov qword ptr [r15+112], r12
    pop r12
    ret

.global asrt_file_read
asrt_file_read:
    xor r8d, r8d
    jmp .Lfile_transfer
.global asrt_file_write
asrt_file_write:
.Lfile_write:
    mov r8d, 1
.Lfile_transfer:
    test rdi, rdi
    jz .Lfile_bad_handle
    cmp qword ptr [rdi], -1
    je .Lfile_bad_handle
    test rdx, rdx
    js .Lfile_bad_argument
    jz .Lfile_empty_transfer
    test rsi, rsi
    jz .Lfile_bad_argument
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    push r14
    and rsp, -16
    sub rsp, 64
    mov ebx, r8d
    mov r12, qword ptr [rdi]
    mov r13, rsi
    mov r14, rdx
    cmp r14, 0x7fffffff
    jbe .Lfile_transfer_size
    mov r14d, 0x7fffffff
.Lfile_transfer_size:
.ifdef AS_WINDOWS
    mov rcx, r12
    mov rdx, r13
    mov r8, r14
    lea r9, [rsp+48]
    mov qword ptr [rsp+32], 0
    test ebx, ebx
    jnz .Lfile_win_write
    api ReadFile
    jmp .Lfile_win_result
.Lfile_win_write:
    api WriteFile
.Lfile_win_result:
    test eax, eax
    jz .Lfile_transfer_error
    mov eax, dword ptr [rsp+48]
    jmp .Lfile_transfer_ok
.Lfile_transfer_error:
    api GetLastError
    test ebx, ebx
    jnz .Lfile_transfer_native_error
    cmp eax, 38
    je .Lfile_transfer_eof
    cmp eax, 109
    je .Lfile_transfer_eof
.Lfile_transfer_native_error:
    mov qword ptr [r15+112], rax
    neg rax
    jmp .Lfile_transfer_done
.Lfile_transfer_eof:
    xor eax, eax
.else
    mov rdi, r12
    mov rsi, r13
    mov rdx, r14
.Lfile_transfer_retry:
    mov eax, ebx
    syscall
    cmp rax, -4
    je .Lfile_transfer_retry
    test rax, rax
    jns .Lfile_transfer_ok
    mov rcx, rax
    neg rcx
    mov qword ptr [r15+112], rcx
    jmp .Lfile_transfer_done
.endif
.Lfile_transfer_ok:
    mov qword ptr [r15+112], 0
.Lfile_transfer_done:
    lea rsp, [rbp-32]
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret
.Lfile_bad_handle:
.ifdef AS_WINDOWS
    mov qword ptr [r15+112], 6
    mov rax, -6
.else
    mov qword ptr [r15+112], 9
    mov rax, -9
.endif
    ret
.Lfile_bad_argument:
.ifdef AS_WINDOWS
    mov qword ptr [r15+112], 87
    mov rax, -87
.else
    mov qword ptr [r15+112], 22
    mov rax, -22
.endif
    ret
.Lfile_empty_transfer:
    xor eax, eax
    mov qword ptr [r15+112], rax
    ret

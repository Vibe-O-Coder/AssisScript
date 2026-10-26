/* Synchronous time and atomic namespace operations, all failures recoverable. */
.global asrt_stdout_write
asrt_stdout_write:
    cmp rdi, 1
    je .Lstdout_channel_ok
    cmp rdi, 2
    jne .Largument_invalid
.Lstdout_channel_ok:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    and rsp, -16
    sub rsp, 48
    mov r12, rsi
    mov r13, rdx
.ifdef AS_WINDOWS
    mov ecx, -11
    cmp rdi, 2
    jne .Lstdout_get_handle
    mov ecx, -12
.Lstdout_get_handle:
    api GetStdHandle
    mov qword ptr [rsp+32], rax
.else
    mov qword ptr [rsp+32], rdi
.endif
    lea rdi, [rsp+32]
    mov rsi, r12
    mov rdx, r13
    call .Lfile_write
    lea rsp, [rbp-16]
    pop r13
    pop r12
    pop rbp
    ret

.global asrt_sleep
asrt_sleep:
    cmp rdi, 0x7fffffff
    ja .Largument_invalid
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rcx, rdi
    api Sleep
    mov rsp, rbp
    pop rbp
    xor eax, eax
.else
    sub rsp, 32
    mov rax, rdi
    xor edx, edx
    mov ecx, 1000
    div rcx
    mov qword ptr [rsp], rax
    imul rdx, rdx, 1000000
    mov qword ptr [rsp+8], rdx
.Lsleep_retry:
    mov rdi, rsp
    lea rsi, [rsp+16]
    mov eax, 35
    syscall
    cmp rax, -4
    jne .Lsleep_done
    mov rax, qword ptr [rsp+16]
    mov qword ptr [rsp], rax
    mov rax, qword ptr [rsp+24]
    mov qword ptr [rsp+8], rax
    jmp .Lsleep_retry
.Lsleep_done:
    add rsp, 32
.endif
    jmp .Lsystem_result

.global asrt_civil
asrt_civil:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 48
    lea rcx, [rsp+32]
    api GetSystemTimeAsFileTime
    mov rax, qword ptr [rsp+32]
    mov rcx, 116444736000000000
    sub rax, rcx
    xor edx, edx
    mov ecx, 10000
    div rcx
    mov rsp, rbp
    pop rbp
.else
    sub rsp, 16
    xor edi, edi
    mov rsi, rsp
    mov eax, 228
    syscall
    test rax, rax
    js .Lcivil_error
    mov rax, qword ptr [rsp+8]
    xor edx, edx
    mov ecx, 1000000
    div rcx
    imul rcx, qword ptr [rsp], 1000
    add rax, rcx
    add rsp, 16
    mov qword ptr [r15+112], 0
    ret
.Lcivil_error:
    add rsp, 16
    jmp .Lsystem_result
.endif
    mov qword ptr [r15+112], 0
    ret

.global asrt_file_sync
asrt_file_sync:
    test rdi, rdi
    jz .Lsync_invalid
    mov rdi, qword ptr [rdi]
    cmp rdi, -1
    je .Lsync_invalid
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    mov rcx, rdi
    api FlushFileBuffers
    test eax, eax
    jnz .Lsync_success
    api GetLastError
    neg rax
    jmp .Lsync_return
.Lsync_success:
    xor eax, eax
.Lsync_return:
    mov rsp, rbp
    pop rbp
.else
    mov eax, 74
    syscall
.endif
    jmp .Lsystem_result
.Lsync_invalid:
    call .Lfile_bad_handle
    mov rax, -1
    ret

/* Private UTF-8 -> UTF-16 adapter for filesystem names. */
.ifdef AS_WINDOWS
.Lsystem_wide_path:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    and rsp, -16
    sub rsp, 48
    mov r12, rdi
    test r12, r12
    jz .Lwide_invalid
    mov ecx, 65001
    mov edx, 8
    mov r8, r12
    mov r9d, -1
    mov qword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    api MultiByteToWideChar
    test eax, eax
    jz .Lwide_error
    mov r13, rax
    lea rdi, [rax+rax]
    xor esi, esi
    call .Lalloc
    mov qword ptr [rsp+40], r13
    mov qword ptr [rsp+32], rax
    mov r13, rax
    mov ecx, 65001
    mov edx, 8
    mov r8, r12
    mov r9d, -1
    api MultiByteToWideChar
    test eax, eax
    jnz .Lwide_success
    api GetLastError
    mov r12, rax
    mov rdi, r13
    call .Lfree
    mov qword ptr [r15+112], r12
    xor eax, eax
    jmp .Lwide_done
.Lwide_success:
    mov rax, r13
    jmp .Lwide_done
.Lwide_invalid:
    mov eax, 87
    jmp .Lwide_save_error
.Lwide_error:
    api GetLastError
.Lwide_save_error:
    mov qword ptr [r15+112], rax
    xor eax, eax
.Lwide_done:
    lea rsp, [rbp-16]
    pop r13
    pop r12
    pop rbp
    ret
.endif

.global asrt_file_replace
asrt_file_replace:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    and rsp, -16
    sub rsp, 32
    mov r14, rsi
    call .Lsystem_wide_path
    test rax, rax
    jz .Lreplace_failed_path
    mov r12, rax
    mov rdi, r14
    call .Lsystem_wide_path
    test rax, rax
    jz .Lreplace_second_failed
    mov r13, rax
    mov rcx, r12
    mov rdx, r13
    mov r8d, 9
    api MoveFileExW
    test eax, eax
    jnz .Lreplace_success
    api GetLastError
    neg rax
    jmp .Lreplace_free_paths
.Lreplace_success:
    xor eax, eax
.Lreplace_free_paths:
    mov r14, rax
    mov rdi, r13
    call .Lfree
    jmp .Lreplace_free_first
.Lreplace_second_failed:
    mov r14, qword ptr [r15+112]
    neg r14
.Lreplace_free_first:
    mov rdi, r12
    call .Lfree
    mov rax, r14
    jmp .Lreplace_done
.Lreplace_failed_path:
    mov rax, qword ptr [r15+112]
    neg rax
.Lreplace_done:
    lea rsp, [rbp-24]
    pop r14
    pop r13
    pop r12
    pop rbp
.else
    mov eax, 82
    syscall
.endif
    jmp .Lsystem_result

.global asrt_file_remove
asrt_file_remove:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    push r12
    push r13
    and rsp, -16
    sub rsp, 32
    call .Lsystem_wide_path
    test rax, rax
    jz .Lremove_bad_path
    mov r12, rax
    mov rcx, rax
    api DeleteFileW
    test eax, eax
    jnz .Lremove_success
    api GetLastError
    neg rax
    jmp .Lremove_free_path
.Lremove_success:
    xor eax, eax
.Lremove_free_path:
    mov r13, rax
    mov rdi, r12
    call .Lfree
    mov rax, r13
    jmp .Lremove_done
.Lremove_bad_path:
    mov rax, qword ptr [r15+112]
    neg rax
.Lremove_done:
    lea rsp, [rbp-16]
    pop r13
    pop r12
    pop rbp
.else
    mov eax, 87
    syscall
.endif
.Lsystem_result:
    test rax, rax
    jns .Lsystem_success
    neg rax
    mov qword ptr [r15+112], rax
    mov rax, -1
    ret
.Lsystem_success:
    mov qword ptr [r15+112], 0
    ret

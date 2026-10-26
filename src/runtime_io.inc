/* Raw standard input and monotonic milliseconds. No allocation or GC. */
.global asrt_read
asrt_read:
    test rsi, rsi
    js .Lread_bad_size
    jz .Lread_empty
    test rdi, rdi
    jz .Lread_null
    cmp rsi, 0x7fffffff
    jbe .Lread_size_ok
    mov esi, 0x7fffffff
.Lread_size_ok:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    push r12
    push r13
    and rsp, -16
    sub rsp, 64
    mov r12, rdi
    mov r13, rsi
    mov ecx, -10
    api GetStdHandle
    mov rcx, rax
    mov rdx, r12
    mov r8, r13
    lea r9, [rsp+48]
    mov qword ptr [rsp+32], 0
    api ReadFile
    test eax, eax
    jz .Lread_windows_error
    mov eax, dword ptr [rsp+48]
    jmp .Lread_windows_done
.Lread_windows_error:
    api GetLastError
    cmp eax, 109
    je .Lread_windows_eof
    cmp eax, 38
    je .Lread_windows_eof
    mov rax, -1
    jmp .Lread_windows_done
.Lread_windows_eof:
    xor eax, eax
.Lread_windows_done:
    mov r12, qword ptr [rbp-8]
    mov r13, qword ptr [rbp-16]
    mov rsp, rbp
    pop rbp
.else
    mov rdx, rsi
    mov rsi, rdi
    xor edi, edi
.Lread_retry:
    xor eax, eax
    syscall
    cmp rax, -4
    je .Lread_retry
    test rax, rax
    jns .Lread_return
    mov rax, -1
.Lread_return:
.endif
    ret
.Lread_empty:
    xor eax, eax
    ret
.Lread_bad_size:
    mov edi, 4
    mov rsi, rdx
    jmp .Lerror
.Lread_null:
    mov edi, 1
    mov rsi, rdx
    jmp .Lerror

.global asrt_now
asrt_now:
.ifdef AS_WINDOWS
    push rbp
    mov rbp, rsp
    and rsp, -16
    sub rsp, 32
    api GetTickCount64
    mov rsp, rbp
    pop rbp
.else
    sub rsp, 16
    mov edi, 1
    mov rsi, rsp
    mov eax, 228
    syscall
    test rax, rax
    js .Lnow_error
    mov rax, qword ptr [rsp+8]
    xor edx, edx
    mov ecx, 1000000
    div rcx
    imul rcx, qword ptr [rsp], 1000
    add rax, rcx
    add rsp, 16
    ret
.Lnow_error:
    add rsp, 16
    mov rax, -1
.endif
    ret

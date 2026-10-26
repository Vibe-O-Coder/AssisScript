/* Locale independent exact hexadecimal IEEE-754 output. No libc or heap. */
.global asrt_print_uint
asrt_print_uint:
    sub rsp, 64
    mov r9, rsi
    mov rax, rdi
    lea r8, [rsp+63]
    mov ecx, 10
.Luint_digit:
    xor edx, edx
    div rcx
    add dl, 48
    mov byte ptr [r8], dl
    dec r8
    test rax, rax
    jnz .Luint_digit
    inc r8
    lea rdx, [rsp+64]
    sub rdx, r8
    mov rdi, r9
    mov rsi, r8
    call .Lwrite
    add rsp, 64
    ret

.global asrt_print_float
asrt_print_float:
    sub rsp, 64
    mov r9, rsi
    mov rax, rdi
    mov r10, rax
    lea r8, [rsp]
    test rax, rax
    jns .Lfloat_positive
    mov byte ptr [r8], 45
    inc r8
.Lfloat_positive:
    mov rcx, rax
    shr rcx, 52
    and ecx, 2047
    cmp ecx, 2047
    je .Lfloat_special
    mov word ptr [r8], 0x7830
    add r8, 2
    mov byte ptr [r8], 48
    test ecx, ecx
    jz .Lfloat_subnormal
    mov byte ptr [r8], 49
    sub ecx, 1023
    jmp .Lfloat_fraction
.Lfloat_subnormal:
    mov ecx, -1022
    mov rdx, rax
    shl rdx, 1
    test rdx, rdx
    jnz .Lfloat_fraction
    xor ecx, ecx
.Lfloat_fraction:
    inc r8
    mov byte ptr [r8], 46
    inc r8
    mov r11d, ecx
    shl rax, 12
    lea rsi, [rip+.Lfloat_hex]
    mov ecx, 13
.Lfloat_nibble:
    mov rdx, rax
    shr rdx, 60
    mov dl, byte ptr [rsi+rdx]
    mov byte ptr [r8], dl
    inc r8
    shl rax, 4
    dec ecx
    jnz .Lfloat_nibble
    mov byte ptr [r8], 112
    inc r8
    mov eax, r11d
    mov byte ptr [r8], 43
    test eax, eax
    jns .Lfloat_exp_abs
    mov byte ptr [r8], 45
    neg eax
.Lfloat_exp_abs:
    inc r8
    lea rsi, [rsp+63]
    mov ecx, 10
    xor r11d, r11d
.Lfloat_exp_digit:
    xor edx, edx
    div ecx
    add dl, 48
    mov byte ptr [rsi], dl
    dec rsi
    inc r11d
    test eax, eax
    jnz .Lfloat_exp_digit
.Lfloat_exp_copy:
    inc rsi
    mov dl, byte ptr [rsi]
    mov byte ptr [r8], dl
    inc r8
    dec r11d
    jnz .Lfloat_exp_copy
    jmp .Lfloat_out
.Lfloat_special:
    mov rdx, r10
    shl rdx, 12
    test rdx, rdx
    jnz .Lfloat_nan
    mov word ptr [r8], 0x6e69
    mov byte ptr [r8+2], 102
    jmp .Lfloat_special_end
.Lfloat_nan:
    mov word ptr [r8], 0x616e
    mov byte ptr [r8+2], 110
.Lfloat_special_end:
    add r8, 3
.Lfloat_out:
    mov rdi, r9
    mov rsi, rsp
    mov rdx, r8
    sub rdx, rsi
    call .Lwrite
    add rsp, 64
    ret
.Lfloat_hex: .ascii "0123456789abcdef"

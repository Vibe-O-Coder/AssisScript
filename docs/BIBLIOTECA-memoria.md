# std/memoria.assis

Biblioteca obrigatória. Importe `#yuri <std/memoria.assis>`.

`preencher(destino: *byte, quantidade: int, valor: byte)` preenche bytes. `copiar(destino: *byte, origem: *byte, quantidade: int)` copia buffers sem sobreposição. Ambas são O(n), exigem quantidade >= 0 e memória válida em todo o intervalo. Quantidade zero não acessa memória. Os aliases históricos permanecem disponíveis.

```assis
#yuri <std/memoria.assis>
assis assis_assis(): int {
    let buffer: *byte = alloc<byte>(128);
    preencher(buffer, 128, byte(255)); print(buffer[127]);
    free(buffer); return 0;
}
```

Somente libere ponteiros originais de alocação, uma única vez. Ponteiros emprestados por bytes(texto) não podem ser escritos ou liberados. Esta API não verifica capacidade, sobreposição ou tempo de vida; prefira Array<byte> na aplicação quando possível. [Catálogo](BIBLIOTECAS.md).

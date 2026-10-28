# std/memoria.assis

Biblioteca obrigatória. Importe `import "std/memory.assis";`.

`fill(destino: *byte, count: int, value: byte)` preenche bytes. `copy(destino: *byte, origem: *byte, count: int)` copia buffers sem sobreposição. Ambas são O(n), exigem quantidade >= 0 e memória válida em todo o intervalo. Quantidade zero não acessa memória. Os aliases históricos foram removidos.

```assis
import "std/memory.assis";
fn main(): int {
    let buffer: *byte = alloc<byte>(128);
    fill(buffer, 128, byte(255)); print(buffer[127]);
    free(buffer); return 0;
}
```

Somente libere ponteiros originais de alocação, uma única vez. Ponteiros emprestados por bytes(texto) não podem ser escritos ou liberados. Esta API não verifica capacidade, sobreposição ou tempo de vida; prefira Array<byte> na aplicação quando possível. [Catálogo](BIBLIOTECAS.md).

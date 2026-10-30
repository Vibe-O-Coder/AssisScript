# std/memoria.assis

Biblioteca obrigatória. Importe `import "std/memory.assis";`.

Na continuação M1 de 29/10/2026, `ByteBuffer(max_bytes)` acrescenta armazenamento
de bytes com `try_reserve`, `try_resize`, `get`, `set`, `size`, `capacity`,
`max_bytes`, `clear` e `release`. Falha de reserva mantém os dados anteriores.
O limite de payload inclui a reserva antiga e a candidata durante a troca.
O controlador ainda usa new fatal; não é quota de RSS ou de todo o documento.
Veja o [contrato de alocação recuperável](ALOCACAO-FALLIVEL.md) e o
[exemplo](../exemplos/36_fallible_buffers.assis). Exige compilador reconstruído
com `try_alloc<T>`; não promove os pacotes anteriores.

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

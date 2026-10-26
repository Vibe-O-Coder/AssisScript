# std/codificacao.assis

Biblioteca opcional; selecione `--with encoding` ou instalação completa. Importe `#yuri <std/encoding.assis>`.

| API | Resultado |
| --- | --- |
| `hex_encode(Array<byte>)` | Texto proprietário, letras minúsculas |
| `hex_decode(text)` | ResultadoBytes; aceita ambas as caixas, exige pares sem espaços/prefixo |
| `base64_encode(Array<byte>)` | Texto proprietário com alfabeto padrão +/, padding =, sem quebras |
| `base64_decode(text)` | ResultadoBytes; exige múltiplo de quatro, padding final e bits canônicos |

Todas são O(n), aceitam entrada vazia e suportam dados binários com byte zero. Base64 URL e espaços não são aceitos. Essas codificações não criptografam os dados.

`BytesResult` contém `ok`, `position` e `data: Array<byte>`. Erro de formato é recuperável; dados pode conter prefixo parcial, que não deve ser consumido como resultado válido. Posição conta bytes a partir de zero. Libere o resultado com `dispose(); free()`, inclusive em erro. O Texto codificado exige a mesma dupla liberação.

```assis
#yuri <std/encoding.assis>
assis assis_assis(): int {
    let data: Array<byte> = [byte(0), byte(255)];
    let base64: String = base64_encode(data);
    print(base64.view());
    let original: BytesResult = base64_decode(base64.view());
    if (original.ok) { print(len(original.data)); }
    original.dispose(); free(original); base64.dispose(); free(base64); free(data); return 0;
}
```

Uso: transporte de bytes em campos de texto, logs binários e formatos de intercâmbio. [Catálogo](BIBLIOTECAS.md).

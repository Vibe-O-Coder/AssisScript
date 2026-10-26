# std/codificacao.assis

Biblioteca opcional; selecione `--with codificacao` ou instalação completa. Importe `#yuri <std/codificacao.assis>`.

| API | Resultado |
| --- | --- |
| `hexadecimal_codificar(Array<byte>)` | Texto proprietário, letras minúsculas |
| `hexadecimal_decodificar(text)` | ResultadoBytes; aceita ambas as caixas, exige pares sem espaços/prefixo |
| `base64_codificar(Array<byte>)` | Texto proprietário com alfabeto padrão +/, padding =, sem quebras |
| `base64_decodificar(text)` | ResultadoBytes; exige múltiplo de quatro, padding final e bits canônicos |

Todas são O(n), aceitam entrada vazia e suportam dados binários com byte zero. Base64 URL e espaços não são aceitos. Essas codificações não criptografam os dados.

`ResultadoBytes` contém `ok`, `posicao` e `dados: Array<byte>`. Erro de formato é recuperável; dados pode conter prefixo parcial, que não deve ser consumido como resultado válido. Posição conta bytes a partir de zero. Libere o resultado com `dispose(); free()`, inclusive em erro. O Texto codificado exige a mesma dupla liberação.

```assis
#yuri <std/codificacao.assis>
assis assis_assis(): int {
    let dados: Array<byte> = [byte(0), byte(255)];
    let base64: Texto = base64_codificar(dados);
    print(base64.visualizacao());
    let original: ResultadoBytes = base64_decodificar(base64.visualizacao());
    if (original.ok) { print(len(original.dados)); }
    original.dispose(); free(original); base64.dispose(); free(base64); free(dados); return 0;
}
```

Uso: transporte de bytes em campos de texto, logs binários e formatos de intercâmbio. [Catálogo](BIBLIOTECAS.md).

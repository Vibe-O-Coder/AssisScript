# std/texto.assis

**Atualização 3.3.0-alpha.7:** Alpha.7 adiciona Utf8Passo, utf8_proximo/contar/valido sobre buffers gerenciados e comprimento explícito, incluindo NUL. [Contratos](IO-E-APLICACAO-A.md). As APIs Texto anteriores continuam legadas.

Biblioteca obrigatória. Importe `import "std/strings.assis";`. Compilada diretamente para código nativo; não depende de serviço externo.

| API | Contrato |
| --- | --- |
| `starts_with(strings, prefixo): bool` | Compara bytes UTF-8, aceita prefixo vazio |
| `ends_with(strings, sufixo): bool` | Compara bytes UTF-8, aceita sufixo vazio |
| `contains(strings, trecho): bool` | Busca KMP em O(n+m) |
| `find_text(strings, trecho): int` | Primeiro offset de bytes ou -1; vazio retorna 0 |
| `substring(strings, start, count): String` | Cópia proprietária; intervalo válido obrigatório |
| `trim(strings): String` | Remove espaço, tab, CR e LF nas extremidades |
| `concat(a, b): String` | Copia duas entradas para texto independente |
| `join(partes: Array<text>, separador: text): String` | Junta entradas; array vazio produz texto vazio |
| `split(entrada, separador): Array<String>` | KMP O(n+m); separador não vazio; preserva partes vazias |
| `replace(entrada, busca, substituto): String` | Substitui ocorrências sem sobreposição; busca não vazia |
| `read_line(): String` | Lê stdin até LF/EOF; remove CR final; EOF sem dados produz vazio |

`String` possui buffer próprio e crescimento geométrico. `append(text)` aceita inclusive a própria visualização. `append_byte(byte)` exige byte diferente de zero. `size()` é O(1), `reserve(n)` garante capacidade incluindo terminador, `clear()` preserva capacidade e `dispose()` libera o buffer. Os campos com `_` são internos.

```assis
import "std/strings.assis";
fn main(): int {
    let mensagem: String = new String();
    mensagem.append("Pedido: "); mensagem.append("ação");
    print(mensagem.view());
    mensagem.dispose(); free(mensagem);
    return 0;
}
```

`view(): text` é emprestada: mutação ou liberação do proprietário invalida todas as visualizações. `dispose()` é repetível e permite reutilizar o objeto; `free(String)` sozinho não libera seu buffer. Libere ambos explicitamente. Recortes usam offsets de bytes, podendo cortar uma sequência UTF-8; não há normalização Unicode.

`bytes(text): *byte` e `text(*byte): text` são primitivas de baixo nível para bibliotecas. A primeira empresta os bytes sem copiar; não modifique nem libere o ponteiro. A segunda exige buffer não nulo, terminado em zero e vivo durante o uso. Ponteiros brutos não verificam limites. Prefira as operações acima no código de aplicação.

[Catálogo](BIBLIOTECAS.md)

As funções novas também retornam propriedade manual: `resultado.dispose(); free(resultado);`. Em `split`, libere cada `String` dessa forma antes de `free(partes)`. As partes são cópias e sobrevivem à entrada. `replace` libera suas partes intermediárias. A primeira implementação de `read_line` faz uma leitura por byte para preservar linhas sucessivas sem estado global; para volume use o intrínseco `read_bytes` com um buffer. Ele pode ler bytes zero; Texto não aceita NUL interno. [Entrada e tempo](MELHORIAS-3.2.md).
# Adições 3.3 alpha

Os campos de Texto são privados. `pop_byte(): void` trunca um byte em O(1), exige texto não vazio, mantém o terminador e pode cortar uma sequência UTF-8. Visualizações anteriores devem ser consideradas invalidadas. Use tamanho()/visualizacao() para consultar; ler_linha usa esses métodos e preserva a remoção de CR final.


# std/texto.assis

**Atualização 3.3.0-alpha.7:** Alpha.7 adiciona Utf8Passo, utf8_proximo/contar/valido sobre buffers gerenciados e comprimento explícito, incluindo NUL. [Contratos](IO-E-APLICACAO-A.md). As APIs Texto anteriores continuam legadas.

Biblioteca obrigatória. Importe `#yuri <std/texto.assis>`. Compilada diretamente para código nativo; não depende de serviço externo.

| API | Contrato |
| --- | --- |
| `comeca_com(texto, prefixo): bool` | Compara bytes UTF-8, aceita prefixo vazio |
| `termina_com(texto, sufixo): bool` | Compara bytes UTF-8, aceita sufixo vazio |
| `contem(texto, trecho): bool` | Busca KMP em O(n+m) |
| `encontrar_texto(texto, trecho): int` | Primeiro offset de bytes ou -1; vazio retorna 0 |
| `recortar_texto(texto, inicio, quantidade): Texto` | Cópia proprietária; intervalo válido obrigatório |
| `aparar_texto(texto): Texto` | Remove espaço, tab, CR e LF nas extremidades |
| `concatenar(a, b): Texto` | Copia duas entradas para texto independente |
| `juntar(partes: Array<text>, separador: text): Texto` | Junta entradas; array vazio produz texto vazio |
| `dividir(entrada, separador): Array<Texto>` | KMP O(n+m); separador não vazio; preserva partes vazias |
| `substituir(entrada, busca, substituto): Texto` | Substitui ocorrências sem sobreposição; busca não vazia |
| `ler_linha(): Texto` | Lê stdin até LF/EOF; remove CR final; EOF sem dados produz vazio |

`Texto` possui buffer próprio e crescimento geométrico. `adicionar(text)` aceita inclusive a própria visualização. `adicionar_byte(byte)` exige byte diferente de zero. `tamanho()` é O(1), `reservar(n)` garante capacidade incluindo terminador, `limpar()` preserva capacidade e `dispose()` libera o buffer. Os campos com `_` são internos.

```assis
#yuri <std/texto.assis>
assis assis_assis(): int {
    let mensagem: Texto = new Texto();
    mensagem.adicionar("Pedido: "); mensagem.adicionar("ação");
    print(mensagem.visualizacao());
    mensagem.dispose(); free(mensagem);
    return 0;
}
```

`visualizacao(): text` é emprestada: mutação ou liberação do proprietário invalida todas as visualizações. `dispose()` é repetível e permite reutilizar o objeto; `free(Texto)` sozinho não libera seu buffer. Libere ambos explicitamente. Recortes usam offsets de bytes, podendo cortar uma sequência UTF-8; não há normalização Unicode.

`bytes(text): *byte` e `text(*byte): text` são primitivas de baixo nível para bibliotecas. A primeira empresta os bytes sem copiar; não modifique nem libere o ponteiro. A segunda exige buffer não nulo, terminado em zero e vivo durante o uso. Ponteiros brutos não verificam limites. Prefira as operações acima no código de aplicação.

[Catálogo](BIBLIOTECAS.md)

As funções novas também retornam propriedade manual: `resultado.dispose(); free(resultado);`. Em `dividir`, libere cada `Texto` dessa forma antes de `free(partes)`. As partes são cópias e sobrevivem à entrada. `substituir` libera suas partes intermediárias. A primeira implementação de `ler_linha` faz uma leitura por byte para preservar linhas sucessivas sem estado global; para volume use o intrínseco `ler_bytes` com um buffer. Ele pode ler bytes zero; Texto não aceita NUL interno. [Entrada e tempo](MELHORIAS-3.2.md).
# Adições 3.3 alpha

Os campos de Texto são privados. `remover_ultimo_byte(): void` trunca um byte em O(1), exige texto não vazio, mantém o terminador e pode cortar uma sequência UTF-8. Visualizações anteriores devem ser consideradas invalidadas. Use tamanho()/visualizacao() para consultar; ler_linha usa esses métodos e preserva a remoção de CR final.


# std/algoritmos.assis

Na alpha.6, as alternativas `safe map_own<T,U>(borrow entrada: Array<T>, callback pure): own Array<U>`, `filter_own<T>` e `fold_borrow<T,A>` integram ownership. Preservam entrada/ordem e os limites escalares dos callbacks. Saídas own são limpas pelo chamador; não usar free/defer manual para duplicar essa limpeza. [Contratos e exemplo](OWNERSHIP-FUNCOES.md).

Biblioteca opcional. Incluída na instalação completa; selecione `--with algorithms` para instalação com apenas esta opção. Importe `#yuri <std/algorithms.assis>`.

| API | Comportamento e custo |
| --- | --- |
| `sort_ints(Array<int>): void` | Heapsort crescente no próprio array; O(n log n) no pior caso, O(1) auxiliar; não estável |
| `lower_bound(array, value): int` | Primeiro índice >= valor ou len; exige ordem crescente; O(log n) |
| `binary_search(array, value): int` | Primeiro índice igual ou -1; exige ordem crescente; O(log n) |
| `unique_sorted(array): int` | Remove duplicatas consecutivas no próprio array crescente; O(n); retorna tamanho |
| `map<T,U>(entrada, callback): Array<U>` | Callback pure, novo array na ordem original; O(n) |
| `filter<T>(entrada, predicado): Array<T>` | Predicado pure, novo array com ordem preservada; O(n) |
| `fold<T,A>(entrada, inicial, combinar): A` | Callback pure, redução da esquerda; inicial no vazio; O(n), O(1) auxiliar |

Vazios, duplicatas e extremos int64 são aceitos. As operações não assumem posse do array. `sift_down` é auxiliar interno; aplicações devem usar ordenar_inteiros.

```assis
#yuri <std/algorithms.assis>
assis assis_assis(): int {
    let precos: Array<int> = [300, 100, 300, 250];
    sort_ints(precos); unique_sorted(precos);
    print(binary_search(precos, 250));
    free(precos); return 0;
}
```

Uso: índices ordenados, deduplicação de IDs, relatórios e pesquisas em dados em memória. [Catálogo](BIBLIOTECAS.md).

Na alpha.3, map/filter/fold aceitam elementos/acumuladores escalares e funções pure; os tipos dos callbacks são verificados pelo compilador. Map/filter não alteram a entrada e devolvem nova alocação, que exige free/defer free; fold não aloca um array. São APIs de Array legado, sem empréstimos de own/borrow nas assinaturas. Contratos completos e exemplo em [funções e efeitos](FUNCOES-E-EFEITOS.md).

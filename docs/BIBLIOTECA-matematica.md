# std/matematica.assis

Biblioteca obrigatória. Importe `#yuri <std/matematica.assis>`.

`minimo(a, b)` e `maximo(a, b)` retornam o menor/maior int64. `limitar(valor, minimo, maximo)` restringe ao intervalo informado; forneça minimo <= maximo. `absoluto(valor)` usa aritmética modular: absoluto(INT64_MIN) continua INT64_MIN. Todas são O(1), sem alocação. Os aliases históricos continuam disponíveis.

Para detectar overflow ou divisão inválida, use [erros](BIBLIOTECA-erros.md).

```assis
#yuri <std/matematica.assis>
assis assis_assis(): int { print(limitar(150, 0, 100)); return 0; }
```

Uso: limites de paginação, quantidades, comparações e cálculos inteiros. [Catálogo](BIBLIOTECAS.md).

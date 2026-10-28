# std/matematica.assis

Biblioteca obrigatória. Importe `import "std/math.assis";`.

`min(a, b)` e `max(a, b)` retornam o menor/maior int64. `clamp(value, min, max)` restringe ao intervalo informado; forneça minimo <= maximo. `abs(value)` usa aritmética modular: absoluto(INT64_MIN) continua INT64_MIN. Todas são O(1), sem alocação. Os aliases históricos foram removidos.

Para detectar overflow ou divisão inválida, use [erros](BIBLIOTECA-erros.md).

```assis
import "std/math.assis";
fn main(): int { print(clamp(150, 0, 100)); return 0; }
```

Uso: limites de paginação, quantidades, comparações e cálculos inteiros. [Catálogo](BIBLIOTECAS.md).

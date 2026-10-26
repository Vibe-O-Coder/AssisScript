# Canonical English API — alpha.10

The language and standard library use English for canonical keywords, module names, public types, functions and members. Translated documentation keeps those identifiers unchanged. This policy governs project contributions; user-defined identifiers are not checked against an English dictionary.

## Syntax and compatibility

| Canonical | Previous spelling | Compatibility |
| --- | --- | --- |
| `fn`, `class`, `import` | `assis`, `ASSIS`, `importa` | Compiler aliases remain |
| `main` | `assis_assis` | Either entry works; declaring both is rejected |
| `init` | `assis_fodase` | Constructor aliases share one identity; duplicates are rejected |
| `File`, `file_open/read/write/close` | `Arquivo`, `arquivo_abrir/ler/escrever/fechar` | Builtin aliases remain |
| `file_sync/replace/remove` | `arquivo_sincronizar/substituir/remover` | Builtin aliases remain |
| `arg_count`, `arg_size`, `arg_copy` | `argumentos`, `argumento_tamanho`, `argumento_copiar` | Builtin aliases remain |
| `slice_of`, `read_bytes`, `write_bytes` | `fatia`, `ler_bytes`, `escrever_bytes` | Builtin aliases remain |
| `monotonic_ms`, `civil_ms`, `sleep_ms` | `agora`, `relogio_civil`, `dormir` | Builtin aliases remain |

`main` takes no arguments and returns `int` or `void`, stays outside namespaces and cannot be generic. CLI arguments come from the argument builtins. `fn` works in function types, pure/safe declarations and generic declarations. Ownership and effect checks are unchanged. `#yuri`, `#body`, `div`, `.assis`, `.pillow`, `.pkg` and `.lock` retain their existing roles and spellings.

The new English keyword spellings are reserved tokens. Rename older ordinary identifiers that use those spellings. Compiler aliases preserve the earlier syntax, rather than guaranteeing that every alpha.9 program compiles unchanged.

## Standard library migration

| Previous module | Current module |
| --- | --- |
| matematica | math |
| texto | strings |
| memoria | memory |
| erros | errors |
| conversoes | convert |
| algoritmos | algorithms |
| codificacao | encoding |
| tempo | time |
| iteradores | iterators |
| eventos | events |
| proprios | owned |

`cli`, `csv`, `json`, `log` and `unicode` keep their module names and receive English public APIs. Standard library renaming is a breaking alpha migration: the old module files and Portuguese API names are not installed. The explicit 2.x compatibility functions with historical branded names remain in math/memory/strings for the existing compatibility corpus; they are deprecated and are not the canonical API.

Examples: `minimo` → `min`, `ordenar_inteiros` → `sort_ints`, `Texto` → `String`, `tamanho` → `size`, `adicionar_byte` → `append_byte`, `ResultadoInt` → `IntResult`, `eventos::agendar` → `events::schedule`, `proprios::Lista` → `owned::OwnedList`. The global legacy `String` and managed `unicode::String` keep distinct contracts. Use `unicode::String` with `load`, `as_slice` and `slice_range` for managed UTF-8.

The [complete mapping](API-MIGRATION.json) covers renamed identifiers. Apply it to source identifiers and import paths; do not blindly replace text in user data, string literals or comments. The application A example now expects an English CSV header `value`; its output header remains `registros,total` for its documented data format.

1. Keep an alpha.9 copy of your sources and toolchain.
2. Rename imports and public API references, including field names such as `value`, `position`, `data`, `start`, `end` and `valid`.
3. Update callbacks/types and borrowed return origins when they name a renamed parameter.
4. Run `assis lock` from each package project, then `assis check`, tests and the relevant native programs.

Historical handoffs, validation reports and benchmark results preserve their original spellings and hashes. Their snippets describe the earlier compiler, rather than the current API. Library manual filenames remain stable so historical links continue to resolve.

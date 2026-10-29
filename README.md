# AssisScript

[Português (Brasil)](README.pt-BR.md) · [Español](README.es.md)

AssisScript is an experimental native language and the foundation of a proposed **new Web ecosystem**. It compiles directly to Linux x64/ARM64 ELF, Windows x64 PE and experimental macOS x64/ARM64 Mach-O executables. The browser, HTDL, style system and search engine are future ecosystem projects.

Development uses AI assistance (**GPT-6.1 Sol, Extra High reasoning / Extra Alto**). The concept, direction and structure were designed by humans, with AI assistance for suggestions. Humans remain responsible for reviewing and directing the implementation.

Current release: **3.3.0-alpha.15**, experimental. See the [handoff](docs/HANDOFF-3.3-ALPHA.15.md), [validation](docs/VALIDACAO-ALPHA15.json) and [weighted roadmap](docs/PROGRESSO.md).

Testing snapshot: see the [Windows/Linux testing guide](docs/TESTES-GITHUB.md) for the `testing/alpha15` branch, download links and how to report results. This snapshot retains the experimental status and documented outstanding gates.

[Closures, Move variants and owned results](docs/CAPTURAS-E-VARIANTES-MOVE.md).

## Canonical English APIs

Language keywords, standard library modules, public types, functions and members use **English**. Documentation may be translated; API names in examples stay in English. Canonical spellings include `fn`, `class`, `main`, `init`, `import`, `File`, `file_open`, `slice_of` and `monotonic_ms`.

Historical spellings and word comments were removed in alpha.14. The joke edition is isolated in [historical](docs/HISTORICAL.md). Use [the current language guide](docs/LINGUAGEM.md) and regenerate package lockfiles with `assis lock`.

```assis
pure fn double(value: int): int { return value * 2; }

safe fn main(): int {
    own values: Array<int> = [1, 2, 3];
    for (let i: int = 0; i < len(values); i += 1) {
        print(double(values[i]));
    }
    return 0;
}
```

## Get started

Windows: run `instalar-windows.cmd`. Linux: run `sh instalar.sh`. Open a new terminal after installation. See [installation](docs/INSTALACAO.md) for options.

```sh
assis version
assis check hello.assis --safe
assis run hello.assis --safe --debug
assis build hello.assis --safe -o hello
assis fmt hello.assis --check
assis test tests.assis --safe
assis doc hello.assis -o api.json
```

Compiled programs run without Node, Python, GCC or an external assembler. Building the compiler requires C11 and GNU binutils; tests and packaging use Python and Node.

The implementation includes pure functions, generics, function values, Copy records, enums/matching, Option/Result, ownership and borrowing with explicit lifetimes, managed classes, slices, UTF-8, native numeric types, collections, files, arguments, bounded JSON, cooperative events and offline packages. Editor/LSP, developer commands and Linux debugging are included.

Standard modules: `math`, `strings`, `memory`, `errors`, `convert`, `algorithms`, `csv`, `encoding`, `cli`, `json`, `time`, `log`, `iterators`, `events`, `unicode`, `owned`, `http`, `process`, `net`, `random`. See the [catalog](stdlib/catalogo.json) and [contracts](docs/BIBLIOTECAS.md). The global `String` class is legacy; `unicode::String` provides managed UTF-8 text.

Alpha.14 focuses on language usability: text output/building, global constants, byte characters, constructor chaining, two-phase receiver borrows, checked downcasts, indexed owned collections and random numbers. Closures already existed in alpha.13. Linux and Windows are tested natively; [macOS x86_64 is experimental](docs/MACOS.md). This review does not advance the internal roadmap percentage or claim browser readiness.

The alpha.15 development continuation completes typed IR emission, including memory, resources, control flow and debugging scopes. Independent acceptance was confirmed by the project owner. Estimated progress: **97% (97/100)**; see [implementation and validation](docs/BACKEND-IR-COMPLETA.md) and [remaining work](docs/RESTANTE-PARA-100.md). Native ARM64 output and distribution policy remain open.

## Use, libraries and forks

The maintainer selected **CC BY-NC-SA 4.0** for the project's original licensed materials. Read [LICENSE](LICENSE), the [official license](https://creativecommons.org/licenses/by-nc-sa/4.0/), [provenance](docs/PROCEDENCIA.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

1. Commercial use of licensed project materials is not granted. Obtain separate permission from the relevant rights holders when the license or applicable law does not already permit your intended use.
2. You may create AssisScript libraries. Independent libraries may declare their own license; libraries incorporating project code must comply with the applicable attribution, noncommercial and sharing terms. Contributions follow this repository's license and English API policy.
3. Redistributed forks/adaptations must credit **Vibe-O-Coder / AssisScript**, link to [the original repository](https://github.com/Vibe-O-Coder/AssisScript), retain required notices, identify changes and follow ShareAlike. Identify unofficial versions clearly and do not imply endorsement.
4. These notes do not add license restrictions or relicense third-party material. Compiling independent code does not automatically relicense it; copied or embedded project code, including runtime material, retains its applicable terms.
5. There is no warranty. Report defects through [GitHub issues](https://github.com/Vibe-O-Coder/AssisScript/issues). See [support and compatibility](docs/SUPPORT.md).

## Validation

The Makefile and CI cover Windows/Linux native execution, semantic rejections, editor/LSP, clean reconstruction, packaging and strided-key performance. New tests: `make test-alpha15`. Contributions should preserve contracts, use English public APIs and include relevant validation. Record evidence before changing roadmap credit.


## Native ARM64 / v1 candidate

This revision adds `linux-arm64` and `macos-arm64`, a native ARM64 runtime,
Mach-O DWARF symbols, ad hoc ARM64 signatures and `--app` macOS bundles with
the selected v1 icons. See [the target contract](docs/ARM64-NATIVO.md) and
[the applied identity/provenance review](docs/PROCEDENCIA-V1.md).
Native macOS/ARM64 acceptance of this candidate is pending its Actions run.
The Linux compiler now uses compatible system glibc; generated programs
without extern dependencies retain the freestanding project runtime.

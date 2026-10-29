# AssisScript

[English](README.md) · [Español](README.es.md)

AssisScript é uma linguagem nativa experimental e a base de um projeto de **novo ecossistema Web**. Compila diretamente para Linux x86_64, Windows x64 e macOS x86_64 experimental. Navegador, HTDL, estilos e motor de busca são projetos futuros.

A implementação é desenvolvida com assistência de IA (**GPT-6.1 Sol, raciocínio Extra Alto**). Toda a ideia, direção e estrutura do projeto foram concebidas por humanos, com assistência de IAs em sugestões. A revisão e as decisões permanecem sob direção humana.

Versão atual: **3.3.0-alpha.15**, experimental. Consulte [handoff](docs/HANDOFF-3.3-ALPHA.15.md), [validação](docs/VALIDACAO-ALPHA15.json) e [progresso auditável](docs/PROGRESSO.md).

Versão para testes: consulte o [guia Windows/Linux](docs/TESTES-GITHUB.md) para baixar a branch `testing/alpha15` e registrar resultados. A publicação mantém o estado experimental e as pendências documentadas.

[Closures, variantes Move e resultados proprietários](docs/CAPTURAS-E-VARIANTES-MOVE.md).

## Linguagem e stdlib em inglês

As palavras canônicas da linguagem e os nomes públicos de módulos, tipos, funções e membros da biblioteca padrão devem ser **em inglês**. A documentação pode ter traduções; os nomes das APIs nos exemplos continuam em inglês. Use `fn`, `class`, `main`, `init`, `import`, `File`, `file_open`, `slice_of` e `monotonic_ms`.

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

Alpha.11: ABI C escalar, callbacks, HTTP(S), processos/pipes e serviço persistente B/C delimitados. [Contratos e limites](docs/HANDOFF-3.3-ALPHA.11.md). Progresso estimado: 85%; 24 horas reais, capturas/variantes Move e cancelamento assíncrono seguem pendentes.

## Começar

No Windows, execute `instalar-windows.cmd`. No Linux, execute `sh instalar.sh`. Abra um novo terminal. A [documentação de instalação](docs/INSTALACAO.md) descreve as opções.

```sh
assis check hello.assis --safe
assis run hello.assis --safe --debug
assis build hello.assis --safe -o hello
```

Os programas compilados executam sem Python, Node, GCC ou assembler externo. Para reconstruir o compilador, são necessários C11 e GNU binutils; testes e empacotamento usam Python e Node.

Há funções puras, generics, funções como valores, registros Copy, enums/matching, Option/Result, ownership, empréstimos e vidas explícitas, classes gerenciadas, fatias, UTF-8, números nativos, coleções, arquivos, argumentos, JSON limitado, eventos cooperativos e pacotes offline. Editor/LSP, ferramentas e depuração Linux acompanham a distribuição.

Módulos: `math`, `strings`, `memory`, `errors`, `convert`, `algorithms`, `csv`, `encoding`, `cli`, `json`, `time`, `log`, `iterators`, `events`, `unicode`, `owned`, `http` e `process`. Consulte [catálogo](stdlib/catalogo.json) e [contratos](docs/BIBLIOTECAS.md).

Alpha.14 focuses on language usability: text output/building, global constants, byte characters, constructor chaining, two-phase receiver borrows, checked downcasts, indexed owned collections and random numbers. Closures already existed in alpha.13. Linux and Windows are tested natively; [macOS x86_64 is experimental](docs/MACOS.md). This review does not advance the internal roadmap percentage or claim browser readiness.

A continuação de desenvolvimento da alpha.15 conclui a emissão por IR tipada, incluindo memória, recursos, controle e escopos de depuração. O responsável confirmou o aceite independente. Progresso: **97% estimados (97/100)**; consulte a [implementação e validação](docs/BACKEND-IR-COMPLETA.md) e o [trabalho restante](docs/RESTANTE-PARA-100.md). Geração nativa ARM64 e política de distribuição continuam abertas.

## Uso, bibliotecas e versões alternativas

A licença escolhida pelo responsável para os materiais originais é **CC BY-NC-SA 4.0**. Leia [LICENSE](LICENSE), a [licença oficial](https://creativecommons.org/licenses/by-nc-sa/4.0/), a [procedência](docs/PROCEDENCIA.md) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md).

1. Não é concedido uso comercial dos materiais licenciados. Quando a licença ou a lei não autorizarem o uso pretendido, obtenha permissão separada dos titulares pertinentes.
2. É permitida a criação de bibliotecas para AssisScript. Código independente pode ter licença própria; código que incorpore partes do projeto deve cumprir os termos aplicáveis de crédito, uso não comercial e compartilhamento. Contribuições seguem a licença do repositório e a política de APIs em inglês.
3. Forks e adaptações redistribuídas devem creditar **Vibe-O-Coder / AssisScript**, ligar ao [original](https://github.com/Vibe-O-Coder/AssisScript), preservar avisos, indicar mudanças e respeitar ShareAlike. Identifique versões não oficiais e não sugira endosso.
4. Estas notas não acrescentam restrições à licença nem alteram licenças de terceiros. Código próprio não recebe automaticamente a licença do compilador por ser compilado; trechos copiados ou incorporados, inclusive runtime, conservam seus termos.
5. Não há garantia. Relate problemas nas [issues](https://github.com/Vibe-O-Coder/AssisScript/issues). A [política de suporte](docs/SUPPORT.md) explica compatibilidade, atualizações e limitações.

O Makefile e a CI incluem testes nativos, editor/LSP, reconstrução limpa, pacotes e regressão de desempenho. As novas suítes são reunidas em `make test-alpha10`.


## Native ARM64 / v1

This revision adds `linux-arm64` and `macos-arm64`, a native ARM64 runtime,
Mach-O DWARF symbols, ad hoc ARM64 signatures and `--app` macOS bundles with
the selected v1 icons. See [the target contract](docs/ARM64-NATIVO.md) and
[the applied identity/provenance review](docs/PROCEDENCIA-V1.md).
Native Linux ARM64, macOS Intel and Apple Silicon execution, debugging, installers and packages passed [Actions 40847421481](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40847421481) at revision `bb1605d`. The 35-criterion roadmap is complete at 100/100; this remains an experimental alpha.
The Linux compiler now uses compatible system glibc; generated programs
without extern dependencies retain the freestanding project runtime.

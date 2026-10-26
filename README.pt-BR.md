# AssisScript

[English](README.md) · [Español](README.es.md)

AssisScript é uma linguagem nativa experimental e a base de um projeto de **novo ecossistema Web**. Compila diretamente para Linux x86_64 e Windows x64. Navegador, HTDL, estilos e motor de busca são projetos futuros.

A implementação é desenvolvida com assistência de IA (**GPT-6.1 Sol, raciocínio Extra Alto**). Toda a ideia, direção e estrutura do projeto foram concebidas por humanos, com assistência de IAs em sugestões. A revisão e as decisões permanecem sob direção humana.

Versão atual: **3.3.0-alpha.10**, experimental. Consulte [handoff](docs/HANDOFF-3.3-ALPHA.10.md), [validação](docs/VALIDACAO-3.3-ALPHA.10.md) e [progresso auditável](docs/PROGRESSO.md).

## Linguagem e stdlib em inglês

As palavras canônicas da linguagem e os nomes públicos de módulos, tipos, funções e membros da biblioteca padrão devem ser **em inglês**. A documentação pode ter traduções; os nomes das APIs nos exemplos continuam em inglês. Use `fn`, `class`, `main`, `init`, `import`, `File`, `file_open`, `slice_of` e `monotonic_ms`.

As grafias históricas da sintaxe continuam como aliases do compilador. Os nomes portugueses da stdlib foram substituídos na alpha.10: atualize imports e chamadas conforme o [guia](docs/ENGLISH-API.md) e o [mapa completo](docs/API-MIGRATION.json). Projetos com manifesto precisam executar `assis lock` novamente.

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

## Começar

No Windows, execute `instalar-windows.cmd`. No Linux, execute `sh instalar.sh`. Abra um novo terminal. A [documentação de instalação](docs/INSTALACAO.md) descreve as opções.

```sh
assis check hello.assis --safe
assis run hello.assis --safe --debug
assis build hello.assis --safe -o hello
```

Os programas compilados executam sem Python, Node, GCC ou assembler externo. Para reconstruir o compilador, são necessários C11 e GNU binutils; testes e empacotamento usam Python e Node.

Há funções puras, generics, funções como valores, registros Copy, enums/matching, Option/Result, ownership, empréstimos e vidas explícitas, classes gerenciadas, fatias, UTF-8, números nativos, coleções, arquivos, argumentos, JSON limitado, eventos cooperativos e pacotes offline. Editor/LSP, ferramentas e depuração Linux acompanham a distribuição.

Módulos: `math`, `strings`, `memory`, `errors`, `convert`, `algorithms`, `csv`, `encoding`, `cli`, `json`, `time`, `log`, `iterators`, `events`, `unicode` e `owned`. Consulte [catálogo](stdlib/catalogo.json) e [contratos](docs/BIBLIOTECAS.md).

Continuam abertos capturas/closures, variantes Move, FFI C, rede/DNS/HTTP/TLS, aplicações B/C completas, validação real de 24 horas, backend integral por IR, ARM64/macOS e aceite independente. `--safe` é um perfil explícito. O percentual do plano não significa prontidão para produção.

## Uso, bibliotecas e versões alternativas

A licença escolhida pelo responsável para os materiais originais é **CC BY-NC-SA 4.0**. Leia [LICENSE](LICENSE), a [licença oficial](https://creativecommons.org/licenses/by-nc-sa/4.0/), a [procedência](docs/PROCEDENCIA.md) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md).

1. Não é concedido uso comercial dos materiais licenciados. Quando a licença ou a lei não autorizarem o uso pretendido, obtenha permissão separada dos titulares pertinentes.
2. É permitida a criação de bibliotecas para AssisScript. Código independente pode ter licença própria; código que incorpore partes do projeto deve cumprir os termos aplicáveis de crédito, uso não comercial e compartilhamento. Contribuições seguem a licença do repositório e a política de APIs em inglês.
3. Forks e adaptações redistribuídas devem creditar **Vibe-O-Coder / AssisScript**, ligar ao [original](https://github.com/Vibe-O-Coder/AssisScript), preservar avisos, indicar mudanças e respeitar ShareAlike. Identifique versões não oficiais e não sugira endosso.
4. Estas notas não acrescentam restrições à licença nem alteram licenças de terceiros. Código próprio não recebe automaticamente a licença do compilador por ser compilado; trechos copiados ou incorporados, inclusive runtime, conservam seus termos.
5. Não há garantia. Relate problemas nas [issues](https://github.com/Vibe-O-Coder/AssisScript/issues). A [política de suporte](docs/SUPPORT.md) explica compatibilidade, atualizações e limitações.

O Makefile e a CI incluem testes nativos, editor/LSP, reconstrução limpa, pacotes e regressão de desempenho. As novas suítes são reunidas em `make test-alpha10`.

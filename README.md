# AssisScript 3.3.0-alpha.9

Alpha.9 acrescenta classes com receptor/own, fatias com vidas, `unicode::Texto`, `proprios::Lista<T>`, HIR inicial e ELF PIE com locais escalares no GDB. [Handoff](docs/HANDOFF-3.3-ALPHA.9.md), [contratos](docs/RECURSOS-E-FATIAS.md), [progresso: 76%](docs/PROGRESSO.md). Ainda experimental; alvo de 90–100% não atingido.

Versão experimental com registros imutáveis por valor, enums genéricos, matching exaustivo e Option/Result sem alocação. Arquivos own, argumentos Unicode e a aplicação CSV em fluxo integram IO ao modelo gerenciado. Veja [valores/variantes](docs/VALORES-E-VARIANTES.md), [IO e aplicação A](docs/IO-E-APLICACAO-A.md), [ABI](docs/ABI-NATIVA.md) e o [handoff alpha.7](docs/HANDOFF-3.3-ALPHA.7.md).

A estimativa de conclusão do plano é **56%** (56 pontos de 100), pela mesma [régua](docs/PROGRESSO.md). O alvo de 70–80% ainda não foi atingido. Classes/Texto e coleções de proprietários, capturas/closures, text/slices gerais, integrações externas e aplicações B/C continuam pendentes. Isso não é um prazo nem prontidão geral de produção.

Novo: alocador com reutilização, variáveis em registradores, indexação O(1) de textos locais, `own`/`borrow`/`move` sem GC, `div { ... }`, `for`, `defer free`, entrada padrão e tempo monotônico. Veja [melhorias e limites da versão](docs/MELHORIAS-3.2.md), [memória e div](docs/MEMORIA-OWNERSHIP.md) e [comparação reproduzível com C e Python](benchmarks/resultados/nativo-3.2.md). Ownership agora atravessa funções com contratos explícitos; código legado com ponteiros mantém seu contrato manual.

Compilador nativo x86_64 para Windows (PE32+) e Linux (ELF64), com linguagem legível, coleções tipadas e extensão para VS Code. O compilador distribuído gera código de máquina diretamente e não precisa de GCC, Python, Node ou ferramentas externas na máquina do usuário.

```assis
#yuri <std/matematica.assis>

struct Pessoa {
    let nome: text;
    let idade: int;
}

assis assis_assis(): int {
    let pessoa: Pessoa = new Pessoa("Miyabi", 24);
    let numeros: Array<int> = [10, 20, 30];
    numeros.push(maximo(35, 40));
    numeros[0] += 2;

    let pontos: HashMap<text, int> = new HashMap<text, int>();
    pontos.set(pessoa.nome, numeros[0]);
    print(pessoa.nome, pontos.get(pessoa.nome), len(numeros));

    free(pontos);
    free(numeros);
    free(pessoa);
    return 0;
}
```

Nomes agora são livres: `contador`, `Pessoa`, `calcular_total`. `assis` declara funções e métodos, `ASSIS` declara classes, `assis_fodase` é o inicializador e `assis_assis` é a entrada. As palavras antigas permanecem disponíveis como aliases.

## Instalar e usar

No Windows x64, execute `instalar-windows.cmd`, reabra o terminal e use:

```powershell
assis version
assis new meu-projeto
cd meu-projeto
assis run
assis build -o programa.exe
```

O instalador registra a primeira imagem fornecida como ícone de `.assis`, por usuário. A segunda imagem é incorporada como recurso de ícone em todo executável Windows gerado. Para uma instalação sem associação de arquivos, use `bin/assis-setup.exe install --no-associations`. A opção `--no-path` preserva o PATH.

No Linux x86_64, execute `sh instalar.sh` e reabra o terminal. Também é possível usar `bin/assis` ou `bin/assis.exe` diretamente. Programas gerados são independentes do compilador. O ELF não possui ícone de Explorer; as imagens permanecem em `assets/`.

## VS Code

Instale **dist/assisscript-3.3.0-alpha.9.vsix** pelo comando **Extensões: Instalar do VSIX**. O pacote contém compiladores, 16 bibliotecas, documentação e os dois ícones, com funcionamento offline. **AssisScript: Documentação das bibliotecas nativas** abre o manual individual de cada biblioteca.

- Hover técnico de palavras da linguagem, funções padrão e métodos de `Array<T>`/`HashMap<K, V>`.
- Documentação de bibliotecas próprias por `///`, `miyabi` ou `/** ... */` antes da declaração.
- Assinaturas, sugestões, F12, estrutura do arquivo e diagnósticos em fontes não salvos.
- Reconhecimento de `.pillow`, importações transitivas e pacotes.
- Comandos **AssisScript: Abrir documentação da linguagem** e **AssisScript: Ativar ícones de arquivos**.

O tema de ícones precisa estar selecionado para prevalecer sobre temas que já atribuem outro ícone a arquivos desconhecidos. O workspace incluído já seleciona o tema AssisScript. Veja [docs/VSCODE.md](docs/VSCODE.md).

## Módulos e pacotes

```assis
#yuri <std/texto.assis>
#yuri <bibliotecas/utilidades.assis>
#body src.pillow
```

Cada diretiva ocupa sua própria linha. `.assis` é obrigatório em `#yuri`; `.pillow` é obrigatório em `#body`. Um pacote é um manifesto como:

```assis
// src.pillow
#yuri <src/modelos.assis>
#yuri <src/servicos.assis>
#body dependencias.pillow
```

Os fontes do pacote compartilham o mesmo espaço global de nomes. Não há download de dependências nem namespaces automáticos. [Detalhes de bibliotecas e pacotes](docs/BIBLIOTECAS.md).

## Comandos

| Comando | Resultado |
| --- | --- |
| `assis new pasta` | Cria projeto com array, pacote e biblioteca documentada |
| `assis run [arquivo.assis]` | Compila e executa |
| `assis run arquivo.assis --timeout 5` | Limita a execução a cinco segundos |
| `assis build [arquivo.assis] -o programa` | Gera executável nativo |
| `assis check [arquivo.assis]` | Verifica sintaxe e tipos |
| `assis check biblioteca.assis --library` | Verifica biblioteca sem entrada |
| `assis check pacote.pillow --library` | Verifica todos os fontes do pacote |
| `assis tokens arquivo.assis` | Mostra tokens e posições |
| `assis doctor` | Mostra os backends e a instalação |

Sem fonte, a entrada é `assis.assis`. `build` aceita `--target windows-x64` e `--target linux-x64`; `run` exige o sistema atual. `-I pasta` e `ASSIS_PATH` acrescentam caminhos de bibliotecas. `--stdin`, `--overlay` e `--diagnostics=json` atendem a integração com editores.

## Documentação e exemplos

A versão 3.1 oferece cinco bibliotecas obrigatórias na instalação (`matematica`, `texto`, `memoria`, `erros`, `conversoes`) e três opcionais (`algoritmos`, `csv`, `codificacao`). A instalação padrão inclui todas; `--minimal` instala o núcleo e `--with csv,algoritmos` seleciona opcionais. Bibliotecas instaladas só são usadas ao importar e não exigem downloads.

Otimizações nativas estão ativas por padrão. `--no-opt` permite comparação; limites, asserts e erros de execução permanecem verificados. Há conversões com overflow detectado, resultados recuperáveis, `try_get`/`try_pop`, mensagens em `assert` e ajuda nos diagnósticos. Os exemplos `12_relatorio_vendas.assis` e `13_codificacao.assis` demonstram processamento de dados e transporte binário. Veja [desempenho e medições reproduzíveis](docs/DESEMPENHO.md) e [tratamento de erros](docs/ERROS.md).

- [Manual da linguagem](docs/LINGUAGEM.md)
- [Coleções e memória](docs/COLECOES.md)
- [Bibliotecas e pacotes](docs/BIBLIOTECAS.md)
- [Migração de 2.x para 3.0](docs/MIGRACAO-3.md)
- [Gramática](docs/GRAMATICA.ebnf)
- [Windows](docs/WINDOWS.md)
- [Validação](docs/VALIDACAO.md)

`exemplos/01_ola.assis` até `08_modulos.assis` preservam exemplos antigos. `09_colecoes.assis`, `10_structs.assis` e `11_pacotes.assis` demonstram a versão 3.0.

## Desenvolvimento

Linux: `make`, `make test`, `make test-pe`. Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe` e `tests/test-windows.ps1`. As mudanças nos runtimes exigem `python tools/embed-runtime.py` (GNU binutils) ou `sh tools/embed-runtime.sh`.

Testes adicionais: `node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js tests/test-v32.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js`. Para desempenho: `node tools/benchmark.js`. Para distribuir: `python tools/package-vscode.py` e `python tools/package-release.py`. A conversão dos ícones usa Pillow somente durante o desenvolvimento: `python tools/build-icons.py`.

Encapsulamento e primeiro núcleo funcional: `python tests/test-evolution.py` em Windows/Linux, ou `make test-evolution` no Linux. `ASSIS_BIN` seleciona um compilador candidato. O mesmo conjunto verifica check/build/run, ambos os modos de otimização, diagnósticos, preservação de saída existente e ambos os destinos. A configuração em `.github/workflows/ci.yml` reproduz builds nativos e empacota os binários dos dois sistemas; sua execução remota depende de publicar o projeto num repositório.

Especialização de funções e structs: `python tests/test-generics.py` ou `make test-generics`. Exemplo: `identidade::<int>(42)` e `Caixa<int>`. A implementação opera sobre AST e identidades de definições/tipos; o corpo de cada instância concreta passa por tipagem, pureza e ownership. Os templates intrínsecos de Array/HashMap ainda usam o gerador anterior, integrado à resolução dos tipos concretos.

Coleções por AST: `python tests/test-collections-ast.py` ou `make test-collections-ast`. Comparação com a alpha.4: `tools/benchmark-collections-ast.py --baseline CAMINHO --output RELATORIO.json`. Progresso auditável: [PROGRESSO.md](docs/PROGRESSO.md), gerado de [PROGRESSO.json](docs/PROGRESSO.json); conferir com `python tools/report-progress.py --check`.

## Evolução alpha.8

Números nativos (inteiros de largura fixa, f32/f64), namespaces, pacotes offline com lockfile, JSON limitado, IO completo, relógios, logs, pipelines e eventos cooperativos. Ferramentas: `assis fmt`, `assis test`, `assis doc`, `build --symbols` e servidor LSP independente.

Consulte [o handoff atual](docs/HANDOFF-3.3-ALPHA.8.md), [a validação](docs/VALIDACAO-3.3-ALPHA.8.md) e [o progresso auditável](docs/PROGRESSO.md). A versão continua experimental; há contratos e limites por recurso, sem afirmar prontidão geral de serviços.

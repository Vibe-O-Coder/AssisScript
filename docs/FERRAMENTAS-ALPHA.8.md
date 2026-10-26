# Ferramentas de desenvolvimento — alpha.8

O compilador distribuído executa estes comandos sem chamar Node, Python, C ou assembler:

- `assis fmt arquivo.assis`: normaliza LF, indentação de blocos em quatro espaços e espaços ao fim das linhas. Preserva tokens, comentários e literais; não divide instruções numa mesma linha. `--check` não grava e retorna 1 se houver diferença. Substituição usa arquivo temporário exclusivo; erros léxicos/blocos desequilibrados preservam o original.
- `assis test testes.assis --debug --timeout 10`: executa funções globais do arquivo cujo nome começa por `test_` ou `teste_`. Sem parâmetros ou generics; `void` passa se retornar normalmente, `int` passa com zero e `bool` com true. A entrada normal não é executada. Recursos own são limpos em cada função. Asserção/falha fatal encerra a suíte com código 70; timeout usa o contrato de `run`. `--safe` exige todas as funções de teste safe/pure. Não é um executor isolado por caso.
- `assis doc biblioteca.assis [-o API.md]`: verifica tipos/ownership/efeitos e gera Markdown da API pública do arquivo, incluindo comentários `///`, tipos genéricos, campos, variantes, modos e vidas de retorno. Sem `-o`, escreve em stdout. Templates continuam com validação concreta por instanciação; gerar docs não certifica todo argumento de tipo possível.
- `assis build fonte.assis --symbols -o programa`: conserva a execução normal e acrescenta mapa JSON `programa.map.json`. Em ELF, também escreve `.symtab`, `.debug_line`, `.debug_info` e `.debug_abbrev` DWARF v4. O mapa contém RVAs, funções e posições de origem; no Windows, some RVA à base realmente carregada, considerando ASLR.

ELF ainda é ET_EXEC de base fixa; PIE continua pendente. DWARF permite breakpoints por linha, consulta de linha e backtrace de funções; não há descrição de variáveis locais, valores otimizados ou PDB Windows. Para um build Linux nativo, use `gdb ./programa`, `break arquivo.assis:linha`, `run`, `bt`. Cross-build Windows→Linux conserva caminhos Windows no debug; ajuste a busca/substituição de caminhos no depurador.

## LSP independente

`node tools/assis-lsp.js` inicia o servidor por stdio, sem dependências npm. Node 18 ou posterior é uma dependência **da ferramenta de editor**, não do compilador nem dos programas nativos. No VSIX, o script fica em `tools/`; no instalador Linux, em `share/assisscript/tools/`; Windows: `tools/` sob o prefixo.

Configure um cliente LSP com transporte stdio e `initializationOptions` opcionais: `compilerPath`, `includePaths` (array), `entryFile`. O cliente informa `rootUri`/`workspaceFolders`. O protocolo usa posições UTF-16, sincronização incremental ou completa, hover, conclusão, definição, símbolos de documento, assinaturas, formatação e diagnósticos do compilador. Documentos não salvos são snapshots temporários; o servidor não grava o fonte. Compila com `shell:false` e limite de tempo/tamanho. Versões antigas de diagnóstico são descartadas e processos superados são interrompidos.

O editor existente continua funcionando sem iniciar esse servidor; ambos usam a mesma análise de símbolos. Namespaces, tipos qualificados e navegação de `pkg/alias` estão integrados. O compilador é a autoridade de tipagem/lockfile; a navegação tolerante do editor não certifica contratos.

Testes: `tests/test-tooling.py`, `tests/test-lsp.js`; o primeiro exige readelf/GDB no destino Linux para provar breakpoints/backtrace reais. O segundo conversa com o servidor pelo framing LSP e verifica erro/correção de conteúdo não salvo após emoji.

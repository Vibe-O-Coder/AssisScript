# AssisScript 3.3 alpha no VS Code

Instale dist/assisscript-3.3.0-alpha.6.vsix em Extensões → menu … → Instalar do VSIX. Não é necessário Node, Python ou compilador C para usar o pacote. Ele contém os binários nativos, oito bibliotecas, referência de API, manuais e ícones. val/pure/private têm destaque, documentação e navegação; sugestões externas omitem membros privados. Há tipos de função aninhados e ajuda de parâmetros para callbacks tipados em variáveis/parâmetros. Na alpha.4, campos, métodos, construtores e bases genéricas recebem assinaturas concretas na navegação; o snippet genericaclasse cria uma classe parametrizada. Na alpha.5, a migração AST das coleções preserva a sintaxe e as assinaturas públicas. Na alpha.6, parâmetros own/borrow, retornos com origem de vida, tipos de callback safe e campos own preservam contratos na navegação e ajuda de assinatura. Snippets safeborrow e unsafe incluídos. A [estimativa de conclusão do plano é 45%](PROGRESSO.md). A integração foi validada pelos testes dos provedores, sem uma nova sessão visual do editor.

Funções `f<T>` e structs `Caixa<T>` são reconhecidas pelo editor. Navegação preserva a declaração original; ajuda de parâmetros em `f::<int>(...)` e `new Caixa<int>(...)` e campos de `Caixa<int>` exibem tipos substituídos. Os snippets `genericafuncao`, `genericstruct` e `genericachamada` inserem a sintaxe. O compilador é a autoridade para aridade, tipos, pureza e ownership; o editor não infere constraints ou vidas.

Use **AssisScript: Documentação das bibliotecas nativas** para escolher o manual individual offline. Hover e assinaturas acompanham novas funções e métodos recuperáveis. Diagnósticos mostram a indicação de correção e o intervalo informado pelo compilador. Veja [tratamento de erros](ERROS.md).

Abra AssisScript.code-workspace ou um projeto criado por assis new. Use os comandos AssisScript: Verificar arquivo, Compilar programa e Compilar e executar; Ctrl+Shift+B também oferece a tarefa de compilação.

## Ajuda técnica

Passe o mouse sobre palavras da linguagem, funções de stdlib, funções próprias ou métodos de Array<T>/HashMap<K, V>. A ajuda mostra assinatura, tipos concretos, efeitos, precondições, propriedade da memória e complexidade quando pertinente. Os métodos intrínsecos usam src/reference.json como fonte de documentação; funções padrão são documentadas nos próprios fontes.

Funções de biblioteca própria devem ter comentários ///, miyabi ou /** ... */ imediatamente acima. O texto chega ao hover e à ajuda de parâmetros. @param e @return são preservados na documentação. Sem comentário, a extensão oferece a assinatura.

Sugestões após ponto, F12, assinaturas e símbolos reconhecem nomes livres, structs, tipos genéricos, #yuri e #body. Pacotes .pillow são reconhecidos, percorridos e observados para atualização. Diagnósticos usam o compilador e incluem dependências não salvas.

O comando AssisScript: Abrir documentação da linguagem abre o manual incluído em pré-visualização Markdown, sem internet.

## Ícones

Execute AssisScript: Ativar ícones de arquivos ou selecione o tema AssisScript (Miyabi). A primeira imagem identifica .assis e .pillow. A contribuição da linguagem também fornece esse ícone como padrão quando o tema ativo permite. Temas de ícones de terceiros podem prevalecer; o tema incluído garante a associação. O workspace fornecido já seleciona esse tema.

O ícone do programa compilado é o segundo fornecido, incorporado no próprio PE Windows. Não depende do VS Code ou do tema. ELF Linux não tem recurso de ícone de Explorer.

## Configuração

- assisscript.compilerPath: caminho opcional do compilador; vazio usa o binário do VSIX.
- assisscript.entryFile: entrada do projeto, padrão assis.assis.
- assisscript.includePaths: diretórios adicionais, equivalentes a -I.
- assisscript.diagnostics: habilita análise durante a edição.
- assisscript.validationDelay: espera após digitação, padrão 350 ms.
- assisscript.runTimeout: limite de execução, padrão 10 segundos.

Execução e análise de código exigem workspace confiável; cores, documentação e navegação continuam disponíveis em modo restrito. Windows x64 e Linux x86_64 são os destinos suportados.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `time`, `log`, `iterators` e `events` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

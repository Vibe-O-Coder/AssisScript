# Validação — 3.3.0-alpha.5

Data: 25/10/2026, contexto local do usuário. Continuação da fase 1, migrando corpos de coleções para a especialização AST comum. A base comparável é a alpha.4 preservada em `build/baseline-3.3-alpha.4`; resultados antigos não são contados como validação atual.

## Estimativa de conclusão: 34%

**33,5/100 pontos**, pela [régua de 35 critérios ponderados](PROGRESSO.md). P1-COL avança de pendente para concluído; a avaliação retrospectiva da alpha.4 é 31% (30,5 pontos). Os mecanismos da fase 1 estão implementados, mas o gate F1 continua aberto pela propriedade das APIs funcionais, coberta na fase 2. A porcentagem estima o escopo definido, não prazo ou prontidão para produção. Arquivos/argumentos, vidas entre funções, dados algébricos, aplicações A/B/C e integração externa continuam pendentes.

## Verificações desta entrega

| Conjunto | Windows x64 | Linux x86_64 |
| --- | --- | --- |
| Compilador/editor Node | 72 testes aprovados | Corpora portáveis; Node não usado no WSL |
| Suíte nativa/instalador | 128 verificações aprovadas | 133 verificações aprovadas |
| Módulos/instalação Linux | — | 18 verificações aprovadas |
| Harness PE32+ com base relocada | Windows real coberto pelas suítes | 41 casos aprovados |
| Corpus 3.1 | 18 verificações aprovadas | 21 verificações aprovadas |
| Corpus 3.2 | 73 casos aprovados | 73 casos aprovados |
| Evolution | 12 grupos, 472 invocações | 12 grupos, 472 invocações |
| Generics | 13 grupos, 305 invocações | 13 grupos, 305 invocações |
| Functions | 19 grupos, 383 invocações | 19 grupos, 383 invocações |
| Generic classes | 17 grupos, 360 invocações | 17 grupos, 360 invocações |
| Collections AST (novo) | 10 grupos, 143 invocações | 10 grupos, 143 invocações |
| Reconstrução sem cache | Compilador idêntico byte a byte | Compilador idêntico byte a byte |
| Relatório de progresso | Gerado e conferido com --check | Mesmo relatório conferido com --check |

Os conjuntos têm sobreposição; não somar como casos independentes. As cinco suítes Python foram repetidas contra compiladores reconstruídos em árvores temporárias, com regeneração dos dois headers de runtime a partir de assembly. Os hashes coincidem com os compiladores atuais na mesma plataforma/toolchain; não é uma promessa entre toolchains distintas.

A suíte nova compara 140 operações de Array com uma lista independente e 180 operações de HashMap com um dicionário independente, usando sementes fixas. Também cobre colisões de texto e comparação por conteúdo com uma visão de buffer externo ainda vivo, byte/bool, operações recuperáveis, dispose/reutilização, callbacks em valores/arrays de HashMap, classes/structs genéricas aninhadas, assinatura de mil parâmetros, efeitos distintos, cache, orçamento de 256 instâncias do usuário separado do de coleções, rejeição da 257ª coleção, privacidade, nomes internos forjados, ownership e algoritmos funcionais.

Casos aceitos passam por check/run com debug, com e sem otimização, e build para ambos os destinos. Rejeições passam por check/build/run com e sem otimização e por build para os dois destinos explícitos; o arquivo sentinela não é alterado. Casos de índice inválido, pop vazio, capacidade inválida e chave ausente preservam R001/status 70. Não há execução de acessos privados rejeitados.

## Builds e hashes

Windows: MinGW/MSYS2 em `C:/msys64/ucrt64/bin`, flags de `tools/build-windows.ps1`, Python do runtime local e Node no PATH. Linux: GCC/Python3 do Ubuntu via WSL, flags do Makefile. O compilador distribuído continua autônomo para compilar programas comuns.

| Artefato | SHA-256 |
| --- | --- |
| bin/assis.exe | `7a597c78f726fb40bad3f4ac3c4056992c9a5d8ec96e597c90dc55e87e489067` |
| bin/assis | `9408324128831092715217eac62d75805bb58627d1c2f53932b53c3bfc2daba1` |
| bin/assis-setup.exe | `35fb003e6d3c005bf301700b29301557c55d5743a24389b2979302cc1f91b0ef` |

Logs locais: `build/build-alpha5-{win,linux}.log`, `node-alpha5-win.log`, `native-alpha5-win.log`, `regression-alpha5-linux.log`, `*-alpha5-win.log`, `portable31-alpha5-linux.log`, `portable32-alpha5-linux.log`, `clean-alpha5-{win,linux}.log`, `clean-win32.json` e `clean-linux.json`. Baseline e relação de alterações em `build/baseline-3.3-alpha.4` e `build/changes-alpha5.json`. Build/temporários ficam fora dos pacotes; SHA256SUMS cobre os arquivos distribuídos.

## Custo observado e equivalência

Relatórios completos: [Windows](../benchmarks/resultados/colecoes-ast-alpha-windows.md) e [Linux](../benchmarks/resultados/colecoes-ast-alpha-linux.md), com JSONs adjacentes contendo fontes, hashes de ambos os compiladores, amostras e comparações derivadas. Base: compiladores alpha.4 preservados, com hashes coerentes com a validação daquela entrega.

Sete amostras intercaladas após aquecimento, 1/8/32/64 tipos nominais, cada um acrescentando Array<Tag>/HashMap<int,Tag>, além de Array<int>/HashMap<int,int>. Com e sem otimização. O laço de dois mil elementos confere a fórmula independente `2*(3*N*(N-1)/2+7*N)`. Compilação e execução incluem início do processo. Plataformas medidas em sequência, depois dos testes, sem executar as duas cargas simultaneamente.

| Carga com 64 tipos, otimizada | Compilação alpha.4 mediana ms | Alpha.5 mediana ms | Variação |
| --- | ---: | ---: | ---: |
| Windows | 174,158 | 118,906 | −31,7% |
| Linux | 163,273 | 112,418 | −31,1% |

Todos os pares de executáveis comparados são idênticos byte a byte, em ambos os sistemas e modos. Variações de tempo de execução desses binários não correspondem a alterações no código emitido. A diferença medida de compilação caracteriza esta carga com várias especializações; entradas pequenas variam mais com startup/ruído. Não mede RAM, recursos proprietários, grafos, Unicode amplo ou aplicações reais e não demonstra ganho geral nem paridade com C/C++.

## Distribuição e limites

Pacotes: `dist/AssisScript-3.3.0-alpha.5-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.5.vsix`. A verificação extraída em Windows/Linux confere compiladores, hashes das medições, progresso JSON/Markdown, exemplos 12/14/15/16/17/18, oito bibliotecas e rejeições de privacidade/pureza/tipos. O ZIP passa pela conferência de SHA256SUMS. Logs locais: `build/verify-alpha5-{win,linux}.log`. Pacotes anteriores permanecem históricos.

Instalação/remoção foi testada em diretórios temporários, preservando arquivos pessoais e sem alterar PATH permanente/associações do usuário. CI atualizada sem execução remota, por ausência de repositório Git configurado. Provedores do editor validados por testes; não houve nova inspeção visual do VS Code.

Os mecanismos de especialização da fase 1 foram entregues; F1 integrado continua aberto. Não houve ampliação de pure, ownership entre funções, classes own/borrow, destruição de campos, structs por valor, variantes/matching, closures, arquivos/rede/FFI ou fronteira safe/unsafe obrigatória. A estimativa de 34% não altera a classificação experimental.

Na primeira execução Linux, o script de módulos estava com quebras de linha Windows após a atualização do marcador de versão. O arquivo foi normalizado para LF e a validação completa passou. Um aviso de qualificador const no carregamento dos templates foi corrigido antes das regressões finais; os builds finais não têm esse aviso. Não foi preciso alterar runtime, algoritmos ou verificações para passar os testes.

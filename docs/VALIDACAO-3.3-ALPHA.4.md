# Validação — 3.3.0-alpha.4

Data: 25/10/2026, contexto local do usuário. Esta entrega continua a fase 1 com classes genéricas, herança aplicada e métodos especializados. A alpha.3 foi preservada antes das alterações em `build/baseline-3.3-alpha.3`, com manifesto local `BASELINE-SHA256SUMS`. Os resultados abaixo foram repetidos nesta entrega; não são resultados herdados dos handoffs anteriores.

## Verificações

| Conjunto | Windows x64 | Linux x86_64 |
| --- | --- | --- |
| Compilador/editor Node | 72 testes aprovados | Corpora portáveis abaixo; Node não usado no WSL |
| Suíte nativa/instalador | 128 verificações aprovadas | 133 verificações aprovadas |
| Módulos/instalação Linux | — | 17 verificações aprovadas |
| Harness PE32+ com base relocada | Windows real coberto pelas suítes | 41 casos aprovados |
| Corpus 3.1 | 18 verificações aprovadas | 21 verificações aprovadas |
| Corpus 3.2 | 73 casos aprovados | 73 casos aprovados |
| Evolution | 12 grupos, 472 invocações | 12 grupos, 472 invocações |
| Generics | 13 grupos, 305 invocações | 13 grupos, 305 invocações |
| Functions | 19 grupos, 383 invocações | 19 grupos, 383 invocações |
| Generic classes (novo) | 17 grupos, 360 invocações | 17 grupos, 360 invocações |
| Reconstrução sem cache | Compilador idêntico byte a byte | Compilador idêntico byte a byte |

Os conjuntos têm sobreposição; não somar como casos independentes. A redução de 313 para 305 invocações de generics remove a antiga rejeição de toda classe genérica: a funcionalidade agora possui sua própria suíte. As quatro suítes Python também passaram contra compiladores reconstruídos em árvores temporárias, com regeneração de ambos os headers de runtime a partir de assembly. A identidade é verificada na mesma plataforma/toolchain; não é uma promessa entre compiladores C distintos.

A suíte nova cobre campos/construtores/métodos de int e text, substituição em locais/ponteiros/alocações/chamadas genéricas, callbacks em campos/argumentos/retornos, herança entre tipos genéricos e concretos, parâmetros reordenados, upcast e despacho virtual, recursão finita de tipos e métodos, Array/HashMap de classes, isolamento de privados entre especializações, privilégios de base e de funções livres, sobrescritas, inicializadores privados, aridade/tipos, bases inválidas/cíclicas, expansão por assinaturas/bases/corpos na fila, cache, limite compartilhado, pureza, ownership e diagnósticos de módulos com linha original e local de instanciação. Métodos de classes instanciadas são verificados mesmo sem chamada.

Casos aceitos passam por check/run com debug, com e sem otimização, e build para ambos os destinos. Casos negativos são rejeitados em check/build/run com e sem otimização e em build com cada destino explícito; o arquivo sentinela permanece intacto. Não foram executados acessos privados inválidos. O exemplo distribuído 18 produz `21 42`, sem diagnóstico de memória em debug.

## Builds e hashes

Windows: MinGW/MSYS2 em `C:/msys64/ucrt64/bin`, flags em `tools/build-windows.ps1`; Python do runtime local e Node no PATH. Linux: GCC/Python3 do Ubuntu via WSL, flags do Makefile. O compilador distribuído permanece autônomo para compilar programas comuns.

| Artefato | SHA-256 |
| --- | --- |
| bin/assis.exe | `0ea9693021f720b296c5da461831c0e9f7f84ae91b9f9b76716d26ee4d656f2a` |
| bin/assis | `bec5401cf789cd242eeb12c49121f0ce1e3d314602e82cb7136a6ab213e50c31` |
| bin/assis-setup.exe | `5c07e6ac6b7854327798b410c4a7fceed7ab452394e3dec58a381741c7b85664` |

Logs locais: `build/node-alpha4-win.log`, `native-alpha4-win.log`, `regression-alpha4-linux.log`, `*-alpha4-win.log`, `portable31-alpha4-linux.log`, `portable32-alpha4-linux.log`, `clean-alpha4-{win,linux}.log`, `clean-win32.json` e `clean-linux.json`. Fontes modificados estão relacionados em `build/changes-alpha4.json`. Build/baselines/temporários ficam fora da distribuição; SHA256SUMS cobre os arquivos empacotados.

## Custo e distribuição

Medições específicas: [Windows](../benchmarks/resultados/classes-alpha-windows.md) e [Linux](../benchmarks/resultados/classes-alpha-linux.md), com JSONs adjacentes contendo fontes, hashes, amostras e ambiente. Sete amostras intercaladas após aquecimento, 1/8/32/64 classes concretas, versões manuais e genéricas, com e sem otimização. Cada execução confere um milhão de chamadas virtuais pela fórmula independente `3*N*(N-1)/2+7*N`; compilação e execução incluem início de processo. As plataformas foram medidas em sequência depois dos testes, sem executar as duas cargas simultaneamente.

A carga mede crescimento de código e custo de compilação/especialização; o laço executa apenas a primeira classe. Não há desvirtualização/inlining novos, nem medição de RAM, recursos proprietários ou aplicações reais. Tempos pequenos e ruído não sustentam ganho geral, paridade com C/C++ ou prontidão de produção. Os relatórios anteriores permanecem históricos e preservam o hash de seu compilador.

Nesta carga, todos os pares manual/genérico têm o mesmo tamanho de executável, inclusive sem otimização. Com otimização, de 1 a 64 classes o PE cresce de 99.840 para 124.928 bytes e o ELF de 8.216 para 34.304 bytes. Isso caracteriza o crescimento desse programa; não estabelece equivalência para outros corpos ou distribuições de tipos.

Pacotes: `dist/AssisScript-3.3.0-alpha.4-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.4.vsix`. A verificação extrai o VSIX, confere os compiladores e os hashes dos relatórios de classes, executa os exemplos 12/14/15/16/17/18, valida as oito bibliotecas e rejeições de privacidade/pureza/tipos. O ZIP passa pela conferência de todos os hashes. A verificação é executada em Windows e Linux; logs `build/verify-alpha4-{win,linux}.log`. Pacotes anteriores são preservados como referência histórica.

Instalação/remoção foi testada em diretórios temporários, preservando arquivos pessoais e sem modificar PATH permanente ou associações do usuário. CI foi atualizada, sem execução remota por ausência de repositório Git configurado. Editor validado pelos testes dos provedores, sem nova inspeção visual do VS Code.

## Limites e ocorrências

O gate integrado de fase 1/F1 permanece aberto pela migração AST das coleções e pelos contratos de propriedade nas APIs funcionais. Métodos com parâmetros próprios, classes gerenciadas por own/borrow, vidas em assinaturas, destruição de campos, closures, dados algébricos, matching, structs por valor, IO de arquivos/rede/FFI e aplicações A/B/C não foram implementados. Pure continua restrito a escalares/funções pure. Não há imutabilidade profunda nova, modo safe/unsafe global ou conclusão de licença/procedência.

A tentativa inicial restrita falhou ao escrever temporários, antes de invocar o compilador; a execução autorizada funcionou. A primeira regressão nativa detectou expectativas de versão ainda fixadas na alpha.3; elas foram atualizadas e as suítes nativas completas passaram. Um verificador auxiliar local interpretou LASTEXITCODE não definido de um script PowerShell como falha, embora os 128 testes tivessem passado; a continuação usa o resultado das próprias suítes. Essas ocorrências não exigiram mudança de semântica ou runtime.

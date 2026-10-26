# Relatório e continuação — 3.3.0-alpha.2

**Continuação:** [HANDOFF-3.3-ALPHA.3.md](HANDOFF-3.3-ALPHA.3.md) registra funções como valores, efeitos em tipos e callbacks. O conteúdo abaixo preserva o estado histórico da alpha.2.

Data: 24/10/2026, conforme o contexto local do usuário. Continuação autorizada do [plano](PLANO-EVOLUCAO-E-HANDOFF.md), sobre a alpha.1 preservada em `build/baseline-3.3-alpha.1`. Não há repositório Git no workspace. O plano completo e F1 ainda não estão concluídos.

## Implementado

- DefId para definições/parâmetros e TypeId para tipos concretos; aplicações de tipo estruturadas, com origem.
- Funções globais e structs genéricas, múltiplos parâmetros, tipos aninhados, recursão finita e módulos. Chamadas explícitas `nome::<tipos>(argumentos)`.
- Templates guardados como AST; clonagem/substituição por identidade, cache canônico e fila transitiva antes de check/ownership/backend.
- Limites de 16 parâmetros, 256 instâncias do usuário e 64 níveis de expansão. Reutilização de instâncias já existentes antes de aplicar o limite de expansão.
- Privacidade nominal preservada e verificações de tipagem, pureza e ownership em cada instância concreta. Pure templates rejeitam efeitos sintáticos/chamadas impuras também quando não utilizados.
- Integração com Array/HashMap existentes; geração intrínseca usa símbolos concretos, sem depender do nome de exibição para reconstruir tipos.
- Editor: navegação de templates, assinaturas concretas de chamadas/construtores e campos genéricos; snippets e documentação. Exemplo `16_generics.assis`.
- Suíte portável `tests/test-generics.py`, benchmark `tools/benchmark-generics.py`, integração em CI, rebuild limpo e verificação de pacotes.

## Validação e distribuição

Ver [VALIDACAO-3.3-ALPHA.2.md](VALIDACAO-3.3-ALPHA.2.md) para evidência final, hashes, medições e limitações. Os pacotes desta versão são `dist/AssisScript-3.3.0-alpha.2-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.2.vsix`. Preservar os artefatos históricos da alpha.1 como referência, sem usá-los para testar generics do usuário.

Passaram 70 testes Node, 128 verificações nativas Windows, 133 Linux, 15 de módulos Linux, 41 casos PE, 21 verificações portáveis 3.1 e 73 casos 3.2. Evolution: 12 grupos/472 invocações por sistema. Generics: 13 grupos/313 invocações por sistema. Ambos foram repetidos nos builds sem cache, que reproduziram os compiladores byte a byte na mesma toolchain. Os conjuntos têm sobreposição.

Pacotes extraídos passaram em Windows/Linux: oito bibliotecas, quatro exemplos e 444 hashes. No benchmark escalar de sete amostras, manual e genérico emitiram executáveis idênticos byte a byte nos dois sistemas, com e sem otimização. Isso não mede RAM, muitas combinações de tipos, closures ou uma aplicação completa, e não comprova ganho de runtime por generics.

## Contratos e limitações

Leia [GENERICS.md](GENERICS.md) antes de ampliar o escopo. Corpos dependentes de tipos são verificados após instanciação; `check --library` não valida combinações não usadas. Não há inferência/constraints. Structs são referências ao heap; ownership permanece local, sem recursos proprietários em campos ou assinaturas com empréstimos. Pure continua escalar. Type conserva kind/depth/name como compatibilidade do backend; efeitos ainda são atributo da declaração de função, sem tipo de função de primeira classe.

Classes e métodos genéricos estão explicitamente rejeitados. Array/HashMap usam a resolução de tipos concretos/cache de coleções, mas seus corpos ainda passam pelo gerador intrínseco anterior. Não há migração integral para a mesma infraestrutura AST, funções como valores, callbacks, closures, variantes, pattern matching ou IO de arquivos/rede/FFI. A fronteira safe/unsafe, vidas de text e a licença/procedência continuam abertas.

## Próximo incremento

1. Representar tipos de função estruturados com parâmetros, retorno e efeito, com identidades canônicas. Distinguir função pura e função com efeitos no contrato de atribuição/chamada.
2. Implementar nomes de funções como valores, parâmetros/retornos/locais de tipos de função, chamadas indiretas e composição. Começar sem capturas/closures e manter ABI nativa e checks antes da emissão.
3. Integrar especializações genéricas ao tipo de função e proibir callback impuro onde se exige pureza. Validar aliases, shadowing, retornos, composição e chamadas transitivas em Windows/Linux, otimizado/sem otimização.
4. Acrescentar map/filter/fold tipados somente com contratos claros de alocação, propriedade dos elementos e efeitos. Não declarar coleções mutáveis ou text externo profundamente imutáveis.
5. Completar classes genéricas e migração de coleções; depois seguir fase 2 antes de promover generics com recursos proprietários. As aplicações A/B/C e fases de IO/serviços permanecem no plano.

## Operação

Raiz real: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Compilador: `src/assisc.c`; especialização: `src/generics.h`; coleções: `src/collections.h`; ownership local: `src/ownership.h`. O fluxo é `parse -> prepare_generics -> check -> check_ownership -> generate`.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`; Python disponível no runtime local em `C:/Users/babus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`; Node no PATH. Linux: Ubuntu via WSL, `make -B all`, GCC e Python3. `Makefile` acompanha o novo header. `ASSIS_BIN` seleciona candidato nas suítes evolution/generics/Node.

Testes que criam diretórios temporários e iniciam executáveis, e o acesso ao WSL, exigiram permissões ampliadas da ferramenta local nesta sessão. Isso é uma limitação do ambiente de execução, separada dos diagnósticos da linguagem. Logs locais ficam em `build/` e não integram os pacotes; resultados resumidos e medições são distribuídos em docs/benchmarks.

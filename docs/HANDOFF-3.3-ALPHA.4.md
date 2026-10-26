# Relatório e continuação — 3.3.0-alpha.4

**Continuação:** [HANDOFF-3.3-ALPHA.5.md](HANDOFF-3.3-ALPHA.5.md) registra coleções na especialização AST comum e inaugura a estimativa ponderada de conclusão. O texto abaixo preserva a entrega histórica da alpha.4.

Data: 25/10/2026, contexto local do usuário. Continuação autorizada do [plano](PLANO-EVOLUCAO-E-HANDOFF.md), após leitura do plano e dos handoffs alpha.1/2/3, inspeção do compilador, especialização AST, ownership, editor e distribuição. A alpha.3 foi preservada em `build/baseline-3.3-alpha.3`. Não há repositório Git neste workspace.

## Implementado

- Classes genéricas com até 16 parâmetros, especialização nominal por identidade e cache compartilhado com structs. As ASTs dos campos e métodos são substituídas estruturalmente; código do usuário não passa por substituição textual.
- Construtores, parâmetros/retornos, callbacks, locais, alocações e chamadas de funções genéricas dentro dos métodos recebem tipos concretos. Métodos seguem na fila transitiva existente antes de tipagem, privacidade, pureza, ownership e emissão.
- Bases estruturadas: classes genéricas podem herdar bases comuns ou aplicadas, e classes comuns podem herdar uma especialização. Assinaturas de sobrescritas, upcasts e despacho virtual conservam os contratos existentes. Structs e parâmetros de tipo isolados não são bases.
- Privacidade por classe concreta: um método de `C<int>` não recebe acesso privado a `C<bool>`. Membros herdados conservam a identidade da base; funções livres chamadas por métodos não recebem seus privilégios.
- Publicação antecipada de identidade permite tipos recursivos finitos. Ciclos de herança e expansão ilimitada por bases/campos/assinaturas/corpos de métodos são rejeitados, inclusive quando a expansão percorre a fila de trabalho.
- Editor resolve campos, métodos, construtores e bases com argumentos concretos, incluindo parâmetros reordenados na herança e tipos de callback. Snippet `genericaclasse`, gramática, manuais, exemplo `18_classes_genericas.assis`, Makefile e CI atualizados.
- Suíte portável `tests/test-generic-classes.py`, medições em `tools/benchmark-generic-classes.py` e integração na reconstrução limpa e na verificação de pacotes.

Contratos: [GENERICS.md](GENERICS.md). Evidência final: [VALIDACAO-3.3-ALPHA.4.md](VALIDACAO-3.3-ALPHA.4.md).

## Validação e entrega

Passaram 72 testes Node, 128 verificações nativas Windows, 133 Linux, 17 de módulos/instalação Linux e 41 casos PE, além dos corpora portáveis 3.1/3.2. A suíte nova tem 17 grupos/360 invocações por sistema. As reconstruções limpas repetiram evolution (12/472), generics (13/305), functions (19/383) e generic classes (17/360) e reproduziram os compiladores byte a byte na mesma toolchain. Os conjuntos têm sobreposição.

Pacotes: `dist/AssisScript-3.3.0-alpha.4-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.4.vsix`, com SHA256SUMS e verificação extraída em Windows/Linux. Medições de 1/8/32/64 classes contra equivalentes manuais, sete amostras por variante com/sem otimização, em `benchmarks/resultados/classes-alpha-{windows,linux}.{md,json}`. As saídas usam fórmula independente; a carga mede código/compilação/chamadas virtuais, não RAM ou aplicações reais.

## Análise e limites

A infraestrutura estruturada da alpha.2 suportou a extensão a classes sem alterar representação de valores, ABI, runtime ou convenção de chamadas. A emissão conserva o despacho virtual existente; especialização não acrescenta boxing obrigatório. Os corpos são verificados por instância concreta, e templates de classes não instanciados continuam sem validação completa. `check --library` não certifica todos os argumentos de tipo possíveis.

Classes são referências mutáveis ao heap com `new`/`free` legados. A especialização melhora reutilização e tipagem, mas não torna classes dados funcionais imutáveis. `own`/`borrow` de classes, destruição de campos e empréstimos em assinaturas continuam sem suporte. Métodos com parâmetros de tipo próprios continuam rejeitados. Não há novos métodos pure, closures, variantes, matching ou structs por valor.

A fase 1/F1 continua aberta: Array/HashMap ainda geram corpos pelo mecanismo intrínseco anterior, e map/filter/fold ainda usam propriedade e liberação legadas. O próximo bloqueio funcional é expressar propriedade/vidas entre funções; ampliar pure a objetos/text antes disso perderia as garantias atuais. As aplicações A/B/C, IO de arquivos/rede/FFI, fronteira safe/unsafe e licença/procedência continuam pendentes. A prontidão geral permanece experimental.

## Próximo incremento

1. Migrar os corpos de Array/HashMap para templates AST na infraestrutura comum, preservando marca interna confiável, privacidade, layouts, APIs, bounds e hashing. Medir tempo/tamanho e executar as regressões de coleções antes de retirar o gerador anterior. Não estender substituição textual a código arbitrário.
2. Especificar empréstimos compartilhados/mutáveis e consumo/retorno em assinaturas, relação de vidas e análise de fluxo da fase 2. Só então integrar coleções gerenciadas e map/filter/fold sem escape; classes não podem ganhar `own` apenas removendo a rejeição atual.
3. Definir layout/cópia/move e destruição antes de Result/Option, variantes e matching. Closures devem seguir o contrato de captura por valor/move/borrow.
4. Entregar a aplicação A com argumentos, arquivos, erros externos recuperáveis e recursos fechados em todos os caminhos; depois seguir as aplicações B/C. Nenhuma entrega local substitui a validação prolongada de serviços.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Arquivos centrais: `src/assisc.c`, `src/generics.h`, `vscode-assisscript/src/language.js`. Fluxo: `parse -> prepare_generics -> check -> check_ownership -> generate`. `src/ownership.h` não foi ampliado para vidas interprocedurais.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`. Python local: `C:/Users/babus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`; Node no PATH. Linux: Ubuntu via WSL, `make -B all`, GCC e Python3. `python tests/test-generic-classes.py`/`make test-generic-classes`; `ASSIS_BIN` seleciona candidato. `tools/validate-clean.py` executa agora quatro suítes em compiladores reconstruídos com runtimes regenerados.

Medições: `python tools/benchmark-generic-classes.py --output benchmarks/resultados/classes-alpha-windows.json` (Linux: sufixo linux). Pacotes: `tools/package-vscode.py`, `tools/package-release.py`, `tools/verify-release.py`. Os relatórios de benchmarks anteriores permanecem históricos, associados aos seus hashes; a verificação da alpha.4 confere os relatórios de classes contra os compiladores distribuídos.

Testes com temporários e processos exigiram execução autorizada com permissões ampliadas da ferramenta local; a tentativa inicial restrita falhou antes de invocar o compilador. Logs, baselines e temporários em build/ são locais e excluídos dos pacotes. A configuração de CI foi atualizada; não houve execução remota por ausência de repositório configurado.

# Relatório e continuação — 3.3.0-alpha.3

**Continuação:** [HANDOFF-3.3-ALPHA.4.md](HANDOFF-3.3-ALPHA.4.md) registra classes genéricas com herança e métodos especializados. O conteúdo abaixo preserva o estado histórico da alpha.3.

Data: 25/10/2026, no contexto local do usuário. Continuação do [plano de evolução](PLANO-EVOLUCAO-E-HANDOFF.md), após leitura dos três handoffs e inspeção do compilador, especialização, ownership, biblioteca, editor e distribuição. A alpha.2 foi preservada em `build/baseline-3.3-alpha.2`; não há repositório Git neste workspace.

## Implementação

- Tipo de função estruturado com parâmetros, retorno e efeito, igualdade estrutural e TypeId canônico. Substituição recursiva e cache de especialização distinguem os efeitos.
- Funções globais como valores, inclusive `nome::<Tipo>`, vínculos mutáveis/imutáveis, parâmetros, retornos, chamadas encadeadas e composição sem captura.
- Chamadas indiretas nativas em PE/ELF, mesma ABI interna, avaliação do callback uma vez antes dos argumentos, da esquerda para a direita, e diagnóstico de endereço nulo.
- Pureza conferida em atribuições, argumentos, retornos e chamadas. Função pure pode ser usada num contrato comum; o caminho inverso é rejeitado. Tipos internos de parâmetros/retorno permanecem invariantes.
- Templates pure não utilizados recebem verificação simbólica de efeitos com escopos, incluindo callbacks e nomes ocultados por variáveis locais. Cada instância ainda passa pela tipagem, pureza, privacidade e ownership concretos.
- `map<T,U>`, `filter<T>` e `fold<T,A>` na biblioteca algoritmos, para tipos escalares/funções pure. Contrato explícito de nova alocação em map/filter, preservação da entrada e liberação pelo chamador. APIs usam Array legado, sem empréstimos de own/borrow nas assinaturas.
- Editor lê tipos de função aninhados, parâmetros e retornos sem confundir os dois pontos internos; ajuda de assinatura de callbacks em variáveis/parâmetros, snippet e referência atualizados.
- Exemplo `17_funcoes.assis`, suíte portável `tests/test-functions.py`, benchmark de chamadas, CI, reconstrução limpa e verificação dos pacotes integrados.

Os contratos completos estão em [FUNCOES-E-EFEITOS.md](FUNCOES-E-EFEITOS.md). A validação e os hashes constam em [VALIDACAO-3.3-ALPHA.3.md](VALIDACAO-3.3-ALPHA.3.md).

## Validação e entrega

Passaram 71 testes Node, 128 verificações nativas Windows, 133 Linux, 16 de módulos Linux e 41 casos PE; corpora portáveis 3.1/3.2 também aprovados. As reconstruções sem cache repetiram evolution (12 grupos/472 invocações), generics (13/313) e functions (19/383) em cada sistema, reproduzindo os compiladores byte a byte na mesma toolchain. Os conjuntos têm sobreposição.

Pacotes: `dist/AssisScript-3.3.0-alpha.3-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.3.vsix`; verificação em Windows/Linux e SHA256SUMS atualizado. Medições de chamadas diretas/indiretas/ordem superior com sete amostras ficam em `benchmarks/resultados/funcoes-alpha-{windows,linux}.{md,json}`; saídas conferidas por fórmula independente. O benchmark mede custo de chamadas escalares e não caracteriza RAM ou aplicações reais.

## Limites e próximo incremento

O núcleo de ordem superior de F1 avançou. O gate integrado de fase 1/F1 continua aberto: classes genéricas e migração dos corpos das coleções para a infraestrutura AST ainda faltam; coleções de ordem superior usam contratos legados. Ownership permanece local, sem empréstimos nas assinaturas, recursos proprietários em campos ou retorno gerenciado. Não há closures/lambdas, variantes, pattern matching, structs por valor ou IO de arquivos/rede/FFI.

Pure permite int/byte/bool e funções pure, recursivamente. Não ampliar a text/objetos antes de resolver vidas e mutabilidade. Funções como valores não capturam ambientes e não estabelecem segurança geral para ponteiros brutos. Os benchmarks medem chamadas escalares; não medem RAM ou aplicações reais. A classificação de prontidão do plano permanece experimental.

1. Continuar fase 1 em incremento próprio: classes genéricas, substituição dos membros/métodos preservando identidade declaradora, herança e privacidade; ou migrar os corpos intrínsecos de coleções para AST, sem voltar à substituição textual para código do usuário.
2. Especificar e implementar empréstimos/vidas nas assinaturas e retornos na fase 2, antes de aceitar own/borrow nas APIs map/filter/fold ou recursos proprietários em campos.
3. Dados algébricos, Result/Option e matching exaustivo vêm com o contrato de layout/cópia/move; closures exigem análise das capturas. Não antecipar essas garantias por meio de ponteiros de função.
4. Concluir aplicação A com arquivos, argumentos e erros externos recuperáveis; seguir as demais fases e aplicações B/C. Licença/procedência e fronteira safe/unsafe continuam abertas.

## Operação

Raiz real: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Arquivos centrais: `src/assisc.c`, `src/generics.h`, `src/ownership.h`, `stdlib/algoritmos.assis` e `vscode-assisscript/src/language.js`. O fluxo permanece `parse -> prepare_generics -> check -> check_ownership -> generate`.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`. Python local: `C:/Users/babus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`; Node no PATH. Linux: Ubuntu via WSL, `make -B all`, GCC e Python3. Nova suíte: `python tests/test-functions.py`, ou `make test-functions`; ASSIS_BIN seleciona candidato. Rebuild limpo: `tools/validate-clean.py`, agora com as três suítes evolution/generics/functions.

Os testes com processos/temporários e o acesso ao WSL exigiram execução autorizada com permissões ampliadas nesta sessão. Tentativas restritas falharam antes da avaliação da linguagem; os registros de validação distinguem essa limitação de erros semânticos. Logs em build/ são locais e ficam fora dos pacotes. A configuração de CI foi atualizada, sem execução remota por ausência de repositório configurado.

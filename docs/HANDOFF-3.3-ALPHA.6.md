# Relatório e continuação — 3.3.0-alpha.6

**Continuação:** [alpha.7](HANDOFF-3.3-ALPHA.7.md) registra valores/variantes e IO nativo. O conteúdo abaixo preserva o estado histórico da alpha.6.

Data: 25/10/2026, contexto local do usuário. Continuação autorizada após leitura dos seis documentos fornecidos e inspeção do compilador, runtimes, coleções, editor e distribuição. Alpha.5 preservada em `build/baseline-3.3-alpha.5`. Não há repositório Git neste workspace.

## Estimativa de conclusão: 45%

São **44,5 pontos de 100**, arredondados para **45% do escopo do plano**, pela mesma [régua de 35 critérios](PROGRESSO.md). A alpha.5 permanece em 33,5 pontos/34% no histórico congelado. Esta entrega acrescenta 11 pontos, sem mudar pesos ou contar testes/documentação como funcionalidades.

| Critério | Antes → agora | Pontos novos |
| --- | --- | ---: |
| P0-SAFE | Pendente → parcial | 1,5 |
| P0-FLOW | Parcial → concluído para o modelo gerenciado suportado | 1,5 |
| P2-LOCAL | Parcial → concluído para o modelo gerenciado suportado | 2 |
| P2-LIFE | Pendente → concluído com vidas explícitas e conservadoras | 4 |
| P2-DROP | Pendente → parcial | 2 |

O percentual estima atendimento dos critérios, sem prazo ou prontidão para produção. P0-FLOW/P2-LOCAL avaliam o fluxo dos recursos que a linguagem admite como gerenciados; não afirmam segurança dos ponteiros legados nem suporte de todos os tipos de recurso. A ampliação de recursos/representação continua em P2-DROP/P2-VALUE/P3-TEXT. Não há crédito duplicado para F1.

## Implementado

- Parâmetros own/borrow/borrow mut; retornos own e borrow(origem)/borrow mut(origem). A origem deve ser parâmetro borrow compatível, e referências a locais não podem escapar.
- Contratos nos tipos de função, incluindo origem por índice no retorno. Chamadas diretas/indiretas, callbacks, generics e sobrescritas preservam identidade, modos e efeitos. Consumo exige move explícito ou alocação/retorno own.
- Empréstimos lexicais derivados, reempréstimos, suspensão de referências incompatíveis e empréstimos temporários entre argumentos. Avaliação da esquerda para a direita não permite mover/liberar o receptor ou um argumento ainda em uso.
- Reserva do endereço de atribuições durante a avaliação do lado direito; verificação também na condição dos laços. Estados de consumo são unidos pelos caminhos que continuam após return/break/continue.
- Campos own em structs, construção posicional consumidora, destruição recursiva inversa, movimento parcial, reinicialização e limpeza de structs parcialmente movidas. Campos transferidos são zerados; os helpers de destruição verificam a pilha.
- Bounds de buffers preservados por campos e retornos emprestados, em ambos os modos de emissão. Sem GC, contagem de referências, boxing ou mudança na ABI de ponteiros.
- Perfil opcional safe assis e tipos de função safe. Dentro dele, chamadas/operações legadas exigem unsafe explícito. --safe exige entrada safe; unsafe não desliga ownership, privacidade, pureza ou tipagem. Text externo e classes continuam fora do perfil verificado.
- map_own/filter_own/fold_borrow na biblioteca algoritmos, preservando as APIs antigas para migração. Exemplo 19 combina relatório composto, cálculo puro, retorno emprestado e extração de campo sem free manual.
- Parser de tipos/contratos, navegação, assinaturas e snippets do editor; gramática, referência, manuais, CI, testes, reconstrução e empacotamento integrados.

Contratos completos: [OWNERSHIP-FUNCOES.md](OWNERSHIP-FUNCOES.md). Evidência final e hashes: [VALIDACAO-3.3-ALPHA.6.md](VALIDACAO-3.3-ALPHA.6.md).

## Estado do plano

F1 passa a ter uma API gerenciada para coleções escalares/funções pure. A fase 2 inteira e F2 permanecem abertas. Structs continuam referências mutáveis ao heap; own não significa dado funcional imutável. Não há layout por valor, enums/variantes, Result/Option, matching, closures ou coleções persistentes.

P2-DROP é parcial: campos own de structs estão implementados, mas classes/Texto, coleções de proprietários e recursos externos não têm destruição gerenciada. P0-SAFE é parcial: o perfil é opcional e exclui text externo; o código legado conserva seu contrato manual. A análise bloqueia a raiz inteira de uma struct e proíbe consumir proprietários externos em laços, inclusive quando um raciocínio mais amplo poderia provar segurança.

Arquivos/argumentos e aplicação A, rede/FFI/persistência e aplicações B/C, validação prolongada, depuração, licença/procedência e suporte comercial continuam pendentes. A linguagem permanece experimental.

## Próximo incremento

1. Projetar destruição de classes/Texto, campos privados e herança sem duplicar dispose/free; definir recursos proprietários nas coleções. Não liberar own para classes só removendo a rejeição atual.
2. Definir layout/alinhamento e Copy/Move por valor antes de enums/Result/Option e matching exaustivo. Closures exigem contratos próprios para capturas e vidas.
3. Adotar bytes/text com comprimento e vida explícitos; depois ampliar o perfil safe e IO recuperável. Concluir aplicação A com arquivos/argumentos/caminhos Unicode, fechamento em todos os caminhos e memória limitada.
4. Usar as medições desta entrega para orientar custo de chamadas e drop; não remover verificações para obter um benchmark melhor. Prosseguir para B/C e testes prolongados nas fases correspondentes.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Fluxo: parse → especialização AST → tipos/pureza → ownership → safe → emissão. Principais fontes: `src/assisc.c`, `src/ownership.h`, `src/safety.h`, `src/generics.h`, `stdlib/algoritmos.assis` e `vscode-assisscript/src/language.js`.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`. Python local: `C:/Users/babus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Linux: Ubuntu via WSL, `make -B all`. Nova suíte: `python tests/test-ownership-functions.py`/`make test-ownership-functions`; ASSIS_BIN seleciona candidato. `tools/validate-clean.py` repete as seis suítes em compiladores com runtimes regenerados e exige reprodução byte a byte na mesma toolchain.

Medições: `python tools/benchmark-ownership.py --baseline COMPILADOR_ALPHA5 --output benchmarks/resultados/ownership-alpha-windows.json` (Linux: sufixo linux e `--iterations 2000000`). Sem --baseline mede referência manual atual versus own, sem afirmar comparação histórica; a CI usa esse modo e transporta os relatórios com os binários. Sete amostras locais incluem tempo de compilação, execução, bytes e pico de RAM por processo, com saída independente e checagem de alocações vivas em debug. A referência manual gera executáveis idênticos à alpha.5. O caso gerenciado acrescenta chamadas e apresentou custo de cerca de 19% no Linux otimizado; veja a investigação e os limites na validação.

Progresso: editar PROGRESSO.json, preservar os snapshots de versões anteriores e gerar/verificar com `tools/report-progress.py`. Pacotes: package-vscode.py, package-release.py e verify-release.py. A verificação confere os hashes dos compiladores contra as medições atuais; relatórios de versões anteriores são históricos.

Logs e baselines ficam em build/ e não integram os pacotes. Execução de subprocessos/temporários e WSL precisou das permissões locais correspondentes; a primeira tentativa restrita de evolution falhou antes de invocar o compilador. A CI foi atualizada localmente; não houve execução remota, pois não existe repositório configurado.

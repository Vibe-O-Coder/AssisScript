# Continuação — 3.3.0-alpha.13

Data: 26/10/2026, contexto do usuário. Base alpha.12 com alterações recebidas
sem commit sobre `257e719`; preservadas, sem reset, commit ou push automático.
Binários comparáveis e patch dos arquivos rastreados em `build/alpha12-baseline`.

## Entrega e análise da linguagem

- Closures safe com capturas explícitas val/own/borrow, assinatura estrutural
  distinta de fn, chamadas compartilhadas ou exclusivas com `closure mut`,
  destruição de ambientes, generics, campos, coleções próprias e retornos compostos.
- Capturas borrow mantêm a origem viva por empréstimo lexical; não podem escapar
  por move, retorno ou armazenamento em outro proprietário. Retornos
  `borrow(self)` mantêm o ambiente vivo. Val captura um snapshot Copy.
- Enums com payload own são recursos Move, com destruição somente da variante
  ativa. Match emprestado lê recursos; `match(move(dono))` transfere os payloads
  e libera o invólucro em todos os caminhos. Copy permanece inline e sem heap.
- Biblioteca: OwnedOption/OwnedResult, consulta e transformação de resultado own;
  `iterators::reduce_with` usa closures emprestadas sem coleções intermediárias.
- Editor/LSP, gramática, matrizes nativas, reconstrução limpa, CI, versão,
  catálogo, lockfile, instaladores e ZIP/VSIX sincronizados.

[Contrato e limites](CAPTURAS-E-VARIANTES-MOVE.md),
[exemplo](../exemplos/30_closures_and_owned_results.assis),
[validação](VALIDACAO-3.3-ALPHA.13.md).

O núcleo funcional agora combina valores Copy sem alocação, recursos afins,
variantes, funções globais pure e closures safe com ambientes explícitos. O custo
é visível: uma alocação por ambiente de closure ou invólucro de enum Move,
despacho indireto por chamada capturada e liberação determinística, sem GC.
Capturas compartilhadas retêm dados imutáveis para os pipelines. Isso amplia
aplicações nativas delimitadas; não transforma closures em callbacks ABI C,
nem o executável nativo em isolamento para conteúdo hostil.

## Progresso

**92% estimados (91,5/100 pontos)**, antes 89,5. Os 35 critérios e pesos
originais foram preservados. P2-ADT avança de parcial a concluído no contrato
documentado de variantes Move e capturas verificadas: +2 pontos. Enums Move
ficam no heap; closures são safe com efeitos explícitos, não pure; captura
borrow mut e vidas de closures emprestadas que escapam não foram implementadas.

**100% não foi atingido.** Restam 8,5 pontos: ensaio real de 24 horas,
emissão integral por IR, otimizações mais amplas, backend/novos alvos,
direitos de imagens/revisão de distribuição e aceite humano independente.
O [roteiro restante](RESTANTE-PARA-100.md) discrimina cada critério e sua prova.
Não atribuir crédito de 24 horas aos ensaios de 120 segundos ou reutilizar
CI remota de uma versão anterior.

## Operação e próxima continuação

`make test-alpha13`; Windows `tools/build-windows.ps1` e novas suítes Python.
`tools/test-native.py` executa as 29 suítes. `tools/validate-clean.py` regenera
os dois runtimes e compara o compilador produzido; nesta entrega foram
executadas as duas novas suítes sobre cada reconstrução limpa. Os 29 conjuntos
completos foram executados nos binários de bytes idênticos do workspace.

`tools/benchmark-alpha13.py` mantém as cargas comparáveis da alpha.12 e
acrescenta chamadas de closure, empréstimos e variantes próprias, com/sem
otimização. `tools/benchmark-optimization.py` mantém o gate adverso de hash.
`tools/audit-build.py --check` valida inventários por ligação real.
`tools/verify-release.py` executa os compiladores extraídos, bibliotecas,
aplicações e o exemplo novo e confere hashes/medições/rejeições.

Continuar pelo roteiro restante, com backend em incrementos comparáveis e
24 horas sobre árvore congelada. Obter os direitos dos assets e aceite por
pessoa distinta; não substituir esses atos por autorrevisão do agente.

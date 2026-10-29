# Continuação do backend: instruções escalares, condições e hosts ARM64

Data: 28/10/2026. Base: `aa96b83`, branch experimental `testing/alpha15`.
É uma revisão de desenvolvimento da alpha.15; a identidade de distribuição
permanece a mesma até uma preparação de versão separada. Não há novo release/tag.

## Emissão por IR

Declarações/atribuições de locais escalares e expressões descartadas elegíveis
agora têm instruções `store-local` e `eval`. A atribuição composta baixa a leitura,
operação tipada e escrita explicitamente; preserva a leitura do lado esquerdo
antes dos efeitos do lado direito. O emissor dessas instruções usa a identidade
resolvida do local e os valores tipados, sem consultar a expressão AST.

Condições escalares elegíveis também usam o grafo de valores: curto-circuito,
negação, comparações inteiras com sinal/largura corretos e teste de divisibilidade
por potência de dois. Ponto flutuante conserva o caminho IEEE da IR de expressões.
Otimizações não suprimem divisões por zero ou reordenam chamadas observáveis.

`assis ir` conserva HIR-v1 e ScalarIR-v1, acrescentando `opcode` às operações e
`local` às escritas escalares. O campo numérico `kind` anterior é preservado.
`value` em uma atribuição composta agora identifica o resultado completo, com
operandos anteriores ao consumidor, e não apenas seu lado direito.
As operações com `opcode: ast` continuam explicitamente na migração incremental.

As estruturas verificadas ainda dão ordem aos blocos, escopos e cleanups;
retornos, TCO, recursos, endereços, métodos, match e partes das condições com
recursos têm caminhos AST. O ponteiro de origem das operações serve também à
análise de liveness e aos diagnósticos. P5-IR permanece parcial, sem crédito novo.

## Hosts e destinos

O compilador C pode ser construído em Linux/macOS ARM64 para `check`, `ir` e
compilação cruzada dos três destinos x86_64. `doctor` explicita host/destinos;
`run` e `test` em ARM64 retornam diagnóstico A002 antes de executar. Não há
runtime ou geração de instruções ARM64 nesta revisão.

O Actions inclui Linux ARM64/QEMU e macOS ARM64/Rosetta. Em cada job, o compilador
executa nativamente e os programas gerados executam em emulação explicitamente
registrada. Os cabeçalhos de runtime x86_64 já embutidos são usados nos hosts
ARM64; sua regeneração a partir do assembler permanece nos jobs x64.
O job macOS Intel mantém regressões nativas e passa a guardar um relatório JSON.

A execução anterior `40753610676` aprovou Linux/Windows e falhou no build macOS
porque os macros POSIX escondiam `mkdtemp` no SDK Darwin. A revisão habilita
`_DARWIN_C_SOURCE` antes dos includes para expor a API declarada pelo sistema.
P5-TARGET continua pendente: emulação não encerra geração ARM64, instaladores e
depuração dos novos destinos.

## Validação

`tests/test-backend-evolution.py` passou de 10 para 16 regressões. Os casos novos
conferem instruções explícitas, todos os operadores relacionais em oito tipos
inteiros contra referência Python, extremos de módulo, efeitos/aliases,
arredondamento f32, NaN e cleanup em break/continue. Executam com/sem otimização.

`tools/test-portability.py` executa sete casos com/sem otimização, confere
ELF/PE/Mach-O x86_64, análise/IR e um programa rejeitado. Registra hashes,
arquitetura do host e modo de execução. O teste não chama esses resultados de
validação nativa ARM64 e falha se o modo/arquitetura esperados não coincidirem.

Resultados locais e remotos desta revisão devem ser associados ao commit e ao
SHA-256 do compilador. Relatórios alpha.15 e ensaios históricos de 24 horas
continuam associados aos seus próprios binários. A pontuação permanece 94/100.

Validação Windows desta continuação: 31 suítes / 289 testes nativos aprovados,
incluindo as 16 regressões de backend; 14 execuções do harness de portabilidade
aprovadas. A primeira passagem da suíte `net` apontou para uma pasta sem curl
e recebeu erro do carregador Windows; os oito casos passaram ao repetir com
a DLL já instalada no Git. O relatório inicial e o log da repetição foram
preservados separadamente em `build/review-tests/`.
SHA-256 do compilador candidato:
`29c866b18ab13c7e13179655a1e2c4b6665443f797b17f05fdcfb5517fd5c837`.

A primeira [execução remota desta revisão](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40794766601)
aprovou macOS Intel, Linux ARM64/QEMU e macOS ARM64/Rosetta. No Linux x64,
um teste de eventos pressupunha que um timer de 1 ms ainda estaria no futuro
quando outro callback agendasse um timer imediato. Essa ordem pode mudar em
qualquer host. O teste passou a criar a ação de parada antes da ação pendente
no mesmo callback e exige exatamente duas ações antes da parada; mantém
cancelamento, IDs, reentrância e retomada sem depender desse intervalo de 1 ms.
O runtime não foi alterado por essa correção. O resultado final deve ser
conferido nos checks do [PR #1](https://github.com/Vibe-O-Coder/AssisScript/pull/1).

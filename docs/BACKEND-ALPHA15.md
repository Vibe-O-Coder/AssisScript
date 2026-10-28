# Backend e análise da linguagem — alpha.15

## Escopo entregue

A alpha.15 retoma as fases 5/6 do plano a partir da árvore alpha.14 recebida.
Preserva a sintaxe canônica, ownership e a ABI. O backend permanece x86_64.

`expression_ir.h` traduz expressões escalares verificadas em valores tipados
independentes da AST: constantes como bits, locais resolvidos, operações unárias/
binárias, conversões e chamadas globais com argumentos e retorno escalares.
`expression_emit.h` emite esses valores para x86_64, preservando normalização
inteira, IEEE, ordem dos argumentos, curto-circuito e erros em execução.
Inlining limitado substitui identidades de parâmetros na IR, sem texto/AST.
`--no-opt` conserva o emissor AST como comparação executável; os testes também
usam fórmulas Python independentes, pois dois emissores podem compartilhar bugs.

`assis ir` mantém `AssisScript-HIR-v1` e acrescenta `valueFormat` com
`AssisScript-ScalarIR-v1`. IDs dos operandos precedem seus consumidores.
Operações e condições apontam o valor com `value`/`conditionValue`; -1 significa
que aquela expressão ainda depende do backend AST. Efeitos são conservadores,
não uma autorização para reordenar instruções. O formato é experimental.

## Registradores e intervalos

`registers.h` calcula conjuntos use/def e liveness até ponto fixo nos sucessores
do CFG, incluindo retornos, ramos, backedges, break/continue e bindings de match.
Constrói interferências para valores vivos e também escritas cujo resultado
morre; parâmetros coexistem na entrada e na substituição em cauda. Coloração
gulosa ponderada por frequência de laço reutiliza RBX/R12/R13/R14. R15 continua
reservado para o runtime. Os quatro registradores são preservados por chamadas.

Locais endereçados permanecem em memória: chamadas, métodos e aliases não podem
observar uma cópia obsoleta na pilha. Valores de ponto flutuante viajam como bits
na ABI interna e também podem ocupar esses registradores. Há limites de 256
candidatos, 4096 blocos e 8192 iterações; excesso usa o alocador por frequência
anterior. Não há spill/reload dinâmico nem garantia de coloração ótima.
Com `--symbols`, o mesmo fallback preserva registradores exclusivos por variável
lexical: o DWARF atual ainda não tem listas de localização por intervalo.

As provas de `ranges.h` cobrem `int` em:

- início constante não negativo, `i < len(a)-k`, incremento unitário;
- início `len(a)-k` com k >= 1, `i >= limite` não negativo, decremento unitário;
- acessos `a[i+d]`/`a[i-d]` somente quando ambos os extremos provam
  `0 <= índice < len(a)`, sem overflow modular;
- chamadas globais `pure` com contratos escalares já verificados.

O corpo não pode modificar índice/identidade da coleção, criar aliases brutos,
executar unsafe ou chamar código com efeitos que invalide a prova. Métodos
mutáveis, chamadas indiretas, strides diferentes e offsets não provados mantêm
checks. Arrays, buffers gerenciados e slices conservam o mesmo contrato.

## Análise e trabalho restante

O núcleo é útil para ferramentas nativas: monomorfização, dados Copy, recursos
afins e destruição determinística permitem composição sem GC obrigatório.
Closures e variantes Move já vieram da alpha.13; a alpha.14 resolveu atritos de
texto, construtores e coleções. Esta entrega melhora a separação e o custo do
backend, sem trocar o modelo da linguagem.

P5-OPT passa a concluído no contrato acima, +1 ponto pela régua original.
P5-IR permanece parcial: instruções, endereços/recursos, métodos e condições
otimizadas ainda têm caminhos AST; não há SSA nem backend integral por IR.
Próximo passo: baixar endereços, efeitos de memória e cleanups explicitamente,
depois migrar terminadores/emissão de instruções e só então estabilizar novos
alvos. Copiar ponteiros AST para uma nova estrutura não conclui essa etapa.

Outras lacunas mantidas: métodos genéricos próprios/interfaces, propagação `?`,
closures pure/borrow mut, Unicode por grafemas/normalização, concorrência segura
e isolamento de scripts. Não recebem crédito extra nem são requisitos inventados
para a pontuação atual. Mach-O permanece experimental; ARM64 não existe.

## Verificação e medições

`tests/test-backend-evolution.py` cobre IR, referência modular independente,
ordem/curto-circuito/traps, registradores em escopos/ramos/laços, parâmetros de
recursão em cauda, métodos/aliases, match/cleanup e limites/fallbacks.
Integra Makefile, matriz nativa, reconstrução limpa e CI; CI remota não é
presumida por execução local. `exemplos/32_backend_evolution.assis` demonstra
percursos e pode ser inspecionado com `assis ir`.

`tools/benchmark-backend.py` compara binários preservados da alpha.14 com a
candidata, intercala amostras, confere resultados por fórmulas independentes e
registra hashes, compilações, tamanhos e dispersão. Veja os resultados
[Windows](../benchmarks/resultados/backend-alpha15-windows.md) e
[Linux](../benchmarks/resultados/backend-alpha15-linux.md). As cargas incluem
início de processo e não provam desempenho geral. O gate adverso de hash e os
testes completos continuam obrigatórios.

Sem `--baseline`, o medidor compara a candidata com sua própria emissão AST
`--no-opt`, usada na CI quando o binário histórico não está disponível. O modo
e os hashes ficam explícitos no JSON; isso não vira comparação com alpha.14.

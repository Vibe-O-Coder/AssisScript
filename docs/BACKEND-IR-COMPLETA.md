# P5-IR — emissão integral pela IR tipada

Continuação de desenvolvimento a partir de `b7f9212`, em 28/10/2026.
A identidade de distribuição continua 3.3.0-alpha.15, identificada também pelo
commit e pelos hashes; esta etapa não cria uma versão estável.

## Fronteira entre frontend e emissão

O frontend resolve nomes/tipos, especializa generics, verifica ownership/efeitos,
prova intervalos e aloca os registradores. Depois, `backend_ir.h` baixa todas as
expressões e instruções verificadas para valores tipados e um CFG de emissão.

Antes da geração otimizada, o compilador limpa o conteúdo dos nós AST e remove
os corpos das funções da representação de frontend. As entradas dos emissores
AST também recusam execução no modo otimizado. `backend_emit.h` recebe somente
IR, tipos, layouts, identidades resolvidas e metadados de origem/depuração.
Isso vale em todos os builds otimizados, incluindo `--symbols`.

`--no-opt` mantém a árvore e o emissor anterior como referência executável
separada. Não é fallback automático para algum recurso da linguagem.

## Operações cobertas

- Endereços locais, campos, índices e desreferência; leituras e escritas tipadas.
- Provas/checks de limites, slices, texto/UTF-8, alocação e cópias de temporários.
- Chamadas diretas, virtuais, super, indiretas, closures e ABI C já resolvida.
- Construção de valores/objetos, variantes, coleções e ambientes de closures.
- Movimento com limpeza da origem, substituição own e destruição tipada.
- Retornos escalares/compostos, preservação do resultado durante cleanup e TCO.
- Ramos, laços, match e drops explícitos antes de return/break/continue.
- Intrínsecos de arquivos, argumentos, relógios, espera, IO, casts e assert.
- Escopos e variáveis de depuração independentes dos nós descartados.

O verificador confere identidades/ordem de operandos, endereços tipados,
despacho/argumentos, condições bool, sucessores e contratos de retorno.
Os operandos têm IDs anteriores aos consumidores; leituras de locais são
avaliadas no ponto de uso. Essa IR não é SSA e não autoriza reordenar efeitos.
O backend nativo continua x86_64; ARM64 permanece em P5-TARGET.

## Inspeção e compatibilidade

`assis ir` conserva HIR-v1 e ScalarIR-v1 para consumidores existentes. Acrescenta
`backendFormat: AssisScript-TypedIR-v1`, `backendValues`, `emission` e
`astFallbacks: 0`. A seção `emission` contém o CFG efetivamente consumido pelo
backend, com endereços, efeitos, drops e terminadores explícitos. A seção HIR
anterior permanece como visão de análise do frontend.

A ordem de layout dos blocos é separada de seus IDs. O seletor elimina saltos
para o bloco seguinte e preserva o resultado de retorno na pilha somente quando
há cleanup que possa sobrescrevê-lo. Provas de intervalos, liveness, inlining
escalar e contratos numéricos anteriores são preservados.

## Evidência

`tests/test-complete-ir.py` acrescenta sete regressões: representação tipada de
memória/recursos, drops antes das saídas, ordem de substituição own, função
indireta capturada antes dos argumentos, cópia de agregados antes de mutações,
laços contra referência Python e closures com retorno composto/símbolos.

A matriz completa agora tem 32 suítes, executadas em Windows e Linux. A
comparação usa `--no-opt`, referências Python independentes e o compilador
preservado antes desta mudança. O gate de GDB do Linux inclui parâmetros,
locais e escopos com shadowing. As reconstruções limpas regeneram os três
runtimes e comparam os bytes com o candidato selecionado por `--compare-binary`.

Os resultados exatos, hashes e caminhos de evidência estão em
[VALIDACAO-P5-IR.json](VALIDACAO-P5-IR.json). CI do incremento anterior está
aprovada; resultados remotos do P5-IR devem ser conferidos na revisão que o
publicar. P5-IR passa a concluído dentro deste contrato, +1 ponto.

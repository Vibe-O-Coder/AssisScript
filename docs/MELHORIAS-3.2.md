# Melhorias 3.2 e situação do relatório

Esta versão trata primeiro os gargalos observados no relatório de 24/10/2026 e introduz ownership/borrowing local. O relatório foi usado como referência técnica; suas medições em Linux não foram tratadas como medições desta máquina.

| Área | Implementado | Limite atual |
| --- | --- | --- |
| Alocação | Pools por tamanho, slabs de 64 KiB, zero ao reutilizar, debug de free/vazamentos | Slabs retidos; não é um alocador concorrente |
| Texto | Comprimento cacheado de variáveis locais e parâmetros; índices e `len` O(1) nesses valores otimizados | Campos e expressões temporárias usam o caminho legado; texto continua terminado por zero |
| Backend | Até quatro escalares frequentes em registradores preservados; comparações diretamente ligadas aos desvios; divisão/resto por potência de dois com sinal correto; outras divisões constantes sem testes redundantes | Sem IR, inlining, SIMD ou ABI de argumentos em registradores |
| Memória | `own`, `borrow`, `borrow mut`, `move`, limpeza de escopos, buffers gerenciados com limites | [Ownership local e restrições](MEMORIA-OWNERSHIP.md); não cobre o modelo completo de lifetimes entre funções |
| Conveniência | `div {}`, `for`, `defer free` | Sem `for x in colecao` |
| Entrada e tempo | `read_bytes`, `monotonic_ms`, `ler_linha` em std/texto | Sem arquivos, argumentos do programa ou relógio civil; ler_linha lê um byte por chamada |
| Texto padrão | `concatenar`, `juntar`, `dividir`, `substituir` | Retornam Texto proprietário; sem operador `+` de text |
| Robustez | Limite de pilha com diagnóstico; debug de memória | Sem sanitizador completo para ponteiros legados |
| Medição | C `-O2`, Python, anterior, otimizado e `--no-opt`, com saídas conferidas | Quatro cargas; início do processo incluído; não prova paridade geral com C/C++ |
| Editor e distribuição | Hover, cores, snippets, escopo do for e binários atualizados | Sem LSP independente |

Resultados reproduzíveis: [medições nativas](../benchmarks/resultados/nativo-3.2.md) e [dados brutos](../benchmarks/resultados/nativo-3.2.json).

## Texto e compatibilidade

O comprimento é calculado uma vez ao inicializar/atribuir um `text` local ou receber um parâmetro. Uma referência extra ao slot de comprimento ocupa oito bytes no quadro. `--no-opt` mantém a indexação legada para comparação. Tomar o endereço `&variavel_texto` desabilita o cache daquela variável, pois uma escrita indireta poderia alterar o ponteiro. Não há mudança na ABI pública de `text`: código antigo e `bytes(texto)` continuam usando ponteiros finos.

Textos são imutáveis. As visões retornadas por `text(buffer)`/`Texto.visualizacao()` só valem enquanto o armazenamento e conteúdo permanecerem válidos. Alterar/liberar o buffer invalida uma visão anterior; crie outra visão após a mutação. O primeiro byte zero ainda termina `text`; para binários use `*byte` e comprimento explícito. Não há alegação de indexação O(1) em todo campo ou valor temporário, nem de suporte a NUL interno.

## Entrada e relógio

`ler_bytes(buffer: *byte, capacidade: int): int` lê até a capacidade, com limite de 2.147.483.647 por chamada. Pode retornar leitura parcial; zero indica EOF e -1 erro do sistema. Não escreve terminador. Capacidade negativa é erro de execução. Para ponteiro legado, o chamador garante a capacidade real; para buffer gerenciado, ela é verificada. A entrada é em bytes; a codificação da console Windows depende de sua configuração, enquanto arquivos/pipes redirecionados preservam os bytes.

`agora(): int` retorna milissegundos monotônicos, ou -1 em erro. Use `fim - inicio` para medir tempo; não interprete como data Unix. Windows usa `GetTickCount64`; Linux usa `clock_gettime(CLOCK_MONOTONIC)`.

## Continuação do trabalho

Ainda precisam de projetos próprios: texto com comprimento explícito em toda a ABI, ownership entre funções e campos, structs por valor, arquivos/argumentos, float e larguras fixas, Result/Option genéricos, generics do usuário, namespaces, Set/fatias, eliminação de bounds comprovados, IR/inlining/ABI em registradores, ELF PIE/símbolos/DWARF, formatador/LSP e ARM/macOS. A distância para C/C++ depende da carga e deve ser medida a cada mudança; não existe garantia de equivalência de desempenho para toda a linguagem.

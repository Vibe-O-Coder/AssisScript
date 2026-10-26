# Otimização — alpha.10

Continuação do [relatório alpha.7](RELATORIO-OTIMIZACAO-AssisScript-3.3.0-alpha.7.md), lido integralmente junto aos handoffs até alpha.9. As medições históricas permanecem intactas. Os comparativos novos usam os binários alpha.9 do commit inicial `e88af38832c4ce7d42ab8a62b62f16c80970e7f9` e a versão atual, na mesma máquina.

## Mudanças

1. HashMap inteiro mistura os 64 bits com operações unsigned antes da máscara de capacidade. Chaves negativas/extremas, passos 1/64/4096/65536, tombstones, substituição e crescimento recebem testes independentes. O hash de texto conserva o algoritmo anterior; o finalizador inteiro é determinístico e não oferece proteção criptográfica contra chaves adversárias escolhidas.
2. Alocações grandes obtidas diretamente de `mmap`/`VirtualAlloc` aproveitam a garantia de memória zerada do sistema. Blocos reutilizados dos pools continuam zerados; debug continua preenchendo na liberação. Não foi acrescentado cache de grandes blocos: eles continuam devolvidos ao SO fora de debug, preservando a política de retenção.
3. Prólogos/epílogos salvam somente os registradores que a função utiliza. A verificação de pilha permanece em todas as funções e destrutores; nenhum ganho depende de removê-la.
4. A escolha dos quatro registradores preservados considera frequência sintática ponderada pela profundidade dos laços, com saturação do escore. Não é alocação global por intervalos de vida.
5. Imediatos cabíveis em 32 bits, LEA para multiplicações por 3/5/9, endereçamento escalonado para elementos de 1/2/4/8 bytes e deslocamento na divisão do comprimento de buffers por potências de dois reduzem instruções. Tamanhos compostos conservam o caminho geral. Cópias de registrador para ele mesmo são omitidas.
6. Funções globais `pure` com um único retorno de expressão escalar, no máximo quatro parâmetros e 16 nós podem ser expandidas quando os argumentos são nomes/literais. Divisão, deslocamentos, chamadas, heap e efeitos são excluídos desse caminho. A expansão é desativada com símbolos de depuração ou `--no-opt`. Funções pequenas com argumentos que produzem efeitos conservam a chamada e sua ordem de avaliação.
7. Uma prova conservadora identifica `for (let i:int=0; i<len(a); i+=1)` sobre buffer gerenciado, fatia ou Array cuja identidade permanece estável. Pode omitir os testes repetidos somente para `a[i]` no corpo. Chamadas, operações brutas, `unsafe`, novos recursos, movimento/liberação, alteração do índice ou da coleção invalidam a prova. A condição continua verificando o comprimento a cada iteração. Outras formas, inclusive `a[i+1]`, mantêm as verificações.

`assis ir` apresenta `provenBounds` por função para inspecionar a prova, também sem otimização; a emissão só a usa no modo otimizado. Verificações de tipos, pureza, privacidade, ownership e safe antecedem todas essas decisões.

## Medição e regressões

`tools/benchmark-optimization.py` confere saídas por fórmulas independentes, aquece, intercala candidato/baseline, mede compilação/tamanho e publica amostras brutas, medianas, versões e hashes. `--check` exige que os passos medidos permaneçam até cinco vezes o tempo das chaves sequenciais. A CI executa esse gate nos dois sistemas; ele não mede resistência criptográfica de hash.

Resultados: [Windows](../benchmarks/resultados/optimization-alpha10-windows.md), [Linux](../benchmarks/resultados/optimization-alpha10-linux.md). As execuções locais usam sete amostras, 20 mil entradas e cinco rodadas de leituras. O ensaio de alocação faz 300 alocações de 8 MiB, verifica zero e escreve nas extremidades; não é o caso de 3000 alocações do relatório original. O custo de início do processo está incluído. Os resultados não são diretamente comparáveis aos tempos absolutos do relatório em outra máquina.

`tests/test-optimization.py` verifica oráculos aritméticos com extremos e casos aleatórios determinísticos, capacidade/zeragem, colisões, preservação de efeitos e fallback diante de mutação, chamadas e `unsafe`. A suíte roda com/sem otimização, com debug de memória e geração dos dois formatos nativos.

A CI sem `--baseline` mede o compilador recém-construído e verifica o gate entre passos; os relatórios locais incluem a comparação histórica. A mistura de hash acrescenta custo no caso sequencial, que deve ser avaliado junto à remoção da degeneração nos passos grandes. Não interpretar os ganhos adversos como ganho universal do HashMap.

## Auditoria dos itens do relatório original

| Item | Situação atual |
| --- | --- |
| Mistura do hash inteiro | Corrigida e medida; hash textual/seed secreto continuam evolução |
| Zeragem de páginas novas | Corrigida; cache grande não implementado |
| Salvamento seletivo | Implementado; guarda de pilha preservada |
| Registradores, imediatos e endereços | Implementação limitada acima; sem alocação global ou peephole geral |
| Eliminação de bounds | Somente mediante a prova descrita; sem hoisting geral de ponteiros/tamanhos |
| Inlining | Folhas puras escalares; métodos/push/append_byte ainda chamados |
| ABI com argumentos em registradores | Pendente; conserva LVS1 |
| IR tipada | HIR de fluxo/efeitos existe; expressões/emissão ainda usam AST |
| Texto com comprimento em campos/retornos | `unicode::String` oferece API nova; `text` legado conserva seu custo |
| PIE/debug | Implementados na alpha.9; regressão repetida nesta entrega |
| Introsort/pdqsort | Pendente; `sort_ints` conserva heapsort |
| Gate contínuo de desempenho | Adicionado para hash por passo; sem limite geral contra C/Python |

P5-OPT continua parcial: as melhorias não equivalem a um otimizador global completo. A linguagem permanece experimental.

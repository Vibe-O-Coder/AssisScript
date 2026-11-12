# Memória em debug, temporários x64 e corpus de validação

11/11/2026, America/Fortaleza. Base publicada `5922558`, branch
`work/m3-confined-loader-2026-11-11`. Esta unidade responde à auditoria
do compilador nativo. Os níveis da régua ficam em 50,40% e 0/5 gates após
as duas unidades anteriores desta entrega.

## Runtime e emissão

O runtime x64 preenchia com veneno todo o bloco grande liberado em
`--debug` e mantinha a alocação mapeada. Isso tornava residentes até páginas
que a aplicação nunca tocou. Linux e macOS x64 agora desmapeiam o restante
do bloco mantendo o cabeçalho, e Windows x64 desconfirma essas páginas.
O backend ARM64 também libera a cauda e conserva um prefixo alinhado a
até 64 KiB. A reserva virtual no Windows e os cabeçalhos retidos continuam
crescendo com o número de liberações em debug. O runtime preserva os
diagnósticos de double free e de alocação viva ao sair.

Em 2.000 ciclos de 1 MiB, tocando cada página antes de liberar, o aumento
de memória residente foi de 7,81 MiB no Linux x64 e entre 7,82 e 7,85 MiB
no Windows x64. As duas medições por host usam modos otimizado e
`--no-opt` com `--debug`. Os diagnósticos de double free e vazamento
retornaram 70.

O compilador já alocava variáveis escalares por liveness no CFG.
O emissor x64 passa a reservar até quatro temporários para um operando
direito composto por aritmética inteira e sem efeitos. Divisão, shifts
dinâmicos, chamadas e árvores que excedem o limite conservam o caminho
de pilha. Multiplicações por potência de dois elegíveis usam shift.
O teste diferencial cobre valores extremos, profundidade acima do limite,
ordem de efeitos e equivalência com `--no-opt`. A alocação geral de
temporários de chamadas, vetores e valores vivos entre blocos permanece
na fila de otimização.

No segundo ensaio Linux, 11 amostras intercaladas deram mediana de
9,694 → 7,791 ms na expressão inteira aninhada. No mesmo ensaio, o stencil
passou de 309,655 para 323,889 ms. Os resultados das seis cargas e o
primeiro ensaio estão disponíveis por amostra.
[Comparação Linux](../ecossistema/evidencias/loader-http-2026-11-11/backend-linux-repeat.json).

## Corpus e distribuição

O caso 035 agora chama o método canônico `double`. A suíte de módulos
instala o compilador sob teste em um prefixo temporário junto à stdlib
da revisão. A validação de APIs inglesas compara o catálogo com os módulos
reais, verifica cada biblioteca e continua a rejeitar os nomes obsoletos.
O teste CLI da revisão publicada já usava a mensagem atual e passou com
o compilador reconstruído. Os três benchmarks legados usam `safe fn main`
e os recipientes gerenciados usam `own`. Os corpora portáteis são gerados
com Node e podem ser reexecutados em outro host com o compilador indicado
por `ASSIS_BIN`.

O `make test` em Linux aprovou 133 testes nativos e 28 de módulos.
O replay validou 22 verificações 3.1 e 73 casos 3.2. Os 71 exemplos
passaram na checagem dos dois hosts, com os dois finais do RPG executados.
Na matriz selecionada, Windows x64 registrou 98 métodos executados e
1 pulado. Linux x64 registrou 88 executados e 4 pulados. A nova fixture
de seleção após quebra de linha foi repetida nos dois hosts após ajuste
no empréstimo do teste. Os instaladores seletivos fecharam 29 bibliotecas
opcionais por host, executaram a demo instalada e removeram o compilador
preservando o arquivo pessoal do prefixo. No Windows também passaram
4 testes de locks e 40 testes Node com o instalador reconstruído.
O exemplo de saída Linux x64 gerou um ELF de 8.224 bytes, sem seção
dinâmica. O compilador também gerou PE Windows x64, ELF Linux ARM64 e
Mach-O macOS x64/ARM64. Windows e Linux x64 têm execução nativa nesta
unidade. A execução em Linux ARM64 e macOS segue pendente. Threads, atômicos,
assembly inline, `volatile`, layout C de agregados, casts entre ponteiros,
`sizeof`, bare metal, overhead de alocações pequenas e algoritmos de
sort/map continuam fora desta unidade.

[Resultados reproduzíveis](../ecossistema/evidencias/loader-http-2026-11-11/).

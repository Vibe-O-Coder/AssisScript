# Validação — 3.3.0-alpha.7

Data: 25/10/2026, contexto local do usuário. Fontes, diagnósticos, runtime, bibliotecas, editor e documentação foram verificados em Windows x64 e Ubuntu via WSL2. A alpha.6 foi preservada em build/baseline-3.3-alpha.6, com hashes. Não há Git configurado neste workspace; não houve execução remota de CI.

## Conclusão estimada: 56%

São **56 pontos de 100**, pela régua original de 35 critérios e pesos preservados. Alpha.6 continua congelada em 44,5 pontos/45%. Acréscimos: P2-VALUE +4; P2-ADT +2; P3-TEXT +1,5; P3-IO +3; P5-ABI +1. Critérios/evidências/limites estão em [PROGRESSO](PROGRESSO.md) e no [handoff](HANDOFF-3.3-ALPHA.7.md). **O alvo de 70–80% não foi atingido.** A métrica não mede prazo ou prontidão geral para produção.

## Matriz final repetida

| Conjunto | Resultado nesta entrega |
| --- | --- |
| Node: compilador/editor e regressões anteriores | 75 testes aprovados no Windows |
| Nativo Windows, instalação/reinstalação/remoção | 129 verificações aprovadas |
| Nativo Linux | 133 verificações aprovadas, incluindo o caso de 256 operações aritméticas |
| Módulos/instalação/remoção Linux | 21 verificações aprovadas |
| Harness PE com base relocada e ABI Microsoft | 41 casos aprovados; stubs KERNEL32/SHELL32; não substitui Windows real |
| Corpus portável 3.1 / 3.2 | 21 / 73 casos aprovados em Linux, regenerados/verificados por Node Windows |
| Evolution / generics | 12 grupos / 472 invocações; 13 / 305, por sistema |
| Functions / generic classes | 19 / 383; 17 / 360, por sistema |
| Collections AST / ownership functions | 10 / 143; 26 / 580, por sistema |
| Values | 21 grupos / 334 invocações, por sistema |
| Files | 10 grupos / 101 invocações, por sistema |
| Text bytes | 4 grupos / 32 invocações, por sistema |
| Aplicação A | 2 compilações e cenários válidos/adversos em ambos os modos por sistema |

Os conjuntos se sobrepõem e não devem ser somados como testes independentes. As dez suítes Python também passaram nos compiladores reconstruídos em diretórios limpos, sem bin/build/dist da base. Repetições adicionais foram motivadas por alterações concretas e falhas encontradas, não usadas como crédito de funcionalidades.

Valores: cópias independentes, payloads, layout de até 4096 bytes, profundidade e frame limitados, callbacks em campos/variantes, generics, retornos diretos/indiretos/virtuais, avaliação única/esquerda-direita, recursos nos braços, snapshots antes de efeitos posteriores, buffers/coleções e TCO. Os negativos rodam em check/build/run, nos dois modos, e também nos dois destinos; saídas sentinelas permanecem intactas.

IO: arquivos binários com NUL/255, leitura, escrita, append, EOF, caminho Unicode/emoji, argumentos com espaço/aspas/backslashes/vazio, falhas de abertura, índices, buffers e recursos fechados. Arquivos atravessam generics/callbacks e retornos emprestados. A limpeza automática preserva erro_io ao substituir campos e limpar parâmetros antes de retornar uma falha.

UTF-8 foi confrontado com o decoder estrito independente do Python, incluindo sequências limítrofes, aleatórias com seed fixa, overlong, surrogates, truncamento e NUL. A formatação decimal foi comparada com a representação independente, incluindo INT64_MIN.

A aplicação A processou 100 mil registros atravessando fronteiras de blocos em cada modo, com oráculo CSV/int independente. Testou números/cabeçalho inválidos, campos extras, NUL, CR, limites de linha, overflow, EOF, leitura de diretório, abertura/escrita sem permissão e preservação da saída anterior em erro de parse. Linux root executa o caso de permissão como nobody. O benchmark amplia para um milhão de registros. O dialeto é uma coluna numérica com cabeçalho literal valor, conforme [contrato](IO-E-APLICACAO-A.md); não é CSV/JSON geral.

## Auditoria de memória e correções durante a validação

O frontend C foi reconstruído com AddressSanitizer e UndefinedBehaviorSanitizer; as suítes finais values (21/334) e files (10/101) passaram com UBSAN halt_on_error e ASAN detect_leaks=0. O frontend conserva arenas/alocações de compilação até encerrar; essa execução não certifica vazamentos do compilador. Os programas gerados não são instrumentados por ASAN: usam bounds, checks de pilha/nulo e contador de alocações do runtime em debug.

Dois casos encontrados na revisão foram corrigidos e receberam regressões: own direto sobre Copy agora é rejeitado antes da emissão, impedindo liberar um endereço do frame como heap; destruição implícita de Arquivo preserva o erro da operação anterior. own/borrow/free/move sobre valores Copy, inclusive campos, são tratados separadamente dos recursos que os contêm. Não se ampliou own para classes/Texto por relaxamento de diagnósticos.

As listas antigas de instalação estavam incompletas para documentos recentes. O manifesto Windows agora é gerado dos arquivos reais e conferido com --check. Linux copia os JSONs atuais, marca a versão correta e registra os caminhos de instalações novas; a remoção dessas instalações preserva arquivos extras dentro de docs. Compatibilidade de remoção de marcadores antigos foi mantida. O fallback de instalações antigas sem manifesto conserva a política anterior de remover a árvore de dados da instalação.

## Ambiente e reconstrução

CPU reportada: Intel Core i7-6820HQ, 2,70 GHz. Windows: kernel 10.0.19045, MinGW GCC 15.2.0 (MSYS2 Rev13), Node 24.17.0, Python 3.12.14. Linux: WSL2 6.18.54.1, glibc 2.39, GCC 13.3.0. Flags de compilador: -O2, C11, avisos, link estático; Windows inclui -municode/-static-libgcc e timestamp do linker desativado. Versões do OS/CPU, amostras brutas e hashes também acompanham os JSONs de medição. Frequência/turbo, temperatura, antivírus e escalonamento WSL não foram controlados.

tools/validate-clean.py copiou apenas fontes/bibliotecas, removeu e regenerou ambos os headers do runtime, recompilou e repetiu dez suítes por destino. A reprodução é byte a byte na mesma toolchain, não uma promessa entre toolchains diferentes.

| Binário | SHA-256 final, igual ao build limpo |
| --- | --- |
| bin/assis.exe | `db5b8e8540c054d4b6851ba926766b7b87814242aba99336fea754762cb27c9a` |
| bin/assis | `7c242b968bf403c1f7738d91a61e0d6fd3d2268af05b36dc09d744f7468c377a` |

## Medições e investigação

Sete amostras intercaladas, dois milhões de iterações por variante, compilação/execução/tamanho/pico de RAM, saída conferida por N² e execução debug de cada fonte. A referência histórica usa o binário alpha.6 preservado. O custo de iniciar o processo é incluído e há um ensaio separado de início/print/saída. RAM é pico do processo, não uma medida de memória útil do programa ou prova geral de ausência de vazamentos.

Na implementação inicial, rep movsb para cópias pequenas e cópias repetidas para o próprio destino tornaram o caso Copy cerca de três/quatro vezes mais lento que heap. A correção usa words para até 64 bytes, evita cópia redundante de construções/chamadas e acessa campos escalares de valores locais sem copiar o agregado inteiro. Os snapshots entre argumentos, checks e invariantes foram preservados. Valores grandes continuam com cópia em bloco; o limite de frame usa contagem de slots sem criar um Var fictício por word. Medições iniciais ficaram em build/perf-inicial-alpha7; a tabela abaixo e os relatórios vinculados são do compilador final.

| Destino | Heap atual (ms) | Copy atual (ms) | Início alpha.6 / atual (ms) |
| --- | ---: | ---: | ---: |
| windows | 55.495 | 46.940 | 6.858 / 13.841 |
| linux | 49.422 | 42.245 | 0.489 / 0.484 |

O ganho vale para essa carga e muda a representação/alocação; não comprova superioridade geral com C/C++ ou em toda aplicação. Houve custo fixo adicional de aproximadamente 7 ms e 2,7 MB no Windows, observado também no programa de início/print/saída. A importação de SHELL32 e a preparação dos argumentos são novas; os dados são compatíveis com esse custo de inicialização, sem isolá-lo por perfil de cada API. É uma regressão registrada da base Windows; inicialização/importação sob demanda fica como trabalho posterior. No Linux, diferenças de heap/compilação variaram entre rodadas e mudaram de sinal, com amostras sobrepostas; não se declara ganho/regressão estável fora da carga Copy.

| Destino | Entrada menor / maior (bytes) | Pico menor / maior (bytes) | Mediana maior (ms) |
| --- | ---: | ---: | ---: |
| windows | 1100006 / 11000006 | 5545984 / 5554176 | 188.406 |
| linux | 1100006 / 11000006 | 270336 / 270336 | 168.001 |

A memória medida permaneceu semelhante para entradas de 1,1/11 MB; o fonte usa buffers fixos. RSS Linux tem resolução/contabilização do OS; não interpretar valores iguais como medição exata de todos os bytes. Os testes não simulam queda de energia, falha física de disco, serviço de 24 horas ou concorrência.

Relatórios completos: [Windows](../benchmarks/resultados/valores-io-alpha-windows.md), [JSON Windows](../benchmarks/resultados/valores-io-alpha-windows.json), [Linux](../benchmarks/resultados/valores-io-alpha-linux.md), [JSON Linux](../benchmarks/resultados/valores-io-alpha-linux.json). Medições de alphas anteriores foram preservadas com seus hashes originais.

## Distribuição e limites

Pacotes desta versão: dist/AssisScript-3.3.0-alpha.7-windows-linux.zip e dist/assisscript-3.3.0-alpha.7.vsix. Incluem ambos os compiladores, oito bibliotecas, editor, contratos, exemplos 20/21, testes/fontes no ZIP e a régua. SHA256SUMS acompanha o ZIP. A verificação confere os hashes dos compiladores contra as medições finais e a versão/porcentagem dos documentos.

Os pacotes extraídos passaram em Windows e Linux: bibliotecas, exemplos antigos/novos, negativos e aplicação A nativa compilada/executada a partir do pacote.

Classes/Texto gerenciados gerais, coleções de donos, variantes Move, capturas, text/slices com vidas gerais, números novos, namespaces/pacotes versionados, FFI C, rede, aplicações B/C e validação prolongada permanecem pendentes. Safe continua opcional e a aplicação A contém uma fronteira unsafe explícita para text C de argumentos. Não há isolamento de scripts hostis, licença escolhida pelo agente ou alegação de produto estável. A próxima instância deve continuar pelo handoff alpha.7 e preservar os estados históricos da métrica.

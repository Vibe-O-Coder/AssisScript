# Validação — 3.3.0-alpha.9

Data: 25/10/2026, contexto do usuário. **Conclusão estimada: 76% (75,5/100 pontos)** pela mesma régua de 35 critérios. Alvo de 90–100% não atingido. P2-DROP +2; P3-TEXT +1,5; P5-IR +1 (parcial); P5-DEBUG +1. Pesos e snapshots históricos preservados. [Handoff e auditoria de pendências](HANDOFF-3.3-ALPHA.9.md), [contratos](RECURSOS-E-FATIAS.md).

## Matriz efetivamente executada

| Conjunto | Resultado |
| --- | --- |
| Windows nativo e instalação/remoção isolada | 130 verificações aprovadas |
| Compilador/editor/LSP Node | 79 testes aprovados |
| Linux nativo | 133 verificações aprovadas |
| Módulos/instalação Linux | 24 verificações aprovadas |
| Harness PE32+ com base relocada | 41 casos aprovados; complementa Windows real |
| Corpus independente 3.1 no Linux | 22 verificações aprovadas |
| Corpus independente 3.2 no Linux | 73 casos aprovados |
| Rebuild limpo Windows/Linux | 18 suítes Python em cada sistema; compiladores idênticos byte a byte |

Os conjuntos se sobrepõem e não devem ser somados como cenários independentes. As duas expectativas antigas que rejeitavam classes own foram convertidas em casos positivos com o novo contrato; suas rejeições de uso incorreto permanecem e foram ampliadas.

| Suíte Python | Grupos por sistema |
| --- | ---: |
| test-evolution.py | 12 |
| test-generics.py | 13 |
| test-functions.py | 19 |
| test-generic-classes.py | 17 |
| test-collections-ast.py | 10 |
| test-ownership-functions.py | 26 |
| test-values.py | 21 |
| test-files.py | 10 |
| test-text-bytes.py | 4 |
| test-cli.py | 1 |
| test-numbers.py | 11 |
| test-packages.py | 12 |
| test-json.py | 4 |
| test-system.py | 8 |
| test-tooling.py | 5 |
| test-slices.py | 5 |
| test-managed-classes.py | 9 |
| test-backend-alpha9.py | 4 |

São 191 grupos por sistema: 191 executados no Linux, 190 mais um skip de GDB no Windows. O GDB correspondente foi executado no Linux. Suítes novas conferem check/build/run, ambos os modos de otimização, emissão PE/ELF e debug de alocações quando aplicável.

## Evidências novas

- Fatias: buffers e subfatias, vazio no fim, tamanhos estreitos/valores Copy, chamadas genéricas/indiretas e destino oculto de retorno. Criação/indexação fora dos limites terminam com diagnóstico; posições negativas e contagens enormes não provocam overflow permissivo. Escape de local, free com empréstimo ativo, compartilhado convertido em mutável, cópia por let e campos sem vida são rejeitados antes de executar código.
- Classes: construtores e receptores compartilhados/exclusivos; sobrescritas conservam contratos. Upcast/move para base usa drop dinâmico; aninhamento, substituição de campos, retorno antecipado, break/continue e elementos restantes da lista encerram sem vazamentos em debug. Lista transfere valores sem dupla destruição e conserva a vida de obter().
- Texto: UTF-8 estrito/NUL, cópia independente, falha recuperável preserva destino e recortes conservam comprimento/fronteiras. O teste adverso compara 270 entradas com o decoder UTF-8 estrito do Python, incluindo todos os 256 bytes isolados e limites de sequências multibyte. Herança de classes final, inclusive especializações e módulos, é rejeitada; não se pode substituir o construtor para contornar as invariantes do texto/lista.
- ELF: e_type=ET_DYN; nenhum segmento executável é gravável e a pilha não é executável. Três execuções exibiram endereços de função distintos com resultado igual, mantendo ASLR ativo. Endereços RIP e slots relativos dispensam loader externo e relocação de páginas de código.
- GDB: breakpoint por linha, backtrace com chamador, parâmetro n=40 e variável sombreada x=99, com/sem otimização. Escopos e localizações em registradores/frame são descritos; não há descrição fictícia de compostos, PDB ou ABI C.
- HIR: tipos, efeitos conservadores, blocos e sucessores válidos; instruções inacessíveis reduzem bytes de código. Tipagem/pureza/ownership/safe continuam verificando ramos que não executam. Não é SSA nem backend independente por IR; P5-IR recebe somente crédito parcial.
- Instalação: os dois sistemas executaram o exemplo 25 a partir da instalação real isolada, incluindo as bibliotecas opcionais novas. Reinstalação/remoção preservaram arquivos pessoais, sem alterar PATH/associações globais nos testes Windows.

## Reconstrução e hashes finais

Runtimes regenerados em árvore temporária sem bin/build/dist; GCC C11 com as flags documentadas, Windows sem timestamp inserido. Todas as 18 suítes foram repetidas usando o compilador reconstruído. A comparação é na mesma toolchain por sistema; não promete identidade entre toolchains diferentes.

| Arquivo | Bytes | SHA-256 |
| --- | ---: | --- |
| bin/assis.exe | 370688 | `8365fac951362a6da23903a0ad576051d5e7507a7244f956d9bcedbe11bb92b0` |
| bin/assis | 1083400 | `0f1f42b59cfdf66d6b92e6cc3bcd4d283a5004cb19dd429722b585c2acd1c7be` |
| bin/assis-setup.exe | 45056 | `d8f69b2a5c53f824473ac9a93143f8e803bf3f5b133456a5031b39acb191aee1` |

Logs: build/alpha9-{build,native,clean}-{windows,linux}.log, alpha9-node.log e logs portáveis. Baseline alpha.8 e hashes preservados em build/baseline-3.3-alpha.8; nenhum Git está configurado. Logs/baselines não integram os pacotes.

## Medições e investigação

[Windows](../benchmarks/resultados/evolucao-alpha9-windows.md) e [Linux](../benchmarks/resultados/evolucao-alpha9-linux.md), acompanhados dos JSONs com todas as amostras, fontes, hashes, opções, saída esperada e RAM. Sete amostras por variante com 2 milhões de iterações; CSV com 100 mil/1 milhão de linhas; fatias, UTF-8 e listas medidas separadamente, com saídas independentes e debug de alocações. Não há comparação histórica das APIs que não existiam na alpha.8.

Variações acima de 5% motivaram investigação com 21 amostras intercaladas, duas de aquecimento e 10 milhões de iterações. As amostras iniciais foram preservadas.

| Comparação longa alpha.8 → alpha.9 | Mediana de execução | Mediana de compilação |
| --- | ---: | ---: |
| windows, otimizado | +3.52% | -2.79% |
| windows, sem otimização | +3.43% | +19.64% |
| linux, otimizado | -2.51% | -7.36% |
| linux, sem otimização | +4.56% | -6.04% |

As medianas de execução longas ficaram dentro de 5%; há dispersão grande e início de processo incluído. A compilação Windows sem otimização apresentou +19,6% na mediana (18,59→22,24 ms), com intervalos sobrepostos e outliers de centenas de ms nas duas versões. A causa não foi isolada; a variação permanece aberta em P5-OPT. Não atribuir causalidade comprovada à HIR, não prometer ganho geral e não retirar verificações para melhorar números. RAM zero em processo curto significa observação indisponível, não ausência de consumo.

## Distribuição

Pacotes desta versão: dist/AssisScript-3.3.0-alpha.9-windows-linux.zip e dist/assisscript-3.3.0-alpha.9.vsix. Catálogo/instaladores com 16 bibliotecas; manifesto Windows sincronizado com 160 arquivos. Fontes de medição conferidas contra o workspace e verificadas também dentro do ZIP. SHA256SUMS é gerado com o pacote. Verificação dos pacotes extraídos **aprovada em Windows e Linux**: 16 bibliotecas e 579 hashes conferidos em cada sistema. Inclui execução do exemplo 25, CLI de arquivos, configuração persistente, pacote offline, demais exemplos e LSP onde Node está disponível. O lock do exemplo offline foi regenerado para a versão alpha.9; o verificador normaliza os separadores de caminhos Windows/Linux ao conferir os hashes dos fontes. ZIP/VSIX contêm os compiladores e relatórios finais desta entrega.

## Limites sem crédito adicional

Safe continua opcional; text C/Texto/CSV legados não recebem automaticamente as garantias da API nova. Não há variantes Move, capturas/closures verificadas, campos emprestados armazenáveis ou Array/HashMap de donos. A lista é limitada a 1024 nós e usa destruição recursiva com verificação de pilha. Novos recursos externos exigem adaptadores explícitos.

FFI C/callbacks externos, rede/DNS/TLS/HTTP, B/C completas, processos/IPC e 24 horas reais permanecem pendentes. Persistência é parcial e a fila é de uma thread. HIR é parcial, novos alvos ARM/macOS e ABI C não foram entregues. Licença/procedência/política comercial dependem do responsável e o aceite de instalação por terceiro não foi simulado. CI configurada localmente, sem execução remota por ausência de repositório. Não houve publicação externa, escolha de licença, ensaio de 24 horas ou declaração de prontidão geral para produção.

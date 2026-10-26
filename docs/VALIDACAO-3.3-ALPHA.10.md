# Validação — 3.3.0-alpha.10

Data: 26/10/2026; trabalho iniciado em 25/10/2026, contexto do usuário. **Conclusão estimada: 77% (76,5/100 pontos)** pela mesma régua de 35 critérios; o alvo de 90–100% não foi atingido. P6-POLICY avança de pendente a parcial (+1 ponto), com a escolha de licença, suporte e avisos. Pesos e snapshots anteriores foram preservados. [Progresso](PROGRESSO.md), [handoff](HANDOFF-3.3-ALPHA.10.md), [otimizações](OPTIMIZATION-ALPHA.10.md).

O commit inicial `e88af38832c4ce7d42ab8a62b62f16c80970e7f9` foi criado e enviado antes das alterações. Comparações de desempenho usam seus binários alpha.9. Relatórios históricos não foram reescritos para representar esta versão.

## Compiladores e reconstrução

As reconstruções limpas copiaram somente fontes, biblioteca e exemplos para uma árvore temporária, regeneraram ambos os runtimes e compilaram sem cache. Repetiram as 21 suítes Python e produziram os mesmos bytes dos compiladores locais. A versão passou a ser compartilhada entre compilador e instalador Windows por `src/version.h`; o catálogo mantém a mesma versão. Os blobs e fontes textuais usam LF determinístico.

| Sistema | Toolchain local | SHA-256 do compilador |
| --- | --- | --- |
| Windows x64 | GCC MSYS2 15.2.0 | `a68395b57e48a5b47424a2cabc5061bf9ac3292615a3523e085ac389916e843f` |
| Linux x86_64, Ubuntu/WSL | GCC 13.3.0 | `c167a9560ead07cf893ad7f56a298e21e004e8cbcfb0a5f61412fa37bf7e6a66` |

Os dois binários alpha.9 usados como baseline foram conferidos contra os bytes do commit inicial, por SHA-256. Não são reconstruções aproximadas de outra versão. A igualdade local do compilador não promete identidade de ZIPs ou de builds com outra toolchain.

## Testes executados

| Conjunto | Resultado local |
| --- | --- |
| Corpus nativo Windows | 130 verificações aprovadas |
| Corpus nativo Linux | 133 verificações aprovadas, incluindo 256 operações aritméticas |
| Módulos/instalação Linux | 25 verificações aprovadas |
| Harness PE32+ no Linux | 41 casos aprovados, com base relocada e ABI Microsoft |
| Node/editor/LSP/instalador | 81 testes aprovados no Windows, Node 24.17.0 |
| Python evolution até backend-alpha9, optimization, english-api, release-policy | 21 suítes aprovadas nas reconstruções limpas de cada sistema |
| Corpora portáveis recém-gerados pelo Node | 18 verificações 3.1 no Windows, 22 no Linux; 73 casos 3.2 em cada sistema |
| Pacotes extraídos | Windows e Linux aprovados: 16 bibliotecas, exemplos, configuração persistente, rejeições, ferramentas e 613 hashes |

Os conjuntos têm sobreposição e não devem ser somados como casos independentes. O teste GDB é executado no Linux e explicitamente ignorado no Windows. Node não está instalado no WSL local; por isso `make test-dev` local nesse ambiente não foi executado. Os corpora foram gerados no Windows e reproduzidos no Linux. A CI instala Node nos dois sistemas para testar também o editor/LSP no Linux.

As novas suítes verificam extremos e oráculos aritméticos, inlining/equivalência de efeitos, estabilidade da prova de bounds, mutação/calls/unsafe como fallback, zeragem nova/reutilizada, HashMap com passos/negativos/extremos/tombstones, sintaxe inglesa e compatibilidade de aliases, bibliotecas gerenciadas, READMEs executáveis e inclusão de licenças. Após a revisão de mensagens localizadas e comentários da stdlib, a suíte inglesa e a verificação dos pacotes conferem os fontes atuais.

Falhas encontradas e corrigidas: expectativas antigas de versão/diagnóstico/imports, corpora ignorados de versões anteriores, cabeçalho CSV com bytes antigos, marcador Linux contendo informação extra, caminho MSYS2 fixo na CI e reserva temporária Windows em duas operações. Esta última falhou em testes concorrentes; `CreateDirectoryW` agora reserva um nome exclusivo atomicamente. Falhas iniciais por permissão para criar temporários/iniciar executáveis foram repetidas com as permissões locais apropriadas.

## Medições

Sete amostras, aquecimento, alternância candidato/baseline e saídas conferidas por fórmulas independentes. Hash: 20 mil entradas e cinco rodadas de leitura. Alocação: 300 blocos de 8 MiB com verificação de zero e escrita nas extremidades. Tempos incluem início de processo e não são diretamente comparáveis aos absolutos do relatório alpha.7 em outra máquina.

| Carga | Windows alpha.9 → alpha.10 (ms) | Linux alpha.9 → alpha.10 (ms) |
| --- | ---: | ---: |
| Hash passo 1 | 20,511 → 22,924 | 7,758 → 11,832 |
| Hash passo 64 | 40,143 → 23,029 | 26,885 → 10,312 |
| Hash passo 4096 | 1052,660 → 23,153 | 1016,975 → 10,111 |
| Hash passo 65536 | 12327,735 → 23,357 | 12212,168 → 10,101 |
| Blocos grandes | 635,099 → 19,677 | 1689,771 → 5,784 |
| Folha pure, 10 milhões de chamadas | 52,033 → 34,050 | 40,754 → 16,866 |
| fib(35) | 120,625 → 104,603 | 114,641 → 128,535 |

A razão máxima dos passos 64/4096/65536 divididos pelo passo 1 foi 1,019× no Windows e 0,872× no Linux, abaixo do gate de 5×. **O caso sequencial ficou mais lento: +11,8% no Windows e +52,5% no Linux nas medianas observadas.** Não atribuir ganho universal ao HashMap; efeitos individuais das mudanças não foram isolados. O hash determinístico não demonstra proteção contra chaves escolhidas para colisão.

Dados completos: [Windows](../benchmarks/resultados/optimization-alpha10-windows.json), [Linux](../benchmarks/resultados/optimization-alpha10-linux.json), com ambiente, versões, hashes e amostras. Medições dos recursos atuais: [Windows](../benchmarks/resultados/evolucao-alpha10-windows.md), [Linux](../benchmarks/resultados/evolucao-alpha10-linux.md), sete amostras, dois milhões de iterações e CSV de 100 mil linhas. Incluem compilação, tamanho e pico de memória; zero no pico significa observação indisponível para processo curto. Os hashes de todos os fontes src/stdlib desses relatórios correspondem aos arquivos distribuídos.

## Distribuição e GitHub

Pacotes: `dist/AssisScript-3.3.0-alpha.10-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.10.vsix`. Os READMEs em inglês/português/espanhol, LICENSE, avisos de terceiros e documentação de migração estão no ZIP, VSIX e nos instaladores. O verificador executa também o exemplo 26, conferindo `2`, `4`, `6`, `3`; checa hashes dos compiladores contra as medições e hashes de fonte contra o pacote. As somas atuais estão em SHA256SUMS.

A [primeira execução remota](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40250923703) encontrou o manifesto antigo e um caminho fixo `C:/msys64` que não existia no runner Windows. O manifesto foi atualizado; a CI agora usa o caminho retornado por `msys2/setup-msys2`, com geração LF e gate de desempenho nos dois sistemas. As medições são transportadas junto dos binários correspondentes para o job de pacote. Consulte o [workflow](https://github.com/Vibe-O-Coder/AssisScript/actions/workflows/ci.yml) e o status do commit atual para a evidência remota, em vez de inferir sucesso somente pela configuração.

P0-CI permanece parcial enquanto o inventário completo dos componentes dos binários não for concluído. P6-POLICY também permanece parcial por direitos de imagens e revisão integral dos componentes. Os detalhes não confirmados não recebem crédito. Uma execução breve, teste automatizado ou pacote instalado em temporário não equivale a 24 horas nem a aceite independente.

Os logs locais ficam em `build/`, excluído da distribuição. FFI/rede/B/C, capturas/variantes Move, safe obrigatório/text externo, otimização global/IR integral, novos alvos e aceite por terceiro continuam abertos conforme o handoff. A entrega permanece experimental.

## Regressão adicional de caminhos Windows

A [execução 40258606887](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40258606887) aprovou todos os passos Linux, inclusive Node/LSP, reconstrução limpa e medições. O Windows compilou e passou 79 de 80 testes antes de revelar a classificação incorreta de caminhos abreviados. A correção posterior passou os 81 testes locais, incluindo a nova cobertura de comentários documentais com modificadores ingleses, e a regressão Windows de pacotes, que inclui lock determinístico entre grafias longa/curta, entrada não salva e overlay de dependência. A normalização fica restrita às comparações de pacote e não reescreve os caminhos exibidos nos diagnósticos. A comparação física que rejeita escapes por symlink/hardlink foi preservada.

## Dispersão e verificação adicional de Fibonacci

A mediana de fib(35) no Linux ficou pior nesta repetição, com amostras do candidato entre 94,225 e 220,156 ms. O ensaio adicional de fib(37), 21 amostras intercaladas, observou 227,105 ms no candidato e 255,452 ms na baseline. Esse ensaio maior não substitui os dados de fib(35), não isola causalidade e não autoriza ganho universal. A variação continua explícita em P5-OPT. O JSON Linux contém fonte, saída independente, hashes dos programas e todas as amostras adicionais.

As [medições locais versionadas](https://github.com/Vibe-O-Coder/AssisScript/blob/master/benchmarks/resultados/optimization-alpha10-linux.json) preservam a comparação e essa investigação. A CI produz medições novas do seu próprio binário, sem baseline nem investigação adicional; seus artefatos devem ser lidos com essa diferença de escopo.

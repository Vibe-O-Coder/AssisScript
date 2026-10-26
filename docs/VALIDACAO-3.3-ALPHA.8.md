# Validação — 3.3.0-alpha.8

Data: 25/10/2026. **Conclusão estimada: 70% (70/100 pontos)** pela régua original, com 14 pontos novos e estados históricos preservados. Critérios, contratos e pendências: [handoff](HANDOFF-3.3-ALPHA.8.md) e [progresso](PROGRESSO.md).

## Matriz executada

As 15 suítes Python passaram em Windows x64 e Ubuntu/WSL2: evolution, generics, functions, generic classes, collections AST, ownership functions, values, files, text bytes, aplicação A, numbers, packages, JSON, system e tooling. Os testes compilam/executam nos dois modos; negativos verificam rejeição antes de sobrescrever saídas. Tooling executa readelf/GDB no Linux e verifica breakpoint/backtrace por linha.

Passaram 78 testes Node de compilador/editor/LSP no Windows, 129 verificações nativas Windows, 133 nativas Linux, 22 de módulos/instalação Linux e 41 casos do harness PE em base relocada/ABI Microsoft. Esses conjuntos têm sobreposição, e não devem ser somados como casos independentes. Os corpora portáveis 3.1/3.2, regenerados pelo Node, passaram em 22/73 verificações no Linux. No teste de symlink do Windows houve um skip por falta de permissão para criar o link; o mesmo caso passou no Linux, inclusive com sanitizadores. A execução remota da CI continua indisponível por ausência de repositório configurado.

## Casos novos e auditoria

Números: oráculo inteiro independente, unsigned64, módulos de 8/16/32/64 bits, shifts, divisão, saturação, NaN/infinito/±0, subnormais, literais aleatórios por bits e reconstrução exata da impressão. Tipos atravessam buffers, registros, enums, generics, funções e coleções. Conversão inteira para f32 recebeu caso de empate que revelava arredondamento intermediário; agora usa conversão direta. Igualdade de agregados com reais é estrutural e compara somente o payload ativo.

Módulos/pacotes: nomes iguais, tipos genéricos, chamadas internas, callbacks, shadowing lexical, privados entre arquivos com mesmo namespace, versões exatas, transitividade, SHA-256 confrontado com hashlib, repetibilidade, alteração de dependência, overlay e escapes. A expansão inicial confundiu tipos de retorno de função com novas declarações; a suíte antiga de functions encontrou a regressão, e o scanner foi corrigido antes da entrega. O lockfile agora usa os bytes já carregados, evitando divergência por segunda leitura. Aliases de um arquivo dentro do mesmo pacote recebem hashes para todos os caminhos; hardlinks entre pacotes diferentes são rejeitados para preservar o contexto de importações relativas. O prefixo std e o fallback .pillow também passam pelo confinamento. O editor/LSP verifica submódulos no contexto da entrada e do lockfile do projeto, inclusive dependências transitivas.

JSON: dezenas de documentos, gramática/UTF-8 adversos, surrogate isolado/pareado, NUL, BOM, números extremos, orçamento de tokens, profundidade e offsets. Serialização foi decodificada independentemente pelo Python, incluindo todos os bytes ASCII de controle. Não se alega DOM ou parser incremental.

Sistema: ordem/cancelamento/reagendamento/reentrância/capacidade da fila, limite de ações e overflow de iterador; relógios civis comparados com o host e espera monotônica; stdout/stderr binários; filtros de log; criação exclusiva, sync, erro de handle e remoção. A configuração persistente foi reaberta por outro processo; parse inválido, arquivo grande, temporário existente e falha de rename preservam dados anteriores. Nenhum teste de queda de energia ou serviço de 24 horas foi executado.

Ferramentas: fmt idempotente com comentários, strings, emoji, CRLF e preservação em falha; teste nativo com recursos own e retornos void/int/bool; doc com genéricos, privados e vidas; mapas de ambos os destinos e DWARF/GDB real no Linux. O LSP foi exercitado pelo protocolo stdio com versões de documento, edição após emoji, diagnóstico/correção, navegação, hover, conclusão, símbolos, formatação e shutdown.

## Reconstrução, medições e pacotes

As reconstruções limpas copiaram apenas entradas de fonte, regeneraram ambos os runtimes sem bin/build/dist da base e repetiram as 15 suítes Python. As cinco novas somam 40 grupos: números 11, pacotes 12, JSON 4, sistema 8 e ferramentas 5; o skip Windows está descrito acima. Cada destino reproduziu seu compilador byte a byte com a mesma toolchain. Isso não promete identidade entre toolchains diferentes.

O frontend C também foi reconstruído com AddressSanitizer e UndefinedBehaviorSanitizer: números, pacotes, valores, JSON, sistema e ferramentas passaram com halt_on_error e detect_leaks=0. Arenas do frontend permanecem até o processo encerrar; não se certificam vazamentos do compilador. Programas gerados não são instrumentados pelo ASAN; testes usam bounds, checks de pilha/nulo e contadores de alocações do runtime em debug.

Uma reconstrução Linux inicialmente detectou relocação PLT pendente em uma chamada global do runtime; ela foi substituída pelo rótulo local correspondente. A regeneração ELF/COFF e a reconstrução limpa confirmaram a correção. As expectativas de versão e de diagnóstico de conversão foram atualizadas porque a conversão agora admite reais; o programa inválido continua rejeitado antes de gerar executável.

| Compilador | SHA-256 final, igual à reconstrução limpa |
| --- | --- |
| bin/assis.exe | `a581522d3a23bfcf0da4e786c152a96847adceadf3208ead9d9a348cede130c4` |
| bin/assis | `80c3403d1335d19ab0696addd9206ad4b37f70732abcbfc32dbf87e5584e54b9` |

Ambiente: Windows 10.0.19045, MinGW GCC 15.2.0 MSYS2 Rev13, Node 24.17.0, Python 3.12.14; Ubuntu/WSL2 6.18.54.1, glibc 2.39 e GCC 13.3.0. CPU Intel Core i7-6820HQ. Compiladores: -O2, C11, avisos e ligação estática; Windows usa -municode/-static-libgcc e timestamp do linker desativado. GDB/readelf foram usados no Linux. Não houve Node Linux disponível neste host: o protocolo LSP foi executado no Windows; a CI configurada prepara Node nos dois sistemas.

## Medições finais

Sete amostras intercaladas, dois milhões de iterações e saída N² independente, com referências alpha.7 preservadas. Novas cargas medem f64, u32, 20 mil validações JSON e 20 mil ações cooperativas, nos dois modos. Compilação, início de processo, execução, tamanho e pico de RAM são registrados; RAM é pico por processo, não memória útil ou prova geral de ausência de vazamentos.

| Destino | Heap alpha.7 / atual (ms) | Copy atual (ms) | CSV 1 milhão (ms) | Pico CSV menor / maior (bytes) |
| --- | ---: | ---: | ---: | ---: |
| windows | 56.895 / 56.589 | 45.765 | 173.311 | 5558272 / 5554176 |
| linux | 53.919 / 53.443 | 41.613 | 190.976 | 270336 / 270336 |

CSV usa entradas de 1,1/11 MB e buffers fixos. RSS igual no Linux reflete também a contabilização do OS; não é medição exata de cada byte. As comparações Copy/heap mudam representação/alocação e não demonstram superioridade geral com C/C++.

Uma rodada preliminar mostrou mediana Linux maior em cerca de 19% no caso heap. A investigação foi ampliada para onze pares alternados e 40 milhões de itens, separando version/check do compilador. Medições anteriores à correção de aliases foram preservadas em build/medicoes-alpha8-antes-hardlinks; as tabelas e JSONs vinculados aqui foram repetidos com os hashes finais.

| Investigação longa | Heap alpha.7 / atual (ms) | Diferença da mediana |
| --- | ---: | ---: |
| windows | 861.571 / 861.510 | -0.01% |
| linux | 923.079 / 916.276 | -0.74% |

No Linux, as instruções das funções do usuário são iguais após normalizar destinos de saltos/chamadas; o layout/endereço do código mudou. Isso não prova a causa dos tempos. Amostras variam e há sobreposição; frequência, turbo, temperatura, antivírus e escalonamento Windows/WSL não foram controlados. Não se anuncia ganho/regressão universal nem se retiram checks para melhorar medição. As amostras brutas e os custos novos permanecem publicados.

Relatórios: [Windows](../benchmarks/resultados/evolucao-alpha8-windows.md), [JSON Windows](../benchmarks/resultados/evolucao-alpha8-windows.json), [Linux](../benchmarks/resultados/evolucao-alpha8-linux.md), [JSON Linux](../benchmarks/resultados/evolucao-alpha8-linux.json), [investigação Windows](../benchmarks/resultados/investigacao-alpha8-windows.md), [investigação Linux](../benchmarks/resultados/investigacao-alpha8-linux.md).

## Distribuição e limites

Artefatos: dist/AssisScript-3.3.0-alpha.8-windows-linux.zip e dist/assisscript-3.3.0-alpha.8.vsix, com SHA256SUMS. Os instaladores usam o catálogo gerado de cinco bibliotecas obrigatórias/nove opcionais e incluem dependências opcionais, exemplos aninhados, LSP e documentos atuais. O ZIP inclui fontes, testes e ferramentas; baselines/logs locais ficam fora.

verify-release.py confere os hashes dos compiladores contra as medições finais, versão/progresso, docs, 14 bibliotecas e extração nativa nos dois sistemas. Inclui exemplos antigos, números, eventos, pacote offline, comando test, aplicação CSV e configuração JSON com persistência; o VSIX extraído também inicia seu LSP no Windows. A matriz de instalação/reinstalação/remoção preserva arquivos pessoais e inclui seleção de log com cli.

A verificação dos artefatos finais passou no Windows e no Linux: 14 bibliotecas e 559 hashes do ZIP conferidos, além da execução nativa do conteúdo extraído do VSIX. Os registros locais estão em build/verify-release-windows-alpha8.log e build/verify-release-linux-alpha8.log.

P2-DROP/P2-ADT/P3-TEXT continuam parciais. Faltam classes/Texto e coleções de proprietários gerais, variantes Move, capturas, slices/text com vidas gerais. FFI C, rede/TLS, processos/IPC, B/C completos, validação real de 24 horas, PIE/PDB/variáveis locais, licença e aceitação por terceiro continuam pendentes. JSON e formatação têm os limites dos contratos. Safe permanece opcional e não isola scripts hostis. O percentual de 70% não é uma certificação de produto estável.


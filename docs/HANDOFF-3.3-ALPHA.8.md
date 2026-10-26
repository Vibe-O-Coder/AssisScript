# Relatório e continuação — 3.3.0-alpha.8

**Continuação:** [alpha.9](HANDOFF-3.3-ALPHA.9.md) registra recursos/fatias e avanço para 76%. Este relatório preserva o estado histórico da alpha.8.

Data: 25/10/2026, contexto do usuário. Continuação após leitura do plano e dos sete handoffs fornecidos, inspeção dos fontes e preservação da alpha.7 em `build/baseline-3.3-alpha.7`. Não há Git neste workspace.

## Conclusão estimada: 70%

São **70 pontos de 100**, pela mesma régua de 35 critérios, sem alterar pesos ou estados históricos. Alpha.7 permanece em 56 pontos/56%. O alvo solicitado de 70–80% foi alcançado no limite inferior, sem contabilizar o navegador, HTDL ou busca.

| Critério | Alpha.7 → alpha.8 | Acréscimo |
| --- | --- | ---: |
| P3-NUM | Pendente → concluído | 3 |
| P3-LIB | Parcial → concluído no escopo CLI limitado | 1,5 |
| P3-PKG | Pendente → concluído para pacotes offline vendorizados | 3 |
| P4-EVENT | Pendente → concluído para fila cooperativa de uma thread | 3 |
| P4-STORE | Pendente → parcial | 1,5 |
| P5-DEBUG | Pendente → parcial | 1 |
| P6-TOOLS | Parcial → concluído | 1 |
| **Total novo** | | **14** |

O percentual mede atendimento do plano, não prazo ou prontidão geral para produção. Persistência e debug recebem somente crédito parcial: processos/IPC, serviço C, PIE e descrição de variáveis locais continuam faltando. Capturas, variantes Move e gerenciamento geral de classes/Texto não recebem crédito por iteradores ou callbacks sem captura.

## Implementado

- Inteiros i8/i16/i32/u16/u32/u64, aliases i64/u8 e reais f32/f64 nativos. Layout, buffers, campos, enums, chamadas diretas/indiretas, callbacks, generics e coleções; overflow modular, conversões explícitas/saturantes, IEEE/NaN/infinito/subnormais e impressão hexadecimal exata. Igualdade de valores compostos respeita os campos reais e o payload ativo. [Contrato](NUMEROS.md).
- Namespaces nominais, tipos/funções públicos ou privados ao módulo, nomes qualificados e resolução AST antes da especialização. Manifestos versionados, dependências transitivas locais, limites/ciclos, confinamento após resolver symlinks/junctions, lockfile SHA-256 determinístico e obrigatório em projetos com manifesto. Hash dos mesmos bytes carregados, inclusive overlays/BOM; nenhuma instalação/download implícito. [Contrato](PACOTES-E-NAMESPACES.md).
- Seis bibliotecas opcionais: cli, json, tempo, log, iteradores e eventos. JSON UTF-8 estrito com posição, profundidade e orçamento de tokens; serialização de strings preserva NUL e o destino em falha. IO trata escritas parciais e limites; pipelines imutáveis não alocam intermediários.
- Relógio civil separado do monotônico, espera nativa retomada após EINTR, saída binária em stdout/stderr. Fila limitada com callbacks safe, ordem por prazo/ID, cancelamento, reagendamento, parada, orçamento e rejeição de reentrância. [Contrato](EVENTOS-E-PERSISTENCIA.md).
- Arquivos com criação exclusiva, sincronização, remoção e substituição atômica no mesmo filesystem. Exemplo 24 valida configuração JSON, escreve temporário novo, sincroniza, fecha e substitui; testes incluem nova execução lendo o resultado e preservação do alvo em falhas. Não é a aplicação C completa.
- `fmt`, `test`, `doc`, LSP independente por stdio, integração do editor, mapas JSON e ELF com símbolos/DWARF v4. Breakpoint por linha e backtrace foram executados com GDB no Linux. [Ferramentas](FERRAMENTAS-ALPHA.8.md).
- Catálogo com 14 bibliotecas, dependências opcionais geradas para ambos os instaladores, seleção de log incluindo cli, exemplos/pacote offline/LSP integrados ao ZIP, VSIX e instalação. Reconstrução, CI local e verificação de distribuição incluem as suítes novas.

## Validação e distribuição

A [validação desta entrega](VALIDACAO-3.3-ALPHA.8.md) reúne os resultados, hashes finais, reconstrução limpa, medições e verificação dos pacotes. Logs/baselines permanecem em build, fora da distribuição. A CI foi atualizada localmente; não houve execução remota por ausência de repositório configurado.

## Limites e próxima etapa

1. Continuar destruição de classes/Texto e coleções de proprietários com contratos corretos de receptor/herança. Não habilitar own por simples remoção de rejeições. Depois variantes Move e propagação com limpeza/ABI preservadas.
2. Definir text/slices gerais com comprimento/vidas e capturas por valor/move/borrow. O novo lexer JSON usa spans de índices; não cria referências emprestadas armazenáveis. Iteradores atuais não são coleções persistentes nem closures.
3. FFI/ABI C, polling de descritores, rede/DNS/TLS/HTTP, processos/IPC e serviço C completo continuam abertos. A fila é síncrona, cooperativa e de uma thread. Não marcar validação de 24 horas com ensaio curto.
4. JSON ainda não tem DOM, consultas por chave, conversão decimal para float nem leitura incremental entre blocos. Texto C/CSV legado conservam seus contratos. Formatação decimal curta de reais, f64/f32 matemáticos mais amplos e Unicode/grafemas permanecem evolução de APIs.
5. Safe continua opcional, com fronteiras legadas explícitas; ELF continua ET_EXEC. Não há PDB ou variáveis DWARF. Licença/procedência e política comercial dependem do responsável. A linguagem permanece experimental, sem isolamento de scripts hostis.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`. Linux: `make -B all`. Runtimes: `tools/embed-runtime.py`, incluindo `runtime_numeric.inc` e `runtime_system.inc`; atualizar PE/harness junto. Novos headers: numeric, numeric_emit, namespaces, packages, sha256, devtools e debug_info.

Suítes novas: test-numbers.py, test-packages.py, test-json.py, test-system.py, test-tooling.py e test-lsp.js. `make test-alpha8` reúne as cinco Python; `make test-dev` inclui LSP. `ASSIS_BIN` seleciona candidato. `tools/validate-clean.py` reconstrói runtimes e compilador sem caches e repete as 15 suítes Python.

Benchmark: `tools/benchmark-alpha8.py --baseline COMPILADOR_ALPHA7 --output benchmarks/resultados/evolucao-alpha8-windows.json` (Linux: sufixo linux). Preserva relatórios anteriores; mede cargas antigas comparáveis e novas separadamente, com resultados independentes e RAM. Sem baseline, não afirma comparação histórica. A etiqueta de baseline foi parametrizada na ferramenta de valores/IO existente.

Progresso: editar PROGRESSO.json preservando os 35 estados de cada snapshot, gerar/verificar com report-progress.py. Instaladores: generate-install-manifest.py gera manifesto Windows, opcionais/dependências e catálogo shell. Antes de distribuir: gerar manifesto, compilar os dois destinos, reconstruir limpo, medir, empacotar VSIX/ZIP e verificar a extração nos dois sistemas. Não editar snapshots de baseline nem relatórios históricos para fazê-los parecer atuais.

# Relatório e continuação — 3.3.0-alpha.5

**Continuação:** [HANDOFF-3.3-ALPHA.6.md](HANDOFF-3.3-ALPHA.6.md) registra ownership entre funções e conclusão estimada de 45%. O conteúdo abaixo preserva a entrega histórica da alpha.5.

Data: 25/10/2026, contexto local do usuário. Continuação do desenvolvimento neste mesmo chat, autorizada pelo usuário. A alpha.4 foi preservada em `build/baseline-3.3-alpha.4`. Não há repositório Git no workspace.

## Estimativa de conclusão: 34%

São **33,5 pontos de 100**, arredondados para **34% do escopo atual do plano**. A [régua de progresso](PROGRESSO.md) possui 35 critérios ponderados nas fases 0–6; a [fonte auditável](PROGRESSO.json) registra estados e evidências. Pela mesma régua, a alpha.4 corresponde retrospectivamente a 31% (30,5 pontos). O avanço desta entrega é P1-COL: corpos de Array/HashMap na infraestrutura AST comum, mais três pontos.

O número estima atendimento do plano, não tempo restante, data, horas de trabalho ou prontidão para produção. O escopo inclui F0–F4 e aplicações A/B/C, sem duplicar crédito entre trilhas. Não inclui construir navegador, HTDL, estilos ou busca. Pesos e crédito parcial são convenções de engenharia explícitas, revisáveis se o escopo mudar. A partir desta entrega, **cada novo handoff e relatório de validação deve apresentar a porcentagem, o critério avançado e as pendências**.

## Implementado

- Array/HashMap usam a rotina comum de especialização AST de classes em `src/generics.h`. Tipos são substituídos por identidade em campos, parâmetros, retornos, locais e corpos dos métodos; a fila concreta segue para tipos/privacidade/pureza/ownership/emissão.
- Templates internos são analisados uma vez por compilação que usa coleções. Não há substituição textual, fonte concreto gerado por combinação nem serialização de tipos de volta para código.
- Hash de texto e hash de inteiro têm corpos AST previamente analisados, selecionados pelo tipo da chave. Algoritmos de hashing/sondagem, tombstones e crescimento permanecem os mesmos.
- Cache de coleções conserva TypeRef/DefId e a classe nominal concreta desde a publicação inicial. O limite de 256 combinações de coleções continua separado das 256 instâncias do usuário. Implementação interna não consome o orçamento de expansão do usuário.
- Privacidade por owner concreto, origem interna confiável, layouts, vtables, API, bounds, limpeza e semântica de memória preservados. Nomes/caminhos parecidos com os internos não concedem privilégio.
- Tipos de função extensos conservam a estrutura completa sem depender do buffer de exibição ou de reanálise de texto. Testes incluem assinatura de mil parâmetros, efeitos distintos e callbacks em valores de HashMap/Array.
- Nova suíte portável `tests/test-collections-ast.py`, comparação com a alpha.4 em `tools/benchmark-collections-ast.py`, integração em Makefile/CI/reconstrução limpa/pacotes, documentação e régua de progresso gerada e verificável.

Contratos: [GENERICS.md](GENERICS.md). Evidência: [VALIDACAO-3.3-ALPHA.5.md](VALIDACAO-3.3-ALPHA.5.md).

## Validação e entrega

Passaram 72 testes Node, 128 verificações nativas Windows, 133 Linux, 18 de módulos/instalação Linux, 41 casos PE e os corpora portáveis 3.1/3.2. A suíte nova tem dez grupos/143 invocações por sistema. As reconstruções limpas repetiram as cinco suítes Python e reproduziram os compiladores byte a byte na mesma toolchain. Os conjuntos têm sobreposição.

Na carga otimizada de 64 tipos nominais, a mediana de compilação caiu de 174,158 para 118,906 ms no Windows e de 163,273 para 112,418 ms no Linux, cerca de 31% em cada sistema. Todos os pares de executáveis medidos são idênticos byte a byte com/sem otimização. Isso não mede RAM nem estabelece ganho geral de runtime. JSONs e fontes em `benchmarks/resultados/colecoes-ast-alpha-{windows,linux}.{md,json}`.

Distribuição: `dist/AssisScript-3.3.0-alpha.5-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.5.vsix`, com verificação extraída nos dois sistemas. O progresso acompanha ambos os pacotes e tem coerência de versão/porcentagem conferida. Relatórios anteriores e seus benchmarks permanecem históricos.

## Estado do plano e próximo incremento

Os mecanismos de tipos/especialização previstos na fase 1 estão implementados. Isso não fecha o gate integrado F1: map/filter/fold ainda usam Array legado com liberação explícita, sem empréstimos nas assinaturas. Classes continuam referências mutáveis e rejeitam own/borrow; pure permanece restrito a escalares e funções pure. A migração interna não cria garantias novas de vida ou imutabilidade profunda.

O próximo trabalho é a fase 2: especificar contratos de consumo, empréstimo compartilhado/mutável e relações de vida em parâmetros/retornos; implementar análise de fluxo antes de permitir que referências gerenciadas atravessem essas interfaces. Depois, campos proprietários/destruição, layout por valor e variantes/Result/Option/matching. Capturas de closures exigem o mesmo contrato de vidas. Métodos com parâmetros genéricos próprios e constraints continuam fora do escopo entregue.

Arquivos/argumentos e aplicação A, rede/FFI/persistência e aplicações B/C, validação prolongada, safe/unsafe obrigatório e licença/procedência continuam abertos. A linguagem permanece experimental. Não aumentar a porcentagem por apenas adicionar testes, documentação ou repetir validação sem avançar um critério da régua.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Fontes centrais: `src/collections.h`, `src/generics.h`, `src/assisc.c`. Fluxo: `parse -> prepare_generics/prepare_collections -> check -> check_ownership -> generate`. O runtime, os emissores e a análise interprocedural de ownership não foram alterados.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`; Python local em `C:/Users/babus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`; Node no PATH. Linux: Ubuntu via WSL, `make -B all`, GCC e Python3. Suíte nova: `python tests/test-collections-ast.py`/`make test-collections-ast`; ASSIS_BIN seleciona candidato. `tools/validate-clean.py` executa agora cinco suítes contra compiladores com runtimes regenerados.

Progresso: editar `docs/PROGRESSO.json`, gerar com `python tools/report-progress.py` e verificar com `--check`. Preservar a régua ao comparar versões; o histórico de cada versão congela seus 35 estados em overrides, para atualizações futuras não alterarem as avaliações anteriores. O gerador exige esse snapshot completo. Gerar/publicar o relatório somente com evidências existentes.

Comparação: `python tools/benchmark-collections-ast.py --baseline CAMINHO_DO_COMPILADOR_ALPHA4 --output benchmarks/resultados/colecoes-ast-alpha-windows.json` (Linux: sufixo linux). A referência pode ser extraída do pacote alpha.4; não depender do baseline local para uma distribuição limpa. Pacotes: `tools/package-vscode.py`, `tools/package-release.py`, `tools/verify-release.py`. Relatórios antigos permanecem associados aos respectivos hashes de compilador.

Logs e baselines ficam em build/ e não integram os pacotes. A CI foi atualizada sem execução remota, por ausência de repositório configurado. Execução com temporários/processos e acesso ao WSL usam as permissões locais necessárias; resultados de ambiente e resultados da linguagem são registrados separadamente.

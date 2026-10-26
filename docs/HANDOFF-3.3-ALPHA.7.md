# Relatório e continuação — 3.3.0-alpha.7

**Continuação:** [alpha.8](HANDOFF-3.3-ALPHA.8.md) registra o avanço a 70%. O conteúdo abaixo preserva o estado histórico da alpha.7.

Data: 25/10/2026, contexto do usuário. Continuação após leitura dos sete documentos fornecidos. Base preservada em `build/baseline-3.3-alpha.6`, incluindo hashes. Não há repositório Git neste workspace. Consultar a [validação](VALIDACAO-3.3-ALPHA.7.md) para resultados finais, hashes e medições.

## Conclusão estimada: 56%

São **56 pontos de 100**, pela mesma [régua de 35 critérios](PROGRESSO.md). A alpha.6 permanece congelada em 44,5 pontos/45%. Pesos, método e escopo não foram alterados. O alvo solicitado de 70–80% **não foi atingido** por esta entrega; não converter lacunas em crédito para alcançar um número.

| Critério | Alpha.6 → alpha.7 | Acréscimo |
| --- | --- | ---: |
| P2-VALUE | Pendente → concluído para os tipos Copy/Move suportados | 4 |
| P2-ADT | Pendente → parcial | 2 |
| P3-TEXT | Pendente → parcial | 1,5 |
| P3-IO | Pendente → concluído no dialeto validado da aplicação A | 3 |
| P5-ABI | Pendente → parcial | 1 |
| **Total novo** | | **11,5** |

P2-VALUE especifica Copy inline e Move dos recursos existentes, sem admitir campos Move inline. P2-ADT permanece parcial porque não há capturas verificadas/closures ou variantes proprietárias. P3-TEXT é parcial: buffers têm comprimento verificável e APIs UTF-8, mas text geral conserva representação C. P5-ABI é parcial: ABI interna/retornos/adaptadores existentes estão documentados e testados; FFI C pública não foi entregue. TCO, testes adicionais e correções de instalação não recebem crédito duplicado.

## Implementado

- `value struct` imutável, Copy sem alocação, layout/alinhamento recursivo e limites explícitos. Referências `struct`/`ASSIS` anteriores permanecem. Campos Copy inline também funcionam dentro de objetos legados e gerenciados.
- Enums genéricos, construção de variantes, match exaustivo, vínculos imutáveis, fluxo de recursos nos braços e pureza simbólica/concreta. Option/Result e auxiliares de transformação na biblioteca erros.
- Retornos/argumentos compostos por cópia em funções diretas, indiretas e virtuais. Snapshots preservam avaliação da esquerda para a direita. Array/HashMap e buffers admitem elementos Copy; igualdade usa representação canônica.
- Recursão direta em cauda em funções pure reutiliza o frame, inclusive com valores compostos. Sem otimização preserva chamadas e diagnóstico de pilha.
- Arquivo opaco own/borrow, abertura anulável, leitura/escrita em blocos, erros recuperáveis e fechamento automático em todos os desvios normais. Recursos compõem campos own de structs.
- Argumentos do processo, caminhos Unicode no Windows, conversão UTF-8/UTF-16 estrita e importação separada de KERNEL32/SHELL32. Harness PE atualizado junto com os dois runtimes e blobs.
- `len` de buffers gerenciados em elementos, UTF-8 estrito com comprimento explícito e formatação decimal sem alocação. NUL binário permanece dado válido nos buffers.
- Aplicação A real em AssisScript: CLI de CSV numérico com argumentos, processamento em blocos fixos, saída persistente, validação e códigos de erro. Não depende de helper para executar sua função.
- Editor, gramática, referência, snippets, exemplos, CI, reconstrução limpa e verificação de pacotes integrados. Manifesto gerado do instalador Windows corrige listas antigas; instalador Linux copia os JSONs/documentos atuais e registra caminhos para preservar extras na remoção de instalações novas.

Contratos: [valores/variantes](VALORES-E-VARIANTES.md), [IO e aplicação A](IO-E-APLICACAO-A.md), [ABI](ABI-NATIVA.md).

## Limites e próximos passos

As fases 2–6 não estão completas. Classes/Texto e coleções de donos ainda não têm gerenciamento geral; não habilitar own nessas classes apenas relaxando diagnósticos. Não há variantes Move, text/slices gerais com vida e comprimento, closures/capturas, iteradores persistentes, floats/larguras numéricas novas, namespaces/lockfile, FFI C, rede/TLS, serviços B/C ou validação de 24 horas. Não houve decisão de licença/procedência do responsável nem execução remota de CI. A linguagem permanece experimental; a aplicação A cobre o dialeto descrito no contrato, sem JSON ou CSV geral.

1. Completar destruição de classes/Texto e coleções de proprietários com empréstimos de receptor e despacho de destruição corretos. Projetar variantes Move e propagação preservando o destino oculto da ABI e a limpeza de cada caminho.
2. Ampliar dados com comprimento/vidas para text e slices, depois capturas por valor/move/borrow e iteradores. Não transformar ponteiros temporários usados pelo backend em referências públicas.
3. Acrescentar diretórios, persistência atômica e JSON limitado; evoluir a aplicação A além do dialeto mínimo. IO atual é síncrono e não é uma fronteira de permissões para scripts hostis.
4. Só depois avançar integração C/eventos/rede e aplicações B/C com falhas simuladas e 24 horas reais. Não marcar o ensaio prolongado como concluído com uma execução curta.
5. Manter os snapshots históricos da régua e os relatórios de benchmarks das alphas anteriores. Novos critérios só avançam com implementação e evidência próprias.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`; Linux: `make -B all`. Regerar blobs ao alterar assembly: `tools/embed-runtime.py` com binutils configurado. Runtimes novos compartilham `src/runtime_files.inc`. Contratos e layout estão em `src/assisc.c`, especialização em `src/generics.h`, recursos em `src/ownership.h` e perfil em `src/safety.h`.

Suítes novas: `test-values.py`, `test-files.py`, `test-text-bytes.py`, `test-cli.py`. Todas integram Makefile, CI e `tools/validate-clean.py`. `ASSIS_BIN` seleciona candidato; o gerador de manifesto é `tools/generate-install-manifest.py`, com `--check`. `tools/report-progress.py --check` confere a régua. Antes de distribuir, gerar manifesto, compilar ambos os sistemas, medir, reconstruir limpo e executar `package-vscode.py`, `package-release.py`, `verify-release.py` nos dois destinos.

Medição atual: `tools/benchmark-values-io.py --baseline CAMINHO_ALPHA6 --output benchmarks/resultados/valores-io-alpha-windows.json` (Linux: sufixo linux). Sem baseline compara referências heap/Copy do compilador atual; não afirma comparação histórica. O ensaio alterna variantes, confere N² independentemente, mede compilação/execução/tamanho/RAM e executa a CLI com entradas de dois tamanhos. Logs/baselines ficam em build e não integram os pacotes.

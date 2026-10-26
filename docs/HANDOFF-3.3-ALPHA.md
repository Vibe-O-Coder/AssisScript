# Relatório e continuação — 3.3.0-alpha.1

**Continuação disponível:** [HANDOFF-3.3-ALPHA.2.md](HANDOFF-3.3-ALPHA.2.md) registra o incremento seguinte de funções/structs genéricas. O conteúdo abaixo preserva o relatório histórico da alpha.1.

Data: 24/10/2026. A execução do plano foi iniciada; a direção de programação funcional foi incorporada. O plano completo não está concluído. O incremento 3.3.0-alpha.1 está implementado, validado e empacotado; os resultados estão em [VALIDACAO-3.3-ALPHA.md](VALIDACAO-3.3-ALPHA.md). O ponto de passagem é F0 funcional e a correção B01; não uma declaração de conclusão das fases 0–6.

## Implementado

- Privacidade nominal de campos/métodos, inicializadores e construção posicional; rejeição de sobrescrita privada.
- B01: todos os campos de Array/HashMap e os auxiliares do mapa são privados, inclusive diante de aliases, borrow e ponteiros tipados.
- Confiança de fontes gerados por marca interna, sem conceder privilégio por caminho `<colecoes>`.
- Buffers de Texto e proprietários internos de CSV privados; ler_linha usa métodos; ler_csv delega ao método analisar da classe.
- `val` local e `pure assis` escalar, composição, recursão, parâmetros imutáveis e rejeição transitiva de efeitos antes da emissão.
- Gramática, documentação, exemplo funcional, editor, snippets, instaladores, configuração de CI e suíte portável de regressões.
- Remoção Linux reconhece versões antigas e alpha sem aceitar marcador de outro produto; arquivos pessoais são preservados nos testes.
- Builds limpos regeneram runtimes com tamanho canônico em ELF/COFF, removem timestamp do linker Windows e reproduzem os compiladores byte a byte na mesma toolchain.

## Entregas e evidência

Pacotes: `dist/AssisScript-3.3.0-alpha.1-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.1.vsix`. Ambos incluem documentação, exemplo funcional, bibliotecas e compiladores dos dois sistemas. SHA256SUMS foi regenerado. A verificação dos pacotes extraídos passou em Windows e Linux.

Foram aprovados 69 testes Node, 128 verificações nativas Windows, 133 Linux, 14 de módulos Linux, 41 casos do harness PE, 21 verificações portáveis 3.1 e 73 casos portáveis 3.2. A nova suíte tem 12 grupos/472 invocações por sistema e foi repetida em builds sem cache. Há sobreposição entre conjuntos.

Os benchmarks funcionais registram sete amostras e confrontam saídas com fórmula independente. Neste caso, o programa otimizado pure/val e as versões legadas atual/3.2 são idênticos byte a byte; os tempos variam e não comprovam ganho da anotação. Os relatórios não medem RAM, generics, closures ou aplicação real. Logs e hashes de reconstrução ficam em build/; a síntese e os hashes dos compiladores estão na documentação distribuída.

## Próxima implementação

1. Ler o plano atualizado e os contratos; verificar os hashes e repetir a validação local. Não usar o antigo ZIP 3.2 como compilador de referência funcional.
2. Introduzir DefId/TypeId, tipos aplicados/variáveis e tipos de função com efeitos. O Type atual em assisc.c ainda contém kind/depth/name; não implementar generics do usuário por substituição textual.
3. Guardar templates de função/struct como AST com posições, substituir tipos por identidade, criar cache/fila de especialização e limites de expansão. Começar pelos testes de identidade<int/byte/bool> e Caixa<int/text> descritos na fase 1.
4. Rodar tipagem, pureza e ownership sobre cada instância concreta. Preservar privacidade por identidade declaradora ao clonar AST; não permitir que um template externo ganhe acesso a privados.
5. Implementar funções como valores e composição, efeitos nos callbacks e map/filter/fold após os tipos estruturados. Rejeitar callback com efeitos onde se exige pureza.
6. Avançar vidas em assinaturas/retornos, campos proprietários, destruição, structs por valor, variantes e matching. Só então ampliar pure a text/objetos/closures e coleções funcionais.
7. Concluir a aplicação A com arquivos, argumentos e erros recuperáveis; depois fases 4–6 e aplicações B/C. O teste prolongado de 24 horas e o navegador seguro permanecem fora do escopo concluído.

## Limitações e gates abertos

A fase 0 foi avançada, mas o gate integral de segurança não está encerrado: não há modo safe/unsafe obrigatório nem prova geral de vidas de text. A análise de ownership segue local. Licença e direitos das imagens dependem do responsável; ver inventário. A configuração de CI foi adicionada localmente, sem execução remota, pois não existe repositório Git configurado neste workspace.

F0 funcional escalar foi entregue; F1–F4 continuam pendentes. Não há funções como valores, generics do usuário, closures, pattern matching, dados persistentes, TCO, arquivos/rede/FFI ou prontidão geral de produção. Os novos recursos não alteram runtime/layout/ABI e não transformam referências legadas em dados imutáveis.

## Operação

Raiz: `C:\Users\babus\Desktop\AssisScript\AssisScript`. Cópia original: `build/baseline-2026-10-24`, com src/stdlib/bin/docs/tests/tools/editor e hashes. Sem Git; não pressupor commits recuperáveis. A cópia de baseline é local e excluída do ZIP.

Windows: MinGW em `C:\msys64\ucrt64\bin`; tools/build-windows.ps1 ajusta o PATH do processo. Node 24.17.0 disponível. Python desta sessão: `C:\Users\babus\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Linux: Ubuntu via WSL, gcc/python3 disponíveis; Node não estava instalado, usar os corpora portáveis gerados no Windows.

Testes novos: `python tests/test-evolution.py`, 12 grupos e 472 invocações por sistema. A variável ASSIS_BIN permite testar candidato. Makefile oferece test-evolution. Benchmarks do incremento: tools/benchmark-evolution.py. Pacotes são gerados por tools/package-vscode.py e tools/package-release.py e precisam passar tools/verify-release.py nos dois sistemas.

Arquivos centrais alterados: src/assisc.c (privacidade, val/pure), src/collections.h, stdlib/texto.assis, stdlib/csv.assis, src/windows_setup.c, scripts de instalação/remoção e geração, Makefile e vscode-assisscript/. src/ownership.h permanece com a análise local anterior, sem nova análise interprocedural. A configuração .github/workflows/ci.yml deve acompanhar a raiz real do projeto ao criar um repositório.

O próximo gate útil é F1/fase 1: tipos estruturados e especialização com efeitos, seguido por funções como valores. Implementar isso sobre o Type atual apenas por nomes ou anunciar que a adição de pure já concluiu o paradigma funcional perderia os contratos estabelecidos nesta entrega. As fases de IO, ownership completo e serviços exigem novas implementações e ciclos de validação próprios.

Comandos WSL e testes que iniciam subprocessos exigiram execução com permissões ampliadas da ferramenta local; as tentativas restritas retornaram acesso negado/EPERM, e as execuções autorizadas funcionaram. Isso não foi falha de semântica do compilador.

Houve uma interrupção transitória da revisão automática de aprovação por limite de uso da conta. Após o usuário solicitar continuação, a mesma ação foi submetida novamente e executada; não há bloqueio de execução pendente nesta entrega.

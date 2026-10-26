# Validação experimental — 3.3.0-alpha.1

Data: 24/10/2026. A base 3.2 passou nos 68 testes Node existentes antes das alterações. Cópia e hashes em build/baseline-2026-10-24.

A suíte nova de encapsulamento e pureza passou nos compiladores candidatos Windows/Linux: 12 grupos e 472 invocações em cada sistema. Verifica todos os membros internos, aliases, ponteiros tipados, empréstimos, métodos privados, subclasses, construtores, spoofing por stdin, composição/recursão pura, imutabilidade, efeitos em código não chamado, diagnósticos de módulos, limites e preservação do binário anterior após erro.

## Resultados finais desta entrega

| Conjunto executado | Resultado |
| --- | --- |
| Node: compilador, bibliotecas e provedores do editor | 69 testes aprovados no Windows |
| tests/test-windows.ps1 | 128 verificações nativas aprovadas |
| tests/test.sh | 133 verificações Linux aprovadas |
| tests/test-modules.sh | 14 verificações Linux aprovadas, incluindo marcadores de remoção antigos/atual/inválido |
| tests/test-pe.sh | 41 casos PE com relocação e ABI Microsoft aprovados no harness Linux |
| tests/test-evolution.py | 12 grupos, 472 invocações por sistema; também repetidos nas reconstruções limpas |
| tests/test-v31-portable.py | 21 verificações Linux aprovadas, incluindo perfis de instalação |
| tests/test-v32-portable.py | 73 casos gerados no Windows repetidos com sucesso no Linux |
| tools/validate-clean.py | Windows e Linux aprovados, regenerando runtimes e reproduzindo os hashes dos compiladores |
| tools/verify-release.py | VSIX extraído e ZIP verificados em Windows e Linux; 8 bibliotecas e 433 hashes |

Esses conjuntos se sobrepõem e não devem ser somados como testes independentes. Resultados históricos 3.2 permanecem em VALIDACAO.md. O Ubuntu foi executado via WSL2; não houve uma nova sessão visual do VS Code nem execução remota da configuração de CI. Não houve teste prolongado de serviço ou implementação das aplicações A/B/C.

Os testes de pacote conferiram versão, igualdade dos binários empacotados, CRC/hashes, as oito bibliotecas, execução de exemplos de relatório, ownership e programação funcional e rejeição de acesso privado, efeito impuro e reatribuição de val. As instalações e remoções foram exercitadas em destinos temporários.

## Reconstrução e hashes

Windows: GCC 15.2.0 MinGW/MSYS2; Node 24.17.0; Python fornecido pelo runtime local. Linux: GCC/CPython do Ubuntu. A reconstrução limpa copia somente src/stdlib e a ferramenta de geração, descarta os dois blobs na cópia temporária, regenera, compila e executa a suíte nova. Ela exige igualdade byte a byte com o compilador do workspace para a mesma plataforma e toolchain.

| Compilador | SHA-256 reproduzido |
| --- | --- |
| bin/assis.exe | cb7aeb9608d933c2eba4b03cd1ace70a828a537fcb488906df6042e2ef53df49 |
| bin/assis | 61f5cc8e6a9d69c09bfd3c1dabcb279efa48b219e9c4bbf823cbffec4ebdb573 |

O gerador Python usa símbolo de fim para excluir padding do COFF. A construção Windows usa --no-insert-timestamp. Essas correções eliminaram diferenças encontradas na verificação; não significam reprodução entre versões diferentes de GCC/binutils. O alocador, os contratos de layout e as instruções dos runtimes não foram alterados neste incremento.

## Desempenho delimitado

[Windows](../benchmarks/resultados/funcional-alpha-windows.md) e [Linux](../benchmarks/resultados/funcional-alpha-linux.md) registram sete amostras intercaladas de dez milhões de chamadas, uma compilação observada por variante, tamanho e hashes. Os JSON adjacentes contêm as amostras e o ambiente. A saída foi conferida pela fórmula independente 3*N*(N-1)/2+7*N.

Nos dois sistemas, a variante legada 3.2, a legada atual e a versão pure/val otimizada geraram executáveis idênticos byte a byte nesse programa. No Linux houve diferença de medianas acima de 5% entre esses mesmos bytes: a inspeção dos hashes identifica variação de execução, não uma alteração no código emitido pela anotação. Não se atribui ganho ou regressão de runtime a pure/val com base nesses tempos. A amostra única de compilação não sustenta comparação de velocidade do compilador. RAM, closures, generics e aplicações completas não foram medidos.

## Reproduzir

```powershell
tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe
tests/test-windows.ps1
python tests/test-evolution.py
python tools/validate-clean.py --cc C:/msys64/ucrt64/bin/gcc.exe --binutils-dir C:/msys64/ucrt64/bin
node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js tests/test-v32.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js
```

```sh
make -B all
make test test-pe test-evolution
python3 tools/validate-clean.py
python3 tools/package-vscode.py
python3 tools/package-release.py
python3 tools/verify-release.py
```

Os pacotes exigem os dois compiladores já construídos. A configuração de CI combina os artefatos nativos de cada sistema antes de empacotar. A geração dos corpora portáveis segue VALIDACAO.md. As medições funcionais podem ser repetidas com tools/benchmark-evolution.py; --baseline aponta para uma cópia preservada da 3.2.

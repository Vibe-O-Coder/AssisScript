# Validação atual: 3.3.0-alpha.2

Veja [VALIDACAO-3.3-ALPHA.2.md](VALIDACAO-3.3-ALPHA.2.md) para os resultados da entrega atual e [HANDOFF-3.3-ALPHA.2.md](HANDOFF-3.3-ALPHA.2.md) para continuar o plano. A validação da alpha.1 permanece em [VALIDACAO-3.3-ALPHA.md](VALIDACAO-3.3-ALPHA.md). O conteúdo abaixo é histórico da 3.2/3.1.

# Validação do AssisScript 3.2.0

Executada em 24/10/2026, em Windows x64 e Ubuntu x86_64 via WSL2. Compiladores nativos e instalador reconstruídos a partir dos fontes.

| Verificação | Resultado |
| --- | --- |
| Suíte Node de compilador, biblioteca e editor | 68 testes aprovados no Windows |
| tests/test-windows.ps1 | 128 verificações nativas aprovadas |
| tests/test.sh | 133 verificações Linux aprovadas |
| tests/test-modules.sh | 10 verificações Linux aprovadas |
| tests/test-pe.sh | 41 casos PE32+ com base relocada e ABI Microsoft aprovados |
| tests/test-v32-portable.py | 73 casos gerados e validados no Windows, repetidos com sucesso no Linux |
| Benchmark C/Python/AssisScript | 4 cargas, 5 variantes, 5 amostras após aquecimento; saídas idênticas |

Os 17 grupos de testes 3.2 cobrem ownership e conflitos de empréstimo, proibição de fuga e uso após move, limpeza em return/break/continue, defer com buffers e classes legadas, limites de buffers gerenciados, todas as classes do alocador, várias slabs, blocos grandes, zero ao reutilizar, vazamentos, free duplo, recursão extrema, milhares de comparações de divisão/resto contra BigInt, preservação de registradores e aliases, texto UTF-8, entrada binária com NUL e 0xFF, EOF, linhas sucessivas e relógio monotônico. Os casos executáveis são verificados com e sem otimização.

O teste de instalação foi repetido com perfis completo, mínimo e seletivo em destinos temporários, preservando PATH e associações pessoais. A integração do editor foi validada nos testes dos provedores; não foi aberta uma sessão real do VS Code nesta etapa. As execuções de VS Code real descritas no histórico abaixo pertencem à entrega 3.1.

Os [resultados atuais](../benchmarks/resultados/nativo-3.2.md) incluem ambiente, CPU, compiladores, amostras e limites de interpretação. Aritmética e texto ficaram próximos de C nesta medição; Collatz e alocação ainda levam cerca de 1,4 vez o tempo de C. Tempos pequenos incluem início do processo; isso não demonstra paridade geral com C/C++.

## Reproduzir 3.2

```powershell
tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe
tests/test-windows.ps1
$env:ASSIS_V32_FIXTURE_DIR = 'build/v32-fixtures'
node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js tests/test-v32.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js
```

```sh
make runtime all test test-pe
# Depois de gerar build/v32-fixtures:
python3 tests/test-v32-portable.py
python3 tools/benchmark-native.py --samples 5 --cc gcc
python3 tools/package-vscode.py
python3 tools/package-release.py
python3 tools/verify-release.py
```

O restante deste arquivo é um registro histórico. Para os recursos suportados atualmente e os limites da segurança de memória, consulte [MELHORIAS-3.2.md](MELHORIAS-3.2.md) e [MEMORIA-OWNERSHIP.md](MEMORIA-OWNERSHIP.md).

---

# Histórico: validação do AssisScript 3.1.0

Ambiente: Windows 10 x64 real, GCC 15.2 MinGW-w64 e Ubuntu x86_64 via WSL. Os compiladores Windows e Linux e o instalador foram reconstruídos dos fontes. As verificações abaixo foram executadas em 24/10/2026.

| Verificação | Resultado |
| --- | --- |
| tests/test-windows.ps1 | 128 verificações nativas Windows aprovadas |
| tests/test.sh no Linux | 133 verificações aprovadas, incluindo 256 operações aritméticas |
| tests/test-modules.sh no Linux | 10 verificações de módulos e instalação aprovadas |
| tests/test-pe.sh | 41 casos PE32+ com base relocada e ABI Microsoft aprovados |
| Suíte Node do compilador e extensão | 50 testes aprovados |
| Corpus 3.1 no Linux e perfis de instalação | 21 verificações adicionais aprovadas |
| Extensão no VS Code real | 27 verificações aprovadas |
| Benchmarks | 4 cargas, 3 variantes, 7 execuções medidas após aquecimento por combinação; todas as saídas conferidas |

A suíte nova confronta aritmética modular com BigInt, codificações com Buffer e ordenação com a implementação independente do JavaScript. Exercita extremos int64, overflow, entrada inválida, CSV com aspas/escapes/CRLF, todos os 256 bytes nas codificações, padding inválido, propriedade e reutilização de Texto, buscas recuperáveis, efeitos na atribuição composta e funções com 6.000 variáveis locais. Executa os casos válidos com e sem otimizações. O mesmo corpus é gerado e executado no backend Linux, que não exige Node instalado.

A instalação foi exercitada em pastas temporárias nos perfis completo, mínimo e seletivo. Conferimos a presença das cinco bibliotecas obrigatórias, as opcionais escolhidas, documentação individual, execução com o compilador instalado e remoção. Os testes Windows usam --no-path e --no-associations; não alteram as preferências pessoais. O registro efetivo de associações e PATH no perfil do usuário não foi repetido nesta entrega.

O teste no VS Code real aprovou sugestões, hover, F12, assinaturas, diagnósticos não salvos, overlays de dependências, pacotes .pillow, catálogo offline, documentação de conversões e try_get tipado. A falha de overlay registrada na entrega anterior não se repetiu.

As medições estão no [relatório](RESULTADOS-DESEMPENHO.md), com [amostras brutas](DESEMPENHO.json), ambiente, tamanho de binário e tempo separado de compilação. Na máquina medida, a comparação com 3.0 mostrou cerca de 1,9× em aritmética, 1,4× em HashMap e 6,5× no teste de prefixos. O array teve diferença pequena, próxima ao custo de início do processo. Isso não generaliza para todas as cargas e não compara com outras linguagens.

## Reproduzir

```powershell
tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe
tests/test-windows.ps1
$env:ASSIS_FIXTURE_DIR = 'build/v31-fixtures'
node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js
node tools/benchmark.js
```

```sh
make -B
make test
make test-pe
# Após gerar o corpus em build/v31-fixtures:
python3 tests/test-v31-portable.py
python3 tools/package-vscode.py
python3 tools/package-release.py
python3 tools/verify-release.py
```

O teste do editor usa vscode-assisscript/test/extension-host.js como extensionTestsPath, extensão local como extensionDevelopmentPath e um perfil isolado. O relatório técnico de execução fica em build/extension-host-result.json.

Não há validação de ARM, macOS, bases grandes ou depuração com breakpoints. Não há try/catch, destrutores automáticos, rastreamento de propriedade, FFI, rede ou API de arquivos nesta entrega. Ponteiros brutos e o tempo de vida de referências continuam sob responsabilidade do programa. As bibliotecas de CSV e codificação processam dados em memória. Falta de memória e falhas de programação continuam fatais.

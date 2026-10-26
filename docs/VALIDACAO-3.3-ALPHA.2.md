# Validação experimental — 3.3.0-alpha.2

Data: 24/10/2026, conforme o contexto local do usuário. Incremento de funções e structs genéricas, com compiladores nativos reconstruídos em Windows x64 e Ubuntu x86_64 via WSL2. A fase 1/F1 completa e a prontidão geral de produção continuam abertas.

A base alpha.1 teve os hashes conferidos com a validação anterior e as 472 invocações da suíte evolution repetidas com sucesso em Windows/Linux antes da implementação. A cópia local `build/baseline-3.3-alpha.1` guarda fontes/binários e `baseline-hashes.csv`; a base 3.2 anterior permanece em outra pasta de build.

## Resultados desta entrega

| Conjunto executado | Resultado |
| --- | --- |
| Node: compilador, bibliotecas e provedores do editor | 70 testes aprovados no Windows |
| tests/test-windows.ps1 | 128 verificações nativas aprovadas |
| tests/test.sh | 133 verificações Linux aprovadas |
| tests/test-modules.sh | 15 verificações Linux aprovadas, incluindo remoção de marcadores antigos/alpha.1/alpha.2 |
| tests/test-pe.sh | 41 casos PE32+ com relocação e ABI Microsoft aprovados no harness Linux |
| tests/test-evolution.py | 12 grupos, 472 invocações por sistema; repetidos nos builds sem cache |
| tests/test-generics.py | 13 grupos, 313 invocações por sistema; repetidos nos builds sem cache |
| tests/test-v31-portable.py | 21 verificações Linux aprovadas |
| tests/test-v32-portable.py | 73 casos gerados no Windows e repetidos no Linux |
| tools/validate-clean.py | Windows e Linux aprovados; runtimes regenerados e compiladores reproduzidos byte a byte |
| tools/verify-release.py | VSIX extraído e ZIP aprovados em Windows/Linux; 8 bibliotecas e 444 hashes |

Os conjuntos têm sobreposição e não devem ser somados como casos independentes. O editor foi testado pelos provedores, sem sessão visual adicional. A CI foi atualizada localmente, sem execução remota, pois o workspace não possui Git configurado. Não houve execução prolongada de serviço ou implementação das aplicações A/B/C.

As regressões novas cobrem identidade int/byte/bool/text, structs com vários parâmetros, isolamento de parâmetros T/U, recursão mútua, cache e limites, tipos aninhados/ponteiros/Array/HashMap, imports, diagnósticos da declaração e instanciação, privacidade nominal, pureza de templates não utilizados e ownership de cada instância. Os helpers verificam check/build/run, otimizado/sem otimização, ambos os destinos, mensagens JSON e preservação de um arquivo de saída existente após erros. Programas rejeitados não são executados.

Durante o desenvolvimento, os testes revelaram e corrigiram a validação de assinaturas antes da materialização das coleções e diferenças em dois diagnósticos legados. Os resultados da tabela são das execuções posteriores às correções. Logs detalhados permanecem em build/, excluído dos pacotes.

## Reconstrução e hashes

Windows: GCC 15.2.0 MinGW/MSYS2, Node 24.17.0 e Python do runtime local. Linux: GCC 13.3.0 e Python 3.12.3 do Ubuntu via WSL. A reconstrução limpa copia somente fontes/stdlib/ferramenta de geração, remove os blobs da cópia, regenera os runtimes, compila e executa as suítes evolution e generics. A igualdade é para a mesma plataforma/toolchain; não comprova reprodução entre versões diferentes de GCC/binutils.

| Compilador | SHA-256 reproduzido |
| --- | --- |
| bin/assis.exe | 5682de92c6120baa28230df8b2d5331a4d1156c94e3b73fd78c30c69f8baa0fc |
| bin/assis | 2fb410c3f6c45b06a3144891a3c4c94eecea1a2f38aeb8296720f84acfb75820 |

O runtime/layout/ABI dos programas não foi alterado. O compilador passou a resolver templates AST e especializações antes da análise e emissão nativa.

## Pacotes

`dist/AssisScript-3.3.0-alpha.2-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.2.vsix` foram gerados com os dois compiladores, documentação, fontes pertinentes, exemplos e resultados dos benchmarks. SHA256SUMS foi atualizado. A verificação extrai o VSIX, compara seus compiladores com o workspace, confere os hashes dos compiladores registrados nos benchmarks, executa exemplos de relatório/ownership/funcional/generics e valida as oito bibliotecas. Também rejeita acesso privado, reatribuição de val e efeitos/tipos indevidos em pure genérico. O ZIP passa por CRC e conferência de todas as 444 entradas listadas em SHA256SUMS.

Instalação/remoção foram repetidas em destinos temporários Windows/Linux com os novos documentos/exemplo/relatórios incluídos. Os artefatos anteriores da alpha.1 foram preservados em dist; os nomes da alpha.2 identificam a entrega atual. A cópia local de baseline e os logs de build não integram o ZIP.

## Medições de especialização

`tools/benchmark-generics.py` compara uma função manual com a especialização int equivalente, otimizado e sem otimização. Usa sete amostras intercaladas de compilação/execução após aquecimento, com dez milhões de chamadas por execução; cada saída é conferida pela fórmula independente `3*N*(N-1)/2+7*N`. Registra fontes, hashes e tamanhos dos executáveis. As medições incluem início do processo e não medem RAM, explosão de combinações, structs, closures ou aplicações reais.

Relatórios: [Windows](../benchmarks/resultados/generics-alpha-windows.md) e [Linux](../benchmarks/resultados/generics-alpha-linux.md), com JSON adjacentes contendo todas as amostras. Não atribuir ganho de runtime a generics quando as variantes emitem os mesmos bytes.

Nos dois sistemas, as variantes manual/genérica produziram binários idênticos byte a byte em cada modo de otimização. Os executáveis têm 99.328 bytes no Windows e 8.193 bytes no Linux neste programa. As diferenças entre medianas de tempo refletem variação de execução para os mesmos bytes; não comprovam ganho ou regressão de runtime por generics. O custo observado de compilação permanece delimitado à pequena carga registrada, com início do processo e acesso ao filesystem incluídos.

## Reproduzir

```powershell
tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe
tests/test-windows.ps1
python tests/test-generics.py
python tests/test-evolution.py
python tools/validate-clean.py --cc C:/msys64/ucrt64/bin/gcc.exe --binutils-dir C:/msys64/ucrt64/bin
node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js tests/test-v32.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js
```

```sh
make -B all
make test test-pe test-evolution test-generics
python3 tools/validate-clean.py
python3 tools/package-vscode.py
python3 tools/package-release.py
python3 tools/verify-release.py
```

Os pacotes exigem os dois compiladores já reconstruídos. Corpora portáveis seguem as instruções de VALIDACAO.md. O benchmark aceita `--output` para preservar resultados por plataforma.

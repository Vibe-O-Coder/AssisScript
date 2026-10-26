# Validação — 3.3.0-alpha.3

Data: 25/10/2026, contexto local do usuário. Esta entrega implementa o incremento de funções como valores e efeitos em tipos de F1. O plano completo continua aberto. A alpha.2 foi preservada antes das alterações em `build/baseline-3.3-alpha.2`; seus resultados históricos não são contados como validação atual.

## Verificações repetidas nesta entrega

| Conjunto | Windows x64 | Linux x86_64 |
| --- | --- | --- |
| Compilador/editor Node | 71 testes aprovados | Corpus portável abaixo; Node não usado no WSL |
| Suíte nativa | 128 verificações aprovadas | 133 verificações aprovadas |
| Módulos/instalação Linux | — | 16 verificações aprovadas |
| Harness PE32+ com base relocada | Windows real coberto pela suíte nativa e callbacks | 41 casos aprovados |
| Corpus 3.1 | 18 verificações aprovadas | 21 verificações aprovadas |
| Corpus 3.2 | 73 casos aprovados | 73 casos aprovados |
| Evolution (privacidade/val/pure) | 12 grupos, 472 invocações | 12 grupos, 472 invocações |
| Generics | 13 grupos, 313 invocações | 13 grupos, 313 invocações |
| Functions (novo) | 19 grupos, 383 invocações | 19 grupos, 383 invocações |
| Reconstrução sem cache | Compilador idêntico byte a byte | Compilador idêntico byte a byte |

Os conjuntos têm sobreposição; não somar como casos independentes. As três suítes Python foram aprovadas novamente contra os compiladores reconstruídos em árvores temporárias, com regeneração dos dois headers de runtime a partir de assembly. O hash desses compiladores coincide com o distribuído na mesma plataforma/toolchain. Isso não demonstra identidade entre toolchains diferentes.

A suíte nova cobre valores/aliases de função, callbacks escalares e de ordem superior, retornos e chamadas encadeadas, recursão e composição, funções genéricas especializadas como valores, substituição de tipos de função, cache que distingue efeitos, shadowing, argumentos e retornos incompatíveis, efeitos em ramos mortos e templates pure não utilizados, parâmetros imutáveis, ordem de avaliação e oito argumentos, métodos e privacidade, função em campo/Array/ponteiro, restrições de fuga e uso após liberação, empréstimo inválido de nome global, diagnóstico de callback zero e assinatura de 900 parâmetros dentro de coleção. Map/filter/fold são testados com vazio, ordem preservada, resultado independente, mudança int/byte e callback com efeitos rejeitado.

Casos aceitos passam por check e run com debug, com/sem otimização, além de build para os dois destinos. Casos negativos são rejeitados em check/build/run e não sobrescrevem o arquivo sentinela; também são rejeitados ao escolher explicitamente cada destino. O caso de campo de função zerado confirma R001/saída 70 nos dois modos. Não há execução dos antigos exemplos de acesso privado inválido.

## Builds e hashes

Windows: GCC/MinGW MSYS2 15.2.0 (Rev13), flags em `tools/build-windows.ps1`; Node 24.17.0 e Python 3.12.14. Linux: GCC/Python3 do Ubuntu via WSL, flags do Makefile. O compilador distribuído continua sem depender dessas ferramentas para gerar programas comuns.

| Artefato | SHA-256 |
| --- | --- |
| bin/assis.exe | `d64c291950dc62da333a263cb91bc3c5a5e35fb11e1b04863357b98a71f02b12` |
| bin/assis | `e46483d8a44401086312ae9646006203fb56e9e760c2aa6364b13c83cde53e72` |
| bin/assis-setup.exe | `f05408b4093d0fcad53278185567754505d2cc92f134d368cdcc6740e12db6b2` |

Logs locais: `build/regression-node.log`, `regression-windows.log`, `regression-linux.log`, `clean-alpha3-win.log`, `clean-alpha3-linux.log`, `clean-win32.json`, `clean-linux.json` e `portable-*.log`. Build/baselines/temporários são excluídos dos pacotes. Os hashes de todos os arquivos distribuídos constam em SHA256SUMS.

## Custo observado

Medições finais feitas em sequência por plataforma, depois dos demais testes: cinco milhões de chamadas, sete amostras intercaladas por variante após aquecimento, com saída conferida pela fórmula independente `3*N*(N-1)/2+7*N`. Variantes: chamada direta, indireta e wrapper genérico de ordem superior, com/sem otimização. JSON inclui fontes, amostras, hash do compilador, tamanhos de executáveis e tempos de compilação/execução.

Resultados completos: [Windows](../benchmarks/resultados/funcoes-alpha-windows.md) e [Linux](../benchmarks/resultados/funcoes-alpha-linux.md). Chamadas indiretas acrescentam carga/salto e o wrapper acrescenta uma chamada. Não há inlining/desvirtualização novos; pure não serve como dica para remover efeitos. Os tempos incluem início de processo e variabilidade do ambiente. Esta carga não mede RAM, coleções funcionais, closures, muitas especializações ou aplicações reais e não comprova ganho geral nem paridade com C/C++.

## Distribuição

Pacotes da entrega: `dist/AssisScript-3.3.0-alpha.3-windows-linux.zip` e `dist/assisscript-3.3.0-alpha.3.vsix`. Ambos contêm os compiladores atuais, oito bibliotecas, documentação, exemplos e relatórios. A verificação do VSIX extraído executa os cinco exemplos 12/14/15/16/17, confere as oito bibliotecas, diagnósticos negativos e os hashes dos binários associados às medições; o ZIP passa pela conferência de todos os hashes. A verificação é executada em Windows e Linux. Pacotes anteriores permanecem como referência histórica.

O instalador Windows foi testado em prefixos temporários, sem modificar o PATH permanente da sessão do usuário; o instalador/removedor Linux foi validado em diretório temporário. A CI foi atualizada, sem execução remota porque este workspace não possui repositório configurado. Os testes do editor exercitam os provedores; não foi feita nova inspeção visual do VS Code.

## Limites que permanecem

Tipos puros abrangem int/byte/bool e funções pure sem captura. Não há closures, tipos algébricos/matching ou imutabilidade profunda de objetos. Classes/métodos genéricos e migração integral das coleções para AST faltam. Map/filter/fold usam arrays legados com liberação explícita; não aceitam own/borrow como argumentos enquanto faltarem empréstimos nas assinaturas. Ownership segue local; ponteiros brutos/text externo mantêm seus limites. A fronteira safe/unsafe, licença/procedência e aplicações A/B/C continuam abertas. O nível de prontidão permanece experimental.

As tentativas iniciais de WSL e testes com temporários na execução restrita retornaram acesso negado antes da avaliação da linguagem. A execução autorizada com permissões ampliadas funcionou. Houve uma correção do teste novo para esperar o código 70 já definido pelo runtime para R001; isso não exigiu mudar o runtime. Não há gate local de validação pendente nesta entrega.

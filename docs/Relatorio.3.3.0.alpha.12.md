# AssisScript 3.3.0-alpha.12: análise crítica

Oct 26, 2026 · @Huginho

A AssisScript alpha.12 já é um compilador de verdade: rápido, autocontido e com um verificador de ownership que funciona. Também é um dialeto de três eras, com o perfil safe quase inutilizável para texto, sem closures e com documentação que se contradiz. Os 90% de progresso medem um plano interno e não incluem navegador, HTDL, FluxStyle nem buscador, que são o objetivo do ecossistema.

## Números medidos

Tudo abaixo foi executado por mim em Linux x86\_64, com o compilador do zip oficial alpha.12. O `.7z` traz uma árvore de trabalho à frente do binário (ver prioridade 3 na seção 4).

| Medida | AssisScript | Referência |
| --- | --- | --- |
| Compilar o analisador safe | 7 ms | n/a |
| Tamanho do executável (safe, estático, sem libc) | 25 KB | n/a |
| fib(38) recursivo | 0,46 s | C com gcc -O2: 0,14 s |
| fib(35) recursivo | 0,13 s | Python 3.13: 1,85 s |
| Crivo de primos até 20 milhões | 0,47 s | C: 0,35 s |
| HashMap de int, 2 milhões de inserções e leituras | 1,12 s | C++ unordered\_map: 0,32 s; Python dict: 1,10 s |
| Array, 20 milhões de push e soma | 0,76 s | Python: 5,37 s |
| Exemplos que passam em `check` no perfil padrão (safe) | 11 de 29 | 29 de 29 com `--legacy` |
| Suítes de teste do próprio projeto que rodei | 7 passaram, 0 falharam | 238 testes declarados no total, rodei 7 suítes de 27 |

Leitura: o código gerado fica entre 1,3 e 3,5 vezes mais lento que C otimizado, é de 7 a 14 vezes mais rápido que Python em recursão e arrays, e a tabela hash é apenas equivalente ao dict do Python.

## O programa que escrevi

Escrevi o `htdl_lint`, um analisador de documentos HTDL (só `<div type=...>`): tokeniza, valida o aninhamento, conta elementos por `type`, mede a profundidade e imprime o contorno. Foi escolhido por ser o tipo de código que um navegador feito em AssisScript precisaria ter. Fiz duas versões, com a mesma entrada de teste e a mesma saída: 8 elementos, 5 textos, profundidade 3 e 3 problemas (um `<div>` sem type no byte 161, um `</div>` sem abertura no byte 188 e um div não fechado). Conferi os offsets por fora com Python.

|  | Versão legacy | Versão safe |
| --- | --- | --- |
| Estilo | Classes polimórficas, enum + match, `String`, `HashMap<text,int>`, árvore de `Node` | Descida recursiva sobre `slice<byte>`, `own` buffers, classe `final` com receptores, sem árvore |
| Compilou e rodou de primeira | Sim, depois de corrigir um erro de construtor | Não: 2 erros de compilação a contornar |
| Tamanho do executável | 111 KB | 25 KB |
| Com `--debug` | Acusa 77 alocações vazadas (eu não liberei a árvore) | Zero vazamentos |
| Saída do contorno | Imprime os nomes dos tipos | Imprime os nomes via `write_bytes` com buffer copiado, porque não há como imprimir um slice |

O que travou durante a escrita, em ordem:

1. Subclasse com `init` de assinatura diferente é rejeitada ("sobrescrita deve manter a assinatura"). Tive que criar o objeto vazio e chamar setters.
2. Um parâmetro chamado `to` dá o erro "to sem comentário te aberto", porque `te ... to` é sintaxe de comentário herdada.
3. Não há literal de caractere. Escrevi `byte(60)` para `<` e comentei cada um.
4. Não há constante global. Usei funções `pure fn c_lt(): byte`.
5. `rep.problem(5, rep.close_at)` é rejeitado: o `borrow mut` do receptor já está ativo quando o argumento lê `rep`. Rust aceita isso há anos (two-phase borrows). Precisei de uma variável temporária.
6. No safe, `print(unicode::String)` e `print(slice)` compilam sem aviso e imprimem um endereço de memória.

Os dois arquivos vão junto com a resposta no chat.

## Pontos positivos

- **Toolchain realmente autocontida.** O compilador emite ELF e PE direto, sem assembler, linker nem libc. Compila em milissegundos e o binário de 25 KB não é dinâmico (`ldd` confirma). Isso é raro e é o melhor argumento técnico do projeto.
- **O verificador de ownership funciona.** Testei de forma adversa: uso após `move`, `borrow` e `borrow mut` simultâneos, mutação com `borrow` ativo, mover um dono emprestado e uso após `free` em código safe. Todos foram recusados em tempo de compilação, com linha e coluna.
- **Falhas em execução são fechadas.** Divisão por zero, índice fora do limite (inclusive em buffer bruto no safe) e estouro de pilha terminam com status 70 e a linha do erro, sem comportamento indefinido.
- **`--debug` de verdade.** Detecta vazamento e, no legacy, envenena memória liberada: o uso após `free` que no build normal devolveu 42 passou a dar lixo e SIGSEGV.
- **Ferramentas incluídas.** `check`, `run`, `build`, `test`, `fmt`, `doc`, `ir`, `tokens`, `new`, LSP independente, extensão de VS Code e símbolos DWARF. Para uma alpha, é muito.
- **Modelo de efeitos coerente.** `pure fn` recusa IO e alocação, `value struct` e `enum` são Copy, `match` é exaustivo. Para quem quer provar propriedades de um núcleo (como o motor do FluxStyle), isso é uma base boa.
- **Honestidade documental sobre o que falta.** `PROGRESSO.md` lista closures, variantes Move, 24 horas de soak, ARM64 e aceite independente como abertos, e diz que ownership não isola scripts hostis. Poucos projetos fazem isso.
- **Disciplina de testes.** 27 suítes declaradas e as 7 que rodei passaram, com centenas de invocações (578 em ownership de funções, 334 em valores, 305 em generics).

## O que melhorar

Ordenado por impacto. P1 são problemas de coerência e credibilidade, P2 de usabilidade da linguagem, P3 de maturidade.

| Prio | Problema | Evidência | Sugestão |
| --- | --- | --- | --- |
| P1 | Três eras de sintaxe coexistem na superfície pública | `LINGUAGEM.md` ainda ensina `assis`, `Fodase` e diz "não há for"; 18 dos 29 exemplos não compilam no perfil padrão; `assis doc` imprime `pure assis` em vez de `fn`; o erro de um `val` global manda "usar ASSIS" | Migrar manual, exemplos, template e mensagens para a forma canônica `fn`/`class`/`main`; deixar os apelidos só no compilador |
| P1 | Marca com palavrão na saída de runtime e nos templates | Todo erro de execução começa com `FODASE R001`; `assis new` gera um programa que imprime "Assis, mundo. Fodase."; o relatório de vazamento sai colado, `77FODASE R001`, um bug de formatação | Prefixo neutro (`assis: erro R001`). Em escola, concurso ou qualquer demonstração pública isso custa credibilidade sem dar nada em troca |
| P1 | Pacote entregue é uma árvore de trabalho inconsistente | `src/version.h` diz alpha.13 e `stdlib/errors.assis` já usa `own T` em enum e `closure(...)`; o binário é alpha.12 e recusa esse arquivo, o que quebra os exemplos 12, 20 e 21. O zip alpha.12 dentro de `dist/` está certo. Não há `.git` | Entregar sempre uma tag limpa; manter WIP em outra árvore |
| P2 | Texto no perfil safe é quase impossível | Função safe não aceita `text` na assinatura; `print` de `unicode::String` ou slice imprime endereço sem erro; `write_bytes` não aceita slice; não há builder safe, concatenação, literal de caractere nem constante global | Fazer `print`/`write_bytes` aceitarem slice e `unicode::String` ou rejeitar o que hoje imprime lixo; adicionar `'a'`, `const` e um builder safe |
| P2 | Coleções próprias muito fracas | `OwnedList` é lista encadeada com só `push_front`, teto de 1024 elementos e acesso O(n). Não existe `Array` de recursos Move | Um `Array<own T>` com iteração por empréstimo. Sem isso o safe não expressa uma árvore DOM de forma razoável |
| P2 | Sem closures, lambdas, métodos genéricos, interfaces, downcast nem `switch`/`for-in` | Cada um rejeitado pelo parser nos meus testes. Callbacks de eventos são "sem captura" | Closures primeiro: qualquer runtime reativo (o fluxo do FluxStyle) precisa delas |
| P2 | OOP rígida | `init` de subclasse tem de ter a assinatura da base; sem `super`; para usar uma classe como \`own\`, todos os métodos precisam de receptor explícito (\`borrow self\`) | Permitir `init` próprio por classe, como em qualquer linguagem com construtores |
| P2 | `float` só imprime em hexadecimal | `print(0.1 + 0.2)` mostra `0x1.3333333333334p-2`. Está documentado como limitação | Formatação decimal na stdlib antes de chamar a linguagem de uso geral |
| P2 | Verificador mais rígido que o necessário | Sem two-phase borrows: `v.m(v.campo)` é rejeitado | Implementar two-phase borrows |
| P2 | Diagnósticos irregulares | Linha, coluna e cursor são bons. Mas a "Ajuda" é genérica e às vezes errada (conflito de borrow sugere "confira os tipos"); mensagens com `;;` duplicado; "to sem comentário te aberto" para um parâmetro chamado `to` | Ajuda por categoria de erro; palavras herdadas como `to`, `te` só reservadas dentro de comentários |
| P3 | Desempenho de HashMap e recursão | 3,5 vezes mais lento que `unordered_map`; fib 3,3 vezes mais lento que gcc -O2 | Aceitável numa alpha. Não priorizar antes das linhas acima |
| P3 | O progresso é autoavaliado | A régua tem 35 critérios com pesos e crédito parcial de 50%, definidos pela mesma sessão que implementou, testou e validou. A própria doc lista o aceite independente como pendente | Publicar uma lista de casos que falham e pedir revisão de uma pessoa externa antes de citar porcentagem |
| P3 | Plataformas e concorrência | Só x86\_64. Heap de uma thread, rede em polling cooperativo, HTTP depende de libcurl | Ponto de partida honesto; para navegador, concorrência é obrigatória |

## Quantas linguagens ela mistura

Minha contagem: **cinco tradições de linguagem** fundidas no desenho, mais **o dialeto histórico dela mesma**, que na prática é uma sexta que você precisa conhecer para ler os exemplos e a stdlib.

| # | Origem | O que aparece na AssisScript | Onde o encaixe machuca |
| --- | --- | --- | --- |
| 1 | C | Ponteiros brutos, `alloc<T>`, `free`, bits, `extern`, ABI C, `unsafe` | Convive com o modelo seguro sem separação clara fora do `safe` |
| 2 | Java/C# | `class`, `extends`, despacho virtual, `private`, `final`, `init` | Sem interface, `super` nem downcast, e `init` rígido |
| 3 | Rust | `own`, `borrow mut`, `move`, vidas `borrow(self)`, `enum`, `match`, `Option`/`Result`, generics com `::<T>` | Sem two-phase borrows, sem closures, vidas só de uma origem |
| 4 | Haskell/ML | `pure fn`, `val`, tipos de efeito em funções, `value struct` | Três "cores" de função (legacy, safe, pure), sem função anônima |
| 5 | Go/Zig | `defer free`, toolchain única, `platform(...)`, sem GC, `Array`/`HashMap` embutidos | `div { }` como escopo de recurso é só da AssisScript |
| 6 | Dialeto Assis/Fodase (2.x) | Palavras como `Assis`, `AssIs`, `Fodase`, `FODASE`, `miyabi`, `#yuri`, `#body`, `te ... to` | Não é compatível com a regra "nomes em inglês" e ainda aparece em exemplos e mensagens |

Além das linguagens, há camadas dentro da própria linguagem: três modelos de memória (manual legado, `own`/`borrow`, ponteiro bruto), quatro tipos de texto (`text` de C, `String` legada, `unicode::String` e `slice<byte>`) e a stdlib com nomes de parâmetros em português dentro de uma API "canônica em inglês" (`prefixo`, `entrada`, `_dados`). Esse acoplamento de camadas, mais do que a lista de influências, é o que torna a linguagem difícil de aprender. Misturar boas ideias não é o problema; o problema é não ter ainda um caminho único entre elas.

## Curva de aprendizado

Minha avaliação: **difícil para quem começa do zero, moderada para quem já viu Rust e C.** O núcleo imperativo (variáveis, `if`, `while`, `for`, funções, `Array`, `HashMap`, classes) se aprende em uma tarde. A dificuldade vem do que vem depois.

- **Conceitos simultâneos.** Para ler código safe real é preciso dominar `own`, `borrow`, `borrow mut`, `move`, vidas `borrow(self)`, Copy contra Move, `pure`/`safe`/legacy, `unsafe`, generics com `::<>` e a diferença entre quatro tipos de texto. É a lista de Rust sem o mesmo nível de mensagem de erro, de documentação e de comunidade.
- **Manual contraditório.** Quem abre `LINGUAGEM.md` aprende `assis` e `Fodase`. Quem abre o README aprende `fn`. Quem roda os primeiros exemplos recebe um erro de perfil safe e precisa descobrir `--legacy`. Hoje o maior obstáculo não é a linguagem, é a porta de entrada.
- **Erros que não ensinam.** A linha e a coluna estão certas, mas a "Ajuda" quase sempre é genérica.

Caminho que eu recomendaria, e que o projeto deveria publicar como trilha oficial:

1. Sintaxe canônica com `--legacy`: variáveis, controle de fluxo, `Array`, `HashMap`, `print`.
2. Classes e herança (o núcleo legado, à la Java).
3. `struct`, `value struct`, `enum` e `match`, depois `pure fn`.
4. `own`/`borrow`/`move` em programas pequenos no perfil padrão.
5. Slices, `unicode::String` e bibliotecas com vidas.
6. Só por último `unsafe`, FFI e ponteiros brutos.

Para você especificamente, o salto é menor do que para um iniciante: as classes de Python e o básico de Rust já cobrem boa parte dos passos 1 a 3. Os passos 4 e 5 é que vão exigir tempo.

## Utilidade hoje e quando estiver pronta

**Hoje (alpha.12).** Útil para três coisas: estudar como um compilador e um verificador de ownership funcionam (o fonte do compilador tem cerca de 6 mil linhas de C, sem contar o ícone embutido), escrever ferramentas de linha de comando pequenas e rápidas, e fazer experimentos de linguagem. Não serve ainda para: programas com muito texto formatado (sem concatenação, sem formatação decimal de float), interfaces gráficas (não há nada), concorrência, e qualquer coisa que precise de estabilidade, porque a API da stdlib já mudou de português para inglês nas alphas 10 e 11 e vai mudar de novo.

**Quando terminar o plano atual.** Seria uma linguagem de sistemas pequena, parecida com um Rust simplificado com toolchain de um binário só, no estilo do Go e do Zig. A diferença real é a simplicidade de distribuição (um executável de cerca de 1 MB que gera executáveis de dezenas de KB). O que não terá de especial: não há recurso na linguagem que Rust, Zig ou Go não ofereçam melhor hoje. O valor dela só aparece se for a base do ecossistema HTDL, e aí a pergunta muda.

**Para o objetivo de recriar a web.** Aqui sou direto: o plano que chega a 90% exclui de propósito navegador, HTDL, estilos e buscador (está escrito no `PROGRESSO.md`). E a arquitetura atual aponta para o lado oposto de "substituir o JavaScript":

- JavaScript roda código não confiável de qualquer site dentro de um sandbox. A AssisScript compila para executável nativo e a própria doc diz que ownership não é isolamento contra script hostil. Falta um alvo de execução seguro (bytecode ou WebAssembly) e um modelo de capacidades.
- Não há DOM, gráficos, fontes, decodificadores de imagem, TLS próprio (HTTP depende de libcurl) nem threads. A FFI só aceita escalares, então chamar bibliotecas gráficas que passam structs por valor não é possível hoje.
- O FluxStyle é reativo por padrão (dependências explícitas e atualizações consistentes). Isso quase sempre pede closures que capturam estado. A AssisScript não as tem, e os callbacks de eventos são "sem captura".

Nada disso torna o projeto inviável, mas cada item é meses de trabalho e nenhum está nos 90%.

## Previsão

Base da previsão. A memória das outras sessões só guarda o objetivo do ecossistema (HTDL, FluxStyle, SSC, navegador e buscador próprios) e que a documentação chega em arquivos compactados. O histórico versão a versão vem do próprio pacote: do zip 2.2.0 (23/10, 21:34) ao alpha.12 (26/10, 16:04) há 16 lançamentos em cerca de 2,8 dias, e a régua interna foi de 31% (alpha.4) a 90% (alpha.12) em cerca de 30 horas. O README diz que a implementação é feita com assistência de IA em nível alto de raciocínio. Esse ritmo é real, mas tem três limites: mede acréscimo de recursos, não amadurecimento (docs e exemplos ficaram para trás); os últimos 10% da régua concentram os itens mais difíceis; e o ritmo cai quando entram usuários, bugs reportados e compatibilidade.

São estimativas minhas, não medições.

| Marco | Estimativa | Confiança | O que precisa acontecer |
| --- | --- | --- | --- |
| A régua interna chega a 100% | 2 a 6 semanas | Média a alta | Closures e variantes Move, backend por IR, 24 horas de soak (só tempo), aceite por uma pessoa de fora. Chegar a 100% não significa pronta |
| Estável para ferramentas de terceiros | 4 a 9 meses | Média | Manual único em sintaxe canônica, texto e float utilizáveis no safe, coleções próprias decentes, API congelada, mensagens de erro que ensinam, usuários reais achando bugs |
| Versão 1.0 para uso geral pequeno | 1 a 2 anos | Baixa | Concorrência, stdlib ampla, ARM64 e macOS, política de compatibilidade, comunidade e pelo menos um projeto que não seja o próprio compilador |
| Base para navegador, buscador e substituir o JavaScript | Mais de 4 anos, e só com mudança de arquitetura | Baixa | Alvo de execução com sandbox (bytecode ou WebAssembly), DOM e modelo de capacidades, pilha de gráficos, texto e TLS, threads. Nada disso está no plano atual |

Minha leitura estratégica: o caminho mais provável e mais valioso é a AssisScript virar a linguagem do **motor** (parser de HTDL, grafo de dependências do FluxStyle, cálculo físico do SSC), compilado para nativo, enquanto o que roda dentro das páginas é outra camada, com sandbox. Dizer isso cedo evita descobrir daqui a um ano que o escopo era dois projetos.

## Limites desta avaliação

- Testei só em Linux x86\_64. O Windows (`assis.exe`), o instalador, a extensão de VS Code e o LSP não foram exercitados por mim.
- Não testei rede (`net`, `http`, exigem libcurl), FFI, processos, serviço persistente, pacotes com `assis.pkg` além do exemplo 11, nem o loop de eventos além dos exemplos.
- Rodei 7 das 27 suítes do projeto. As outras não foram executadas.
- Os benchmarks são pequenos, de uma máquina de nuvem e de uma só execução cada. Servem para ordem de grandeza, não para ranking.
- Escrevi um programa em cada perfil (186 e 144 linhas). Isso mostra atritos reais, mas não substitui um projeto maior.
- As previsões são minhas e subjetivas.

Fontes: os arquivos do próprio pacote (`README.pt-BR.md`, `docs/PROGRESSO.md`, `docs/HANDOFF-3.3-ALPHA.12.md`, `docs/VALIDACAO-3.3-ALPHA.12.md`, `docs/SAFE-DEFAULT.md`, `docs/LINGUAGEM.md`, `docs/NUMEROS.md`, `docs/RECURSOS-E-FATIAS.md`, `stdlib/owned.assis`) e os testes descritos acima.

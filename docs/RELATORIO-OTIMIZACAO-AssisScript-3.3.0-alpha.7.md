# AssisScript 3.3.0-alpha.7 — Relatório de otimização

Data: 25/10/2026. Escopo: **somente desempenho do código gerado, do runtime e da biblioteca padrão**, e o plano de evolução de otimização. Compara a 3.3.0-alpha.7 com a 3.2.0 e a 3.1.0 (versões anteriores recebidas), com C `-O2` e com Python 3.13 como referências.

## 1. Resumo

A 3.3 resolveu os dois maiores problemas do relatório anterior e já fica entre **3 e 74 vezes mais rápida que o Python** na maioria das cargas, mas **ainda tem dois defeitos graves de desempenho** que o relatório anterior não alcançava e que só apareceram com testes novos.

**O que melhorou (confirmado por medição):**

- Alocação: 1 milhão de objetos passou de **4.430 ms para 8,5 ms** (520×); o runtime faz 2 chamadas `mmap` em vez de 1 milhão. A lista de 500 mil nós caiu de **1.953 MB para 30 MB** de memória.
- Indexação de `text` em variável local ou parâmetro: de **581 ms para 0,4 ms** (30 mil bytes).
- Divisão e resto por constante: Collatz de **318 ms para 83 ms**, a 1,2× do C.
- Recursão em cauda em funções `pure` agora roda em pilha constante: 50 milhões de chamadas em 43 ms.
- Estouro de pilha vira erro com status 70, em vez de `Segmentation fault`.

**O que ainda está ruim:**

1. **HashMap com chaves em passo fixo é catastrófico.** O hash de inteiros é a identidade; com chaves múltiplas de 65536, 100 mil entradas e 200 mil leituras levam **41 s** (Python: 0,06 s). Com múltiplos de 4096 e 2 milhões de leituras, 10 s contra 0,26 s.
2. **Blocos grandes são zerados de novo a cada alocação.** 3000 alocações de 8 MB levam **8,8 s** (Python: 3,0 s; C: 0,9 ms), porque o runtime executa `rep stosb` mesmo em memória recém-mapeada, que o kernel já entrega zerada.
3. **Código gerado ainda está a 2 a 12 vezes do C** em laços com arrays, chamadas e métodos pequenos, por falta de inlining, alocação de registradores por profundidade de laço e eliminação de verificações.
4. A `fib(35)` ficou **~8% mais lenta que na 3.1** (78,8 → 85,0 ms), provavelmente pelo custo novo do prólogo de cada função.

## 2. Metodologia

- **Máquina:** Linux x86_64, 2 núcleos. Todas as versões, C e Python rodaram na mesma máquina e na mesma sessão de medição.
- **Compiladores:** as três versões do AssisScript foram compiladas do fonte com `make` (`cc -O2`). O binário pré-compilado dos `.7z` não foi usado.
- **Referências:** C compilado com `gcc 13.3 -O2 -static -fwrapv`; Python 3.13.
- **Programas:** 23 programas equivalentes, mesmo algoritmo nas quatro linguagens (laços `while` no Python, sem NumPy nem funções embutidas aceleradas, exceto onde indicado). Saídas conferidas contra o Python em todos os casos antes de medir.
- **Medição:** 1 execução de aquecimento e 7 amostras; tabela mostra a **mediana**. O tempo inclui o início do processo.
- **Memória:** pico de RSS lido de `wait4`. Todo processo mostra um piso de ~14 MB (artefato do processo medidor); só valores acima disso significam algo.
- **C:** onde o compilador poderia eliminar o trabalho, usei barreiras de memória. Não há C para HashMap (não existe equivalente na biblioteca padrão) nem para recursão em cauda (o `gcc` provavelmente a reduziria a uma fórmula fechada, o que tornaria a comparação sem sentido; não testei).
- **Python:** a ordenação usa `list.sort()` (implementada em C), então o ganho de 1,6× em ordenação reflete isso.
- **Não testado:** Windows (PE), instalador, extensão do VS Code e as bibliotecas novas (`json`, `cli`, `eventos`, `iteradores`, `log`, `tempo`).

## 3. Resultados

Tempos em milissegundos (mediana de 7). "3.3 vs C" é quantas vezes a 3.3 demora o que o C demora.

### 3.1 Programas do relatório anterior

| Programa | 3.1 | 3.2 | 3.3 | C -O2 | Python | 3.3 vs Python | 3.3 vs C |
|---|---:|---:|---:|---:|---:|---|---:|
| Hello world | 0,2 | 0,2 | 0,2 | 1,0 | 14,7 | 77,6× mais rápido | 0,2× |
| Laço aritmético (50M) | 91,4 | 63,4 | 59,4 | 16,7 | 4.366,6 | 73,5× mais rápido | 3,6× |
| fib(35) recursivo | 78,8 | 88,6 | 85,0 | 17,1 | 1.036,2 | 12,2× mais rápido | 5,0× |
| Crivo até 5M | 46,7 | 40,0 | 42,2 | 22,9 | 676,7 | 16,0× mais rápido | 1,8× |
| Collatz até 300 mil | 318,1 | 89,1 | 83,3 | 70,0 | 2.494,4 | 30,0× mais rápido | 1,2× |
| Matriz 200×200 | 29,2 | 25,4 | 28,9 | 6,1 | 722,2 | 25,0× mais rápido | 4,8× |
| Quicksort 300 mil | 58,4 | 55,3 | 52,1 | 27,8 | 541,5 | 10,4× mais rápido | 1,9× |
| HashMap (chaves sequenciais) | 42,0 | 46,8 | 45,0 | — | 145,9 | 3,2× mais rápido | — |
| Objetos/métodos (10M) | 40,1 | 44,5 | 40,5 | 7,9 | 1.130,4 | 27,9× mais rápido | 5,1× |
| Alocar+liberar 1M objetos | 4.430,0 | 9,3 | 8,5 | 1,4 | 129,9 | 15,3× mais rápido | 6,3× |
| Lista de 500 mil nós | 3.467,8 | 22,7 | 18,9 | 18,9 | 173,1 | 9,2× mais rápido | 1,0× |
| Percorrer texto de 30 mil (local) | 581,3 | 0,4 | 0,4 | 6,5 | 20,4 | 54,2× mais rápido | 0,1× |

Observações: o tempo do "Percorrer texto" em C inclui um `strlen` por iteração, de propósito, para espelhar a verificação do AssisScript; o hello world mede basicamente o início do processo.

### 3.2 Programas novos (recursos e cargas que a 3.3 introduz ou promete)

| Programa | 3.2 | 3.3 | C -O2 | Python | 3.3 vs Python | 3.3 vs C |
|---|---:|---:|---:|---:|---|---:|
| Ordenar 1M inteiros (heapsort da lib) | 376,6 | 399,0 | 153,8 | 656,4 | 1,6× mais rápido | 2,6× |
| fold com callback pure (20M chamadas) | não compila | 68,4 | 35,3 | 1.193,6 | 17,4× mais rápido | 1,9× |
| Laço com chamada direta (20M) | não compila | 87,0 | 12,4 | 2.003,2 | 23,0× mais rápido | 7,0× |
| Recursão em cauda pure (50M) | não compila | 42,7 | — | 2.120,5 | 49,7× mais rápido | — |
| Texto: 5M adicionar_byte | 66,3 | 67,3 | 7,9 | 267,6 | 4,0× mais rápido | 8,5× |
| HashMap (chaves aleatórias) | 147,2 | 153,0 | — | 1.248,2 | 8,2× mais rápido | — |
| HashMap (chaves múltiplas de 4096) | 8.672,3 | 10.256,5 | — | 259,9 | **39,5× mais lento** | — |
| 3×1M objetos retidos e liberados | 102,9 | 101,3 | 69,3 | 1.229,1 | 12,1× mais rápido | 1,5× |
| 3000 blocos de 8 MB | 8.786,3 | 8.812,4 | 0,9 | 3.040,9 | **2,9× mais lento** | ≈9.400× |
| 1M alocações de 1 a 2000 elementos | 60,2 | 57,9 | 68,8 | 664,2 | 11,5× mais rápido | 0,8× |
| 5×1M push + soma | 91,4 | 86,1 | 7,3 | 554,3 | 6,4× mais rápido | 11,8× |

Na 3.2 os programas com `pure`, genéricos e `fold` não compilam, como esperado.

### 3.3 HashMap: efeito do passo das chaves

100 mil inserções e 200 mil leituras (2 rodadas), chaves `i * passo`:

| Passo | AssisScript 3.3 (ms) | Python (ms) |
|---:|---:|---:|
| 1 | 17,0 | 47,7 |
| 2 | 15,3 | 50,2 |
| 8 | 19,5 | 48,2 |
| 64 | 65,2 | 46,8 |
| 512 | 347,7 | 53,4 |
| 1.024 | 610,0 | 56,1 |
| 4.096 | 2.810,1 | 63,4 |
| 65.536 | **41.366,4** | 57,5 |

O tempo cresce quase linearmente com o passo, o padrão típico de uma cadeia de colisões que degenera em busca linear.

### 3.4 Memória (pico de RSS, MB, piso de 14 MB do medidor)

| Programa | 3.1 | 3.2 | 3.3 | C | Python |
|---|---:|---:|---:|---:|---:|
| Lista de 500 mil nós | 1.953 | 30 | 30 | 16 | 50 |
| 3×1M objetos retidos e liberados | — | 70 | 70 | 39 | 95 |

## 4. Situação das sugestões do relatório anterior (somente otimização)

| Sugestão | Situação | Evidência |
|---|---|---|
| Alocador por classes de tamanho | **Concluído** com ressalvas | 1M objetos: 4.430 → 8,5 ms; `strace`: 2 `mmap` no total. Ressalvas: zeragem sempre e blocos grandes (seção 5.2); cabeçalho de 32 bytes por bloco; retenção 70 MB contra 39 MB do C |
| Comprimento de `text` em O(1) | **Parcial** | Locais e parâmetros: 581 → 0,4 ms. **Campo de classe continua O(i)**: 30 mil bytes em 437 ms |
| Divisão e resto por constante | **Concluído** | Código gerado: `% 2 == 0` virou `test rax,1`; `/ 2` virou `sar`/`shr`/`add`/`sar`; zero `idiv` no Collatz (a 3.1 tinha 2). Collatz 318 → 83 ms |
| Comparação ligada ao desvio | **Concluído** | `n != 1` agora gera `cmp` + `je`, sem `setne`/`movzx`/`test` |
| Registradores para variáveis | **Parcial** | Quatro registradores preservados (`rbx`, `r12`–`r14`). Falta prioridade por laço (seção 5.3) |
| Argumentos de chamada em registradores | **Pendente** | Argumentos seguem na pilha (`push rax` / `call` / `add rsp`) |
| Inlining de funções e métodos pequenos | **Pendente** | `push`, `adicionar_byte`, getters e `pure` pequenas continuam como chamadas |
| Eliminação de verificação de limites | **Pendente** | Cada acesso a `Array` faz teste de nulo e `cmp` com o tamanho, mesmo dentro de `while (i < len(a))` |
| Perfil de HashMap | **Pendente, e agora há defeito concreto** | Seção 5.1 |
| Estouro de pilha com mensagem | **Concluído** | Recursão de 10 milhões de níveis: status 70 e mensagem (3.1: status 139). Tem custo de prólogo (5.4) |
| Representação intermediária (IR) | **Pendente** | Critério P5-IR do `PROGRESSO.md` |
| ELF PIE, símbolos e depuração | **Pendente** | O executável ainda é `EXEC`, sem tabela de seções; `perf` e `gdb` não conseguem usá-lo |
| Benchmark contra C e Python | **Concluído** | `tools/benchmark-native.py`, 4 cargas; este relatório amplia para 23 |
| Recursão em cauda (novo na 3.3) | **Concluído** para `pure` | 50M chamadas em 43 ms, pilha constante |
| Generics sem custo | **Confirmado em tempo** | `maior::<int>` 59,1 ms contra 54,1 ms da versão manual, faixas sobrepostas. Os binários não são byte a byte idênticos neste teste (296 bytes de código diferem, mesmo tamanho), ao contrário do que o relatório de generics do projeto (`generics-alpha-linux.md`) registra para a carga dele |

## 5. Novos achados, em ordem de prioridade

### 5.1 HashMap: hash identidade com máscara de potência de 2 (crítico)

Em `src/collections.h`: `_hash(key) = int(key) & 0x7fff_ffff_ffff_ffff`, depois `& (capacidade - 1)`, com sondagem linear e capacidade em potência de 2. Para chaves múltiplas de 2^k, só 1 em cada 2^k posições é usada como ponto de partida; as entradas se agrupam e cada busca percorre o grupo todo (seção 3.3). Chaves comuns nessa forma: identificadores múltiplos de 1000, endereços alinhados, coordenadas empacotadas como `(y << 16) | x`, marcas de tempo arredondadas.

**Correção:** misturar os bits antes da máscara (multiplicação por constante ímpar de 64 bits e uso dos bits altos, ou o finalizador do MurmurHash3/splitmix64). Custa 2 ou 3 instruções. Adicionar um teste de regressão com passos 1, 64, 4096 e 65536 que falhe se o tempo passar de, por exemplo, 5× o do passo 1.

### 5.2 Alocação: zeragem incondicional e blocos grandes (alto)

Em `src/runtime_memory.inc`, o rótulo `.Lallocated` executa `rep stosb` sobre o tamanho pedido em **toda** alocação. Para um bloco recém-obtido por `mmap`, isso é redundante (a memória já vem zerada) e força o kernel a materializar todas as páginas. Em 3000 alocações de 8 MB: 3000 `mmap` + 3000 `munmap` (~241 µs por `munmap` sob `strace`, que inflaciona o valor); cada iteração leva ~2,9 ms no total, compatível com zerar 8 MB e atender as faltas de página, embora a medição não tenha isolado essas duas parcelas. O `calloc` do C evita a zeragem e o custo de páginas que o programa nunca toca.

**Correção:** (a) pular a zeragem quando o bloco veio direto do `mmap`; (b) para blocos grandes, devolver memória com `munmap` apenas acima de um limite e manter um pequeno cache de blocos recentes; (c) zerar na reutilização só o que for necessário (a documentação exige zero ao reutilizar, então mantém-se para blocos de pool).

### 5.3 Qualidade do código gerado nos laços (alto)

Do desassemblado do laço interno da multiplicação de matrizes (3.3), 4,8× mais lento que o C:

- As variáveis mais quentes do laço (`soma`, `k`) ficam na pilha (`[rbp-0x40]`, `[rbp-0x48]`), enquanto `n`, `i`, `j` ocupam registradores. Os registradores parecem ser atribuídos pela ordem de declaração, não pela profundidade do laço.
- O array é recarregado da pilha e testado contra nulo a cada acesso; o tamanho e o ponteiro de dados são relidos do objeto.
- O índice usa `imul rcx,rcx,8` + `add` em vez de endereçamento escalonado `[base+idx*8]`.
- Operandos de expressões passam por `push`/`pop`.
- Constantes passam por `mov ecx, imm` + `cmp rax, rcx`, em vez de `cmp reg, imm`; há cópias redundantes (`mov rax,r13; mov rbx,rax`), o parâmetro é copiado duas vezes, e `3*n+1` usa `imul` em vez de `lea`.

**Correção em ordem de custo-benefício:** (1) atribuir registradores por frequência ponderada pela profundidade do laço; (2) usar imediatos e endereçamento escalonado; (3) remover cópias e saltos mortos (`jmp` para a instrução seguinte aparece na `fib`); (4) içar para fora do laço o ponteiro, o tamanho e a verificação de nulo do array quando a variável não é reatribuída; (5) eliminar o teste de limites quando o laço já o prova.

### 5.4 Prólogo de função (médio)

Toda função salva e restaura **os quatro** registradores preservados, mesmo os que não usa (na `fib`, só `rbx` é usado, mas `r12`–`r14` também são salvos/restaurados), e executa a verificação do limite de pilha (`mov rax,rsp; sub rax,N; cmp rax,[r15+0x68]; jae`). Isso explica de forma plausível a `fib(35)` mais lenta que na 3.1 (+8%, faixas de 76–80 ms contra 84–91 ms, sem sobreposição); a medição não isolou a causa.

**Correção:** salvar só os registradores usados; dispensar a verificação em funções folha com quadro pequeno, ou trocá-la por uma página de guarda com tratador de sinal.

### 5.5 Chamadas e funções pequenas (médio)

Um laço com chamada direta de uma função `pure` de uma linha, 20 milhões de vezes, leva 87 ms; o C leva 12,4 ms (inline). `push` em `Array` (5 milhões, 86 ms contra 7,3 ms) e `adicionar_byte` (5 milhões, 67 ms contra 7,9 ms) pagam uma chamada completa por elemento. Em compensação, o `fold` com callback `pure` (20M chamadas indiretas) fica a 1,9× do C, o que mostra que o mecanismo de chamada indireta é saudável.

**Correção:** inlining de funções e métodos folha pequenos, e um caminho rápido embutido para `push` e `adicionar_byte` (capacidade suficiente: grava e incrementa; senão chama a rotina de crescimento). Passar os primeiros argumentos em registradores reduz o custo de todas as chamadas.

### 5.6 `text` em campo de classe ainda é O(i) (médio)

O comprimento em cache só vale para locais e parâmetros (`MELHORIAS-3.2.md`); `self.s[i]` em um loop de 30 mil bytes levou 437 ms contra 0,4 ms na variável local. A correção definitiva está no critério P3-TEXT (texto com comprimento na representação). Até lá, o compilador pode copiar o campo para um local no início do método quando não há escrita nele.

### 5.7 Biblioteca padrão (baixo a médio)

- `ordenar_inteiros` (heapsort) leva 399 ms para 1M elementos, 2,6× o `qsort` do C. Introsort ou pdqsort, com comparador genérico, reduziria isso e evitaria o pior caso de cache do heapsort.
- `fold`, `map` e `filter` funcionam bem (seção 3.2); medir `map` e `filter` quando houver tempo.

### 5.8 Depuração e medição nativa (habilitador)

O ELF não tem seções nem símbolos, e usa endereço fixo `0x400000`. Sem isso, `perf`, `gdb` e `objdump -d` não funcionam diretamente (usei `objdump -D -b binary` neste estudo), o que encarece cada otimização futura.

## 6. Plano de evolução de otimização

Estimativas de ganho são **estimativas**, não medições.

| # | Mudança | Resolve | Esforço | Ganho esperado |
|---:|---|---|---|---|
| 1 | Misturar bits no hash de inteiros e teste de regressão por passo | 5.1 | Baixo (poucas linhas + testes) | Passo 65536: de 41 s para o patamar das chaves sequenciais (dezenas de ms) |
| 2 | Não zerar memória recém-mapeada; cache de blocos grandes | 5.2 | Baixo a médio (runtime em assembly, dois destinos) | `3000 blocos de 8 MB`: de 8,8 s para a ordem de ms |
| 3 | Prólogo: salvar só registradores usados; verificação de pilha só onde necessário | 5.4 | Baixo | Recupera e supera a `fib` da 3.1; todo código com chamadas |
| 4 | Registradores por frequência de laço; imediatos e endereçamento escalonado; remover cópias e saltos mortos | 5.3 | Médio | Laços com arrays e matrizes: aproximar de 2× do C (hoje 4 a 5×) |
| 5 | Içar ponteiro, tamanho e teste de nulo do array para fora do laço; eliminar limites provados | 5.3 | Médio | Laços de coleção e `Array.push` em sequência |
| 6 | Inlining de folhas pequenas e caminho rápido embutido de `push` e `adicionar_byte` | 5.5 | Médio | `push` e `Texto`: de 8 a 12× para ~2× o C |
| 7 | Argumentos em registradores na ABI interna | 5.5 | Médio a alto (ABI, adaptadores Windows) | Toda chamada; `fib` e métodos |
| 8 | IR tipada (P5-IR) | habilita 4 a 7 e um segundo backend | Alto | Base para os itens 4 a 7 e para ARM64 |
| 9 | Comprimento de `text` em campos e retornos (P3-TEXT) | 5.6 | Alto | Remove o O(i) restante |
| 10 | ELF PIE com seções, símbolos e linhas | 5.8 | Médio | Habilita `perf` e `gdb` |
| 11 | Introsort/pdqsort genérico na biblioteca | 5.7 | Baixo | Ordenação a cerca de 1× do `qsort` |
| 12 | Suíte de regressão de desempenho em integração contínua, com limites relativos ao C | todos | Baixo | Evita regressões silenciosas como a da `fib` e do HashMap |

**Ordem sugerida:** 1, 2 e 3 primeiro (baixo esforço, tiram os defeitos graves); depois 4, 5 e 6; o item 8 deve começar antes de 7, porque a ABI em registradores é muito mais simples de implementar sobre IR.

## 7. Limitações deste relatório

- Uma máquina de 2 núcleos, um conjunto de compiladores e versões; os números absolutos mudam de máquina para máquina (o Python mediu 3.940 ms e 4.367 ms no laço aritmético em duas sessões do mesmo dia).
- O tempo inclui o início do processo; programas abaixo de ~20 ms têm esse custo relevante.
- O código gerado foi inspecionado em quatro programas (Collatz, `fib`, matriz, e comparação genérico/manual); outros padrões de código podem ter outros problemas.
- A causa do aumento de tempo da `fib` (5.4) é uma hipótese consistente com o código gerado, não uma medição isolada.
- C e Python são referências, não metas: o C não faz verificação de limites, de nulo nem de pilha, que o AssisScript mantém.

## 8. Reprodução

O arquivo `assisscript-benchmark-3.3.zip` traz os 23 programas em AssisScript, Python e C, o corredor de medição e os resultados brutos (JSON). Resumo:

```sh
# compilar os três compiladores (em pastas separadas)
make -C AssisScript            # gera bin/assis
# AssisScript: ASSIS_PATH deve apontar para uma pasta que contém std/ com a stdlib da versão
ASSIS_PATH=./stdpath bin/assis build programa.assis -o programa
# C
gcc -O2 -std=gnu11 -static -fwrapv programa.c -o programa
# corredor: 7 amostras, mediana
python3 -I runner3.py <pasta> 7 v32,v33,py,c resultados.json
```

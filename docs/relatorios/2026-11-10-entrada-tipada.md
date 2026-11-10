# Auditoria do AssisScript e entrada tipada

10/11/2026, America/Fortaleza. O ZIP, a árvore de origem e a branch remota
`work/m3-local-resources-2026-11-04` apontaram para
`29dc9836ac4a8cd63daafe1c8657ca23471bc61a`. A continuação usa a branch
`work/typed-input-audit-2026-11-10` e uma cópia isolada. E01-04, E02-04,
E11-02 e E11-03 receberam evidência parcial. A régua do ecossistema
permanece **48,30/100, 0/5 gates**. A meta de 50% segue aberta.

## Funcionalidade observada

O AssisScript é funcional para programas nativos no perfil exercitado. Escrevi
programas em AssisScript para avaliar coleções, entrada tipada, Unicode,
conversão numérica e diagnósticos. Também executei programas de regressão de CSV,
ownership, recursos de página e os dois finais do RPG.

| Ensaio | Resultado |
| --- | --- |
| Array genérico com quatro itens, soma, pop e tamanho final | `4 18 8 3` |
| [Pedido](../exemplos/68_typed_input.assis), entrada `Júlia / 3 / 12.50 / true` | `Júlia 3 37.50`, exit 0 |
| Pedido com confirmação `false` | `Pedido cancelado`, exit 0 |
| Pedido com quantidade `9223372036854775808` | Código 3, offset 18, exit 1 |
| CLI CSV da aplicação A | Verificada contra o leitor CSV do Python, inclusive registros em limites de bloco, UTF-8 e preservação do arquivo de destino em falha |
| `print(0.1, 12.5)` | `0x1.999999999999ap-4 0x1.9000000000000p+3` |
| `read_line` legado com stdin vazio e com LF | `String` de tamanho zero nos dois casos |
| `read_line` legado com `a\x00b\n` | Assert, exit 70 |

## Onde a linguagem ainda peca

1. **Identidade da distribuição.** O `bin/assis.exe` do ZIP e o
   compilador do pacote de desenvolvimento informam `3.3.0-alpha.15`.
   Seus SHA-256 começam por `c519e591` e `8e89ae09`, respectivamente.
   O primeiro passou em 29/69 checagens e rejeitou, por exemplo,
   `try_alloc<byte>`. O pacote passou em 69/69. Os dois finais do RPG
   rodaram com ambos. O VS Code instalado tinha o mesmo binário Windows
   de 610304 bytes da distribuição antiga. Melhoria proposta: montar os
   pacotes com compiladores reconstruídos e registrar a revisão e os
   hashes por host. Rodar a matriz de compatibilidade sobre os arquivos
   contidos no pacote.
2. **Ergonomia de entrada e saída.** `read_bytes` expõe buffers, EOF e
   fragmentos. `read_line` lê byte a byte, confunde EOF com linha vazia e
   aborta em NUL. O novo leitor resolve esses casos em streams UTF-8 e
   permanece síncrono. Console interativo Windows, code page, cancelamento
   e leitura sem bloquear a UI precisam de contrato e aceite próprios.
   Para saída humana, falta formatação decimal geral com round-trip,
   precisão, largura e locale explícitos. Um programa financeiro deve
   usar inteiro escalado ou um tipo decimal próprio.
3. **Modelos de texto e composição.** `text`/`String` legados e
   `slice<byte>`/`unicode::String` têm regras distintas para vida,
   comprimento e NUL. `value struct Item<T>` com `Item<text>` é recusado
   porque o campo é referência. Vale documentar uma trajetória única de
   aprendizado, conversões com FFI, condições para especializar genéricos
   e retorno de texto com propriedade. Para edição faltam shaping, bidi,
   composição IME e aceite com tecnologia assistiva.
4. **Atrito de autoria e diagnósticos.** `val number=42` pede anotação
   de tipo. `val ação:int=42` é rejeitado no primeiro byte não ASCII.
   Duas atribuições incompatíveis no mesmo programa produziram um
   diagnóstico JSON A001. `read_bytes(data,len(data))` é recusado por
   empréstimo ativo na expressão. Calcular o comprimento antes da chamada
   compila. Melhorias de maior retorno são códigos específicos por erro,
   localização do empréstimo e de seu último uso, recuperação de múltiplos
   diagnósticos e inferência local em contextos não ambíguos. Identificadores
   Unicode pedem política explícita de normalização.
5. **Contrato de falhas e integração.** Há ownership, resultados
   recuperáveis e alocação falível. Ainda convivem sentinelas, structs
   com flags, enums e traps. Falta consolidar propagação de erros,
   exercitar OOM por ponto de alocação e demonstrar que falhas de
   componentes preservam o shell. `safe` aplica regras de memória da
   linguagem. O executor de página responde pela fronteira de autoridade
   e pelos limites de execução.
6. **Portabilidade e ecossistema.** Gerei o pedido nos cinco formatos
   Windows x64, Linux x64/ARM64 e macOS x64/ARM64. A execução desta
   unidade cobriu Windows e Linux x64. Continuam na
   [fila](../ecossistema/FILA-M0-M1.md) loader confinado e recursos
   declarados, controles/imagens/regiões vivas, SDK de strings/células e
   inscrições, identidade incremental/editor, RSS/disco/órfãos, portas
   nativas, rede, perfis, persistência, busca, M4–M9, distribuição,
   teste de 24 horas e aceites.

## Implementação

- [`std/parse.assis`](../BIBLIOTECA-parse.md) lê i8/i16/i32/i64,
  u8/u16/u32/u64, bool e f32/f64. Também valida fatias UTF-8 e copia
  conteúdo para `unicode::String`. Inteiros checam limites antes de
  acumular. Reais usam arredondamento para o par diretamente na
  precisão pedida, com subnormais, zero assinado e erro de overflow.
- [`cli::Stdin`](../BIBLIOTECA-cli.md) expõe `readln`, `readint`,
  `readfloat` e `readbool`. Reutiliza buffers, preserva bytes da linha
  seguinte e distingue EOF, vazio, I/O e limite. `line()` empresta
  dados após `readln` bem-sucedido. `cli::parse_integer` usa o novo
  parser i64 e conserva seu contrato. `read_line` e `parse_int` continuam
  disponíveis aos programas legados.
- Catálogo e instalação seletiva resolvem `cli → parse → unicode`.
  O VS Code ganhou o snippet `readint`. O empacotador aceita
  `--bin-dir` para selecionar os compiladores reconstruídos. Este VSIX
  de desenvolvimento traz compiladores Windows x64 e Linux x64.

## Validação

| Evidência | Windows x64 | Linux x64 (WSL) |
| --- | ---: | ---: |
| Testes nativos selecionados | 116 executados, 0 pulados | 109 executados, 2 pulados |
| Checagem dos exemplos | 70/70 | 70/70 |
| Finais do RPG | 2/2 | 2/2 |

Suítes: typed-input, numbers, cli, safe-default, text-bytes, values, generics,
ownership-functions, increment, install-mask e page-resources.
Frame-responsiveness executou em Windows. Linux pulou dois casos do provider
Windows em page-resources. A suíte tipada verifica as oito larguras com
limites, erros, LF/CRLF, UTF-8 inválido e com NUL, linha longa cruzando blocos,
EOF e recuperação. Para reais, compara 440 entradas por precisão com
`float` do Python e arredondamento racional independente para f32.
Os quatro métodos de entrada nova executam os programas nos modos otimizado
e `--no-opt`, com `--debug`. Os ensaios de stdin usaram redirecionamento.

Os 93 testes Node Windows passaram, incluindo extensão, LSP e instalação
isolada do compilador/stdlib. A instalação seletiva de `cli` e de `log`
incluiu suas dependências e executou o pedido a partir do prefixo instalado.
A validação do pacote e a versão instalada do VS Code são registradas à parte.

SHA-256 dos compiladores de teste:

- Windows x64 `815a7f116708b6e845367cee1626046757b23721578dfc1cc3d874cb88e782ed`
- Linux x64 `5d466b9faf280c36325a416b80579831e5408db946612a21eebaaf5be5d8688b`

Para reproduzir, reconstrua o compilador, configure `ASSIS_BIN` apontando
para o compilador adjacente à stdlib atual, execute
`python tests/test-typed-input.py`,
`python tools/validate-examples.py --output build/examples.json`,
`python tools/generate-install-manifest.py --check` e
`python tools/report-ecosystem-progress.py --check`. O comando de
checagem de exemplos executa os finais do RPG. O pedido e a suíte tipada
tiveram execuções nativas separadas.

## Visual e continuação

A demonstração anterior abriu a janela “AssisScript - Paineis SSC com
cadencia ativa”. A inspeção automatizada expirou com
`Computer Use app approval timed out`. A sessão não obteve captura nem
aceite visual novo. Seguem pendentes fluidez SSC, leitor de tela, escala e
múltiplos monitores. O demo de leitura é somente leitura. O aceite IME
requer um controle de texto exercitável.

A próxima unidade de ecossistema proposta é loader de disco confinado
para recursos declarados. Deve partir de concessão explícita, manter a
autoridade no handle efetivamente aberto e testar traversal, Unicode,
links/reparse points, corrida entre validação e abertura, cotas,
cancelamento e preservação do Frame ativo em falha. A pontuação e os
gates permanecem na [régua](../ecossistema/PROGRESSO.md). Easy continua
na última etapa.

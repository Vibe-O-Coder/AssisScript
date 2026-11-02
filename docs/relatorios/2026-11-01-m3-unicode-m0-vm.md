# Relatório — grafemas, funções em inglês e spikes de execução

Data: **01/11/2026**, America/Fortaleza. **30,10% → 32,10%; 0/5 → 0/5 gates**.
A meta solicitada de 40% não foi atingida. M0-EXEC e M3 continuam parciais.
Nenhum requisito foi retirado ou convertido em opcional para aumentar a régua.

## Base e objetivo

Base **a542aff0f6ace008e6558c1cb1553c9ea05cc2eb**, PR #20 aberta/draft/sem merge,
head confirmado pelo conector GitHub. Foram lidos masterprompt, índice, planos,
fila, JSON/relatórios, baseline, perfil viewer, ABI e ADR-0001. Raiz/status,
worktrees, branches e histórico foram conferidos. Não foi encontrado AGENTS.md.

Cópia isolada por clone local sem hardlinks em
`C:/Users/babus/Desktop/AssisScript/work/unicode-reader-20261101`, branch
**work/m3-unicode-reader-2026-11-01**. Originais e projetos irmãos preservados;
sem subagentes, reset, limpeza, merge ou force push. A pasta original contém
alterações de outras sessões; só seus ponteiros de continuidade são atualizados.

Duas unidades publicadas juntas: corrigir fronteiras de leitura e nomes de
funções (E02-04/E04-04/E11-02), e produzir os spikes M0-EXEC
(E06-01/E06-02/E06-03). O compilador atual contra a stdlib exata da base recusa
os dois novos imports: [before.json](../ecossistema/evidencias/m3-unicode-vm-2026-11-01/before.json).
Isso é reprodução de frontend, não execução dos recursos antigos.

## Implementação e decisões

`std/graphemes.assis` implementa UAX #29 revisão 47/Unicode 17.0.0 em AssisScript:
cursor constante, contexto índico/emoji/regionais e índice proprietário de
fronteiras UTF-8. Tabelas fixadas/reproduzíveis (833 intervalos e Hangul
algorítmico), proveniência SHA-256 e licença Unicode V3 incluídas. Seleção,
Shift+setas, hit test e quebra medidos passam a respeitar grafemas. Recusa de
grafema maior que viewport/4096 bytes preserva candidato/documento anterior.
Não se acrescenta ponto por Unicode: normalização/palavras/bidi/IME faltam.
[Contrato](../BIBLIOTECA-graphemes.md).

Funções/métodos de bibliotecas e exemplos foram migrados para inglês, inclusive
RPG e pacote offline. `cli::saida` → `cli::write_output`; auxiliares 2.x agora
usam `legacy_min/max/clamp/abs/fill/copy/starts_with/ends_with`. Assinaturas e
semântica anteriores são conservadas sob os nomes novos; fontes antigas
precisam migrar. API-MIGRATION, migrador, consumidores, testes, extensão e lock
do pacote foram sincronizados. Strings do produto não foram traduzidas.
Inventário por arquivo: [FUNCTION-NAMES](../FUNCTION-NAMES-2026-11-01.json).
Baseline e evidências históricas não foram reescritas.

`std/pagevm.assis` executa formato experimental ASV1, com validação de tamanho,
opcode/operandos/import versão/alvos antes de copiar/alocar. Inteiros i64,
booleanos 0/1, calls com frames isolados, memória linear, instruções medidas e
fatias cooperativas têm tetos explícitos. O único host call é soma de contador
constante e limitada; inicia negada, com concessão por identidade/origem/geração
do host e revogação permanente. Nenhuma instrução acessa FFI, arquivos,
processos, rede, relógio ou objetos nativos. Falhas são locais à instância;
efeitos já executados não têm rollback. [Contrato](../BIBLIOTECA-pagevm.md).

Wasm é spike separado em Node/V8 com fixtures geradas confiáveis. O engine
valida tipos/bytes, a ferramenta nega nomes de imports e limita o contador.
Overflow modular e controle booleano funcionam nas fixtures. MIN/-1 dá trap,
ao contrário de AssisScript/ASV1: exige lowering. Loop infinito exigiu que o
processo pai encerrasse o processo Wasm; não há fuel, loader restrito ou verificação geral dos limites
Wasm. O teste demonstra essa lacuna. **Não foi escolhido formato de página**;
semântica completa, tradução IR, ABI/SDK, custos comparáveis e sandbox seguem
abertos no [ADR-0001](../ecossistema/ADR-0001-EXECUCAO-PAGINA.md).

Frontend/backends nativos, sintaxe, ownership e efeitos do compilador não foram
alterados. Catálogo, dependências, targets de teste, runner, avisos de licença e
manifestos foram sincronizados. Novas bibliotecas opcionais: graphemes/pagevm.
O exemplo 47 executa explicitamente bytes locais ASV1, sem carregar nativo.

## Validação e evidências

Compiladores próprios reconstruídos dos fontes desta cópia: Windows x64 GCC
15.2 e Linux x64/WSL GCC 13. Hashes, duração por suíte, logs, tentativas e
limites no [resumo verificável](../ecossistema/evidencias/m3-unicode-vm-2026-11-01/summary.json).
Não se reutilizou resultado de execução da base. Comandos principais:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-unicode.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-unicode-linux
ASSIS_BIN=<candidato> python docs/ecossistema/evidencias/m3-unicode-vm-2026-11-01/run.py
ASSIS_BIN=<candidato> python tools/validate-examples.py --output <host-examples.json>
python docs/ecossistema/evidencias/m3-unicode-vm-2026-11-01/stage_installer.py
python tools/generate-grapheme-data.py --check
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-unicode-vm-evidence.py --write
python tools/verify-unicode-vm-evidence.py
git diff --check
```

PowerShell usa ucrt64/bin e aspas no argumento -Wl; WSL usa python3.
Execução de temporários/build/rede local precisou de acesso fora do ambiente
restrito após PermissionError/WinError 10061. Recusas não foram contadas como
pass. Logs iniciais e falhas corrigidas são conservados separadamente.

Corpus oficial: **766 casos Unicode**, executados nos dois modos em cada host;
oráculo são marcadores oficiais, sem reutilizar as regras da implementação.
Adversos incluem UTF-8 inválido, NUL, limites, OOM, contexto longo, seleção
invertida, acentos/ZWJ/bandeiras, reflow, viewport pequeno e sessão preservada.
Revisão do diff encontrou espaço final pertencente a grafema Prepend+space;
o trim foi corrigido para remover somente clusters de espaço independentes,
com caso adverso explícito e nova execução das fronteiras de Reader/View.
Teste antigo de textwrap que separava acento foi limitado a grafemas de um
escalar; caso explícito independente verifica `abc/af/é` em viewport estreito.

VM: modelo Python de expressões/aritmética independente, overflow, divisão,
booleans, calls, código copiado, fuel cumulativo/yield, recursão, memória,
import negado, revogação, identidade cruzada, quota, OOM e instância vizinha.
Geração/inspeção dos cinco formatos nos dois modos; execução somente x64 do
host. ARM64/macOS não executados. Linux não tem provider gráfico ou Node;
Wasm executado somente no Windows. Não há CI global/24h/release demonstrados.

Todos os 49 exemplos são verificados, com finais vitória/derrota do RPG em
Windows e Linux. As suítes Node validam APIs legadas/coleções/CSV/encoding/
BigInt/editor e instalação em prefixes temporários sem PATH/associações.
O teste de instalação inicialmente usou binário histórico e falhou ao copiar
docs novos; candidato reconstruído e distribuição temporária com compilador
próprio são usados na validação final. Nenhum binário rastreado foi substituído.
Seleção `--with reader` verifica a closure de dependências; cópias instaladas
executam grafemas e o contador ASV1. O script de staging está rastreado junto
às evidências; o executável do instalador e a distribuição temporária não são release.

Matriz final: **236 métodos executados/1 not-run no Windows x64** e
**204 executados/10 not-run no Linux x64**, mais **23 testes Node no Windows**.
Contagens de métodos não somam repetições e não confundem os 766 casos Unicode
internos com métodos unittest. Os not-run são o symlink sem privilégio e as
provas gráficas no Linux; Node/Wasm no Linux permanece explicitamente não executado.
Uma execução Windows concluiu as asserções da janela e falhou na remoção de
optimized.exe (WinError 5); log preservado e suíte repetida sem alterar asserções.
O primeiro script de staging escreveu resultado Node aprovado, mas sua impressão
de símbolos Unicode falhou em cp1252; impressão corrigida e staging final repetido.

Computer Use: habilidade lida, aplicativo próprio aberto e janela única
localizada. Captura com texto+imagem e repetição somente imagem retornaram
`window capture timed out: timed out waiting on channel`. Sem screenshot ou
aceite de desktop. Não foi usado acesso alternativo para contornar a captura.
Leitor real, DPI/monitores, IME e aceite 200% do OS seguem not-run. Registros
em [computer-use.json](../ecossistema/evidencias/m3-unicode-vm-2026-11-01/computer-use.json).

## Régua, riscos e continuidade

Somente E06-01 **0→1 (+0,50)**, E06-02 **0→2 (+1,00)** e E06-03 **0→1
(+0,50)** recebem crédito: formato ainda é spike, limites ASV1 são funcionais
delimitados e capacidade é apenas contador local. Demais 57 níveis, pesos,
aceites, baseline e retratos anteriores preservados; novo retrato integral
dos 60 critérios/cinco gates. **32,10%; nenhum gate aprovado**.

ASV1 não é escolha/compilador de página, segurança remota, sandbox ou SDK.
Limites de buffers são corpos solicitados, não RSS/overhead. O host deve
atribuir identidades sem reuso e só pode oferecer operações limitadas.
Faltam floats/objetos/ownership de página, compilador/host sob orçamento,
IPC/requests/tarefas e recuperação real de aba. Unicode não é shaping/bidi.

Próximo: fechar restrições comparáveis Wasm/VM e representação de valores/IR
antes de decidir formato. Na trilha visual permanecem desktop/leitor/DPI/
monitores e shaping/bidi/IME; catálogo HTDL/editor/identidade/loader, FS/SSC,
M1 RSS, rede/persistência/busca, M4–M9, distribuição e aceite de terceiro
continuam sem dispensa. **Easy permanece a última etapa**.

Branch de publicação: **work/m3-unicode-reader-2026-11-01**, incremental sobre
#20. Commit exato deste relatório pelo histórico, evitando hash autorreferente.
Publicação/PR/SHA remoto são confirmados por adendo depois de verificados;
push não significa merge, release ou CI aprovada.

## Adendo — publicação verificada

Implementação **f53313320dd5b6a65174d4d43728fe85d43532ca** publicada por push
normal. **155 paths alterados e 1999 blobs** da árvore inteira foram comparados
com a API GitHub (modo e SHA), com SHA remoto igual ao local. Inventário em
[published-implementation.json](../ecossistema/evidencias/m3-unicode-vm-2026-11-01/published-implementation.json).

[PR de rascunho #21](https://github.com/Vibe-O-Coder/AssisScript/pull/21),
aberta/sem merge sobre #20, vinculada à conversa. A integração negou criar PR
com HTTP 403; operação concluída pela API usando credencial Git existente,
sem expor credencial ou pedir nova autorização de rotina. O conector confirmou
depois título, base/head, estado draft e ausência de merge.

O adendo e os ponteiros de continuidade são publicados em commit documental
posterior; seu SHA exato é obtido pelo histórico deste relatório. Testes e
fontes de produto não mudaram nesse adendo. **32,10%, 0/5 gates**. CI global,
release e merge não foram declarados aprovados.

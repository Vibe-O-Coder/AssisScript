# ADR-0001 — estratégia de escolha do executor de página

Continuação de isolamento Windows, 02/11/2026: worker e compilador recebem
[LPAC sem capabilities](PERFIL-WINDOWS-ISOLATION-V1.md), identidade e perfil
por processo e teste nativo de recusas. A decisão ASV2 não muda; sandbox macOS,
quota agregada de shell/Reader, armazenamento do perfil e G2 continuam abertos.

Continuação de 02/11/2026: compilação escalar via ASC1/1 é serviço descartável com SDK embutido, orçamento de processo e supervisão em AssisScript; [contrato](../BIBLIOTECA-pagecompiler.md). A decisão ASV2 não muda. Isso remove a compilação sem orçamento desse fluxo, mas não encerra quota agregada de shell/Reader/RSS, valores gerais, sandbox Windows/macOS ou G2.

Data inicial: 29/10/2026. Decisão de 02/11/2026: **ASV2 escolhido para o perfil
escalar local; executor geral e extensão de valores/ownership ainda abertos**.
Escopo: E00-03/E06-01/E06-03. Nenhum gate aprovado.

## Decisão delimitada — reader-worker-local-1 / page-asv2

Manter a VM ASV2 em AssisScript como executor do perfil escalar documentado.
O candidato Wasm comparável agora executa os mesmos bytes produzidos pelo
backend real, preserva inteiros/booleanos, funções/controle, fuel total,
frames lógicos, memória e concessão de contador. É alternativa válida de
comparação; a decisão não depende da lacuna de fuel do spike antigo.

`tools/asv2-wasm-candidate.py` valida ASV2 e traduz para wasm32: i64 modular,
duas páginas de memória linear com máximo igual ao mínimo, um dispatcher
balanceado de PC e frames explícitos. Não há start, table, imports, grow,
chamada indireta ou recursão na pilha nativa. Cada instrução ASV2 cobra um
passo antes de executar, inclusive saltos/calls; quantum e limite cumulativo
coincidem com a VM. Registros/retornos e memória da página têm regiões
separadas, com guardas anteriores ao acesso. MIN/-1 e shifts fora de 0..63
recebem lowering explícito para conservar a linguagem. A
[semântica numérica Wasm](https://webassembly.github.io/spec/core/exec/numerics.html)
e a [validação de módulos](https://webassembly.github.io/spec/core/valid/modules.html)
foram consultadas; bytes e resultados têm provas executadas.

O harness Node invoca o verificador canônico antes de instanciar: somente
bytes exatamente reconstruídos a partir de ASV2 validado e limites aceitos
são permitidos. Mutação de fuel/import/start/memória altera os bytes e é
recusada. Depois, V8 valida o módulo e uma segunda guarda exige zero imports.
Globals/memória exportados são privados do harness confiável; nunca expostos
à página ou usados como isolamento de JS. Resposta por event/request/call e
concessão por instância/origem/geração são verificadas fora do Wasm. Imports
SDK 2..8 suspendem e esperam resposta; o harness de comparação não implementa
um segundo HTDL/SDK de produto nem conecta essa alternativa ao worker nativo.

Corpus fixo, quatro programas, sete amostras de quarenta instâncias por
amostra/engine/host. VM e Wasm observam o mesmo resultado e número de passos.
Windows x64 e Linux x64/WSL2 foram executados. No batch sum-2000 (34014 passos
por instância), medianas VM/Wasm foram 62/9,451 ms em Windows e 75/8,4762 ms
em Linux. Nos casos pequenos, o relógio inteiro da VM tem resolução insuficiente;
0 ms não significa custo nulo. Dados crus de execução, validação/compilação,
tamanho e RSS amostrado estão nos
[Windows](evidencias/m0-page-integration-2026-11-02/windows-benchmark.json) e
[Linux](evidencias/m0-page-integration-2026-11-02/linux-benchmark.json).
Tempos do processo incluem startup; tempos internos usam relógios diferentes.
Não são benchmark de um backend Wasm direto otimizado, SLA ou quota de RSS.

Razões para ASV2 neste perfil: já integra worker restrito Linux/ASIP/HTDL/SDK,
Reader, ownership local e recuperações em AssisScript; evita introduzir um
engine e outro embedding no produto e tem auditoria uniforme do custo por
instrução. Wasm ganha execução nos loops deste protótipo e merece reavaliação
se um requisito de desempenho justificar esse custo de integração. Não se
afirma que ASV2 seja universalmente mais rápido ou que o candidato substitua
um estudo de Wasmtime/embedding C com fuel próprio.

Manutenção: VM/verificador/worker próprios conservam licença do repositório.
O tradutor e harness são ferramentas locais de teste, sem nova dependência
redistribuída. Node/V8 existentes foram medidos nas versões registradas por
host (24.17.0 e 24.16.0). As licenças e avisos de Node/V8 constam do
[inventário oficial de Node](https://github.com/nodejs/node/blob/v24.17.0/LICENSE);
qualquer embedding distribuído futuro exige inventário/atualização próprios.

Objetos, strings, generics/ownership de página, orçamento do compilador e RSS
integral, sandbox Windows/macOS, broker/perfis e loader FS/SSC/recursos continuam
abertos. O programa de página não recebe FFI/arquivo/processo/rede/relógio por
esta decisão. [Reader/worker](../BIBLIOTECA-pagereader.md) usa somente ASV2.
A escolha geral exigirá novo ADR/perfil com suas provas; esta decisão não
fecha M0/M4 nem G2. As continuações abaixo preservam o histórico anterior.

## Continuação worker de 02/11/2026 — decisão VM/Wasm ainda aberta

ASV2/HTDL/SDK agora têm worker separado, ASIP/1 e navegação transacional em
AssisScript, com restrições Linux x64 verificadas e Windows explicitamente
sem sandbox de autoridade. [Perfil](PERFIL-WORKER-LOCAL-V1.md),
[relatório](../relatorios/2026-11-02-m0-page-worker.md). Isso não escolhe o
executor geral nem dispensa a alternativa Wasm comparável. G2 continua aberto.
Compilação/RSS, sandbox Windows/macOS, broker/perfis e Reader/loader conjunto
continuam pendentes. As seções anteriores de entrega abaixo são históricas.

## Continuação de 02/11/2026 — backend escalar e host local, escolha geral aberta

O destino `page-asv2` agora emite bytes a partir de IR tipada, sem AST na emissão.
O [perfil versionado](PERFIL-PAGINA-ASV2.md) define representação i64/bool,
rejeições, layout, imports, limites e ciclo de evento. Execução é AssisScript,
com SDK read-only-1, células, concessões e projeção HTDL imutável. O host copia
antes de commit, rejeita respostas antigas e alterna Pages com quanta/deadlines.
O modelo de [autoridade e falhas](AMEACAS-PAGINA-LOCAL-V1.md) liga os casos aos
testes, sem equiparar confinamento de bytecode à proteção do OS.

ASV2 é decisão de implementação **experimental desse perfil local**, não escolha
final do runtime geral. Não se usou a falha do spike Wasm como dispensa de
implementá-lo sob limites comparáveis. O comparativo Wasm anterior permanece
evidência histórica; não foi reexecutado nesta unidade. A especificação de
[operações inteiras Wasm](https://webassembly.github.io/spec/core/exec/numerics.html)
é referência primária para a diferença de divisão com sinal descrita abaixo.
Não há backend Wasm restrito novo, objetos/ownership de página, tradução geral,
budget completo de compilação/RSS, host bloqueante, processo isolado ou G2.

Próxima decisão: alternativa Wasm com validação/imports/fuel equivalentes,
medição comparável e extensão explícita de valores/ownership. SDK mutável,
broker/IPC, isolamento Windows/Linux/macOS e integração com Reader seguem
separados. [Relatório desta unidade](../relatorios/2026-11-02-m0-page-runtime.md).

## Continuação de 01/11/2026 — dois spikes parciais, escolha aberta

`std/pagevm.assis` executa ASV1 em AssisScript, com validação estrutural,
registradores i64/booleanos, calls, memória e fuel totais, fatias cooperativas
e contador hospedeiro com concessão/revogação locais. Não há frontend de
página, FFI ou autoridade nativa no bytecode. Contrato em
[BIBLIOTECA-pagevm.md](../BIBLIOTECA-pagevm.md); relatório/evidências em
[Unicode e VM](../relatorios/2026-11-01-m3-unicode-m0-vm.md).

O comparativo Wasm usa fixtures confiáveis em Node 24/V8, sem redistribuir
runtime: validação pelo engine, nomes de import negados, contador limitado,
overflow i64, desvio booleano e memória de um page com máximo explícito.
MIN/-1 produz trap, enquanto ASV1/nativo preservam MIN: um backend Wasm precisa
lowering para preservar a linguagem. Loop infinito exigiu terminar o processo
do teste; não há fuel cooperativo/validador geral de memória/imports de host.
Os testes de timeout demonstram a lacuna, sem dar aceite de confinamento.

Não foi escolhida VM em função dessa prova menor. Faltam representação de
objetos/ownership, tradução do IR, ABI/SDK completo, compilador/host submetidos
a orçamento, rejeições/semântica do subconjunto anunciado, medição comparável
de custo e alternativa Wasm com restrições verificáveis. A memória cobrada é
corpo solicitado, não RSS. Não há sandbox de processo nem recuperação de aba.
E06-01/E06-03 recebem apenas fundação (1); E06-02 delimita execução ASV1 (2).
Nenhum gate aprovado. Os parágrafos abaixo preservam o contrato de escolha.

Nativo atual serve shell/broker/motor confiáveis. Conteúdo remoto não pode
executar binário nativo privilegiado. safe e processo sem restrições não
definem autoridade, limites de CPU nem isolamento do sistema operacional.
Wasm e VM própria permanecem alternativas do plano, sem escolher runtime,
licença ou versão por suposição.

A próxima decisão exige dois spikes comparáveis de uma sessão, limitados a
valores inteiros/booleanos, funções, controle e chamada hospedeira de contador.
O candidato Wasm deve fixar wasm32/layout, representação de recursos, loader,
validação e imports. O candidato VM deve fixar bytecode, verificador, layout,
dispatcher e custo das instruções. Nenhum spike anuncia subconjunto completo
da linguagem ou G2. Generics/ownership/erros/números mantêm semântica no perfil
que for efetivamente anunciado; formas não cobertas são rejeitadas.

Ambos registram: fonte/hash, compilação, execução contra referência nativa,
ordem de efeitos, overflow/traps, validação de bytes malformados, imports
negados, forja/replay/revogação de tokens, loop/recursão interrompidos,
memória/pilha e custos de chamada ao host. Repetir o teste com outra instância
ativa. Contabilizar memória do compilador e host call bloqueante, além de VM.

O host começa sem arquivos/processos/FFI/rede/relógio para página. Só imports
versionados e capacidades atribuídas por origem/instância/geração entram na
lista explícita. Atributos da página não atribuem origem. Broker aplica
limites antes de copiar/alocar e descarta respostas tardias por requestId.

A escolha final requer evidência de semântica e de autoridade contida, custo
medido, inventário de manutenção/licença e decisão publicada. Falha em uma
dessas provas mantém a decisão aberta. Mesmo com formato aprovado, sandbox
nativa Windows/Linux/macOS é obrigação separada de E06-04 e G2.

Nenhum backend, executor, provider ou sandbox é implementado por este ADR.
AssisScript Web/Easy continuam fora desta régua; Easy permanece a última etapa.

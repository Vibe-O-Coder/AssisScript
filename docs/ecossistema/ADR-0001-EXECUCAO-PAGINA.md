# ADR-0001 — estratégia de escolha do executor de página

Data: 29/10/2026. Estado: **estratégia aceita; formato ainda não escolhido**.
Escopo: E00-03/E06-01, sem promoção de capacidade ou gate.

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

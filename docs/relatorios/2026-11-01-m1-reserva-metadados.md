# Relatório — preparação de metadados e continuidade atualizada

Data: **01/11/2026**, America/Fortaleza. Unidade **M1-ALLOC / E02-03**,
com rastreabilidade **E00-05**. **22,30% → 22,30%; 0/5 → 0/5 gates**.
M0/M1 e o aceite integrado continuam abertos.

## Base reconciliada e objetivo

O masterprompt solicitado estava na cópia original em `1ed22f5`, branch
`docs/ecossistema-web-2026-10-29`, com 31 alterações antigas. A inspeção de
branches/worktrees e a consulta GitHub revelaram a continuação publicada
`a77f3d6d377d233886f586d11a676c2554062ceb`,
`work/m1-shared-budget-2026-11-01`, [PR #13](https://github.com/Vibe-O-Coder/AssisScript/pull/13),
aberta em rascunho. Ela contém as reconciliações M0 e entregas posteriores;
não foram republicadas como trabalho novo. A cópia original foi preservada.

Base desta unidade: esse SHA a77f3d6. Branch de trabalho:
`work/ecosystem-current-2026-11-01`, em
`AssisScript/work/ecosystem-current-20261101`. A leitura do relatório e fila
atuais indicou reserva de metadados como próximo incremento M1-ALLOC.

Antes, BufferPool criava Slot e caminhos do índice ao criar buffers; não
havia Preparation/prepare_slots. A reprodução com os fontes da base e o
compilador reconstruído rejeita o tipo `buffers::Preparation` com A001
([before.json](../ecossistema/evidencias/m1-buffer-preallocation-2026-11-01/before.json)).
Isso identifica a ausência da API; não é apresentado como execução nativa.

## Implementação e decisões

`buffers::BufferPool.prepare_slots(count)` prepara pelo menos count slots
livres recicláveis. Não reserva payload nem publica identidades de buffer.
`ready_slots()` expõe o estoque. Criação consome um slot preparado; remoção
devolve-o quando sua geração permite reciclagem. Aposentadoria não devolve
estoque. Close/reset/drop liberam os metadados normalmente.

O resultado é enum Copy `Preparation.Ready(ready)` ou
`Preparation.Incomplete(code,ready)`, sem alocar para informar falha. Códigos
1 fechado, 2 limite de slots, 3 recusa do alocador, 4 quantidade inválida.
**Preparação incremental:** cada slot completo é conservado quando o próximo
candidato falha; o resultado informa o estoque total exato. A escolha permite
usar o progresso já obtido e repetir a operação. Não se promete rollback
integral dos metadados. Cada candidato incompleto é destruído; dados, quota,
ocupação e IDs dos buffers vivos permanecem intactos.

Criar buffers vazios a partir do estoque e reciclar slots não aloca pela
biblioteca. Payload não vazio continua sujeito a recusa, preservando o estoque
nesse caso. Não há quota de metadados/RSS ou integração com arena/texto nesta
unidade. Nenhuma alteração de sintaxe, compilador, ABI ou provider.

O masterprompt agora exige conferir branches e worktrees antes de escolher
trabalho, ler fila/contratos e usar a ponta reconciliada. A nota de continuidade
liga a um [índice de todos os relatórios da evolução](../ecossistema/ESTADO-ATUAL.md),
com revisões fixadas, progresso, contratos e pendências. A entrada e o plano
mestre distinguem seu diagnóstico histórico do estado atual. O masterprompt
e o índice também são copiados para o caminho original solicitado pelo usuário.

Arquivos: buffers.assis, contrato da biblioteca, exemplo 40, nova suíte,
runner/Makefile/CI/portabilidade, masterprompt/índice/fila/plano/progresso,
manifesto de instalação regenerado, evidência e verificador. O diff publicado
fornece a lista exata. Não há novo pacote, instalador, VSIX ou binário publicado.

## Validação própria

Windows x64, Python 3.14.6, GCC MSYS2 15.2.0; Linux x64 Ubuntu/WSL2,
Python 3.12.3, GCC 13.3.0. Candidatos reconstruídos sem alterar bin/:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-current.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-current-linux
```

ASSIS_BIN seleciona o candidato. Reprodução das verificações desta unidade:

```text
python docs/ecossistema/evidencias/m1-buffer-preallocation-2026-11-01/run.py
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-buffer-preallocation-evidence.py
git diff --check
```

Linux usa python3. O runner registra comandos, plataforma, tempos, stdout,
stderr, hashes do compilador e testes ignorados. Em cada host:

| Conjunto | Resultado |
| --- | --- |
| Nova suíte de preparação | **6/6**, sem dispensa |
| Regressões selecionadas de BufferPool | **8/8** |
| OwnedArray mutável | **12/12** |
| APIs canônicas | **4/4** |
| Pacotes | **12 executados sem falha, 1 not-run** |
| Total dos métodos | **42 executados sem falha, 1 not-run** |
| Portabilidade | **30/30 execuções locais**, cinco formatos gerados/inspecionados |

Not-run em pacotes: symlink no Windows; alias Windows 8.3 no Linux. Não recebem
crédito de aprovação. São regressões selecionadas, não a matriz completa de
41 suítes. O runner nativo/CI passa a incluir a nova suíte para execuções
futuras; a edição do workflow não é CI aprovada nesta revisão.

Oráculos: modelo Python de inventário lógico, 220 operações, seed 20261102,
sem reproduzir árvore ou lista livre; casos de fronteira, aposentadoria,
instâncias e fechamento; exclusividade/privacidade rejeitadas; IR sem fallback;
exemplo e geração dos cinco destinos com/sem otimização. Casos nativos usam
`--debug`, exigindo stderr sem diagnóstico de blocos vivos.

A fixture C de teste já existente recusa novos slabs de 64 KiB somente no
executável filho. Os dez laços de drenagem agora têm **2.048 passos máximos**
cada. Mesmo se a recusa falhasse, o teto é 66.408.448 bytes de payload retido,
mais os ledgers e overhead; há timeout externo de 20 s por executável.
O ensaio não busca esgotar a RAM do sistema. Mede recusa local, consumo de
estoque, falha parcial com 0/1/3/8 blocos devolvidos por classe, recursos
restantes e vizinho intacto, nos dois modos.

A revisão automática inicialmente barrou o comando com laços sem teto
explícito, citando risco de esgotamento de memória. O teste foi limitado
conforme acima e a execução seguinte foi aceita. Nenhuma rota alternativa
foi usada para executar a versão rejeitada.

Na inspeção inicial da cópia antiga houve tentativas sem crédito: acesso
negado aos temporários e candidato aninhado em pasta que impedia localizar
stdlib. Esses resultados não são usados como validação da revisão atual.
As evidências desta unidade vêm exclusivamente da cópia isolada reconciliada.

| Compilador | SHA-256 |
| --- | --- |
| Windows | 0970dfaeee0710a2106b4e0c3661ff8165346ca299b4d39a5c6335457630ee62 |
| Linux | 034d61bfe7b1106f53b4e5dadec1100faffaa4292688adfc5cd5a4f2ff9ae78c |

Os compiladores coincidem com a base porque seus fontes não mudaram. As
bibliotecas/aplicações foram recompiladas e executadas nesta sessão.
[summary.json](../ecossistema/evidencias/m1-buffer-preallocation-2026-11-01/summary.json)
identifica fontes/logs por hash. O verificador aceita `--revision SHA` para
comparar com blobs Git; ele não substitui os testes.

Não executados: macOS/ARM64 nativos, emulação ARM64, janela/IME/acessibilidade,
HTDL/FS/SSC real, Browser integrado, executor/sandbox, crash, OOM killer e
carga de 24h. Identidades locais e quota de payload não provam isolamento.

## Régua, publicação e continuidade

E02-03 permanece **2/4**, E00-05 permanece **2/4**. Nova evidência de reserva
antecipada não demonstra toda a quota do documento. Acrescentado retrato
completo dos 60 níveis e cinco gates, sem alterar pesos ou estados históricos.
A cópia antiga indicava 19,90%; o crescimento até 22,30% pertence às entregas
anteriores, não recebe crédito novamente nesta unidade.

Publicação normal autorizada pelo masterprompt lido a pedido do usuário:
branch de trabalho e PR incremental de rascunho sobre #13, sem merge.
O SHA que introduz este relatório é obtido pelo histórico Git. A confirmação
remota é registrada no encerramento; push não significa CI, merge ou release.

Próximo M1-ALLOC: orçamento por documento integrado com arena/árvore/texto,
com cobrança e rollback explícitos. Executor M0-EXEC, verificação visual M2 e
parser M3 continuam tarefas próprias. Esta entrega não anuncia prontidão do
navegador nem fecha qualquer gate.

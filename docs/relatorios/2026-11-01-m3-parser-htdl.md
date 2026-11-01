# Relatório — parser HTDL real do perfil bootstrap

Data: **01/11/2026**, America/Fortaleza. **M3-PARSER**, E07-01;
fundações E07-02/E07-05; driver E00-04; cobrança E02-03/rastreabilidade E00-05.
**22,30% → 23,90%; 0/5 → 0/5 gates**. M0/M1/M2/M3 continuam abertos.
A tentativa de chegar a 30% encerra esta unidade verificável abaixo da meta;
não se promove critério sem evidência nem se retira pendência da fila.

## Base e comportamento

Conferidos instruções aplicáveis (nenhum AGENTS.md encontrado), status, remoto,
worktrees, branches e histórico. A pasta original continua no planejamento
1ed22f5, com alterações alheias preservadas. A base efetiva é
`8bec8933a6a179b07bfc6ce96ab145030e4dcaa1`, branch
`work/m1-document-memory-2026-11-01`; PR #16 confirmada pelo conector como
aberta, em rascunho e sem merge, com esse SHA. Nova cópia isolada:
`AssisScript/work/htdl-parser-20261101`, branch
`work/m3-htdl-parser-2026-11-01`, incremental sobre #16.

Lidos índice, fila reconciliada, plano mestre/PLANO-ECOSSISTEMA, progresso,
baseline congelada, relatório mais recente pelo histórico, contratos de perfil,
ABI/ADR e snapshot HTDL 0.1 com proveniência. Não se reimplementaram as
reconciliações, arena, alocador, árvore ou provider Windows.

Antes, o compilador real da base rejeitava import de std/htdl.assis porque o
módulo não existia: [before.json](../ecossistema/evidencias/m3-htdl-parser-2026-11-01/before.json).
É rejeição do frontend, sem execução nativa. Agora `htdl::load` faz parsing,
valida sintaxe/semântica e só então ativa. Fonte inválida, quota/OOM e
instância recusada preservam o ativo; candidato externo ocupado não é
descartado. Tentativas que abrem candidato consomem sua instância.

## Implementação e decisões

`stdlib/htdl.assis` implementa o perfil congelado de nove tipos. Há BOM,
comentários, três formas de atributo, entidades nomeadas/numéricas, Unicode,
CR/CRLF, conteúdo textual, raiz/version/lang, head/title/body, modelos de
conteúdo, atributos permitidos, booleanos, heading, nomes de botão, IDs e
classes. Recursos fora do perfil falham explicitamente. Não executa conteúdo,
resolve URLs ou abre arquivos. Elementos, fragmentos e atributos usam a
mesma doctree/orçamento; 16 bytes de payload guardam spans originais.
Consultas tipadas, atributos, find_id e navegação ordenada são somente leitura.
Contrato/API/layout em [BIBLIOTECA-htdl.md](../BIBLIOTECA-htdl.md).

`documents::Store.begin_reserved` conserva begin antigo e retira a reserva
temporária antes de construir candidato. Parser cobra 96 bytes de corpo
nativo v1, scratch source_size+16 e min(20000, source_size/11+1) int64s para
IDs. O teste confronta o corpo com allocationBytes do IR. A reserva
conservadora permanece no teto depois de liberar o parser. Headers,
alinhamento/slabs/RSS, pilha e I/O do chamador permanecem fora. Não é quota
total de processo nem encerramento de E02-03.

Parsing/validação são iterativos. O primeiro ensaio encontrou limite seguro
de pilha antes dos 256 níveis: a implementação recursiva foi substituída e
os limites repetidos nos dois sistemas. IDs usam heapsort sem hashing;
duplicatas reportam a segunda ocorrência, inclusive cinco repetições.
Classes conservam primeira ocorrência e têm guarda operacional de oito
milhões de unidades de trabalho, H401. `level` usa um dígito de 1 a 6.
Essas decisões/limites são explícitos no contrato.

## Testes e evidências

Comandos/resultados por suíte, tempo, plataforma/Python e SHA-256 do
compilador são registrados pelo runner. Não se reutiliza CI ou hash de binário
anterior como validação atual. Builds próprios:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-htdl.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-htdl-linux
ASSIS_BIN=<candidato> python docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01/run.py
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-htdl-parser-evidence.py
git diff --check
```

PowerShell: PATH inclui ucrt64/bin; -Wl,--no-insert-timestamp recebe aspas.
Linux usa python3. Restrições do ambiente impediram inicialmente acesso a
temporários Python/WSL; os testes foram executados com acesso local adequado.
Os bloqueios de ambiente não foram contados como passes.

A regressão de preparação de slots recusou duas vezes a gravação de um
executável temporário no Windows, antes de executar o caso. A fixture comum
reescrevia os mesmos fault.exe/fault-reference.exe em chamadas sucessivas.
Passou a gerar caminhos distintos por chamada/modo, evitando reescrever uma
imagem recém-executada. Asserções e injeção de OOM foram preservadas; parser,
document-memory e buffer-preallocation foram repetidos nos dois hosts após
essa correção. Logs das duas tentativas iniciais ficam na evidência e não
contam como sucesso. Não se alterou o alocador ou relaxou uma asserção.

Resultados finais: [summary.json](../ecossistema/evidencias/m3-htdl-parser-2026-11-01/summary.json),
[Windows](../ecossistema/evidencias/m3-htdl-parser-2026-11-01/windows.json),
[Linux](../ecossistema/evidencias/m3-htdl-parser-2026-11-01/linux.json).
Logs distinguem métodos executados de not-run; portabilidade distingue
geração/inspeção dos cinco formatos de execução Windows/Linux x64.

| Conjunto final | Windows x64 | Linux x64 |
| --- | --- | --- |
| Parser novo | 16/16 | 16/16 |
| Documento candidato | 12/12 | 12/12 |
| Árvore | 9/9 | 9/9 |
| Preparação de slots | 6/6 | 6/6 |
| Catálogo/API | 4/4 | 4/4 |
| Pacotes | 12 executados; 1 not-run | 12 executados; 1 not-run |
| IR completa | 7/7 | 7/7 |
| Otimização | 6/6 | 6/6 |
| Total de métodos | **72 aprovados; 1 not-run** | **72 aprovados; 1 not-run** |
| Portabilidade, dois modos | **36/36 execuções** | **36/36 execuções** |

O corpus declarativo contém 69 casos; os métodos acrescentam árvores geradas
e fronteiras adversas. O caso de symlink não foi executado por restrição do
host e não conta como pass. Logs iniciais preservam a falha com caminhos de
usuário redigidos; resultados/asserções não foram alterados. Hashes são
conferidos também contra os blobs Git com --revision.

A suíte nova tem 16 métodos, otimizado/--no-opt com --debug: corpus
declarativo; árvores aleatórias seed 20261101; formas de atributo; spans;
UTF-16 com emoji/CRLF; entidades nos limites escalares; UTF-8/controles
inválidos; truncamentos; limites exatos de fonte/profundidade/nós/valor;
IDs/classes; consultas/empréstimos; reload/busy/instância antiga; varredura
de quota; recusa do OS em 12 configurações de suprimento de classes.
Ativo fica intacto e candidato é liberado, sem estressar OOM do sistema.
As configurações não constituem enumeração nominal de cada chamada
individual ao alocador; E02-03 permanece em 2.

Oráculos: XML ElementTree para árvore/entidades/CR somente na sintaxe em
comum; escalar Python para U+FFFF (XML proíbe, HTDL permite); expectativas
declarativas para erros HTDL. Não se chama XML de oráculo completo HTDL.
Árvores/diagnósticos são comparados byte a byte entre os dois modos.
Toda lógica de produto permanece em AssisScript.

macOS/ARM64 nativos, janela/IME/200%, leitor de tela, FS/SSC, sandbox,
buscador e soak de produto ficam not-run/unsupported conforme matriz.
Nenhum gate aprovado, pacote promovido ou CI global declarada verde.

## Arquivos e régua

Biblioteca/contrato/exemplo; begin_reserved compatível; corpus/driver/suíte;
runner/verificador; catálogo/dependências/manifestos; Makefile/runner nativo/
portabilidade; progresso/continuidade. Não há sintaxe nova que afete o editor.

E07-01: 1 → 2 por subconjunto útil real; catálogo completo/recuperação faltam.
E07-02: 0 → 1 por atributos/consultas; mutação HTDL validada/foco faltam.
E07-05: 0 → 1 por ativação local validada; código/recursos/origens/rede e
respostas tardias faltam. E00-04: 0 → 2 por driver reproduzível com oráculo e
matriz; FS/SSC/demais perfis faltam. Obrigações distintas, sem crédito de
parser por janela. Cada mudança rende 0,40: **+1,60 → 23,90%**.
Demais níveis/pesos, baseline e históricos anteriores são preservados;
retrato novo contém os 60 critérios/cinco gates.

## Publicação e continuidade

Publicação preparada para `work/m3-htdl-parser-2026-11-01` no
Vibe-O-Coder/AssisScript, PR de rascunho sobre #16. SHA remoto/inventário e
PR serão confirmados em adendo. Até isso não se declara envio concluído.
O SHA deste relatório é localizado pelo histórico Git, sem hash autorreferente.

Próximo: M2-WINDOW, janela útil integrada ao documento validado, texto,
eventos, recursos e prova visual. M3 ainda exige apresentação textual,
controles/foco/seleção/scroll, ponte acessível, catálogo completo,
recuperação de edição e mutações semânticas. M0-EXEC exige os dois spikes
VM/Wasm e decisão; parsing não o libera. M1 ainda não limita RSS/processo.
Easy permanece a última etapa.

## Adendo — publicação bloqueada pela revisão automática

Implementação/testes/evidências registrados em
`d8af5d1940698452e408b7d88e13724b4bce1941`, **53 arquivos**, com árvore de
trabalho limpa. Os 115 hashes foram conferidos também contra os blobs desse
commit. Este adendo atualiza somente continuidade/publicação e hashes
documentais; não altera código ou resultados validados.

O primeiro push falhou por conexão bloqueada. A tentativa com acesso à rede,
`git push -u origin work/m3-htdl-parser-2026-11-01`, foi **rejeitada antes da
execução pela revisão automática**. Motivo informado: publicar 53 arquivos
locais de fontes/testes/evidências num GitHub público pode expor dados do
projeto e exige autorização direta do usuário para payload e destino exatos.
A autorização de publicação no masterprompt não foi considerada suficiente.

Não foi usada rota alternativa. **Sem publicação ou PR nova confirmadas**.
O commit e um patch completo ficam locais; a ação pendente é autorizar o envio
dos 53 arquivos desta branch ao repositório público
`https://github.com/Vibe-O-Coder/AssisScript.git`, seguido de PR de rascunho
incremental sobre `work/m1-document-memory-2026-11-01`, sem merge/release.
O SHA final deste adendo é localizado pelo histórico, sem hash autorreferente.

## Adendo — autorização direta e publicação confirmada

Após o bloqueio, o usuário autorizou diretamente nesta conversa a publicação
dos 53 arquivos do commit
`ff2997322995ce797ddc47ae6c600785eb2014ea` no repositório público
Vibe-O-Coder/AssisScript e a criação da PR de rascunho, sem merge/release.
O push da branch `work/m3-htdl-parser-2026-11-01` foi concluído; ls-remote
confirmou o SHA e a API compare confirmou os 53 caminhos e hashes de blob
contra o inventário Git local. Os 115 hashes também foram verificados no
commit autorizado, antes da publicação.

[PR de rascunho #17](https://github.com/Vibe-O-Coder/AssisScript/pull/17),
incremental sobre `work/m1-document-memory-2026-11-01` (#16), criada e
vinculada à conversa. A API confirmou aberta, draft=true, merged=false,
head=ff2997322995ce797ddc47ae6c600785eb2014ea e 53 arquivos alterados.
O conector retornou 403 ao criar; a operação autorizada foi concluída usando
a autenticação Git existente, sem expor credenciais. A leitura posterior
pelo conector confirmou a PR.

Este adendo e as correções de continuidade são documentais. Fontes/testes,
resultados, 23,90% e 0/5 gates permanecem iguais. Não se declara CI aprovada,
merge ou release. O SHA final é obtido pelo histórico deste relatório,
evitando autorreferência. O bloqueio anterior acima é registro histórico,
resolvido pela autorização direta e publicação conferida.

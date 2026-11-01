# Relatório — janela integrada ao HTDL e apresentação local

Data: **01/11/2026**, America/Fortaleza. **M2-WINDOW e M3 parcial**.
**23,90% → 27,00%; 0/5 → 0/5 gates**. A tentativa de alcançar 30% ainda não
atingiu a meta. Nenhum peso, requisito, baseline ou histórico foi removido.

## Base, objetivo e antes/depois

Base `ebd3185ae952a85c64cb2a83cd014ac07c0e8c7f`, branch publicada
work/m3-htdl-parser-2026-11-01. O conector confirmou PR #17 aberta, em rascunho,
sem merge e com esse SHA; Git ref remoto conferido pela API. Foram consultados
status, remoto, worktrees, branches e histórico. A pasta original em 1ed22f5
com alterações de outras sessões foi preservada. Nenhum AGENTS.md aplicável
foi encontrado. Cópia isolada limpa: `AssisScript/work/htdl-viewer-20261101`,
branch **work/m2-htdl-viewer-2026-11-01**, descendente incremental de #17.

Lidos masterprompt, índice/fila, planos, progresso/baseline, contratos
viewer-local-bootstrap-v1/ABI/ADR e rascunho HTDL/proveniência. Não foram
refeitos parser, arena, Store ou provider base. Uma reconstrução da stdlib do
SHA base, usando o compilador atual sem mudanças de frontend/backend, recusa
import std/viewer.assis: [before.json](../ecossistema/evidencias/m2-viewer-2026-11-01/before.json).
Isso é reprodução de rejeição do frontend, não execução de produto antigo.

Agora o exemplo 44 lê o caminho HTDL explicitamente passado, valida-o, constrói
apresentação própria e abre janela nativa com texto acentuado, botões, foco,
teclado/ponteiro, rolagem, redimensionamento e fechamento. O estado e as decisões
do produto são AssisScript. O shim adapta somente medidas, retângulos e mensagens
User32/GDI. Não há rede nem execução de página.

## Implementação e decisões

`stdlib/viewer.assis` percorre a árvore iterativamente, colapsa espaços entre
fragmentos inline, omite head/hidden e constrói linhas próprias com NodeId
completo. Quebra usa medidas do provider, palavras e fronteiras de escalares
UTF-8. A mesma geometria atende paint e hit test, incluindo a omissão de linhas
parciais nas bordas. Disabled conserva desenho, mas impede foco/ativação.
Button vazio pode apresentar a11y-label como alternativa textual.

View é construída à parte: recusa de geometria, medição, workspace ou alocador
não muda a apresentação anterior. Resize restaura foco por identidade e scroll
limitado, cancela gestos e impede repetição adicional de Enter pressionado.
Os bytes não dependem do Store depois de construídos. Close é idempotente;
apresentação fechada, instância incorreta e sequência antiga recusam eventos.

Tab/Shift+Tab percorrem botões habilitados e revelam foco; Enter ativa uma vez
no down e Espaço no up. Ponteiro exige down/up no mesmo botão visível; perda
de foco/captura cancela o gesto. Setas/PageUp/PageDown/Home/End/roda limitam
scroll. Change Copy entrega uma ativação local ao shell, sem handler de página.

Extensão viewer 1 mantém a ABI base 0x00010000. Novos imports ficam somente
em viewer; window continua carregável contra provider v1 antigo, verificado
pela fixture original. DLL antiga com import viewer falha no loader: não se
promete detecção dinâmica. platform_token expõe identidade opaca somente à
ponte do host; não é ponteiro/HWND ou capacidade de autorização. Temporários
ativos de window passam a try_alloc; o chamador deve usar try_new no objeto.

Workspace: até source_size bytes e min(32768,source_size+tree.size+1) linhas
de 72 bytes; guarda de 8 milhões de bytes em medidas de prefixo, até 4096
bytes por chamada. Teto adicional ao Store, sem RSS/overhead. O File legado
do exemplo ainda aloca caminho de até 32768 bytes por caminho fatal. Não há
recuperação integral de OOM da aplicação. [Contrato/API](../BIBLIOTECA-viewer.md).

## Validação e resultados

Builds próprios da revisão, sem reutilizar binário/CI anterior:

```text
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o build/assis-viewer.exe
cc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-viewer-linux
ASSIS_BIN=<candidato> python docs/ecossistema/evidencias/m2-viewer-2026-11-01/run.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m2-viewer-2026-11-01/before.py
ASSIS_BIN=<Windows> python docs/ecossistema/evidencias/m2-viewer-2026-11-01/snapshot.py
ASSIS_BIN=<Linux> python tools/validate-window-fallback.py --output docs/ecossistema/evidencias/m2-viewer-2026-11-01/linux-fallback.json
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-viewer-evidence.py --write
python tools/verify-viewer-evidence.py
git diff --check
```

No PowerShell o PATH do build inclui ucrt64/bin e a opção -Wl recebe aspas.
Linux usa python3 e WSL Ubuntu local. O acesso inicial a diretórios temporários
e ao serviço WSL foi recusado pelo ambiente; os testes foram executados com
acesso local adequado. Esses bloqueios não contam como pass.

| Conjunto | Windows x64 | Linux x64 |
| --- | --- | --- |
| Viewer | 12/12 executados | 10/10 executados; 2 Windows not-run |
| Fronteira provider Windows | 19/19 | unsupported; não executada |
| Parser HTDL | 16/16 | 16/16 |
| Document memory/tree | 21/21 | 21/21 |
| FFI/API inglês/pacotes/IR/otimização | 38/38; 1 symlink not-run | 38/38; 1 symlink not-run |
| Total da matriz | **106 executados; 1 not-run** | **85 executados; 3 not-run** |

Cada método relevante executa os modos otimizado/referência. O probe viewer
gera e inspeciona os cinco formatos nos dois modos, executando somente no host
x64 correspondente. A fronteira Windows repete o oráculo C e a geração dos
cinco formatos. Não se chama geração de execução ARM/macOS. Fallback Linux
ausente também é executado em ambos os modos. Não foi executada CI global.

Oráculo textwrap Python com métricas escalares independentes, quatro larguras,
seed 20261101, acentos/combinação/emoji/palavra grande; árvore/parser conserva
seus oráculos próprios. O modelo remove espaços ASCII finais por contrato:
Python 3.10 e 3.14 diferem nesse detalhe de quebra de palavras grandes. Não
se afirma segmentação por grafema. Medidas nativas são comparadas a GDI direto;
retângulos a modelo independente por pixel com coordenadas extremas.

Há recusa do OS com caches esgotados, preservando snapshot/botão e janela
vizinha; temporários de desenho/medida e criação de janela falham sem trap.
Thread errada, handles, UTF-8, fila saturada, OOM de superfície, liberação,
provider antigo e 1.000 ciclos são conferidos. A aplicação real, em processo
separado, recebe mensagens nativas, abre caminho Unicode, recusa UTF-8/sintaxe/
arquivo grande/ausente, ativa por Enter/Espaço/clique, redimensiona e fecha.
O teste espera a conclusão do clique antes do resize; resize cancela gestos.

Ensaios iniciais identificaram e corrigiram localização da DLL no runner,
quebra gulosa em fronteiras de palavra e preservação dos imports base. A janela
IME auxiliar foi excluída pelo nome da classe no teste de processo. Falhas de
construção de dumps foram corrigidas sem alterar asserções funcionais. Resultados
finais por comando, tempo/plataforma e hashes estão nos JSONs e logs atuais.

Computer Use localizou o processo interativo, mas a captura falhou com
FrameArrived timeout e novamente após ativação. **Captura da janela real e
aceite visual de desktop continuam not-run**. Foram gerados/inspecionados dumps
da superfície real do provider em três estados, com bytes iguais entre modos:
[início](../ecossistema/evidencias/m2-viewer-2026-11-01/top.png),
[foco](../ecossistema/evidencias/m2-viewer-2026-11-01/focused.png),
[fim](../ecossistema/evidencias/m2-viewer-2026-11-01/bottom.png).
Não são screenshots do desktop, prova de leitor de tela ou aceite de 200%.
Exports de dump/inspeção existem só na DLL de teste e não na produção.

## Régua, arquivos e limites

E04-02 1→2: janela com documento/eventos reais; monitores/touch/suspensão faltam.
E04-03 1→2: composição/recorte úteis integrados; imagens/transforms faltam.
E04-04 0→1: medição de fonte/UTF-8; shaping/bidi/seleção/IME faltam.
E07-04 0→2: estado e entrada por documento com snapshot/recusas; células,
inscrição de handlers, mutações e transações de página completas faltam.
E08-02 0→1: fundação de layout/snapshot/hit test/scroll; constraints row/column,
FS/SSC e snapshot acessível faltam. E08-05 0→1: artigo em três superfícies e
eventos reais; contador/dois painéis/leitor de tela e inspeção de grafo faltam.
Obrigações distintas: entrada, desenho, medidas, estado, geometria e corpus.
**+0,50+0,50+0,50+0,80+0,40+0,40 = +3,10 → 27,00%**.
Retrato novo conserva os 60 critérios e cinco gates; nenhum nível 4 concedido.

Fontes: viewer/window, provider/header; exemplo/artigo; testes/runner/verificador
e evidências; catálogo/dependências/manifestos/Makefile; contratos, progresso,
continuidade e este relatório. Frontend/backend/sintaxe/semântica da linguagem
não mudaram. Baseline congelada e antiga trilha de 100/100 foram preservadas.

M2/M3 permanecem parciais por aceite visual/seleção/acessibilidade. Não há
zoom/200%, IME/clipboard, árvore assistiva, FS/SSC, catálogo HTDL completo,
recuperação de editor, mutação HTDL validada, código/rede/sandbox, busca ou
soak 24h. Callback de medição é confiável. Tag de documento recusa entrega
semântica antiga, mas não cancela por si só mensagens do OS ainda não obtidas
antes de navegação. Portanto não aprova loader completo, M4 ou G2.

## Publicação e próximo incremento

Publicação normal autorizada pelo masterprompt no repositório
Vibe-O-Coder/AssisScript, branch work/m2-htdl-viewer-2026-11-01 e PR de rascunho
incremental sobre #17, sem merge/release. SHA remoto, inventário e PR serão
confirmados no adendo; antes disso não se declara envio concluído. O SHA do
relatório é localizado pelo histórico, sem autorreferência.

Próximo: seleção de texto, verificação real de 200%/monitores e ponte acessível
do perfil, com leitor de tela e captura de desktop. Não remover esses aceites
porque a superfície já desenha. M0-EXEC exige spikes VM/Wasm/decisão próprios;
M1 ainda não limita RSS. Demais M0–M9/60 critérios continuam na fila.
Easy permanece a última etapa de todo o projeto.

## Adendo — revisão automática bloqueou a publicação

Implementação, testes e relatório foram commitados em
`d39371d8cbaefa85df7ed9923c78df495c584a98`, **62 arquivos**. Os 167 hashes
da evidência foram conferidos também contra os blobs desse commit. O patch
completo e inventário de paths/blobs ficam em build/m2-viewer.patch e
build/publication-inventory.json, locais e fora da distribuição.

O envio `git push -u origin work/m2-htdl-viewer-2026-11-01` foi **rejeitado
antes de executar pela revisão automática de aprovação**. Motivo informado:
enviar 62 arquivos de fontes/testes/evidências a um GitHub público é saída
externa sensível; as mensagens diretas do usuário não autorizavam explicitamente
esse payload/destino exatos. A autorização de publicação do masterprompt não
foi considerada suficiente pelo revisor.

Não houve nova tentativa por outra rota. **Branch não publicada e nenhuma PR
nova criada**. Este adendo atualiza somente o estado documental; fontes,
testes, 27,00% e 0/5 gates permanecem iguais. O SHA documental final é obtido
pelo histórico deste relatório. O diff continua contendo os mesmos 62 paths.

A ação pendente é autorizar explicitamente os 62 arquivos da revisão final
da branch work/m2-htdl-viewer-2026-11-01 para o repositório público
`https://github.com/Vibe-O-Coder/AssisScript.git` e a PR de rascunho incremental
sobre work/m3-htdl-parser-2026-11-01 (#17), sem merge ou release. Publicar
torna fontes, logs e imagens de demonstração visíveis publicamente.

## Adendo — autorização direta e publicação confirmada

O usuário autorizou diretamente publicar os **62 arquivos** do commit
`3b09a2a15e7cb75915a9e78448ea0eff9c2ffc93` no repositório público
Vibe-O-Coder/AssisScript e abrir a PR de rascunho, sem merge ou release.
O push da branch work/m2-htdl-viewer-2026-11-01 foi concluído; ls-remote
confirmou o SHA autorizado e a API compare conferiu os 62 paths e hashes de
blob contra o inventário Git local. Os 167 hashes de evidência também foram
conferidos contra os blobs commitados antes do envio.

[PR de rascunho #18](https://github.com/Vibe-O-Coder/AssisScript/pull/18),
incremental sobre work/m3-htdl-parser-2026-11-01 (#17), criada e vinculada à
conversa. O conector confirmou state=open, draft=true, merged=false,
head=3b09a2a15e7cb75915a9e78448ea0eff9c2ffc93 e changed_files=62.
O conector retornou 403 na criação; a operação autorizada foi concluída
pela autenticação Git existente, sem expor credenciais.

Este adendo e as correções de continuidade são documentais. Código, testes,
27,00% e 0/5 gates permanecem iguais. Não se declara merge, release ou CI
global aprovada. A revisão documental final é localizada pelo histórico deste
relatório, sem autorreferência. O bloqueio descrito no adendo anterior é
histórico e foi resolvido pela autorização direta e publicação conferida.

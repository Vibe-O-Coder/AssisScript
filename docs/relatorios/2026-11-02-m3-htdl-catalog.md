# Relatório — catálogo estático HTDL 0.1 e editor

**02/11/2026, America/Fortaleza. 42,70% → 43,30%; 0/5 → 0/5 gates.**
Meta 50% pendente. M3 parcial, E00-01 1→2 (+0,20), E07-01 2→3 (+0,40).
E00-04/E07-02/E11-02 recebem evidência nova sem subir de nível. Demais pesos,
níveis, aceites, baseline congelada e história permanecem; acrescentado retrato
completo dos 60 estados e cinco gates. Nenhum nível 4. Easy segue por último.

## Base, objetivo e reprodução

Base publicada **f00d1ff95694dd312f90ec46d563606bda258356**, branch
`work/m0-windows-isolation-2026-11-02`, confirmada por fetch_commit GitHub e
git ls-remote antes de alterar. Repositório original em `1ed22f5`, com alterações
alheias preservadas. Worktrees, branches, histórico, status, remoto, planos,
fila efetiva, 60 critérios, baseline e contratos viewer/ABI/ADR consultados.
O relatório mais recente é o da unidade Windows por ancestralidade Git, não
pela ordenação de nomes. Não havia AGENTS.md aplicável; nenhum subagente usado.

Cópia isolada sem hardlinks:
**C:/Users/babus/Desktop/AssisScript/work/htdl-catalog-20261102**.
Branch **work/m3-htdl-catalog-2026-11-02**, remoto
**https://github.com/Vibe-O-Coder/AssisScript.git**. Sem reset, limpeza, troca
de branch de outra sessão, merge, force push ou promoção de pacote.
Rascunhos públicos/procedência preservados; a referência irmã 0.1 foi lida.

Objetivo: ultrapassar a limitação estática do catálogo bootstrap sem anunciar
controles/recursos visuais ainda ausentes, e oferecer análise recuperável ao
editor. A [reprodução nativa](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/before.json)
usa o mesmo documento com input/label: a base publicada e o bootstrap atual
retornam H203, enquanto a entrada catalog retorna sucesso. Não é classificado
como bug da base: o perfil anterior deliberadamente recusava esses recursos.
O binário histórico foi usado somente nessa reprodução, com hash registrado.

## Implementação e decisões

Toda análise sintática/semântica permanece em **stdlib/htdl.assis**. Sem sintaxe
nova do AssisScript, FFI, shim ou dependência externa. O Parser mantém corpo
nativo de 96 bytes e workspace reservado antes de alocar. APIs canônicas em inglês.

`stage_catalog`/`load_catalog` aceitam os 23 tipos do catálogo, preservando IDs
1..9 e acrescentando 10..23. Validam metadados e ordem/cardinalidade de head,
atributos específicos/comuns, data-*, referências de label/input, nomes únicos
de controles por form, nomes acessíveis, restrições de main/form, checkbox,
submit, eventos e declaração de script. Valores de input permanecem texto.
IDs únicos/classes/Unicode/entidades/spans reaproveitam a fundação existente.
`query` reconhece os novos tipos; `data_attribute` distingue nomes dinâmicos.

`stage`/`load` continuam no bootstrap. Reader/pagereader não são ampliados por
reconhecer tipos no parser. src/href são dados: não abrem recursos, executam
script ou concedem autoridade. O filtro lexical recusa esquemas de execução,
absolutos, backslash e espaços; não implementa URL, autorização, DNS ou loader.
`format=wasm` só é reconhecido como metadado do rascunho, sem mudar o ADR ASV2.

`Diagnostics` tem construção fallível, capacidade 1..64, corpo nativo de
**40 bytes** e payload externo de capacity*56 bytes. `inspect` nunca ativa
o candidato, mesmo válido; sempre aborta seu próprio candidato e preserva
ativo/vizinha/candidato de outro produtor. Após árvore sintaticamente completa,
continua após erros semânticos e recupera diagnósticos com spans UTF-16.
Sintaxe/UTF-8 inválidos ainda produzem somente o primeiro erro; nenhuma fonte
é consertada ou tornada executável. Truncamento e H401 são explícitos.

Limites originais preservados e trabalho de referências cobrado: oito milhões
de unidades compartilhadas; varredura de registro custa 128, comparação de
byte/ancestral custa uma. Pode recusar documento estruturalmente válido com
muitas referências. Não é RSS ou SLA de UI. O ensaio inicial que varria todos
os controles sem esse custo excedeu 30 segundos; foi corrigido antes da matriz
final, com atalho para nome acessível explícito e teste de saturação determinista.

LSP/VS Code usam **tools/htdl-check.assis**, compilado de fonte confiável fixa;
rascunho entra por stdin. JS só adapta protocolo/IDE. Analisador é filho direto,
com deadline total de 15 s, saída de 64 KiB, cancelamento e limpeza de temporários.
Geração/versão impedem publicar respostas antigas; fechar limpa diagnósticos.
LSP oferece termos de conclusão e não envia HTDL ao formatter AssisScript.
VS Code respeita confiança/diagnósticos e oferece check manual HTDL, gramática
e configuração próprias. Assinatura de função/recurso exigem o loader futuro.

Manifestos Windows/shell, catálogo, dependências opcionais, empacotador VSIX,
Makefile e documentação sincronizados. Instalação mínima precisa selecionar
htdl (`--with htdl` no shell). Não se torna a biblioteca obrigatória globalmente.

## Testes e evidência

[Resumo verificável](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/linux.json),
[editor](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/windows-editor.json).
São execuções desta unidade, com comandos, logs, hashes de fontes/binários,
plataformas e contagens rastreados; evidência histórica não é contada de novo.

| Suíte de métodos | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Catálogo/editor nativo, ambos os modos | 16/0 | 16/0 |
| Parser bootstrap, ambos os modos | 16/0 | 16/0 |
| Transações do Reader | 15/0 | 11/4 |
| Reader | 10/0 | 7/3 |
| Host de página | 13/0 | 13/0 |
| Reader/worker otimizado | 10/0 | 9/1 |
| Reader/worker referência | 10/0 | 9/1 |
| **Total** | **90/0** | **81/9** |

Contagens são métodos de teste, não instruções, subprocessos ou cenários
globais de conformidade. Suítes compararam os modos internamente quando
marcado. Foram gerados cinco formatos nativos nos dois modos; somente Windows
x64 e Linux x64/WSL2 executados. ARM/macOS continuam not-run.

Novo corpus declarativo tem 26 casos; testes adicionais exercitam todos os
tipos, árvores aleatórias contra XML ElementTree na sintaxe em comum, ordem e
escapes/entidades, labels forward, metadados, nomes por formulário, atributos
data-* e eventos. Há raízes semanticamente hostis, UTF-8 truncado, saída
limitada, fontes >1 MiB, varredura excessiva, sweep de quota, OOM real do OS,
rollback, empréstimos, vizinha e candidato de outro produtor. Oráculo XML
não define a semântica HTDL e não é usado para atributos on:* sem namespace.

**54 exemplos por host** analisados e duas terminações RPG executadas por host.
Exemplo 52 executado nos dois modos em cada host: `HTDL-CATALOG 21` e
`EDITOR-DIAGNOSTICS 2`, preservando a árvore anterior. **37 testes Node Windows**
cobrem LSP como processo independente, UTF-16, rascunho, correção, descarte de
versões, protocolo hostil, cancelamento antes/durante processo e temporários.
VS Code tem host simulado para confiança, comandos e ranges; não é aceite
interativo do aplicativo. Node não está disponível no Linux desta matriz.

57 arquivos do snapshot histórico têm integridade conferida; os 16 cenários
integrados históricos permanecem not-run. Não são promovidos a conformidade
por estes testes. Sem CI remota, release, leitor de tela real ou novo aceite UI.

Ensaios de desenvolvimento expuseram assert em label sem for durante recuperação,
e este foi corrigido com testes de raízes/tipos inválidos. A disposição nativa
de Diagnostics foi medida por IR como 40 bytes; não se adotou a hipótese de 32.
Inicialmente a suíte importou testes históricos com perfil safe indevido e um
coletor imprimiu Unicode com codificação local: os harnesses foram corrigidos
e a evidência final reexecutada. Uma revisão automática atingiu limite de uso
antes de executar o último teste de cancelamento; após continuação do usuário,
a execução autorizada passou. Nenhuma recusa foi contornada.

Comandos principais, com ASSIS_BIN apontando ao candidato novo de cada host:

```text
gcc <flags C11/O2 do host> src/assisc.c -o build/assis[.exe]
python tools/collect-htdl-catalog-evidence.py
python tools/collect-htdl-catalog-extra.py [--baseline <copia-base>] [--editor]
python tools/validate-examples.py --output <evidencia>/<host>-examples.json
python tools/check-ecosystem-references.py --output <evidencia>/reference-integrity.json
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/prepare-page-sdk.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-htdl-catalog-evidence.py --write
python tools/verify-htdl-catalog-evidence.py
git diff --check
```

A validação da instalação offline usa distribuição isolada e binários próprios;
resultado e comandos ficam no adendo/evidência abaixo. Nenhum prefixo do usuário,
PATH, associação, binário rastreado ou pacote de release é promovido.

## Arquivos e limites

Núcleo: stdlib/htdl.assis, catálogo e exemplo 52. Driver/corpus e suíte de
catálogo preservam os arquivos bootstrap congelados. Editor: tools/htdl-check.assis,
src/htdl.js da extensão, assis-lsp.js, extension.js, package/gramática/configuração
HTDL e testes. Ferramentas de coleta/verificação, instaladores/manifestos,
contrato e relatório completam a unidade. Inventário exato no diff/publicação.

Não há suporte visual para os novos controles, ações padrão, envio/validação
de form, scripts vinculados, resource loader, SDK mutável/strings/subscriptions,
FS/SSC ou parser URL. Recuperação sintática geral e identidade incremental
continuam abertas. Perfis de execução/sandbox anteriores são preservados; esta
unidade não reexecuta os oráculos LPAC/seccomp completos nem aprova G2.

Fila integral preservada: catálogo no Reader, desktop/leitor real/DPI/monitores,
shaping/bidi/edição/IME, quota agregada shell/Reader/RSS e disco/perfis órfãos,
macOS/ARM, SDK/HTDL/editor/loader/FS/SSC/recursos, rede/broker/perfis/cookies/cache,
persistência/índice multidocumento/crawler/serviço, M4–M9, distribuição, 24h reais
e aceite por terceiro. Easy por último. 43,30% não mede prazo ou prontidão.

Próxima unidade: recuperação de múltiplos erros sintáticos e identidade do
editor, seguida da ligação do catálogo a controles/árvore acessível e loader
transacional. Aceites de desktop e quota agregada continuam com contratos próprios.

## Publicação

Destino autorizado pelo masterprompt: **Vibe-O-Coder/AssisScript**, branch
**work/m3-htdl-catalog-2026-11-02**, sobre a base f00d1ff. Commit, SHA remoto,
inventário e resultado da PR serão registrados no adendo após verificação.
Nenhum commit local ou pedido de push é tratado como publicação concluída.
Hash do próprio relatório será obtido pelo histórico, sem autorreferência.

## Adendo — instalação e artefato isolados

Instalador Windows reconstruído com os **657 caminhos** do manifesto desta
unidade; **23 testes Node aprovados** em distribuição/prefixos temporários.
[Resultado e hashes](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/windows-node.json).
No Linux, instalação offline com `--with htdl`, fechamento das dependências,
compilação/execução do checker instalado e desinstalação foram executadas.
O binário instalado e os arquivos novos tinham hashes idênticos aos candidatos;
arquivo do usuário foi preservado e os dois arquivos gerenciados novos removidos.
[Resultado](../ecossistema/evidencias/m3-htdl-catalog-2026-11-02/linux-installed-checker.json).

VSIX criado somente em build/catalog-distribution, com os compiladores novos
Windows/Linux, sem promoção. Arquivo foi aberto para comparar paths/blobs,
verificar ausência de duplicatas e presença de configuração/gramática/helper/stdlib.
Após extrair, seu próprio compilador executou o checker e seu adaptador JS
resolveu a ferramenta corretamente: `0 0` e `[]`. Hash do VSIX e dos seis
arquivos relevantes em windows-node.json/vsix. Não houve instalação do VS Code
interativo nem publicação do pacote. Comandos adicionais reproduzíveis:

```text
python tools/stage-resource-budget-installer.py --evidence-dir docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02 --stage-dir build/catalog-distribution
python tools/verify-htdl-catalog-vsix.py
# No Linux, ASSIS_BIN aponta ao compilador Linux novo:
python3 tools/verify-htdl-catalog-install.py
```

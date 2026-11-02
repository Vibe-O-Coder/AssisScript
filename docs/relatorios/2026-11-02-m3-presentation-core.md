# Relatório — núcleo local FluxStyle e SSC finito

**02/11/2026, America/Fortaleza. Avaliação local 43,30% → 44,90%; 0/5 → 0/5 gates.**
Meta 50% não atingida. E08-01 0→2 e E08-03 0→2, +0,80 por critério; fundações
M3/M4, sem encerrar marco. E00-01/E00-04/E08-04/E11-01 recebem evidência sem
promoção. Pesos, aceites, cinco gates e baseline congelada permanecem iguais;
histórico recebe retrato completo dos 60 estados. Nenhum nível 4 ou gate novo.
**Publicação desta unidade pendente de autorização**, conforme seção final.

## Base e problema

Base **6701d1b6d67687144606c03e2431c0f5a6ddf313**, recuperação sintática HTDL
testada nesta sessão e agora publicada após autorização explícita do usuário.
O bloqueio inicial de revisão automática foi resolvido para esse commit exato;
git ls-remote/fetch e o conector conferiram o SHA, 38 paths/blobs/modos e 2364
entradas da árvore completa. Base ancestral pública 5fad34e foi conferida no início.
[Relatório e confirmação da unidade anterior](2026-11-02-m3-htdl-recovery.md).

Cópia isolada: **C:/Users/babus/Desktop/AssisScript/work/htdl-recovery-20261102**,
branch **work/m3-presentation-core-2026-11-02**. Original e trabalho alheio preservados.
Nenhum subagente, reset, limpeza de outras cópias, merge, force push ou release.
Planos, fila, régua, baseline, contratos e rascunhos congelados 10/11/12/14/16/17
orientaram o perfil. Easy continua como última etapa.

Antes não existiam frontend/avaliador FS ou parser/canais SSC nesta linhagem;
o import das novas bibliotecas era inexistente. O instalador já tinha 31
bibliotecas opcionais e o gerador recusava a 32ª para evitar shift indefinido
do mask unsigned. Isso bloquearia a distribuição do novo núcleo.

A reprodução com o compilador da base pública retorna A001 para ambos os imports;
o candidato atual aceita os mesmos fontes. Fonte, comandos, saídas e hashes dos
compiladores ficam no campo import_reproduction da evidência Windows. Nenhum
binário histórico foi usado como candidato da matriz final.

Agora há dois módulos reais em AssisScript, sem shim, nova sintaxe da linguagem,
engine externo, thread, GC ou JIT. [Contrato versionado e limites](../ecossistema/PERFIL-APRESENTACAO-LOCAL-V1.md).

## Implementação e decisões

**FluxStyle:** parser de flow/input/let/bind com spans e limites; nomes forward,
grafo de dependências e rejeição de ciclos inclusive em ramos inativos; tipos,
unidades, enumerações, quinze propriedades e domínios; choose/&&/|| curtos;
produtor único por nó/propriedade e bind idempotente, sem cascata. Estado usa
schema consistente e um valor por chave/escopo. Checked/disabled vêm da árvore
atual; demais entradas requerem dados tipados do host. Fonte FS não acessa FFI,
recursos, relógio, rede ou geometria final. APIs/identificadores em inglês.

Q16.16 público com intermediários int64 checados, arredondamento explícito e
time canônico em segundos: 4Hz*500ms é 2, não 2000. Produto/divisão têm empate
para +infinito; conversão de literal tem empate afastando de zero. Não se
confunde a semântica modular do AssisScript com o perfil numérico checado.
Style copia todas as saídas do nó após validar o candidato; erro conserva a
versão anterior. Não é transação de página inteira nem dirtiness entre chamadas.

**SSC:** gramática motion/spring/bind, argumentos em qualquer ordem, dois eixos,
produtor único e exigência de produtor FS explícito. Perfil experimental
**ssc-grid-42-q16-v1**, sete frequências × seis razões. Fora da grade é S402,
inclusive parâmetros dentro das faixas gerais do rascunho. Nenhum gerador de
coeficientes em runtime ou afirmação de cobertura contínua.

Gerador offline usa Decimal a 90/110 dígitos e confronta a fórmula binary64 do
snapshot, com concordância dos 42 vetores. Matriz 4Hz/0.8 é exatamente
[64251,461,-290983,45727]. Integração inteira em 1/120 s, teto oito passos por
chamada, descarte real de atraso, repouso de três passos, retarget contínuo,
pausa de aba, reexibição de nó no destino, proteção de foco/edição e reduced
motion. O host fornece tempo/políticas e calcula ancestrais protegidos.

Motion conserva NodeId e versão do Style, confere a árvore antes de avançar
e fecha em navegação/remoção. Produtos físicos verificam int64; posição pública
tem guarda. Destino válido fora de ±4096px ou falha de passo aplica destino
direto e informa S401. Destino não representável é recusado. Esse fallback não
prova precisão/estabilidade global ou tolerância em toda sequência de destinos.

**Distribuição:** seleção Windows e dependências usam uint64_t/UINT64_C até
63 opcionais, com assert de compilação e recusa do gerador antes de escrever
em caso de 64. As duas novas opcionais ocupam índices 31/32, com dependências
canônicas. Catálogo, shell, manifestos Windows, documentação e alvo Makefile
sincronizados. Não se promove binário rastreado, VSIX ou pacote de release.
CI Windows/Linux x64 foi ampliada para as novas suítes e os verificadores de
coeficientes/régua; Windows passa a incluir também o teste nativo de editor HTDL.
Essa configuração está preparada, mas não foi executada no GitHub por publicação bloqueada.

## Evidência desta revisão

[Resumo e hashes](../ecossistema/evidencias/m3-presentation-core-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m3-presentation-core-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m3-presentation-core-2026-11-02/linux.json).

| Suíte de métodos | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| FluxStyle, otimizado e referência | 17/0 | 17/0 |
| SanSCript, otimizado e referência | 9/0 | 9/0 |
| Mask nativo 31/32/33/63 e recusa 64 | 2/0 | 2/0 |
| **Total novo nativo** | **28/0** | **28/0** |
| Distribuição/editor Node Windows | **23/0** | **not-run: Node indisponível** |

Testes FS usam Fraction com inteiros ilimitados: 244 vetores de operações e
65 literais determinísticos, seeds 2026110202/03. Verificam avaliação curta,
resolução forward, tipos de ramos inativos, ciclos, conflitos entre id/classe,
domínios, estado compartilhado, fonte host, quotas, profundidade, rollback,
retry, versão antiga, identidade revogada e recusa real de alocação do OS.
O card.fxs e casos congelados são executados como fonte, sem alterar a referência.

SSC executa **42 × 360 passos por modo/host**. Posições e repouso coincidem
bit a bit com a emulação congelada; os hashes das trajetórias coincidem entre
Windows e Linux. A comparação com solução analítica tem escopo limitado a
degrau de **8px por três segundos**; maior erro registrado nos arquivos de
[Windows](../ecossistema/evidencias/m3-presentation-core-2026-11-02/windows-ssc-traces.json)
e [Linux](../ecossistema/evidencias/m3-presentation-core-2026-11-02/linux-ssc-traces.json),
abaixo de 1/16px apenas nesse ensaio. Não se extrapola essa tolerância.
Há testes de pausa/proteção/reexibição, descarte de atraso, reduced motion,
continuidade de retarget, produtor ausente, conflito, parâmetros fora da grade,
OOM real, avanço sem alocação, encerramento e identidade antiga.

Ambas as bibliotecas geram cinco formatos em otimizado e referência com
astFallbacks=0. Somente Windows x64 e Linux x64/WSL2 foram executados; ARM/macOS
continuam not-run. **56/56 exemplos por host** e duas terminações RPG por host.
Exemplo 54 executado em cada modo/host: `FLOW-TARGET -524288` e
`SSC-REST -524288 true`. É pipeline local de dados, sem janela/captura visual.

Instaladores próprios Windows e shell Linux selecionam sanscript e o fechamento
de oito opcionais, conferem hashes de todas as bibliotecas instaladas, executam
o exemplo do prefixo com espaços e removem arquivos geridos preservando arquivo
pessoal. Node Windows reexecuta 23 métodos, incluindo minimal/full/seleções
anteriores, novos bits 31/32 e programas instalados. Sem PATH/associações/registro
de perfil do usuário. [Windows](../ecossistema/evidencias/m3-presentation-core-2026-11-02/windows-install.json),
[Linux](../ecossistema/evidencias/m3-presentation-core-2026-11-02/linux-install.json).
Integridade de 57 arquivos congelados passou; 16 cenários integrados históricos
continuam not-run. Sem CI remota, novo soak de 24h ou aceite desktop/leitor/IME.

Comandos principais, com ASSIS_BIN no candidato próprio de cada host:

```text
python tools/generate-ssc-coefficients.py --check
python tools/collect-presentation-core-evidence.py
python tools/validate-examples.py --output <evidência>/<host>-examples.json
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
python tools/verify-presentation-install.py
python tools/check-ecosystem-references.py --output <evidência>/reference-integrity.json
python tools/prepare-page-sdk.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-presentation-core-evidence.py --write
python tools/verify-presentation-core-evidence.py
git diff --check
```

Ensaios de desenvolvimento corrigiram a classificação de literal científico
inválido e fixaram unidade base de time antes da matriz final. A revisão de
contexto acrescentou restrições de disabled/checked e textScale/largura do pai;
as suítes finais foram reexecutadas após essas alterações. Não se contam os
ensaios falhos como passes. Os testes de instalação final usam seu próprio
compilador/instalador, não o binário rastreado de uma versão anterior.

## Limites e próximo incremento

Há reavaliação do grafo por chamada e memoização local, não dirtiness entre
transações. Style e Motion são por nó; faltam transação da página inteira,
quota agregada de canais/RSS, integração de layout e um snapshot comum para
desenho/hit test/acessibilidade. Os leitores atuais continuam no bootstrap.
Avisos de bind sem correspondência e inspector/LSP FS/SSC não foram entregues.
O schema de estado local é conservador por recurso, mais estrito em flows
sem interseção. O perfil SSC é uma grade finita, não os contínuos do rascunho.

Fila integral preservada: identidade incremental/editor; catálogo no Reader;
desktop/leitor real/DPI/monitores, shaping/bidi/edição/IME; SDK/strings/eventos;
loader HTDL/código/FS/SSC/recursos/versões; semântica/estilo da página inteira;
quota agregada/RSS/disco/perfis órfãos; macOS/ARM; rede/broker/perfis/cookies/
cache; persistência/banco/crawler/índice/serviço; M4–M9, corpus visual, 24h reais,
distribuição/terceiro e gates. **Easy permanece por último.**

Próximo incremento recomendado: snapshot de apresentação da página inteira,
quota agregada e ligação ao layout/Reader, preservando os aceites de desktop
e catálogo que ainda faltam. Não ampliar HTML/URL/execução remota por estes módulos.

## Publicação da base confirmada; autorização do novo commit pendente

O push da unidade anterior, commit 6701d1b (38 arquivos), foi inicialmente
recusado pela revisão automática por exigir autorização explícita do usuário
para o conteúdo/destino. O usuário autorizou esse commit exato; publicação e
verificação concluídas. PR não criada: conector 403 Resource not accessible by
integration. Não houve contorno por API/credencial, merge ou force push.
O novo núcleo tem payload separado e permanece local, pronto para aprovação.

Entrega pronta para revisão em Vibe-O-Coder/AssisScript, branch de trabalho
work/m3-presentation-core-2026-11-02, sem merge/force push/release. O histórico Git
identifica o SHA deste relatório e o inventário/patch local preserva os arquivos.
Pendente: autorização explícita para publicar o novo commit FS/SSC e seus
relatórios/evidências; depois, conferir SHA/paths/blobs no remoto. A recuperação
HTDL já está publicada e não precisa de nova autorização.

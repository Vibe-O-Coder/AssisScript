# Relatório — layout comum, composição atômica e instalador de desenvolvimento

02/11/2026, America/Fortaleza. Base pública confirmada pelo conector:
542827e43143c94a977d26e116308036cefc7f1d. Branch local
work/m5-page-layout-2026-11-02, cópia isolada
C:/Users/babus/Desktop/AssisScript/work/page-layout-20261102.

**45,30% → 45,70% local, 0/5 gates. Meta 50% pendente.**
E08-02 2→3 (+0,40). E02-03/E04-03/E07-02/E08-04/E11-01 recebem evidência
sem promoção. Baseline, pesos, aceites, história anterior e gates preservados;
o novo retrato contém os 60 níveis e cinco gates. M5 continua parcial.

**Estado local: implementação e pacote de desenvolvimento validados.** A falha
de revisão por limite de uso foi resolvida e todas as verificações pendentes
executaram. Publicação será confirmada no adendo; sem merge, release, nova CI
remota afirmada ou alteração da instalação global.

## Problema e mudança

Flowpage confirmava saídas FS, mas faltava uma geometria comum de desenho,
hit test e acessibilidade. [pageframe](../BIBLIOTECA-pageframe.md) agora constrói
um snapshot proprietário em AssisScript: restrições horizontais descendentes,
alturas automáticas ascendentes, row/column/block, padding/gap/alinhamento,
quebra por grafemas Unicode 17, escala de texto uma vez, offsets e recortes.
Não há realimentação da geometria final em FS. parent.availableWidth continua
entrada do host; este módulo consome o conjunto autoral já confirmado.

[pagepresent](../BIBLIOTECA-pagepresent.md) produz comandos e projeção MSAA
a partir desse mesmo Frame. O provider Windows prepara outra superfície e
a cópia acessível; sucesso publica ambas, falha preserva ambas. A adaptação C
faz fonte/raster/COM; a lógica de layout, ordem, semântica e políticas permanece
em AssisScript. A extensão frame 1 é aditiva, sem mudar ABI/imports anteriores.

Disabled/hidden/remoção atuais vencem saídas FS antigas. Uma falha FS conserva
as últimas saídas válidas nos nós sobreviventes e o Frame usa a semântica atual.
Novo documento não herda styleVersion. Falha do motor exige bloquear interação.
Snapshots, ações acessíveis e gestos antigos não se transferem para nova
projeção/geração; até um Packet anterior ainda vivo consulta se continua atual.
Tab segue a ordem semântica, enquanto sobreposição visual controla hit test.

Exemplo 56 executa dois painéis sem provider; 57 apresenta uma janela real,
permite Tab/Enter/Space/ponteiro/resize e oferece --once para smoke automático.
O par Frame/Packet só muda após commit nativo. Apresentação física é uma chamada
posterior: falha do OS/resize não recebe promessa de rollback perfeito de pixels.

## Reprodução do problema de instalação informado pelo usuário

O erro `owned.assis:50:44: esperado ;; encontrado ArrayNode` não é um ponto e
vírgula ausente. O executável antigo não reconhece try_new. A comparação de
SHA-256 confirmou que o assis encontrado no PATH e bin/assis.exe do checkout
eram idênticos: c519e591eacb52f87593064879e93b98f12de69218e09acd79a821cb30d9e4c5.
O candidato novo validado tem SHA-256
8e89ae09a3a47e75e21e18edba8c8db9b48b9b009f2f5a57898dab53e256925f.

O instalador histórico pode copiar bibliotecas atuais junto com esse binário
antigo. Atualizar fontes ou usar -I não atualiza o parser do executável.
O catálogo instalado já continha os novos módulos, reforçando a mistura.
[Diagnóstico rastreado](../ecossistema/evidencias/m5-page-frame-2026-11-02/installed-compiler-diagnosis.json).

O usuário havia retirado std/ de imports em 23 arquivos para tentar contornar
o erro. Essas cópias foram preservadas em build/user-import-workaround-20261102,
com RESTORED.json; somente os imports canônicos foram restaurados. Alterações
de implementação não foram descartadas. A pasta original antiga/suja permanece
preservada, sem reset, limpeza, troca de branch ou subagentes.

`tools/prepare-development-installer.py` prepara um pacote Windows separado:
reconstrói o compilador e exige o hash da matriz nativa aprovada, reconstrói o
provider e instalador, inclui bibliotecas/catálogo/exemplos coerentes, DLL,
BUILD-INFO.json e hashes. O manifesto privado inclui a DLL na instalação e
remoção. Binários históricos, pacote de release, PATH e instalação global
não são promovidos ou modificados.

O wrapper instalar-windows.cmd passa a recusar a cópia Git de desenvolvimento,
com orientação ao pacote preparado, evitando repetir silenciosamente a mistura.
O wrapper do pacote completo continua instalando normalmente. O novo pacote
é de desenvolvimento, com **instalação isolada validada**, sem promover release.
A validação padrão do preparador instalou em
prefixo temporário com espaços, confere hashes, executa exemplos sem janela
e com --once e removeu preservando arquivo pessoal. O wrapper da cópia Git
foi executado com --help: recusou o binário histórico com diagnóstico e código 2.

## Evidência nativa concluída

[Resumo parcial e hashes](../ecossistema/evidencias/m5-page-frame-2026-11-02/summary.json),
[Windows](../ecossistema/evidencias/m5-page-frame-2026-11-02/windows.json),
[Linux](../ecossistema/evidencias/m5-page-frame-2026-11-02/linux.json).

| Suíte | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| Frame novo | 17/0 | 17/0 |
| Composição nova | 6/0 | 2/4 |
| Página FS | 17/0 | 17/0 |
| FluxStyle | 17/0 | 17/0 |
| SSC finito | 9/0 | 9/0 |
| Memória de documento | 12/0 | 12/0 |
| Parser HTDL | 16/0 | 16/0 |
| Reader | 10/0 | 7/3 |
| Transações Reader | 15/0 | 11/4 |
| **Total** | **119/0** | **108/11** |

Cada suíte usa otimizado/referência conforme seu contrato. A nova matriz gera
os cinco formatos nos dois modos e confere astFallbacks=0 para os dois exemplos.
Geração ARM/macOS não é execução nativa. Windows 10 x64 19045 e Linux x64/WSL2
foram executados; versões, duração, comando, compilador e SHA de cada log estão
nos JSONs. Os 11 not-run Linux dependem de provider gráfico e não são passes.

Modelos de pilha de retângulos independentes com seed 2026110205 verificam
row/column, dimensões e gaps; casos adicionais cobrem restrições aninhadas,
offset sem afetar fluxo, interseção, zoom não cumulativo, grafemas indivisíveis,
foco/ordem/sobreposição, disabled e erro FS, remoção/navegação, nomes próprios,
limites e recusa real do alocador sem derrubar quadro/vizinho. O provider testa
recusa em todas as fronteiras de alocação do commit, pixels/objeto acessível
anteriores e contagem GDI sem aumento; projeção inválida após raster válido,
UTF-8/recortes hostis e versões antigas são recusados.

O exemplo 56 executou em ambos os modos/hosts: FRAME 8 4 1 1 / LEFT 8 28 104 16.
A janela 57 publicou/fechou com --once nos dois modos Windows: FRAME 1 10.
Métricas GDI reais a 100/200% alimentaram layout e desenho na integração nativa.
Isso não é aceite por leitor de tela, DPI do OS ou inspeção visual de desktop.

Computer Use foi inicializado conforme a skill. O lançamento não expôs janela
alvo e a nova listagem não continha o aplicativo; não houve screenshot/input.
Essa tentativa permanece not-run, sem transformar smoke nativo em aceite visual.

Integridade dos 57 arquivos de referência passou; os 16 cenários históricos
de conformidade integrada continuam not-run. SDK embutido e 42 coeficientes SSC
passaram nas verificações documentais próprias, sem nova alegação de conformidade.

## Verificações finais e resolução do bloqueio temporário

A primeira chamada de validação dos 59 exemplos foi configurada por engano
com bin/assis.exe histórico: 29/59, com erros de sintaxe nova. Não é contada
como matriz do candidato. O JSON está identificado como historical-compiler.
A nova chamada explícita com build/assis.exe, e a chamada Linux equivalente,
foram recusadas **antes da execução** porque a revisão automática de permissões
não pôde terminar por limite de uso da conta. A mensagem declara que isso é
falha da revisão, não determinação de que a ação é insegura. Não houve contorno
dessas execuções negadas por outro transporte.

O mecanismo de revisão voltou a funcionar. As mesmas chamadas foram
reapresentadas ao controle de permissões, sem contorno. Os **59/59 exemplos
passaram por host**, incluindo os dois finais do RPG. Instalação, execução e
remoção isoladas Windows/Linux passaram; fechamento das 14 dependências e
hashes foram conferidos. Windows também executou **4 testes de locks do
instalador e 23 Node**, todos aprovados. O pacote destinado ao usuário passou
na instalação isolada, executou 56 e 57 --once pelo compilador instalado e
removeu compilador/DLL preservando arquivo pessoal. BUILD-INFO.json e a evidência
registram installation_validation=pass. A preparação anterior com --prepare-only
é histórica, não o estado final do pacote. A publicação é confirmada no adendo.

Retomar com ASSIS_BIN explícito para o candidato próprio de cada host:

```text
python tools/validate-examples.py --output <evidência>/<host>-examples.json
python tools/generate-install-manifest.py
python tools/verify-pageframe-install.py
python tools/prepare-development-installer.py
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-pageframe-evidence.py --write
python tools/verify-pageframe-evidence.py
git diff --check
```

O verificador completo exige todos os itens e os hashes; a opção
--allow-incomplete só serviu ao retrato parcial durante o bloqueio histórico.
A conferência final usa o verificador completo. Publicar a branch autorizada
em Vibe-O-Coder/AssisScript e conferir SHA/árvore/paths/blobs/modos permanece
a etapa final até o adendo. O SHA deste relatório é obtido pelo histórico.

## Limites e fila integral

Somente catálogo visual bootstrap. Sem estilos inline mistos, radius/imagens,
scroll interno independente, layout intrínseco/subpixel geral ou avaliação
automática descendente de parent.availableWidth. Reservas de corpos solicitados
não são RSS/CPU/quota integral; fontes nativas não prometem igualdade de pixels
entre sistemas. A ponte acessível conserva projeção plana, sem novo TextPattern.

Próximo incremento funcional: SSC agregado e quota de canais coordenados ao
Frame, depois integração com seleção/Reader e loader. Também permanecem:
identidade incremental/editor, catálogo visual completo, desktop/leitor real/
DPI/monitores/shaping/bidi/IME, SDK/strings/eventos gerais, loader de HTDL/código/
FS/SSC/recursos/versões, quota agregada/RSS/disco/perfis órfãos, macOS/ARM nativos,
rede/broker/perfis/cookies/cache, persistência/banco, crawler/índice/serviço de
busca, M4–M9, corpus visual, 24h reais, distribuição, terceiro e cinco gates.
Nenhum requisito foi dispensado para aproximar 50%. **Easy por último.**

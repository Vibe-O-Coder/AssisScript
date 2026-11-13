# M3 e M5 — Revalidação de leitura, formulários e SSC

12/11/2026, Windows x64. Base pública `13e81a897388e694d9a02bcfb4b3984665d7c3c9`,
branch `work/ecosystem-2026-11-12`. E04-02/05 e E08-02/05 recebem evidência,
com os mesmos níveis e 0/5 gates. Esta unidade reexecuta a interface da base
junto à [rodada de busca](2026-11-12-m8-servico-busca-local.md).

## Rasters nativos

`python tools/check-frame-visual.py --output build/session/visual` produziu
oito rasters GDI nos dois modos. Os bytes de cada imagem coincidem entre
os modos e com o corpus da publicação anterior. As superfícies verificadas
mostram o contador em 0 e 10, a seleção de leitura a 200%, o deslocamento de
um painel mantendo os pixels do outro e o formulário desmarcado, marcado
e validado a 200%. A medição é do cliente GDI instrumentado.
[Hashes da repetição](../ecossistema/evidencias/search-transport-segments-2026-11-12/visual.json) ·
[Leitura](../ecossistema/evidencias/ecosystem-2026-11-12/reading-200.png) ·
[Painéis](../ecossistema/evidencias/ecosystem-2026-11-12/panels-moved.png) ·
[Formulário](../ecossistema/evidencias/ecosystem-2026-11-12/forms-200.png).

## Janela real

O Computer Use abriu as janelas de formulário e catálogo. A árvore
acessível do formulário expôs documento, grupo, checkbox, rótulo e botão.
Tab focou o checkbox, Espaço foi enviado, Tab focou Validar e Enter foi
enviado. No catálogo foram observados o link, a lista e os itens. Tab
focou o link e Enter foi enviado. A mudança do valor e o rodapé de
validação são verificados pelo oráculo de raster e pelos testes nativos.

As quatro tentativas de captura das duas janelas expiraram, incluindo
`FrameArrived timed out` e `window capture timed out`. A tentativa de
abrir SSC expirou na aprovação da aplicação. A repetição retornou
`launched app did not expose a targetable window`. A demonstração SSC
abriu no teste nativo que produziu o raster. Ao detectar entrada do
usuário na janela do catálogo, o Computer Use encerrou a sequência de
entradas. [Registro do desktop](../ecossistema/evidencias/search-transport-segments-2026-11-12/desktop.json).

O aceite de leitor de tela real, DPI do sistema, monitores, IME e fluidez
SSC percebida continua pendente. O zoom ensaiado é de texto. O próximo
incremento M3 continua sendo a edição de texto/número por nó, com
integração IME, imagens, importação HTML e regiões de anúncio na fila.
[Aceites e dependências](../ecossistema/FILA-M0-M1.md).

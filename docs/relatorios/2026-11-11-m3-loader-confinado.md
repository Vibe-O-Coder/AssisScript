# Loader confinado e inspeção visual do Frame

11/11/2026, America/Fortaleza. Base publicada
`592255811b447ab9ea918c32e371384167e30c4d`, conferida com `git ls-remote`.
Branch `work/m3-confined-loader-2026-11-11`, cópia limpa
`work/confined-loader-20261111`. A base inclui a entrada tipada de 11/11,
os recursos locais de 04/11 e o catálogo de leitura de 03/11.

O shell antes precisava fornecer um caminho absoluto para cada arquivo.
Agora escolhe uma raiz local e carrega `resources.assr`. O manifesto declara
HTDL, FS, SSC, fonte ou ASV2 e dados opcionais. A lógica de plano, identidade,
cotas, prazo, cancelamento e entrega é AssisScript. O provider existente do
worker ganha quatro símbolos para abrir, consultar e revogar a concessão
nativa. A associação final reaproveita o commit conjunto do Frame e worker.
[Contrato e exemplo](../BIBLIOTECA-localresources.md).

## Confinamento e rollback

- O Linux abre sob a raiz por `openat2` e fixa o inode antes de ler. Windows
  abre os componentes relativamente ao handle de diretório e confere nome,
  tipo e atributos após a abertura. A extensão recusa links, reparse points,
  hardlinks múltiplos e arquivos especiais. Chaves são ASCII canônico. O
  diretório concedido aceita UTF-8, inclusive acentos e espaços.
- A entrega verifica o limite do tipo e o orçamento restante antes de ler
  o payload. Uma leitura fora do prazo, um arquivo alterado ou uma declaração
  inválida descarta o candidato. O oráculo troca um diretório válido por um
  link durante 400 leituras e verifica que nenhum byte do vizinho é entregue.
- A prova integra manifesto em CRLF, dados com NUL e ASV2 restrito. A ativação
  real ocorre em Windows e Linux x64. Arquivo faltante e FS inválido conservam
  o Frame, o documento e o worker ativos. O exemplo 69 recompila a variante de
  fonte. Cancelamento ocorre entre leituras síncronas. As capturas de vários
  arquivos refletem o instante de leitura de cada arquivo.

## Inspeção Windows

O Computer Use expirou na primeira abertura e não retornou janela alvo para
o candidato reconstruído. As demos abriram e fecharam em testes nativos.
O [oráculo visual](../../tools/check-frame-visual.py) obteve cinco rasters
do cliente GDI pelo provider de teste. Os pixels do host otimizado e
`--no-opt` coincidiram com o mesmo worker. A inspeção revelou palavras cortadas, corrigidas
no `pageframe` com preferência por espaço. O `framereader` recompõe o espaço
para preservar o texto copiado e a seleção durante o reflow.

- Dez eventos de Enter alteraram apenas o rodapé do contador, de 0 para 10.
  A seleção sobreviveu ao zoom de fonte a 200% e o contador permaneceu em 10.
  [Leitura a 200%](../ecossistema/evidencias/loader-http-2026-11-11/reading-200.png).
- O painel esquerdo deslocou-se após quatro passos de 25 ms. O painel direito
  conservou seus pixels. As frases passam para a próxima linha em espaços
  quando há uma quebra possível. [Painéis antes](../ecossistema/evidencias/loader-http-2026-11-11/panels-initial.png)
  e [depois](../ecossistema/evidencias/loader-http-2026-11-11/panels-moved.png).

Os rasters registram a superfície do aplicativo. Fluidez percebida no desktop,
anúncios de leitor de tela real, DPI do sistema, troca entre monitores, IME e
aceite humano continuam pendentes. Os testes de Frame e MSAA automatizados
continuam com seus próprios resultados. [Matriz e hashes](../ecossistema/evidencias/loader-http-2026-11-11/).

**48,30% → 48,80%, 0/5 gates.** E03-01 passa de 1 para 2 pela leitura física
relativa, Unicode na raiz, links, corrida e revogação demonstrados nos dois
hosts. E07-05, E08-02 e E08-05 recebem evidência adicional. A fila mantém
controles, imagens, live regions, SDK geral e os aceites integrais.
A publicação desta unidade segue na branch acima junto às demais mudanças.

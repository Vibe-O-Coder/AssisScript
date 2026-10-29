# Continuação — 3.3.0-alpha.16

Data: 28/10/2026. Base: 3.3.0-alpha.15 com alterações locais preservadas.

## Auditoria desta continuação

Os documentos de plano, restante para 100%, progresso, backend e validação da
alpha.15 foram lidos em conjunto com a árvore atual. O estado verificável
permanece em **94/100 pontos**. Não foi atribuído crédito artificial aos gates
que exigem outro sistema, outra pessoa ou decisão de procedência.

## Validação reproduzida

`tools/report-progress.py --check` passou e confirmou 94% / 94,0 pontos.
Uma execução direta de `tests/test-backend-evolution.py` não alcançou a fase
semântica: os 10 casos falharam ao escrever `main.assis` em diretórios
temporários, com `PermissionError [WinError 5]`, e a limpeza posterior recebeu
o mesmo bloqueio. A repetição com `TEMP` e `TMP` apontando para `build/test-temp`
reproduziu exatamente o comportamento. Um `assis check` direto em arquivo dentro
de `build` passou, portanto o resultado não deve ser classificado como
regressão do compilador.

Esse bloqueio deve ser resolvido no ambiente/harness antes de usar a suíte como
evidência para qualquer avanço de P5-IR. Não se deve relaxar a validação nem
marcar testes não executados como aprovados.

**Revalidação para publicação de testes, 28/10/2026:** a mesma suíte foi
reexecutada com acesso normal à pasta temporária do Windows, fora das restrições
do executor anterior. Os 10 testes passaram. Isso resolve o bloqueio observado
nessa execução; não exigiu mudança no compilador. Não houve avanço de P5-IR.

## Pendências que continuam abertas

### Informações adicionais recebidas em 28/10/2026

O responsável esclareceu que as imagens são stickers da comunidade com autores
não identificados. Foi criada uma [proposta vetorial](IDENTIDADE-VISUAL-PROPOSTA.md)
para substituir essa dependência visual; os ícones ativos e pacotes ainda não
foram trocados. A revisão dos demais termos de distribuição continua aberta.

Também relatou download e uso em outros computadores Windows/Linux. Esclareceu
que escreveu e executou programas próprios: Hello World, função `dobrar()` e
arrays com `own`, `borrow` e funções `pure`, aproximadamente na alpha.6 segundo
sua lembrança. O [registro do relato](ACEITE-RELATO-USUARIO-2026-10-28.md)
preserva essa evidência histórica e os dados ainda não fornecidos. A aceitação
da distribuição atual, depuração/distribuição A/B/C e uso por terceiro continuam
abertos. A pontuação permanece em 94/100.

- P5-IR: migrar instruções, recursos, endereços e condições para emissão pela
  IR tipada, mantendo equivalência com `--no-opt`.
- P5-TARGET: validar execução nativa ARM64 e macOS em hosts reais, incluindo
  runtime, depuração, instalador e CI.
- P6-POLICY: registrar autor/origem/permissão dos assets e fechar termos de
  redistribuição.
- P6-ACCEPT: terceiro instalar e usar a distribuição para compilar, testar e
  depurar A/B/C, registrando hash, sistema, passos e aceite.

## Próximo passo obrigatório

Os 10 testes backend foram confirmados na revalidação acima. O próximo passo
técnico é continuar a migração integral da IR com equivalência e casos adversos.
Os resultados da alpha.15 e o ensaio de 24 horas permanecem válidos conforme
`HANDOFF-3.3-ALPHA.15.md` e `VALIDACAO-ALPHA15.json`.

Publicação experimental autorizada pelo responsável no repositório existente,
pela branch `testing/alpha15`, com [guia de testes](TESTES-GITHUB.md). Esta
continuação não cria uma versão estável nem atribui aprovação remota antes do
resultado efetivo do GitHub Actions.

Preparação local da publicação: 10 testes de backend, 2 de documentação/avisos
e 41 de desenvolvimento/editor/LSP aprovados. O compilador Windows foi
reconstruído com bytes idênticos ao anterior; o instalador foi reconstruído com
manifesto de 263 arquivos, incluindo os quatro documentos novos. A alteração de
`src/install_files.inc` é posterior aos hashes da validação histórica alpha.15.
O pacote VSIX alpha.10 acrescentado pelo responsável ao GitHub foi preservado;
o guia distingue esse arquivo dos binários da branch de testes.

## Continuação: instruções escalares e validação de hosts

O responsável informou novamente sucesso nos testes em outras máquinas e
recomendou Actions para macOS/ARM64. A continuação está descrita em
[BACKEND-IR-CONTROL.md](BACKEND-IR-CONTROL.md): emissão IR de escritas locais e
condições escalares elegíveis, 16 regressões de backend, compilador hospedeiro
Linux/macOS ARM64 e jobs de saídas x86_64 via QEMU/Rosetta. Também corrige a
declaração oculta de `mkdtemp` que impediu o build macOS da execução anterior.
O novo relato reforça o sucesso informado, sem inventar arquitetura, versão ou
passos de teste não especificados. P5-IR permanece parcial, P5-TARGET pendente e
o total preserva 94/100. Próximo incremento: endereços, efeitos de memória e
cleanups explícitos antes de migrar integralmente o controle e o backend ARM64.

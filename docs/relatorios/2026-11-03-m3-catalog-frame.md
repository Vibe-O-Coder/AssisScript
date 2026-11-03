# Relatório — catálogo de leitura no Frame e fragmentos locais

03/11/2026, America/Fortaleza. Base pública
**6f4398c830fadde4d809bbbac104a1fa4f22c711**, conferida pelo conector GitHub.
Branch **work/m3-catalog-frame-2026-11-03**, cópia isolada
**C:/Users/babus/Desktop/AssisScript/work/catalog-frame-20261103**.
Pasta original antiga/suja e demais continuações preservadas. Sem reset,
limpeza, troca de branch alheia, merge, force push ou subagentes.

Unidade M3/M5 parcial: E00-01/E04-05/E07-02/E07-05/E08-02/E11-01.
**47,10% → 47,50%, 0/5 gates.** E07-02 2→3 (+0,40) pelo contrato
de árvore/consultas integrado ao catálogo de leitura, modelos de ordem/listas,
remoção/navegação e revogação no Frame/acessibilidade, com falhas adversas e
execução Windows/Linux x64. Os demais critérios recebem evidência sem promoção.
Histórico acrescenta retrato dos 60 estados e cinco gates; pesos e baseline preservados.
Meta 50% continua pendente e os cinco gates permanecem abertos.

## Problema e resultado

O parser estático já conhecia 23 tipos, mas o bundle visual só aceitava o
bootstrap. O perfil negociado `(2,1,1)` agora apresenta 18 tipos de leitura:
regiões estruturais, listas/itens e links por fragmento, além dos tipos
anteriores e metadados. `(1,1,1)` conserva a entrada bootstrap estrita.
O título é buscado pelo tipo, respeitando a ordem livre válida de head.

Layout, seleção, clips, hit test e projeção acessível recebem as mesmas caixas
compostas por FS/SSC. Marcadores são medidos antes dos filhos, com recuo próprio,
altura mínima e numeração dos irmãos visíveis. Não entram na cópia textual.
Listas aninhadas e números de um a três dígitos têm modelos independentes.

Links resolvem somente `#id` no mesmo documento/quadro; inline id aponta ao
bloco contêiner. A consulta retorna scroll limitado ou falha para destino
oculto/expirado. O host prepara/publica outro Frame explicitamente. Remoção,
navegação e requests antigos invalidam interação. Caminhos, HTTPS, scripts,
controles, imagens e live regions continuam recusados nesse perfil, inclusive
sob hidden. O teto de referências cobra oito milhões de bytes de fonte.

Enter passa a ativar no pressionamento, com bloqueio de repetição; Espaço ativa
botão na liberação e rola em link/documento. Gestos de teclado/ponteiro têm
origem separada. Reflow conserva Enter segurado para impedir clique duplicado.
Essa correção altera a expectativa antiga de Enter na liberação, alinhando o
Frame Reader ao contrato HTDL; o Reader anterior não foi alterado.

A ponte Windows ganha símbolos adicionais de catalog-reading 1. Os símbolos,
versões e papéis aceitos pelas ABIs anteriores permanecem. MSAA exporta grupos,
links, listas e itens em projeção plana; o hit escolhe o filho sobre a região
envolvente. As bibliotecas novas exigem a DLL correspondente, pois import
ausente pode falhar antes de main. Não há fallback que retire acessibilidade.

Toda a lógica de leitura/layout/navegação é AssisScript. O shim C só adapta
papéis, buffers, raster e COM do OS. Não foram alterados sintaxe, compilador,
semântica numérica ou licenças/dependências redistribuídas.

## Arquivos, contrato e exemplos

- stdlib/pageframe, framereader, framehost e pagepresent; provider frame/reader
  e header ABI; catálogo/manifestos/Makefile/CI.
- [Perfil local completo](../ecossistema/PERFIL-LEITURA-CATALOGO-V1.md) e
  documentação das quatro bibliotecas/ABIs.
- [Exemplo 62](../../exemplos/62_catalog_reader.assis), sem janela, e
  [exemplo 63](../../exemplos/63_catalog_reader_window.assis), janela com seleção,
  zoom e ativação de fragmento. --once/--smoke apresentam e fecham.
- [Suíte nativa](../../tests/test-catalog-frame.py) e
  [oráculo COM independente](../../tests/catalog_frame_oracle.c).
- Coletores/verificadores e preparação de pacote Windows com `--profile catalog`.

## Validação rastreada

[Resumo e hashes](../ecossistema/evidencias/m3-catalog-frame-2026-11-03/summary.json),
[Windows](../ecossistema/evidencias/m3-catalog-frame-2026-11-03/windows.json),
[Linux](../ecossistema/evidencias/m3-catalog-frame-2026-11-03/linux.json).
Os arquivos registram comando, SO/Python, duração, hash do compilador e logs.
Otimizado/referência executam os mesmos casos. Gerar cinco formatos é distinto
de execução nativa Windows/Linux x64; ARM/macOS não foram executados.

| Suíte | Windows executados/not-run | Linux executados/not-run |
| --- | ---: | ---: |
| htdl-catalog | 16/0 | 16/0 |
| framereader | 14/0 | 13/1 |
| framehost | 12/0 | 10/2 |
| motionpage | 14/0 | 14/0 |
| pagepresent | 9/0 | 3/6 |
| flowpage | 17/0 | 17/0 |
| fluxstyle | 17/0 | 17/0 |
| sanscript | 9/0 | 9/0 |
| document-memory | 12/0 | 12/0 |
| htdl-parser | 16/0 | 16/0 |
| htdl-reader | 10/0 | 7/3 |
| reader-transactions | 15/0 | 11/4 |
| catalog-frame | 21/0 | 18/3 |
| pageframe | 17/0 | 17/0 |
| **Total** | **199/0** | **180/19** |

**65/65 exemplos por host**, finais vitória/derrota do RPG, instalação/execução/
remoção isoladas em ambos e fechamento de **18 bibliotecas**. Windows executa
também **4 testes de locks e 23 Node**, com DLL reconstruída e verificada por hash.
O pacote Windows de desenvolvimento reconstrói compilador/provider/instalador,
instala em prefixo com espaços, executa exemplos headless/janela e remove,
conservando arquivo pessoal. Não é release ou instalação global.
Arquivo local: `build/AssisScript-catalog-development-20261103-windows-x64.zip`.
A matriz integral precedeu a correção final do recorte; as suítes catalog-frame
e pageframe foram reexecutadas nos dois hosts após essa mudança.
57 referências congeladas têm integridade conferida; os 16 cenários integrais
da referência permanecem not-run e não são contados como conformidade.

A revisão final encontrou um recorte de item que descontava duas vezes o espaço
do marcador. Foi corrigido e ganhou teste específico do retângulo interno antes
da composição, sem cortar a área reservada aos filhos.

O modelo de listas usa pilha/retângulos monoespaçados explícitos, uma seed fixa
de itens ocultos e 104 ordinais. O modelo de texto compara os bytes esperados
sem derivá-los dos runs do produto. O oráculo C verifica papéis MSAA pelas
constantes independentes do Windows, nomes, ações, foco, localização/hit,
revogação COM e conservação de recursos em cada falha nativa do commit testado.
Entradas de versão, alvo inexistente/oculto, fronteiras de requests, semântica
mutada, leitura antiga e fontes fora do perfil têm rejeições próprias.

Recusa real de alocação do OS com suprimentos 0/1/2/4/8 conserva ativo e vizinho;
suprimento suficiente pode completar, seguido por abort. Esse teste não significa
injeção em cada alocação lógica. Há também publicação nativa recusada, retry,
ações acessíveis e limpeza de recursos. Esses tetos não são quota de RSS.

A instalação Windows inicial revelou que a nova biblioteca precisava da DLL
correspondente: o provider histórico não tinha os símbolos adicionais. O teste
agora reconstrói e inclui o provider em manifesto privado do prefixo, verifica
seu hash e usa somente o bin desse prefixo no PATH do processo de teste. O
pacote de desenvolvimento também testa essa combinação; o PATH global não muda.

Uma regressão Windows terminou sua execução, mas falhou ao remover panels-0.exe
temporariamente bloqueado na limpeza. O log inicial foi preservado, e a suíte
foi repetida. Uma interrupção do coletor antes do checkpoint final exigiu repetir
as suítes restantes; o coletor agora salva cada resultado. Resultados finais
contam somente as execuções aprovadas e registradas. Erros iniciais de fixture,
nome reservado e ambiente não são passes.

Computer Use foi inicializado pela skill e tentou abrir o executável exato.
Retornou **Computer Use app approval timed out**; nova listagem não encontrou
janela correspondente. Zero screenshots/inputs. Não houve captura ou UI por
outro mecanismo. [Registro not-run](../ecossistema/evidencias/m3-catalog-frame-2026-11-03/desktop.json).
Sem aceite desktop/leitor real/DPI do OS/múltiplos monitores/IME.

Comandos principais, ASSIS_BIN apontando ao candidato fresco de cada host:

```text
gcc -O2 -std=c11 -municode -static -static-libgcc -Wl,--no-insert-timestamp src/assisc.c -o build/assis.exe
cc -O2 -std=c11 src/assisc.c -o build/assis-linux
python tools/collect-catalog-frame-evidence.py
python tools/validate-examples.py --output <evidencia>/<host>-examples.json
python tools/verify-catalog-frame-install.py
python tools/prepare-development-installer.py --profile catalog
python tools/check-ecosystem-references.py --output <evidencia>/reference-integrity.json
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/verify-catalog-frame-evidence.py --write
python tools/verify-catalog-frame-evidence.py
git diff --check
```

Linux usa python3, nativamente no Ubuntu WSL2. A inicialização do WSL teve erro
RPC e depois foi recuperada pela distribuição Ubuntu, sem reconfiguração do OS.
As restrições iniciais de clone/GCC/pastas temporárias foram resolvidas pela
revisão normal de execução. Nenhuma instalação global foi alterada. O ZIP de desenvolvimento exclui os
dois registros que dependem de seu próprio hash (summary/development-bundle),
publicados canonicamente no repositório; BUILD-INFO registra os arquivos reais.

## Limites e continuação integral

Perfil de leitura de 18 tipos, sem conformidade visual 0.1 completa. Restam
script, label/input/form/image, edição/IME, live regions e hierarquia assistiva
completa. Links de arquivo/HTTPS, loader de recursos externos e integração ASV2
continuam como próximo incremento. Fragments não transferem foco ao destino.
Não há novo benchmark de shaping/bidi, SLA de quadros ou aceite visual.

Identidade incremental/editor, SDK/valores/eventos gerais, RSS/disco/perfis órfãos,
sandbox macOS/ARM, rede/TLS/origens/perfis, persistência, busca multidocumento,
M4–M9, carga integrada 24h, distribuição por terceiro e todos os aceites continuam
integralmente na fila. Pesos, baseline congelada e histórico não são alterados
para alcançar 50%. **Easy por último.**

## Publicação

Publicação normal autorizada pelo masterprompt para Vibe-O-Coder/AssisScript.
SHA/árvore remotos e inventário serão confirmados no adendo após o envio.
Sem afirmar release, merge ou CI remota nova.

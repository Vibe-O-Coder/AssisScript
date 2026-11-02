# HTDL static-catalog-0.1-v1

Contrato de desenvolvimento, 02/11/2026, E00-01/E07-01/E11-02, M3 parcial.
Referência: [rascunho HTDL 0.1 congelado](referencias/htdl-drafts-2026-10-29/docs/02-htdl-0.1.md)
e seu [manifesto de procedência](referencias/htdl-drafts-2026-10-29/PROVENANCE.json).
Não ratifica o rascunho nem declara conformidade de execução/apresentação 0.1.

## Entradas e fronteiras

`htdl::stage`/`load` continuam estritamente no perfil viewer-local-bootstrap-v1.
`stage_catalog`/`load_catalog` validam sintaxe e semântica estática do catálogo.
Carregar uma árvore não abre src/href, compila script, vincula funções ou concede
arquivos, rede, processos, janela ou execução de página. Reader/pagereader usam
a entrada bootstrap. Não há fallback que silencie recursos não apresentados.
O loader futuro precisa vincular assinaturas, resolver versões e recursos,
confinar caminhos após links e aplicar política de origem. `format=wasm` é
metadado reconhecido do rascunho, não um novo executor disponível.

APIs novas usam os mesmos Store/Document/NodeId, quotas, transação e ownership.
Erro aborta somente o candidato criado pela chamada; documento ativo e candidato
de outro produtor são preservados. Instâncias abortadas continuam consumidas.
NodeId não concede autoridade. `query` aceita todos os 23 tipos neste perfil.
`data_attribute(document,node,name)` consulta o nome exato de data-* e retorna
um NodeId local ou ausente. O empréstimo impede reload enquanto usado.

## Catálogo e atributos

IDs anteriores permanecem: document=1, head=2, title=3, body=4, container=5,
paragraph=6, text=7, heading=8, button=9. Extensões: meta=10, script=11, main=12,
section=13, header=14, footer=15, nav=16, link=17, list=18, item=19, label=20,
input=21, form=22, image=23.

Chaves fixas: type=1, version=2, lang=3, level=4, id=5, class=6, hidden=7,
disabled=8, action=9, a11y-label=10, name=11, content=12, src=13, format=14,
href=15, ordered=16, for=17, kind=18, value=19, placeholder=20, required=21,
checked=22, alt=23, a11y-live=24, on:click=25, on:input=26, on:change=27,
on:submit=28, on:focus=29, on:blur=30. Atributos são registros 100+chave;
data-* usa registro 200 com nome no span original e valor decodificado.
Consulta numérica da chave 100 é recusada para não tornar nomes ambíguos.

O parser aplica modelos de conteúdo e atributos comuns/específicos do rascunho,
cardinalidade/ordem de document/head, unicidade de main, ancestrais de form/main,
nomes de controles por formulário, labels forward/backward para input, nome
acessível obrigatório, checked somente checkbox e submit somente em form.
Nomes de eventos são identificadores, permitidos apenas nos tipos do contrato;
declaração exige script. Conferir existência/assinatura do símbolo exige o loader.
`value` de input permanece texto, inclusive número temporariamente inválido;
validação de envio e ações padrão são trabalho de controles/runtime.

Vazio aceita espaços e comentários, nunca filhos ou texto significativo.
src/href aceitam referências relativas com `/`, HTTPS minúsculo e, só em href,
fragmento #id com gramática de identificador. São recusados caminhos absolutos,
backslash, espaços/controles e outros esquemas. Isso é filtro lexical estático,
não biblioteca URL, autorização, IDNA, DNS, TLS, resolução de fragmento ou defesa
de traversal/TOCTOU. `../` pode existir no texto; apenas o loader decidirá se a
resolução permanece na raiz concedida. Referência a arquivo inexistente passa
na análise estática porque nenhum arquivo é aberto.

## Limites, falhas e editor

Mantêm-se 1 MiB de fonte, UTF-8 estrito/BOM, 20.000 nós, profundidade 256,
64 atributos e 64 KiB por valor.
O atributo level exige a forma canônica de um dígito 1..6, preservando o limite
do bootstrap; não aceita representações alternativas como 01 ou +1.
Classes, identificadores e referências partilham
8 milhões de unidades de trabalho. Visita de registro na varredura de referências
custa 128 unidades, incluindo consultas geracionais/atributos. Comparações de
bytes e passos de ancestral custam uma unidade. O limite é operacional e pode
recusar documentos estruturalmente válidos com muitas referências; retorna H401.
Não é quota de RSS nem orçamento agregado do shell/Reader.

Parser conserva corpo nativo de 96 bytes e workspace reservado por Store. O
editor usa `Diagnostics(capacity)` com capacity 1..64, construção fallível,
`is_ready`, `size`, `get`, `reset` e `truncated`. Esse objeto é memória externa
do chamador: corpo nativo de 40 bytes + capacity*56 bytes de payload solicitado,
além de overhead do alocador. `inspect(store,instance,source,output)` nunca ativa
o documento, mesmo válido. Retorna false se output não está pronto; erros de
fonte/recurso ficam no output. Candidato próprio é sempre abortado ao terminar.

Recuperação atual: após árvore sintaticamente completa, o editor continua nos
próximos elementos após erros semânticos, elimina diagnósticos repetidos e mantém
no máximo 64. Verifica referências em segunda fase; erros derivados podem aparecer
depois dos estruturais. UTF-8/léxico/sintaxe inválidos produzem o primeiro erro,
sem reparar fonte ou expor árvore parcial. Recuperação de múltiplos erros de
sintaxe e identidade incremental de nós continuam pendentes.

H101–H206/H401 preservados; H207 indica associação/nome acessível ausente ou
inválido; H301 indica evento sem script. Spans originais em bytes; linhas/colunas
UTF-16 base 1/fim exclusivo. `tools/htdl-check.assis` é um adaptador confiável:
stdin contém só dados; stdout contém contagem/truncamento e sete inteiros por
diagnóstico. Retorno 2 indica falha do próprio adaptador. Nada declarado no HTDL
é executado. LSP/VS Code traduzem esse protocolo, não reimplementam o parser.

O editor compila somente o adaptador fixo para pasta temporária própria, inicia
o analisador diretamente, limita a 15 segundos totais/64 KiB de saída e envia
o rascunho por stdin. Cancelar fecha o processo acompanhado, recolhe arquivos
temporários e descarta resultado antigo por geração/versão. Arquivo fechado
limpa diagnósticos. Falha de ferramenta vira aviso de verificação indisponível.
Formatação HTDL no LSP retorna lista vazia, sem passar HTDL ao formatter AssisScript.
O VS Code respeita workspace confiável e a opção existente de diagnósticos.

## Evidência e pendências

[Corpus declarativo](../../tests/fixtures/htdl-catalog-corpus.json),
[suíte nativa](../../tests/test-htdl-catalog.py),
[protocolo/editor](../../tests/test-htdl-editor.js),
[LSP](../../tests/test-lsp.js) e
[relatório desta revisão](../relatorios/2026-11-02-m3-htdl-catalog.md).
Windows/Linux x64 têm execução própria; formatos ARM/macOS gerados não são
execução nativa. O snapshot histórico é conferido, sem ser alterado.

Controles visuais, IME, bidi/shaping, leitor real, DPI, catálogo no Reader,
ações padrão/formulários, funções/SDK mutável e loader de recursos/FS/SSC
permanecem abertos. Gates, baseline, pesos e fila integral são preservados.
Easy continua por último.

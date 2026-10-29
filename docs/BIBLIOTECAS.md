# Bibliotecas — alpha.14

São 22 módulos nos fontes de desenvolvimento, incluindo a [arena geracional](BIBLIOTECA-arena.md) e a [janela nativa Windows](BIBLIOTECA-window.md). O provider da janela é opcional e ainda exige build separado; os pacotes anteriores não o contêm.
O caminho recomendado para novos programas é unicode, own/borrow
e slices. A revisão acrescenta random, o builder Unicode, sort safe e
owned::OwnedArray de recursos Move. Consulte [o manual atual](LINGUAGEM.md).
As atualizações abaixo preservam a história dos contratos anteriores.


**Atualização alpha.13:** closures e variantes Move próprias usam o [novo contrato](CAPTURAS-E-VARIANTES-MOVE.md). As limitações históricas abaixo sobre sua ausência foram superadas; demais limites permanecem.

**Atualização alpha.12:** 19 bibliotecas. [net](BIBLIOTECA-net.md) acrescenta HTTP(S) com polling/cancelamento; [safe é o padrão](SAFE-DEFAULT.md). As atualizações abaixo são históricas.

**Atualização alpha.11:** ABI C escalar, callbacks e recursos externos documentados em [FFI-C.md](FFI-C.md). Novos módulos opcionais [http](BIBLIOTECA-http.md) e [process](BIBLIOTECA-process.md), totalizando 18 bibliotecas. O texto seguinte é histórico quando descreve a ausência de FFI/B/C.

**Atualização alpha.10:** sintaxe e APIs canônicas em inglês; imports e nomes antigos da stdlib exigem migração. Veja [ENGLISH-API.md](ENGLISH-API.md) e o [handoff atual](HANDOFF-3.3-ALPHA.10.md). A alpha.14 removeu as grafias históricas; consulte o manual atual.

**Atualização alpha.9:** [Recursos/fatias e backend](RECURSOS-E-FATIAS.md) complementam os contratos abaixo: classes gerenciadas com receptor, slice<T>, texto UTF-8 com comprimento, vtable com drop e ELF PIE. [Handoff atual](HANDOFF-3.3-ALPHA.9.md).

**Atualização 3.3.0-alpha.8:** Alpha.7 mantém oito bibliotecas, com Option/Result em erros, UTF-8 explícito em texto e formatação sem alocação em conversoes. [IO nativo e aplicação A](IO-E-APLICACAO-A.md) são intrínsecos do runtime.

Alpha.6: algoritmos acrescenta map_own/filter_own/fold_borrow com contratos gerenciados. Texto/CSV e APIs manuais anteriores continuam legados. [Ownership](OWNERSHIP-FUNCOES.md).

## Inclusão de fontes

```assis
import "std/math.assis";
import "bibliotecas/geometria.assis";
```

`#yuri` exige `<...>` e extensão .assis. Cada diretiva ocupa uma linha própria; um ponto e vírgula final é opcional. A busca começa na pasta do arquivo importador, depois usa `-I`, `ASSIS_PATH` e os caminhos padrão de `std/`. Bibliotecas são fontes compilados e incorporados ao executável; não são carregadas em tempo de execução.

## Pacotes .pillow

```assis
// assis.assis
import "src.pillow";
```

O arquivo src.pillow pode conter:

```assis
import "src/modelos.assis";
import "src/calculos.assis";
import "dependencias.pillow";
```

O sufixo .pillow é obrigatório. O manifesto aceita somente #yuri, #body e comentários. Caminhos dentro dele são relativos ao próprio manifesto. Um caminho pontuado como `#body meu.pacote.pillow` tenta primeiro o arquivo literal e depois `meu/pacote.pillow`. Não há download, resolução de versões ou namespaces; todos os símbolos públicos compartilham o mesmo espaço global.

Fontes repetidos são incluídos uma única vez, inclusive se referenciados por caminhos diferentes para o mesmo arquivo. Ciclos em fontes ou pacotes geram erro. Colisões de nomes são erros. Tipos, assinaturas e retornos de todos os módulos são verificados antes de gravar o executável. O destino não pode sobrescrever um fonte ou manifesto carregado.

`assis check src.pillow --library` verifica um pacote sem exigir entrada. `assis build src.pillow` é possível se os fontes do pacote definirem assis_assis.

## Biblioteca padrão

| Arquivo | Funções legíveis |
| --- | --- |
| `std/math.assis` | `min`, `max`, `clamp`, `abs` |
| `std/strings.assis` | `starts_with`, `ends_with`, `contains` |
| `std/memory.assis` | `fill`, `copy` |
| `std/errors.assis` | `IntResult`, `checked_add`, `checked_div`, `error_message` |
| `std/convert.assis` | `parse_int`, `int_to_string` |
| `std/algorithms.assis` (opcional) | Heapsort, busca binária, deduplicação |
| `std/csv.assis` (opcional) | CSV com aspas, escapes, CRLF e erro recuperável |
| `std/encoding.assis` (opcional) | Hexadecimal e Base64 estritos para dados binários |

O instalador inclui as cinco obrigatórias em todos os perfis. Por padrão instala também as três opcionais. Use `bin/assis-setup.exe install --minimal` (Windows) ou `sh instalar.sh --minimal` (Linux) para o núcleo. `--with csv,algorithms` instala núcleo e apenas as opcionais selecionadas; `--with` pode ser repetido. Reinstalar acrescenta bibliotecas sem remover opções anteriormente instaladas. O VSIX contém o conjunto completo, independente do perfil do instalador.

### Manuais individuais

- [Matemática](BIBLIOTECA-matematica.md)
- [Texto, busca KMP e Texto proprietário](BIBLIOTECA-texto.md)
- [Memória](BIBLIOTECA-memoria.md)
- [Erros e resultados](BIBLIOTECA-erros.md)
- [Conversões](BIBLIOTECA-conversoes.md)
- [Algoritmos](BIBLIOTECA-algoritmos.md)
- [CSV](BIBLIOTECA-csv.md)
- [Codificação](BIBLIOTECA-codificacao.md)

Cada manual acompanha a instalação e o VSIX; no editor use **AssisScript: Documentação das bibliotecas nativas**. Os fontes também têm comentários para hover, assinaturas e F12. O catálogo versionado fica em stdlib/catalogo.json. Os exemplos de venda e codificação são programas de aplicação executáveis, com validação e liberação de recursos.

Array<T> e HashMap<K, V> são intrínsecos e não exigem importação. As funções históricas das bibliotecas 2.x continuam disponíveis. Cada função padrão possui documentação técnica junto da declaração, usada pelo hover e pelas assinaturas no VS Code.

## Bibliotecas próprias e hover

```assis
/// Retorna x*x + y*y sem extrair raiz, com overflow modular de 64 bits.
/// @param codepoint Referência válida a Ponto.
/// @return Quadrado da distância à origem.
fn distancia_quadrada(codepoint: Ponto): int {
    return codepoint.x * codepoint.x + codepoint.y * codepoint.y;
}
```

O editor encontra essa documentação por #yuri ou por #body, incluindo imports transitivos e fontes não salvos. Comentários ///, miyabi e /** ... */ são aceitos. Sem comentário, a extensão mostra a assinatura; ela não inventa a semântica de bibliotecas externas.

## Compatibilidade

A sintaxe antiga `importa "std/math";` ainda funciona e permite omitir extensão, como em 2.x. Para novos programas, prefira #yuri. No Windows, ASSIS_PATH separa pastas com ponto e vírgula; no Linux, com dois pontos.

## Bibliotecas opcionais da alpha.8

- [cli](BIBLIOTECA-cli.md): Argumentos own, inteiros de bytes e IO completo com limites.
- [json](BIBLIOTECA-json.md): Lexer, validador e strings JSON UTF-8 com limites.
- [tempo](BIBLIOTECA-tempo.md): Prazos monotônicos e espera cooperativa.
- [log](BIBLIOTECA-log.md): Log em stderr com timestamp civil, níveis e filtro.
- [iteradores](BIBLIOTECA-iteradores.md): Intervalos e pipelines imutáveis sem alocações intermediárias.
- [eventos](BIBLIOTECA-eventos.md): Fila limitada de uma thread com temporizadores e cancelamento.

Há 14 bibliotecas: cinco obrigatórias e nove opcionais. O instalador seleciona dependências opcionais automaticamente (`log` inclui `cli`). Todas continuam locais e só entram no programa ao importar.

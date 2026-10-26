# Bibliotecas e pacotes 3.1

**Atualização alpha.9:** [Recursos/fatias e backend](RECURSOS-E-FATIAS.md) complementam os contratos abaixo: classes gerenciadas com receptor, slice<T>, texto UTF-8 com comprimento, vtable com drop e ELF PIE. [Handoff atual](HANDOFF-3.3-ALPHA.9.md).

**Atualização 3.3.0-alpha.8:** Alpha.7 mantém oito bibliotecas, com Option/Result em erros, UTF-8 explícito em texto e formatação sem alocação em conversoes. [IO nativo e aplicação A](IO-E-APLICACAO-A.md) são intrínsecos do runtime.

Alpha.6: algoritmos acrescenta map_own/filter_own/fold_borrow com contratos gerenciados. Texto/CSV e APIs manuais anteriores continuam legados. [Ownership](OWNERSHIP-FUNCOES.md).

## Inclusão de fontes

```assis
#yuri <std/matematica.assis>
#yuri <bibliotecas/geometria.assis>
```

`#yuri` exige `<...>` e extensão .assis. Cada diretiva ocupa uma linha própria; um ponto e vírgula final é opcional. A busca começa na pasta do arquivo importador, depois usa `-I`, `ASSIS_PATH` e os caminhos padrão de `std/`. Bibliotecas são fontes compilados e incorporados ao executável; não são carregadas em tempo de execução.

## Pacotes .pillow

```assis
// assis.assis
#body src.pillow
```

O arquivo src.pillow pode conter:

```assis
#yuri <src/modelos.assis>
#yuri <src/calculos.assis>
#body dependencias.pillow
```

O sufixo .pillow é obrigatório. O manifesto aceita somente #yuri, #body e comentários. Caminhos dentro dele são relativos ao próprio manifesto. Um caminho pontuado como `#body meu.pacote.pillow` tenta primeiro o arquivo literal e depois `meu/pacote.pillow`. Não há download, resolução de versões ou namespaces; todos os símbolos públicos compartilham o mesmo espaço global.

Fontes repetidos são incluídos uma única vez, inclusive se referenciados por caminhos diferentes para o mesmo arquivo. Ciclos em fontes ou pacotes geram erro. Colisões de nomes são erros. Tipos, assinaturas e retornos de todos os módulos são verificados antes de gravar o executável. O destino não pode sobrescrever um fonte ou manifesto carregado.

`assis check src.pillow --library` verifica um pacote sem exigir entrada. `assis build src.pillow` é possível se os fontes do pacote definirem assis_assis.

## Biblioteca padrão

| Arquivo | Funções legíveis |
| --- | --- |
| `std/matematica.assis` | `minimo`, `maximo`, `limitar`, `absoluto` |
| `std/texto.assis` | `comeca_com`, `termina_com`, `contem` |
| `std/memoria.assis` | `preencher`, `copiar` |
| `std/erros.assis` | `ResultadoInt`, `somar_seguro`, `dividir_seguro`, `mensagem_erro` |
| `std/conversoes.assis` | `inteiro_de_texto`, `texto_de_inteiro` |
| `std/algoritmos.assis` (opcional) | Heapsort, busca binária, deduplicação |
| `std/csv.assis` (opcional) | CSV com aspas, escapes, CRLF e erro recuperável |
| `std/codificacao.assis` (opcional) | Hexadecimal e Base64 estritos para dados binários |

O instalador inclui as cinco obrigatórias em todos os perfis. Por padrão instala também as três opcionais. Use `bin/assis-setup.exe install --minimal` (Windows) ou `sh instalar.sh --minimal` (Linux) para o núcleo. `--with csv,algoritmos` instala núcleo e apenas as opcionais selecionadas; `--with` pode ser repetido. Reinstalar acrescenta bibliotecas sem remover opções anteriormente instaladas. O VSIX contém o conjunto completo, independente do perfil do instalador.

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
/// @param ponto Referência válida a Ponto.
/// @return Quadrado da distância à origem.
assis distancia_quadrada(ponto: Ponto): int {
    return ponto.x * ponto.x + ponto.y * ponto.y;
}
```

O editor encontra essa documentação por #yuri ou por #body, incluindo imports transitivos e fontes não salvos. Comentários ///, miyabi e /** ... */ são aceitos. Sem comentário, a extensão mostra a assinatura; ela não inventa a semântica de bibliotecas externas.

## Compatibilidade

A sintaxe antiga `importa "std/matematica";` ainda funciona e permite omitir extensão, como em 2.x. Para novos programas, prefira #yuri. No Windows, ASSIS_PATH separa pastas com ponto e vírgula; no Linux, com dois pontos.

## Bibliotecas opcionais da alpha.8

- [cli](BIBLIOTECA-cli.md): Argumentos own, inteiros de bytes e IO completo com limites.
- [json](BIBLIOTECA-json.md): Lexer, validador e strings JSON UTF-8 com limites.
- [tempo](BIBLIOTECA-tempo.md): Prazos monotônicos e espera cooperativa.
- [log](BIBLIOTECA-log.md): Log em stderr com timestamp civil, níveis e filtro.
- [iteradores](BIBLIOTECA-iteradores.md): Intervalos e pipelines imutáveis sem alocações intermediárias.
- [eventos](BIBLIOTECA-eventos.md): Fila limitada de uma thread com temporizadores e cancelamento.

Há 14 bibliotecas: cinco obrigatórias e nove opcionais. O instalador seleciona dependências opcionais automaticamente (`log` inclui `cli`). Todas continuam locais e só entram no programa ao importar.

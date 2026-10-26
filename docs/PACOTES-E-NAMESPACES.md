# Namespaces e pacotes offline — alpha.8

Um arquivo pode começar com `namespace medidas;`. Seus tipos e funções ficam em `medidas::Nome`; declarações globais são privadas ao arquivo por padrão. `public` exporta uma declaração. Dois arquivos que escrevem o mesmo namespace continuam sem compartilhar seus privados. Campos/métodos mantêm a privacidade nominal existente. Bibliotecas antigas sem namespace conservam o espaço global público.

```assis
namespace medidas;
public value struct Ponto<T> { let x: T; let y: T; }
pure assis interno(n: int): int { return n * 2; }
public pure assis dobro(n: int): int { return interno(n); }
```

O consumidor importa o arquivo e usa `medidas::dobro(21)` ou `new medidas::Ponto<int>(20,22)`. Especialização explícita: `medidas::identidade::<int>(42)`. Nomes locais continuam ocultando funções; resolver namespaces não é substituição textual de código. Identidades, efeitos, vidas e privacidade continuam sendo verificados após a especialização AST. A entrada `assis_assis` permanece no arquivo sem namespace.

## Manifesto e lockfile

`assis.pkg` deve ficar ao lado da entrada do projeto. É texto UTF-8, com comentários `#`, um registro por linha e aspas em caminhos com espaços:

```text
package meu_app 1.0.0
dep medidas 2.0.0 "vendor/medidas locais"
```

Cada dependência tem seu próprio `assis.pkg` com nome e versão `X.Y.Z` exata, e pode declarar outras dependências locais. Não há intervalos de versão, registro, downloads ou scripts de instalação. Fontes são vendorizados dentro da árvore do projeto; symlinks/junctions são resolvidos antes de verificar esse limite. IDs de alias são locais ao manifesto importador.

`#yuri <pkg/medidas/api.assis>` resolve somente o alias declarado. Dependências transitivas usam seus próprios aliases. Dependências não podem importar código externo por escapes relativos ou pesquisa ambiente; devem declarar `pkg/alias/...`. `std/` refere-se às bibliotecas do compilador e também tem conteúdo registrado no lockfile. Projetos com manifesto não aceitam módulos externos não vendorizados via `-I`.

Após revisar as dependências, execute `assis lock entrada.assis`. O compilador carrega e verifica o projeto antes de substituir `assis.lock` atomicamente. O arquivo registra a versão do compilador, hashes SHA-256 dos manifestos transitivos, dos fontes de dependências efetivamente importados e das bibliotecas padrão usadas. A comparação é exata e ordenada, sem datas ou caminhos absolutos do host. Os hashes representam os mesmos bytes carregados para compilação, inclusive BOM; alterações por overlays também são verificadas.

`check`, `build`, `run`, `test` e `doc` verificam o lockfile sem atualizá-lo. Alterar dependências/imports, bibliotecas padrão usadas ou compilador exige revisão e novo `lock`. Editar apenas o programa principal não exige atualizar hashes de seus próprios fontes. Fontes não importados não são parte do artefato compilado e não são inventariados pelo lockfile.

Limites: 128 pacotes, 64 níveis no grafo, 1024 módulos e 16 MiB totais de fontes. Ciclos, aliases repetidos, versões divergentes, arquivos ausentes, escapes e lockfile divergente falham antes da emissão. Integridade local não prova autoria/assinatura de um pacote. Não há publicação ou resolução de registro nesta entrega.

Aliases físicos de um mesmo arquivo dentro de um pacote conservam uma só identidade de módulo, mas todos os caminhos importados entram no lockfile. Hardlinks/aliases compartilhados entre pacotes diferentes, ou entre aplicação e stdlib, são rejeitados: o contexto de importações relativas seria ambíguo. O prefixo `std/` não autoriza escapar da pasta padrão, e bibliotecas padrão não podem importar dependências particulares do projeto. Essas regras também valem para o fallback pontuado de `.pillow`.

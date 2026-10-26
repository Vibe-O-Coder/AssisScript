# AssisScript — plano de evolução e passagem para a próxima instância

**Continuação atual — 3.3.0-alpha.9: 76% (75,5/100 pontos).** Classes gerenciadas/receptores, fatias com vidas, texto UTF-8 e lista proprietária, HIR inicial, ELF PIE e locais escalares no GDB. Alvo de 90–100% ainda não atingido. [Handoff atual](HANDOFF-3.3-ALPHA.9.md), [validação](VALIDACAO-3.3-ALPHA.9.md), [progresso](PROGRESSO.md). Entradas seguintes são históricas.

**Continuação atual, 25/10/2026 — 3.3.0-alpha.8:** números nativos, namespaces/pacotes offline, seis bibliotecas CLI, eventos cooperativos, persistência recuperável e ferramentas/depuração. **Conclusão estimada: 70% (70/100 pontos)** pela régua original, atingindo o alvo de 70–80% no limite inferior. [Handoff](HANDOFF-3.3-ALPHA.8.md), [validação](VALIDACAO-3.3-ALPHA.8.md), [progresso](PROGRESSO.md). Pendências de ownership geral, capturas, text/slices, FFI/rede/B/C/24 horas, PIE e licença permanecem explícitas. As entradas seguintes são históricas.

**Continuação atual, 25/10/2026 — 3.3.0-alpha.7:** registros Copy por valor, enums/Result/Option/matching, recursão pure em cauda, arquivos own, argumentos Unicode, bytes/UTF-8 explícitos e aplicação A em CSV numérico com buffers fixos. **Conclusão estimada: 56% (56/100 pontos)** pela régua original; alvo solicitado de 70–80% ainda não atingido. [Handoff](HANDOFF-3.3-ALPHA.7.md), [validação](VALIDACAO-3.3-ALPHA.7.md), [contratos de valores](VALORES-E-VARIANTES.md), [IO e A](IO-E-APLICACAO-A.md). As entradas anteriores são históricas.

**Continuação atual, 25/10/2026 — 3.3.0-alpha.6:** ownership em assinaturas/retornos, vidas explícitas, campos own de structs, movimentos parciais, análise de fluxo e perfil opcional safe/unsafe. APIs funcionais gerenciadas integram F1 no subconjunto escalar. **Conclusão estimada: 45% (44,5/100 pontos)** pela mesma régua; fases 2–6 continuam abertas. [Handoff atual](HANDOFF-3.3-ALPHA.6.md), [contratos](OWNERSHIP-FUNCOES.md), [validação](VALIDACAO-3.3-ALPHA.6.md).

Data: 24/10/2026. Base examinada: AssisScript 3.2.0, Windows/Linux x86_64.

**Atualização de execução, 24/10/2026:** implementação iniciada a pedido do usuário. A direção adotada é **programação funcional**, com compatibilidade transitória para o núcleo imperativo existente. A versão experimental 3.3.0-alpha.1 corrige B01 e acrescenta `private`, `val` e funções escalares `pure assis`. O [relatório da alpha.1](HANDOFF-3.3-ALPHA.md) preserva o escopo e a validação daquela entrega. As fases abaixo continuam sendo o plano completo; não estão todas concluídas.

**Continuação, 24/10/2026 — 3.3.0-alpha.2:** primeiro incremento da fase 1 implementado: identidades DefId/TypeId, aplicações de tipo estruturadas, templates AST de funções/structs, cache/fila de especialização transitiva, limites de expansão e verificação concreta de tipos/pureza/ownership. Contratos em [GENERICS.md](GENERICS.md); estado e operação em [HANDOFF-3.3-ALPHA.2.md](HANDOFF-3.3-ALPHA.2.md). A fase 1 completa e F1 continuam abertas: faltam classes genéricas, tipos de função com efeitos, funções como valores e migração integral dos corpos das coleções. Não avançar a classificação de prontidão geral por esta entrega.

## 1. Pedido e conclusão

**Continuação, 25/10/2026 — 3.3.0-alpha.5:** corpos de Array/HashMap migrados para a especialização AST comum, com templates analisados uma vez, substituição por identidade e seleção do hash por AST. APIs, layouts, hashing, privacidade, bounds e limites separados preservados. [Handoff](HANDOFF-3.3-ALPHA.5.md), [validação](VALIDACAO-3.3-ALPHA.5.md). Os mecanismos da fase 1 estão implementados; F1 ainda depende dos contratos de propriedade da fase 2.

**Estimativa histórica da alpha.5: 34%** (33,5 pontos de 100); a alpha.6 atinge **45% (44,5 pontos)**. A [régua auditável](PROGRESSO.md) distribui 35 critérios ponderados nas fases 0–6, incluindo F0–F4 sem contar pontos em duplicidade. É estimativa de atendimento do plano, não de prazo ou prontidão para produção. Pela mesma régua, a alpha.4 corresponde retrospectivamente a 31%. Não inclui construir o navegador, HTDL, estilos ou motor de busca. A partir desta entrega, registrar porcentagem, critério avançado e pendências em cada novo handoff/validação.

**Continuação, 25/10/2026 — 3.3.0-alpha.4:** classes genéricas com campos/métodos especializados, construtores, herança aplicada, upcasts e despacho virtual implementadas, preservando identidade declaradora e privacidade de cada especialização. [Contratos](GENERICS.md), [handoff](HANDOFF-3.3-ALPHA.4.md) e [validação](VALIDACAO-3.3-ALPHA.4.md). Métodos com parâmetros de tipo próprios, migração AST das coleções e empréstimos nas assinaturas continuam pendentes; a fase 1/F1 e a prontidão geral permanecem abertas.

**Continuação, 25/10/2026 — 3.3.0-alpha.3:** tipos de função com efeitos, funções globais como valores, especializações como valores, callbacks puros e composição implementados. Map/filter/fold genéricos acrescentados à biblioteca algoritmos para escalares/funções pure, com Array legado e liberação explícita. [Contratos](FUNCOES-E-EFEITOS.md), [handoff](HANDOFF-3.3-ALPHA.3.md) e [validação](VALIDACAO-3.3-ALPHA.3.md). Classes genéricas, migração AST das coleções e empréstimos nas assinaturas permanecem abertos; o gate integrado fase 1/F1 e a classificação de prontidão geral não avançam para produção.

A pergunta que deve orientar cada entrega é: **“Essa linguagem pode ser comercializada? Eu poderia criar uma aplicação real com ela?”**

O pedido original era somente produzir o plano. O usuário autorizou sua execução e determinou a adoção do paradigma funcional. As evidências da seção 2 descrevem a inspeção histórica da 3.2; os resultados posteriores devem ser consultados no relatório da implementação.

**Nem todas as sugestões do relatório 3.1 foram concluídas.** Na base 3.2 examinada, havia uma lacuna concreta de encapsulamento, ownership local, ausência de generics do usuário e integrações essenciais com o sistema ainda faltantes. As alphas posteriores corrigiram B01, introduziram generics e ordem superior e, na alpha.6, contratos de ownership entre funções e campos own de structs. A alpha.7 acrescenta dados Copy por valor, variantes e IO de arquivos. Recursos gerenciados gerais e integrações externas continuam abertos. Essas entregas ainda não estabelecem prontidão geral para produção.

Hoje é possível criar programas nativos pequenos, ferramentas de terminal com entrada padrão, transformações em memória e a aplicação A delimitada, com arquivos/argumentos e processamento em fluxo validado na alpha.7. Isso já tem utilidade real em ambientes controlados. A evidência disponível não basta para apresentar a linguagem como plataforma madura para serviços, aplicações gráficas, execução de conteúdo não confiável ou um navegador.

“Comercializável” neste plano significa **prontidão técnica e operacional para uma oferta definida**. Não é uma conclusão jurídica, financeira ou uma garantia de vendas. Não foi localizado arquivo LICENSE/COPYING no fonte examinado; a decisão de licença e o inventário de procedência dos componentes ainda precisam ser tratados pelo responsável pelo projeto.

**Decisão do usuário: adotar o paradigma de programação funcional.** Priorizar vínculos e dados imutáveis, funções como valores, composição, funções de ordem superior, tipos algébricos e pattern matching. Separar cálculo puro de efeitos de entrada/saída, memória e sistema. Ownership e geração nativa continuam sendo requisitos; programação funcional não exige impor GC, boxing ou despacho dinâmico global. A implementação será incremental e as garantias devem ser verificadas pelo compilador. `let` legado continua mutável durante a migração; a existência de funções comuns não equivale a suporte funcional completo.

## 2. Evidência examinada nesta etapa

Foram lidos o compilador, a implementação de coleções, o verificador de ownership, os runtimes, o catálogo e os fontes das oito bibliotecas, a documentação de validação e os resultados de desempenho. Foram executadas **15 verificações de sintaxe/tipos**, sem alterar fontes nem executar programas potencialmente inseguros:

| Verificação feita agora | Resultado |
| --- | --- |
| As oito bibliotecas com `check --library` | Todas aceitas |
| Uso de `Array<int>` | Aceito |
| Declaração de função genérica pelo usuário | Rejeitada no `<` após o nome |
| Declaração de struct genérica pelo usuário | Rejeitada no `<` após o nome |
| Alteração de `Array._length` com `own` | Aceita; problema a corrigir |
| Leitura de `Array._data[indice]` com `own` | Aceita; problema a corrigir |
| `own mensagem: Texto = new Texto()` | Rejeitada: classes como Texto não são cobertas |
| Passagem de um proprietário para função legada | Rejeitada: falta contrato de empréstimo na assinatura |

As suítes completas **não foram repetidas neste turno de planejamento**. O registro da entrega 3.2 em [VALIDACAO.md](VALIDACAO.md) informa 68 testes Node, 128 verificações nativas Windows, 133 Linux, 10 de módulos, 41 casos PE e 73 casos portáveis. Esses conjuntos têm sobreposição e não devem ser somados como casos independentes. São uma base de regressão, não uma certificação de produção.

### Bloqueio B01: invariantes públicas de coleções

**Histórico 3.2; corrigido no incremento 3.3.0-alpha.1.** Os exemplos abaixo agora são rejeitados por privacidade de membros. A conclusão é sobre encapsulamento; ponteiros legados ainda não têm segurança geral de memória.

Estes trechos foram submetidos apenas a `check --stdin`; ambos foram aceitos:

```assis
assis assis_assis(): int {
    own a: Array<int> = [1];
    a._length = 999999;
    return 0;
}
```

```assis
assis assis_assis(): int {
    own a: Array<int> = [1];
    print(a._data[999999]);
    return 0;
}
```

`_length` e `_data` são descritos como internos, mas o verificador de membros não impõe essa separação. Alterar o comprimento interfere na informação usada para verificar índices; acessar o buffer bruto evita o caminho de indexação da coleção. A aceitação desses programas, combinada com a emissão atual de ponteiros, revela uma lacuna de segurança do modelo público. **Não houve execução desses acessos nem demonstração de exploração.**

Pontos de inspeção: `src/assisc.c`, funções `find_field`, `check_expr`/`N_MEMBER`, `gen_address`; `src/ownership.h`, `managed_origin` e `memory_expr`; campos gerados em `src/collections.h`.

**Antes de anunciar segurança de memória, o acesso aos detalhes internos precisa ser efetivamente restringido.** Bloquear só os dois exemplos, só um nome de campo ou só o comando `check` não resolve: a regra precisa valer também para alias, ponteiros derivados, todos os modos de compilação e demais coleções.

## 3. Situação das sugestões anteriores

| Tema | Estado na 3.2 | Trabalho restante |
| --- | --- | --- |
| Alocador por tamanho | Entregue com limites | Medir RAM/retenção; política de grandes blocos e futura concorrência |
| Texto com acesso rápido | Parcial | Cache em locais/parâmetros; comprimento explícito em toda a representação, campos, retornos e coleções |
| Texto binário/Unicode | Parcial | NUL ainda termina text; separar bytes de texto e definir validação/iteração Unicode |
| Entrada, arquivos, argumentos e tempo | Parcial | Há stdin e relógio monotônico; faltam arquivos, diretórios, argumentos e relógio civil |
| Divisão constante e comparações | Entregue no backend atual | Ampliar otimizações comprovadas sem alterar sinal, overflow ou efeitos |
| Registradores, ABI e inlining | Parcial | Quatro escalares frequentes; faltam IR, análise mais ampla, ABI de argumentos e inlining |
| Eliminação de bounds e perfil de HashMap | Pendente | Provar limites; medir colisões/cargas adversas antes de alterar algoritmos |
| Estouro de pilha com mensagem | Entregue com limites | Limite conservador; avaliar configuração e interações com código externo |
| Debug de memória | Parcial | Há preenchimento e contagem agregada; não há sanitizador completo nem locais de vazamentos |
| Ownership e borrowing | Parcial, com B01 | Funções, retornos, campos, destrutores, recursos compostos e garantias contra desvios |
| `div`, `defer`, repetição | Parcial | div/defer/for presentes; falta for-in/iteradores |
| Float e inteiros de largura fixa | Pendente | Modelo numérico, layout, conversões e geração nativa |
| Result/Option | Pendente como recurso geral | Existe ResultadoInt manual; faltam variantes genéricas e propagação |
| Generics e interfaces do usuário | Pendente | Só Array/HashMap têm parametrização intrínseca |
| Struct por valor, Set, slices e sort genérico | Pendente | Especificação de layout, semântica de cópia/move e APIs |
| Namespaces e versões de pacotes | Pendente | Espaço global e manifestos de inclusão; sem resolução versionada/lockfile |
| ELF PIE, símbolos, debug e perf | Pendente | Linux ainda usa ET_EXEC/base fixa; falta suporte a depuradores |
| Benchmark externo | Parcial | Quatro cargas, C/Python; ampliar duração, variedade e métricas, incluir C++ quando pertinente |
| Formatador, LSP, ARM e macOS | Pendente | Incrementos separados, após contratos fundamentais |
| Organização e distribuição | Parcial | Há headers separados e exclusão de build no pacote; frontend segue concentrado em assisc.c |

`div { ... }` permanece um bloco lexical e uma referência cultural ao Assis. Sua existência não implica implementação de HTML ou HTDL.

## 4. Bibliotecas atuais: avaliação

As oito bibliotecas formam uma base coerente para manipulação de dados em memória. Passar na tipagem e possuir testes de exemplo não comprova robustez diante de entradas hostis, execução prolongada ou grandes volumes. A divisão “obrigatória/opcional” abaixo é a do instalador atual; o VSIX contém as oito.

| Biblioteca | Perfil | Valor atual | O que falta para uma API de produção |
| --- | --- | --- | --- |
| matematica | Obrigatória | min/max, limites e absoluto inteiros | Tipos numéricos, operações verificadas e convenções de overflow; absoluto de INT64_MIN requer contrato explícito |
| texto | Obrigatória | Builder, KMP, recorte, concatenação, divisão, junção, substituição e ler_linha | Integrar ownership de Texto; texto com comprimento, Unicode e leitura em blocos; não depender de dispose/free manual como caminho seguro |
| memoria | Obrigatória | Copiar/preencher ponteiros | APIs públicas com slices e limites; operações brutas em fronteira unsafe; cópia com sobreposição definida |
| erros | Obrigatória | ResultadoInt recuperável | Result<T,E>/Option<T>, erros estruturados, propagação e tratamento de erro externo sem abortar o processo |
| conversoes | Obrigatória | Decimal int64 estrito e formatação | Ampliar números/formatos, manter detecção de overflow e evitar alocações obrigatórias para todo resultado pequeno |
| algoritmos | Opcional | Heapsort/busca e, na alpha.3, map/filter/fold genéricos com callbacks pure | Integração de ownership nas assinaturas, tipos compostos, comparadores de ordenação e iteradores |
| csv | Opcional | CSV em memória com erros de formato recuperáveis | Streaming, limites configuráveis, integração com arquivos e liberação segura de todas as estruturas e visões |
| codificacao | Opcional | Hex/Base64 estritos e bytes zero nos dados binários | APIs de bytes/slices, streaming e limites; não confundir codificação com criptografia |

Array e HashMap são intrínsecos, fora desse catálogo. Além de B01, o hash de inteiros é simples e o de texto é previsível. A resistência a cargas adversas **ainda precisa ser medida**; custo esperado O(1) não equivale a proteção contra entrada escolhida para produzir colisões.

### Bibliotecas a acrescentar

| Prioridade | Grupo proposto | Escopo e critério de entrega |
| --- | --- | --- |
| P0/P1 | io, arquivos, caminhos, processo/ambiente | stdin/stdout/stderr, leitura/escrita em blocos, arquivos/diretórios, argumentos, variáveis de ambiente e códigos de saída; erros recuperáveis, Unicode em caminhos e fechamento garantido |
| P1 | colecoes e iteradores | Array/HashMap públicos com internos privados, Set, slices, comparação/ordenação e ownership dos elementos |
| P1 | resultado e opcao | Tipos genéricos por valor quando possível, sem alocação e boxing obrigatórios para casos escalares |
| P1 | bytes, texto e unicode | Buffer/slices separados de UTF-8; comprimento, validade, pontos de código e contratos de fronteira; graphemes/normalização definidos por API |
| P1 | tempo, aleatorio, log e testes | Relógios distintos, temporizadores, geração determinística e entropia do sistema em APIs distintas, logs configuráveis e testes de integração |
| P1/P2 | json e configuracao | Parse/serialização com limites de profundidade/tamanho, erros com posição e ownership claro; nenhuma rede implícita |
| P2 | ffi e bibliotecas externas | ABI C documentada, carga/ligação controlada, callbacks, structs e gerenciamento de handles; dependências declaradas |
| P2 | rede, url, dns, tls, http | Timeouts, cancelamento, limites e erros estruturados; integração criptográfica avaliada separadamente, sem inventar protocolos de segurança |
| P2 | persistencia e concorrencia | Integração com banco/armazenamento, processos/IPC, atomics, sincronização e event loop; threads só com contrato de memória e alocador adequado |
| P3 | plataforma grafica | Janelas, eventos, fontes, layout, imagens e renderização, com interface específica por plataforma |

Essa é uma proposta de organização, não uma obrigação de colocar tudo no runtime mínimo. Recursos opcionais devem declarar dependências, custos e plataformas. A distribuição básica deve continuar utilizável offline, sem exigir GCC/Python/Node para compilar programas comuns.

## 5. Arquitetura proposta e ordem das entregas

Não iniciar todas as frentes ao mesmo tempo. As fases são ordenadas por dependências e critérios de aceitação, sem prometer datas ou equivalência geral de desempenho com C/C++.

### Trilha funcional obrigatória, integrada às fases

| Etapa | Dependências | Entrega e aceitação | Estado |
| --- | --- | --- | --- |
| F0 — vínculos e pureza escalar | Encapsulamento da fase 0 | `val`, parâmetros puros imutáveis, `pure assis`, proibição transitiva de IO/ponteiros/alocação; composição e recursão em Windows/Linux | Implementada na alpha; ver limites no manual funcional |
| F1 — tipos e funções de ordem superior | Representação estruturada e especialização da fase 1 | Tipo de função com efeitos na assinatura; passar, retornar e compor funções; map/filter/fold tipados; callbacks puros não aceitam função com efeitos | Núcleo na alpha.3; mecanismos da fase 1 na alpha.5; APIs gerenciadas map_own/filter_own/fold_borrow integram F1 na alpha.6; alpha.7 amplia a valores Copy |
| F2 — dados algébricos e valores imutáveis | Ownership e layout da fase 2 | Enums/variantes, matching exaustivo, Result/Option e registros por valor; construir novo valor sem modificar o original; cópia/move explícitos | Núcleo Copy por valor, variantes e matching na alpha.7; variantes Move e recursos gerais pendentes |
| F3 — capturas e coleções funcionais | F1/F2 e análise de vidas | Closures com captura por valor/move/borrow verificada; iteradores e pipelines, compartilhamento imutável ou estruturas persistentes com custo medido | Pendente |
| F4 — efeitos e otimização | Aplicações A/B/C e backend | Fronteira explícita para IO/FFI/rede; composição preserva ordem dos efeitos; eliminação de recursão de cauda e fusão somente com provas e comparação | Parcial: IO e TCO direto pure na alpha.7; FFI/rede, fusão e aplicações B/C pendentes |

Não usar `pure` como simples dica ao otimizador: um corpo com efeitos deve ser rejeitado mesmo quando não é chamado ou o efeito está num ramo inalcançável. Pureza não garante término, ausência de divisão por zero ou de estouro de pilha. A alpha.1 restringiu funções puras a int/byte/bool; a alpha.3 acrescenta funções pure sem captura com contrato recursivo. Text emprestado e objetos mutáveis continuam excluídos antes de resolver suas vidas. A mutação de acumuladores escalares locais é permitida e não escapa da função; o estilo novo recomenda `val` sempre que não houver atualização.

### Fase 0 — baseline, encapsulamento e contratos de segurança

1. Registrar hashes/versões dos fontes, binários, runtimes e dependências. Separar evidência repetida agora de resultados históricos. Preservar os casos válidos e as otimizações 3.2.
2. Corrigir B01 e examinar o mesmo padrão em HashMap, Texto e classes da biblioteca. Representar visibilidade/origem confiável de membros; o prefixo `_` por convenção não basta. Definir acesso legítimo de métodos internos sem conceder privilégios ao código do usuário por nome ou caminho forjável.
3. Especificar a fronteira safe/unsafe: ponteiros brutos, bytes/text emprestados, FFI, acesso ao sistema e liberação manual. A ausência de GC não deve ser anunciada como prova automática de segurança.
4. Testar aliases, reempréstimos futuros, alterações indiretas de metadados, reatribuições, fluxo condicional e laços. Auditar a decisão de confiar em text de vida externa.
5. Criar execução contínua reproduzível Windows/Linux e inventário de licenças/procedência de fonte, imagens e dependências. A escolha de licença cabe ao responsável.

**Aceitação:** código comum não acessa nem altera buffers/metadados privados; casos positivos legítimos continuam funcionando; acessos brutos autorizados são explicitamente separados; regressões equivalentes testadas em check/build/run, otimizado/sem otimização e nos dois sistemas. Não retirar bounds checks para passar testes de desempenho.

### Fase 1 — tipos estruturados e generics reais

Implementar funções e structs/classes genéricas do usuário por **monomorfização**, reaproveitando as especializações nativas já existentes. Cada combinação necessária de tipos concretos recebe código especializado; isso evita impor despacho dinâmico ou boxing apenas por se usar um parâmetro de tipo. A estratégia tem custo de compilação e tamanho de binário, que deve ser medido. [Referência primária sobre essa troca](https://rustc-dev-guide.rust-lang.org/backend/monomorph.html).

**Sintaxe implementada para funções e structs na alpha.2, ainda não suportada na 3.2:**

```assis
assis identidade<T>(valor: T): T { return valor; }
struct Caixa<T> { let valor: T; }

// Chamada explícita, para não confundir com comparações < e >:
// let numero: int = identidade::<int>(42);
// let caixa: Caixa<int> = new Caixa<int>(42);
```

A semântica de cópia/move depende do tipo concreto e de seu contrato de ownership; o exemplo não autoriza copiar proprietários. Sua aceitação inicial deve ser testada com escalares e com as representações já definidas, ampliando para recursos gerenciados somente após os contratos da fase 2.

Trabalho técnico:

- Introduzir identidades estáveis de definições e tipos (`DefId`/`TypeId`, nomes ilustrativos), aplicações de tipo e variáveis de tipo. Não representar toda a semântica apenas concatenando nomes.
- Incluir tipos de função e informação de efeitos nessa representação. Antecipar funções como valores e composição para esta fase; a integração de eventos da fase 4 depende desse recurso, não deve ser seu primeiro desenho.
- Armazenar declarações genéricas como AST/representação tipada, com posições de origem. **Não generalizar o replace textual de collections.h para código arbitrário.**
- Resolver argumentos de tipo, criar chave canônica de especialização, cache e fila de trabalho transitiva. Emitir uma especialização por definição/argumentos/ABI e somente instâncias necessárias.
- Preservar símbolos entre módulos, recursão legítima, tipos aninhados e diagnósticos que apontem declaração e instanciação. Distinguir recursão finita de expansão ilimitada de tipos, com limites e erro determinístico.
- Para a primeira versão, verificar operações do corpo após substituição concreta; documentar esse comportamento. Planejar constraints/interfaces com despacho estático para a etapa seguinte, sem fingir que já existem.
- Migrar gradualmente Array/HashMap para a infraestrutura comum, mantendo seus contratos. Atualizar gramática, editor, assinaturas, exemplos, instaladores e empacotamento.

**Aceitação:** identidade<int>/byte/bool, Caixa<int>/text, composição com Array/HashMap, múltiplos parâmetros, módulos, recursão suportada, nomes iguais em contextos distintos, erros de aridade/tipo, instanciações repetidas e abusos de expansão. Benchmark de função genérica versus equivalente escrita manualmente; crescimento de código e tempo de compilação registrados. A análise de ownership deve rodar sobre cada instância concreta antes da emissão.

### Fase 2 — ownership útil em toda a aplicação e erros por valor

- Definir contratos de entrada e retorno: consumo, empréstimo compartilhado/mutável e relação entre a vida do retorno e de suas origens. Retornar referência para local deve ser rejeitado.
- Incluir campos proprietários, recursos compostos, destruição determinística e movimentação parcial, com invariantes explícitas. Dar suporte seguro a Texto, arquivos e coleções de objetos.
- Substituir a análise local por análise de fluxo onde necessário. Manter a regra de acesso exclusivo; otimizações de vida útil devem ser comprovadas, não inferidas por conveniência.
- Definir tipos Copy/Move, layout/alinhamento/tamanho de cada tipo e semântica de structs por valor em uma evolução versionada. Na base 3.2, `value_size` só distinguia 1 e 8 bytes. A alpha.7 implementa o layout Copy e a ABI correspondente; variantes Move inline continuam abertas.
- Implementar tipos de soma/enums e pattern matching suficientes para Result<T,E>/Option<T>; só depois definir operador de propagação. Diferenciar erro de entrada/OS recuperável de bug fatal.
- Fazer matching exaustivo e semântica de dados imutáveis parte da aceitação funcional F2. Projetar captura por valor/move/borrow junto das vidas, evitando closures com referências a locais destruídos.
- Migrar bibliotecas do padrão “dispose e free em cada caminho” para APIs seguras. A propagação deve liberar recursos, sem duplicar destruição ou impor alocação para Result<int,E> escalar.

**Aceitação:** funções recebem/devolvem objetos e buffers sem fuga, arquivos fecham em todos os caminhos, recursos aninhados são liberados uma vez, erros de entrada não derrubam a aplicação inteira, invariantes sobrevivem a move/retorno/propagação. Testar interações com generics, coleções, callbacks e compatibilidade legada explícita.

### Fase 3 — texto completo, números e bibliotecas para CLI reais

- Adotar representação explícita de dados/comprimento para texto e slices, com ownership separado do empréstimo. Resolver passagem por parâmetro, retorno, campo e coleção; não apenas cachear locais. Definir como interagir com strings C terminadas em zero.
- Manter bytes binários independentes de UTF-8 e permitir NUL em buffers. Definir indexação por byte versus iteração por caractere e rejeição de UTF-8 inválido onde exigido.
- Acrescentar tipos inteiros de largura fixa e f64/f32 conforme especificação de overflow, conversão, NaN/infinito e comparação. Implementação nativa e layout precedem bibliotecas matemáticas mais amplas.
- Entregar arquivos/caminhos/argumentos, io em blocos, tempo, logs e JSON/configuração, integrados aos contratos da fase 2. Melhorar CSV e codificação para fluxos e volumes limitados.
- Incluir namespaces/visibilidade pública e privada para evitar colisões reais de bibliotecas. Planejar manifesto versionado, lockfile e resolução offline reproduzível antes de downloads automáticos.

**Aceitação por aplicação A:** ferramenta de terminal escrita em AssisScript que recebe argumentos, lê CSV/JSON de arquivo, valida entradas, gera um resultado persistente e relata erros com códigos de saída. Deve operar com arquivos grandes em memória limitada, caminhos Unicode e falhas de permissão, em Windows/Linux. O programa não pode depender de um helper Python/C para fazer o trabalho que a linguagem ainda não oferece.

### Fase 4 — integração nativa, eventos, rede e persistência

- Definir FFI/ABI C, representação de dados, chamadas/callbacks, fechamento de handles e dependências opcionais por plataforma. Não confundir a ABI interna atual com ABI C.
- Integrar funções como valores e closures já previstas nas etapas F1/F3 com callbacks externos. Event loop, temporizadores e cancelamento devem ter contratos verificáveis e efeitos explícitos.
- Acrescentar rede e HTTP/TLS com limites, validação de certificados, resolução de nomes e cancelamento. Avaliar implementações e licenças antes da escolha; não produzir criptografia nova como efeito colateral deste plano.
- Acrescentar IPC/processos e persistência. Antes de threads, definir atomics, races, segurança de compartilhamento e sincronização do alocador; ele hoje é de uma thread.

**Aceitação por aplicações B/C:** um cliente de rede e um serviço persistente de teste, com falhas simuladas, timeout, desconexão, carga concorrente e recuperação de erro. Integrar armazenamento por API documentada. Medir estabilidade por pelo menos 24 horas em ambiente controlado, limites de RAM e liberação de conexões/handles. Testes locais reproduzíveis devem preceder dependência de serviços públicos.

### Fase 5 — backend, depuração e desempenho sustentado

Esta frente pode avançar em pequenos incrementos após a fase 0, mas não deve alterar simultaneamente todas as representações de dados.

- Separar lexer/parser/resolução/tipagem, IR e emissão, preservando diagnósticos e testes. A primeira IR deve ter operações tipadas, efeitos explícitos, blocos e fluxo de controle.
- Acrescentar propagação de constantes, remoção de código morto, inlining limitado, análise de intervalos e alocação de registradores mais ampla. Bounds só podem ser removidos quando a prova sobreviver a mutação e alias.
- Especificar convenção de chamadas e interfaces com syscalls/Win32/FFI. Validar recursão, preservação de registradores, argumentos mistos e retornos compostos antes de medir ganho.
- Entregar ELF PIE, símbolos/linhas e ferramentas de diagnóstico; avaliar DWARF e suporte Windows correspondente. Manter separação de código/dados e proteção de memória.
- Só depois estabilizar interfaces de backend para ARM64/macOS. Novos alvos precisam de geração, runtime, instaladores e CI próprios.

**Aceitação:** equivalência de resultados entre modos de emissão e referência independente, ausência de regressões de segurança, ganhos reproduzíveis nos casos relevantes e rastreabilidade de falhas. O novo backend deve ser adotado por evidência, sem reescrita total sem comparativo.

### Fase 6 — ferramentas, distribuição e oferta comercial delimitada

- Comandos fmt/test/doc, integração de editor e LSP independente, documentação gerada da API e guia de migração. Decidir aliases/entrada main preservando compatibilidade documentada.
- Builds reproduzíveis e CI Windows/Linux limpos, sem depender de arquivos ignorados de build. Regerar blobs do runtime ao mudar assembly e atualizar os emissores/harnesses de plataforma juntos.
- Inventário de licenças/procedência, versão suportada, política de compatibilidade, changelog, atualização/rollback, canal de falhas e política de correções de segurança. Não decidir sozinho a licença do usuário.
- Confirmar o mesmo conjunto de fontes, compiladores e manuais no instalador, VSIX e ZIP. Bibliotecas novas exigem atualizar catálogo e listas dos dois instaladores; copiar o arquivo para stdlib não conclui a integração.
- Só chamar de produto estável quando os critérios técnicos da oferta específica forem atendidos; um pacote vendável de desenvolvimento experimental deve ser identificado como tal.

**Aceitação:** terceiro consegue instalar, compilar, testar, depurar e distribuir as aplicações A/B/C seguindo apenas documentação pública; atualização e remoção não perdem dados ou alteram preferências sem necessidade; dependências e limitações são explícitas.

## 6. Política de desempenho

Os dados 3.2 estão em [nativo-3.2.md](../benchmarks/resultados/nativo-3.2.md) e [JSON](../benchmarks/resultados/nativo-3.2.json). Exemplos das medianas registradas, em milissegundos:

| Carga | AssisScript 3.2 | C -O2 |
| --- | ---: | ---: |
| Aritmética | 17,134 | 19,030 |
| Collatz | 67,542 | 47,371 |
| Um milhão de alocações | 17,924 | 12,522 |
| Percurso de texto | 0,609 | 0,833 |

São quatro programas, com início de processo incluído. Os tempos pequenos e a variação observada impedem concluir superioridade ou equivalência geral. C++ não foi medido nessa entrega. O ganho de cerca de 607 vezes em alocação é contra a versão anterior deste projeto nesse teste, não contra C.

Para cada mudança relevante:

1. Conferir resultados e semântica antes do tempo. Usar referências independentes para inteiros, texto, coleções e parser; `--no-opt` sozinho não é oráculo.
2. Medir núcleo de trabalho suficientemente longo, separar início do processo e compilação e intercalar variantes para reduzir viés de aquecimento/frequência.
3. Registrar CPU, OS, compiladores/opções, tamanhos das entradas, amostras, variabilidade, tamanho de binário, tempo de compilação e pico/retenção de RAM. Medir monomorfização e destruição, não só loops escalares.
4. Incluir arquivos, texto/UTF-8, JSON/CSV, alocação de objetos vivos, árvores/grafos, hash adverso, generics contra código manual e aplicações completas. Comparativos C/C++ devem preservar comportamento observável e explicitar diferenças de verificações.
5. Investigar regressões repetidas acima de 5% quando excederem o ruído; esse é um limiar inicial de investigação, não uma garantia universal. Uma regressão necessária para corrigir segurança deve ser identificada e compensada por otimizações comprovadas, nunca escondida removendo validações.

Não introduzir GC global obrigatório, interpretação geral, boxing ou despacho dinâmico obrigatório como atalho para implementar generics. Despacho dinâmico ou outros modelos futuros devem ser escolhas explícitas com custos documentados.

## 7. Preparação para o navegador futuro

A visão do usuário é um navegador personalizável, com HTDL, linguagem de estilo própria e AssisScript como linguagem de script, com foco em privacidade e vários provedores de busca. **Este plano não implementa o navegador, o HTDL, a linguagem de estilos nem uma engine de busca.** Os contratos das duas linguagens externas devem ser recebidos de seus projetos; não inventar uma gramática e chamá-la de compatível.

### Host nativo e scripts de páginas são ambientes diferentes

O navegador pode ser uma aplicação nativa feita em AssisScript. Um script recebido de uma página não deve herdar automaticamente ponteiros brutos, acesso a arquivos/rede do host, FFI ou permissões do processo principal. Ownership não substitui isolamento e uma falha de renderer não pode comprometer toda a aplicação.

Como referência de arquitetura, Chromium separa componentes e usa processos com acesso restrito para conter falhas; o isolamento de sites acrescenta fronteiras contra acesso a dados de outros sites. A proposta para o AssisScript deve ser avaliada à luz desses objetivos, sem copiar detalhes automaticamente. [Arquitetura multiprocesso](https://www.chromium.org/developers/design-documents/multi-process-architecture/), [isolamento de sites](https://www.chromium.org/Home/chromium-security/site-isolation/).

Planejar dois perfis explícitos da linguagem: aplicação confiável e script restrito. Para o segundo, decidir entre execução verificada/VM, backend isolado ou código nativo restrito por uma arquitetura demonstrada. Qualquer escolha exige limites de CPU/memória, interrupção de loops, permissões por origem, mediador de operações, validação de IPC e testes de fuga. Não reutilizar o executável AOT irrestrito atual como ambiente seguro de páginas.

### Recursos que a linguagem deve conseguir expressar

- Árvores de documentos, grafos de referências, eventos e objetos de vida longa, sem depender de free espalhado. Ownership de grafos exige estratégia: arenas por documento, IDs com geração, referências fracas e fechamento explícito são opções a avaliar; contagem de referências sozinha não resolve ciclos.
- Entrada em fluxos, parsers incrementais, erros de sintaxe recuperáveis e limites para entradas malformadas.
- Layout numérico, fontes, escrita bidirecional, imagens, renderização, acessibilidade e eventos. Esses subsistemas pertencem a bibliotecas/projetos próprios, não todos ao compilador.
- Threads ou event loop, processos/IPC, cancelamento e isolamento de componentes. Alocação atual de uma thread não autoriza presumir concorrência segura.
- Bindings controlados entre documento, estilo e script, com ownership/handles e revogação ao fechar ou navegar uma página.

### Privacidade verificável e busca

Definir modelo de ameaças, dados coletados, armazenamento, permissões, política de logs e conexões de fundo. Personalização deve considerar exposição de características identificáveis do usuário; “total privacidade” precisa ser traduzida em propriedades testáveis, sem promessa absoluta de anonimato.

Adaptadores de provedores de busca devem ser separados do motor de renderização e do compilador. Uma busca própria é outro produto: coleta/indexação, ranking, atualização, resistência a abuso e avaliação de relevância exigem corpus, métricas e infraestrutura. Qualidade comparável à desejada pelo usuário não pode ser deduzida da velocidade da linguagem nem prometida por esta entrega.

O primeiro experimento futuro deve ser um visualizador offline de um subconjunto especificado de HTDL, seguido por eventos/scripts restritos e testes de isolamento. Isso só pode demonstrar viabilidade desse subconjunto; não equivale a um navegador seguro ou compatível com a Web existente.

## 8. Como decidir se foi suficiente

| Nível | Evidência exigida | Situação atual |
| --- | --- | --- |
| Linguagem experimental utilizável | Exemplos e ferramentas pequenas, instalação e comportamento documentados | Sim, com restrições |
| Base para CLI de uso real com dados persistentes | Aplicação A, erros externos, arquivos/argumentos, memória e distribuição | A delimitada validada na alpha.7; não generalizar além do dialeto/contratos demonstrados |
| Produto de desenvolvimento de uso geral | B01 resolvido, contratos safe/unsafe, generics, ownership completo para APIs, debug e manutenção | Ainda não atingido |
| Plataforma para serviços e desktop | Aplicações B/C, integração, estabilidade, observabilidade, gráficos quando necessários | Ainda não atingido |
| Plataforma para navegador com conteúdo hostil | Isolamento demonstrado, perfis restritos, permissões, quotas e subsistemas de documentos/renderização | Ainda não atingido |

Após cada fase, revisar a pergunta principal e registrar: aplicação que passou a ser possível, evidência nova, limitação remanescente e impacto de desempenho. Contar funcionalidades ou passar mais testes unitários não substitui concluir essas aplicações e seus testes adversos.

## 9. Passagem operacional para a próxima instância

### Contexto e arquivos

- Workspace Windows externo: `C:\Users\babus\Desktop\AssisScript`.
- Raiz real do compilador: `C:\Users\babus\Desktop\AssisScript\AssisScript`.
- Compilador principal: `src/assisc.c`. Tipos/geração de coleções: `src/collections.h`. Análise local: `src/ownership.h`.
- Runtime: `src/runtime.S`, `src/runtime_win.S`, `src/runtime_memory.inc`, `src/runtime_io.inc` e os headers de blobs gerados. PE: `src/pe_writer.h`; ELF é emitido em assisc.c.
- Fontes/importação: `src/modules.h`; catálogo: `stdlib/catalogo.json`; contratos atuais: [MELHORIAS-3.2.md](MELHORIAS-3.2.md) e [MEMORIA-OWNERSHIP.md](MEMORIA-OWNERSHIP.md).
- Biblioteca: `stdlib/`; editor: `vscode-assisscript/`; instaladores: `instalar.sh` e `src/windows_setup.c`.
- Testes: `tests/test-development.js`, `test-v3.js`, `test-v31.js`, `test-v32.js`, suítes Windows/shell e `tests/pe_probe.c`. A geração do corpus 3.2 usa `ASSIS_V32_FIXTURE_DIR`, e `tests/test-v32-portable.py` permite executá-lo sem Node no Linux.
- Desempenho: `tools/benchmark-native.py`. Pacotes: `tools/package-vscode.py`, `tools/package-release.py`, `tools/verify-release.py`.
- Ferramentas disponíveis na etapa anterior: MinGW em `C:\msys64\ucrt64\bin`, Node no Windows e Ubuntu via WSL. Redescobrir caminhos/disponibilidade; não depender de caches locais ou snapshots de build para uma release limpa.
- Não foi encontrado repositório Git na raiz examinada nem instrução AGENTS.md nas buscas feitas. Conferir novamente antes de implementar; não presumir histórico recuperável. Preservar uma base comparável antes das primeiras alterações.

### Ordem inicial recomendada quando a implementação for solicitada

1. Ler este plano e confirmar o estado real dos arquivos; não repetir como fatos atuais resultados antigos de testes.
2. Confirmar que os testes negativos de B01 continuam rejeitados; a correção e a suíte test-evolution já foram entregues na alpha. Não repetir os programas inseguros da base como executáveis.
3. Fixar a especificação mínima de tipos/generics/ownership e a fronteira safe/unsafe, registrando migração para mudanças incompatíveis.
4. Executar a fase 1 em incrementos revisáveis: representação de tipos, funções genéricas, structs/classes genéricas, instâncias/módulos e migração das coleções. Verificar corretude e custo a cada incremento.
5. Avançar pela fase 2 antes de anunciar generics com recursos proprietários ou API padrão segura. Depois concluir a aplicação A com as bibliotecas da fase 3.

Uma entrega de implementação só se encerra com fontes, diagnósticos, documentação, exemplos, testes relevantes, medições e pacotes consistentes com o escopo concluído. Se algum gate falhar, registrar o bloqueio e não aumentar a classificação de prontidão.

**Passagem histórica após a alpha.6 (superada pelo handoff alpha.7):** ler [o handoff atual](HANDOFF-3.3-ALPHA.6.md), [ownership entre funções](OWNERSHIP-FUNCOES.md) e a [régua de progresso](PROGRESSO.md). Consumo/empréstimos/vidas explícitas e campos own de structs já existem; não reiniciar essas frentes. Continuar destruição de classes/Texto e coleções de donos, layout por valor e variantes/Result/Option/matching; depois arquivos/argumentos e aplicação A. Não ampliar pure a objetos/text sem os contratos que ainda faltam. Preservar os estados históricos da métrica e atualizar percentuais/evidências nas próximas entregas.

**Estado histórico do planejamento:** naquela etapa somente este documento havia sido acrescentado. Esse estado foi substituído pela execução descrita em [HANDOFF-3.3-ALPHA.md](HANDOFF-3.3-ALPHA.md). Não usar os pacotes históricos 3.2 para testar `private`, `val` ou `pure`.

# AssisScript no navegador

**Nota de 27/10/2026:** as avaliações de implementação e as versões citadas abaixo são históricas. Esta rodada de planejamento não consultou nem executou o projeto AssisScript durante seu teste de 24 horas. A linguagem pode já ter resolvido limitações observadas antes. Os [contratos de capacidades](18-arquitetura-nativa-e-capacidades.md) descrevem o que a integração futura precisa demonstrar, sem presumir ausência atual de recursos.

Estado: diagnóstico pontual e proposta de integração, 24/10/2026. O AssisScript está sendo desenvolvido em paralelo; este documento não congela sua evolução nem propõe uma linguagem separada.

## O que já existe

Foram lidos o compilador C, os cabeçalhos de módulos, coleções e ownership, a documentação, bibliotecas e os testes de evolução. Foram executados apenas comandos de identificação e verificações pontuais, descritas no registro de validação ao final deste documento. Não foi executada a suíte completa do projeto nem reconstruído o compilador.

| Observação | Evidência local | Implicação para o navegador |
| --- | --- | --- |
| Compilação direta para x86_64, com PE Windows e ELF Linux | `src/assisc.c`: `generate`, `write_executable`, seleção de `--target`; `src/pe_writer.h` | Esses executáveis não são o formato de um programa embutido de página |
| Lexer, parser, checagem de tipos e geração estão no mesmo programa C | `src/assisc.c`: `parse`, `check`, `generate` | Há frontend reutilizável, mas será necessário separar dependências do backend |
| Sintaxe legível preserva `assis`, `ASSIS`, entrada `assis_assis` e aliases históricos | Tabela `words` e parser; `docs/LINGUAGEM.md` | A identidade da linguagem pode ser preservada na integração |
| Tipos escalares incluem int64, byte, bool e text; classes e structs são referências | `TypeKind`, checagem e manual | Não pressupor floats, structs por valor ou objetos JavaScript |
| Módulos usam `#yuri` e `.pillow`, com nomes compartilhados | `src/modules.h`; `docs/BIBLIOTECAS.md` | Reutilizar o modelo, acrescentando um resolvedor de recursos adequado ao host |
| Coleções são especializadas pelo compilador | `src/collections.h`; `parse_collections` | O destino embutido precisa implementar as operações emitidas para coleções |
| Há gestão manual de memória; o fonte atual também contém `own`, `borrow`, `move`, `defer` e verificações de ownership | `src/ownership.h`; `tests/test-v32.js` | Reutilizar essas verificações, sem concluir que referências legadas ficaram automaticamente seguras |
| O fonte em desenvolvimento também inclui `for`, `div`, leitura de bytes e relógio | Tabela de tokens e parser; testes 3.2 | O perfil de navegador deve mapear ou rejeitar operações de ambiente explicitamente |
| Diagnósticos estruturados e modo de biblioteca já existem | `check --library`, `--diagnostics=json` | Base útil para editor, verificador de páginas e erros integrados |
| Não foi encontrado destino WebAssembly, FFI pública ou mecanismo geral de callbacks de página | Destinos CLI, parser, tipos e documentação inspecionados | São capacidades a implementar; não há uma chave de configuração que já embuta a linguagem |

Na leitura inicial, o fonte e o manifesto da extensão declaravam **3.2.0**, enquanto `bin/assis.exe version` e `doctor` informavam **3.1.0**. Na verificação posterior dos exemplos, o binário já informou **3.2.0**, sem alteração deste trabalho no projeto irmão. O autor confirmou desenvolvimento simultâneo. Assim, cada observação corresponde a um momento; a presença de um recurso no fonte não foi confundida com uma validação completa dele.

O manual e a gramática ainda identificavam 3.1 e descreviam limites anteriores, como ausência de `for`. A prova de conceito deverá escolher um snapshot do AssisScript em coordenação com seu desenvolvimento, sem exigir que esta proposta altere a versão em andamento.

## O que significa embutir a linguagem

Além de hospedar programas de página, o navegador final deverá ser **implementado em AssisScript**, conforme esclarecimento do autor. O aplicativo nativo e o programa de página usam a mesma linguagem com autoridades diferentes. Este documento detalha principalmente o segundo ambiente; a evolução nativa e a integração com plataformas estão na [visão do navegador](08-navegador-assisscript-privacidade-e-busca.md).

O navegador terá a implementação necessária para executar programas AssisScript durante toda a vida da página. O autor escreve `.assis`; o ambiente fornece eventos, memória da instância, funções hospedeiras e serviços permitidos.

O runtime não encerra a aba quando a função de entrada retorna. A adaptação de `assis_assis` inicializa o programa e devolve o controle ao navegador; os manipuladores continuam chamáveis na mesma instância. O uso independente da linguagem conserva o comportamento de entrada e saída de um programa nativo.

O **runtime** precisa estar no navegador. O **compilador** completo pode ficar no SDK de desenvolvimento, produzindo módulos previamente compilados. Compilação dentro do navegador é uma possibilidade posterior e deverá ocorrer sob limites e isolamento próprios.

## Caminhos avaliados

| Caminho | O que reaproveita | Trabalho adicional e limite | Direção |
| --- | --- | --- | --- |
| Carregar o código x64 gerado no processo do navegador | Parte do emissor atual | ABI, relocação, chamadas hospedeiras e isolamento; ponteiros seriam nativos e o código teria poder excessivo | Não usar como modelo de página |
| Executável nativo em processo isolado com IPC | Backend atual | Sandbox por sistema operacional, protocolo de interação e portabilidade; não entrega runtime embutido por si só | Pode servir a ferramentas, não é a recomendação central |
| VM própria de bytecode/interpretador | Parser, tipos e parte da semântica | Implementar e manter instruções, runtime, limites, depuração e validação | Alternativa viável se houver requisito forte de VM própria |
| Novo destino WebAssembly com runtime embutido | Frontend, tipos, módulos, análise de ownership e semântica | Novo emissor, runtime de memória e biblioteca hospedeira; não é conversão direta de PE/ELF | Recomendação inicial para a prova de conceito |

WebAssembly seria a representação de execução do AssisScript, não uma linguagem de autoria adicional exigida do usuário. O modelo permite imports controlados e memória isolada do host. Erros de ponteiros ainda podem corromper objetos dentro da memória do próprio módulo; o backend e as APIs continuam responsáveis por suas verificações. [Segurança de WebAssembly](https://webassembly.org/docs/security/).

## Plano de evolução do compilador

Fluxo pretendido:

```text
fontes .assis e pacotes .pillow
  -> carregamento de módulos
  -> lexer e parser
  -> símbolos, tipos e ownership
  -> representação intermediária pequena e independente do destino
     -> emissor x64 + runtime nativo -> PE / ELF
     -> emissor wasm32 + runtime da linguagem -> módulo de navegador
```

O primeiro trabalho é explicitar a fronteira entre frontend e emissão, atualmente no mesmo arquivo. Não é necessário reescrever o compilador em outra linguagem. Uma representação intermediária pequena deve expressar valores, blocos, chamadas, memória e posições de fonte, preservando a ordem dos efeitos. A introdução pode ser gradual; o caminho nativo deve continuar verificável durante a migração.

O nome sugerido de destino é `browser-wasm32`. Ele ainda não existe. O perfil identifica as APIs permitidas; compilar para WebAssembly genérico não implica automaticamente ter permissão para interagir com a página.

### Semânticas que o novo destino deve preservar

- `int` permanece int64, com overflow modular, curto-circuito e avaliação da esquerda para a direita. `byte` e `bool` conservam suas regras.
- Divisão por zero, deslocamento inválido e acesso fora do limite continuam diagnosticados. A divisão de INT64_MIN por -1 precisa de tratamento explícito: a semântica documentada do AssisScript não deve mudar por causa de uma instrução WebAssembly que produz trap.
- `text` continua UTF-8 imutável com as regras documentadas de comprimento em bytes. O contrato de memória deve ser identificado pela versão do compilador; uma evolução futura de texto não deve ser escondida no backend.
- Classes continuam referências com despacho de métodos; structs continuam referências enquanto essa for a semântica geral da linguagem.
- `own`, empréstimos e limpezas, quando presentes no snapshot escolhido, conservam seu comportamento em retorno, laços e erros. Não transformá-los em um segundo modelo de ownership apenas para páginas.
- Ponteiros do módulo são offsets em sua memória linear. Nunca apontam para objetos do navegador. Endereços wasm32 têm 32 bits, mesmo com `int` de 64 bits.
- Definir um `DataLayout` do destino para tamanhos, alinhamento, campos e ponteiros; eliminar suposições implícitas de endereço x64. Não usar o tamanho de ponteiro do compilador hospedeiro como tamanho de ponteiro do programa.
- Variáveis cujo endereço é obtido precisam de representação endereçável na memória linear. Reservar um intervalo nulo e verificar nulo antes de dereferenciar; offset zero não vira automaticamente um erro em toda leitura WebAssembly.

Os runtimes em assembly Windows/Linux não podem ser incorporados ao módulo como estão. Será necessário fornecer alocação/liberação, texto, coleções, falhas e demais primitivas em implementação apropriada ao destino. O primeiro módulo pode cobrir apenas funções e inteiros, declarando claramente seu subconjunto; a versão pública deve ter uma matriz explícita de compatibilidade.

`print` deve escrever no console de desenvolvimento da página por uma API de log. Leitura de terminal deve ser rejeitada no perfil de página, com diagnóstico útil. Relógio e futuras operações de rede ou arquivo só existirão por serviço hospedeiro. Não conceder WASI genérico, acesso a processos ou diretórios do usuário implicitamente.

## Módulo de integração com a página

Proposta de biblioteca virtual do SDK:

```assis
#yuri <browser/htdl.assis>
```

Esse módulo **não existe atualmente**. Seu reconhecimento registrará símbolos hospedeiros tipados no compilador do perfil de navegador. Não será uma biblioteca de fontes comuns que consegue chamar o motor sem suporte do compilador. O desenho evita exigir nova sintaxe geral de FFI para o primeiro exemplo; a forma interna de registrar imports deve ser implementada e testada no compilador.

O prefixo `htdl_` fica reservado aos símbolos desse módulo somente no perfil de navegador. Nomes existentes no uso nativo não são retroativamente proibidos. A inclusão duplicada segue as regras de deduplicação do sistema de módulos.

### Assinaturas de autoria propostas

A tabela é um contrato de funções, não código de declarações sem corpo já aceito pelo parser.

| Assinatura | Contrato |
| --- | --- |
| `htdl_no_por_id(id: text): int` | Identificador positivo do nó; zero se não encontrado |
| `htdl_no_texto(no: int, valor: text): int` | Substitui conteúdo textual de `heading`, `paragraph`, `text`, `button`, `link` ou `label`; copia os bytes |
| `htdl_no_texto_int(no: int, valor: int): int` | Mesma operação, com formatação decimal de int64; conveniência inicial para não exigir alocação textual no contador |
| `htdl_no_hidden(no: int, valor: bool): int` | Oculta ou mostra a subárvore |
| `htdl_no_disabled(no: int, valor: bool): int` | Altera estado em `button` ou `input` |
| `htdl_no_focar(no: int): int` | Solicita foco em controle elegível |
| `htdl_no_checked(no: int): bool` | Lê checkbox válido; tipo ou identificador inválido gera falha de contrato |
| `htdl_no_valor_tamanho(no: int): int` | Comprimento UTF-8 do valor de `input`, ou status negativo |
| `htdl_no_valor_copiar(no: int, destino: *byte, capacidade: int): int` | Copia valor e terminador zero; retorna bytes do valor ou status negativo; capacidade inclui o terminador |
| `htdl_estado_int(chave: text): int` | Lê estado inteiro da instância; chave ausente vale zero |
| `htdl_estado_int_definir(chave: text, valor: int): int` | Grava estado inteiro da instância |
| `htdl_evento_cancelar(evento: int): int` | Cancela ação padrão de evento cancelável ainda ativo |

Funções mutadoras retornam zero no sucesso; valores negativos indicam falhas recuperáveis: `-1` identificador inválido/expirado, `-2` tipo ou operação incompatível, `-3` texto/capacidade inválidos, `-4` quota. Leitura e cópia de valor usam esses mesmos negativos. Busca ausente não é erro. A leitura booleana de checkbox é deliberadamente estrita; erro de contrato suspende o programa e aparece no console. APIs futuras poderão oferecer resultados tipados mais ricos.

`htdl_no_texto` substitui os filhos textuais anteriores; seus identificadores são invalidados. O identificador do nó receptor permanece válido. Não interpreta marcação. Uma string contendo `<div>` aparece como texto, o que evita criar uma segunda entrada de parser em cada atualização.

`htdl_no_valor_copiar` primeiro valida tudo; se a capacidade for insuficiente, não escreve nada e retorna `-3`. Copia inclusive o terminador, mas o retorno exclui esse byte. Na 0.1 não há reentrada nem concorrência entre medir e copiar. Ponteiros continuam sujeitos à disciplina de memória do AssisScript; validar a memória linear não prova que o buffer pertence a uma alocação válida dentro do módulo.

Esse estado por chave é uma facilidade da biblioteca hospedeira, sem armazenamento persistente. Permite um primeiro programa com estado entre eventos sem depender de variáveis globais, closures ou novos recursos de linguagem. Objetos alocados pelo próprio programa também podem persistir na memória da instância conforme as regras gerais do AssisScript. Estado persistente, coleções reativas e binding automático não entram no primeiro contrato.

### Manipuladores e ciclo de execução

Um atributo `on:click="incrementar"` exige:

```assis
assis incrementar(alvo: int, evento: int): void {
    // Chamadas à biblioteca hospedeira.
}
```

São funções nomeadas normais. O compilador/empacotador recebe do HTDL a lista de funções referenciadas, verifica assinaturas e as exporta pelo nome. Não exige ponteiros para funções, closures ou `eval`.

`alvo` é identificador de nó. `evento` é identificador de evento válido só durante essa chamada. O host valida a categoria do recurso e seu documento, evitando usar um evento como nó. IDs removidos e IDs de outra instância são rejeitados, mesmo se numericamente parecidos.

Uma função é executada por vez. A página não mantém um `while(true)` para receber eventos: o navegador chama a função quando necessário. Ao terminar a entrada, o host conserva a instância; ao encerrar a página, descarta tudo. Alterações aceitas são aplicadas em ordem, com desenho consolidado depois da tarefa. Se houver trap no meio, não há rollback automático: preservar as alterações concluídas, suspender a instância e cancelar a ação padrão pendente.

Ausência de export ou assinatura incorreta impede iniciar o programa. Eventos de entrada só são entregues após inicialização bem-sucedida. Funções hospedeiras não chamam novamente o programa enquanto uma função dele estiver na pilha.

## ABI da primeira prova de conceito

Recomendação: módulo WebAssembly Core, uma memória não compartilhada e imports em namespace versionado `htdl_v1`. Evitar, nesta etapa, um sistema de componentes, linking dinâmico, threads ou propostas opcionais que não sejam necessárias.

O runtime escolhido precisará ser acessível ao aplicativo AssisScript por uma interface definida. Uma ABI/FFI ou binding de desenvolvimento é trabalho adicional; a escolha de WebAssembly não implica um host final escrito em Rust.

| Valor na linguagem | Na fronteira WebAssembly |
| --- | --- |
| `int`, identificador de nó/evento | `i64` |
| `bool`, status curto | `i32`, com validação do domínio |
| `text` enviado ao host | Par `offset: i32, tamanho: i32` obtido pelo adaptador do compilador |
| Buffer de saída | `offset: i32, capacidade: i32`, validado antes de copiar |

A assinatura de autoria pode retornar `int` e ser adaptada de um status `i32` por extensão com sinal. O mapeamento é gerado pelo compilador e descrito pela versão da API; nunca reinterpretar arbitrariamente a convenção nativa de chamadas do AssisScript.

Antes de uma leitura ou escrita, o host deve validar o intervalo inteiro sem overflow, o tamanho máximo e UTF-8 quando for texto. Converter capacidade int64 para i32 somente depois de verificar seu intervalo. O host copia dados antes de reentrar no módulo ou permitir crescimento de memória; não guarda ponteiros para buffers do convidado. O núcleo 0.1 não precisa retornar referências textuais do host ao convidado.

O carregador verifica metadata de linguagem/API, exports e imports contra uma lista permitida; não confia apenas no sufixo `.wasm`. Uma assinatura de arquivo identifica o publicador quando houver esse recurso, mas não dispensa isolamento.

## Execução longa, assíncrona e erros

A prova de conceito deve configurar orçamento de instruções e limite de memória e pilha. Um laço infinito precisa suspender o programa sem travar a interface. Wasmtime oferece fuel e interrupção por épocas, que precisam ser ativados e configurados pelo host. As funções hospedeiras exigem também limites de tempo, bytes e filas. [Configuração oficial](https://docs.wasmtime.dev/api/wasmtime/struct.Config.html).

Rede não entra na API inicial. Quando chegar, seguirá pedidos identificados e entrega posterior de evento a uma função nomeada. Isso permite comportamento assíncrono sem obrigar a linguagem a implementar imediatamente `async/await`. Cancelar a página cancela seus pedidos; uma resposta antiga nunca alcança a instância nova.

Uma evolução para `async/await`, funções de primeira classe ou gerenciamento automático de memória deve ser uma decisão geral do AssisScript. O navegador não precisa antecipar essas mudanças para executar o primeiro exemplo.

## Registro de validação deste planejamento

Os comandos iniciais retornaram AssisScript 3.1.0, host Windows x64 e backends PE32+/ELF64. O compilador usado nas verificações finais informou 3.2.0. Os arquivos da pasta AssisScript foram usados somente para leitura e verificações, sem edição.

O [contador](../exemplos/contador/README.md) passou na verificação com assinaturas substitutas temporárias do módulo proposto. Essa verificação cobre sintaxe e tipos no binário disponível; não demonstra integração com runtime, eventos reais ou renderização. O resultado efetivo fica em [VALIDACAO](VALIDACAO.md).

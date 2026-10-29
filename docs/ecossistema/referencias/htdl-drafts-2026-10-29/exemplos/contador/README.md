# Contador HTDL + AssisScript

**Exemplo de contrato futuro. Ainda não executável como página.**

[index.htdl](index.htdl) define a estrutura e os vínculos de evento. [app.assis](app.assis) é o programa AssisScript. O módulo `browser/htdl.assis` e as funções `htdl_*` pertencem à [API proposta](../../docs/03-assisscript-no-navegador.md); não estão disponíveis no compilador atual.

## Comportamento esperado

1. O navegador cria a página inteira, carrega o programa e verifica entrada e manipuladores.
2. `assis_assis()` inicializa o estado da instância e o texto em zero.
3. A ativação de **Somar um** chama `incrementar(alvo, evento)`, com identificadores fornecidos pelo host.
4. A função lê o estado e escreve o novo número no parágrafo `valor`.
5. **Zerar** chama `zerar`, restaurando estado e texto.
6. O contador para em INT64_MAX. Recarregar a página cria uma instância nova e volta a zero.

O texto alterado usa uma região acessível `polite`; o motor deverá anunciar atualizações sem transferir o foco. As classes são pontos de ligação para FluxStyle/SSC, sem estilo autoral definido neste exemplo.

O programa usa funções nomeadas, `let`, `int`, `if`, `return` e `assert`, sem exigir closures, variáveis globais ou `async/await`. O estado por chave é um serviço do host, não uma mudança na sintaxe do AssisScript. Os argumentos `alvo` e `evento` seguem o contrato uniforme, embora este programa não precise consultá-los.

## O que falta para executar

Parser e motor HTDL, destino embutido do AssisScript, runtime da linguagem nesse destino, biblioteca hospedeira, exportação das funções e fila de eventos. A prova de conceito deve demonstrar essas partes; criar funções substitutas que só retornam sucesso não implementa o navegador.

O [registro de validação](../../docs/VALIDACAO.md) distingue a verificação de sintaxe/tipos com assinaturas temporárias de uma execução real, ainda pendente.

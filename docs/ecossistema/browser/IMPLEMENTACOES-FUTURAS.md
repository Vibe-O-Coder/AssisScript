# Implementações futuras — família AssisScript

Decisões de direção do autor, registradas em **29/10/2026**. Estado: ideias para implementação futura, sem compilador, runtime ou compatibilidade declarados. Este documento pertence à documentação do AssisBrowser e fica arquivado também no GitHub do AssisScript para rastreabilidade.

## AssisScript Web

Haverá uma **versão distinta**, chamada **AssisScript Web**, destinada ao ecossistema web do navegador. Será bastante parecida com JavaScript e mais fácil para iniciantes, preservando as particularidades e a identidade do AssisScript.

Semelhança com JavaScript não promete compatibilidade ECMAScript nem execução automática de bibliotecas JS. Sintaxe, tipagem, memória, módulos, extensão de arquivo, ferramentas e ponte com HTDL/FluxStyle/SSC serão especificados em sua própria etapa. Não se deve inventar agora detalhes que o autor ainda não decidiu.

O AssisScript nativo continua sendo a base para implementar o navegador, motor e serviços. A versão Web será de autoria de páginas; seu runtime continuará sujeito a quotas, isolamento, capacidades, origem e API hospedeira. A infraestrutura de execução restrita pode ser desenvolvida por contrato antes da versão de autoria Web, sem fingir que o novo dialeto já existe.

Rascunhos anteriores em Hypertext Div Language descreviam uma única linguagem em dois ambientes. Esses trechos são históricos nesse ponto: a nova direção prevê explicitamente uma versão Web distinta. Ao revisar os contratos, atualizar a terminologia e a compatibilidade, mantendo as fronteiras de segurança já propostas.

## AssisScript Easy

Há a ideia de **AssisScript Easy** como porta de entrada para o AssisScript. A sintaxe será extremamente simples e similar à de Python, mantendo as particularidades da linguagem.

Seu escopo será criar programas básicos de terminal e, no máximo, algumas interfaces simples. Não é substituto para a linguagem nativa ou para a versão Web. A trilha de aprendizado deverá ajudar o usuário a migrar para o AssisScript, com exemplos equivalentes e diferenças explicadas.

**Será a última coisa a ser feita em todo o projeto**, depois da linguagem principal, do navegador, do buscador, do ecossistema web e das demais entregas previstas, inclusive a versão Web. Nenhum marco atual deve depender do Easy.

## Ordem e registro

As duas variantes têm especificação, backlog, critérios e relatórios próprios quando seu desenvolvimento for iniciado. Elas não entram nos 60 critérios nem nos pesos do plano atual de capacidade do AssisScript nativo. Registrar aqui uma ideia não aumenta porcentagem de implementação.

A cada mudança futura, publicar fontes, evidências e relatório no GitHub apropriado; alterações na linguagem e seus contratos devem permanecer rastreáveis no GitHub do AssisScript. A cópia arquivada deste arquivo está em `docs/ecossistema/browser/IMPLEMENTACOES-FUTURAS.md` no repositório AssisScript. Manter as duas cópias equivalentes ao alterar estas decisões.

# HTDL 0.2: recursos de apresentação e carregamento

Estado: **extensão proposta em 27/10/2026**, não implementação. A 0.1 continua definida no documento [02](02-htdl-0.1.md). As regras abaixo completam A03 da [revisão](13-revisao-extensoes-abertos-e-propostas.md); não acrescentam componentes, expressões em atributos ou submissão à rede.

## 1. Diferença em relação à 0.1

Um documento 0.2 mantém todas as regras estruturais e tipos da 0.1 e usa `version="0.2"`. Seu `head` admite ainda zero ou mais elementos vazios `type="presentation"`.

```htdl
<div type="document" version="0.2" lang="en">
  <div type="head">
    <div type="title">Reading room</div>
    <div type="presentation" src="./reading.fxs" language="fluxstyle"></div>
  </div>
  <div type="body">
    <div type="main">
      <div type="heading" level="1">Reading room</div>
      <div type="paragraph">Content remains available without presentation resources.</div>
    </div>
  </div>
</div>
```

| Atributo específico de `presentation` | Regra |
| --- | --- |
| `src` | Obrigatório, texto não vazio; referência a um recurso |
| `language` | Obrigatório; `fluxstyle` ou `ssc`, sensível a maiúsculas |

Não admite filhos nem texto além de espaços de formatação. Não admite `id`, `class`, eventos ou `data-*`, pois é metadado de `head`. A ordem entre recursos de apresentação não muda o significado dos bindings. Mantêm-se exatamente um título e no máximo um programa, nas condições da 0.1.

`language` define o parser, mesmo em uma URL sem extensão. A extensão ajuda o editor e o formato distribuído. `.flux` recebe o mesmo parser FS que `.fxs`; não há busca automática de um arquivo alternativo se `src` falhar. Em transporte remoto futuro, o tipo de conteúdo deve ser compatível com a linguagem declarada; a lista de tipos MIME ainda será registrada antes de M7.

## 2. Identidade e resolução de recursos

Para arquivos locais, o usuário abre uma aplicação com raiz explícita. Referências são resolvidas a partir do arquivo do documento e devem permanecer na raiz autorizada após normalização e resolução de links do sistema de arquivos. Proibir apenas o texto `..` não basta. Acesso a outro diretório depende de outra concessão do usuário e não ocorre por importação implícita.

Para HTTPS futuro, usar a URL final do documento como base, sem `base` de autoria no núcleo. O broker aplica política de origem, valida cada redirecionamento e entrega bytes ao processo de conteúdo. Fragmentos não identificam trechos de FS/SSC e são rejeitados em `src` de apresentação; query faz parte da identidade de rede.

A identidade de acesso ao recurso inclui contexto de aplicação/origem e URL canônica. A unidade analisada acrescenta a linguagem; uma declaração é identificada por `(recurso, linguagem, nome)`. O carregador não admite duas linguagens para a mesma identidade de acesso no mesmo conjunto. Assim:

- Carregar o mesmo recurso duas vezes com a mesma linguagem é idempotente.
- Declarar o mesmo recurso como FS e SSC é erro de carregamento.
- Dois recursos distintos podem declarar `PanelVisuals`; seus bindings resolvem nomes dentro do próprio recurso.
- Nome duplicado dentro do mesmo recurso é erro. Não existem imports entre fontes FS/SSC na 0.1.
- `.fxs` e `.flux` com bytes iguais, mas URLs distintas, continuam sendo dois recursos. Se ambos escrevem a mesma propriedade no mesmo nó, há conflito.

A chave de cache de análise acrescenta hash dos bytes e versões de gramática/contrato/perfil numérico. Reaproveitar uma AST não reaproveita estado da página, handles ou canais físicos.

## 3. Etapas do carregador

| Etapa | Operação | Autoridade e resultado |
| --- | --- | --- |
| Documento | Decodificar, analisar e validar HTDL | Nenhum programa executa durante o parser |
| Recursos | Resolver fontes FS, SSC e programa separadamente | Broker controla acesso e quotas |
| Preparação visual | Tipar FS/SSC, resolver bindings, estados e produtores | Construir candidato ainda invisível |
| Programa | Validar perfil/imports/exports e chamar entrada uma vez | Instância restrita, sem eventos de usuário durante a entrada |
| Primeira publicação | Avaliar candidato com o estado resultante da entrada | Estilos, destinos e geometria da mesma publicação |
| Interação | Liberar manipuladores quando a instância estiver pronta | Tarefas posteriores, sem reentrada |

O navegador pode mostrar uma prévia estática com padrões enquanto aguarda recursos. Essa prévia não recebe manipuladores ainda não inicializados. Não é necessário esperar imagens para inicializar o programa; uma imagem tardia só invalida medição/layout quando suas dimensões se tornam conhecidas.

Todos os recursos de apresentação declarados formam **um conjunto de ativação**. Um arquivo SSC inválido não deixa metade do conjunto autoral ativada. No primeiro carregamento, falhar esse conjunto conserva conteúdo com padrões e sem física. Isso não impede a inicialização independente de um programa válido. O estado produzido por ele fica disponível para uma futura correção.

O loader tem limites de bytes, contagem e tempo por fase; números dependem de medição. Uma falha ou timeout termina a fase com diagnóstico e alternativa estática, sem bloquear indefinidamente o documento. Não há um `ready` autoral que espere uma mola repousar.

## 4. Estados independentes

```text
Document:     loading -> validated -> visible -> disposed
Presentation: absent | preparing -> active | failed
Page program: absent | preparing -> initializing -> ready | suspended | failed
Visibility:   foreground | background
```

Uma falha de sintaxe HTDL termina a tentativa com uma página de diagnóstico do navegador; `validated` não é alcançado. Uma falha de apresentação não implica falha do programa. Um programa suspenso não desabilita o comportamento nativo de rolagem, foco e links permitidos. Não se tenta chamar um manipulador que não está disponível; ações nativas seguem a política do documento, e uma ação cujo manipulador falhou naquela tarefa é cancelada.

Cada tentativa de navegação recebe `navigationEpoch`; cada instância válida recebe `documentInstance`. Resultados assíncronos carregam ambos. Fechar/recarregar invalida o par antes de cancelar trabalhos, de modo que uma resposta tardia é descartada mesmo que o cancelamento não seja imediato.

## 5. Recarregamento e edição

Recarregar a página cria outra instância, reinicia estado e chama a entrada novamente. Uma futura ferramenta de desenvolvimento poderá trocar **somente o conjunto visual**: preparar todos os recursos candidatos, validar contra a árvore atual e publicar atomicamente. Se falhar, manter o conjunto ativo anterior; atualizar programa exige recarregamento completo no primeiro SDK.

Uma troca visual bem-sucedida conserva uma célula de estado somente se chave, escopo, tipo e padrão forem compatíveis. Alterar o contrato de uma célula existente exige recarregar, mesmo que seu valor atual coincida. Células removidas do esquema perdem sua inscrição visual; um valor de aplicação já gravado continua até o fim da instância. Estado por nó termina quando seu nó morre.

O primeiro modo de edição reinicializa todos os canais SSC no destino do novo conjunto. Continuidade entre versões de programa físico fica adiada; continuidade durante **retargeting no mesmo canal ativo** permanece obrigatória. Isso evita atribuir identidade física estável apenas a nomes de arquivo.

## 6. Diagnósticos de carregamento propostos

| Código | Condição | Recuperação |
| --- | --- | --- |
| `H310` | Recurso inacessível ou timeout | Rejeitar conjunto visual; padrões/último conjunto ativo |
| `H311` | Linguagem desconhecida ou metadados incompatíveis | Rejeitar recurso, sem tentar outros parsers |
| `H312` | Caminho/origem não autorizado | Negar acesso antes de entregar bytes |
| `H313` | Mesma identidade com linguagens diferentes | Rejeitar conjunto |
| `H314` | Versão/perfil obrigatório sem suporte | Diagnosticar capacidades incompatíveis |
| `H315` | Esquema de estado incompatível em troca visual | Solicitar recarga pela ferramenta; não apagar estado silenciosamente |

Erros internos de sintaxe/tipos preservam seus códigos F/S e a posição no recurso, com nota da declaração `presentation` que o carregou. Um `bind` vazio continua aviso e pode ganhar correspondência após uma futura mutação semântica autorizada.

Nenhum desses códigos é saída de um parser implementado. O [catálogo de cenários](19-conformidade-e-cenarios.md) usa os códigos como resultados esperados para a implementação futura.

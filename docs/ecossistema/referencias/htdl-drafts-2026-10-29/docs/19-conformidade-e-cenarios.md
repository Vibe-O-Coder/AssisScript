# Conformidade e cenários de referência

Estado: **corpus de planejamento de 27/10/2026**. Os arquivos abaixo definem entradas e resultados esperados. Não são uma suíte executada por um parser FS/SSC/HTDL, e a documentação não declara essas implementações existentes.

## 1. Três níveis de evidência

| Nível | O que comprova | Exemplo |
| --- | --- | --- |
| Integridade documental | Arquivos, links, JSON e trechos estão organizados e coerentes | A referência de um recurso aponta para um arquivo existente |
| Conformidade de linguagem | Uma implementação aceita/rejeita entradas e produz diagnósticos previstos | Parser futuro rejeita dois produtores com `F302` |
| Comportamento integrado | O navegador cumpre semântica, geometria, falhas e isolamento | Desabilitar um botão continua impedindo ativação após uma falha FS |

Conferir um arquivo HTDL com um leitor XML é apenas uma ajuda limitada no primeiro nível. Não verifica a sintaxe sem aspas, o catálogo semântico ou os contratos de execução. JSON parseável também não demonstra o resultado esperado de um cenário.

## 2. Novos exemplos de autoria

| Exemplo | O que especifica | Estado |
| --- | --- | --- |
| [Leitura adaptável](../exemplos/leitura/README.md) | Limites descendentes de largura, fluxos disjuntos e preferências de contraste/tema | Conceitual, sem programa de página |
| [Dois painéis](../exemplos/paineis/README.md) | Estado separado por nó, um mesmo fluxo e um mesmo motion reutilizados | Conceitual, API de página proposta |
| [Cartão existente](../exemplos/fluxstyle/README.md) | Estado global e mola de um canal | Traço numérico isolado já registrado, sem navegador |

Os exemplos novos não dependem de download, instalação, execução do compilador ou mudanças no projeto AssisScript. O exemplo de painéis contém fonte de autoria `.assis`, cuja API continua proposta e não foi verificada nesta rodada.

## 3. Corpus declarativo

O [índice JSON](../exemplos/conformidade/cenarios.json) usa o formato de trabalho `htdl-scenarios-draft-1`. Não é um manifesto de aplicação nem um novo formato de distribuição. Cada item tem ID estável, categoria, arquivos relativos à pasta do índice, fase e expectativa. Cenários de runtime incluem passos e resultado esperado; nomes de ações pertencem ao futuro driver de testes, não à API autoral.

Entradas negativas estão em subpastas próprias e nunca devem ser carregadas como demonstrações válidas. O contexto para FS/SSC isolados é [context.htdl](../exemplos/conformidade/context.htdl), com um nó `.box`; o driver futuro monta o conjunto indicado no cenário. Erros sem posição exata fixada ainda exigem posição válida no arquivo relevante e, em conflitos, notas para as duas origens.

| ID | Expectativa principal |
| --- | --- |
| `L01` | Leitura sem script nem SSC; sem erros de linguagem |
| `L02` | Dois painéis usam células de nó distintas |
| `H01` | Elemento sem `type` → `H201` |
| `H02` | `presentation` em documento 0.1 → diagnóstico estrutural `H2xx` |
| `F01` | Cor em `layout.width` → `F201` |
| `F02` | Dois flows sobre a mesma cor → `F302`, sem prioridade por seletor |
| `F03` | `choose(false, 1px / 0, 8px)` → `8px`, sem erro de divisão |
| `F04` | `choose(true, 8px, #fff)` → `F203`, mesmo com ramo inativo |
| `F05` | Dois defaults de estado incompatíveis → `F306` |
| `F06` | Largura final de `-1px` → `F404` |
| `S01` | SSC sem produtor FS de destino → `S302` |
| `S02` | Eixo lido e escrito diferentes → `S203` |
| `R01` | Ativar primeiro painel não altera segundo painel |
| `R02` | Falha FS conserva saídas autorais, mas respeita `disabled` atual |
| `R03` | Retorno de aba não integra backlog físico |
| `R04` | Recriar ID textual não herda estado/handle da geração anterior |

Para códigos múltiplos, o corpus exige o código principal indicado e permite notas adicionais independentes. Nenhuma execução deve “passar” por escolher o último escritor, saturar um número ou avaliar um ramo curto desnecessariamente.

## 4. Matriz mínima antes de congelar o núcleo

| Área | Evidência exigida | Decisão que pode mudar |
| --- | --- | --- |
| Sintaxe | Corpus de UTF-8, escapes, sem aspas HTDL, EOF, comentários e unidades | Limites do leitor e recuperação do editor |
| Tipos/grafo | Ciclos com caminho, forward references, branches curtos e tipos enumerados | Gramática final e mensagens |
| Números | Vetores de conversão, soma/produto/divisão, overflow e sinais | Perfil experimental fixed16 e seus limites |
| Coeficientes SSC | Geração canônica para valores aceitos, não apenas parâmetros do cartão | Domínio ou representação numérica |
| Layout | Texto longo, largura estreita, padding, scroll e escala de 200% | Semântica de constraints e catálogo de layout |
| Transações | Estado/DOM alterado com erro FS, bindings dinâmicos e versões no inspetor | Protocolo de fallback, sem rollback escondido |
| Entrada | Tab, Enter, Espaço, IME, remoção/foco e movimento reduzido | Política de congelamento e restauração |
| Recursos | Arquivo ausente, origem negada, resposta tardia e troca visual inválida | Loader e política do broker |
| Runtime de página | Loop interrompido, memória limitada, imports negados e handle expirado | Destino isolado e ABI |
| Privacidade | Rede somente por ações previstas e inventário de sinais expostos | Catálogo de ambiente e serviços |

Essa matriz pertence ao futuro navegador. Não deve ser executada contra o projeto AssisScript enquanto seu teste de 24 horas estiver em andamento por iniciativa desta tarefa.

## 5. Como registrar resultados futuros

Um resultado inclui: ID do cenário, hashes dos fontes, versões das linguagens/contrato/perfil numérico/API, identificador da implementação, plataforma, comando do driver, diagnóstico/valor/snapshot produzido e status. `not-run` é diferente de `pass`, `fail` e `unsupported`.

`unsupported` é aceitável em um protótipo de subconjunto, desde que o recurso seja anunciado e diagnosticado. Não conta como aprovação de conformidade completa. Baselines visuais identificam fontes, escala, tamanho de janela e política do usuário; não substituir testes de teclado por comparação de imagem.

## 6. Próximos pontos que precisam de evidência

| ID novo | Tema | Próximo passo |
| --- | --- | --- |
| `P01` | Layout de linha e distribuição de largura | Especificar alocação entre filhos antes de liberar `parent.availableWidth` em `row()` |
| `P02` | Perfil numérico de documentos grandes | Medir coordenadas/rolagem e decidir faixa ou representação; a faixa física não limita o tamanho de um artigo |
| `P03` | API de estado tipada/presença | Definir resultado que distinga ausente, zero e erro, preservando a ponte legada |
| `P04` | Temas/extensões de terceiros | Contrato de tokens, autoridade e conflitos antes de aceitar código |
| `P05` | Componentes de autoria | Identidade, escopo de estado, conteúdo e estilo antes de reservar sintaxe |
| `P06` | Coeficientes físicos | Gerador portátil e vetores canônicos antes de prometer trajetória universal |

São questões novas delimitadas; não reabrem as extensões FS já decididas nem tratam as respostas A01–A14 como ausentes. O objetivo do próximo ciclo é reduzir essas lacunas com modelos e exemplos, preservando a distinção entre planejamento e execução.

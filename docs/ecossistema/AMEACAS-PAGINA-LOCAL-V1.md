# Autoridade e falhas do perfil local ASV2

Continuação 02/11/2026: o perfil [windows-isolation-v1](PERFIL-WINDOWS-ISOLATION-V1.md)
acrescenta LPAC com identidade/perfil por processo ao worker e compilador.
Sentinelas privadas, registro, pai, runtime vizinho, clipboard, rede, código
executável e processos filhos são tentados por C independente. O token do OS,
SID/capabilities e recusas AccessCheck são distintos do HELLO não autenticador.
São preservadas VM/concessões/origem/IPC existentes e seus testes. Riscos
abertos incluem recursos de sistema/armazenamento próprio permitidos ao LPAC,
quota de disco, perfis órfãos após crash, kernel/canais laterais, quota agregada
de shell/Reader e preparação síncrona. A seção inicial e matriz abaixo são
históricas da entrega ASV2; não descrevem ausência atual de proteção Windows/Linux.


Data: 02/11/2026. Escopo delimitado da avaliação E00-02; não é modelo completo
de Browser/rede/busca nem aprovação de sandbox. Implementação: pagevm/pagehost,
backend escalar e SDK read-only-1. Tests/test-page-backend.py e test-page-host.py
ligam os casos abaixo à execução nativa Windows/Linux.

| Ativo/fronteira | Entrada hostil | Controle implementado e caso executável |
| --- | --- | --- |
| Arquivos/processos/rede/FFI/relógio do host | Fonte com extern/builtin ou bytes desconhecidos | Perfil rejeita assinatura/recurso mesmo em ramo morto; loader nega opcode/import desconhecido |
| Estado de outra origem/instância | Forjar IDs, trocar origin/document/generation | Grants/post/reply exigem envelope completo; queries ficam na projeção da própria Page |
| Documento local | Query sem concessão ou após revogação | Default deny, grant nativo e revogação permanente; atributos da fonte não atribuem origem |
| Handles e respostas | Replay, call/request antigo, resposta após close/reload | Contexto de VM, geração, request e sequência de chamada; testes de todos os campos e replay |
| Memória/pilha/CPU do executor | Bytes truncados, memória inválida, recursão/loop | Verificador antes de cópia, tetos, fuel cumulativo, quanta e frames; vizinha continua |
| Disponibilidade da fila | Saturação e request repetido | 32 eventos, backpressure preserva request, ordem determinística |
| Ativação | Candidato inválido/OOM/abort/busy | Estado ativo intacto, geração da tentativa nunca reutilizada, commit sem alocação sob recusa do OS |
| Responsividade cooperativa | Página longa ou deadline expirado | Group alterna slots, limita visitas/instruções e revoga antes do próximo quantum |
| Integridade de valores | Overflow, negativo, avaliação curta/ordem de calls | Native/AST/Python independentes; canal last_error separado das células negativas |
| Privacidade de logs | Fonte, paths, conteúdo e estado de origem | Bibliotecas não escrevem logs nem importam IO; exemplo imprime apenas seus dois resultados numéricos |

Hipóteses explícitas: host é confiável, atribui instance/origin sem reuso,
fornece HTDL validado e relógio monotônico, mantém versão da ABI e chama
poll no loop de eventos. As APIs de concessão/resposta do host não existem no
bytecode. IDs de nó são nomes locais de uma projeção, não credenciais globais.
Cada query é limitada/constante e nunca bloqueia em IO. O contador interno
tem delta/teto de chamadas e não despacha código arbitrário.

Riscos remanescentes: bug nativo pode derrubar todas as Pages desse processo;
compilação/parsing/preparação não têm sandbox nem orçamento completo de RSS
ou deadline. Proteções de Windows/Linux/macOS contra acesso a arquivos/rede/
processos não foram implementadas. Fonte compilada localmente não é conteúdo
remoto confiável. Não existe política de URL/DNS/TLS, broker, segredo de perfil,
mutação de DOM, assinaturas gerais ou executor de outras versões da linguagem.
Esses itens permanecem em E03/E05/E06-04/E07 e nos gates, sem dispensa.

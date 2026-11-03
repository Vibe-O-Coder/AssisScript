Continuação de 02/11/2026: [Frame local](PERFIL-FRAME-LOCAL-V1.md) acrescenta
layout/snapshot comum e extensão frame 1 do provider Windows. Publicação de
raster e MSAA é conjunta; Reader::Session/seleção, SSC agregado e catálogo
visual completo continuam separados. Os contratos anteriores são preservados.

Continuação 02/11/2026: [flowpage](../BIBLIOTECA-flowpage.md) oferece
transação das saídas FS de até 256 elementos e cache exato por nó, mantendo
semântica atual após falha. Não acrescenta geometria/SSC/Reader ou gate.
As limitações por nó descritas abaixo são o contrato histórico do núcleo.

# Apresentação local FS/SSC — contrato de desenvolvimento v1

02/11/2026. E08-01/E08-03, fundações M3/M4, sem conformidade visual ou gate.
Fontes normativas de desenvolvimento: snapshot e PROVENANCE congelados,
docs 10/11/12/14/16/17. Não ratifica os rascunhos. Não adiciona presentation
ao HTDL 0.1 nem altera a decisão ASV2 ou o perfil bootstrap do Reader.

Implementação principal em AssisScript: fluxstyle.assis e sanscript.assis.
Parsing recebe bytes; não abre recurso, executa programa, chama FFI, lê
estado do OS ou concede capacidade. Identidades são NodeId de árvore local,
nunca tokens de autorização. Políticas/origem/loader/sandbox permanecem do host.

FS implementa flow/input/let/bind, referências forward, aritmética dimensional,
funções fechadas, enumerações e quinze saídas do rascunho. Comentários aninhados,
BOM/UTF-8 e spans UTF-16 são explícitos. Tipos e ciclos analisam todos os ramos;
choose/&&/|| só avaliam o necessário. Dois produtores no nó são erro F302,
sem prioridade por id, classe ou ordem. Bind repetido do mesmo flow é idempotente.
Há limites de fonte, vértices, declarações e profundidade; nomes de até 128 bytes
e literais com até nove casas são limites operacionais deste perfil.

Q16.16 público mantém -32768..32767.9999847412109375, em int64. Unidade base:
length em px, time em segundos, frequency em Hz. Cores RGBA sRGB sem aritmética.
Literal/coeficiente arredonda ao mais próximo, empate afastando de zero.
Produto usa (a*b+32768)>>16; divisão normaliza o sinal do divisor e arredonda
empates para +infinito, com piso para negativos. Checagens precedem operações
capazes de overflow; intermediários de produto FS de dois Q32 cabem int64.

F101/102: léxico/sintaxe; F201/203: tipos/ramos; F202: propriedade; F204:
fonte/contexto/versão; F205: nome; F206: declaração duplicada/reservada;
F301: ciclo; F302: produtores; F303: largura indefinida/inválida; F304/306:
schema/valores de estado incompatíveis; F401: faixa/alocação/limites; F402:
divisão por zero; F403: clamp invertido; F404: domínio da propriedade.
Identificador de enum resolve primeiro declaração local. Inputs/lets não
redefinem palavras reservadas nem primitivas. Chaves de estado/escopo têm schema
consistente no recurso inteiro, inclusive flows sem interseção; é restrição
conservadora adicional para estado local. Sem correspondência não publica saída;
aviso F305 ainda não é exposto pela API por nó.

Inputs são dados do host. Estado ausente tem padrão e zeros presentes não são
ausência. Number de estado é inteiro. Checked/disabled vêm da semântica atual;
checked exige input checkbox e disabled exige input/button. Largura do pai
exige valor não negativo. Demais valores ambientais/interativos vêm do host;
textScale precisa ser positivo. O host aplica as políticas do usuário antes
do layout; nenhuma entrada lê a geometria final. Não há herança nem cascata.

Style troca máscara/valores/versão em uma operação somente depois de todos os
produtores e domínios desse nó terem passado. Erro conserva o último Style;
NodeIds antigos não são aceitos em outro documento. Ainda não é transação da
página inteira, avaliação incremental entre transações ou reaplicação visual
na árvore semanticamente alterada. A memoização interna não é dirtiness global.

SSC implementa gramática motion/spring/bind com argumentos sem ordem obrigatória,
dois eixos de apresentação, produtores únicos e dependência de produtor FS.
Não há expressões gerais. Perfil numérico **ssc-grid-42-q16-v1**: somente a
grade de sete frequências e seis razões descrita na biblioteca. S402 rejeita
outros parâmetros; S202 rejeita a faixa; S201 argumentos; S203 eixo; S204 tipo;
S205 nome; S301 conflito; S302 produtor ausente; S403 fonte/alocação/quota/
identidade; S401 domínio/fallback de execução. Sem aviso S303 nesta API.

Tabela é gerada fora do runtime com Decimal a 90 e 110 dígitos, fórmulas do
rascunho e comparação independente binary64 do snapshot. Todas as 42 matrizes
coincidem; (4Hz,0.8) é [64251,461,-290983,45727]. Novos pares exigem revisão
do perfil e vetores. Não se aceitam coeficientes fornecidos pelo conteúdo.
Não se promete igualdade aproximada de floats em todos os parâmetros.

Passo 1/120s, teto oito por avanço, resto fracionário sem backlog inteiro;
aba oculta pausa e descarta o intervalo de retorno; nó oculto reaparece no
destino. Proteção de foco/edição congela deslocamento e zera velocidade;
destinos posteriores são guardados. Reduced motion aplica destino. Quais
ancestrais estão protegidos é dado do host, ainda sem integração Reader/IME.
Retarget conserva posição e velocidade; primeira apresentação inicia no destino.
Repouso usa três passos com |x|<1024 e |v|<32768 em Q16.16. Posição deve caber
no público Q32; velocidade e produtos têm guardas int64. Fallback direto de
destino válido fora do perfil físico ou de falha de passo sempre informa S401.

Conservam-se limites e fila integrais: identidade incremental/editor, catálogo
no Reader, desktop/leitor/DPI/IME, loader/código/recursos e HTDL 0.2, SDK geral,
layout/snapshots, inspector/LSP FS/SSC, quotas de página/RSS/disco/órfãos,
macOS/ARM, rede/perfis/persistência/busca, M4–M9, 24h e distribuição/aceites.
Os novos avaliadores locais não encerram essas integrações. Easy por último.

A coordenação agregada agora está em [motionpage](BIBLIOTECA-motionpage.md): cota de 256 canais, candidatos independentes, foco de ancestrais e composição no Frame. Os limites por nó descritos abaixo continuam válidos.

# sanscript — SSC experimental finito, v1

`import "std/sanscript.assis";` depende de fluxstyle. Instalação mínima:
`--with sanscript`, com fechamento de dependências. Implementação em AssisScript,
sem provider, float ou novo executor. Nome por extenso SanSCript e extensão
`.sscr`, conforme rascunho. [Contrato](ecossistema/PERFIL-APRESENTACAO-LOCAL-V1.md),
[demonstração](../exemplos/54_fluxstyle_sanscript.assis).

`try_new Program(source,max_bytes)` analisa motion/spring/bind e posições.
Consulte `is_open()` e `diagnostic()`; códigos são sufixos de Sxxx. Limites:
64 KiB de fonte, 32 motions, 64 canais declarados, 128 binds, nomes/seletores
de 128 bytes e comentários aninhados até 32. Workspace requer orçamento
conservador de `20000 + source_size` bytes solicitados; não mede RSS.

O perfil `ssc-grid-42-q16-v1` aceita somente frequências 0.5/1/2/4/6/8/10 Hz
e dampingRatio 0.1/0.3/0.8/1/2/4, após conversão Q16.16. As 42 matrizes são
canônicas e versionadas; `coefficients(frequency_q,damping_q)` devolve Matrix.
Par fora dessa tabela, mesmo dentro do intervalo do rascunho, recebe S402.
Não há gerador de coeficientes em runtime nem promessa para valores intermediários.

`Program.attach(document,node,style)` resolve seletores e produtores e devolve
`own Motion`; consulte proprietário, `is_open()` e `status()`. Vínculo idempotente
do mesmo motion não duplica produtor; conflitos entre motions são S301. FS deve
produzir explicitamente o destino de cada eixo, senão S302. Sem correspondência
produz Motion válido sem canais; não há aviso S303 nesta API mínima.

Motion tem até dois canais. `update(document,style)` copia destinos de versão
nova da mesma identidade e conserva posição/velocidade no retargeting.
`advance(document,elapsed_ms,tab_visible,node_visible,protected,reduced)`
consome elapsed entre 0 e 60000 ms, em passos 1/120 s e teto oito por chamada.
Excesso inteiro é descartado e só a fração permanece. Tab pausa sem catch-up;
nó oculto retorna no destino; proteção congela a posição e zera velocidade;
movimento reduzido aplica destino. O host calcula proteção de ancestrais e
fornece políticas/tempo; não há relógio acessível à página.

`at(axis)` e `speed(axis)` devolvem Number, eixo 1=X/2=Y; `asleep()` consulta
repouso, `version()` consulta origem, `close()` libera e invalida. Navegação ou
remoção detectada pelo Document fecha o Motion antes de novo avanço. Qualquer
uso após close retorna S403. Consultas de eixo ausente retornam S302.

Posição usa Q16.16 público; velocidade/intermediários são int64 verificados.
Repouso exige |x|<1/64 px e |v|<0.5 px/s por três passos. Destino representável
fora de ±4096px aplica direto com S401; destino inválido conserva estado. Erro
no passo aplica destino seguro e informa S401. Não se afirma tolerância global
em ±4096px. Os ensaios analíticos de 8px têm escopo próprio no relatório.

Quota agregada de 256 canais por página, composição, geometria compartilhada
com desenho/hit test/acessibilidade, foco nativo/IME, loader, LSP e ciclo de
vida de todos os nós ainda exigem integração do host. Este perfil por nó não
declara `motion-0.1-experimental` completo nem um gate visual aprovado.

Continuação 04/11/2026: `Motion.moving()` distingue dinâmica ativa de repouso,
pausa, hidden e proteção. É consulta para o agendador do shell; não muda
coeficientes, frequência, rounding ou o limite de oito passos por amostra.

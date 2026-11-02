# fluxstyle — perfil local FS, v1

`import "std/fluxstyle.assis";` depende de htdl e suas dependências. Biblioteca
opcional, implementada em AssisScript. Instalação mínima: `--with fluxstyle`.
[Contrato](ecossistema/PERFIL-APRESENTACAO-LOCAL-V1.md) e
[exemplo 54](../exemplos/54_fluxstyle_sanscript.assis).

`try_new Program(source,max_bytes)` copia até 64 KiB de FS UTF-8 e analisa
flow/input/let/bind, expressões puras, tipos, dependências e propriedades.
Consulte proprietário não nulo, `is_open()` e `diagnostic()`; o código é o
sufixo de Fxxx, com spans em bytes e posições UTF-16. Construção fallível,
reserva conservadora de corpos solicitados de `400000 + source_size` bytes;
esse argumento é um mínimo necessário para o workspace limitado, não quota
de RSS nem orçamento agregado de página. 32 flows, 256 declarações, 2048
vértices, 128 binds, 480 saídas e profundidade 64. Nomes têm até 128 bytes.

`flow_index(name)` encontra flow por nome; `input_index(flow,name)` encontra
um input da revisão compilada. São índices locais, sem autoridade de página.
`try_new Inputs(capacity)` aceita capacidade 1..2048; `set(index,type,value)`
valida valores tipados e `clear()` remove os fornecidos. Use `is_ready()`.
Estado ausente usa seu padrão; chaves/escopos iguais têm um valor coerente
entre flows. Valores fornecidos contraditórios são F304. Estados number são
inteiros Q16.16. Fontes externas requerem valor explícito do host; disabled e
checked são derivados da árvore semântica atual, com aplicabilidade validada.

`try_new Style()` conserva a última transação válida de um nó. `is_ready()`,
`version()`, `node()`, `has(property)` e `value(property)` consultam a saída.
`Program.evaluate(document,node,inputs,version,style)` resolve vínculos desse
nó, exige produtor único e copia todos os resultados somente em sucesso.
Versões repetidas/antigas ou identidade diferente são recusadas. Falha de
avaliação preserva versão, máscara e valores. `Style.commit` é uma operação
de host confiável, usada também pelos testes; não é uma API de página.

Tipos: bool=1, number=2, length=3, time=4, frequency=5, color=6, align=7,
overflow=8, children=9, colorScheme=10, contrast=11. Propriedades 1..15:
layout.width/height/padding/children/align/overflow, paint.background/text/
radius/opacity, text.size/weight/align, target.offsetX/offsetY. `children`
codifica `gap_q*4 + mode`, block=0, row=1, column=2. É representação local.

`Number(code,value)` e add/subtract/multiply/divide/decimal implementam o
perfil numérico. Escala 65536; faixa pública codificada -2147483648..2147483647;
time usa segundos e frequency Hz, portanto `4Hz * 500ms == 2`. Produto e
divisão arredondam empates para +infinito; conversão de literal afasta de zero.
decimal admite até nove casas, sinal externo, multiplicador 1/1000 e divisor
1/100/1000; devolve ainda magnitude positiva 2147483648 para o parser poder
aplicar o sinal do limite negativo. O avaliador recusa essa magnitude positiva.

Há memoização dentro da avaliação por nó. [flowpage](BIBLIOTECA-flowpage.md)
coordena saídas da página inteira e cache exato de contexto por nó entre
transações; não é invalidação por vértice. `Inputs.capacity()` informa o
tamanho do contexto. `Program.shared_state(index,inputs)` permite comparar
células page efetivas: Number(1,0) indica índice não compartilhado; código 0
é valor resolvido, 201/304 indicam tipo/conflito. São operações do host.
Layout/desenho, loader HTDL 0.2, Reader, inspector e FS no LSP seguem abertos.
O host aplica políticas/semântica atual antes de publicar geometria.

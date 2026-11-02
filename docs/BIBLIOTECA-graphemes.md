# std/graphemes — Unicode 17.0.0

Biblioteca opcional em AssisScript, dependente de `unicode`. `viewer` a importa.
Implementa grafemas estendidos padrão da UAX #29 revisão 47 (GB3–GB999),
incluindo contexto índico, Hangul, pares de indicadores regionais e emoji ZWJ.
Não faz normalização, case folding, palavras, shaping, bidi, edição ou IME.

`Cursor` conserva estado constante e não aloca em `push(codepoint)`: retorna
1 quando há fronteira antes do escalar, 0 se não há, -1 para não escalar.
Erro preserva o estado; `reset()` inicia novo texto. `unicode_version()` = 170000.

`try_new Index(data)` valida UTF-8 e limita a entrada a 1 MiB antes de alocar.
O índice copia apenas fronteiras: len+1 bytes e um Cursor temporário, além dos
controladores do runtime. Não retém bytes do chamador. `status()` retorna 0,
-1 (UTF-8/limite) ou -4 (OOM). Construtor também pode retornar null.
`size()` é comprimento original em bytes; `count()` é quantidade de grafemas.
`boundary(offset)` custa O(1); `next/previous(offset)` varrem somente os bytes
até a fronteira vizinha e exigem offset em fronteira, devolvendo -1 em erro.
Vazio tem fronteira 0; extremos next(size)/previous(0) são idempotentes.
`codepoint(data,offset)` é auxiliar com precondição de UTF-8 válido/fronteira escalar.

Construção: O(n log R), R=833 intervalos imutáveis mais Hangul algorítmico;
estado do Cursor é constante mesmo com milhões de marcas ou indicadores.
As tabelas são reproduzidas por `tools/generate-grapheme-data.py --check`
usando UCD fixada em tests/fixtures/unicode-17.0.0/PROVENANCE.json. Corpus
oficial de 766 casos; os marcadores de fronteira são o oráculo independente.
Licença em [UNICODE-LICENSE.txt](licenses/UNICODE-LICENSE.txt).

Reader passa a recusar seleção dentro de grafema, inclusive antigos offsets
escalares que eram aceitos. Viewer mede/quebra por grafemas; se um único
grafema excede viewport ou limite de medição de 4096 bytes, o candidato é
recusado e a sessão conserva o documento anterior. Isso é uma mudança de
comportamento deliberada; a assinatura pública continua igual. Índices e
workspace de View/Reader ainda não são quota de RSS ou de documento completo.

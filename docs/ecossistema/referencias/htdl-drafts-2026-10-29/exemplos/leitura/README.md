# Leitura adaptável

Exemplo **conceitual** HTDL 0.2 + FluxStyle 0.1. Não existe navegador/parser capaz de executá-lo neste projeto. Não usa AssisScript nem SSC: texto, links e layout não dependem de movimento ou programa de página.

[index.htdl](index.htdl) carrega [reading.fxs](reading.fxs). A página usa padrões semânticos mesmo que esse recurso falhe. Os flows `ReadingMeasure` e `ReadingSpacing` escrevem propriedades disjuntas do mesmo `main`; a aparência textual é vinculada explicitamente, sem herança genérica de contêiner.

Resultados esperados no futuro motor:

| Entrada | Resultado autoral |
| --- | --- |
| Viewport de 360 px | Body oferece 312 px após padding; `main` usa 312 px |
| Viewport de 1024 px | Body oferece 976 px; `main` usa 720 px |
| `env.colorScheme = dark`, contraste normal | Fundo `#171922`, texto `#f4f1ff` |
| `env.contrast = high` | Fundo preto e texto branco, independentemente do esquema |
| Escala de texto 200% | Tamanho base de 18 px passa uma vez a 36 px antes de medir |

As larguras incluem padding segundo a proposta do documento [17](../../docs/17-execucao-transacoes-e-layout.md). O exemplo não promete centralização automática, fidelidade tipográfica ou uma medida de performance. O fragmento `#details` aponta para uma seção da mesma página.

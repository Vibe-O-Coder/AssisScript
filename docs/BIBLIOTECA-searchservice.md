# searchservice — busca HTTP em loopback

O [exemplo 73](../exemplos/73_search_service.assis) atende consultas ao
snapshot ASIX 1 ou ASIS 1 no diretório de trabalho confiável. Prepare o snapshot com
o [exemplo 71](../exemplos/71_search_index.assis). Use um diretório e uma
chave aleatória de 256 bits por corpus. O serviço recebe a chave de 64
dígitos hexadecimais minúsculos na primeira linha de stdin. A única saída
normal é `READY PORT`. A chave e o texto da consulta ficam fora dos logs.

Inicie `search-service PORT [RUN_MS [--segments]]`. A porta zero escolhe uma porta
livre. Um prazo positivo encerra a escuta e fecha as conexões ao expirar.
Com `--segments`, o serviço usa `webassis.asis`. O modo padrão abre `webassis.asix`.
Para cada consulta explícita, o cliente local envia os campos abaixo.

| Campo | Valor |
| --- | --- |
| Requisição | `POST /v1/search HTTP/1.1` |
| Host | `127.0.0.1:PORT` |
| X-Assis-Search-Key | Chave do corpus |
| Content-Type | `text/plain; charset=utf-8` |
| Content-Length | Comprimento decimal exato do corpo em bytes |
| Corpo | Modo, TAB, offset decimal entre 0 e 255, TAB, consulta UTF-8 |

O modo é `and`, `or` ou `phrase`. A resposta 200 tem até dez linhas de
`ID PONTUAÇÃO OFFSET_EM_BYTES`, da primeira posição pedida até o limite
de 256 resultados. A consulta usa o ranking do índice e o mesmo tratamento
de UTF-8. Se o arquivo estiver ausente, ilegível ou inválido, a resposta
é 503. As respostas têm comprimento explícito, `Cache-Control: no-store`
e fechamento após uma requisição.

São oito conexões e até 4.096 bytes de cabeçalhos, 2.064 de corpo e 2.048
de consulta. A montagem do pedido e o envio da resposta têm dois segundos
cada. O loop lê e escreve por etapas, com estado e prazo por conexão. Uma
requisição com enquadramento ambíguo, `Origin`, transferência codificada,
compressão ou tentativa de trocar a autoridade recebe recusa. O protocolo
admite o alvo acima, campos únicos de autoridade, framing e autenticação,
e uma requisição por socket. [HTTP/1.1, RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html).

Cada consulta aceita abre e verifica um snapshot novo. O modo ASIX fecha
o arquivo antes de consultar. O modo ASIS consulta um segmento por vez
e fecha o arquivo antes de enviar os resultados. Uma troca concluída pode ser vista pela próxima
requisição sem reiniciar o processo. O escritor mantém seu lock e pode
receber recusa de troca no Windows se a leitura do arquivo coincidir com
a publicação. O trabalho do índice corre em série no loop. Limites de latência
sob carga, integração
no Browser, administração remota e TLS são etapas seguintes.

`std/searchservice.assis` oferece `Service(port, key, segmented)`, `port()` e
`poll(wait_ms)`. O host escolhe a cadência, até 50 ms de espera por chamada.
`poll` devolve 0 enquanto a escuta está ativa e -1 em erro. O perfil atual
executa em Windows e Linux x64 com a [biblioteca loopback](BIBLIOTECA-loopback.md).

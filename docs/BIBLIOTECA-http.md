# http — cliente HTTP(S) limitado

Esta API é bloqueante. A biblioteca [net](BIBLIOTECA-net.md) oferece GET com
polling e cancelamento cooperativo.

Importação: `import "std/http.assis";`. API:
`safe fn get(borrow url:*byte, timeout_ms:int, max_bytes:int):own Response`.
URL ASCII terminada em exatamente um NUL, com esquema http/https, sem
credenciais. A URL tem até 8192 bytes incluindo o NUL. O corpo tem até
16 MiB e o timeout pode variar entre 1 e 60000 ms.
Consulte o [perfil de endereços](BIBLIOTECA-httpurl.md).
`Response.body()` retorna slice emprestado; `size`, `status_code`, `error` e
`native_error` separam conteúdo, status HTTP e falhas de transporte.

Para muitas requisições no mesmo processo, crie `own client:http::Client =
new http::Client()` e use `client.get(url, timeout, limite)`. O empréstimo
exclusivo do receptor impede sobreposição de operações na sessão. O cliente
mantém a sessão nativa viva e a fecha ao sair de escopo. `http::get` é a
conveniência para uma requisição isolada e cria uma sessão por chamada.

## POST, cabeçalhos e redirecionamento explícito

Use `Headers.add(name, value)` com fatias ASCII. O retorno `false` conserva
os cabeçalhos já aceitos. Nomes seguem a gramática HTTP de tokens, sem
duplicatas por caixa. Cada nome tem até 64 bytes e o valor tem de 1 a 4096
bytes sem espaço nas pontas nem caracteres de controle. O bloco tem até
8192 bytes. Framing, autoridade, conexão, cookies e credenciais são
reservados ao transporte.

`client.post(url, payload, fields, timeout, max_bytes)` e
`http::post(url, payload, fields, timeout, max_bytes)` enviam uma fatia
binária com comprimento explícito, inclusive zero e bytes NUL.
`client.get_with_headers(url, fields, timeout, max_bytes)` aceita os mesmos
cabeçalhos. Nessas duas operações `Response.raw_headers()` empresta o bloco
final de até 32 KiB. `Response.header(name)` procura uma ocorrência única,
sem distinguir caixa. Valores ausentes, vazios, duplicados ou um bloco com
dobramento de linha produzem uma fatia vazia. O GET original captura o corpo.

```assis
import "std/http.assis";
import "std/httpurl.assis";

safe fn main():int {
    own url:*byte=httpurl::resolve(utf8("http://127.0.0.1:8080/upload"),utf8(""));
    own headers:http::Headers=new http::Headers();
    if(url==null || !headers.add(utf8("Content-Type"),utf8("application/octet-stream"))){return 1;}
    own reply:http::Response=http::post(url,utf8("payload"),headers,5000,65536);
    print(reply.error(),reply.status_code(),reply.size());
    return int(reply.error()!=0);
}
```

`client.get_following(url, fields, redirects, timeout, max_bytes)` segue até
oito saltos GET quando solicitado. Resolve `Location` pelo perfil de URL e
compara esquema, host e porta antes de cada salto. Um destino recusado, um
`Location` ambíguo ou o limite de saltos devolve a resposta 3xx existente.
O orçamento de tempo é recalculado entre requisições. O POST devolve o
status 3xx ao chamador. Use essa API em aplicações confiáveis com destinos
concedidos pelo host.

WinHTTP mantém recursos internos depois de fechar sessões; recriar centenas de
sessões produz retenção observável também em um programa C independente. Use
Client em serviços. A regressão aquece uma sessão, faz 128 requisições nessa
mesma sessão e compara handles/descritores antes e depois, além de verificar
a limpeza do heap em debug. No Linux o handle curl é reutilizado com reset dos
callbacks e userdata antes de liberar cada buffer de resposta.

| error | Significado |
| --- | --- |
| 0 | Transporte concluído; verificar também status HTTP |
| -1 | URL/limites inválidos |
| -2 | Corpo excede limite; conteúdo pode estar parcial |
| -3 | Timeout |
| -4 | Falha de transporte/DNS/desconexão |
| -5 | Falha de TLS/certificado |
| -6 | Falha de inicialização/configuração |
| -8 | Bloco de cabeçalhos acima do limite ou leitura de metadados recusada |

Windows usa WinHTTP do sistema. Linux requer glibc x86_64 e `libcurl.so.4` com
HTTP/HTTPS/TLS. Bibliotecas são opcionais e não são baixadas nem redistribuídas
pelo AssisScript. Ausência de biblioteca/símbolo é falha do loader antes de main.
Não importar http em uma aplicação que deva permanecer freestanding.

O transporte exige verificação padrão de certificado e hostname. Proxies
implícitos, redirects nativos e autenticação do usuário ficam desabilitados.
Corpos são bytes e podem incluir NUL. Descompressão, armazenamento de cookies,
IDNA e cancelamento de POST continuam fora deste perfil. Um HTTP 404 aparece
em `status_code()` com `error()==0` quando o transporte termina normalmente.

No Linux, libcurl aplica timeout total e de conexão. No Windows, WinHTTP tem
timeouts por fase; o tempo total também é classificado ao concluir. A
granularidade/bloqueio de chamadas do OS pode ultrapassar o número solicitado:
não é um prazo de tempo real. A API é bloqueante. Cancelamento durante a
operação, integração de polling no event loop e transporte assíncrono continuam
pendentes. DNS é usado pelo cliente; não há resolvedor público independente.

Aplicação B: `exemplos/27_http_client.assis`, uso `http-client URL saída`.
O arquivo só é aberto após transporte e status 2xx; falhas HTTP preservam uma
saída preexistente. Erro durante escrita pode deixar saída parcial.

Testes locais verificam DNS localhost, HTTP/binário, limites, 404, redirects
para esquema proibido, timeout, desconexão, recuperação e certificados
autoassinados rejeitados. O certificado de teste não é instalado no sistema.
Não se declara homologação completa de provedores TLS nem sucesso de cadeia
de certificados local confiável em Windows.

Referências de configuração

[POST binário em libcurl](https://curl.se/libcurl/c/CURLOPT_POSTFIELDSIZE_LARGE.html),
[WinHttpSendRequest](https://learn.microsoft.com/windows/win32/api/winhttp/nf-winhttp-winhttpsendrequest),
[callback de escrita](https://curl.se/libcurl/c/CURLOPT_WRITEFUNCTION.html),
[timeout](https://curl.se/libcurl/c/CURLOPT_TIMEOUT_MS.html),
[verificação de hostname](https://curl.se/libcurl/c/CURLOPT_SSL_VERIFYHOST.html).

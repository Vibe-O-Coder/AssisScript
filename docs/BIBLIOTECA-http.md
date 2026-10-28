# http — cliente HTTP(S) limitado

**Alpha.12:** esta API continua bloqueante; use [net](BIBLIOTECA-net.md) para polling e cancelamento cooperativos.

Importação: `import "std/http.assis";`. API:
`safe fn get(borrow url:*byte, timeout_ms:int, max_bytes:int):own Response`.
URL ASCII terminada em exatamente um NUL, com esquema http/https, sem
credenciais. Limites: URL 8192 bytes, corpo 0–16 MiB, timeout 1–60000 ms.
`Response.body()` retorna slice emprestado; `size`, `status_code`, `error` e
`native_error` separam conteúdo, status HTTP e falhas de transporte.

Para muitas requisições no mesmo processo, crie `own client:http::Client =
new http::Client()` e use `client.get(url, timeout, limite)`. O empréstimo
exclusivo do receptor impede sobreposição de operações na sessão. O cliente
mantém a sessão nativa viva e a fecha ao sair de escopo. `http::get` é a
conveniência para uma requisição isolada e cria uma sessão por chamada.

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

Windows usa WinHTTP do sistema. Linux requer glibc x86_64 e `libcurl.so.4` com
HTTP/HTTPS/TLS. Bibliotecas são opcionais e não são baixadas nem redistribuídas
pelo AssisScript. Ausência de biblioteca/símbolo é falha do loader antes de main.
Não importar http em uma aplicação que deva permanecer freestanding.

Verificação padrão de certificado e hostname permanece habilitada. Não há API
para desativá-la. Redirects, proxies implícitos e autenticação por credenciais
do usuário são desabilitados; não se fornece armazenamento de cookies.
O corpo mantém bytes NUL e UTF-8 sem interpretá-los. Não há transparência de
descompressão, uploads, cabeçalhos personalizados, IDN ou IPv6 no adaptador
Windows desta versão. HTTP 404 é uma resposta HTTP, não erro de transporte.

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

Referências de configuração: [callback de escrita](https://curl.se/libcurl/c/CURLOPT_WRITEFUNCTION.html),
[timeout](https://curl.se/libcurl/c/CURLOPT_TIMEOUT_MS.html),
[verificação de hostname](https://curl.se/libcurl/c/CURLOPT_SSL_VERIFYHOST.html).

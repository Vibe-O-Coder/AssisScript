# net — HTTP(S) cooperativo e cancelável

Importação: `import "std/net.assis";`. Complementa o cliente bloqueante `http`.
`net::start(borrow url:*byte, timeout_ms:int, max_bytes:int):own Request`
inicia um GET. `start_trusted` recebe também `borrow ca_file:*byte` para uma
fonte de confiança explícita, restrita àquela requisição. Não altera o OS.

URL ASCII com NUL final único, até 8192 bytes; somente http/https, sem
credenciais. Timeout total/conexão de 1–60000 ms; corpo de 0–16 MiB.
URL e caminho de CA são copiados. O chamador pode liberá-los após start.

| Operação em Request | Contrato |
| --- | --- |
| `poll(wait_ms)` | 0 pendente, 1 concluída inclusive erro; -1 para espera fora de 0–50 ms, sem mudar o estado |
| `cancel()` | Remove imediatamente a transferência da fila; true somente na primeira vez antes da conclusão |
| `done()` | Indica conclusão, erro inicial ou cancelamento |
| `error()` | 1 pendente; 0 sucesso; -1 entrada, -2 limite, -3 timeout, -4 transporte/DNS, -5 TLS, -6 configuração/dependência incompatível, -7 cancelamento |
| `native_error()` | Código CURLcode na conclusão, CURLMcode na falha de polling |
| `status_code()` | Status HTTP na conclusão; 0 quando indisponível; 404 não é falha de transporte |
| `size()`, `body()` | Bytes recebidos e slice emprestado; podem conter NUL ou conteúdo parcial |

`poll(0)` não espera atividade de rede. Intercale com `events::run(loop, 1)`
para processar timers/cancelamento da aplicação; polling não é agendado
automaticamente. Para várias requisições, intercale polling de cada uma.
Não há callbacks AssisScript em threads externas nem acesso concorrente ao
heap. O empréstimo exclusivo impede poll/cancel durante uma visão de body:
encerre o escopo da visão antes de continuar a operação.

O destrutor remove a transferência antes de fechar easy/multi e liberar os
buffers. É seguro destruir uma requisição pendente. Cancelamento conserva os
bytes já recebidos; poll posterior retorna concluído e não executa callbacks.
Uma instância representa uma requisição; use `http::Client` quando desejar
reuso de sessão/cache de conexões no caminho bloqueante existente.

Dependência opcional: libcurl >= 7.66, com TLS e DNS assíncrono (`ASYNCHDNS`).
Linux: `libcurl.so.4` e loader glibc; Windows: `libcurl-4.dll` x64 e as
dependências do provedor, instaladas pelo usuário no ambiente de execução.
O loader resolve a biblioteca antes de main. Um provedor sem ASYNCHDNS é
recusado com -6. Git for Windows fornece um provedor usado nos testes locais;
Git não é requisito para o módulo e nenhum DLL é redistribuído pelo projeto.
Programas que não importam net não adquirem essa dependência.

Verificação de cadeia e hostname é sempre habilitada. Não há API para
desativá-la. Proxies herdados, redirects, credenciais implícitas e cookies
estão desabilitados. CA personalizada substitui a fonte padrão somente na
requisição. Os testes positivos usam um certificado local explicitamente
confiado; também recusam certificado não confiado e hostname divergente.

Polling pode executar trabalho de TLS e cópia de buffers. O tempo do OS e de
CPU não constitui garantia de tempo real. Sem upload, servidor HTTP, WebSocket,
decompressão transparente, cabeçalhos arbitrários ou resolvedor DNS público.
As plataformas seguem a sintaxe de URL aceita pelo provedor libcurl.

Exemplo completo: [cliente cancelável](../exemplos/29_http_polling.assis).
Referências de implementação: [multi](https://curl.se/libcurl/c/libcurl-multi.html),
[poll](https://curl.se/libcurl/c/curl_multi_poll.html),
[mensagens](https://curl.se/libcurl/c/curl_multi_info_read.html),
[CAINFO](https://curl.se/libcurl/c/CURLOPT_CAINFO.html).

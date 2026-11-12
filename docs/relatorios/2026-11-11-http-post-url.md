# HTTP POST, cabeçalhos e resolução de endereços

11/11/2026, America/Fortaleza. Base publicada `5922558`, branch
`work/m3-confined-loader-2026-11-11`. O objetivo é oferecer pela stdlib as
operações que o usuário reproduziu diretamente com libcurl.

`http::Client.post` e `http::post` enviam bytes e comprimento explícito.
`Headers.add` valida nomes e valores antes de aceitar o bloco. O transporte
continua a controlar autoridade, framing, cookies, credenciais e proxy.
`get_with_headers` e POST expõem o bloco final limitado e consulta de campo
por nome. O GET existente usa a sessão reutilizável e mantém sua assinatura.
WinHTTP e libcurl mantêm verificação de cadeia e hostname.

`httpurl` implementa parsing e resolução em AssisScript. Aceita referências
relativas, query, fragmento, IPv6 literal e percentuais bem formados. A
comparação é textual por esquema, host e porta. O GET pode seguir até oito
saltos da mesma origem por opção explícita. Um salto ambíguo ou recusado
devolve a resposta 3xx original. O POST devolve o 3xx ao chamador.
[API e exemplo](../BIBLIOTECA-http.md).

O servidor independente confirma o método, o valor de `X-Test`, os bytes
NUL e FF, POST vazio e GET subsequente sem herdar cabeçalhos. O corpus verifica
limites, falta de certificado confiável, status, falha de rede, oito testes de
`http` em cada host e as regressões de cancelamento/TLS de `net`. Os exemplos
de resolução partem do RFC 3986. O servidor registra se algum salto bloqueado
foi alcançado. Em ambos os hosts, o GET público de `https://example.com/`
baixou 577 bytes com a verificação TLS padrão.
[Matriz e hashes](../ecossistema/evidencias/loader-http-2026-11-11/).

**48,80% → 50,40%, 0/5 gates.** E05-01 sobe de 1 a 2 pelo transporte útil
GET/POST e cabeçalhos. E05-02 sobe de 0 a 1 pelo perfil inicial de navegação
com limite e checagem da origem em cada salto. E05-03 sobe de 0 a 2 pelo parser,
serialização, resolução e corpus de endereços. Ficam abertos DNS hostil,
partição, IDNA, autenticação concedida, cookies/cache, streaming e POST
cancelável. G2 continua pendente. A publicação segue na branch de trabalho.

[Exemplos normativos do RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html#section-5.4)

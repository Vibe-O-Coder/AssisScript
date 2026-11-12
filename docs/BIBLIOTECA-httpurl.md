# Endereços HTTP(S) e referências

`import "std/httpurl.assis";` seleciona um parser sem I/O. `parse(slice<byte>)`
recebe até 8191 bytes ASCII sem NUL final e retorna offsets no texto de
entrada, porta efetiva, esquema e estado. O host aceita nomes DNS ASCII,
IPv4 decimal em quatro octetos e IPv6 entre colchetes. Porta explícita
entre 1 e 65535. O perfil recusa credenciais na autoridade, zone IDs,
escapes incompletos, espaços e barras invertidas.

`resolve(base, reference)` recebe uma base absoluta e resolve referências
absolutas, com autoridade, relativas à raiz ou ao diretório, query isolada,
fragmento ou referência vazia. Remove segmentos literais `.` e `..` e
preserva barras consecutivas e escapes percentuais. Retorna um buffer de
tamanho exato com NUL final, pronto para `http`. Comprimento zero indica
entrada recusada. `null` indica recusa de alocação.

`same_origin(a,b)` compara esquema, porta efetiva e grafia do host
ignorando caixa ASCII. Grafias IPv6 diferentes podem comparar desiguais.
O resultado descreve a origem textual e independe de DNS. O perfil
deixa IDNA, endereços resolvidos, classificação de rede e autorização de
conteúdo remoto para o broker.

[RFC 3986 e exemplos de resolução](https://www.rfc-editor.org/rfc/rfc3986.html#section-5.4)

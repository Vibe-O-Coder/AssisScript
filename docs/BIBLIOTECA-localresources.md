# Recursos declarados em raiz local

`import "std/localresources.assis";` seleciona o loader do shell confiável.
No Windows e Linux x64, o executável precisa do provider worker reconstruído
com a extensão `assw_local_*` v1. Prepare o provider com
`python tools/build-page-worker.py --output build/worker --compiler <assis>`.
No Windows, mantenha a DLL na pasta do executável ou no PATH do processo.
No Linux, disponibilize a biblioteca no caminho do loader do processo.

O shell fornece um diretório absoluto UTF-8 concedido pelo usuário e abre um
`Load(root, instance, origin, generation, max_bytes, deadline)`. O manifesto
`resources.assr` fica diretamente nessa raiz e tem até 64 KiB. A primeira linha
é `ASSIS-LOCAL/1`. Cada declaração contém papel, versão e chave separados por
um espaço. Linhas vazias, LF e CRLF são aceitos. A última declaração pode
terminar no EOF.

```text
ASSIS-LOCAL/1
htdl 2 index.htdl
fs 1 styles/main.fxs
ssc 1 styles/main.sscr
source 1 main.assis
data 1 images/asset.bin
```

Inclua um `htdl` (1 ou 2), um `fs` (1), um `ssc` (1) e um `source` ou
`asv2` (1). `data 1` é opcional, fica no shell e pode aparecer mais de uma vez
com chaves diferentes. A lista tem até 64 entradas. As chaves seguem a
gramática ASCII canônica de [pageresources](BIBLIOTECA-pageresources.md),
com segmentos de até 255 bytes. A caixa precisa coincidir com o nome no disco.
Selecione uma raiz com nome Unicode quando necessário. Conteúdos são bytes
e podem incluir NUL. A sintaxe e a versão de cada recurso ativo são validadas
pelos respectivos consumidores durante a preparação da página.

`advance()` lê um arquivo por chamada. Retorna 0 enquanto há trabalho e 1
quando `take()` pode transferir o lote completo uma única vez. Um erro terminal
fecha a concessão e descarta os bytes parciais. `cancel()` e a destruição
liberam a concessão. Use `line()` para a linha de uma declaração rejeitada,
`index()` para o índice de entrega (base zero) e `status()` para o erro.
A ativação usa `frameworker::Session.prepare_bundle`, seguida pelo fluxo
existente de preparação e commit ou publish. [Exemplo completo](../exemplos/69_confined_resource_frame.assis).

O loader retorna -1 para entrada/chave inválida, -3 para cota/teto, -4 para alocação, -6 para arquivo
ausente/recusado/alterado ou erro de I/O, -8 prazo expirado, -9 cancelado ou
lote já retirado, -10 provider indisponível e -11 thread incorreta. -16 indica
versão, papel ou conjunto de declarações incompatível. O prazo absoluto usa
`monotonic_ms()` e é revalidado antes e depois da leitura. Uma leitura física
síncrona em andamento pode ultrapassar esse prazo. Execute cada passo fora
da thread gráfica quando o dispositivo não tiver latência previsível.

A raiz autoriza os arquivos elegíveis abaixo dela no momento de cada abertura.
O manifesto seleciona o subconjunto a ler. Escolha uma raiz dedicada ao
documento. No Linux, a extensão requer `openat2` e `/proc/self/fd`, recusa
travessia de mounts descendentes e fixa o inode antes de reabri-lo. No Windows,
o provider usa caminhos de volume fixo, abre cada componente relativamente ao
handle anterior, retém os diretórios sem compartilhamento para remoção durante
a leitura e valida os atributos e o nome canônico do handle. Links simbólicos,
junctions, reparse points, links físicos múltiplos e arquivos especiais são
recusados. A biblioteca mantém o lote entregue independente de edições futuras.
O contrato faz a captura arquivo por arquivo. Uma edição concorrente entre
duas leituras pode alterar a combinação de versões capturadas.

Referências do provider

- [Linux pathname lookup](https://kernel.org/doc/html/v6.12/filesystems/path-lookup.html)
- [Microsoft NtCreateFile](https://learn.microsoft.com/windows/win32/api/winternl/nf-winternl-ntcreatefile)
- [Metadados do arquivo aberto no Windows](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information)

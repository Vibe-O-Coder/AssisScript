# IO gerenciado e aplicação A — 3.3.0-alpha.7

O executável nativo passa a abrir, ler, escrever e fechar arquivos, além de receber argumentos. Não invoca helpers, shell, Python ou compilador C. Windows usa CreateFileW/ReadFile/WriteFile/CloseHandle; Linux usa syscalls openat/read/write/close. As APIs são síncronas, sem threads, rede, cancelamento ou event loop.

| API | Contrato |
| --- | --- |
| `arquivo_abrir(caminho: text, modo: int): own Arquivo` | 0: leitura; 1: criar/truncar; 2: anexar/criar. Retorna null na falha e exige destino/retorno own. |
| `arquivo_ler(arquivo, buffer, capacidade): int` | Empréstimos exclusivos de Arquivo e buffer *byte. Retorna bytes, zero em EOF ou código nativo negativo. Pode ler menos que a capacidade. |
| `arquivo_escrever(arquivo, buffer, quantidade): int` | Empresta Arquivo exclusivamente e buffer para leitura. Retorna quantidade escrita ou erro negativo; pode escrever menos que o pedido. |
| `arquivo_fechar(arquivo): int` | Fecha o handle, mantendo o invólucro own. Idempotente, retorna zero ou erro negativo. |
| `erro_io(): int` | Último código positivo de IO/argumentos, substituído por operações posteriores. Capturar imediatamente. Códigos nativos não são portáveis. |
| `argumentos(): int` | Inclui executável no índice zero. |
| `argumento_tamanho(indice): int` | Bytes sem NUL ou -1 em erro. |
| `argumento_copiar(indice, buffer, capacidade): int` | Copia argumento e terminador; retorna bytes sem NUL, -1 em erro. Não trunca; capacidade deve exceder o comprimento. |
| `len(buffer own/borrow): int` | Capacidade em elementos, inclusive em campos e retornos emprestados. Ponteiros legados são rejeitados. |

Arquivo é opaco; não admite new, campos, casts, cópia implícita ou acesso ao handle. Pode atravessar assinaturas own/borrow, ser movido e compor campos own de structs. A limpeza fecha o handle e libera o invólucro uma vez, inclusive após fechamento explícito e nos desvios return/break/continue. Fechamento em um destrutor não transforma sua falha em erro retornado: use fechamento explícito para observar erro. Uma falha fatal termina o processo e depende da liberação de handles pelo OS.

A limpeza automática preserva `erro_io`, inclusive ao substituir um campo own ou limpar parâmetros antes de devolver uma falha de abertura. Operações explícitas de IO/argumentos podem substituí-lo. Assim o chamador consegue consultar o erro da operação que acabou de falhar.

Entradas/saídas em buffers gerenciados conferem a quantidade contra a capacidade antes de chamar o OS. O empréstimo se mantém durante a avaliação dos argumentos; calcule `len(buffer)` antes da chamada exclusiva. Leitura exige buffer mutável; escrita permite empréstimo compartilhado. Chamadas de IO nunca são pure. O perfil safe admite os recursos verificados; ponteiros/text legados continuam exigindo unsafe.

Windows converte caminhos UTF-8 estritos em UTF-16 e argumentos em sentido inverso, com CommandLineToArgvW e as regras do sistema para aspas/backslashes. Linux trata caminhos e argumentos como bytes do OS; não faz normalização Unicode. `text` legado conserva terminação NUL: caminhos não podem conter NUL como parte do nome. Não há APIs de diretórios, canonização, criação atômica exclusiva, rename, fsync, transações, permissões por origem ou proteção contra symlinks. Não usar a API como isolamento de scripts hostis.

## Bytes e UTF-8

`stdlib/texto.assis` acrescenta `Utf8Passo` por valor e funções safe `utf8_proximo`, `utf8_contar` e `utf8_valido`, sobre borrow *byte e comprimento explícito. NUL é um ponto de código válido. Rejeitam comprimentos inválidos, sequências truncadas, overlong, surrogates e pontos acima de U+10FFFF. Offsets são bytes; contagem é de pontos de código, sem normalização ou segmentação de grafemas.

`stdlib/conversoes.assis` oferece `formatar_int_buffer(numero, borrow mut buffer)`, sem alocação e sem terminador, incluindo INT64_MIN. Exige capacidade mínima de 20 bytes e retorna -1 se insuficiente. A representação geral de text com comprimento/vidas e slices de dados continuam pendentes; estas APIs de bytes não redefinem o text legado.

## Aplicação A: agregador CSV em fluxo

[21_relatorio_csv_stream.assis](../exemplos/21_relatorio_csv_stream.assis) é uma CLI completa para um dialeto delimitado: cabeçalho literal `valor` sem aspas, uma coluna de inteiros decimais int64, aspas opcionais nos campos numéricos, LF/CRLF e último registro opcionalmente sem LF. Rejeita campos extras, vazios, NUL, sinais `+`, aspas inválidas, CR isolado, linhas longas e overflow de cada número ou da soma. Não é um parser CSV geral: multiline, múltiplas colunas, BOM e comentários não são aceitos.

```text
assis build exemplos/21_relatorio_csv_stream.assis --safe --debug -o relatorio
relatorio entrada.csv saida.csv
```

No Windows, executar `relatorio.exe`. Entrada de exemplo: `valor\n1\n"-2"\n43\n`. Saída persistida: `registros,total\n3,42\n`. Códigos: 0 sucesso; 1 IO; 2 CSV inválido/limite; 3 overflow; 64 uso. A saída é aberta somente após validar e ler toda a entrada, preservando um arquivo existente nos erros de parse. Falhas após a abertura da saída podem deixar um arquivo incompleto; não há substituição atômica nem garantia de durabilidade contra queda de energia.

Usa um bloco de 65536 bytes, linha de 24 bytes e pequenos buffers de saída, sem crescimento proporcional à entrada. A parte numérica usa Result/ResumoCsv por valor. Recursos de arquivo e buffers são own; a conversão C dos argumentos fica em uma função safe com bloco unsafe explícito, mantendo o buffer vivo até terminar a abertura. Esse adaptador limita caminhos a 16384 bytes. O programa é independente dos fontes depois de compilado.

`tests/test-cli.py` confronta os resultados com CSV/inteiros de referência, atravessa fronteiras de blocos, valida entradas adversas, caminhos Unicode, falhas de leitura/escrita/abertura, permissões e preservação da saída nos dois modos de emissão. No Linux executado como root, o teste de permissão roda a CLI como nobody. Medições com duas entradas de tamanhos diferentes e pico de RAM estão em [Windows](../benchmarks/resultados/valores-io-alpha-windows.md) e [Linux](../benchmarks/resultados/valores-io-alpha-linux.md).

A aplicação A especificada foi atendida nesse dialeto. JSON geral, diretórios, coleções proprietárias de Texto, serviços B/C e a validação prolongada continuam abertos. A linguagem permanece experimental.

## Continuação alpha.8

Inteiros de largura fixa e f32/f64 têm [contrato numérico](NUMEROS.md). Módulos `namespace`/`public` e resolução offline com `assis.pkg`/`assis.lock` estão em [pacotes](PACOTES-E-NAMESPACES.md). `cli`, `json`, `tempo`, `log`, `iteradores` e `eventos` são bibliotecas opcionais novas, com empréstimos explícitos e limites documentados.

Comandos `fmt`, `test`, `doc`, LSP independente e símbolos/DWARF: [ferramentas](FERRAMENTAS-ALPHA.8.md). Relógio civil, espera, saída binária, cancelamento e persistência: [contratos](EVENTOS-E-PERSISTENCIA.md). Classes/Texto gerenciados gerais, variantes Move, capturas e slices gerais permanecem abertos; os caminhos C continuam com a fronteira legada documentada.

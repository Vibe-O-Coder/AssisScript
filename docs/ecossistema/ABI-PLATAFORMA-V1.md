# assis_platform_v1 — contrato inicial da ponte nativa

Estado em 29/10/2026: **interface especificada, provider não implementado**.
Serve shell/motor nativo confiáveis; página não importa essa biblioteca.
Mantém a [ABI C escalar existente](../FFI-C.md), sem agregados por valor,
varargs, closures C ou callbacks em threads estrangeiras.

Identidade da biblioteca: assis_platform_v1; versão de ABI 0x00010000.
Tipos abaixo têm largura explícita; int64_t corresponde ao int AssisScript.
Ponteiros de buffer são empréstimos locais durante a chamada, com comprimento
em elementos. O provider copia título/texto antes de retornar e não retém
ponteiros do runtime. Nenhum ponteiro atravessa processos.

```c
int64_t assisp_abi_version(void);
int32_t assisp_open(int64_t instance, int32_t width, int32_t height,
                   const uint8_t *title, int64_t title_len, int64_t *out_window);
int32_t assisp_poll(int64_t window, int32_t timeout_ms,
                   int64_t *event_words, int64_t word_capacity);
int32_t assisp_clear(int64_t window, uint32_t rgba);
int32_t assisp_text_utf8(int64_t window, int32_t x, int32_t y,
                       const uint8_t *text, int64_t length, uint32_t rgba);
int32_t assisp_present(int64_t window);
int32_t assisp_close(int64_t window);
```

Retornos: 0 sucesso, 1 sem evento (somente poll), -1 argumentos/UTF-8,
-2 handle expirado/categoria/instância, -3 provider indisponível, -4 recurso/OOM,
-5 thread incorreta, -6 erro de plataforma. out_window é zerado em falha.
Comprimentos negativos, ponteiro nulo com comprimento positivo, dimensões fora
de 1..16384, título acima de 4096 bytes e texto acima de 1 MiB são recusados
antes de alocação/cópia. NUL em texto é dado; título com NUL é recusado.
O provider valida ABI antes de criar janela. Bibliotecas obrigatórias ausentes
podem falhar no loader antes de main; -3 cobre somente backend opcional já
carregado. Não se promete recuperação de ausência de DLL por um código de API.

window é token opaco não nulo, validado em registro de categoria/instância/
geração. Não é HWND, ponteiro ou índice cru. O host atribui instance positiva,
sem reutilizá-la na vida do processo; esgotamento impede nova instância.
close revoga o token, descarta eventos e libera recursos exatamente uma vez.
close repetido retorna -2 sem chamar destruição nativa novamente.
O adaptador AssisScript zera o token em drop; depois de falha de open nada fecha.

Todas as operações ocorrem na thread principal que criou o provider. poll
aguarda eventos nativos sem espera ocupada; timeout_ms entre 0 e 50, em relógio
monotônico. Não chama código AssisScript por callback. Fila limitada a 256
eventos por janela; movimento/redimensionamento coalescem, close/teclas não
são perdidos silenciosamente: saturação de eventos não coalescíveis falha a
janela com -6 e exige recuperação pelo shell.

event_words exige pelo menos oito int64_t. Em sucesso, escreve exatamente
oito: ABI, kind, window, instance, generation, arg0, arg1, requestId.
Em sem evento/falha, zera os oito se o buffer válido tem essa capacidade.
kind: 1 close, 2 resize (largura/altura), 3 key (código/pressionado),
4 pointer (x/y), 5 focus (booleano/0), 6 scale (milésimos/0).
Teclas iniciais: Tab=9, Enter=13, Escape=27, Space=32. requestId é monotônico
por janela, sem wrap; esgotamento fecha a janela. O host rejeita evento de
token/instância/geração revogados antes de entregar. Esse buffer tem ABI C
local; IPC futuro terá framing e encoding explícitos, sem copiar memória nativa.

rgba tem R nos bits 31..24, G 23..16, B 15..8, A 7..0; clear/text usam
composição source-over e coordenadas de pixels físicos. A primeira prova pode
usar superfície por software. UTF-8 não comprova shaping/bidi/IME: E04-04 e
ponte de acessibilidade exigem interfaces/corpus adicionais antes de G1.

Inventário inicial de candidatos: Windows User32/GDI; Linux e macOS ainda sem
provider selecionado. Cada provider implementado deve registrar versão do SO,
SDK/bibliotecas, licença/redistribuição, binário/hash, thread, ABI e falhas.
Esses campos estão pendentes; nenhuma dependência externa é incluída agora.

Aceite futuro: oráculo C independente contra AssisScript em ambos os modos,
argumentos/retornos/buffers, provider ausente, UTF-8, OOM injetado, thread
errada, token forjado/expirado, fila saturada e 1.000 ciclos sem recursos
residuais. Execução nativa em cada destino anunciado. Todos **not-run**.

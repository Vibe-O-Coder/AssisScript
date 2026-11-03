Continuação 03/11/2026: [catalog-reading 1](PERFIL-LEITURA-CATALOGO-V1.md) acrescenta `assisp_frame_catalog_version` e `assisp_frame_catalog_commit`, com papéis 12..19. As quatro versões anteriores continuam intactas; o commit antigo recusa os novos papéis. Bibliotecas atualizadas exigem provider correspondente.

Continuação de 02/11/2026: [Frame local](PERFIL-FRAME-LOCAL-V1.md) acrescenta
layout/snapshot comum e extensão frame 1 do provider Windows. Publicação de
raster e MSAA é conjunta; Reader::Session/seleção, SSC agregado e catálogo
visual completo continuam separados. Os contratos anteriores são preservados.

# assis_platform_v1 — contrato inicial da ponte nativa

Continuação de 01/11/2026: extensão de preferências em `assisp_preferences`
(header e contrato [Reader](../BIBLIOTECA-reader.md)). Copia dez i64: versão 1,
highContrast, reducedMotion, background, foreground, button, buttonText,
disabledText, selection, selectionText. Capacidade mínima 10; buffer é zerado
em falha quando válido. Cores RGBA opacas de GetSysColor; flags de
SPI_GETHIGHCONTRAST/SPI_GETCLIENTAREAANIMATION. Nenhuma configuração é escrita.
Consulta aceita inscreve somente a janela em eventos 12 (reconsultar) e 13
(visibilidade). Demais callers não recebem novos eventos; todos os símbolos
anteriores e versões base/viewer/reader são conservados. Ponteiro emprestado
não é retido, chamada fica na thread proprietária, token revogado retorna -2.
Os novos imports exigem DLL atual; ausência de símbolo é erro do loader.
Sem dependência redistribuída nova; User32/GDI já inventariados. Testes na
[unidade de transações](../relatorios/2026-11-01-m3-transacoes-preferencias.md).

Estado em 01/11/2026: **provider Windows x64 e extensão de apresentação local,
validados como prova parcial**.
Contrato do módulo em [BIBLIOTECA-window.md](../BIBLIOTECA-window.md), implementação
em providers/platform/windows.c e relatório em
[M1 plataforma](../relatorios/2026-10-29-m1-plataforma-windows.md).
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

Provider Windows: User32/GDI/UCRT do sistema, com APIs que exigem Windows 10
1703+; somente o host Windows x64 registrado na evidência foi executado.
GCC/headers MinGW-w64 de MSYS2 constam do inventário de build da unidade.
Nenhuma biblioteca ou fonte Microsoft é redistribuída. Shim próprio segue
a licença do repositório; GCC Runtime Exception/avisos MinGW continuam em
THIRD_PARTY_NOTICES.md. Linux/macOS permanecem sem provider.

Aceite desta prova: oráculo C independente contra AssisScript em ambos os modos,
argumentos/retornos/buffers, provider ausente, UTF-8, OOM injetado, thread
errada, token forjado/expirado, fila saturada e 1.000 ciclos sem recursos
residuais. Resultados por teste, hashes e limitações no relatório/evidência.
DLL ausente falha no loader; -3 foi injetado somente no backend opcional de
teste já carregado. A produção não expõe os mecanismos de injeção/inspeção.
Execução de providers em outros sistemas, IME, leitores de tela, 200%/monitores,
soak integrado e visualizador HTDL continuam **not-run**; nenhum gate aprovado.

## Extensão viewer 1 — 01/11/2026

As entradas v1 e assisp_abi_version=0x00010000 são preservadas. Somente
std/viewer importa os novos símbolos; std/window continua carregável contra
um provider v1 antigo, comprovado pela fixture de negociação original.
Um executável que importa viewer exige a DLL reconstruída; símbolo ausente
falha no loader antes de main, não é convertido em -3.

```c
int64_t assisp_view_version(void); /* 1 ou -5 */
int64_t assisp_measure_utf8(const uint8_t *text, int64_t length);
int32_t assisp_rect(int64_t window, int32_t x, int32_t y,
                   int32_t width, int32_t height, uint32_t rgba);
```

measure aceita até 4096 bytes, NUL explícito e UTF-8 estrito, retorna
(height << 32) | width ou erro negativo. Mede DEFAULT_GUI_FONT do sistema;
não mantém bytes/fontes do chamador, cria/libera seu DC durante a chamada.
rect exige width/height não negativos, calcula extremos em 64 bits, recorta
à superfície e usa a composição source-over existente. Falha de medida não
muda a superfície. Contratos de thread/identidade/ownership/falhas v1 se aplicam.

poll pode produzir ainda 7 left-down (x/y), 8 left-up (x/y), 9 wheel
(delta vertical/0), 10 capture-lost (0/0). Down toma captura, up a libera;
perder captura gera cancelamento. Não há coalescimento desses eventos.
O host conserva a interpretação/foco/scroll. O adaptador aceita 1..10;
programas antigos que ignoram os novos eventos mantêm seu comportamento.

Na unidade M2 há janela HTDL local real, testes de entradas/resize/fechamento
e dumps da superfície. A captura Computer Use falhou; IME/leitor de tela/
200%/outros providers permanecem sem aceite. O parágrafo not-run anterior
descreve a evidência histórica M1. Nenhum gate foi aprovado.

## Continuação reader 1 — 01/11/2026

Seleção de leitura por escalares UTF-8, cópia explícita, zoom de fonte/reflow
100/200% e projeção MSAA plana documento/blocos foram implementados em
std/reader.assis. [Contrato completo](../BIBLIOTECA-reader.md),
[relatório e evidência](../relatorios/2026-11-01-m3-leitura-acessivel.md).
A ABI base 0x00010000 e extensão viewer 1 permanecem; imports novos só no Reader.
Eventos 11 carregam document_instance/child_index e são revalidados pelo host.
Ponte copia buffers, não retém ponteiros AssisScript; referências COM antigas
ficam desconectadas em navegação/close da Window. Novos imports/formatos estão
no header assis_platform_v1.h e em providers/platform/reader.inc.
A projeção usa 8 palavras i64 por registro: role,flags,x,y,width,height,
name_offset,name_length. Registro 0 é document=1; demais 6/8/9 são paragraph/
heading/button. Flags disabled=1, focused=2, offscreen=4. Até 32769 registros,
1048608 bytes de nomes; ranges/UTF-8/identidade validados antes de cópia.

Cliente MSAA externo, clipboard isolado, fontes GDI e casos adversos têm
execução Windows x64; Linux tem biblioteca/fallback, sem provider. Quatro
surfaces reais são dumps, não screenshots de desktop. Computer Use parou em
app approval timed out. Leitor real, contraste/movimento, DPI multimonitor,
grafemas/edição/IME e UIA TextPattern continuam sem aceite. A escala 200% da
fonte não é escala do OS. Nenhum gate aprovado. O not-run anterior é histórico.

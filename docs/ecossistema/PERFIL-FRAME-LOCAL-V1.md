Continuação 03/11/2026: [Frame Reader](../BIBLIOTECA-framereader.md) seleciona a geometria composta e [Frame host](../BIBLIOTECA-framehost.md) ativa HTDL bootstrap/FS/SSC/layout/leitura em conjunto. As seções anteriores permanecem históricas; catálogo visual/recursos externos/ASV2, desktop/leitor/DPI/IME e gates continuam abertos.

Continuação 03/11/2026: [movimento agregado](PERFIL-MOVIMENTO-PAGINA-V1.md) compõe o Frame candidato antes do selo de Packet. Layout e ABI frame 1 permanecem; o item SSC agregado na lista histórica abaixo foi implementado nesse perfil finito. Reader/seleção e aceites continuam abertos.

# Frame local v1 — contrato de desenvolvimento

02/11/2026. Perfil `frame-local-bootstrap-1`, fundação M5/E08-02, sem gate.
Base normativa de desenvolvimento: snapshot congelado HTDL, documentos
12/14/17 e seus hashes. Não altera HTDL 0.1, o ADR ASV2, ABI base/viewer/reader,
perfil numérico FS ou SSC. [pageframe](../BIBLIOTECA-pageframe.md) especifica
layout/limites/falhas; [pagepresent](../BIBLIOTECA-pagepresent.md) composição.

A implementação não reavalia FS a partir da geometria final. Restrições de
largura descem; altura automática sobe; offsets são de composição. O host
fornece entradas FS e mantém produtor único/transação da página inteira.
FS falho conserva saídas sobreviventes, aplicadas à semântica atual. Falha do
motor conserva o quadro anterior com acerto bloqueado. Não há loop de equilíbrio.

Frame é proprietário e imutável após construção. Desenho, hit test e projeção
MSAA usam as mesmas caixas, recortes e frameVersion. Cada ativação valida
documentInstance/semanticVersion/frameVersion/NodeId; uma projeção acessível
posterior revoga ações da anterior. O host mantém somente o par Frame/Packet
ativo como autoridade de acerto. São identidades locais do host, não capacidades.

Extensão C **frame 1**, Windows x64, thread proprietária:

```c
int64_t assisp_frame_version(void); /* 1, ou -5 */
int64_t assisp_frame_current(int64_t window); /* projection, 0, ou erro */
int64_t assisp_frame_measure(const uint8_t *text, int64_t length,
                            int32_t font_pixels, int32_t weight);
int32_t assisp_frame_commit(int64_t window, int64_t projection, uint32_t bg,
    const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
    const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length);
```

Cada comando tem 14 palavras i64: kind(0 rect/1 text), x,y,width,height,
clipX,clipY,clipWidth,clipHeight,RGBA,fontPixels,weight,textOffset,textLength.
Primitivos são source-over, em ordem. Medida exige até 4096 bytes UTF-8 estritos;
retorna `(height << 32) | width`. Comando text tem os mesmos 4096 bytes,
fontPixels 1..256 e weight 100..900. Recortes ficam dentro da superfície;
coordenadas/extensões dos primitivos têm guarda de 16777216. Cores são RGBA u32.
Access usa o formato de oito palavras da extensão Reader, com nome UTF-8 e
limites acessíveis já recortados. Primeira entrada é documento; demais 6/8/9.

Projection deve ser positiva e maior que a anterior na Window. -1 argumento,
-2 token/projeção antiga, -4 recurso/limite, -5 thread, -6 GDI/OS; retornos da
ponte acessível são preservados. Não há callback AssisScript. Buffers são
emprestados somente durante a chamada. Texto e nomes necessários são copiados;
fontes/DCs temporários são liberados em sucesso/falha. Sem ponteiros entre processos.

Commit prepara superfície extra sob o teto nativo transitório de pixels,
termina todo raster e só depois chama a publicação acessível. Falha libera a
superfície candidata; sucesso troca superfície após a ponte, sem nova operação
fallível nesse caminho. A thread não despacha tarefas de página durante isso.
`assisp_present` permanece separado: estado lógico e apresentação física não
são equivalentes. Resize do OS e falha física têm recuperação do host.

Política de strings/fontes/licença/thread e inventário User32/GDI/Oleacc do
provider anterior permanecem. Extensão importa símbolos novos somente em
pagepresent; window/viewer/reader existentes conservam imports e ABI. DLL antiga
não satisfaz os novos imports: o loader falha, não retorna indisponível.

Limites visuais preservados: catálogo além do bootstrap, estilos inline mistos,
radius/imagens, scroll interno independente, layout subpixel/intrínseco geral,
ligação automática de parent.availableWidth, SSC agregado/canais, seleção/IME,
DPI/múltiplos monitores, leitor de tela real, snapshots de desktop e perfis
completos permanecem na fila. G1/G3 continuam abertos; Easy por último.

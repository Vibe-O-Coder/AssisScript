# Movimento de página v1 — contrato de desenvolvimento

Unidade iniciada em 02/11/2026 e concluída em 03/11/2026, America/Fortaleza.
Perfil `page-motion-256-v1`, M5/E08-03/E08-04; sem gate aprovado.
Sobreposição de host ao SSC finito e Frame local; não altera HTDL 0.1,
o snapshot congelado, coeficientes, ABI de plataforma ou executor ASV2.

[motionpage](../BIBLIOTECA-motionpage.md) define limites, transações, tempo,
ownership, erros, composição e política de foco. Recurso SSC e FS pertencem ao
host confiável. O conteúdo não atribui foco, origem, permissões ou relógio.
O rascunho 11 define posição/velocidade/repouso e 17 a ordenação de transações;
PROVENANCE.json fixa esses documentos e a referência de inteiros independente.

O produtor de presentation.offsetX/Y é único por nó. A quota de 256 é do
conjunto vinculado, não só dos canais acordados; hidden e repouso contam.
Desenho, hit test e acessibilidade consomem uma composição de Frame, depois
selada por Packet. Nenhuma posição física é entrada autoral de FS.

Prepare copia a dinâmica ativa para um candidato independente. Falha de FS
preserva os destinos sobreviventes e não desfaz disabled/hidden/remoção atuais.
Falha de composição/raster/MSAA conserva o estado ativo e não consome seu
tempo. Mudança de semântica/estilo antes de commit revoga o candidato.
Publicação nativa e commit do coordenador ocorrem sem despacho intermediário
na thread proprietária; não há ponteiros entre processos nem callback de página.

Foco/edição protegem o nó e seus ancestrais, sem congelar outro painel.
Ocultação, suspensão, reducedMotion e ausência de backlog conservam o contrato
numérico SSC. O fallback de posição fora do domínio físico é explícito S401.
Não se declara domínio contínuo, tolerância global, precisão subpixel geral,
entrada IME nativa, seleção, igualdade de pixels entre sistemas ou G1/G3.

Aceites ainda necessários: leitor real/desktop/DPI/monitores/IME, catálogo
visual completo, Reader/seleção, loader/código/recursos, quotas RSS/disco/órfãos,
macOS/ARM nativos, rede/perfis/persistência/busca, M4–M9, 24h, distribuição e
terceiro. Easy permanece a última etapa de todo o projeto.

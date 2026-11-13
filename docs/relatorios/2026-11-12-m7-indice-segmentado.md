# M7 — Índice por segmentos com orçamento de memória

12/11/2026, America/Fortaleza. Base pública `13e81a897388e694d9a02bcfb4b3984665d7c3c9`
da branch `work/ecosystem-2026-11-11`, conferida com `git ls-remote`.
Continuação isolada em `work/eco-70-20261112`, branch
`work/ecosystem-2026-11-12`. IDs E02-05, E09-01/02/03/05 e E10-03/04.
A etapa segmentada avança de **56,50% para 58,00%, 0/5 gates** após
o [serviço local](2026-11-12-m8-servico-busca-local.md).

## Persistência, memória e ranking

O snapshot ASIX carregava todos os postings antes de consultar ou atualizar.
O novo ASIS 1 mantém 16 faixas de IDs. O [exemplo 71](../../exemplos/71_search_index.assis)
lê uma faixa, consulta ou atualiza, libera a memória e passa à próxima.
Os mesmos tokens, normalização, posição, frequência e desempate do ASIX
participam do ranking global. São preservadas até 256 posições e nenhum
resultado é entregue antes da validação do último segmento e do EOF.
Os comandos ASIX continuam consultando seus arquivos anteriores.
[Formato e API](../BIBLIOTECA-searchsegments.md).

O lote de escrita é agrupado por faixas crescentes. Há espaço para
até 65.536 ocorrências e 4 MiB de termos por faixa. Uma publicação reescreve
o bundle inteiro com compactação de ocorrências obsoletas, lock único,
arquivo candidato, flush e troca atômica. Após kill, o leitor conserva a
versão publicada e o escritor seguinte substitui o candidato parcial.
No Windows, um leitor com o arquivo aberto ainda pode fazer a troca ser
recusada. O leitor verifica todos os checksums antes de expor a consulta.

## Testes

A [suíte de segmentos](../../tests/test-searchsegments.py) compara 432
documentos, 3.888 ocorrências e cinco offsets por modo com um modelo Python.
O bundle do oráculo tem 77.927 bytes e SHA-256
`89b03fe213c0b77320982ea60d8b232f185e9a63fed72ee6c5eb219f6b3e28de`
em Windows e Linux x64, com e sem otimização. A suíte verifica HTDL inline,
substituição e remoção cruzando faixas, atualização inválida tardia, troca
de ordem de frames, truncamento, versão desconhecida, corrupção, bytes
extras, escritor concorrente recusado e kill após escrita parcial.

No Ubuntu WSL2 x64, um processo otimizado com `--debug` recebeu
`RLIMIT_AS=33.554.432` bytes. Ele construiu, consultou e atualizou
**42.963.592 bytes de índice para 3.200 documentos** sob o mesmo limite.
As amostras de construção, consulta e atualização duraram 12,924 s,
5,761 s e 12,641 s. A medição cobre espaço de endereçamento por processo
no Linux. O teste de limite foi pulado no Windows e não mediu RAM total
do host nem latência em produção.
[Windows](../ecossistema/evidencias/search-transport-segments-2026-11-12/segments-windows.json) ·
[Linux](../ecossistema/evidencias/search-transport-segments-2026-11-12/segments-linux.json).

Segmentos passaram em **10 testes Windows e 11 Linux**, com um caso Linux
pulando no Windows. A regressão ASIX passou em **6 Windows e 7 Linux**, com
o teste POSIX de escrita curta pulando no Windows. As duas execuções finais
contam a fixture HTDL com `type=text` e o código 2 que o leitor de stdin
devolve em UTF-8 inválido. [ASIX Windows](../ecossistema/evidencias/search-transport-segments-2026-11-12/search-windows.json) ·
[ASIX Linux](../ecossistema/evidencias/search-transport-segments-2026-11-12/search-linux.json).

## Régua e continuidade

E02-05 passa 1→2. E09-02, E09-03 e E10-03 passam 2→3 pela validação dos
formatos, limites, recuperação e resultados nos dois hosts. E09-01/05
e E10-04 recebem evidência. Ficam pendentes merge seletivo, compressão,
migração e backup, perda física de energia e ranking com relevância rotulada.
O G4 também requer crawler persistente, política de rede e consulta
voluntária integrada ao Browser. A meta de 70% fica a 12 pontos.
[Fila integral](../ecossistema/FILA-M0-M1.md).

A unidade de persistência e a consulta HTTP usam o mesmo formato e seguem
na [branch de trabalho](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-12).
O [relatório do serviço](2026-11-12-m8-servico-busca-local.md) registra a
conferência da revisão no GitHub.

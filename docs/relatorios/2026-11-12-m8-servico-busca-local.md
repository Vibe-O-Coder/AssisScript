# M8 — Serviço HTTP local de consulta

12/11/2026, America/Fortaleza. Base pública
`13e81a897388e694d9a02bcfb4b3984665d7c3c9` da branch
`work/ecosystem-2026-11-11`, conferida no GitHub com `git ls-remote`.
Branch `work/ecosystem-2026-11-12`, cópia `work/eco-70-20261112`.
IDs E05-04/05, E09-04, E10-05, E11-01/03.
O serviço avança **54,30% → 56,50%, 0/5 gates**. A
[etapa de segmentos](2026-11-12-m7-indice-segmentado.md) fecha a rodada em **58,00%**.

## Transporte e consulta

O [exemplo 73](../../exemplos/73_search_service.assis) atende em
`127.0.0.1` e mantém até oito conexões com I/O não bloqueante.
O operador concede o diretório de trabalho e uma chave por corpus.
O serviço recebe a chave em stdin. Cada pedido usa autoridade exata,
autenticação, enquadramento explícito e uma consulta UTF-8 limitada.
O corpo e a chave ficam fora dos logs. Requisições com `Origin`,
headers de framing duplicados, campos dobrados, cabeçalhos e corpos
excessivos recebem recusa. O processo pode expirar e fechar os sockets.
[Contrato de consulta](../BIBLIOTECA-searchservice.md).

Uma requisição recebe a revisão publicada do índice ASIX 1 ou ASIS 1.
O escritor pode publicar durante a vida do serviço. A próxima consulta
abre a revisão disponível e valida seus bytes. Uma falha de leitura ou
corrupção devolve 503 com corpo vazio. Um cliente lento expira sem prender
as outras conexões durante a leitura do pedido. O processamento dos
snapshots corre em série. O caminho ASIS pode ocupar o loop por vários
segundos no corpus maior e precisa de medição e execução separada antes
da integração remota. Os adaptadores são Winsock e glibc, sem nova
biblioteca distribuída. [ABI do transporte](../BIBLIOTECA-loopback.md).

## Validação

O [cliente independente](../../tests/test-searchservice.py) verifica 16
testes por host nos dois modos. Usa HTTP e sockets reais, incluindo
fragmentação de CRLF e UTF-8, meio fechamento, atraso, cabeçalhos
ambíguos, chave errada, dois corpora simultâneos, mudança durante a vida
do serviço, reinício, arquivo ausente ou truncado, porta ocupada e saída
com prazo. Uma consulta enquanto outro cliente mantinha uma linha
incompleta levou de 7,338 a 11,641 ms nas quatro amostras registradas.
O ensaio usa corpus pequeno e não estabelece p95 sob carga.
[Windows](../ecossistema/evidencias/search-transport-segments-2026-11-12/service-windows.json) ·
[Linux](../ecossistema/evidencias/search-transport-segments-2026-11-12/service-linux.json).

O [resumo](../ecossistema/evidencias/search-transport-segments-2026-11-12/summary.json)
liga as execuções de exemplos, instalação isolada, testes da trilha visual,
hashes dos binários e integridade de 57 referências congeladas. Os 16
cenários integrados da referência continuam not-run. O Windows usou a
DLL reconstruída para o Frame. Linux usou Ubuntu WSL2 x64. macOS e ARM64
seguem sem execução nativa desta unidade. A matriz de CI inclui as novas
suítes. [Inspeção visual](2026-11-12-m3-revalidacao-visual.md).

O conjunto focado passou em **65 testes no Windows e 57 no Linux**, com 2
e 10 casos pulados, respectivamente. Foram verificados **74/74 exemplos por
host**, ambos os finais do RPG e 35 bibliotecas na instalação isolada. O
instalador executou a consulta HTTP, as duas variantes do índice e a demo
de recursos instalados. Windows também passou pela janela instalada, quatro
testes de locks do instalador e 40 testes Node. A demo do serviço emitiu
PE x64, ELF x64/ARM64 e Mach-O x64/ARM64. O perfil de socket executa
em Windows e Linux x64. [Candidato e hashes](../ecossistema/evidencias/search-transport-segments-2026-11-12/summary.json).

Comandos principais, com `ASSIS_BIN` apontando para o compilador nativo
reconstruído em cada host.

```text
python tests/test-searchindex.py
python tests/test-searchsegments.py
python tests/test-searchservice.py
python tools/validate-examples.py --output build/session/examples-<host>.json
python tools/verify-local-resource-install.py --confined --search-forms --output build/session/install-<host>
python tools/check-ecosystem-references.py --output build/session/reference-integrity.json
python tools/generate-install-manifest.py --check
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
git diff --check
```

E05-04 e E09-04 passam 0→1 pelo I/O incremental limitado e pela separação
de dois corpora por diretório e chave. E05-05 e E10-05 passam 0→2 pela
execução funcional delimitada. Administração remota, TLS, serviço
integrado ao Browser, crawler, partição por origem e proteção contra
abuso em escala continuam na fila. O perfil de busca e a etapa M3 de
edição podem avançar independentemente. [Fila integral](../ecossistema/FILA-M0-M1.md).

## Publicação

Destino autorizado [Vibe-O-Coder/AssisScript](https://github.com/Vibe-O-Coder/AssisScript/tree/work/ecosystem-2026-11-12).
A conferência do SHA remoto e a situação da PR entram no adendo.

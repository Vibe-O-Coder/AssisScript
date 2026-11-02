# std/page — SDK htdl_v1 do perfil ASV2

Biblioteca opcional, namespace `htdl_v1`, versão 1 / read-only-1.
Compilável somente como página com `--target page-asv2` para execução pelo
host local. Os externs são substituídos por imports limitados; não há DLL
nativa de página distribuída. Check nativo pode analisar as assinaturas,
mas run nativo precisa de provider de teste explícito e não é o fluxo do SDK.

API canônica em inglês: version, counter_add, event_get, last_error, state_get,
state_set, node_at, node_kind, node_flags, node_count. Tipos/erros/assinaturas,
envelopes e semântica estão no
[contrato versionado](ecossistema/PERFIL-PAGINA-ASV2.md).
`last_error` distingue erro de uma célula que contém valor negativo.

Exemplo compilável: [counter.assis](../exemplos/pages/counter.assis).

```text
assis build exemplos/pages/counter.assis --target page-asv2 -o counter.asv2
assis build exemplos/48_page_runtime.assis -o page-host
page-host counter.asv2
```

No Windows, o host recebe sufixo .exe. Sua saída é `PAGE 2 STATE 2` após init
e duas ativações explícitas pelo shell. Não há navegação remota, mutação HTDL,
FS/SSC ou renderização do contador nessa demonstração.

Valores de célula são privados e arbitrários i64; slot 0..31. Queries de
documento começam negadas e requerem concessão nativa. Handles não contêm
ponteiros e só endereçam a projeção imutável da própria Page. APIs de memória,
arquivos, processos, rede ou relógio não existem nesse vocabulário.

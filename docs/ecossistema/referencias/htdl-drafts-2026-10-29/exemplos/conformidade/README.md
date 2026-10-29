# Corpus declarativo de conformidade

[cenarios.json](cenarios.json) contém entradas e resultados **esperados para uma implementação futura**, com status `not-run`. Não existe runner de conformidade neste diretório. A inspeção de integridade dos arquivos não é resultado de linguagem.

`valid/` contém fontes auxiliares de análise e execução. `invalid/` contém violações intencionais e não deve ser usado como aplicação demonstrativa. Para fontes FS/SSC isoladas, o contexto é [context.htdl](context.htdl); o driver futuro injeta o conjunto indicado no índice antes de ligar produtores. Isso é recurso do teste do motor, não sintaxe adicional de HTDL.

As ações `setPageState`, `setDisabled`, `removeNode`, `createSection` e demais passos do índice são vocabulário descritivo do driver. Não afirmam funções novas na API pública. Os testes de remoção/recriação são testes internos da árvore; criação dinâmica continua fora da API inicial de página.

O documento [19](../../docs/19-conformidade-e-cenarios.md) define níveis de evidência, matriz de aceitação e informações que um relatório futuro precisa preservar. Não executar provas do AssisScript por iniciativa deste corpus durante o teste de 24 horas em andamento.

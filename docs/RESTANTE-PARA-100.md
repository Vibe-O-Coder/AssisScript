# Critério restante — candidato ARM64/v1, 29/10/2026

**99/100 pontos** na mesma régua de 35 critérios, com pesos e histórico preservados.
P6-POLICY foi concluído pela aplicação dos ícones v1 e revisão de distribuição.
P5-TARGET passa a parcial: a implementação está pronta e validada localmente em
ARM64 via QEMU, com ABI C e GDB remoto; falta a aprovação nativa remota.

| Critério | Falta | Evidência exigida |
| --- | ---: | --- |
| P5-TARGET | 1 ponto | Passar o Actions do commit candidato em Linux ARM64 e macOS Intel/Apple Silicon, incluindo execução ARM64, instalador, GDB/LLDB, assinatura e pacotes. |

O workflow agora executa programas ARM64 nativamente nesses runners. Não depende
de Rosetta ou QEMU para aprovar os jobs ARM64. Para executar essa matriz, publicar
a branch candidata e abrir o PR é a etapa seguinte. O sucesso da revisão anterior
não é reutilizado como evidência do código novo. Após os checks do novo commit
passarem, anexar o resultado em VALIDACAO-TARGETS-V1.json e então concluir o critério.

Implementação: [ARM64-NATIVO.md](ARM64-NATIVO.md). Política e ícones:
[PROCEDENCIA-V1.md](PROCEDENCIA-V1.md). Limites de linguagem previamente declarados
continuam fora do escopo; esta rodada não adiciona navegador/HTDL, threads,
varargs C, closures pure, Unicode/grafemas ou registro remoto de pacotes.

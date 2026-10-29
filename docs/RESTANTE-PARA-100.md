# Plano concluído — ARM64/v1, 29/10/2026

**100/100 pontos** na mesma régua de 35 critérios, com pesos e histórico preservados.
Não restam critérios abertos dentro do plano de evolução das fases 0–6.

| Critério final | Entrega | Evidência |
| --- | --- | --- |
| P5-TARGET | Emissão/runtime Linux e macOS ARM64; instaladores, símbolos macOS, GDB/LLDB e execução ARM64 nativa | [Actions 40847421481](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40847421481), revisão `bb1605d`, seis jobs aprovados incluindo pacotes |
| P6-POLICY | Ícones v1 aplicados no editor, instaladores e binários; procedência, avisos e redistribuição revisados | [PROCEDENCIA-V1.md](PROCEDENCIA-V1.md) e gate de identidade/pacotes aprovado |

Os dois runners ARM64 executaram instruções ARM64 nativamente. Linux ARM64
passou 32 suítes / 296 casos, com GDB e os prazos TLS nativos. macOS Intel e
Apple Silicon passaram execução, ABI C, arquivos, DWARF, LLDB e instalação;
Apple Silicon também passou a assinatura ad hoc. Windows e Linux x64
passaram suas matrizes completas, reconstruções limpas e verificações de pacote.

[VALIDACAO-TARGETS-V1.json](VALIDACAO-TARGETS-V1.json) preserva os hashes,
relatórios e a referência exata da aceitação. A validação local anterior fica
identificada como histórica. Os ensaios curtos desta revisão não substituem nem
relabelam o ensaio histórico de 24 horas ou o aceite humano anterior.

A versão continua experimental. Os limites declarados em
[ARM64-NATIVO.md](ARM64-NATIVO.md) e [SUPPORT.md](SUPPORT.md) permanecem vigentes.
Conclusão do plano não inclui navegador/HTDL, Windows ARM64, notarização Apple,
threads, varargs C, closures pure, grafemas ou registro remoto de pacotes.

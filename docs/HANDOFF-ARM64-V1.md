# Handoff ARM64 / ícones v1 — 29/10/2026

**P5-TARGET e P6-POLICY concluídos. O plano está em 100/100**, com os mesmos
35 critérios, pesos e registros históricos. A revisão de implementação
`bb1605d713e1862cac9ec8ba3c99a41a7b882bcf` passou nos seis jobs do
[Actions 40847421481](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/40847421481).
O [PR #3](https://github.com/Vibe-O-Coder/AssisScript/pull/3) está em rascunho,
sobre `development/p5-ir`, sem merge ou nova tag.

- Emissão ELF/Mach-O ARM64 diretamente da IR, runtime próprio, ABI C/callbacks,
  instalação Linux/macOS por arquitetura e seleção correspondente no editor.
- DWARF/símbolos Mach-O, assinatura ad hoc ARM64 e bundles `.app` com v1.
- Ícones v1 em PNG/ICO/ICNS, editor, compilador, instalador e programas gerados;
  stickers e binários históricos excluídos da distribuição revisada.
- **32 suítes / 296 casos em cada um de Windows x64, Linux x64 e Linux ARM64**.
  A rodada ARM64 do Actions foi nativa, incluindo GDB, ABI C e TLS com os prazos
  normais. A execução local anterior via QEMU permanece identificada como tal.
- macOS Intel e Apple Silicon passaram execução nativa, arquivos, ABI C,
  DWARF, LLDB com parâmetros/locais/backtrace, e instalação/desinstalação offline.
  Apple Silicon passou também a verificação de assinatura ad hoc.
- 85 testes de editor/ferramentas, 130 verificações do harness Windows,
  33 exemplos por sistema x64, reconstruções Windows/Linux com bytes idênticos,
  regressão de desempenho e ensaios curtos de 120 segundos aprovados.
- ZIP/VSIX aprovados pelo Actions, com cinco compiladores nativos,
  instalador Windows, runtime, bibliotecas, fontes, avisos e identidade v1.

A validação macOS também cobre retornos de erro das APIs C Darwin e a
separação dos segmentos de memória ao incorporar DWARF. Os binários locais
foram substituídos pelos artefatos dessa execução; seus hashes e a procedência
do download estão em [VALIDACAO-TARGETS-V1.json](VALIDACAO-TARGETS-V1.json).

O compilador Linux usa glibc compartilhada do sistema; estes binários foram
construídos no Ubuntu 24.04. Os programas gerados sem extern continuam com
runtime freestanding. A política e os inventários correspondem aos binários
efetivos. Novas dependências ou provedores exigem nova revisão.

A versão continua **3.3.0-alpha.15, experimental**. A assinatura macOS é ad hoc,
sem Developer ID/notarização. Windows ARM64 e adaptação automática dos módulos
opcionais Linux/Windows de rede/processos para macOS não fazem parte desta
entrega. Ensaios curtos atuais não substituem o ensaio histórico de 24 horas
nem o aceite humano anteriormente registrado.

Implementação: [ARM64-NATIVO.md](ARM64-NATIVO.md). Política:
[PROCEDENCIA-V1.md](PROCEDENCIA-V1.md). Régua: [PROGRESSO.md](PROGRESSO.md).

# Handoff ARM64 / ícones v1 — 29/10/2026

O candidato implementa P5-TARGET e conclui P6-POLICY na distribuição revisada.
A régua está em **99/100**, aguardando apenas a aprovação nativa remota do
novo commit para concluir P5-TARGET. Nenhum resultado antigo é relabelado.

- Emissão ELF/Mach-O ARM64 diretamente da IR, runtime próprio, ABI C/callbacks,
  instalação Linux/macOS por arquitetura e seleção correspondente no editor.
- DWARF/símbolos Mach-O, assinatura ad hoc ARM64 e bundles `.app` com v1.
- Ícones v1 em PNG/ICO/ICNS, editor, compilador, instalador e programas gerados;
  stickers e históricos não são empacotados na nova distribuição.
- **32 suítes / 296 casos Windows** e **32 / 296 Linux** aprovados.
  ARM64: **32 suítes / 296 casos relatados**, executados em QEMU;
  o debugger nativo incompatível com o host foi dispensado nesse corpus e
  substituído por GDB remoto ARM64, que verificou parâmetros, locais,
  shadowing e backtrace nos dois modos de otimização.
- 85 testes de editor/ferramentas; 130 verificações do harness Windows;
  33 exemplos por sistema; reconstruções limpas Windows/Linux com bytes idênticos;
  assinatura macOS verificada página por página, DWARF validado pelo LLVM;
  ensaios curtos de 120 segundos aprovados nos dois sistemas.

Uma mudança de distribuição: o compilador Linux usa glibc compartilhada do
sistema, mantendo a possibilidade de substituição e depuração dos componentes
LGPL. Os programas gerados sem extern continuam com runtime freestanding.
A política, avisos e inventários correspondem a esses binários efetivos.

Implementação: [ARM64-NATIVO.md](ARM64-NATIVO.md). Política:
[PROCEDENCIA-V1.md](PROCEDENCIA-V1.md). Hashes, relatórios e limites:
[VALIDACAO-TARGETS-V1.json](VALIDACAO-TARGETS-V1.json).

## Próxima etapa

Publicar a branch candidata em Vibe-O-Coder/AssisScript e abrir um PR em rascunho
sobre `development/p5-ir`. A matriz passou a exigir execução ARM64 nativa nos
runners Linux/Apple Silicon, GDB/LLDB, instalação e validação dos pacotes.
Após passar o Actions do candidato, registrar a URL/commit e concluir P5-TARGET
na régua, preservando os 35 critérios e pesos. Este handoff não afirma que essa
rodada remota já ocorreu. A licença/procedência é da distribuição atual; novas
dependências ou novos provedores exigem outra revisão.

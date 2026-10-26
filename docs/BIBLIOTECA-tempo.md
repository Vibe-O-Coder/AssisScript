# tempo — prazos

Opcional. `#yuri <std/tempo.assis>`, namespace `tempo`.

`apos(ms): Prazo` captura prazo monotônico Copy, com campo `valido` para erros/overflow. `restante(prazo): int` retorna milissegundos não negativos ou -1. `esperar(prazo): bool` espera em fatias de até 50 ms e retorna false em falha. `relogio_civil` fica separado de `agora`; consulte [eventos e persistência](EVENTOS-E-PERSISTENCIA.md). Não há timezone/calendário, thread ou promessa de precisão de agendamento do OS.

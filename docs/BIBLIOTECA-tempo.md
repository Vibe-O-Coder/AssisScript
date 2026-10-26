# tempo — prazos

Opcional. `#yuri <std/time.assis>`, namespace `time`.

`after(ms): Deadline` captura prazo monotônico Copy, com campo `valid` para erros/overflow. `remaining(prazo): int` retorna milissegundos não negativos ou -1. `wait_until(prazo): bool` espera em fatias de até 50 ms e retorna false em falha. `civil_ms` fica separado de `monotonic_ms`; consulte [eventos e persistência](EVENTOS-E-PERSISTENCIA.md). Não há timezone/calendário, thread ou promessa de precisão de agendamento do OS.

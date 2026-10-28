# Canonical English API — alpha.14

The active language uses fn, class, main, init, import and English builtin names.
The historical Assis/Fodase spellings and Portuguese builtin aliases were removed.
The separate historical compiler in ../historical preserves the joke edition.
--legacy selects manual memory contracts in the current syntax; it never restores
old keyword spellings or word comments.

Use tools/migrate-syntax.py old.assis --write to translate syntax, then review
imports and calls against API-MIGRATION.json. The syntax translator preserves
strings and comments and translates old word comments to /* ... */. Standard
library module/member renames still require the mapping file. Regenerate project
lockfiles with assis lock after changing imported source.

New code should use safe fn main, unicode::String, slice<byte> and own/borrow.
Global const, byte character literals, super.init, is/as and write are available.
Classes have explicit receiver contracts for managed use. Constructors may have
different signatures from their bases; ordinary virtual methods remain invariant.

Closures with explicit val/own/borrow captures and Move enum payloads already
exist. Methods with independent generic parameters are still unsupported.

[Current guide](LINGUAGEM.md) · [Review](RELATORIO-REVISAO-ALPHA14.md) ·
[Closures and Move variants](CAPTURAS-E-VARIANTES-MOVE.md)

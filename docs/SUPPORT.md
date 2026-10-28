# Support, compatibility and contributions

## Current scope

AssisScript 3.3.0-alpha.15 is an experimental Windows x64 / Linux x86_64 toolchain, with experimental macOS x86_64 output. It has no production SLA, guaranteed response time or promise of binary/source compatibility between alphas. The repository's issues are the public channel for defects and proposals. Security-sensitive reports should omit exploit secrets and personal information; do not publish credentials in test cases.

Supported validation covers the versioned compiler, runtime, standard library, editor and examples shipped together. Mixing versions is unsupported. Recompile all modules after an ABI/runtime change; package lockfiles bind inputs to a compiler version.

## Updates and rollback

Keep the previous complete release and your project sources/lockfile before upgrading. Install the new release into a separate prefix for evaluation (`--prefix` and `--no-path`; on Windows also `--no-associations`). Run `assis version`, the project checks/tests and native acceptance programs. Change your PATH or editor selection only after these pass. To roll back, select the previous compiler/stdlib and restore its matching project lockfile; do not downgrade only the executable.

Removal must preserve files outside the installer's recorded distribution. Files you created yourself are not project-owned installation files. The installer tests exercise minimal, selected and complete installations and preservation of extra files.

## Compatibility policy

- Canonical public APIs are English. Localized documentation is welcome.
- Historical syntax aliases were removed in alpha.14; all code uses the canonical English spellings. --legacy changes safety compatibility, not the accepted keyword vocabulary. Standard library renames and the CSV input header change are listed in [ENGLISH-API.md](ENGLISH-API.md).
- A change to ownership, layout, effects, numeric behavior, resource cleanup or external IO requires an explicit contract update and relevant tests.
- Benchmarks include checked outputs and raw samples. A short run does not count as 24-hour acceptance or independent user testing.
- Unsupported features are rejected or documented as absent. Experimental status must remain visible in redistributed packages and downstream descriptions.

## Contributions and rights

Contributors retain the rights they actually hold and submit original project contributions under its CC BY-NC-SA 4.0 terms. Identify third-party material and its notices before inclusion; the project license does not override upstream licenses. Independent AssisScript libraries are permitted. Forks should credit the upstream project, describe modifications and identify themselves as unofficial.

The human owner has selected a project license. Image provenance and the final redistribution review still need confirmation; actual link inventories for Windows/Linux are recorded separately, and [PROCEDENCIA.md](PROCEDENCIA.md) tracks these open items. This document does not claim those rights are resolved.

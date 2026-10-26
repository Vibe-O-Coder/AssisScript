# Third-party notices

The project's selected CC BY-NC-SA 4.0 license applies to its original licensed material and does not replace third-party terms.

- The Windows compiler/installer are built with MSYS2 MinGW-w64 GCC, using static compiler support libraries. The supplied notices include the [GCC Runtime Library Exception](docs/third-party/GCC-RUNTIME-EXCEPTION.txt), [GPL v3 text](docs/third-party/GPL-3.0.txt) and the [MinGW-w64 runtime notices](docs/third-party/MinGW-w64-NOTICES.txt), copied from the build toolchain.
- GCC/binutils, Node, Python, Pillow, VS Code and CI actions are development tools/integrations, rather than AssisScript-owned components. Their own licenses continue to apply. No copy of these tools is included merely by naming them here.
- Generated native programs use the project's assembly runtime and the target OS APIs. Compiler binaries built statically also contain toolchain/runtime support; dependency review must cover each actual distributed binary.
- The project images were supplied with the working tree. Their original authorship and permission have not been independently verified. No third-party image rights are asserted by these notices.

See the [provenance inventory](docs/PROCEDENCIA.md) for the remaining audit. The included notices are evidence of reviewed toolchain files, not a claim that every possible redistribution obligation has been closed.

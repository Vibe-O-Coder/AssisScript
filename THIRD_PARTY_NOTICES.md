# Third-party notices — v1 identity / native ARM64 candidate

The selected [CC BY-NC-SA 4.0 license](LICENSE) applies to the project's own
material. Third-party components retain their own terms, including permissions
to modify, debug and replace those components; the project license does not
restrict rights granted under the LGPL, GCC Runtime Library Exception or the
MinGW runtime notices.

- The active source/compiled icons are the original geometric SVGs
  `assets/propostas/source-v1.svg` and `compiled-v1.svg`, selected by the owner
  on 2026-10-29. PNG/ICO/ICNS, editor copies and embedded resources are generated
  from them. The retired stickers and their original images are excluded from
  new packages. No external images, fonts, character drawings or icon-library
  assets are incorporated. The project does not claim exclusive rights over
  generic programming symbols. See [the v1 provenance record](assets/IDENTIDADE-V1.json).
- Windows compiler/installer builds use unmodified MSYS2 MinGW-w64 GCC.
  Actual archive/startup inputs and members are recorded in
  `docs/build-audit-windows.json`. Distributed texts include the
  [GCC Runtime Library Exception 3.1](docs/third-party/GCC-RUNTIME-EXCEPTION.txt),
  [GPL v3](docs/third-party/GPL-3.0.txt) and
  [MinGW-w64 notices](docs/third-party/MinGW-w64-NOTICES.txt).
- Current Linux compiler releases use shared system glibc rather than bundling
  the static glibc implementation. Startup/support inputs and shared imports
  are recorded in `docs/build-audit-linux.json`. The
  [LGPL 2.1 text](docs/third-party/LGPL-2.1.txt) is included. Users may replace
  compatible system libraries and reverse engineer the combined work to debug
  their modifications to LGPL components. Historical static builds are not
  included in current packages.
- macOS compiler/runtime dependencies are provided by libSystem on the target
  operating system. No Apple library binary is redistributed in the package.
- Generated programs include only the project's x64 assembly or ARM64 C runtime
  and their own application code, plus declared system/extern dependencies.
  The ARM64 blobs are built freestanding with no compiler-support library and
  no unresolved external symbols; macOS import stubs bind public OS functions.
- Optional networking uses separately installed libcurl and its TLS/resolver
  providers. No libcurl, OpenSSL, WinHTTP or external provider binary is shipped.
  Whoever bundles such providers must follow their terms for that new bundle.
- The optional Windows window provider is original project C code built with
  MinGW-w64 GCC and the notices above. It imports system User32/GDI/UCRT;
  no Microsoft library binary or font is redistributed. DEFAULT_GUI_FONT
  remains a system resource. Provider source/build inventory and tested OS
  are recorded in docs/relatorios/2026-10-29-m1-plataforma-windows.md.
- GCC, binutils, LLVM, Python, Pillow, CairoSVG, Node, VS Code and CI actions are
  maintenance tools/integrations. Their implementations are not copied into
  the distribution by naming or invoking them. The extension/LSP have no bundled
  npm dependency tree. The complete original project/runtime/icon sources and
  rebuild commands are included in the source package.

Review and primary license/source references: [PROCEDENCIA-V1.md](docs/PROCEDENCIA-V1.md).

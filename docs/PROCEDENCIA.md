# Inventário inicial de procedência — 24/10/2026

**Atualização alpha.10, 25/10/2026:** o responsável forneceu `docs/LICENSE` e escolheu CC BY-NC-SA 4.0. O mesmo texto, sem alterações, agora está na raiz em [LICENSE](../LICENSE). Os READMEs declaram uso não comercial, crédito, criação de bibliotecas e forks, distinguindo código independente de material incorporado. A política de suporte/compatibilidade está em [SUPPORT.md](SUPPORT.md). Foram incluídos [avisos de terceiros](../THIRD_PARTY_NOTICES.md) e textos da toolchain Windows. Permanecem abertas a confirmação de direitos das imagens e a auditoria completa dos componentes ligados nos dois destinos; P6-POLICY recebe somente crédito parcial. A tabela seguinte preserva as observações históricas e deve ser lida com esta atualização.

## Inventário atual da alpha.10

| Componente atual | Evidência | Limite da revisão |
| --- | --- | --- |
| Compilador e emissores C11 | src/assisc.c, frontend/lexer, HIR/ranges e backends PE/ELF | Fonte e comandos de reconstrução distribuídos; licença original escolhida pelo responsável |
| Runtime nativo | Assembly, includes e blobs regeneráveis com LF determinístico | Sem libc nos programas gerados; dependências do próprio compilador são distintas |
| Stdlib | 16 módulos e catálogo inglês da alpha.10 | Código fonte distribuído; aliases culturais legados explicitamente separados na migração |
| Editor/LSP | JavaScript e reference.json, sem dependências npm obrigatórias | Node é requisito do editor/LSP/testes, não dos executáveis gerados |
| Build Windows | GCC MSYS2 15.2.0 local, -static/-static-libgcc | Avisos da toolchain incluídos; a CI pode usar uma versão mais nova e precisa de revisão própria |
| Build Linux | GCC/ambiente registrados nos logs e relatórios desta entrega, -static | Auditoria completa dos componentes estaticamente ligados ainda pendente |
| Imagens | assets e gerador de ícones existente | Direitos/autoria ainda não confirmados independentemente |
| Distribuição | LICENSE, avisos, READMEs e checksums em ZIP/VSIX/instaladores | Política publicada; não equivale a uma certificação jurídica ou de produção |

## Inventário histórico da base

| Componente | Evidência local | Situação a resolver |
| --- | --- | --- |
| Compilador e emissores C | src/assisc.c, headers de tipos/coleções/ownership, PE/ELF | Autoria e licença do projeto não declaradas nos arquivos inspecionados |
| Runtimes assembly e blobs | runtime.S/runtime_win.S, includes e ferramentas embed-runtime | Blobs derivados dos fontes; registrar revisão e hashes em cada entrega |
| Bibliotecas AssisScript | Oito módulos e stdlib/catalogo.json | Licença/autoria seguem pendentes; não há dependência baixada por esses módulos |
| Extensão VS Code | package.json: publisher assisscript-local; fontes JS | Identificador de publisher não comprova titularidade nem licença |
| Ícones e imagens | assets e tools/build-icons.py descrevem duas imagens fornecidas | Origem, autor, permissão e termos das imagens precisam ser confirmados pelo responsável |
| GCC/MinGW e bibliotecas ligadas | GCC 15.2.0 MSYS2 local; builds usam -static/-static-libgcc | Registrar versão e conferir obrigações de redistribuição/exceções das bibliotecas efetivamente ligadas |
| Ferramentas de desenvolvimento | Node para testes/editor; Python/binutils para geração/pacotes; Pillow para ícones | Não são exigidos para executar programas gerados; inventário de versões/licenças das ferramentas continua separado |
| Integrações Windows/Linux | APIs Win32 e syscalls descritos nos fontes | Não equivale a copiar implementação dessas plataformas; dependências futuras requerem nova revisão |

A base 3.2 foi preservada localmente em `build/baseline-2026-10-24` antes das alterações, com hashes SHA-256 de src/stdlib/bin em `hashes.json`. Essa pasta é uma cópia de trabalho, excluída da distribuição, não um histórico Git. Os hashes publicados em SHA256SUMS pertencem ao pacote da versão correspondente.

O inventário não certifica ausência de componentes de terceiros, direitos das imagens ou conclusão de revisão de licenças. A escolha final permanece com o responsável pelo projeto.

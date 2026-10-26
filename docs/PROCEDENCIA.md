# Inventário inicial de procedência — 24/10/2026

Este é um inventário técnico dos arquivos encontrados, sem atribuir uma licença ao projeto. Nenhum LICENSE/COPYING foi localizado na raiz ou nos fontes distribuídos. O responsável precisa definir direitos e licenças antes de uma oferta comercial. Esta entrega não decide isso.

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

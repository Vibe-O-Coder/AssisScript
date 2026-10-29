# Procedência atual

A revisão de 29/10/2026 está em [PROCEDENCIA-V1.md](PROCEDENCIA-V1.md). Ela aplica os ícones v1 escolhidos, retira stickers da distribuição e fecha a revisão dos componentes desta entrega. As pendências descritas abaixo pertencem aos registros históricos.

## Registro histórico

# Inventário inicial de procedência — 24/10/2026

**Informação do responsável, 28/10/2026:** as duas imagens originais são stickers
comuns na comunidade, sem autor original identificado. Não foi apresentada uma
licença ou autorização de distribuição. Há uma [proposta de substituição por
ícones geométricos](IDENTIDADE-VISUAL-PROPOSTA.md), com SVGs escritos nesta
continuação e sem usar os stickers como material de entrada. A proposta ainda
não substituiu os ícones ativos ou os binários; P6-POLICY permanece parcial.

**Atualização alpha.13:** os inventários vinculados abaixo correspondem à
reconstrução da alpha.13. A matriz inclui closures e variantes Move e foi
executada localmente em Windows/Linux; CI remota desta revisão não foi executada
nesta sessão. Resultados anteriores citados abaixo permanecem históricos.


**Atualização alpha.12 — inventário técnico por ligação real.**
Os relatórios [Windows](build-audit-windows.json) e [Linux](build-audit-linux.json)
são gerados por `tools/audit-build.py`, a partir de uma reconstrução temporária
com mapa do GNU ld e referência cruzada. O script exige bytes idênticos aos
compiladores/instalador distribuídos. Registra cada entrada LOAD, os membros
usados dos archives, objetos de startup, hashes dos archives/objetos e do objeto
do próprio projeto, flags, target/versão/hash do GCC e imports dinâmicos.
A entrada sintética “dll stuff” é identificada como tabela PE gerada pelo ld.
Entradas de arquivo não resolvidas e grupos técnicos desconhecidos são erro.

A matriz Windows/Linux continua declarada em `.github/workflows/ci.yml`;
a alpha.12 acrescenta segurança padrão, net e auditoria de ligação, com upload
dos relatórios de cada build para o job de pacote. A evidência de execução
deste código nesta sessão é local; não há CI remota alpha.12 registrada.

Componentes efetivos: runtime MinGW-w64/bibliotecas de importação e suporte
GCC no Windows; startup, glibc e suporte GCC no Linux estático. Os membros e
versões/pacotes exatos constam nos relatórios, incluindo entradas carregadas
sem membros selecionados. [LGPL 2.1](third-party/LGPL-2.1.txt) foi copiada do
ambiente Linux, além dos avisos GCC/MinGW já distribuídos. O objeto do projeto
é derivado dos fontes incluídos e pode ser reconstruído pela ferramenta.
Este inventário técnico não decide obrigações jurídicas de redistribuição:
procedência de imagens e revisão dos termos/fontes correspondentes continuam
em P6-POLICY, sem crédito adicional por este inventário.

O novo módulo opcional net usa `libcurl.so.4` / `libcurl-4.dll` com DNS
assíncrono/TLS. Não redistribui o provedor nem seus DLLs dependentes. A ABI,
layout x64 e configuração usados estão no contrato de net. Os runtimes dos
programas gerados permanecem derivados dos fontes assembly/blobs incluídos;
somente módulos que usam extern adquirem as dependências declaradas.

`python tools/audit-build.py --check --output docs/build-audit-<sistema>.json`
confere a correspondência com os fontes e binários presentes. Para outra
versão de toolchain, gere novo inventário; não reutilize hashes desta entrega.
As seções seguintes preservam a análise histórica.

**Atualização alpha.11:** módulos http/process usam dependências opcionais do sistema: Windows KERNEL32/WinHTTP; Linux loader glibc, libc e libcurl.so.4. Não se redistribui libcurl/WinHTTP/glibc no pacote. Programas sem extern/callback continuam freestanding; a afirmação histórica abaixo de ausência de libc não se aplica às integrações novas. Licenças e distribuição das dependências do ambiente precisam ser consideradas separadamente.

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

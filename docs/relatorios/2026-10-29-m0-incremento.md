# M0 parcial — reconciliação de incremento e decremento

Data: **29/10/2026**. Critérios: **E00-05**, com nova evidência parcial de
**E01-02/E01-05**. Marco **M0 ainda aberto**; nenhum gate é atendido por esta
unidade. Não há release de pacote nem certificação de produto.

## Problema, base e responsabilidade

O primeiro item da fila do plano mestre é reconciliar as continuações locais
antes de construir novas capacidades. A branch de planejamento contém somente
a documentação; `++`/`--`, microparser e mutação de OwnedArray estavam no
diretório de trabalho, sem publicação dessa continuação.

Base: `1ed22f5c898f21f06c429774992469177bdfd3d9`, branch
`docs/ecossistema-web-2026-10-29`, já confirmada no remoto. Branch desta unidade:
`work/m0-increment-2026-10-29`, destinada a PR sobre a branch de planejamento.
O remoto é `https://github.com/Vibe-O-Coder/AssisScript.git`.

Foi criada uma worktree local em `AssisScript/.worktrees/m0-increment`.
Somente `src/frontend.h`, `src/lexer.h` e `tests/test-increment.py` da
continuação foram copiados para a base limpa e assumidos nesta reconciliação
após revisão e novos testes. Os dois arquivos do compilador conservam
exatamente o conteúdo local auditado. A suíte recebeu dois testes adicionais:
modelo numérico independente e valores IEEE especiais. A documentação e a
integração de testes foram reaplicadas sobre a base limpa por escopo.

As demais modificações preexistentes no diretório original foram preservadas:
OwnedArray, microparser, seus relatórios, catálogos, READMEs e alterações mistas
não entram nesta unidade. Nenhum reset, limpeza ou force push foi usado.
Os rascunhos locais do HTDL estão disponíveis; o documento 14 foi consultado
como proposta de perfis, sem atribuir conformidade HTDL a este compilador.

## Antes e depois

Uma reconstrução da base com GCC reproduziu três observações diretas:

| Fonte | Base | Candidato |
| --- | --- | --- |
| `let n:int=1;n++;` | `check` retorna 1 | `check` retorna 0 |
| `let n:int=1;print(++n);` | `check` retorna 0: dois sinais unários | `check` retorna 1: instrução sem valor |
| `let n:int=1;print(+ +n,- -n);` | `check` retorna 0 | `check` retorna 0 |

A suíte local original de oito métodos também foi executada contra a base:
13 falhas, zero erros, sem tratar o comportamento antigo como recurso ausente
por mera inspeção. Os três probes, incluindo fontes, códigos e diagnósticos,
ficam no JSON suplementar Linux. O binário base foi reconstruído nesta sessão.

`n++`, `++n`, `n--` e `--n` agora são instruções sem valor, inclusive na
inicialização e no passo do `for`. A mudança local existente é reconciliada;
esta sessão não acrescenta nova sintaxe além daquela continuação. A análise
baixa para atribuição composta com uma constante do tipo do destino, conserva
as verificações de escrita/efeitos/empréstimos e usa a IR existente. O destino
é avaliado uma vez. Inteiros conservam overflow modular e reais conservam IEEE.
`val`, `const`, empréstimos compartilhados, booleanos, ponteiros e expressões
que tentam usar um valor de incremento são rejeitados com diagnóstico `A001`.

O contrato de migração explica a tokenização indivisível e a separação dos
sinais unários. O editor já realça sequências de operadores; sua referência
do `for` foi atualizada. Nenhum provider novo, shim, ABI, opcode, versão de
release ou biblioteca proprietária é introduzido.

## Arquivos e decisões

- Compilador: `src/lexer.h`, `src/frontend.h`.
- Contratos: `docs/GRAMATICA.ebnf`, `docs/LINGUAGEM.md`,
  `docs/INCREMENTO-E-DECREMENTO.md`; exemplo `exemplos/33_increment.assis`.
- Testes: `tests/test-increment.py`, `tools/validate-increment.py`,
  `tools/test-native.py`, `Makefile`, `.github/workflows/ci.yml`.
- Editor: `vscode-assisscript/src/reference.json`.
- Régua: JSON/Markdown em `docs/ecossistema`, gerador
  `tools/report-ecosystem-progress.py` e evidências desta unidade.
- Instalador: `src/install_files.inc`, regenerado pelo inventário real dos
  documentos/exemplos/JSONs. Inclui os documentos de planejamento que a base
  ainda não tinha sincronizado. Não recompila nem promove o instalador.

O gerador da régua aceita uma nota de avaliação específica, preservando o texto
anterior quando ausente. Isso evita manter a frase de que nenhum teste foi
reexecutado depois de uma sessão com execução nativa real. Os créditos sem
nova evidência permanecem provisórios.

## Comandos e resultados desta revisão de fontes

Build Linux x64/WSL2, GCC 13, a partir da base e depois dos dois arquivos
reconciliados:

```sh
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation src/assisc.c -s -o build/assis-increment-linux
ASSIS_BIN="$PWD/build/assis-increment-linux" python3 tools/validate-increment.py --output docs/ecossistema/evidencias/m0-incremento-2026-10-29/linux-x64.json
```

Build Windows x64, GCC MSYS2 15.2.0, executado em PowerShell com o diretório
`C:/msys64/ucrt64/bin` no PATH:

```powershell
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation -municode -static -static-libgcc -s '-Wl,--no-insert-timestamp' src/assisc.c -o build/assis-increment.exe
$env:ASSIS_BIN=(Resolve-Path build/assis-increment.exe).Path
python tools/validate-increment.py --output docs/ecossistema/evidencias/m0-incremento-2026-10-29/windows-x64.json
```

Os candidatos foram inicialmente gravados em `build/m0-increment` e copiados,
com os mesmos bytes, para `build/`: o compilador encontra `../stdlib` a partir
do seu diretório. A primeira tentativa de regressões Linux encontrou duas
falhas de localização de módulos; elas não foram contadas como aprovação.
No Windows, duas tentativas sob a restrição de arquivos temporários não
chegaram aos testes semânticos. A execução final com acesso aos temporários
do usuário passou. Não houve mudança de linguagem para mascarar essas falhas
de ambiente. Os JSONs e logs publicados registram a execução final completa.

| Suíte | Windows x64 | Linux x64/WSL2 |
| --- | ---: | ---: |
| increment | 10/10 | 10/10 |
| evolution | 12/12 | 12/12 |
| numbers | 11/11 | 11/11 |
| ownership-functions | 26/26 | 26/26 |
| optimization | 6/6 | 6/6 |
| backend-evolution | 16/16 | 16/16 |
| complete-ir | 7/7 | 7/7 |
| **Total de métodos** | **88/88** | **88/88** |

As suítes aplicam otimizado/referência, rejeições antes da execução, efeitos,
ownership, drops, ordem de avaliação, IR e números. A nova sequência usa seed
`20261029`, oito tipos inteiros e 32 passos por tipo, com resultado calculado
em Python por largura/sinal, sem reutilizar o compilador como oráculo.
Casos de NaN, infinito e arredondamento f32 são explícitos. O teste de IR exige
`astFallbacks == 0` para o programa de incremento.

Validações suplementares:

- `node --test --test-isolation=none vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js`:
  **29/29**, nenhum skip; log `editor-windows.log`.
- `<candidato> run exemplos/33_increment.assis --debug`, também com
  `--no-opt`: **retorno 0**, saída exata `3 255\n`, nos dois sistemas. O exemplo
  verifica inicialização do `for` com incremento e que `break` pula o passo.
- `<candidato> build exemplos/33_increment.assis --target <destino> -o <arquivo>`,
  também com `--no-opt`: cinco destinos por host, **10 gerações por host**.
  Assinatura e arquitetura PE/ELF/Mach-O foram conferidas por leitura independente
  dos headers; tamanhos e SHA-256 ficam nos JSONs suplementares.
- `python tools/report-ecosystem-progress.py` e o mesmo com `--check`:
  consistência dos 60 critérios, cinco gates, histórico e Markdown gerado.
- `python tools/generate-install-manifest.py` e o mesmo com `--check`:
  manifesto sincronizado com os arquivos desta branch.
- `git diff --check`: sem erros de whitespace.

Os últimos três controles são documentais; não substituem os testes nativos.
Não foram reexecutadas todas as suítes do repositório, rede/TLS, soak,
instalação ou validação de release. A suíte de incremento foi integrada aos
comandos existentes de CI, sem alegar aprovação remota da CI.

## Evidências, hashes e limites

Diretório rastreado: `docs/ecossistema/evidencias/m0-incremento-2026-10-29/`.
Os JSONs principais contêm plataforma/Python, base Git, hashes dos arquivos
afetados e de cada suíte/log; os logs correspondentes estão ao lado.

| Candidato | SHA-256 |
| --- | --- |
| Windows x64 | `da249e894a274f8d8f2fd72b98744a6fe39a190b60a44b7fc8648a0321a75244` |
| Linux x64 | `8cb653df1dfc063e4e2645cd70e8e3922b58c78141d3d6c7ce3011499b2b81ec` |

Esses hashes são dos builds desta sessão, não de binários/releases anteriores.
A revisão exata das fontes é recuperável no commit que contém este relatório;
os arquivos do compilador têm hashes próprios nos dois JSONs. Os binários de
teste permanecem em `build/`, sem substituir os pacotes versionados.

Execução nativa: **Windows x64 e Linux x64/WSL2**. Execução macOS x64,
Linux ARM64 e macOS ARM64: **not-run**. Geração de seus formatos foi testada,
sem conferir suporte nativo final. Integração HTDL/FS/SSC, Browser, buscador,
sandbox, conteúdo remoto e SDK de página: **not-run**. `safe` não recebe
qualquer nova garantia de isolamento por este trabalho.

## Pontos, publicação e próxima tarefa

Antes: **19,90/100**, **0/5 gates**. Depois: **20,10/100**, **0/5 gates**.
Somente **E00-05 sobe de 1 para 2** pelo exercício reproduzível de inventário,
relatório e publicação desta unidade; sua aceitação integral permanece aberta.
E01-02 e E01-05 recebem nova evidência sem aumento de nível. O histórico inicial
e os 100/100 das antigas fases 0–6 são preservados, e um novo retrato completo
dos 60 níveis/cinco gates registra esta atualização.

Publicação normal autorizada pelo masterprompt: commit e push da branch
`work/m0-increment-2026-10-29`, seguidos de conferência do SHA remoto e criação
de PR para a branch de planejamento. O SHA final não é inserido no próprio
arquivo, evitando hash autorreferente. Consulte
`git log --follow -- docs/relatorios/2026-10-29-m0-incremento.md` ou o histórico
do relatório no GitHub. A resposta da sessão fornece o SHA/PR e o resultado
efetivamente verificado da publicação; push não significa merge, release ou
aprovação de CI.

Próximo incremento recomendado: reconciliar **microparser/prova HTDL e
OwnedArray em unidades próprias**, com fontes isoladas e testes novos do
candidato, sem promover o microparser a parser HTDL. Depois, congelar perfil
mínimo do visualizador, ABI do shim e estratégia de runtime de página. M0
continua aberto até completar as demais obrigações de baseline e contratos.

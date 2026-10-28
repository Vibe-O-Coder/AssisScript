# Versão experimental para testes no GitHub

Preparada em 28/10/2026. Compilador: **3.3.0-alpha.15**. Os registros alpha.16
são uma continuação da auditoria/documentação; não representam uma nova versão
do compilador.

Esta branch facilita testes e relatos em outros computadores. O projeto segue
experimental, com [94/100 pontos do plano](PROGRESSO.md). Suporte ARM64,
validação macOS, emissão integral por IR, revisão de distribuição e aceite
independente continuam descritos no [restante do plano](RESTANTE-PARA-100.md).
Os stickers atuais têm procedência em revisão; a [identidade proposta](IDENTIDADE-VISUAL-PROPOSTA.md)+ainda aguarda escolha. A publicação para testes não encerra essas pendências.

## Obter a mesma revisão

Use a [branch testing/alpha15](https://github.com/Vibe-O-Coder/AssisScript/tree/testing/alpha15)
ou [baixe seu ZIP](https://github.com/Vibe-O-Coder/AssisScript/archive/refs/heads/testing/alpha15.zip).
Esse ZIP contém a árvore do repositório, e não um release estável certificado.
Com Git:

```sh
git clone --branch testing/alpha15 https://github.com/Vibe-O-Coder/AssisScript.git
cd AssisScript
git rev-parse HEAD
```

Guarde o identificador exibido e a saída de `version`. Quem usar o ZIP deve
guardar o arquivo baixado e o identificador de commit mostrado na página da
branch. A branch pode receber correções; compare sempre a mesma revisão.

## Windows x64

No PowerShell, dentro da pasta extraída ou clonada:

```powershell
.\bin\assis.exe version
.\bin\assis.exe check exemplos/31_language_review.assis
.\bin\assis.exe run exemplos/31_language_review.assis --debug
.\bin\assis.exe run exemplos/32_backend_evolution.assis --debug
```

O exemplo 31 imprime `Turno de Assis (Clérigo) - HP 54/54` e `Decimal: 0.30`.
O exemplo 32 imprime `18`. Para testar instalação, veja [INSTALACAO.md](INSTALACAO.md)
e use `instalar-windows.cmd` da mesma pasta. Também é possível testar os binários
diretamente antes de alterar a instalação existente.

## Linux x86_64

No terminal, dentro da pasta extraída ou clonada:

```sh
chmod +x bin/assis
./bin/assis version
./bin/assis check exemplos/31_language_review.assis
./bin/assis run exemplos/31_language_review.assis --debug
./bin/assis run exemplos/32_backend_evolution.assis --debug
```

As saídas esperadas são as mesmas do Windows. Para testar instalação, siga o
manual e use `sh instalar.sh` da mesma pasta. O binário incluído é x86_64;
uma máquina ARM64 não é um alvo nativo suportado por essa distribuição.

## Testes automáticos e programas próprios

Com Python instalado, `python tests/test-backend-evolution.py` no Windows ou
`python3 tests/test-backend-evolution.py` no Linux executa o teste de backend.
Para programas próprios, use `check`, `run --debug` e `build`, guardando também
os erros encontrados. Os [contratos da linguagem](LINGUAGEM.md) descrevem as APIs
atuais; programas da alpha.6 podem precisar de migração.

Os [resultados do GitHub Actions](https://github.com/Vibe-O-Coder/AssisScript/actions)
devem ser consultados para o commit testado. Publicação da branch e início de um
workflow não equivalem a aprovação dos jobs. Relatórios anteriores permanecem
identificados pelas versões e hashes aos quais pertencem.

Na preparação desta branch, os 10 testes de backend, 2 de documentação/avisos
de distribuição e 41 testes de desenvolvimento/editor/LSP passaram no Windows.
O compilador Windows reconstruído manteve os mesmos bytes da alpha.15 validada;
o instalador foi reconstruído para incluir os quatro documentos acrescentados
desde o manifesto anterior. Os relatórios completos da alpha.15 são históricos
daquela entrega; o manifesto de instalação mudou desde os hashes ali registrados.
Os jobs de CI regeneram os inventários e a validação dos pacotes que produzirem.

O arquivo `assisscript-3.3.0-alpha.10.vsix` já existente na raiz pertence à versão
antiga e foi preservado. Use os binários desta branch ou os artefatos de CI do
mesmo commit para testar a alpha.15; mantenha compilador, stdlib e editor da
mesma versão. `SHA256SUMS` pertence ao pacote preparado pela ferramenta de
distribuição, não é uma lista de verificação do ZIP de fontes do GitHub.

## Informar resultados

Abra uma [issue](https://github.com/Vibe-O-Coder/AssisScript/issues) e informe:

- Sistema e versão, arquitetura e revisão/commit baixado.
- Saída de `assis version` e forma de obtenção/instalação.
- Programa pequeno que reproduza o teste e comando usado.
- Resultado esperado, resultado observado e mensagem completa de erro.
- Se compilou, executou, depurou e/ou testou o instalador.

Compartilhe apenas exemplos sem dados pessoais, credenciais ou arquivos
privados. Para o aceite completo, uma pessoa distinta ainda deve seguir o manual
e testar arquivos/CSV (A), cliente de rede (B) e serviço persistente (C), incluindo
depuração e distribuição. O [relato histórico do responsável](ACEITE-RELATO-USUARIO-2026-10-28.md)
já registra os testes de programas próprios aproximadamente na alpha.6.

# CI nativa do Windows e do Linux ARM64

13/11/2026, America/Fortaleza. Branch `work/ecosystem-2026-11-12`.
A correção parte de `26fcae9a786ffbd854446a7b79aa9a5a026a6d46`.
E00-04 e E11-02 recebem diagnóstico e evidência. A régua local segue em
**58,50% e 0/5 gates**.

## Diagnóstico

A execução de `48a18b7` passou em Linux x64, macOS x64 e macOS ARM64.
O job Windows falhou ao iniciar o GCC do teste nativo de catálogo.
O teste usava um caminho fixo de instalação do MSYS2. A CI já fornece
`CC` para construir o provider. O oráculo agora usa o mesmo compilador
que produziu a DLL sob teste.
[Execução da busca](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/43404887548).

No Linux ARM64, a portabilidade e a validação de símbolos e debugger
passaram antes da suíte semântica. O relatório da suíte listou nove
falhas. Quatro testes de formatos selecionavam o executável Linux x64
para rodar em ARM64. Os outros cinco grupos exigiam o provider de
workers do perfil x64 na preparação. A matriz da revisão anterior
já falhava nas mesmas etapas Windows e Linux ARM64.
[Artefato da matriz](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/43404887548/artifacts/14026408478) ·
[Execução anterior](https://github.com/Vibe-O-Coder/AssisScript/actions/runs/43195828212).

## Correção e evidência

A suíte escolhe o executável pelo sistema e pela arquitetura. Os
casos dependentes de workers registram explicitamente a ausência
do provider fora do Windows/Linux x64. Os testes de geração de
formatos do Frame e de recursos continuam rodando em ARM64, junto
aos testes de lotes e do núcleo do visualizador. O relatório registra
as contagens de casos pulados e o GitHub Actions preserva os logs
individuais do Linux ARM64.

O Windows x64 executou 104 casos nas oito suítes de regressão
focadas, incluindo os 21 casos do catálogo com o GCC indicado por
`CC`. Uma primeira passagem do visualizador encontrou um bloqueio
na remoção do executável temporário após o teste. A repetição com
diretório temporário dedicado passou nos 12 casos. No Ubuntu x64,
as seis suítes focadas passaram com 72 execuções e sete casos
pulados por dependência do Windows. A matriz completa do Ubuntu
reuniu 61 suítes, 573 execuções e 28 casos pulados. [Contagens e
hashes](../ecossistema/evidencias/ci-windows-arm64-2026-11-13/summary.json).

No Ubuntu, `aarch64-linux-gnu-gcc -O2 -std=c11 -static src/assisc.c`
produziu o compilador ARM64 com SHA-256
`4b935f529f21ea0b2d03a44688611885a27940ad36e3cf078efc4906a24321ee`.
O QEMU executou o compilador e as saídas ELF ARM64. O teste rejeitou
a execução de binários ELF x64 a partir do processo de testes.
Foram 12 execuções e 64 casos sem provider nos nove grupos
selecionados. A reexecução em runner ARM64 depende do envio da revisão.

## Revalidação de interface

As suítes adicionais de Frame e leitura passaram com 27 execuções
no Windows e 24 no Ubuntu x64, com três casos do provider Windows
pulados no Ubuntu. No desktop, Tab alcançou Validar no formulário.
A janela SSC abriu e Tab percorreu os dois painéis. Enter e Espaço
foram enviados aos botões correspondentes. A captura voltou a expirar
e a fluidez observada no desktop continua pendente. A tecla `uacute`
foi recusada pela automação. A verificação do acento consta no teste
nativo UTF-16 e nos rasters, com o aceite de IME em aberto.

A revisão local da CI está pronta para reexecução no GitHub. O próximo
incremento M3 inclui IME e imagens. [Fila integral](../ecossistema/FILA-M0-M1.md).

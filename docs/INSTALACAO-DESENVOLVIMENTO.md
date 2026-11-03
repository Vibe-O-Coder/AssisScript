# Instalação Windows desta continuação

Esta continuação usa recursos posteriores ao binário histórico conservado em
bin/assis.exe. Instalar fontes atuais junto com esse executável pode produzir
erros como `esperado ;; encontrado ArrayNode` em try_new, ou não localizar
bibliotecas novas. Não acrescente pontos e vírgulas nem retire std/ dos imports
para tentar corrigir essa mistura. -I seleciona arquivos, não atualiza o compilador.

O pacote completo de desenvolvimento fica em
build/AssisScript-development-20261102-windows-x64.zip, com a pasta preparada
em build/development-windows-20261102. Ele contém compilador recém-construído,
catálogo/bibliotecas correspondentes, instalador novo e assis_platform_v1.dll.
BUILD-INFO.json identifica os hashes e o resultado da instalação isolada.
É um pacote de desenvolvimento Windows x64, sem promover uma release estável.

Extraia a pasta inteira e execute o instalar-windows.cmd **desse pacote**.
Não copie somente assis-setup.exe para outra pasta. A instalação padrão atualiza
%LOCALAPPDATA%/AssisScript. Feche programas AssisScript antes de substituir
arquivos em uso. Um terminal novo evita continuar usando outro PATH.
`where assis` deve apontar para essa instalação.

Para experimentar sem instalar, dentro da pasta extraída:

```powershell
.\bin\assis.exe build .\exemplos\57_page_frame_window.assis --safe -o .\bin\paineis.exe
.\bin\paineis.exe
```

Deixe a DLL junto a paineis.exe. --once publica um quadro e fecha. Sem argumento,
Tab/Enter/Space, ponteiro e redimensionamento demonstram a geometria compartilhada.
O uso portátil não altera PATH, associações ou sua instalação anterior.

Para responsáveis pelo build, tools/prepare-development-installer.py reconstrói
e compara o compilador com a matriz nativa rastreada, monta o pacote e valida
instalação/execução/remoção em prefixo temporário. --prepare-only registra
installation_validation=not-run; esse resultado não substitui a validação padrão.
O wrapper na cópia Git recusa instalar o binário histórico diretamente.

Detalhes e limites: [relatório](relatorios/2026-11-02-m5-page-frame.md),
[pageframe](BIBLIOTECA-pageframe.md), [pagepresent](BIBLIOTECA-pagepresent.md).

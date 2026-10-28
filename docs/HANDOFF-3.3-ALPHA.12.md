# Continuação — 3.3.0-alpha.12

Data: 26/10/2026. Base: árvore alpha.11 recebida com alterações ainda sem
commit sobre `257e719`. Preservadas integralmente; não houve reset nem commit
automático. Binários recebidos e hashes em `build/alpha11-baseline`.

## Entrega

- Perfil safe na entrada por padrão, `--legacy` explícito, opções conflitantes
  rejeitadas, projeto novo seguro e configuração de compatibilidade no editor/LSP.
  [Contrato e migração](SAFE-DEFAULT.md). text externo continua fechado na
  fronteira unsafe; dados externos usam bytes/slices/UTF-8 gerenciados.
- Inicializadores com receptor gerenciado só podem ser chamados por new.
  Reentrada podia substituir buffers ainda retidos por um handle externo.
  Inicialização legada do CSV continua no perfil histórico.
- Novo módulo opcional [net](BIBLIOTECA-net.md): HTTP(S) cooperativo, polling
  de 0–50 ms, cancelamento idempotente, corpo limitado, múltiplas requisições
  intercaladas, destruição de operação pendente e confiança TLS por requisição.
  libcurl com DNS assíncrono é dependência explícita nos dois sistemas;
  `http::Client` conserva o backend anterior. [Aplicação B com cancelamento](../exemplos/29_http_polling.assis).
- Inventário real dos mapas de ligação dos compiladores/instalador, incluindo
  arquivos e membros de archives, hashes, startup, imports e toolchain.
  `tools/audit-build.py` exige identidade com os binários distribuídos.
  [Procedência](PROCEDENCIA.md); a análise técnica não resolve direitos de imagens.
- Catálogo, instaladores, CI, editor, documentação e pacotes sincronizados;
  testes históricos escolhem --legacy explicitamente, e a nova suíte segura
  usa diretamente a interface pública padrão.

## Análise da linguagem

O núcleo já expressa aplicações CLI e serviços delimitados com geração nativa,
generics por especialização, dados Copy/variantes, funções de ordem superior,
ownership, recursos externos e IO recuperável. O modelo de custo continua sem
GC/boxing obrigatório. Os backends Windows/Linux e as aplicações A/B/C têm
regressões executáveis; a validação atual está no documento da alpha.12.

A fronteira segura ficou mais clara, mas a adoção funcional ainda é parcial:
`fn` legado continua com efeitos não verificados; safe exige fronteira explícita
para chamá-lo. Closures/capturas e variantes Move permanecem ausentes. As APIs
legadas de text/coleções não herdam automaticamente contratos de vidas. Não
confundir código com ownership com um ambiente isolado para páginas hostis.

A HIR descreve CFG/efeitos de instruções, mas expressões/emissão ainda usam AST.
ARM64/macOS não têm backend validado. O alocador segue de uma thread; processos
isolados e polling cooperativo não autorizam uso concorrente do heap. São
lacunas reais de arquitetura, preservadas na régua de progresso.

## Progresso

**90% estimados (89,5/100 pontos, arredondamento original)**, anteriormente
85/100. Sem alteração de pesos: P0-SAFE +1,5; P0-CI +1,5 pelo inventário
técnico reproduzível e matriz mantida; P4-NET +1,5. A CI remota deste código
não foi executada nesta sessão: a evidência atual é local Windows/Linux e a
configuração contínua. Não se reutiliza um status remoto de versão anterior.

P2-ADT, P4-SOAK, P5-IR, P5-OPT e P6-POLICY continuam parciais; P5-TARGET e
P6-ACCEPT continuam pendentes. **100% não foi atingido.** Ainda faltam capturas
com vidas/variantes Move, 24 horas efetivamente medidas, backend/otimizações
integrais, novos alvos, direitos de imagens/revisão de distribuição e aceite
humano independente. Nenhum teste curto recebeu crédito de 24 horas.

## Operação e continuação

`make test-alpha12`; Windows `tools/build-windows.ps1` e suítes Python.
`tools/test-native.py` cobre a matriz; `tools/validate-clean.py` reconstrói
ambos os runtimes sem caches e valida o compilador resultante.
`tools/audit-build.py --output docs/build-audit-<sistema>.json` gera inventário;
`--check` confere sua correspondência aos fontes/binários.

Próximo incremento funcional: definir um único contrato para variantes Move
e closures com capturas por valor/move/borrow, integrado a destruição e vidas,
antes de abrir capturas em callbacks externos. Executar 24 horas sobre uma
árvore congelada e obter aceite por uma pessoa distinta. Backend/novos alvos
exigem trabalhos próprios; não encerrar esses critérios por contagem de APIs.

Resultados, hashes e limites: [validação alpha.12](VALIDACAO-3.3-ALPHA.12.md).

# Relatório — plano mestre para Browser, busca e ecossistema web

Data: **29/10/2026**. Unidade de mudança: planejamento e governança da nova trilha.

## Objetivo e resultado

Definir tudo que a plataforma AssisScript precisa demonstrar para implementar o navegador, seu motor HTDL/FluxStyle/SSC, o buscador e os serviços de apoio. A entrega estabelece 12 frentes, 60 critérios, 100 pontos, marcos M0–M9, cinco gates de integração e um masterprompt operacional para as próximas sessões.

Antes, os 100/100 publicados encerravam somente as fases 0–6. A auditoria e a continuação local apontavam necessidades do ecossistema sem uma régua própria. Agora há escopo, dependências, aceitação, sequência de incrementos, limites e cálculo reproduzível separado do histórico anterior. O novo planejamento não implementa nem anuncia capacidades novas do compilador/runtime.

## Base, escopo e arquivos

- Base local: `e9183e7f98447e97feb2f2e7f1953c035e24f7e6`, AssisScript 3.3.0-alpha.15.
- Branch de origem inspecionada: `development/native-arm64-icons-v1`.
- Destino desta unidade: `docs/ecossistema-web-2026-10-29`, em `Vibe-O-Coder/AssisScript`.
- IDs: especificação/registro E00 e suporte de medição E11; planejamento M0. Nenhum gate de execução é promovido.
- Entrada: [PLANO-ECOSSISTEMA.md](../../PLANO-ECOSSISTEMA.md).
- Plano, progresso JSON/Markdown, baseline com hashes, masterprompt e cópia do registro futuro: `docs/ecossistema/`.
- Cálculo/validação: `tools/report-ecosystem-progress.py`.
- Resultado de verificação documental: [VALIDACAO-PLANEJAMENTO.json](../ecossistema/VALIDACAO-PLANEJAMENTO.json).

Criados na pasta irmã Browser: `AssisBrowser/README.md` e `AssisBrowser/docs/IMPLEMENTACOES-FUTURAS.md`. O segundo arquivo está espelhado em [docs/ecossistema/browser/IMPLEMENTACOES-FUTURAS.md](../ecossistema/browser/IMPLEMENTACOES-FUTURAS.md) para publicação no GitHub do AssisScript. A pasta Browser não tinha repositório Git ou documentação anterior encontrados nesta inspeção.

O registro futuro prevê AssisScript Web como versão distinta, parecida com JavaScript e acessível a iniciantes, preservando a identidade da linguagem. Registra também Easy como entrada com sintaxe muito simples, similar a Python, voltada a terminal e interfaces simples, e **última etapa de todo o projeto**. Essas variantes não integram os 60 critérios nem os pesos desta trilha.

## Decisões

1. Preservar o progresso e todas as evidências das fases 0–6. A nova medição tem versão e histórico próprios.
2. Medir capacidade demonstrada da plataforma, incluindo integrações de referência, sem exigir que toda lacuna seja resolvida por nova sintaxe.
3. Exigir compilação/semântica, memória/coleções, sistema/eventos, plataforma gráfica/acessibilidade, rede, executor/isolamento, HTDL/SDK, FS/SSC/layout, persistência, busca e distribuição.
4. Separar níveis de capacidade da aprovação dos gates. `safe`, uma página desenhada ou um teste antigo não certificam isolamento nem distribuição nova.
5. Tornar relatório e publicação de cada unidade lógica partes obrigatórias do masterprompt. GitHub recebe somente os arquivos desta unidade, preservando fontes e evidências locais de outras sessões.

## Pontuação e limites

Antes desta mudança: não havia porcentagem definida para este escopo. Não corresponde a 0% nem a 100%.

Baseline nova: **19,90/100 pontos (19,90%)**, estimativa documental provisória, com **0/5 gates aprovados**. Há crédito parcial para fundações já existentes; nenhum critério recebe nível 4. Esta sessão não concede pontos de implementação por escrever o plano.

Os níveis foram atribuídos conservadoramente a partir de documentação, fontes e resultados históricos identificados. A baseline preserva hashes dos insumos e distingue a continuação local não publicada dos arquivos já rastreados. A nova porcentagem não representa prazo, esforço ou prontidão para produção. A primeira sessão de implementação precisa confirmar ou corrigir a evidência dos critérios que trabalhar.

## Validação

Ambiente: Windows, PowerShell e Python 3.14.6. Foram executados geração e modo `--check` da nova régua. A conferência documental inclui 12 frentes, 60 IDs únicos, soma de 100 pontos, níveis válidos, dependências sem ciclos, cinco gates, histórico completo, fontes rastreadas/locais identificadas e correspondência do Markdown com o JSON.

Verificações adicionais e hashes dos arquivos entregues constam do JSON de validação. Incluem cálculo independente, rejeição de estados inconsistentes, links locais, equivalência do registro futuro entre as duas pastas e preservação byte a byte do trabalho preexistente inventariado.

Não foram executados testes do compilador/runtime, builds nativos, suites gráficas, sandbox ou busca. Não houve mudança em código da linguagem, bibliotecas, binários, instaladores, versões ou CI nesta unidade. Testes históricos do material inspecionado não são apresentados como execução desta sessão. A nova ferramenta calcula consistência e não certifica o conteúdo dos testes citados.

## Publicação e continuidade

Esta unidade é preparada como um commit documental separado na branch de destino indicada. O SHA exato é o commit que introduz este relatório, consultável no histórico do GitHub; a confirmação de publicação e seu link são fornecidos no encerramento da sessão. A publicação do plano não publica automaticamente as continuações locais de outras sessões, nem equivale a merge, CI aprovada ou release de pacote.

Próxima unidade recomendada: M0, reconciliar e validar a continuação local já existente em entregas próprias, congelar o perfil mínimo do visualizador e a ABI de plataforma, e iniciar arena geracional/alocação fallível e primeira janela. Cada unidade segue o [masterprompt](../ecossistema/MASTERPROMPT.md), com evidência, relatório e publicação.

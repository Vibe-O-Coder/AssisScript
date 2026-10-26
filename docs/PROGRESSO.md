# Estimativa de conclusão — 3.3.0-alpha.10

Data: 26/10/2026. **Conclusão estimada: 77%** (76,5 pontos de 100).

Escopo: Conclusão do plano de evolução das fases 0–6, incluindo a trilha funcional e as aplicações A/B/C. Não inclui construir o navegador, HTDL, estilos ou motor de busca.

É uma estimativa de engenharia baseada nas entregas do plano, não uma medição de horas restantes, prazo, probabilidade de sucesso ou garantia de produção. Uma linguagem pode continuar evoluindo após este escopo. Os pesos representam importância relativa e são uma convenção explícita, revisável.

## Método

São 35 critérios, cinco por fase. Cada critério divide igualmente o peso de sua fase. Concluído recebe 100% desse crédito; parcial recebe 50%; pendente recebe 0%. A soma ponderada é arredondada ao inteiro mais próximo, com meio ponto para cima. Parcial indica uma implementação útil com parte relevante da aceitação ainda aberta. Mudanças de escopo/peso devem ser registradas antes de comparar versões.

As etapas F0–F4 estão incorporadas aos critérios: efeitos/ordem superior na fase 1, vidas/dados/capturas na fase 2, iteradores na fase 3 e efeitos externos/TCO nas fases 4/5; não recebem pontos em duplicidade. O crédito de ownership das APIs funcionais pertence à fase 2; a alpha.6 integra F1 para coleções escalares/funções pure. Uma fase com mecanismos completos não certifica produção.

| Fase | Peso | Atendimento dos critérios | Pontos obtidos |
| --- | ---: | ---: | ---: |
| 0 — Baseline e segurança | 15 | 80% | 12,0 |
| 1 — Tipos estruturados e especialização | 15 | 100% | 15 |
| 2 — Ownership e dados funcionais | 20 | 90% | 18,0 |
| 3 — Texto, números e aplicação CLI | 15 | 100% | 15 |
| 4 — Integração, rede e serviços | 15 | 30% | 4,5 |
| 5 — Backend e depuração | 10 | 50% | 5,0 |
| 6 — Ferramentas e oferta delimitada | 10 | 70% | 7,0 |
| **Total** | **100** | **77% estimados** | **76,5** |

## Histórico pela mesma régua

| Versão | Estimativa | Observação |
| --- | ---: | --- |
| 3.3.0-alpha.4 | 31% (30,5 pontos) | Reconstrução retrospectiva; não era um número publicado na entrega |
| 3.3.0-alpha.5 | 34% (33,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.6 | 45% (44,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.7 | 56% (56,0 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.8 | 70% (70,0 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.9 | 76% (75,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.10 | 77% (76,5 pontos) | Avaliação desta entrega |

Cada registro histórico congela seus 35 estados; atualizações futuras não alteram retroativamente esses estados.

## Evidência por critério

### Fase 0 — Baseline e segurança

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P0-BASE — Baseline, hashes e reconstrução local comparável | Concluído no escopo do critério | [Documento](VALIDACAO-3.3-ALPHA.10.md) — Estado alpha.9 preservado em commit Git antes das mudanças; reconstrução limpa da entrega atual. |
| P0-PRIV — Encapsulamento nominal e rejeições de B01 nos dois destinos | Concluído no escopo do critério | [Documento](CONTRATOS-E-SEGURANCA.md) |
| P0-SAFE — Fronteira safe/unsafe obrigatória e garantias para text externo | Parcial (50%) | [Documento](OWNERSHIP-FUNCOES.md) — Perfil safe exige fronteira unsafe; migração global e text externo permanecem abertos. |
| P0-FLOW — Auditoria de aliases, fluxo, laços e empréstimos completos | Concluído no escopo do critério | [Documento](OWNERSHIP-FUNCOES.md) — Auditoria do modelo gerenciado suportado; bloqueios conservadores em laços/campos. Não abrange ponteiros legados. |
| P0-CI — Matriz adversa contínua Windows/Linux e inventário técnico | Parcial (50%) | [Documento](PROCEDENCIA.md) — Matriz acionada no GitHub e falhas iniciais de ambiente corrigidas; inventário completo dos componentes dos binários ainda parcial. |

### Fase 1 — Tipos estruturados e especialização

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P1-TYPES — Identidades, aplicações estruturadas e cache canônico limitado | Concluído no escopo do critério | [Documento](GENERICS.md) |
| P1-FUN — Funções e structs genéricas por AST com validação concreta | Concluído no escopo do critério | [Documento](GENERICS.md) |
| P1-CLASS — Classes genéricas, herança, métodos e privacidade nominal | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.4.md) |
| P1-EFFECT — Tipos de função com efeitos, valores, callbacks e composição | Concluído no escopo do critério | [Documento](FUNCOES-E-EFEITOS.md) |
| P1-COL — Corpos de Array/HashMap na especialização AST comum | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.5.md) |

### Fase 2 — Ownership e dados funcionais

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P2-LOCAL — Análise de fluxo e exclusividade para recursos da aplicação | Concluído no escopo do critério | [Documento](OWNERSHIP-FUNCOES.md) — Fluxo/exclusividade para buffers, coleções escalares/funções e structs gerenciadas; outros recursos continuam em P2-DROP. |
| P2-LIFE — Consumo, empréstimos e vidas em assinaturas/retornos | Concluído no escopo do critério | [Documento](OWNERSHIP-FUNCOES.md) — Consumo e retornos com uma origem explícita; contratos também em generics/callbacks. Sem inferência ou união de vidas. |
| P2-DROP — Campos proprietários, destruição composta e movimento parcial | Concluído no escopo do critério | [Documento](RECURSOS-E-FATIAS.md) — Structs/classes com campos own, receptor verificado, destruição dinâmica, movimentos parciais e lista proprietária limitada. Recursos externos requerem adaptadores; Array/HashMap legados não assumem elementos. |
| P2-VALUE — Layout por valor, contratos Copy/Move e dados imutáveis | Concluído no escopo do critério | [Documento](VALORES-E-VARIANTES.md) — Layout Copy inline imutável, cópias em chamadas/retornos/coleções e contrato separado Move para recursos own. Campos Move inline são rejeitados. |
| P2-ADT — Variantes, Result/Option, matching e capturas verificadas | Parcial (50%) | [Documento](VALORES-E-VARIANTES.md) — Enums genéricos Copy, matching exaustivo, Option/Result; capturas/closures e variantes Move continuam pendentes. |

### Fase 3 — Texto, números e aplicação CLI

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P3-TEXT — Texto com comprimento/vidas, bytes e APIs Unicode | Concluído no escopo do critério | [Documento](BIBLIOTECA-unicode.md) — API nova unicode::Texto com UTF-8/NUL/comprimento, own em campos/listas e slices com vidas em parâmetros/retornos. text C e Texto legado preservam contrato anterior; sem grafemas/normalização. |
| P3-NUM — Inteiros de largura fixa e números de ponto flutuante | Concluído no escopo do critério | [Documento](NUMEROS.md) — Inteiros de largura fixa e f32/f64 nativos, layout/ABI/coleções, overflow/conversões e IEEE verificados; print real hexadecimal exato. |
| P3-IO — Arquivos, caminhos e argumentos com aplicação A validada | Concluído no escopo do critério | [Documento](IO-E-APLICACAO-A.md) — Arquivos own, argumentos/caminhos Unicode e aplicação A em CSV numérico de uma coluna, com fluxo limitado, erros e permissões nos dois sistemas. Sem API geral de diretórios/JSON. |
| P3-LIB — Bibliotecas CLI, JSON, tempo, logs e iteradores com recursos seguros | Concluído no escopo do critério | [Documento](BIBLIOTECAS.md) — CLI own, JSON UTF-8 com limites, tempo/logs e pipelines imutáveis entregues no escopo CLI. DOM/JSON incremental, CSV legado geral e APIs mais amplas permanecem evolução. |
| P3-PKG — Namespaces e pacotes versionados com lockfile offline | Concluído no escopo do critério | [Documento](PACOTES-E-NAMESPACES.md) — Namespaces/visibilidade nominal, versões exatas, dependências transitivas vendorizadas e lockfile SHA-256 offline; sem registro/download. |

### Fase 4 — Integração, rede e serviços

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P4-FFI — ABI C/FFI com recursos e callbacks externos | Pendente | [Documento](PLANO-EVOLUCAO-E-HANDOFF.md) |
| P4-EVENT — Event loop, temporizadores, cancelamento e efeitos explícitos | Concluído no escopo do critério | [Documento](EVENTOS-E-PERSISTENCIA.md) — Fila cooperativa limitada de uma thread, callbacks safe sem captura, relógios, prazos, IDs/cancelamento, reagendamento, parada e orçamento. Sem polling de descritores ou preempção. |
| P4-NET — Rede, DNS e HTTP/TLS com limites e aplicação B | Pendente | [Documento](PLANO-EVOLUCAO-E-HANDOFF.md) |
| P4-STORE — Persistência, processos e IPC com aplicação C | Parcial (50%) | [Documento](EVENTOS-E-PERSISTENCIA.md) — Persistência nativa, criação exclusiva, sync/substituição e configuração reaberta após reinício. Processos/IPC, serviço C completo e durabilidade por queda de energia pendentes. |
| P4-SOAK — Concorrência definida e validação prolongada de 24 horas | Pendente | [Documento](PLANO-EVOLUCAO-E-HANDOFF.md) |

### Fase 5 — Backend e depuração

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P5-IR — Frontend separado e IR tipada com fluxo/efeitos | Parcial (50%) | [Documento](RECURSOS-E-FATIAS.md) — Lexer/frontend separados da emissão; HIR tipada com blocos, efeitos, sucessores e DCE conservadora. Expressões ainda AST; sem SSA/backend por IR completo. |
| P5-OPT — Otimizações comprovadas, TCO, intervalos e alocação de registradores | Parcial (50%) | [Documento](OPTIMIZATION-ALPHA.10.md) — Hash inteiro/alocação corrigidos; salvamento seletivo, ponderação por laço, imediatos/LEA, inlining escalar e prova conservadora de bounds. Alocação global, métodos e otimização ampla continuam abertos. |
| P5-ABI — ABI documentada e validada para interfaces e retornos compostos | Parcial (50%) | [Documento](ABI-NATIVA.md) — ABI interna LVS1, cópia/retornos compostos e adaptadores OS documentados e validados. ABI C pública, FFI e callbacks externos pendentes. |
| P5-DEBUG — ELF PIE, símbolos/linhas e depuração nativa | Concluído no escopo do critério | [Documento](RECURSOS-E-FATIAS.md) — ELF ET_DYN/PIE, RIP/vtables relativos, símbolos/DWARF e GDB com parâmetros/locais escalares e escopos. Windows conserva mapas; sem PDB ou descrição de compostos. |
| P5-TARGET — Backend extensível e novos alvos ARM64/macOS validados | Pendente | [Documento](PLANO-EVOLUCAO-E-HANDOFF.md) |

### Fase 6 — Ferramentas e oferta delimitada

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P6-INSTALL — Instalação, atualização e remoção offline preservam dados | Concluído no escopo do critério | [Documento](VALIDACAO-3.3-ALPHA.10.md) — Catálogo/instaladores sincronizados com 16 bibliotecas e preservação de dados. |
| P6-TOOLS — Editor, documentação, fmt/test/doc e LSP independente | Concluído no escopo do critério | [Documento](FERRAMENTAS-ALPHA.8.md) — fmt/test/doc nativos, editor com namespaces/pacotes e LSP independente por stdio, sem dependências npm. Formatter cobre indentação, LF e espaços finais. |
| P6-RELEASE — Pacotes coerentes e reconstrução local limpa reproduzível | Concluído no escopo do critério | [Documento](VALIDACAO-3.3-ALPHA.10.md) — Pacotes e reconstrução da entrega atual. |
| P6-POLICY — Licença/procedência resolvidas e política de suporte/compatibilidade | Parcial (50%) | [Documento](PROCEDENCIA.md) — Licença CC BY-NC-SA escolhida pelo responsável, suporte/compatibilidade e avisos Windows publicados; direitos de imagens e auditoria completa de componentes ainda abertos. |
| P6-ACCEPT — Terceiro instala, depura e distribui aplicações A/B/C pelo manual | Pendente | [Documento](PLANO-EVOLUCAO-E-HANDOFF.md) |

A evidência vinculada também descreve limites, inclusive para critérios pendentes. A base de bibliotecas, distribuição, vidas explícitas, recursos compostos, fatias/texto gerenciado, valores Copy/variantes e a aplicação A delimitada já existe; variantes Move/capturas, aplicações B/C, integração externa, conclusão da HIR e novos alvos concentram o restante. A licença foi escolhida pelo responsável; direitos de imagens e auditoria completa de componentes permanecem abertos.

Fonte auditável: [PROGRESSO.json](PROGRESSO.json). Gerar com `python tools/report-progress.py`; verificar com `python tools/report-progress.py --check`. Relatórios históricos de versões anteriores permanecem preservados; a porcentagem começa a ser publicada na alpha.5.

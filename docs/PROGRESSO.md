# Estimativa de conclusão — 3.3.0-alpha.15

Data: 28/10/2026. **Conclusão estimada: 94%** (94,0 pontos de 100).

Escopo: Conclusão do plano de evolução das fases 0–6, incluindo a trilha funcional e as aplicações A/B/C. Não inclui construir o navegador, HTDL, estilos ou motor de busca.

É uma estimativa de engenharia baseada nas entregas do plano, não uma medição de horas restantes, prazo, probabilidade de sucesso ou garantia de produção. Uma linguagem pode continuar evoluindo após este escopo. Os pesos representam importância relativa e são uma convenção explícita, revisável.

## Método

São 35 critérios, cinco por fase. Cada critério divide igualmente o peso de sua fase. Concluído recebe 100% desse crédito; parcial recebe 50%; pendente recebe 0%. A soma ponderada é arredondada ao inteiro mais próximo, com meio ponto para cima. Parcial indica uma implementação útil com parte relevante da aceitação ainda aberta. Mudanças de escopo/peso devem ser registradas antes de comparar versões.

As etapas F0–F4 estão incorporadas aos critérios: efeitos/ordem superior na fase 1, vidas/dados/capturas na fase 2, iteradores na fase 3 e efeitos externos/TCO nas fases 4/5; não recebem pontos em duplicidade. O crédito de ownership das APIs funcionais pertence à fase 2; a alpha.6 integra F1 para coleções escalares/funções pure. Uma fase com mecanismos completos não certifica produção.

| Fase | Peso | Atendimento dos critérios | Pontos obtidos |
| --- | ---: | ---: | ---: |
| 0 — Baseline e segurança | 15 | 100% | 15 |
| 1 — Tipos estruturados e especialização | 15 | 100% | 15 |
| 2 — Ownership e dados funcionais | 20 | 100% | 20 |
| 3 — Texto, números e aplicação CLI | 15 | 100% | 15 |
| 4 — Integração, rede e serviços | 15 | 100% | 15 |
| 5 — Backend e depuração | 10 | 70% | 7,0 |
| 6 — Ferramentas e oferta delimitada | 10 | 70% | 7,0 |
| **Total** | **100** | **94% estimados** | **94,0** |

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
| 3.3.0-alpha.11 | 85% (85,0 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.12 | 90% (89,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.13 | 92% (91,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.14 | 92% (91,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.15 | 93% (92,5 pontos) | Avaliação desta entrega |
| 3.3.0-alpha.15 — 24 horas aprovadas, 28/10/2026 | 94% (94,0 pontos) | Avaliação desta entrega |

Cada registro histórico congela seus 35 estados; atualizações futuras não alteram retroativamente esses estados.

## Evidência por critério

### Fase 0 — Baseline e segurança

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P0-BASE — Baseline, hashes e reconstrução local comparável | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.15.md) — Baseline alpha.14 e patch rastreado preservados; três runtimes regenerados em árvores limpas; compiladores Windows/Linux idênticos aos testados na alpha.15. |
| P0-PRIV — Encapsulamento nominal e rejeições de B01 nos dois destinos | Concluído no escopo do critério | [Documento](CONTRATOS-E-SEGURANCA.md) |
| P0-SAFE — Fronteira safe/unsafe obrigatória e garantias para text externo | Concluído no escopo do critério | [Documento](SAFE-DEFAULT.md) — Entrada safe por padrão; --legacy explícito. Chamadas legadas/text C externo exigem unsafe; assinaturas/recursos safe recusam text sem vida. Reentrada em inicializadores gerenciados rejeitada. |
| P0-FLOW — Auditoria de aliases, fluxo, laços e empréstimos completos | Concluído no escopo do critério | [Documento](OWNERSHIP-FUNCOES.md) — Auditoria do modelo gerenciado suportado; bloqueios conservadores em laços/campos. Não abrange ponteiros legados. |
| P0-CI — Matriz adversa contínua Windows/Linux e inventário técnico | Concluído no escopo do critério | [Documento](PROCEDENCIA.md) — 29 suítes nativas locais Windows/Linux e inventário real dos três binários atualizados; CI remota alpha.13 não executada nesta sessão. Direitos de imagens ficam em P6-POLICY. |

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
| P2-VALUE — Layout por valor, contratos Copy/Move e dados imutáveis | Concluído no escopo do critério | [Documento](VALORES-E-VARIANTES.md) — Copy inline imutável e Move explícito para recursos. Enums com payload own usam invólucro no heap e destruição por tag; registros Move inline não são suportados. |
| P2-ADT — Variantes, Result/Option, matching e capturas verificadas | Concluído no escopo do critério | [Documento](CAPTURAS-E-VARIANTES-MOVE.md) — Enums Copy inline e Move próprios, matching exaustivo emprestado/consumidor; closures safe val/own/borrow com vidas lexicais e reduce_with. Sem Move inline, closures pure, captura borrow mut ou adaptação para ABI C. |

### Fase 3 — Texto, números e aplicação CLI

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P3-TEXT — Texto com comprimento/vidas, bytes e APIs Unicode | Concluído no escopo do critério | [Documento](BIBLIOTECA-unicode.md) — API nova unicode::String com UTF-8/NUL/comprimento, own em campos/listas e slices com vidas em parâmetros/retornos. text C e String global legado preservam contrato anterior; sem grafemas/normalização. |
| P3-NUM — Inteiros de largura fixa e números de ponto flutuante | Concluído no escopo do critério | [Documento](NUMEROS.md) — Inteiros de largura fixa e f32/f64 nativos, layout/ABI/coleções, overflow/conversões e IEEE verificados; print real hexadecimal exato. |
| P3-IO — Arquivos, caminhos e argumentos com aplicação A validada | Concluído no escopo do critério | [Documento](IO-E-APLICACAO-A.md) — Arquivos own, argumentos/caminhos Unicode e aplicação A em CSV numérico de uma coluna, com fluxo limitado, erros e permissões nos dois sistemas. Sem API geral de diretórios/JSON. |
| P3-LIB — Bibliotecas CLI, JSON, tempo, logs e iteradores com recursos seguros | Concluído no escopo do critério | [Documento](BIBLIOTECAS.md) — CLI own, JSON UTF-8 com limites, tempo/logs e pipelines imutáveis entregues no escopo CLI. DOM/JSON incremental, CSV legado geral e APIs mais amplas permanecem evolução. |
| P3-PKG — Namespaces e pacotes versionados com lockfile offline | Concluído no escopo do critério | [Documento](PACOTES-E-NAMESPACES.md) — Namespaces/visibilidade nominal, versões exatas, dependências transitivas vendorizadas e lockfile SHA-256 offline; sem registro/download. |

### Fase 4 — Integração, rede e serviços

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P4-FFI — ABI C/FFI com recursos e callbacks externos | Concluído no escopo do critério | [Documento](FFI-C.md) — ABI C escalar em Windows/Linux, callbacks síncronos, dependências explícitas e handles com drop. Agregados C por valor e callbacks em threads externas não são suportados. |
| P4-EVENT — Event loop, temporizadores, cancelamento e efeitos explícitos | Concluído no escopo do critério | [Documento](EVENTOS-E-PERSISTENCIA.md) — Fila cooperativa limitada de uma thread, callbacks safe sem captura, relógios, prazos, IDs/cancelamento, reagendamento, parada e orçamento. Sem polling de descritores ou preempção. |
| P4-NET — Rede, DNS e HTTP/TLS com limites e aplicação B | Concluído no escopo do critério | [Documento](BIBLIOTECA-net.md) — HTTP(S)/DNS assíncrono pelo cliente net, polling/cancelamento cooperativos, múltiplas requisições, limites e TLS com confiança isolada/certificado não confiado/hostname divergente. Aplicação B com cancelamento; dependência opcional libcurl nos dois sistemas, sem servidor HTTP ou resolvedor público. |
| P4-STORE — Persistência, processos e IPC com aplicação C | Concluído no escopo do critério | [Documento](BIBLIOTECA-process.md) — Persistência, processos/pipes, supervisão de grupo/job, locks liberados pelo OS e serviço C com reinício/corrupção/erro de commit. Sem durabilidade por queda de energia. |
| P4-SOAK — Concorrência definida e validação prolongada de 24 horas | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.15.md) — 24 horas reais aprovadas em Windows e Linux/WSL2: quatro serviços por sistema, polling e intervalo de 1s; 342519/345056 rodadas, falhas HTTP e cancelamentos esperados, memória/handles controlados e recuperação dos oito contadores. Compiladores e fontes conferidos; carga declarada, sem alegação de throughput máximo. |

### Fase 5 — Backend e depuração

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P5-IR — Frontend separado e IR tipada com fluxo/efeitos | Parcial (50%) | [Documento](BACKEND-IR-CONTROL.md) — CFG tipada e ScalarIR independente de AST para valores, escritas locais e condições escalares elegíveis; referência AST --no-opt. Recursos/endereços, retornos, cleanups e controle estruturado ainda têm caminhos AST; migração integral permanece aberta. |
| P5-OPT — Otimizações comprovadas, TCO, intervalos e alocação de registradores | Concluído no escopo do critério | [Documento](BACKEND-ALPHA15.md) — Liveness global com ponto fixo/coloração e reutilização dos quatro registradores preservados, exclusão de locais endereçados, fallback limitado; intervalos em laços diretos/reversos com offsets e chamadas pure. Equivalência/adversos Windows/Linux e comparação com alpha.14; sem alegação de otimalidade do alocador. |
| P5-ABI — ABI documentada e validada para interfaces e retornos compostos | Concluído no escopo do critério | [Documento](FFI-C.md) — LVS2 preservada e ABI C escalar pública delimitada, registradores mistos/pilha/retornos/callbacks validados contra biblioteca C independente; agregados C por valor são rejeitados. |
| P5-DEBUG — ELF PIE, símbolos/linhas e depuração nativa | Concluído no escopo do critério | [Documento](RECURSOS-E-FATIAS.md) — ELF ET_DYN/PIE, RIP/vtables relativos, símbolos/DWARF e GDB com parâmetros/locais escalares e escopos. Windows conserva mapas; sem PDB ou descrição de compostos. |
| P5-TARGET — Backend extensível e novos alvos ARM64/macOS validados | Pendente | [Documento](BACKEND-IR-CONTROL.md) — Hosts Linux/macOS ARM64 preparados para frontend e geração cruzada x86_64, com CI QEMU/Rosetta explicitamente emulado. Geração/runtime ARM64, instaladores e depuração dos novos destinos permanecem abertos. Resultado remoto deve ser verificado por commit. |

### Fase 6 — Ferramentas e oferta delimitada

| Critério | Estado | Evidência e limites |
| --- | --- | --- |
| P6-INSTALL — Instalação, atualização e remoção offline preservam dados | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.15.md) — Catálogo com 20 bibliotecas, 259 caminhos obrigatórios, instaladores/versão e lockfile sincronizados; perfis mínimo/completo e preservação de dados exercitados pelos harnesses. |
| P6-TOOLS — Editor, documentação, fmt/test/doc e LSP independente | Concluído no escopo do critério | [Documento](FERRAMENTAS-ALPHA.8.md) — fmt/test/doc nativos, editor com namespaces/pacotes e LSP independente por stdio, sem dependências npm. Formatter cobre indentação, LF e espaços finais. |
| P6-RELEASE — Pacotes coerentes e reconstrução local limpa reproduzível | Concluído no escopo do critério | [Documento](HANDOFF-3.3-ALPHA.15.md) — Reconstruções limpas com binários idênticos Windows/Linux; ZIP/VSIX e compiladores extraídos verificados na alpha.15. Entrega local, sem tag ou publicação remota. |
| P6-POLICY — Licença/procedência resolvidas e política de suporte/compatibilidade | Parcial (50%) | [Documento](PROCEDENCIA.md) — Licença escolhida pelo responsável e avisos publicados; inventário técnico de ligação concluído na alpha.12. Direitos de imagens e revisão dos termos/fontes de redistribuição continuam abertos. |
| P6-ACCEPT — Terceiro instala, depura e distribui aplicações A/B/C pelo manual | Pendente | [Documento](ACEITE-RELATO-USUARIO-2026-10-28.md) — Relato recebido em 28/10/2026: responsável compilou e executou programas próprios (Hello World, dobrar, arrays own/borrow e funções pure) em outros computadores Windows/Linux, aproximadamente na alpha.6 segundo sua lembrança. Versão exata/pacote não informados; evidência histórica do núcleo, sem aceite da distribuição atual ou de depuração/distribuição A/B/C por terceiro. Pontuação e estados históricos preservados. |

A evidência vinculada também descreve limites, inclusive para critérios pendentes. A base de bibliotecas, distribuição, vidas explícitas, recursos compostos, fatias/texto gerenciado, valores Copy/variantes e a aplicação A delimitada já existe; a conclusão da IR e os novos alvos concentram o restante técnico. As 24 horas reais Windows/Linux da alpha.15 estão registradas no handoff e na validação JSON. Variantes Move/capturas verificadas e pipelines com ambientes foram acrescentados na alpha.13. As aplicações B/C delimitadas e a ABI C escalar foram acrescentadas na alpha.11; a alpha.12 torna safe padrão, acrescenta rede cooperativa e inventário por ligação real. A licença foi escolhida pelo responsável; direitos de imagens e revisão de distribuição permanecem abertos; o inventário técnico dos binários está documentado.

Fonte auditável: [PROGRESSO.json](PROGRESSO.json). Gerar com `python tools/report-progress.py`; verificar com `python tools/report-progress.py --check`. Relatórios históricos de versões anteriores permanecem preservados; a porcentagem começa a ser publicada na alpha.5.

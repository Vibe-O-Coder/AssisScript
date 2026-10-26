# Continuação — 3.3.0-alpha.10

Data: 26/10/2026; trabalho iniciado em 25/10/2026, contexto do usuário. Plano, handoffs alpha.1–9 e relatório de otimização alpha.7 lidos. O estado recebido foi preservado no commit inicial `e88af38832c4ce7d42ab8a62b62f16c80970e7f9`, enviado ao GitHub antes de alterar os fontes. As baselines/medições históricas permanecem preservadas.

## Entrega

- Corrigidos hash de chaves inteiras em passos fixos e zeragem redundante de grandes mapeamentos. Salvamento seletivo de registradores, prioridade por laço, imediatos, LEA, endereçamento escalonado, inlining escalar limitado e prova conservadora de bounds. [Contratos e auditoria do relatório](OPTIMIZATION-ALPHA.10.md).
- Sintaxe canônica inglesa `fn/class/import/main/init`, aliases da sintaxe anterior e builtins ingleses. As entradas antiga/nova e os construtores compartilham regras de identidade; duplicações são rejeitadas. Dezesseis módulos mantidos, com nomes/APIs públicos em inglês, exemplos, editor/LSP, documentação e pacote offline migrados. [Migração](ENGLISH-API.md).
- READMEs em inglês, português e espanhol, licença escolhida pelo humano na raiz e na distribuição, regras de crédito/uso não comercial/bibliotecas/forks, política de suporte e avisos de terceiros. Direitos de imagens e auditoria completa de componentes ainda abertos.
- Novas suítes optimization/english-api/release-policy, gate de desempenho em CI, verificação de licenças/READMEs nos pacotes, manifesto/instaladores atualizados. Diretórios temporários de `run` no Windows são reservados atomicamente, eliminando a sequência arquivo temporário → apagar → criar diretório, que falhou durante testes concorrentes.

## Progresso e limites

**Conclusão estimada: 77% (76,5/100 pontos).** P6-POLICY passa de pendente a parcial, acrescentando um ponto; os demais estados e os pesos permanecem. Ganhos de desempenho e renomeações não recebem crédito duplicado.

A régua original de 35 critérios e seus snapshots históricos continuam sendo usados. O alvo solicitado de **90–100% ainda não foi atingido**. A estimativa consolidada e a evidência por critério estão em [PROGRESSO.md](PROGRESSO.md); os resultados efetivos desta sessão estão em [VALIDACAO-3.3-ALPHA.10.md](VALIDACAO-3.3-ALPHA.10.md).

P5-OPT continua parcial. Há provas e otimizações úteis, mas faltam alocação global, inlining de métodos/coleções, hoisting geral e ABI de argumentos em registradores. HIR não substitui expressões/emissão por AST. O hash de texto ainda é determinístico/previsível e grandes blocos não têm cache. O texto C legado conserva seus limites; `unicode::String` é a API gerenciada separada.

P6-POLICY avança de pendente para parcial: a escolha de licença agora existe, há suporte/compatibilidade e avisos da toolchain Windows; direitos de imagens e inventário completo dos binários continuam sem confirmação. Não tratar documentação ou teste automatizado como aceite por terceiro.

Permanecem abertas capturas/closures e variantes Move; safe obrigatório/text externo; FFI C/callbacks externos; rede/DNS/HTTP/TLS; processos/IPC e aplicações B/C completas; concorrência e 24 horas reais; backend integral por IR; ARM64/macOS; aceite independente e itens de procedência. Não contabilizar essas lacunas para atingir uma porcentagem.

## Operação

Fonte/emissão: `src/assisc.c`; recursos: `src/ownership.h`; análise de intervalos: `src/ranges.h`; HIR: `src/ir.h`; hash: `src/collections.h`; alocação: `src/runtime_memory.inc`. Especialização → tipos/pureza → ownership → safe → HIR/provas → emissão.

Windows: `tools/build-windows.ps1 -Compiler C:/msys64/ucrt64/bin/gcc.exe`. Linux: `make -B all`. Ao alterar assembly, regenerar ambos os blobs com `tools/embed-runtime.py`; alterações no catálogo/documentação requerem regenerar o manifesto e recompilar o instalador. As suítes novas estão em `make test-alpha10` e na reconstrução limpa.

`tools/benchmark-optimization.py --baseline COMPILADOR_ALPHA9 --output benchmarks/resultados/optimization-alpha10-SISTEMA.json --check` mede regressões específicas. `tools/benchmark-alpha10.py` mede cargas/recursos atuais, preservando os relatórios alpha.9. Antes de distribuir, reconstruir e validar, medir contra os binários finais, empacotar VSIX/ZIP e verificar ambos os sistemas.

Na próxima sessão, usar o commit final desta entrega como baseline, manter inglês nas novas APIs e atacar um contrato grande por vez: variantes Move/capturas com vidas, ABI C/FFI e integrações B/C. Registrar a implementação, falhas simuladas e evidência real antes de atualizar a régua.

## Correção após a CI Windows

A execução 40258606887 aprovou a etapa Linux completa e encontrou no Windows um alias 8.3 (`RUNNER~1`) não reconhecido como raiz do pacote. A correção normaliza somente as comparações de pacote/lockfile, preserva os caminhos dos diagnósticos e compara overlays por identidade de arquivo quando necessário. O teste Windows cobre grafias longa/curta, lock determinístico, entrada não salva e overlay que precisa invalidar o lock. As verificações físicas de confinamento e hardlinks permanecem em vigor.

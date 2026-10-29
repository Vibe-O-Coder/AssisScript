# Auditoria do restante do plano — alpha.15

A régua original permanece com 35 critérios e os mesmos pesos. A alpha.15
passou de 91,5 a 92,5 pontos ao concluir P5-OPT no contrato de
liveness global, provas de intervalos e equivalência/medições documentadas em
[BACKEND-ALPHA15.md](BACKEND-ALPHA15.md). Em 28/10/2026, a conferência das
[24 horas Windows/Linux](HANDOFF-3.3-ALPHA.15.md#ensaio-de-24-horas-concluído-e-aprovado) concluiu P4-SOAK (+1,5 ponto).
Nesta continuação, P5-IR foi concluído com emissão integral independente da AST
e equivalência Windows/Linux (+1 ponto), e o responsável confirmou o aceite por
outra pessoa seguindo o manual, incluindo depuração/distribuição de A/B/C
(+2 pontos). O total atual é **97/100 pontos (97%)**. Restam 3 pontos.

| Critério | Pontos faltantes | Trabalho e evidência necessários |
| --- | ---: | --- |
| P5-TARGET | 2 | Interface de backend estabilizada, geração/runtime ARM64 e macOS, instaladores, depuração e CI com execução nos novos destinos. Hosts ARM64 agora podem analisar/gerar x86_64; CI QEMU/Rosetta mede compatibilidade, sem atender geração nativa ARM64. |
| P6-POLICY | 1 | Responsável comprovar direitos das imagens/assets e fechar revisão dos termos/fontes de redistribuição. Inventário de ligação não decide autoria ou autorização de imagens. |

P5-IR está documentado em [BACKEND-IR-COMPLETA.md](BACKEND-IR-COMPLETA.md).
O [registro de aceite](ACEITE-RELATO-USUARIO-2026-10-28.md) distingue o relato
histórico inicial da confirmação independente recebida posteriormente.

## Ordem de continuação

Os ensaios Windows/Linux de 86400 segundos em cópias congeladas foram
concluídos, com recuperação dos oito serviços e hashes conferidos. Os relatórios
e o limite de carga declarado estão no [handoff](HANDOFF-3.3-ALPHA.15.md#ensaio-de-24-horas-concluído-e-aprovado).

1. Manter os compiladores anteriores preservados e validar a revisão P5-IR em CI.
   A execução remota `40796601634` aprovou o incremento anterior, incluindo pacotes;
   os resultados locais P5-IR são evidência separada da nova revisão.
2. Usar a IR completa para implementar geração e runtime ARM64, completando
   instaladores e depuração nos novos destinos com execução nativa.
3. Concluir a identidade visual e a revisão de distribuição. A direção escolhida
   é uma proposta geométrica com cores inspiradas em Miyabi e traços discretos
   de raposa, registrada em [IDENTIDADE-VISUAL-PROPOSTA.md](IDENTIDADE-VISUAL-PROPOSTA.md).

## Limitações que continuam explícitas

Borrow de closures é lexical e compartilhado; não escapa por move. Enums Move
ficam no heap, enquanto Copy permanece inline. Não há closures pure, adaptação
de capturas para ABI C, operador `?`, heap multithread, servidor HTTP, normalização
Unicode/grafemas, registro remoto de pacotes ou isolamento de páginas hostis.
Esses itens não recebem pontos novos por esta entrega. Navegador, HTDL, estilos,
renderização e busca continuam fora deste plano da linguagem.

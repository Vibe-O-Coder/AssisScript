# Auditoria do restante do plano — alpha.15

A régua original permanece com 35 critérios e os mesmos pesos. A alpha.15
passou de 91,5 a 92,5 pontos ao concluir P5-OPT no contrato de
liveness global, provas de intervalos e equivalência/medições documentadas em
[BACKEND-ALPHA15.md](BACKEND-ALPHA15.md). Em 28/10/2026, a conferência das
[24 horas Windows/Linux](HANDOFF-3.3-ALPHA.15.md#ensaio-de-24-horas-concluído-e-aprovado) concluiu P4-SOAK (+1,5 ponto).
O total atual é **94/100 pontos (94%)**. Restam 6 pontos.

| Critério | Pontos faltantes | Trabalho e evidência necessários |
| --- | ---: | --- |
| P5-IR | 1 | Separar resolução/tipagem e emissão com operações tipadas; migrar com equivalência e referência independente. IR já emite valores, escritas locais e condições escalares elegíveis sem AST; recursos/endereços, retornos/cleanups e controle estruturado ainda têm caminhos AST. Veja [a continuação](BACKEND-IR-CONTROL.md). |
| P5-TARGET | 2 | Interface de backend estabilizada, geração/runtime ARM64 e macOS, instaladores, depuração e CI com execução nos novos destinos. Hosts ARM64 agora podem analisar/gerar x86_64; CI QEMU/Rosetta mede compatibilidade, sem atender geração nativa ARM64. |
| P6-POLICY | 1 | Responsável comprovar direitos das imagens/assets e fechar revisão dos termos/fontes de redistribuição. Inventário de ligação não decide autoria ou autorização de imagens. |
| P6-ACCEPT | 2 | Pessoa distinta instalar, compilar, testar, depurar e distribuir A/B/C usando só documentação pública; registrar falhas, correções e aceite independente. Autorrevisão do agente não substitui essa pessoa. |

## Ordem de continuação

Os ensaios Windows/Linux de 86400 segundos em cópias congeladas foram
concluídos, com recuperação dos oito serviços e hashes conferidos. Os relatórios
e o limite de carga declarado estão no [handoff](HANDOFF-3.3-ALPHA.15.md#ensaio-de-24-horas-concluído-e-aprovado).

1. Manter uma cópia da alpha.15 congelada e repetir a matriz em CI remota; a execução local
   desta entrega não é um status remoto.
2. Migrar backend em incrementos com equivalência e casos adversos, preservando
   os binários alpha.14/alpha.15 para comparação. Novos alvos dependem dessa interface.
3. Obter a documentação dos assets e o aceite externo; não presumir autorização
   ou declarar produção antes de atender os critérios da oferta pretendida.

## Limitações que continuam explícitas

Borrow de closures é lexical e compartilhado; não escapa por move. Enums Move
ficam no heap, enquanto Copy permanece inline. Não há closures pure, adaptação
de capturas para ABI C, operador `?`, heap multithread, servidor HTTP, normalização
Unicode/grafemas, registro remoto de pacotes ou isolamento de páginas hostis.
Esses itens não recebem pontos novos por esta entrega. Navegador, HTDL, estilos,
renderização e busca continuam fora deste plano da linguagem.

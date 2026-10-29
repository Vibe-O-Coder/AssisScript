# ADR-0001 — estratégia de escolha do executor de página

Data: 29/10/2026. Estado: **estratégia aceita; formato ainda não escolhido**.
Escopo: E00-03/E06-01, sem promoção de capacidade ou gate.

Nativo atual serve shell/broker/motor confiáveis. Conteúdo remoto não pode
executar binário nativo privilegiado. safe e processo sem restrições não
definem autoridade, limites de CPU nem isolamento do sistema operacional.
Wasm e VM própria permanecem alternativas do plano, sem escolher runtime,
licença ou versão por suposição.

A próxima decisão exige dois spikes comparáveis de uma sessão, limitados a
valores inteiros/booleanos, funções, controle e chamada hospedeira de contador.
O candidato Wasm deve fixar wasm32/layout, representação de recursos, loader,
validação e imports. O candidato VM deve fixar bytecode, verificador, layout,
dispatcher e custo das instruções. Nenhum spike anuncia subconjunto completo
da linguagem ou G2. Generics/ownership/erros/números mantêm semântica no perfil
que for efetivamente anunciado; formas não cobertas são rejeitadas.

Ambos registram: fonte/hash, compilação, execução contra referência nativa,
ordem de efeitos, overflow/traps, validação de bytes malformados, imports
negados, forja/replay/revogação de tokens, loop/recursão interrompidos,
memória/pilha e custos de chamada ao host. Repetir o teste com outra instância
ativa. Contabilizar memória do compilador e host call bloqueante, além de VM.

O host começa sem arquivos/processos/FFI/rede/relógio para página. Só imports
versionados e capacidades atribuídas por origem/instância/geração entram na
lista explícita. Atributos da página não atribuem origem. Broker aplica
limites antes de copiar/alocar e descarta respostas tardias por requestId.

A escolha final requer evidência de semântica e de autoridade contida, custo
medido, inventário de manutenção/licença e decisão publicada. Falha em uma
dessas provas mantém a decisão aberta. Mesmo com formato aprovado, sandbox
nativa Windows/Linux/macOS é obrigação separada de E06-04 e G2.

Nenhum backend, executor, provider ou sandbox é implementado por este ADR.
AssisScript Web/Easy continuam fora desta régua; Easy permanece a última etapa.

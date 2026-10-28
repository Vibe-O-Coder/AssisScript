# Revisão da linguagem — 3.3.0-alpha.14

Data: 26/10/2026. Objetivo: corrigir os atritos relatados nas duas análises,
sem continuar a pontuação do plano anterior. Esta é uma revisão local de uma
árvore que já continha alterações; não é uma tag limpa publicada.

## Mudanças

- Texto safe: print de slices e objetos com as_slice, write sem separadores,
  literais UTF-8 estáticos, write_bytes com slice e builder Unicode com reserva
  geométrica, append_int e formatação decimal explícita.
- Constantes globais/exportadas, referências entre constantes com detecção de
  ciclos e limite de expansão; caracteres de um byte com escapes.
- Construtores por classe com assinaturas independentes; super.init e chamadas
  diretas à base. Construtores sem argumentos da base são encadeados automaticamente.
- Reserva em duas fases no receptor mutável, preservando a rejeição de aliases
  conflitantes. Consulta dinâmica is e downcast emprestado as, com null na falha.
- OwnedArray de recursos Move, com get emprestado e pop que transfere posse.
  Árvore indexada: O(log capacidade), sem limite artificial de 1024 elementos.
- Retornos own temporários exigem destino explícito (vínculo local, transferência
  ou free): métodos, indexação e len não descartam o proprietário silenciosamente.
  Leituras escalares como values.push(len(values)) encerram o empréstimo antes
  de ativar o receptor mutável.
- Sorteio reproduzível com rejeição sem viés de módulo e ordenação safe por heapsort.
- Vocabulário canônico no compilador, manual, exemplos e ferramentas. Removidos
  aliases Assis/Fodase, comentários por palavras, div e diretivas #yuri/#body.
  Diagnósticos e template deixaram de emitir palavrões; booleanos usam true/false.
- Compilador histórico 2.1.0 isolado com fontes, binários e testes. É a edição
  mais antiga encontrada, não uma versão 1.x presumida. Procedência em ORIGIN.json.
- Backend experimental Mach-O x86_64 com dyld/libSystem, geração cruzada e
  seleção de platform. Linux/Windows continuam ELF/PE.

Closures, variantes Move e liberação automática de classes já existiam na
alpha.13 recebida; foram preservadas e revalidadas, não contadas como novidade.

## Validação e limpeza

- 30 suítes semânticas/nativas em Windows e Linux; 273 testes por sistema.
- 85 testes de editor/LSP/ferramentas, além dos harnesses existentes: 133 casos
  nativos Linux, 28 de módulos/instalação, 41 de PE e 130 nativos Windows.
- 32 exemplos passam no perfil padrão. Exemplos de memória manual usam uma
  fronteira unsafe explícita; isso não os converte em implementações safe.
- RPG migrado para nomes/sintaxe atuais. Semente 1 termina em vitória e semente
  5 em derrota; ambos executam em Windows/Linux com status 0 e stderr vazio
  sob --debug. O fonte original foi preservado antes da migração.
- Reconstrução limpa dos três runtimes e dos compiladores reproduz os binários
  entregues. Inventários de link atualizados para Windows/Linux.
- Limpeza: 6.202 arquivos gerados/pacotes antigos, 329.142.135 bytes (329 MB).
  Fontes, Git, edição histórica e snapshot anterior à revisão foram preservados.
- Empacotamento exclui arquivos .7z/.zip incidentais, build, caches e a edição
  histórica da distribuição moderna. A edição histórica tem um ZIP separado.

[Evidência e hashes](VALIDACAO-ALPHA14.json) · [Inventário da limpeza](LIMPEZA-ALPHA14.json).
As contagens são casos de teste, não alegação de aceite independente ou de
produção. A validação remota de CI não foi acionada nesta revisão local.

## Limites explícitos

Não foram implementados interpolação como expressão, métodos genéricos
próprios, interfaces, concorrência, async/await, ARM64 ou execução isolada de
scripts. print(f64) continua hexadecimal; o builder oferece decimal com
precisão solicitada e faixa documentada. OwnedArray usa uma árvore, não um
buffer contíguo Array<own T>. As APIs manuais ainda exigem seus contratos de
liberação; o caminho seguro é Unicode/own/borrow.

Mach-O foi inspecionado estruturalmente; execução real em macOS não foi
realizada nesta máquina. O novo job de CI é a validação nativa pendente.
O backend não oferece extern de usuário, símbolos Mach-O, assinatura nem
notarização. Consulte MACOS.md.

O foco arquitetural desta entrega é o núcleo nativo para ferramentas e motores.
Um navegador e scripts de páginas exigem uma camada de execução isolada própria.
Não há alegação de substituição pronta do JavaScript nem de conclusão de 100%.

## Como usar a entrega

Os binários ativos em bin/assis.exe e bin/assis correspondem à alpha.14.
A documentação de entrada foi reescrita em [LINGUAGEM.md](LINGUAGEM.md).
O exemplo 31 reúne os novos recursos; o RPG preserva seus contratos manuais.
A sintaxe canônica é obrigatória inclusive com --legacy. O script
migrate-syntax.py traduz o dialeto; os nomes antigos de módulos/membros usam
API-MIGRATION.json como referência adicional.

Para gerar outro sistema: assis build programa.assis --target linux-x64,
windows-x64 ou macos-x64. A extensão .exe é aplicada apenas ao alvo Windows.
Geração cruzada foi verificada; run exige o alvo hospedeiro. O arquivo macOS
é Mach-O real, experimental, sem alegação de execução nativa já validada.

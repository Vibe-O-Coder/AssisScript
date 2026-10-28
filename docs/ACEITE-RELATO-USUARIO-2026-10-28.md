# Testes em outros computadores — relato do responsável

Relato recebido em 28/10/2026; a data em que os testes ocorreram não foi informada.
Fonte: declaração direta do responsável pelo projeto nesta conversa.

> Testei baixar em outros computadores (incluindo linux e windows) e os códigos de exemplo compilaram sem problemas.

Esclarecimento posterior do mesmo responsável:

> Fiz programas eu mesmo (não baixei os exemplos), mas eles funcionaram. As versões se datam da alpha.6 se eu não estiver enganado. Os programas que fiz foi um simples "Hello World", função dobrar() e manipulação de arrays com own, borrow e as funções pure.

O esclarecimento substitui a interpretação inicial de que foram usados os
exemplos distribuídos. O teste foi de programas escritos pelo próprio usuário,
com compilação e execução bem-sucedidas segundo seu relato.

## Evidência disponível

- O responsável relata download da linguagem e uso de programas próprios em
  outros computadores Windows/Linux, com compilação e execução funcionando.
- A versão é aproximadamente alpha.6, segundo a lembrança do responsável; não
  há confirmação do número exato nem identificação do pacote.
- Programas descritos: Hello World, função `dobrar()` e manipulação de arrays
  com `own`, `borrow` e funções `pure`.
- O relato é evidência humana de uso em outras máquinas, complementar aos testes
  automatizados. Não houve uma nova execução desses testes pelo agente.

## Informações ainda não fornecidas

- Versão exata/pacote baixado, origem do download e hash do pacote.
- Versões dos sistemas, arquiteturas e quantidade de máquinas.
- Fontes dos programas, comandos usados e saídas observadas.
- Depuração e distribuição das aplicações A/B/C.
- Participação de outra pessoa que tenha seguido apenas o manual público.

Campos não informados permanecem desconhecidos, sem presumir falha ou sucesso.
O responsável pode complementar o registro com o que lembrar; não é necessário
repetir etapas que já tenham evidência suficiente.

## Efeito no plano

O relato reforça a validação histórica de download, compilação, execução,
funções e ownership de arrays em Windows/Linux, aproximadamente na alpha.6.
Não é uma validação da distribuição alpha.15 atual ou de recursos posteriores.
O critério P6-ACCEPT inclui instalação, teste, depuração e distribuição de A/B/C por
terceiro, conforme a fase 6 do plano. Seu estado permanece pendente, pois esse
escopo ainda não está demonstrado pelo relato. A pontuação permanece 94/100.

Para concluir a aceitação, preparar um pacote identificado e um roteiro curto
baseado no manual para que um testador externo registre as etapas restantes,
incluindo as dificuldades e correções encontradas.

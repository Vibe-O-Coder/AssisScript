# Edição histórica separada

O código atual usa somente a sintaxe canônica. A edição de brincadeira fica
em `historical/assis-joke-2.1.0/`, com seu próprio compilador Windows/Linux,
fontes, bibliotecas e exemplos. O pacote histórico é distribuído separadamente
do compilador atual. Execute seus exemplos com o binário dessa mesma pasta.

2.1.0 é a edição mais antiga encontrada nos arquivos fornecidos. A procedência
e o SHA-256 do arquivo original estão em ORIGIN.json. Não foi encontrada uma
versão 1.x. O material foi preservado sem modernizar seus tokens.

`historical/migration-inputs/rpg-alpha6.assis` preserva o RPG antes da migração.
Esse arquivo pertence à alpha.6, não ao compilador de brincadeira 2.1.0.
A versão migrada fica em `exemplos/rpg.assis`; mantém o modelo manual de memória
numa fronteira unsafe explícita. O exemplo 31 demonstra os novos recursos safe.

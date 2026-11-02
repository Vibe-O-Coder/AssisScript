# Recuperação HTDL de editor, v1

Contrato de desenvolvimento de 02/11/2026. Complementa
[static-catalog-0.1-v1](PERFIL-HTDL-CATALOGO-V1.md), sem ampliar Reader ou loader.
E07-01/E11-02, M3 parcial. A entrada pública continua `htdl::inspect`.

O editor percorre um rascunho UTF-8 e acumula erros independentes de sintaxe.
Entidades inválidas não escondem o texto posterior; abertura malformada se
sincroniza em `>` ou antes do próximo `<`; comentário quebrado consome até
`-->` ou EOF, sem interpretar marcação dentro do comentário. Fechamento sem
abertura é reportado. EOF com elemento aberto recebe diagnóstico. Uma segunda
raiz é ambígua e encerra a recuperação com H102. Não se promete determinar a
árvore pretendida de um documento malformado, nem recuperar todos os erros.

Cada iteração consome fonte ou termina. Limites do parser continuam: fonte
1 MiB, profundidade 256, 20.000 elementos/fragmentos, 64 atributos por abertura,
64 KiB por valor e guarda de trabalho. H401 encerra imediatamente; a primeira
tentativa de ultrapassar a capacidade de Diagnostics marca truncamento e
encerra. A capacidade pública continua 1..64. UTF-8 inválido/caractere proibido
continua encerrando com o primeiro H101, antes da construção de árvore.

Quando ocorre erro sintático ou de atributo durante construção, não se executa
validação semântica sobre a árvore parcial. Sem esses erros, o mesmo catálogo
e as verificações de referências/IDs anteriores continuam. Diagnósticos usam
offsets em bytes e posições UTF-16 base 1, fim exclusivo, sempre na fonte
original. O parser não insere bytes, corrige a fonte nem publica nós parciais.

`inspect` aborta somente seu candidato, inclusive em sucesso, saturação,
falha de alocação ou limite. Ativo e candidato de outro produtor permanecem.
`stage`, `load`, `stage_catalog` e `load_catalog` conservam o parser estrito:
qualquer erro impede ativação. O workspace e o corpo nativo de Parser continuam
os mesmos; Diagnostics permanece memória externa do chamador. Não é quota
de RSS ou do shell. Não há identidade incremental de editor nem execução de
rascunho, recursos, script, FS ou SSC.

Aceite: casos independentes de sintaxe, ranges derivados da fonte Unicode,
mutação determinística, truncamentos, limites/saturação e preservação do
ativo/vizinho/candidato externo, em otimizado e referência. LSP recebe múltiplos
erros no rascunho, descarta versões ultrapassadas e limpa ao fechar. Execução
nativa por sistema e limitações constam do relatório desta unidade.

# Recursos gerenciados e fatias — alpha.9

## Classes e receptores

`ASSIS` pode declarar campos own. Uma classe usada como own/borrow precisa ter todos os métodos com receptor explícito: `assis ler(borrow self):int` ou `assis alterar(borrow mut self,n:int):void`. O receptor aparece primeiro e não é passado pelo usuário. Métodos com receptor são safe; operações legadas exigem unsafe. Métodos antigos continuam com seu contrato manual e impedem promover a classe para own apenas por anotação.

Campos de referência devem ser own; os demais campos devem ser valores escalares/Copy ou text de vida externa no perfil legado. Safe rejeita text externo. Construtores com receptor mutável podem inicializar campos own, com liberação automática do valor anterior. Um receptor compartilhado não pode modificar campos nem chamar métodos mutáveis. Sobrescritas conservam o modo do receptor e os contratos anteriores.

`final ASSIS` impede herança, inclusive de especializações genéricas e entre módulos. É um modificador contextual da declaração. As classes de unicode/proprios são final: seus construtores e métodos não podem ser sobrescritos por uma subclasse que evite a inicialização ou altere as invariantes da API.

Retornos `borrow(self)`/`borrow mut(self)` conservam a vida do receptor. O segundo exige receptor exclusivo. Mover um campo own através de borrow mut é permitido: o campo é zerado e a posição é marcada movida localmente, podendo ser reinicializada. Não se pode mover/liberar o próprio receptor emprestado. As regras conservadoras de laços e reserva de endereços permanecem.

Destruição de classe usa o tipo dinâmico, mesmo após upcast/move para uma base. Um endereço de drop fica imediatamente antes da vtable; libera campos own da derivada para a base em ordem inversa e depois o objeto. Não chama um dispose legado por nome. Structs mantêm seu drop concreto. Não há destrutor de usuário ou GC. Cada recurso externo novo precisa de seu próprio adaptador de drop.

`proprios::Lista<T>` integra proprietários em uma coleção limitada e preserva empréstimos dos elementos. Não transforma Array/HashMap legados em coleções proprietárias.

## Fatias

`slice<T>` representa dois words inline: endereço dos elementos e quantidade. T é um escalar/valor Copy, sem referência. `fatia(buffer,inicio,quantidade)` e `fatia(slice,inicio,quantidade)` avaliam argumentos uma vez da esquerda para a direita. Exigem buffer gerenciado, índices não negativos e quantidade menor ou igual ao tamanho restante; subtração antes da comparação evita overflow. Uma fatia vazia no fim é válida. A indexação sempre confere limites.

Fatias são empréstimos, não proprietários nem valores Copy públicos: exigem vínculos/parâmetros borrow, retornos com origem explícita e não podem ser copiadas por let, guardadas em campos/coleções, comparadas, liberadas ou convertidas para ponteiros brutos. Compartilhamento/exclusividade se aplicam à raiz inteira. Não há empréstimos disjuntos inferidos.

Argumentos/retornos inline seguem o destino oculto da ABI de valores, mas a tipagem não os classifica como Copy. Descritores não alocam no heap. Retornar fatia de local é rejeitado; chamadas indiretas e especializações mantêm o tipo do elemento e a origem. `slice<int>` e `slice<byte>` têm identidades distintas.

`unicode::Texto` é a API textual nova com comprimento/vida explícitos, UTF-8 e NUL. A API C `text`, Texto legado e CSV legado conservam seus contratos e não recebem garantias por coexistirem com essa biblioteca. Grafemas/normalização continuam extensões de APIs.

## Backend e diagnóstico

Linux passa a ET_DYN sem dependência de loader externo: endereços de código/dados são RIP-relative e entradas de vtable são deslocamentos de 64 bits relativos à própria entrada. Dispatch e drop somam a base da entrada. Não há relocação de páginas executáveis, código gravável ou base fixa. PE mantém suas relocations e vtables absolutas. O formato interno da vtable mudou; recompilar aplicações, sem misturar objetos/binários de alphas.

`--symbols` inclui DWARF v4 com linhas, funções, parâmetros e locais escalares, inclusive escopos e shadowing. Locais em registradores usam a localização correspondente e os demais usam RBP/frame base. Tipos compostos/ponteiros não recebem uma descrição fictícia; ainda não há PDB.

`assis ir fonte.assis` imprime `AssisScript-HIR-v1`: funções concretas, blocos, sucessores, tipos e efeitos conservadores. A primeira HIR conserva expressões na AST verificada, não é SSA nem substitui o backend. Decide somente remoção de instruções comprovadamente inacessíveis (após desvios e ramos constantes), depois de tipagem/ownership/safe de todo o fonte. `--no-opt` conserva emissão dessas instruções. Faltam otimizações de intervalos, inlining e nova alocação de registradores.

Lexer/diagnósticos estão em lexer.h, tipos/parser/verificações em frontend.h e a IR em ir.h. Permanecem em uma unidade C11 para manter a distribuição autossuficiente; não é uma separação completa em interfaces compiladas independentes.

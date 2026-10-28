# Migração para AssisScript 3.0

## Atualização de 3.0 para 3.1

`bytes` passa a ser palavra reservada; renomeie identificadores antigos com esse nome. As APIs anteriores permanecem disponíveis. `text(buffer)` cria uma visão emprestada de *byte terminado em zero, sem assumir posse. As novas classes de biblioteca Texto, DocumentoCSV e ResultadoBytes exigem `dispose(); free()`; `free` não é um destrutor automático de classes.

A instalação padrão inclui oito bibliotecas; perfis mínimo e seletivo são descritos no [catálogo](BIBLIOTECAS.md). A extensão nova e os binários devem ser atualizados juntos para reconhecer as primitivas. Diagnósticos JSON acrescentam campos sem alterar os existentes. Use `--no-opt` para comparar a geração de código. [Tratamento de erros](ERROS.md).

## Atualização de 2.x para 3.0

A regra de nomes Assis/Fodase foi removida. Os identificadores aceitam letras ASCII, sublinhado e números após o primeiro caractere. Tipos, variáveis, campos, parâmetros, funções e métodos podem ter nomes descritivos. Palavras-chave são sensíveis à caixa; te/to continuam delimitadores de comentário e não podem nomear variáveis.

Use let, int, byte, bool, text, void, if, else, while, return, print, new, free, self, true, false, null, break, continue e extends. Os aliases antigos continuam aceitos. As declarações centrais permanecem assis e ASSIS; a entrada continua assis_assis e o inicializador assis_fodase.

Troque `importa "std/math";` por `import "std/math.assis";`, em uma linha própria. A forma legada permanece compatível. Agrupe fontes em um manifesto .pillow e carregue com #body src.pillow.

Novas palavras são reservadas e podem exigir renomear identificadores de projetos antigos. Array, HashMap e o prefixo __assis_ também são reservados. Ponteiros brutos e classes conservam a semântica anterior. A saída de bool permanece aSsIs/fOdAsE.

Array<T> é uma coleção dinâmica tipada com limites verificados. HashMap<K, V> aceita chaves text, int, byte ou bool. Não há generics definidos pelo usuário. Struct cria registros nominais com referência ao heap, sem métodos ou herança: atribuir um struct compartilha a mesma instância. Isso não é uma struct C com cópia por valor.

free(array) e free(map) liberam os respectivos buffers automaticamente. Objetos armazenados continuam sendo responsabilidade do programa. dispose() apenas esvazia e libera os buffers, permitindo reutilizar a coleção.

O instalador Windows registra o ícone de .assis; os executáveis Windows gerados recebem o segundo ícone como recurso PE. A extensão inclui um tema de ícones e documentação offline. Se já houver uma preferência protegida de aplicativo padrão no Windows, escolha AssisScript nas configurações de aplicativos padrão para usar sua associação.

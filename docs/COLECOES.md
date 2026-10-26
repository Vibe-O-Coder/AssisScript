# Coleções tipadas 3.0

Array e HashMap estão disponíveis sem importação e são especializados pelo compilador para cada combinação de tipos. As operações são compiladas para código nativo. Uma atribuição compartilha a referência da coleção.

```assis
let numeros: Array<int> = [10, 20, 30];
let mapa: HashMap<text, int> = new HashMap<text, int>();
```

`len(colecao)` retorna a quantidade de elementos. Array usa índices entre zero e len - 1; leitura, escrita e atribuição composta verificam limites, incluindo índices negativos. HashMap aceita chave text, int, byte ou bool; textos comparam conteúdo até o primeiro byte zero. Colisões são tratadas por sondagem linear e remoção usa tombstones. A tabela cresce automaticamente; a ordem das entradas não é garantida.

Literais de array precisam de contexto tipado e aceitam aninhamento: `let matriz: Array<Array<int>> = [[1, 2], [3]];`. O mesmo vale para argumentos e retornos tipados. Não há literais de mapa nesta versão: use set.

`free(colecao)` libera os buffers e a instância. `dispose()` libera apenas buffers e reinicia a coleção, permitindo reutilizá-la. Nenhuma dessas operações libera objetos, arrays ou mapas armazenados: libere os elementos separadamente, exatamente uma vez. Campos internos iniciados com sublinhado são detalhes de implementação e não devem ser alterados.

## Array

### push(value: T): void

Acrescenta value ao final. Cresce a capacidade geometricamente quando necessário. Custo amortizado O(1); pode realocar o buffer.

### pop(): T

Remove e retorna o último elemento em O(1). Exige len(array) > 0; array vazio encerra com falha de precondição.

### get(index: int): T

Retorna o elemento no índice em O(1). Exige 0 <= index < len(array). Equivale à leitura array[index].

### set(index: int, value: T): void

Substitui o elemento no índice em O(1), sem alterar o tamanho. Exige índice válido e valor atribuível a T.

### insert(index: int, value: T): void

Insere value antes de index, deslocando os elementos seguintes. Aceita index == len(array). Custo O(n); índices negativos ou maiores que o tamanho falham.

### remove(index: int): T

Remove e retorna o elemento do índice, preservando a ordem dos demais. Custo O(n). Exige índice válido.

### contains(value: T): bool

Busca linear O(n). Textos são comparados por conteúdo; objetos e coleções por identidade de referência.

### reverse(): void

Inverte a ordem dos elementos no próprio array em O(n), sem criar outra coleção.

### reserve(capacity: int): void

Garante capacidade para pelo menos capacity elementos, sem alterar o tamanho. Não reduz a capacidade. Exige 0 <= capacity <= 2^60 - 1; falha se não houver memória.

### clear(): void

Remove logicamente todos os elementos em O(1), preservando o buffer. Não libera os objetos referenciados pelos elementos.

### dispose(): void

Libera o buffer e reinicia tamanho/capacidade para zero. A coleção permanece válida e pode ser reutilizada. free(array) executa esta liberação automaticamente.

## HashMap

### set(key: K, value: V): void

Insere ou substitui o valor da chave. Substituição não altera len(map). Custo esperado O(1); crescimento faz rehash O(n). Não assume posse de objetos armazenados.

### get(key: K): V

Retorna o valor associado em custo esperado O(1). Chave ausente encerra com falha de precondição; use has ou get_or quando a ausência for esperada.

### get_or(key: K, fallback: V): V

Retorna o valor da chave ou fallback se ausente. Não insere a chave. Ambos os argumentos são avaliados antes da chamada.

### has(key: K): bool

Informa se a chave existe, com custo esperado O(1). Não altera a tabela.

### remove(key: K): bool

Remove a chave e retorna true se existia. Mantém a cadeia de colisões por tombstone. Não libera o objeto associado.

### clear(): void

Remove todas as entradas e tombstones em O(capacidade), preservando os buffers. Objetos armazenados continuam sob responsabilidade do chamador.

### keys(): Array<K>

Cria um novo Array<K> com as chaves presentes em ordem não especificada. Custo O(capacidade). O chamador deve liberar o array retornado.

### values(): Array<V>

Cria um novo Array<V> com os valores presentes. Usa a mesma ordem de keys se não houver alterações entre chamadas. Custo O(capacidade); o chamador libera o array.

### dispose(): void

Libera os buffers de chaves, valores e estados e reinicia a tabela vazia. Pode ser reutilizada. Não libera objetos armazenados. free(map) faz isso automaticamente.

## Falhas e limites

Operações com índice inválido, pop em array vazio, get de chave ausente, reserve negativo e assert falso encerram com status 70. Erros internos de métodos das coleções indicam o módulo <colecoes>; indexação direta indica a posição do programa chamador. Alocação valida quantidade e overflow, mas continua limitada à memória disponível.

São permitidas até 256 especializações de coleções por programa. Array aceita tipos escalares, ponteiros, classes, structs e outras coleções. HashMap aceita os mesmos tipos como valor. void não é um tipo de elemento. Não há generics declarados pelo usuário, inferência sem contexto ou coleta automática de lixo.

O custo de hashing de chaves text é O(bytes da chave), além do custo esperado de sondagem. Endereços obtidos com &array[indice] podem ser invalidados por crescimento, reserve, clear, dispose ou free.
# Encapsulamento na 3.3 alpha

Campos internos de Array/HashMap e métodos auxiliares de HashMap são `private`, com verificação nominal do compilador. Acesso por alias, endereço ou ponteiro também é rejeitado em check/build/run. Use len/indexação e métodos públicos. A regra vale para referências legadas e gerenciadas. Ponteiros brutos legados continuam sob responsabilidade do programa; privacidade não é isolamento de memória. Veja [contratos](CONTRATOS-E-SEGURANCA.md).


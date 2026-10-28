# Perfil seguro padrão — alpha.12

`check`, `build`, `run`, `test`, `ir`, `doc` e `lock` usam a entrada verificada
por padrão. Declare `safe fn main():int`. A alpha.14 removeu os aliases históricos.
`--safe` continua aceito e é redundante. `assis new` já gera esse perfil.

`--legacy` é a opção explícita para programas anteriores, por exemplo:
`assis run exemplos/12_relatorio_vendas.assis --legacy --debug`.
`--safe` e `--legacy` juntos são erro, em qualquer ordem. O perfil legado não
desativa a verificação de funções declaradas safe nem de ownership/pureza.

Funções sem safe/pure continuam com efeito legado no tipo. Uma entrada safe
só pode chamá-las (inclusive indiretamente) dentro de `unsafe { ... }`.
Essa fronteira é o ponto de confiança para ponteiros brutos, FFI e APIs C.
Funções não usadas também têm sua declaração safe verificada; ramos mortos
não suprimem diagnósticos. `check --library` admite bibliotecas legadas sem
entrada; isso não as torna safe quando importadas.

`text` externo conserva a semântica histórica de string C. Não pode entrar
nem sair por assinatura safe ou ser armazenado em recurso gerenciado safe.
Conversões de ponteiros para text e APIs legadas exigem unsafe. Somente
`val literal:text="..."` recebe vida estática verificada no perfil seguro;
len/print desse literal são permitidos. Para dados externos, use
`unicode::String`, buffers own e `slice<byte>` com vidas explícitas.
Essa política recusa a fronteira sem prova; não infere uma vida para text C.

No VS Code, `assisscript.legacyMode: true` seleciona a compatibilidade em
diagnósticos/tarefas. No LSP independente, use `initializationOptions.legacyMode`.
Ambos usam false por padrão. A configuração não altera fontes.

Os corpus históricos selecionam --legacy explicitamente; a suíte
`test-safe-default.py` invoca diretamente o perfil padrão, em check/build/run,
ambos destinos, com e sem otimização e preservação do arquivo de saída após
rejeição. Ownership não é isolamento de scripts hostis, e unsafe transfere
a responsabilidade pelo contrato externo ao autor da fronteira.

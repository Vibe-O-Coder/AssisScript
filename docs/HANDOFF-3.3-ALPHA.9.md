# Relatório e continuação — 3.3.0-alpha.9

Data: 25/10/2026, contexto do usuário. Plano e nove documentos fornecidos lidos; fonte, ferramentas e limites analisados. Alpha.8 preservada em build/baseline-3.3-alpha.8 com hashes, sem alterar snapshots anteriores. Não há Git configurado.

## Conclusão estimada: 76%

São **75,5 pontos de 100**, pela mesma régua de 35 critérios. Pesos e os estados anteriores foram preservados. O alvo de 90–100% **não foi atingido**. Não converter trabalho ainda aberto ou um ensaio curto em crédito integral.

| Critério | Alpha.8 → alpha.9 | Pontos novos |
| --- | --- | ---: |
| P2-DROP | Parcial → concluído no modelo gerenciado documentado | 2 |
| P3-TEXT | Parcial → concluído pela API textual nova com comprimento/vidas | 1,5 |
| P5-IR | Pendente → parcial | 1 |
| P5-DEBUG | Parcial → concluído no alvo ELF/DWARF documentado | 1 |
| **Total** | | **5,5** |

Texto novo é unicode::Texto, não uma alteração silenciosa de text C/Texto legado. A lista proprietária é limitada; Array/HashMap não assumem ownership de objetos. HIR é parcial e as expressões continuam na AST. Debug inclui PIE, locais escalares e escopos no Linux; PDB e descrição de compostos continuam extensões. O percentual não certifica prontidão geral de produção.

## Implementado e validado

- Classes com campos own, receptor compartilhado/exclusivo, métodos safe e retornos vinculados ao receptor. Herança conserva contratos; destruição dinâmica libera a classe real mesmo através de base. Movimentos parciais pelo receptor exclusivo zeram campos e conservam a exclusividade. final ASSIS sela as invariantes das classes de biblioteca contra construtores/métodos sobrescritos.
- slice<T> inline, fatias de buffers/subfatias, bounds sem overflow, tamanho e ABI de argumentos/retornos. Origem e exclusividade verificadas inclusive em generics e chamadas indiretas. Sem ponteiros brutos armazenáveis ou alocação de descritores.
- Bibliotecas opcionais unicode e proprios: texto com UTF-8 estrito/NUL/comprimento, cópia recuperável preservando destino, recorte em fronteiras de código, lista de recursos Move com transferência e empréstimos.
- ELF ET_DYN com endereçamento relativo e vtables relativas; código/dados somente leitura e pilha não executável. DWARF descreve parâmetros e locais escalares em registradores/frame, com escopos e shadowing.
- Separação inicial de lexer/frontend, HIR tipada de fluxo/efeitos, inspeção por comando e remoção conservadora de instruções inacessíveis após todas as verificações.
- Editor, documentação, exemplo 25, catálogo de 16 bibliotecas, instaladores, testes, CI, reconstrução, medições e distribuição integrados. Resultados efetivos em [VALIDACAO-3.3-ALPHA.9.md](VALIDACAO-3.3-ALPHA.9.md); contratos em [RECURSOS-E-FATIAS.md](RECURSOS-E-FATIAS.md).

## Auditoria das pendências

1. **Fase 0:** safe é opcional; text C externo continua legado. CI foi configurada e executada localmente, sem execução remota/repositório. Procedência/licença seguem pendentes do responsável.
2. **Fase 1:** manter mecanismos entregues; métodos com parâmetros genéricos próprios e constraints são extensões não implementadas. Não reabrir generics básicos.
3. **Fase 2:** variantes Move, propagação com limpeza e closures/capturas por valor/move/borrow permanecem abertas em P2-ADT. Não chamar callbacks sem captura ou vtables de closures. Arrays/maps de donos, coleções persistentes e vidas de campos emprestados ainda não existem.
4. **Fase 3:** API textual nova completa no contrato; migração do CSV/Texto legado, JSON DOM/incremental, decimal float e grafemas/normalização são evolução de APIs. Fatias não se armazenam em campos sem contrato de vida.
5. **Fase 4:** faltam FFI C/callbacks externos, polling/rede/DNS/TLS/HTTP, aplicações B/C completas, processos/IPC e 24 horas reais. Persistência atual é parcial. A fila continua cooperativa, síncrona e de uma thread.
6. **Fase 5:** HIR ainda não substitui expressões/emissão por AST; faltam SSA/intervalos/inlining/alocação mais ampla, ABI C, novos alvos ARM64/macOS e debug de compostos/PDB. Mudança de vtable exige recompilação.
7. **Fase 6:** licença/procedência e política de suporte, instalação/depuração/distribuição por terceiro das aplicações A/B/C continuam pendentes. Não escolher licença em nome do usuário nem simular aceite humano.

## Operação e próximos passos

Raiz real: C:\Users\babus\Desktop\AssisScript\AssisScript. Driver/emissão: src/assisc.c; lexer: src/lexer.h; tipos/parser: src/frontend.h; HIR: src/ir.h; recursos: src/ownership.h; debug: src/debug_info.h. Fluxo: especialização → tipos/pureza → ownership → safe → HIR → emissão.

Windows: tools/build-windows.ps1 com GCC MSYS2. Linux: make -B all. Novas suítes: test-slices.py, test-managed-classes.py e test-backend-alpha9.py; make test-alpha9. Rebuild limpo repete as 18 suítes Python. GDB valida parâmetros/locais/escopos, além dos breakpoints/backtrace existentes.

Manifestos vinculam o lockfile à versão do compilador. Após revisar a migração de versão, executar assis lock no projeto antes de recompilar. O lock do exemplo pacote-offline foi atualizado para a alpha.9 e validado nos pacotes dos dois sistemas; snapshots alpha.8 continuam intactos.

Próximo incremento deve especificar variantes Move e capturas com vidas antes de conectá-las a callbacks externos. Em paralelo de planejamento, preparar ABI C/FFI e B/C com serviços locais reproduzíveis. Não lançar ensaio de 24 horas como se uma execução breve o concluísse. Preservar relatórios/histórico, atualizar PROGRESSO.json com evidência e regenerar manifesto, binários, medições e pacotes de modo coerente.

A investigação de desempenho preservou as sete amostras iniciais e acrescentou 21 pareadas com 10 milhões de iterações. As medianas de execução ficaram dentro de 5% nas quatro comparações longas. Compilação Windows sem otimização variou +19,6% na mediana (18,59→22,24 ms), com intervalos sobrepostos; a origem não foi isolada. Registrar essa variação aberta de tempo de compilação, sem atribuir causalidade à HIR ou prometer ganho geral. P5-OPT continua parcial.

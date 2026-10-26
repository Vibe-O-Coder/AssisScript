# Validação — AssisScript 3.3.0-alpha.6

Data: 25/10/2026. **Conclusão estimada: 45% (44,5/100 pontos)** pela [régua preservada](PROGRESSO.md). Critérios avançados: P0-SAFE parcial, P0-FLOW completo no modelo gerenciado, P2-LOCAL completo nesse modelo, P2-LIFE completo com contratos conservadores e P2-DROP parcial. Acrescenta 11 pontos à alpha.5. Não é prazo nem declaração de produção.

## Escopo e verificações

Ownership foi exercitado em parâmetros/retornos, empréstimos derivados, funções como valores, generics, campos own, movimentação parcial, reinicialização, destruição recursiva, laços e caminhos que retornam. Os negativos são rejeitados antes de emitir/executar código, em check/build/run, otimizado/sem otimização e nos dois destinos. Um arquivo sentinela confere que falhas não sobrescrevem uma saída existente. Os testes não executam programas que foram definidos como rejeições.

O perfil safe tem casos positivos/negativos para assinaturas, operações brutas, text externo, chamadas indiretas e fronteiras unsafe. A suíte também verifica que unsafe não permite escapar um recurso gerenciado. O exemplo 19 roda com --safe --debug; map/filter/fold gerenciados preservam entrada e tratam vazio sem vazamentos.

| Conjunto local | Resultado |
| --- | --- |
| Node: compilador, biblioteca e provedores do editor | 74 testes aprovados |
| Nativos Windows | 128 verificações aprovadas |
| Nativos Linux | 133 verificações aprovadas |
| Módulos/instalação Linux | 19 verificações aprovadas |
| PE com realocação e ABI Microsoft | 41 casos aprovados |
| Evolution | 12 grupos / 472 invocações por sistema |
| Generics | 13 grupos / 305 invocações por sistema |
| Functions | 19 grupos / 383 invocações por sistema |
| Generic classes | 17 grupos / 360 invocações por sistema |
| Collections AST | 10 grupos / 143 invocações por sistema |
| Ownership functions | 26 grupos / 580 invocações por sistema |

Os conjuntos se sobrepõem e não devem ser somados como testes independentes. As seis suítes Python foram repetidas na reconstrução limpa em cada sistema. Os corpora Node 3.1/3.2 foram regenerados para os diagnósticos atuais e repetidos pelos harnesses portáveis: 18 verificações 3.1 no Windows, 21 no Linux, e 73 casos 3.2 por sistema. A CI acompanha essas suítes, mas não houve execução remota.

## Reconstrução e identidade

Toolchains locais: MinGW UCRT64 GCC 15.2.0 (MSYS2 Rev13) no Windows e GCC 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) no Ubuntu/WSL. CPU Intel Core i7-6820HQ a 2,70 GHz. `validate-clean.py` copia apenas fontes/stdlib, remove os blobs de runtime dessa cópia, regenera ELF/COFF e compila sem bin/build/dist locais. Ambos reproduziram os compiladores byte a byte, repetindo as seis suítes. A exigência vale dentro da mesma toolchain, sem prometer identidade entre compiladores C diferentes.

| Artefato | SHA-256 |
| --- | --- |
| bin/assis.exe | `af5097c56d192696ec0afc226a91ce1d856bc980a5f50050058801b541f887a3` |
| bin/assis | `76224baea569a614e98870e8ee472c9a8b510808a1baf5a4d1bd00e96fc14210` |
| src/assisc.c | `17b1d414ae622899de8f0efbfdcbbe3ffbdf89aa51ebb88b16349fe5371bfda6` |
| src/ownership.h | `4da3cc053726b9cb936db93d26993caab0494439a4944ec32cf104e2b1602117` |
| src/safety.h | `4022462ce80eafa183d7861dd87fb626502f9a3147ec8814922a30c0a05aedd7` |
| src/generics.h | `ad19d3be9b47f1c246a4561764683aab719d8898ba4f82977641a31f94d5d634` |

Os hashes dos runtimes permanecem `758edd25288683ea6388778447920cf100f45d307cf6fc8f8410e77a99b57546` (ELF) e `644fb7296e1b81fe222903f32869a0e18e461f783e4898041a471282617ae2e4` (PE). SHA256SUMS cobre os arquivos distribuídos; logs de reconstrução e baselines são locais e excluídos.

## Custo e limites das medições

O [relatório Windows](../benchmarks/resultados/ownership-alpha-windows.md) e o [Linux](../benchmarks/resultados/ownership-alpha-linux.md), com JSONs adjacentes, comparam alpha.5 manual, alpha.6 manual e alpha.6 gerenciado em 200 mil registros/arrays no Windows e dois milhões no Linux. São sete amostras intercaladas após aquecimento, em ambos os modos de otimização. A saída N² é calculada por fórmula independente; debug exige zero alocações vivas no fim.

As referências manuais alpha.5/alpha.6 geraram executáveis idênticos byte a byte nos dois sistemas e modos. No Windows otimizado, medianas de 478,729/478,137/473,738 ms para baseline/manual/own; sem otimização, 523,516/521,496/525,929 ms. No Linux com carga ampliada, 166,513/168,796/201,085 ms e 179,341/181,817/192,183 ms, respectivamente. A variante own custa cerca de 19,1% sobre a manual atual no Linux otimizado e 5,7% sem otimização; suas chamadas adicionais não foram eliminadas. Esse é um custo desta implementação/carga, sem promessa de ganho de runtime por ownership. O pico mediano foi igual entre variantes em cada sistema: 2.719.744 bytes de working set no Windows e 270.336 bytes de RSS no Linux.

A [primeira medição Linux](../benchmarks/resultados/ownership-alpha-linux-inicial.md) foi preservada: sua carga curta de 200 mil iterações mostrou diferença de 24% entre arquivos manuais idênticos sem otimização. A investigação confirmou identidade pelos hashes; a carga foi ampliada dez vezes. A diferença das referências caiu para cerca de 1,4%, dentro dos intervalos observados. Nenhum resultado foi apagado ou convertido em ganho do compilador.

A variante gerenciada inclui chamadas adicionais criar/ler e helper de destruição composta. A diferença não isola a análise estática, que roda no compilador. Os relatórios registram início de processo, compilação, tamanho, variabilidade e pico de RAM por processo. Pico de working set Windows e RSS Linux são métricas distintas. Não medem retenção prolongada, aplicações A/B/C, concorrência ou estabilidade de 24 horas. Regressões materiais devem ser descritas com seus custos, sem retirar verificações.

## Distribuição e pendências

ZIP `dist/AssisScript-3.3.0-alpha.6-windows-linux.zip` e VSIX `dist/assisscript-3.3.0-alpha.6.vsix` incluem compiladores, oito bibliotecas, documentação, exemplos, métrica e relatórios. verify-release.py extrai os pacotes, confere versão/hashes, executa os exemplos, verifica bibliotecas e rejeições, incluindo ownership/safe. Relatórios anteriores não são reinterpretados como medições desta versão.

A verificação extraída passou no Windows e Linux: oito bibliotecas e 487 hashes do ZIP conferidos em cada sistema. O exemplo 19 executou com --safe --debug e sem alocações vivas na saída.

P2-DROP permanece parcial: classes/Texto, coleções de proprietários e recursos externos ainda faltam. P0-SAFE permanece parcial: perfil opcional, text externo excluído e código legado manual. Valores por valor/Copy/Move, Result/Option, matching, closures, arquivos/argumentos, aplicações A/B/C e licença/procedência seguem abertos. A auditoria de fluxo conclui o subconjunto gerenciado descrito em [OWNERSHIP-FUNCOES.md](OWNERSHIP-FUNCOES.md), com bloqueio conservador da raiz inteira e de consumo externo em laços; não comprova segurança geral de memória.

Limitações de ambiente foram separadas das falhas da linguagem: a tentativa restrita inicial de evolution não conseguiu criar temporários, sem invocações do compilador; a execução autorizada passou. As primeiras verificações nativas após o bump de versão apontaram expectativas ainda fixadas na alpha.5; as expectativas foram atualizadas e a matriz foi repetida.

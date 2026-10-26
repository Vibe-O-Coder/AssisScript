# Medições 3.2

A comparação atual com C -O2 e Python está em [nativo-3.2.md](../benchmarks/resultados/nativo-3.2.md), com dados brutos ao lado. Reproduza com `python tools/benchmark-native.py --samples 5 --cc gcc`. Para incluir o compilador anterior preservado, use `--baseline caminho/do/compilador`. Os números abaixo são históricos da versão 3.1. [Mudanças de backend e limites](MELHORIAS-3.2.md).

# Desempenho 3.1

O compilador gera código x86_64 diretamente. A versão 3.1 reduz expressões constantes com semântica modular de int64, usa cargas diretas de variáveis locais, evita empilhar operandos simples, reduz multiplicações constantes por potências de dois e emite imediatos menores. `--no-opt` permite comparar o mesmo programa com a geração anterior dessas operações. Tipos continuam sendo verificados antes da otimização, e divisões/deslocamentos inválidos preservam o erro de execução.

HashMap aproveita capacidades em potência de dois para sondagem por máscara, limpa tombstones sem aumentar a tabela desnecessariamente e calcula hash de texto com uma passagem pelos bytes. As bibliotecas usam comprimento calculado uma vez e acesso limitado aos bytes; a indexação pública text[i] continua com verificação e pode custar O(i). Texto usa crescimento geométrico; KMP tem O(n+m), heapsort O(n log n).

## Reproduzir medições

```powershell
node tools/benchmark.js
node tools/benchmark.js --baseline build/assis-3.0.exe
```

O relatório JSON e Markdown fica em benchmarks/resultados/. São medidos separadamente tempo de compilação, mediana/mínimo/máximo da execução e tamanho do executável. A execução mede binários já compilados, inclui inicialização do processo, tem aquecimento e sete amostras por padrão. Cada saída é conferida; resultados incorretos ou timeout invalidam a medição. Ambiente e versões ficam registrados. `--samples N` altera o número de amostras.

O comparativo `--no-opt` isola a geração de código dentro da mesma versão; `--baseline` também inclui mudanças nas coleções. O programa de texto usa biblioteca congelada nos dados de benchmark para comparar implementações sem importar bibliotecas novas na versão antiga. Os números dependem da máquina e da carga; não constituem promessa de superioridade sobre outras linguagens. Não há comparação com C, Rust ou Go nesta entrega.

Veja [relatório medido](RESULTADOS-DESEMPENHO.md), também incluído na instalação e no VSIX, e [validação](VALIDACAO.md).

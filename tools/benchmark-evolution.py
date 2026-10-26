"""Measure the cost of scalar pure/val against equivalent legacy code.

Includes process startup. Measures one compilation per variant, no RAM claim.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', type=Path)
parser.add_argument('--samples', type=int, default=7)
parser.add_argument('--output', type=Path, default=ROOT / 'benchmarks/resultados/funcional-alpha.json')
args = parser.parse_args()
if not 3 <= args.samples <= 30:
    parser.error('Use de 3 a 30 amostras')
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
count = 10_000_000
expected = str(3 * count * (count - 1) // 2 + 7 * count) + '\n'
legacy = ('assis calcular(n:int):int{let v:int=n*3+7;return v;}\n'
          'assis assis_assis():int{let total:int=0;'
          f'for(let i:int=0;i<{count};i+=1){{total+=calcular(i);}}'
          'print(total);return 0;}\n')
functional = legacy.replace('assis calcular', 'pure assis calcular').replace('let v:int', 'val v:int')


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=count, includesProcessStartup=True, expected=expected.strip(),
              compiler=run([compiler, 'version']).strip(), results=[])
with tempfile.TemporaryDirectory(prefix='assis-functional-bench-') as temp:
    directory = Path(temp)
    variants = [('atual-legado', compiler, legacy, []), ('atual-puro', compiler, functional, []),
                ('atual-puro-sem-opt', compiler, functional, ['--no-opt'])]
    if args.baseline:
        variants.append(('base-3.2-legado', args.baseline.resolve(), legacy, []))
        report['baseline'] = run([args.baseline.resolve(), 'version']).strip()
    commands = []
    for name, comp, text, flags in variants:
        source = directory / (name + '.assis')
        binary = directory / (name + ('.exe' if os.name == 'nt' else ''))
        source.write_text(text, encoding='utf-8')
        start = time.perf_counter_ns()
        run([comp, 'build', source, '-o', binary, *flags])
        compile_ms = (time.perf_counter_ns() - start) / 1e6
        if run([binary]) != expected:
            raise AssertionError(name + ': saída diferente da fórmula independente')
        data = binary.read_bytes()
        report['results'].append(dict(variant=name, compileMs=compile_ms, binaryBytes=len(data),
                                     sha256=hashlib.sha256(data).hexdigest(), samplesMs=[]))
        commands.append([binary])
    for sample in range(args.samples):
        for index in [(sample + offset) % len(commands) for offset in range(len(commands))]:
            start = time.perf_counter_ns()
            actual = run(commands[index])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if actual != expected:
                raise AssertionError('Saída divergente durante medição')
            report['results'][index]['samplesMs'].append(elapsed)
for result in report['results']:
    result['medianMs'] = statistics.median(result['samplesMs'])
    result['minMs'] = min(result['samplesMs'])
    result['maxMs'] = max(result['samplesMs'])
report['optimizedBinariesIdentical'] = len({entry['sha256'] for entry in report['results'] if entry['variant'] != 'atual-puro-sem-opt'}) == 1
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
markdown = ('# Custo do primeiro incremento funcional\n\n' + report['compiler'] + '; ' + report['platform'] + '.\n\n'
            f'{count} chamadas escalares, {args.samples} amostras intercaladas após um aquecimento. '
            'Todas as saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Tempos incluem início do processo.\n\n'
            '| Variante | Mediana ms | Mín–máx ms | Bytes | Compilação ms (uma observação) |\n'
            '| --- | ---: | ---: | ---: | ---: |\n')
for result in report['results']:
    markdown += f'| {result["variant"]} | {result["medianMs"]:.3f} | {result["minMs"]:.3f}–{result["maxMs"]:.3f} | {result["binaryBytes"]} | {result["compileMs"]:.3f} |\n'
markdown += ('\nOs fontes têm os mesmos vínculos e operações: a variante funcional troca let por val e anota a função com pure. '
             'pure/val não ativam otimizações novas. '
             'Hashes e amostras estão no JSON adjacente. Não mede generics, closures, RAM ou aplicações completas '
             'e não permite concluir paridade com C/C++. Diferenças dentro da faixa de variação exigem repetição antes de atribuir causa.\n')
if report['optimizedBinariesIdentical']:
    markdown += '\nAs variantes otimizadas, incluindo a base quando informada, geraram executáveis idênticos byte a byte neste caso. A diferença entre seus tempos não corresponde a uma diferença de código emitido.\n'
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

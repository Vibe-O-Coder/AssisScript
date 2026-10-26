"""Compare native scalar specialization with an equivalent handwritten function.

Seven interleaved samples by default. Compilation includes process startup; no
RAM or general throughput claim. Source paths/order/lines are held constant.
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
parser.add_argument('--samples', type=int, default=7)
parser.add_argument('--output', type=Path, default=ROOT / 'benchmarks/resultados/generics-alpha.json')
args = parser.parse_args()
if not 3 <= args.samples <= 30:
    parser.error('Use de 3 a 30 amostras')
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
count = 10_000_000
expected = str(3 * count * (count - 1) // 2 + 7 * count) + '\n'


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


variants = [('manual', False, []), ('generico', True, []),
            ('manual-sem-opt', False, ['--no-opt']), ('generico-sem-opt', True, ['--no-opt'])]
report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=count, includesProcessStartup=True, expected=expected.strip(),
              compiler=run([compiler, 'version']).strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(), results=[])
with tempfile.TemporaryDirectory(prefix='assis-generics-bench-') as temp:
    directory = Path(temp)
    source = directory / 'mesmo.assis'
    for name, generic, flags in variants:
        call = 'calcular::<int>(i)' if generic else 'calcular(i)'
        declaration = 'calcular<T>(n:T)' if generic else 'calcular(n:int)'
        text = ('assis assis_assis():int{let total:int=0;'
                f'for(let i:int=0;i<{count};i+=1){{total+={call};}}'
                'print(total);return 0;}\n'
                f'pure assis {declaration}:int{{return int(n)*3+7;}}\n')
        source.write_text(text, encoding='utf-8')
        binary = directory / (name + ('.exe' if os.name == 'nt' else ''))
        record = dict(variant=name, source=text, binaryBytes=0, compileSamplesMs=[], samplesMs=[])
        report['results'].append(record)
    # Interleave both build and execution so order is not tied to a variant.
    for sample in range(args.samples + 1):
        for index in [(sample + offset) % len(variants) for offset in range(len(variants))]:
            name, generic, flags = variants[index]
            record = report['results'][index]
            source.write_text(record['source'], encoding='utf-8')
            binary = directory / (name + ('.exe' if os.name == 'nt' else ''))
            start = time.perf_counter_ns()
            run([compiler, 'build', source, '-o', binary, *flags])
            compiled = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual = run([binary])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if actual != expected:
                raise AssertionError(name + ': saída diferente da fórmula independente')
            data = binary.read_bytes()
            record['binaryBytes'] = len(data)
            record['sha256'] = hashlib.sha256(data).hexdigest()
            if sample:
                record['compileSamplesMs'].append(compiled)
                record['samplesMs'].append(elapsed)
for record in report['results']:
    record['medianMs'] = statistics.median(record['samplesMs'])
    record['compileMedianMs'] = statistics.median(record['compileSamplesMs'])
report['identicalOptimized'] = report['results'][0]['sha256'] == report['results'][1]['sha256']
report['identicalUnoptimized'] = report['results'][2]['sha256'] == report['results'][3]['sha256']
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
markdown = ('# Custo da especialização escalar — alpha.2\n\n' + report['compiler'] + '; ' + report['platform'] + '.\n\n'
            f'{count} chamadas por execução, {args.samples} amostras intercaladas após aquecimento, '
            'com saídas conferidas pela fórmula 3*N*(N-1)/2+7*N. Compilação e execução incluem início do processo.\n\n'
            '| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |\n'
            '| --- | ---: | ---: | ---: | ---: |\n')
for r in report['results']:
    markdown += f'| {r["variant"]} | {r["medianMs"]:.3f} | {min(r["samplesMs"]):.3f}–{max(r["samplesMs"]):.3f} | {r["binaryBytes"]} | {r["compileMedianMs"]:.3f} |\n'
markdown += ('\nOs fontes e hashes estão no JSON adjacente. Esta carga mede uma especialização int; '
             'não mede RAM, explosão de combinações, structs, closures ou aplicações reais. '
             'Não sustenta uma conclusão geral de desempenho ou paridade com C/C++.\n'
             f'\nBinários manual/genérico idênticos: otimizado={report["identicalOptimized"]}; sem otimização={report["identicalUnoptimized"]}. '
             'Quando os bytes são iguais, diferenças de time refletem variação de execução, não código diferente devido a generics.\n')
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

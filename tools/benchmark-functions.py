"""Measure direct calls, function values and generic higher-order calls.

Interleaved samples with formula-checked output, including process startup.
Does not measure RAM, closures, collection pipelines or a complete application.
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
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not 3 <= args.samples <= 30:
    parser.error('Use de 3 a 30 amostras')
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
count = 5_000_000
expected = str(3 * count * (count - 1) // 2 + 7 * count) + '\n'


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


variants = [(name + suffix, call, flags) for suffix, flags in [('', []), ('-sem-opt', ['--no-opt'])]
            for name, call in [('direta', 'calcular(i)'), ('indireta', 'f(i)'),
                               ('ordem-superior', 'aplicar::<int>(f,i)')]]
report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=count, includesProcessStartup=True, expected=expected.strip(),
              compiler=run([compiler, 'version']).strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(), results=[])
with tempfile.TemporaryDirectory(prefix='assis-functions-bench-') as temp:
    folder = Path(temp)
    source = folder / 'mesmo.assis'
    for name, call, flags in variants:
        text = ('assis assis_assis():int{val f:pure assis(int):int=calcular;let total:int=0;'
                f'for(let i:int=0;i<{count};i+=1){{total+={call};}}'
                'print(total);return 0;}\n'
                'pure assis calcular(n:int):int{return n*3+7;}\n'
                'pure assis aplicar<T>(f:pure assis(T):T,v:T):T{return f(v);}\n')
        report['results'].append(dict(variant=name, source=text, compileSamplesMs=[], samplesMs=[]))
    for sample in range(args.samples + 1):
        for index in [(sample + j) % len(variants) for j in range(len(variants))]:
            name, call, flags = variants[index]
            record = report['results'][index]
            source.write_text(record['source'], encoding='utf-8')
            binary = folder / (name + ('.exe' if os.name == 'nt' else ''))
            start = time.perf_counter_ns()
            run([compiler, 'build', source, '-o', binary, *flags])
            compiled = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual = run([binary])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if actual != expected:
                raise AssertionError(name + ': saída diferente da fórmula independente')
            data = binary.read_bytes()
            record.update(binaryBytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            if sample:
                record['compileSamplesMs'].append(compiled)
                record['samplesMs'].append(elapsed)
for record in report['results']:
    record['medianMs'] = statistics.median(record['samplesMs'])
    record['compileMedianMs'] = statistics.median(record['compileSamplesMs'])
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
markdown = ('# Custo de funções como valores — alpha.3\n\n' + report['compiler'] + '; ' + report['platform'] + '.\n\n'
            f'{count} chamadas, {args.samples} amostras intercaladas após aquecimento. '
            'Saída conferida por 3*N*(N-1)/2+7*N. Tempos incluem início do processo.\n\n'
            '| Variante | Mediana execução ms | Mín–máx ms | Bytes | Mediana compilação ms |\n'
            '| --- | ---: | ---: | ---: | ---: |\n')
for r in report['results']:
    markdown += f'| {r["variant"]} | {r["medianMs"]:.3f} | {min(r["samplesMs"]):.3f}–{max(r["samplesMs"]):.3f} | {r["binaryBytes"]} | {r["compileMedianMs"]:.3f} |\n'
markdown += ('\nChamadas indiretas acrescentam uma carga/endereço e salto; ordem superior inclui outra chamada. '
             'Não há inlining ou desvirtualização novos. Os fontes, amostras e hashes estão no JSON adjacente. '
             'Esta carga não mede RAM, coleções, closures ou aplicações reais, nem estabelece paridade com C/C++.\n')
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

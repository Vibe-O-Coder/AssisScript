"""Measure class specialization against handwritten classes, including growth.

Samples interleave builds/runs. Includes process startup; does not measure RAM.
Each program prints an independently calculated integer sum.
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
iterations = 1_000_000
expected = str(3 * iterations * (iterations - 1) // 2 + 7 * iterations) + '\n'


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def program(count, generic):
    body, declarations = [], []
    for i in range(count):
        declarations.append(f'struct Tag{i}{{let marcador:int;}}')
        name = f'Caixa<Tag{i}>' if generic else f'Caixa{i}'
        body.append(f'let c{i}:{name}=new {name}();')
        if not generic:
            declarations.append(f'ASSIS Caixa{i}{{let value:Tag{i};'
                                f'assis ler(v:Tag{i}):Tag{i}{{return v;}}'
                                'assis calcular(v:int):int{return v*3+7;}}')
    if generic:
        declarations.append('ASSIS Caixa<T>{let value:T;assis ler(v:T):T{return v;}'
                            'assis calcular(v:int):int{return v*3+7;}}')
    body.append('let total:int=0;'
                f'for(let i:int=0;i<{iterations};i+=1){{total+=c0.calcular(i);}}print(total);')
    body.extend(f'free(c{i});' for i in range(count))
    return 'assis assis_assis():int{' + ''.join(body) + 'return 0;}\n' + '\n'.join(declarations)


report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=iterations, includesProcessStartup=True, expected=expected.strip(),
              compiler=run([compiler, 'version']).strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(), results=[])
for count in [1, 8, 32, 64]:
    for flags in [[], ['--no-opt']]:
        for generic in [False, True]:
            label = ('generico' if generic else 'manual') + ('-sem-opt' if flags else '')
            report['results'].append(dict(variant=label, instances=count, flags=flags,
                                          source=program(count, generic), compileSamplesMs=[], samplesMs=[]))
with tempfile.TemporaryDirectory(prefix='assis-classes-bench-') as temp:
    directory = Path(temp)
    source = directory / 'mesmo.assis'
    for sample in range(args.samples + 1):
        print(f'Amostra {sample}/{args.samples} (0 = aquecimento)', flush=True)
        for offset in range(len(report['results'])):
            index = (sample + offset) % len(report['results'])
            record = report['results'][index]
            source.write_text(record['source'], encoding='utf-8')
            binary = directory / ('programa.exe' if os.name == 'nt' else 'programa')
            start = time.perf_counter_ns()
            run([compiler, 'build', source, '-o', binary, *record['flags']])
            compiled = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual = run([binary])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if actual != expected:
                raise AssertionError('Saída diferente da fórmula independente')
            data = binary.read_bytes()
            record['binaryBytes'] = len(data)
            record['sha256'] = hashlib.sha256(data).hexdigest()
            if sample:
                record['compileSamplesMs'].append(compiled)
                record['samplesMs'].append(elapsed)
for r in report['results']:
    r['medianMs'] = statistics.median(r['samplesMs'])
    r['compileMedianMs'] = statistics.median(r['compileSamplesMs'])
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
markdown = ('# Custo de classes especializadas — alpha.4\n\n' + report['compiler'] + '; ' + report['platform'] + '.\n\n'
            f'{iterations} chamadas virtuais por execução, {args.samples} amostras intercaladas após aquecimento. '
            'Cada programa aloca/libera 1/8/32/64 objetos de tipos distintos e confere a soma pela fórmula '
            '`3*N*(N-1)/2+7*N`. Compilação e execução incluem início do processo.\n\n'
            '| Variante | Instâncias | Execução mediana ms | Mín–máx ms | Bytes | Compilação mediana ms |\n'
            '| --- | ---: | ---: | ---: | ---: | ---: |\n')
for r in report['results']:
    markdown += f'| {r["variant"]} | {r["instances"]} | {r["medianMs"]:.3f} | {min(r["samplesMs"]):.3f}–{max(r["samplesMs"]):.3f} | {r["binaryBytes"]} | {r["compileMedianMs"]:.3f} |\n'
markdown += ('\nFontes, amostras e hashes estão no JSON adjacente. Esta carga mede especialização nominal e '
             'crescimento de código/métodos; o laço usa apenas a primeira classe. As classes manuais têm as mesmas '
             'assinaturas concretas, com o mesmo despacho virtual existente. Não há desvirtualização ou novo inlining. '
             'Não mede RAM, recursos proprietários, coleções funcionais nem aplicações reais e não sustenta paridade geral com C/C++.\n')
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

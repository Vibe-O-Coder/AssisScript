"""Compare collection AST specialization to a supplied previous compiler.

The workload checks an integer formula. Startup is included; runtime timings
are not a general throughput measurement. RAM is not measured.
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
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--samples', type=int, default=7)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not 3 <= args.samples <= 30:
    parser.error('Use de 3 a 30 amostras')
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
baseline = args.baseline.resolve()
iterations = 2_000
expected = str(2 * (3 * iterations * (iterations - 1) // 2 + 7 * iterations)) + '\n'


def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def program(count):
    declarations, body = [], ['let a:Array<int>=[];let m:HashMap<int,int>=new HashMap<int,int>();']
    for i in range(count):
        declarations.append(f'struct Tag{i}{{let marcador:int;}}')
        body.append(f'let a{i}:Array<Tag{i}>=[];let m{i}:HashMap<int,Tag{i}>=new HashMap<int,Tag{i}>();')
    body.append(f'for(let i:int=0;i<{iterations};i+=1){{a.push(i*3+7);m.set(i,i*3+7);}}'
                f'let total:int=0;for(let i:int=0;i<{iterations};i+=1){{total+=a[i]+m.get(i);}}print(total);')
    body.extend(f'free(a{i});free(m{i});' for i in range(count))
    body.append('free(a);free(m);return 0;')
    return 'assis assis_assis():int{' + ''.join(body) + '}\n' + '\n'.join(declarations)


report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=iterations, includesProcessStartup=True, expected=expected.strip(),
              compiler=run([compiler, 'version']).strip(),
              baseline=run([baseline, 'version']).strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              baselineSha256=hashlib.sha256(baseline.read_bytes()).hexdigest(), results=[])
progress = json.loads((ROOT / 'docs/PROGRESSO.json').read_text(encoding='utf-8'))
credits = {'complete': 1, 'partial': 0.5, 'pending': 0}
report['completionEstimatePercent'] = int(sum(p['weight'] * sum(credits[i['status']] for i in p['items']) / len(p['items']) for p in progress['phases']) + 0.5)
report['completionMetricVersion'] = progress['version']
for count in [1, 8, 32, 64]:
    for flags in [[], ['--no-opt']]:
        for label in ['alpha4', 'alpha5']:
            report['results'].append(dict(variant=label, nominalTypes=count, flags=flags,
                                          source=program(count), compileSamplesMs=[], samplesMs=[]))
with tempfile.TemporaryDirectory(prefix='assis-collections-bench-') as temp:
    directory = Path(temp)
    source, binary = directory / 'mesmo.assis', directory / ('programa.exe' if os.name == 'nt' else 'programa')
    for sample in range(args.samples + 1):
        print(f'Amostra {sample}/{args.samples} (0 = aquecimento)', flush=True)
        for offset in range(len(report['results'])):
            index = (sample + offset) % len(report['results'])
            record = report['results'][index]
            source.write_text(record['source'], encoding='utf-8')
            selected = baseline if record['variant'] == 'alpha4' else compiler
            start = time.perf_counter_ns()
            run([selected, 'build', source, '-o', binary, *record['flags']])
            compiled = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual = run([binary])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if actual != expected:
                raise AssertionError('Saída diferente da fórmula independente')
            data = binary.read_bytes()
            record['binaryBytes'], record['sha256'] = len(data), hashlib.sha256(data).hexdigest()
            if sample:
                record['compileSamplesMs'].append(compiled); record['samplesMs'].append(elapsed)
for r in report['results']:
    r['medianMs'] = statistics.median(r['samplesMs'])
    r['compileMedianMs'] = statistics.median(r['compileSamplesMs'])
report['comparisons'] = []
for i in range(0, len(report['results']), 2):
    old, new = report['results'][i:i+2]
    report['comparisons'].append(dict(nominalTypes=old['nominalTypes'], flags=old['flags'],
                                      identicalBinary=old['sha256'] == new['sha256'],
                                      compileMedianChangePercent=100 * (new['compileMedianMs'] / old['compileMedianMs'] - 1)))
report['allBinariesIdentical'] = all(c['identicalBinary'] for c in report['comparisons'])
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
markdown = ('# Migração AST das coleções — alpha.5\n\n' + report['compiler'] + '; ' + report['platform'] + '.\n\n'
            'Base: ' + report['baseline'] + '.\n\n'
            f'Conclusão estimada do plano nesta entrega: **{report["completionEstimatePercent"]}%**, pela [régua de progresso](../../docs/PROGRESSO.md). A porcentagem mede atendimento do plano e não desempenho.\n\n'
            f'{args.samples} amostras intercaladas após aquecimento, com/sem otimização. '
            'Cada kind nominal acrescenta Array<Tag> e HashMap<int,Tag>; há também Array<int>/HashMap<int,int>. '
            f'O laço usa {iterations} elementos e confere `2*(3*N*(N-1)/2+7*N)`. '
            'Compilação e execução incluem início de processo.\n\n'
            '| Compilador | Tipos nominais | Modo | Compilação mediana ms | Execução mediana ms | Mín–máx execução ms | Bytes |\n'
            '| --- | ---: | --- | ---: | ---: | ---: | ---: |\n')
for r in report['results']:
    mode = 'sem opt' if r['flags'] else 'opt'
    markdown += f'| {r["variant"]} | {r["nominalTypes"]} | {mode} | {r["compileMedianMs"]:.3f} | {r["medianMs"]:.3f} | {min(r["samplesMs"]):.3f}–{max(r["samplesMs"]):.3f} | {r["binaryBytes"]} |\n'
markdown += ('\nFontes, hashes e amostras no JSON adjacente. A carga exercita especializações distintas e '
             'crescimento de código, com operações escalares de coleção. Não mede RAM, vidas entre funções, '
             'estruturas persistentes, textos grandes ou aplicações reais. Tempos de execução incluem startup e '
             'não sustentam uma conclusão de desempenho geral. Layout, hashing, bounds e algorithms são preservados.\n')
markdown += f'\nTodos os pares de executáveis são idênticos byte a byte: {report["allBinariesIdentical"]}. Quando os bytes coincidem, variações no time de execução não correspondem a alterações no código emitido.\n'
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

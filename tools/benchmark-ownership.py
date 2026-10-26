"""Compare explicit cleanup with owned returns, loans and composite drops.

Baseline is alpha.5; independent output N*N, alternating variants, one warmup.
Process startup is included; peak working set/RSS measured separately per child.
"""
import argparse
import ctypes
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
parser.add_argument('--baseline', type=Path, help='Alpha.5 opcional; sem ele mede apenas referência manual current vs own')
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--samples', default=7, type=int)
parser.add_argument('--iterations', default=200_000, type=int)
args = parser.parse_args()
assert 3 <= args.samples <= 30
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
baseline = args.baseline.resolve() if args.baseline else compiler
count = args.iterations
assert 1 <= count <= 10_000_000
expected = f'{count * count}\n'

def run(command):
    p = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=120)
    if p.returncode:
        raise AssertionError((command, p.returncode, p.stdout, p.stderr))
    return p.stdout

manual = '''struct Caixa{let data:Array<int>;}
assis calcular(n:int):int{let r:Caixa=new Caixa([n,n+1]);
let total:int=r.data[0]+r.data[1];free(r.data);free(r);return total;}
'''
managed = '''struct Caixa{own data:Array<int>;}
safe assis create(n:int):own Caixa{return new Caixa([n,n+1]);}
safe assis ler(borrow r:Caixa):int{return r.data[0]+r.data[1];}
safe assis calcular(n:int):int{own r:Caixa=create(n);return ler(r);}
'''
entry = f'''assis assis_assis():int{{let total:int=0;
for(let i:int=0;i<{count};i+=1){{total+=calcular(i);}}print(total);return 0;}}
'''
implementations = [('alpha5-manual', baseline, manual), ('alpha6-manual', compiler, manual), ('alpha6-own', compiler, managed)] if args.baseline else [('current-manual', compiler, manual), ('current-own', compiler, managed)]
variants = [(name + suffix, cc, code + entry, flags)
            for suffix, flags in [('', []), ('-sem-opt', ['--no-opt'])]
            for name, cc, code in implementations]
progress = json.loads((ROOT / 'docs/PROGRESSO.json').read_text(encoding='utf-8'))
credits = dict(complete=1, partial=.5, pending=0)
points = sum(p['weight'] * sum(credits[i['status']] for i in p['items']) / len(p['items']) for p in progress['phases'])
report = dict(platform=platform.platform(), cpu=platform.processor(), iterations=count, samples=args.samples,
              includesProcessStartup=True, expected=expected.strip(), compiler=run([compiler, 'version']).strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              baselineSha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
              baselineVersion=run([baseline, 'version']).strip(), historicalBaseline=bool(args.baseline),
              completionMetricVersion=progress['version'], completionEstimatePercent=int(points + .5),
              peakMemoryMetric='PeakWorkingSetSize bytes' if os.name == 'nt' else 'maximum resident set KiB converted to bytes', results=[])

def peak_memory(binary, folder):
    if os.name == 'nt':
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in ['peak', 'working', 'quotaPeakPaged', 'quotaPaged', 'quotaPeakNonPaged', 'quotaNonPaged', 'pagefile', 'peakPagefile', 'private']]
        p = subprocess.Popen([str(binary)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=120)
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        query = ctypes.WinDLL('psapi').GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        query.restype = wintypes.BOOL
        if not query(int(p._handle), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError()
        assert p.returncode == 0 and out.decode() == expected and not err
        return counters.peak
    measurement = folder / 'rss.txt'
    actual = run(['/usr/bin/time', '-f', '%M', '-o', measurement, binary])
    assert actual == expected
    return int(measurement.read_text().strip()) * 1024

with tempfile.TemporaryDirectory(prefix='assis-ownership-bench-') as temp:
    folder = Path(temp)
    source = folder / 'mesmo.assis'
    for name, cc, code, flags in variants:
        report['results'].append(dict(variant=name, source=code, compileSamplesMs=[], samplesMs=[], peakMemoryBytes=[]))
    for sample in range(args.samples + 1):
        for index in [(sample + i) % len(variants) for i in range(len(variants))]:
            name, cc, code, flags = variants[index]
            record = report['results'][index]
            source.write_text(code, encoding='utf-8')
            binary = folder / (name + ('.exe' if os.name == 'nt' else ''))
            start = time.perf_counter_ns()
            run([cc, 'build', source, '-o', binary, *flags])
            compile_ms = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual = run([binary])
            elapsed = (time.perf_counter_ns() - start) / 1e6
            assert actual == expected, (name, actual)
            if sample:
                record['samplesMs'].append(elapsed)
                record['compileSamplesMs'].append(compile_ms)
                record['peakMemoryBytes'].append(peak_memory(binary, folder))
            record.update(binaryBytes=binary.stat().st_size, sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    # Debug independently checks that all three variants finish without live allocations.
    for name, cc, code, flags in variants:
        source.write_text(code, encoding='utf-8')
        assert run([cc, 'run', source, '--debug', *flags]) == expected
for record in report['results']:
    record.update(medianMs=statistics.median(record['samplesMs']),
                  compileMedianMs=statistics.median(record['compileSamplesMs']),
                  peakMemoryMedianBytes=statistics.median(record['peakMemoryBytes']))
if args.baseline:
    report['manualBinaryIdentity'] = {suffix or 'optimized': next(r['sha256'] for r in report['results'] if r['variant'] == 'alpha5-manual' + suffix) == next(r['sha256'] for r in report['results'] if r['variant'] == 'alpha6-manual' + suffix) for suffix in ['', '-sem-opt']}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
markdown = f'''# Custo de ownership entre funções — alpha.6

{report['compiler']}; {report['platform']}. {count} registros/arrays por execução;
{args.samples} amostras intercaladas após aquecimento. Saída independente N² = {expected.strip()}.
Inclui início de processo. RAM é pico por processo; não mede retenção prolongada.

| Variante | Mediana ms | Mín–máx ms | Compilação ms | Bytes executável | Mediana pico bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
for r in report['results']:
    markdown += f'| {r["variant"]} | {r["medianMs"]:.3f} | {min(r["samplesMs"]):.3f}–{max(r["samplesMs"]):.3f} | {r["compileMedianMs"]:.3f} | {r["binaryBytes"]} | {r["peakMemoryMedianBytes"]:.0f} |\n'
markdown += ('\nA variante own faz chamadas adicionais create/ler e uma chamada de destruição composta. '
             'A diferença não isola o custo de análise estática. Não há nova otimização de chamadas. '
             'Pico de RAM depende do OS; as métricas Windows/Linux não são diretamente equivalentes. '
             'Não demonstra aplicações A/B/C, 24 horas de estabilidade nem paridade com C/C++. '
             'Fontes, amostras e hashes no JSON adjacente. --debug terminou sem alocações vivas em todas as variantes.\n')
if args.baseline:
    markdown += '\nIdentidade byte a byte das referências manuais alpha.5/alpha.6: ' + json.dumps(report['manualBinaryIdentity']) + '. Diferenças entre tempos de arquivos idênticos refletem variação da medição.\n'
args.output.with_suffix('.md').write_text(markdown, encoding='utf-8')
print(markdown)

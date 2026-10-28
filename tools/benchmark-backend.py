"""Interleaved backend comparisons with independent Python output references."""
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
parser.add_argument('--compiler', type=Path, default=ROOT/'bin'/('assis.exe' if os.name == 'nt' else 'assis'))
parser.add_argument('--baseline', type=Path, help='Preserved compiler; otherwise compare the current AST --no-opt emitter')
parser.add_argument('--samples', type=int, default=7)
parser.add_argument('--iterations', type=int, default=2000000)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.samples < 3 or args.iterations < 100000:
    parser.error('At least three samples and 100000 iterations are required')
n = args.iterations
main = lambda body: 'safe fn main():int{'+body+'return 0;}'
scopes = 'let total:int=0;'
for k in range(12):
    scopes += f'{{let sum{k}:int=0;for(let index{k}:int=0;index{k}<{n};index{k}+=1){{sum{k}+=index{k}+{k};}}total+=sum{k};}}'
size = 8192
rounds = max(100, n//1024)
programs = {
    'disjoint_loops': (main(scopes+'print(total);'), 12*n*(n-1)//2+sum(range(12))*n),
    'stencil_offsets': (main(f'own a:*int=alloc<int>({size});for(let i:int=0;i<len(a);i+=1){{a[i]=i;}}'
        f'let sum:int=0;for(let r:int=0;r<{rounds};r+=1){{for(let i:int=1;i<len(a)-1;i+=1){{sum+=a[i-1]+a[i]+a[i+1];}}}}print(sum);'),
        rounds*3*(size-2)*(size-1)//2),
    'reverse_traversal': (main(f'own a:Array<int>=new Array<int>();for(let i:int=0;i<{size};i+=1){{a.push(i);}}'
        f'let sum:int=0;for(let r:int=0;r<{rounds};r+=1){{for(let i:int=len(a)-1;i>=0;i-=1){{sum+=a[i];}}}}print(sum);'),
        rounds*size*(size-1)//2),
    'scalar_leaf': ('pure fn step(n:int):int{return n*3+1;}'+main(f'let sum:int=0;for(let i:int=0;i<{n*8};i+=1){{sum+=step(i);}}print(sum);'),
        3*(n*8)*(n*8-1)//2+n*8),
    'float_values': (main(f'let sum:f64=0.0;for(let i:int=0;i<{n*8};i+=1){{sum+=0.5;}}print(int(sum));'), n*4),
}
compilers = {'candidate': args.compiler.resolve(), 'baseline': (args.baseline or args.compiler).resolve()}
report = dict(format='AssisScript-backend-v1', host=dict(system=platform.platform(), machine=platform.machine(),
    processor=platform.processor(), logicalCpus=os.cpu_count()), samples=args.samples, iterations=n,
    reference='Python integer formulas; both compilers checked before and during measurement', compilers={}, workloads={})
for name, compiler in compilers.items():
    report['compilers'][name] = dict(sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
        version=subprocess.check_output([compiler, 'version'], text=True).strip(), mode='--no-opt' if name == 'baseline' and args.baseline is None else 'optimized')
with tempfile.TemporaryDirectory(prefix='assis-backend-perf-') as temp:
    folder = Path(temp)
    for name, (source, expected) in programs.items():
        path = folder/(name+'.assis');path.write_text(source, encoding='utf-8')
        metrics = {};binaries = {}
        for label, compiler in compilers.items():
            binary = folder/(name+'-'+label+('.exe' if os.name == 'nt' else ''))
            start = time.perf_counter_ns()
            flags=['--no-opt'] if label == 'baseline' and args.baseline is None else []
            result = subprocess.run([compiler, 'build', path, '--safe', *flags, '-o', binary], capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stderr
            metrics[label] = dict(compileMs=(time.perf_counter_ns()-start)/1e6, bytes=binary.stat().st_size,
                binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(), runMs=[])
            binaries[label] = binary
            result = subprocess.run([binary], capture_output=True, text=True, timeout=60)
            assert (result.returncode, result.stdout, result.stderr) == (0, str(expected)+'\n', ''), (name, label, result)
        for sample in range(args.samples):
            labels = list(compilers) if sample % 2 == 0 else list(reversed(compilers))
            for label in labels:
                start = time.perf_counter_ns()
                result = subprocess.run([binaries[label]], capture_output=True, text=True, timeout=60)
                metrics[label]['runMs'].append((time.perf_counter_ns()-start)/1e6)
                assert (result.returncode, result.stdout, result.stderr) == (0, str(expected)+'\n', '')
        for value in metrics.values():
            value['medianMs'] = statistics.median(value['runMs'])
            value['minMs'] = min(value['runMs']);value['maxMs'] = max(value['runMs'])
        speedup = metrics['baseline']['medianMs']/metrics['candidate']['medianMs']
        report['workloads'][name] = dict(expected=expected, sourceSha256=hashlib.sha256(source.encode()).hexdigest(),
            measurements=metrics, speedup=speedup)
        print(f'{name}: {speedup:.3f}x', flush=True)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
lines = ['# Backend comparison — alpha.15', '',
    f'{args.samples} interleaved samples, one warmup, {n} base iterations. Times include process startup.', '',
    '| Workload | Candidate median (ms) | Reference median (ms) | Speedup |', '| --- | ---: | ---: | ---: |']
for name, record in report['workloads'].items():
    m = record['measurements']
    lines.append(f'| {name} | {m["candidate"]["medianMs"]:.3f} | {m["baseline"]["medianMs"]:.3f} | {record["speedup"]:.3f}x |')
lines += ['', 'Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.',
    'These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.']
args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')

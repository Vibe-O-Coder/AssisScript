"""Compare heap/reference values with Copy values and measure bounded native CSV IO."""
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
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--baseline', type=Path)
parser.add_argument('--baseline-label', default='alpha6')
parser.add_argument('--samples', type=int, default=7)
parser.add_argument('--iterations', type=int, default=200_000)
parser.add_argument('--csv-rows', type=int, default=1_000_000)
args = parser.parse_args()
assert 3 <= args.samples <= 30 and 1000 <= args.iterations <= 10_000_000
assert 1000 <= args.csv_rows <= 10_000_000
compiler = ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')


legacy_support = {}

def run(command, expected=None):
    if len(command)>1 and command[1] in ("build","run","check") and "--safe" not in command and "--legacy" not in command:
        key=str(command[0])
        if key not in legacy_support:legacy_support[key]=b"--legacy" in subprocess.check_output([command[0],"help"])
        if legacy_support[key]:command=[*command,"--legacy"]
    p = subprocess.run(list(map(str, command)), capture_output=True, timeout=120)
    assert p.returncode == 0 and not p.stderr, (command, p.returncode, p.stderr.decode(errors='replace'))
    if expected is not None:
        assert p.stdout == expected, (p.stdout, expected)
    return p.stdout


def peak_memory(command, expected, folder):
    if os.name == 'nt':
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in ['peak', 'working', 'quotaPeakPaged', 'quotaPaged', 'quotaPeakNonPaged', 'quotaNonPaged', 'pagefile', 'peakPagefile', 'private']]
        p = subprocess.Popen(list(map(str, command)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=120)
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        query = ctypes.WinDLL('psapi').GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        query.restype = wintypes.BOOL
        if not query(int(p._handle), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError()
        assert p.returncode == 0 and out == expected and not err
        return counters.peak
    file = folder / 'rss.txt'
    run(['/usr/bin/time', '-f', '%M', '-o', file, *command], expected)
    # Some hosts report zero RSS for very short processes; keep that measurement explicit.
    return int(file.read_text().strip()) * 1024


progress = json.loads((ROOT / 'docs/PROGRESSO.json').read_text(encoding='utf-8'))
credit = dict(complete=1, partial=.5, pending=0)
points = sum(p['weight'] * sum(credit[i['status']] for i in p['items']) / len(p['items']) for p in progress['phases'])
report = dict(platform=platform.platform(), cpu=platform.processor(), samples=args.samples,
              iterations=args.iterations, compiler=run([compiler, 'version']).decode().strip(),
              compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              completionMetricVersion=progress['version'], completionEstimatePercent=int(points + .5),
              peakMemoryMetric='PeakWorkingSetSize bytes' if os.name == 'nt' else 'maximum resident set KiB converted to bytes; zero means unobserved for a short process',
              includesProcessStartup=True, results=[], csv=[], startup=[])
heap = 'struct Par{let x:int;let y:int;}fn item(n:int):own Par{return new Par(n,n+1);}'
value = 'value struct Par{let x:int;let y:int;}pure fn item(n:int):Par{return new Par(n,n+1);}'
body = 'fn main():int{let total:int=0;for(let i:int=0;i<N;i+=1){BIND p:Par=item(i);total+=p.x+p.y;}print(total);return 0;}'
definitions = [('current-heap', compiler, heap + body.replace('BIND', 'own')), ('current-value', compiler, value + body.replace('BIND', 'val'))]
if args.baseline:
    definitions.insert(0, (args.baseline_label+'-heap', args.baseline.resolve(), heap + body.replace('BIND', 'own')))
    report['baselineSha256'] = hashlib.sha256(args.baseline.read_bytes()).hexdigest()
variants = [(name+suffix, cc, source.replace('N;', str(args.iterations)+';'), flags)
            for suffix, flags in [('', []), ('-sem-opt', ['--no-opt'])] for name, cc, source in definitions]
expected = f'{args.iterations**2}\n'.encode()
with tempfile.TemporaryDirectory(prefix='assis-values-io-', ignore_cleanup_errors=True) as temp:
    folder = Path(temp)
    for name, cc, source, flags in variants:
        file, binary = folder/(name+'.assis'), folder/(name+'-debug'+('.exe' if os.name=='nt' else ''))
        file.write_text(source, encoding='utf-8')
        record = dict(variant=name, source=source, compileSamplesMs=[], samplesMs=[], peakMemoryBytes=[])
        run([cc, 'build', file, '-o', binary, '--debug', *flags]); run([binary], expected)
        report['results'].append(record)
    # Separate each output from a just-exited Windows image (which the OS/AV may still lock).
    for sample in range(args.samples):
        for i in [(sample+j)%len(variants) for j in range(len(variants))]:
            name, cc, source, flags=variants[i];record=report['results'][i]
            file=folder/(name+'.assis');binary=folder/(name+f'-{sample}'+('.exe' if os.name=='nt' else ''))
            start=time.perf_counter();run([cc,'build',file,'-o',binary,*flags]);record['compileSamplesMs'].append((time.perf_counter()-start)*1000)
            record['binaryBytes']=binary.stat().st_size
            record['binarySha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
            record['path']=str(binary)
    # Interleave variants, checking the independent integer formula on every run.
    for sample in range(args.samples+1):
        for i in [(sample+j)%len(variants) for j in range(len(variants))]:
            record=report['results'][i]; binary=Path(record['path'])
            start=time.perf_counter();run([binary],expected);elapsed=(time.perf_counter()-start)*1000
            if sample: record['samplesMs'].append(elapsed)
    for record in report['results']:
        record['peakMemoryBytes']=[peak_memory([record['path']],expected,folder) for _ in range(args.samples)]
        record['medianMs']=statistics.median(record['samplesMs']);record['compileMedianMs']=statistics.median(record['compileSamplesMs'])
        del record['path']
    binary=folder/('relatorio.exe' if os.name=='nt' else 'relatorio')
    run([compiler,'build',ROOT/'exemplos/21_relatorio_csv_stream.assis','--safe','--debug','-o',binary])
    input_file,output=folder/'entrada á 日本.csv',folder/'saida á 日本.csv'
    for rows in [max(1000,args.csv_rows//10),args.csv_rows]:
        with input_file.open('wb') as f:
            f.write(b'value\n'); chunk=b'"1234567"\r\n'*1000
            for _ in range(rows//1000):f.write(chunk)
            f.write(b'"1234567"\r\n'*(rows%1000))
        expected_out=f'Registros {rows} total {1234567*rows}\n'.encode()
        record=dict(rows=rows,inputBytes=input_file.stat().st_size,samplesMs=[],peakMemoryBytes=[])
        for _ in range(args.samples):
            start=time.perf_counter();run([binary,input_file,output],expected_out);record['samplesMs'].append((time.perf_counter()-start)*1000)
            assert output.read_bytes()==f'registros,total\n{rows},{1234567*rows}\n'.encode()
            record['peakMemoryBytes'].append(peak_memory([binary,input_file,output],expected_out,folder))
        record['medianMs']=statistics.median(record['samplesMs']);record['outputSha256']=hashlib.sha256(output.read_bytes()).hexdigest()
        report['csv'].append(record)
    # Separate the fixed process/runtime cost, including Windows DLL/argument setup.
    startup_variants=[('current',compiler)]
    if args.baseline:startup_variants.insert(0,(args.baseline_label,args.baseline.resolve()))
    file=folder/'start.assis';file.write_text('fn main():int{print(0);return 0;}',encoding='utf-8')
    for name,cc in startup_variants:
        binary=folder/(name+'-start'+('.exe' if os.name=='nt' else ''))
        run([cc,'build',file,'-o',binary])
        report['startup'].append(dict(variant=name,samplesMs=[],peakMemoryBytes=[],path=str(binary)))
    for sample in range(args.samples+1):
        for i in [(sample+j)%len(startup_variants) for j in range(len(startup_variants))]:
            record=report['startup'][i];start=time.perf_counter();run([record['path']],b'0\n');elapsed=(time.perf_counter()-start)*1000
            if sample:record['samplesMs'].append(elapsed)
    for record in report['startup']:
        record['peakMemoryBytes']=[peak_memory([record['path']],b'0\n',folder) for _ in range(args.samples)]
        record['medianMs']=statistics.median(record['samplesMs']);del record['path']
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text='# Valores Copy e IO nativo — '+report['compiler']+'\n\n'
text+=f'{args.samples} amostras por variante; {args.iterations} iterações; início do processo incluído. Saída conferida por N².\n\n'
text+='| Variante | Compilar (ms) | Executar (ms) | Binário (bytes) | Pico de RAM (bytes) |\n| --- | ---: | ---: | ---: | ---: |\n'
for r in report['results']:text+=f'| {r["variant"]} | {r["compileMedianMs"]:.3f} | {r["medianMs"]:.3f} | {r["binaryBytes"]} | {max(r["peakMemoryBytes"])} |\n'
text+='\nA comparação heap/Copy altera representação e custo de alocação; não mede equivalência geral com C ou ganho universal. RSS zero em processo curto significa medição indisponível, não consumo zero.\n\n'
text+='| CSV (rows) | Entrada (bytes) | Mediana (ms) | Pico de RAM (bytes) |\n| --- | ---: | ---: | ---: |\n'
for r in report['csv']:text+=f'| {r["rows"]} | {r["inputBytes"]} | {r["medianMs"]:.3f} | {max(r["peakMemoryBytes"])} |\n'
text+='\nA CLI usa buffers fixos, verifica inteiros, errors e liberação em debug. Este ensaio local não é um teste de serviço prolongado ou de durabilidade contra queda de energia.\n'
text+='\n| Início/print/saída | Mediana (ms) | Pico de RAM (bytes) |\n| --- | ---: | ---: |\n'
for r in report['startup']:text+=f'| {r["variant"]} | {r["medianMs"]:.3f} | {max(r["peakMemoryBytes"])} |\n'
args.output.with_suffix('.md').write_text(text,encoding='utf-8')
print(args.output)

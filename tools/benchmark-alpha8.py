"""Preserve prior reports; compare alpha.7 and measure the new native features."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import statistics
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--samples',type=int,default=7)
parser.add_argument('--iterations',type=int,default=2_000_000)
parser.add_argument('--csv-rows',type=int,default=1_000_000)
args=parser.parse_args()
assert 3<=args.samples<=30 and 1000<=args.iterations<=10_000_000
with tempfile.TemporaryDirectory(prefix='assis-alpha8-bench-') as temp:
    folder=Path(temp);previous_argv=sys.argv
    sys.argv=[str(ROOT/'tools/benchmark-values-io.py'),'--output',str(folder/'baseline.json'),'--samples',str(args.samples),'--iterations',str(args.iterations),'--csv-rows',str(args.csv_rows),'--baseline-label','alpha7']
    if args.baseline:sys.argv+=['--baseline',str(args.baseline.resolve())]
    context=runpy.run_path(str(ROOT/'tools/benchmark-values-io.py'));sys.argv=previous_argv
    report=json.loads((folder/'baseline.json').read_text(encoding='utf-8'));report['nativeFeatures']=[]
    run=context['run'];peak=context['peak_memory'];compiler=context['compiler'];n=args.iterations
    document=b'{"value":[1,2,true,null,"acao"]}'
    json_n=max(1000,n//100)
    payload=''.join(f'b[{i}]=byte({c});' for i,c in enumerate(document))
    workloads=[
        ('f64',f'safe fn main():int{{let total:f64=0.0;for(let i:int=0;i<{n};i+=1){{total+=f64(i)*0.5;}}print(total);return 0;}}',float(n*(n-1)/4).hex().encode()+b'\n'),
        ('u32',f'safe fn main():int{{let total:u32=u32(0);for(let i:int=0;i<{n};i+=1){{total+=u32(i);}}print(total);return 0;}}',str((n*(n-1)//2)%(1<<32)).encode()+b'\n'),
        ('json','import "std/json.assis";\nsafe fn main():int{own b:*byte=alloc<byte>('+str(len(document))+');'+payload+f'for(let i:int=0;i<{json_n};i+=1){{assert(json::validate(b,{len(document)},64,4096).valid);}}print({json_n});return 0;}}',str(json_n).encode()+b'\n'),
        ('events','import "std/events.assis";\nsafe fn acao(borrow mut l:events::Loop,n:int):void{if(n<'+str(json_n)+'){assert(events::schedule(l,0,n+1,acao)>0);}}safe fn main():int{own l:events::Loop=events::create(1);assert(events::schedule(l,0,1,acao)>0);print(events::run(l,'+str(json_n)+'));return 0;}',str(json_n).encode()+b'\n')
    ]
    records=[]
    for name,source,expected in workloads:
        for suffix,flags in [('',[]),('-sem-opt',['--no-opt'])]:
            label=name+suffix;file=folder/(label+'.assis');file.write_text(source,encoding='utf-8');binary=folder/(label+('.exe' if os.name=='nt' else ''))
            run([compiler,'build',file,'--safe','--debug','-o',binary,*flags]);run([binary],expected)
            record=dict(variant=label,source=source,compileSamplesMs=[],samplesMs=[],peakMemoryBytes=[],expectedStdout=expected.decode(),binaryBytes=0)
            records.append((record,file,binary,flags,expected))
    for sample in range(args.samples):
        for index in [(sample+j)%len(records) for j in range(len(records))]:
            record,file,binary,flags,expected=records[index]
            binary=folder/(record['variant']+f'-{sample}'+('.exe' if os.name=='nt' else ''))
            start=time.perf_counter();run([compiler,'build',file,'--safe','-o',binary,*flags]);record['compileSamplesMs'].append((time.perf_counter()-start)*1000)
            record['binaryBytes']=binary.stat().st_size;record['binarySha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
            records[index]=(record,file,binary,flags,expected)
    for sample in range(args.samples+1):
        for index in [(sample+j)%len(records) for j in range(len(records))]:
            record,file,binary,flags,expected=records[index];start=time.perf_counter();run([binary],expected);elapsed=(time.perf_counter()-start)*1000
            if sample:record['samplesMs'].append(elapsed)
    for record,file,binary,flags,expected in records:
        record['peakMemoryBytes']=[peak([binary],expected,folder) for _ in range(args.samples)]
        record['medianMs']=statistics.median(record['samplesMs']);record['compileMedianMs']=statistics.median(record['compileSamplesMs']);report['nativeFeatures'].append(record)
    report['benchmarkScope']='alpha.7 legacy heap/startup comparison, current Copy, bounded CSV, IEEE f64, modular u32, bounded JSON and cooperative events; no 24-hour or concurrency claim'
    report['runtimeSourceHashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').glob('runtime*')) if p.is_file()}
    if sys.platform.startswith('linux'):
        report['cpuModel']=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),'unknown')
    else:report['cpuModel']=platform.processor()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    text='# Evolução alpha.8 — '+report['compiler']+'\n\n'+(folder/'baseline.md').read_text(encoding='utf-8')
    text+='\n## Novos recursos nativos\n\n| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |\n| --- | ---: | ---: | ---: | ---: |\n'
    for r in report['nativeFeatures']:text+=f'| {r["variant"]} | {r["compileMedianMs"]:.3f} | {r["medianMs"]:.3f} | {r["binaryBytes"]} | {max(r["peakMemoryBytes"])} |\n'
    text+='\nSaídas conferidas por fórmulas independentes e contratos de JSON/events, em debug e nos dois modos. Não há baseline histórico para tipos/APIs que a alpha.7 não admite. Custos de iniciar processo estão incluídos; RAM zero de processo curto significa indisponível. Sem ganho geral prometido.\n'
    args.output.with_suffix('.md').write_text(text,encoding='utf-8',newline='\n')
    print(args.output)

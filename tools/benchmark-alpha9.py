"""Compare unchanged workloads with alpha.8 and measure managed native APIs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import statistics
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
with tempfile.TemporaryDirectory(prefix='assis-alpha9-bench-') as temp:
    folder=Path(temp)
    sys.argv=[str(ROOT/'tools/benchmark-values-io.py'),'--output',str(folder/'base.json'),'--samples',str(args.samples),'--iterations',str(args.iterations),'--csv-rows',str(args.csv_rows),'--baseline-label','alpha8']
    if args.baseline:sys.argv+=['--baseline',str(args.baseline.resolve())]
    context=runpy.run_path(str(ROOT/'tools/benchmark-values-io.py'))
    report=json.loads((folder/'base.json').read_text(encoding='utf-8'))
    compiler=context['compiler'];run=context['run'];peak=context['peak_memory'];n=args.iterations
    rounds=max(10,n//1024)
    workloads=[
        ('slice',f'safe assis assis_assis():int{{own b:*int=alloc<int>({n});for(let i:int=0;i<{n};i+=1){{b[i]=i;}}borrow s:slice<int>=fatia(b,0,{n});let total:int=0;for(let i:int=0;i<len(s);i+=1){{total+=s[i];}}print(total);return 0;}}',str(n*(n-1)//2)+'\n'),
        ('unicode','#yuri <std/unicode.assis>\nsafe assis assis_assis():int{own b:*byte=alloc<byte>(1024);for(let i:int=0;i<1024;i+=1){b[i]=byte(65);}own t:unicode::Texto=new unicode::Texto();let total:int=0;for(let i:int=0;i<'+str(rounds)+';i+=1){assert(t.carregar(fatia(b,0,1024)));total+=t.tamanho();}print(total);return 0;}',str(rounds*1024)+'\n'),
        ('proprios','#yuri <std/proprios.assis>\nstruct R{own b:*byte;}safe assis assis_assis():int{let total:int=0;for(let i:int=0;i<'+str(rounds)+';i+=1){own l:proprios::Lista<R>=new proprios::Lista<R>();for(let j:int=0;j<128;j+=1){l.inserir(new R(alloc<byte>(16)));}total+=l.tamanho();}print(total);return 0;}',str(rounds*128)+'\n')
    ]
    records=[]
    for name,source,expected in workloads:
        for flags in [[],['--no-opt']]:
            label=name+('-sem-opt' if flags else '');file=folder/(label+'.assis');file.write_text(source,encoding='utf-8');binary=folder/(label+('.exe' if os.name=='nt' else ''))
            expected=expected.encode() if isinstance(expected,str) else expected
            run([compiler,'build',file,'--safe','--debug','-o',binary,*flags]);run([binary],expected)
            record=dict(variant=label,source=source,expectedStdout=expected.decode(),compileSamplesMs=[],samplesMs=[],peakMemoryBytes=[])
            records.append((record,file,binary,flags,expected))
    for sample in range(args.samples):
        for index in [(sample+j)%len(records) for j in range(len(records))]:
            record,file,binary,flags,expected=records[index];start=time.perf_counter();run([compiler,'build',file,'--safe','-o',binary,*flags]);record['compileSamplesMs'].append((time.perf_counter()-start)*1000)
            record['binaryBytes']=binary.stat().st_size;record['binarySha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    for sample in range(args.samples+1):
        for index in [(sample+j)%len(records) for j in range(len(records))]:
            record,file,binary,flags,expected=records[index];start=time.perf_counter();run([binary],expected);elapsed=(time.perf_counter()-start)*1000
            if sample:record['samplesMs'].append(elapsed)
    report['nativeFeatures']=[]
    for record,file,binary,flags,expected in records:
        record['peakMemoryBytes']=[peak([binary],expected,folder) for _ in range(args.samples)];record['medianMs']=statistics.median(record['samplesMs']);record['compileMedianMs']=statistics.median(record['compileSamplesMs']);report['nativeFeatures'].append(record)
    report['benchmarkScope']='alpha.8 comparable workloads; current bounded slices, UTF-8 snapshots and ownership lists; no network, concurrency or 24-hour claim'
    report['sourceHashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ['src','stdlib'] for p in sorted((ROOT/directory).glob('*')) if p.is_file()}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    text='# Evolução alpha.9 — '+report['compiler']+'\n\n'+(folder/'base.md').read_text(encoding='utf-8')
    text+='\n## APIs gerenciadas atuais\n\n| Variante | Compilar (ms) | Executar (ms) | Bytes | Pico de RAM (bytes) |\n| --- | ---: | ---: | ---: | ---: |\n'
    for r in report['nativeFeatures']:text+=f'| {r["variant"]} | {r["compileMedianMs"]:.3f} | {r["medianMs"]:.3f} | {r["binaryBytes"]} | {max(r["peakMemoryBytes"])} |\n'
    text+='\nSaídas independentes conferidas também em debug. Início de processo incluído; RAM zero significa observação indisponível para processo curto. Não há comparação histórica das APIs ausentes na alpha.8. Os relatórios antigos permanecem históricos.\n'
    args.output.with_suffix('.md').write_text(text,encoding='utf-8',newline='\n');print(args.output)

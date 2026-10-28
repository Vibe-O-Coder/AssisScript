"""Reproducible strided HashMap / large allocation / small call measurements."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler',type=Path,default=ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis'))
parser.add_argument('--baseline',type=Path)
parser.add_argument('--samples',type=int,default=7)
parser.add_argument('--entries',type=int,default=20000)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--check',action='store_true',help='Require strided workloads to stay within 5x sequential keys')
args=parser.parse_args()
if args.samples<3 or args.entries<1000:parser.error('Use at least 3 samples and 1000 entries')
def main(body):return 'fn main():int{'+body+'return 0;}'
programs={}
for stride in [1,64,4096,65536]:
    programs[f'hash_stride_{stride}']=(main(f'own m:HashMap<int,int>=new HashMap<int,int>();for(let i:int=0;i<{args.entries};i+=1){{m.set(i*{stride},i);}}let total:int=0;for(let r:int=0;r<5;r+=1){{for(let i:int=0;i<{args.entries};i+=1){{total+=m.get(i*{stride});}}}}print(total);'),str(5*args.entries*(args.entries-1)//2)+'\n')
programs['large_zero_allocations']=(main('let total:int=0;for(let i:int=0;i<300;i+=1){own p:*byte=alloc<byte>(8388608);assert(p[0]==0&&p[8388607]==0);p[0]=byte(1);p[8388607]=byte(255);total+=len(p);}print(total);'),str(300*8388608)+'\n')
programs['scalar_leaf_calls']=('pure fn step(n:int):int{return n*3+1;}'+main('let total:int=0;for(let i:int=0;i<10000000;i+=1){total+=step(i);}print(total);'),str(3*10000000*9999999//2+10000000)+'\n')
programs['fib35']=('pure fn fib(n:int):int{if(n<2){return n;}return fib(n-1)+fib(n-2);}'+main('print(fib(35));'),'9227465\n')
compilers={'candidate':args.compiler.resolve()}
if args.baseline:compilers['baseline']=args.baseline.resolve()
record={'format':'AssisScript-optimization-v1','platform':os.name,'host':{'system':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'logical_cpus':os.cpu_count()},'samples':args.samples,'entries':args.entries,'compilers':{},'workloads':{}}
for label,compiler in compilers.items():
    record['compilers'][label]={'sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'version':subprocess.check_output([compiler,'version'],text=True).strip()}
with tempfile.TemporaryDirectory(prefix='assis-perf-') as temp:
    folder=Path(temp)
    for name,(source,expected) in programs.items():
        path=folder/(name+'.assis');path.write_text(source,encoding='utf-8')
        binaries={};metrics={}
        for label,compiler in compilers.items():
            binary=folder/(label+('.exe' if os.name=='nt' else ''))
            start=time.perf_counter_ns();subprocess.run([compiler,'build',path,*(['--legacy'] if '--legacy' in subprocess.check_output([compiler,'help'],text=True) else []),'-o',binary],check=True,capture_output=True)
            metrics[label]={'compile_ms':(time.perf_counter_ns()-start)/1e6,'bytes':binary.stat().st_size,'binarySha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'run_ms':[]}
            # Distinct files survive interleaved measurements.
            target=folder/(name+'-'+label+binary.suffix);binary.rename(target);binaries[label]=target
            result=subprocess.run([target],capture_output=True,text=True,timeout=60)
            assert (result.returncode,result.stdout,result.stderr)==(0,expected,''),(name,label,result)
        for sample in range(args.samples):
            labels=list(compilers)
            if sample%2:labels.reverse()
            for label in labels:
                start=time.perf_counter_ns();result=subprocess.run([binaries[label]],capture_output=True,text=True,timeout=60)
                elapsed=(time.perf_counter_ns()-start)/1e6
                assert (result.returncode,result.stdout,result.stderr)==(0,expected,''),(name,label,result)
                metrics[label]['run_ms'].append(elapsed)
        for value in metrics.values():value['median_ms']=statistics.median(value['run_ms'])
        record['workloads'][name]=metrics
        print(name+': '+', '.join(label+'='+format(value['median_ms'],'.3f')+'ms' for label,value in metrics.items()),flush=True)
sequential=record['workloads']['hash_stride_1']['candidate']['median_ms']
record['max_stride_ratio']=max(record['workloads']['hash_stride_'+str(s)]['candidate']['median_ms']/sequential for s in [64,4096,65536])
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
lines=['# Optimization regression measurements','',f'Host: {os.name}. Samples: {args.samples}. Entries: {args.entries}. Interleaved samples, one warmup, independent output checks.','', '| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |','| --- | ---: | ---: | ---: |']
for name,metrics in record['workloads'].items():
    current=metrics['candidate']['median_ms'];old=metrics.get('baseline',{}).get('median_ms')
    lines.append(f'| {name} | {current:.3f} | '+(f'{old:.3f} | {old/current:.2f}x |' if old is not None else '— | — |'))
lines+=['',f'Maximum strided/sequential ratio: {record["max_stride_ratio"]:.3f}. Gate: <=5.0.','', 'Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.']
args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
if args.check and record['max_stride_ratio']>5:raise SystemExit('Strided HashMap performance regression (>5x sequential median)')

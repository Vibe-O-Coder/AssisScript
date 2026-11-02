"""Measured scalar profile comparison. Samples are local observations, not SLAs."""
import base64
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-integration-2026-11-02'
BUILD=ROOT/'build/page-executor-comparison';BUILD.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
COMPILER=Path(os.environ['ASSIS_BIN']).resolve()
spec=importlib.util.spec_from_file_location('wasm_candidate',ROOT/'tools/asv2-wasm-candidate.py');wasm=importlib.util.module_from_spec(spec);spec.loader.exec_module(wasm)
corpus=json.loads((ROOT/'tests/fixtures/page-execution-comparison.json').read_text())

def measured(command,env=None):
    start=time.perf_counter();out=tempfile.TemporaryFile();err=tempfile.TemporaryFile()
    p=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env,stdout=out,stderr=err)
    peak=0
    def memory():
        if os.name=='nt':
            class Counters(ctypes.Structure):
                _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('peak','working','pool_peak','pool','nonpaged_peak','nonpaged','page','page_peak')]
            c=Counters();c.cb=ctypes.sizeof(c)
            if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(int(p._handle)),ctypes.byref(c),c.cb): return c.peak
        else:
            try:
                for line in Path(f'/proc/{p.pid}/status').read_text().splitlines():
                    if line.startswith('VmHWM:'): return int(line.split()[1])*1024
            except FileNotFoundError: pass
        return 0
    while p.poll() is None:
        peak=max(peak,memory())
        if time.perf_counter()-start>30:
            p.kill();p.wait();out.close();err.close();raise TimeoutError(command)
        time.sleep(.001)
    if os.name=='nt':peak=max(peak,memory())
    p.wait();out.seek(0);err.seek(0);stdout=out.read();stderr=err.read();out.close();err.close()
    if p.returncode:raise RuntimeError((command,p.returncode,stderr.decode(errors='replace')))
    return dict(seconds=time.perf_counter()-start,peak_rss_sampled_bytes=peak,stdout=stdout.decode(),stderr=stderr.decode())

records=[]
for case in corpus['cases']:
    source=BUILD/(case['id']+'.assis');source.write_text(case['source'],encoding='utf-8')
    artifact=BUILD/(case['id']+'.asv2')
    compiled=measured([COMPILER,'build',source,'--target','page-asv2','-o',artifact]);data=artifact.read_bytes()
    limits=dict(frames=32,fuel=1000000,calls=10000,memory_limit=65536)
    start=time.perf_counter();generated=wasm.translate(data,**limits);translation=time.perf_counter()-start
    own='own code:*byte=try_alloc<byte>('+str(len(data))+');assert(code!=null);'+''.join(f'code[{i}]=byte({b});' for i,b in enumerate(data))
    body='import "std/pagevm.assis";safe fn main():int{'+own+'let steps:int=0;let value:int=0;val start:int=monotonic_ms();'
    body+=f'for(let i:int=0;i<{corpus["repeats"]};i++){{own v:pagevm::Instance=try_new pagevm::Instance(1,7,1,slice_of(code,0,len(code)),65536,32,1000000,10000);'
    body+='assert(v!=null && v.status()==0);assert(v.grant_counter(1,7,1));while(v.run(10000)==1){}assert(v.status()==2);value=v.result();steps=v.steps();}'
    body+=f'assert(value=={case["expected"]});print(monotonic_ms()-start,value,steps);return 0;}}'
    host=BUILD/(case['id']+'-vm.assis');host.write_text(body,encoding='utf-8');exe=host.with_suffix('.exe' if os.name=='nt' else '.native')
    measured([COMPILER,'build',host,'-o',exe])
    observation=measured([exe]);_,value,steps=map(int,observation['stdout'].split());assert value==case['expected']
    actions=[dict(op='grant',identity=[1,7,1])]+[dict(op='tick',quantum=10000)]*((steps+9999)//10000)
    envelope=BUILD/(case['id']+'.json');envelope.write_text(json.dumps(dict(asv2=base64.b64encode(data).decode(),wasm=base64.b64encode(generated).decode(),limits=limits,actions=actions,repeat=corpus['repeats'])))
    vm_samples=[];wasm_samples=[]
    for _ in range(corpus['samples']):
        native=measured([exe]);ms,result,count=map(int,native['stdout'].split());assert (result,count)==(case['expected'],steps)
        vm_samples.append(dict(executor_ms=ms,process_ms=native['seconds']*1000,peak_rss_sampled_bytes=native['peak_rss_sampled_bytes']))
        run=measured(['node',ROOT/'tools/run-wasm-candidate.js',envelope]);record=json.loads(run['stdout']);assert record['status']=='executed',record
        last=record['snapshots'][-1];assert (last['state'],int(last['result']),last['steps'])==(2,case['expected'],steps)
        wasm_samples.append({k:record[k] for k in ('execute_ms','validator_ms','engine_compile_ms','linear_bytes','rss_bytes')})
        wasm_samples[-1].update(process_ms=run['seconds']*1000,peak_rss_sampled_bytes=run['peak_rss_sampled_bytes'])
    records.append(dict(id=case['id'],expected=str(case['expected']),steps=steps,asv2_bytes=len(data),wasm_bytes=len(generated),asv2_compile=compiled,
        translation_ms=translation*1000,vm_samples=vm_samples,wasm_samples=wasm_samples,
        vm_median_ms=statistics.median(v['executor_ms'] for v in vm_samples),wasm_median_ms=statistics.median(v['execute_ms'] for v in wasm_samples)))
    print(case['id'],steps,'steps; medians',records[-1]['vm_median_ms'],records[-1]['wasm_median_ms'],flush=True)
report=dict(schema=corpus['schema'],platform=platform.platform(),machine=platform.machine(),processor=platform.processor(),python=platform.python_version(),
    node=subprocess.check_output(['node','-p','JSON.stringify(process.versions)'],text=True).strip(),compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
    repeats=corpus['repeats'],samples=corpus['samples'],cases=records,
    limits=['Single local host per OS; no throughput/SLA extrapolation','VM integer-ms clock is coarse for tiny cases; Wasm uses performance.now',
        'Wasm includes fixed 128 KiB linear memory and engine; VM requested bytes exclude allocator/process overhead',
        'RSS is sampled process high water, not an enforced compilation/host RSS quota','Wasm dispatcher uses a balanced PC tree; not an optimized direct-source Wasm backend',
        'Python canonical validation is separate from engine compilation; both are included in end-to-end time',
        'Existing Node runtime is a comparison dependency, never embedded or distributed'])
(OUT/('windows-benchmark.json' if os.name=='nt' else 'linux-benchmark.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')

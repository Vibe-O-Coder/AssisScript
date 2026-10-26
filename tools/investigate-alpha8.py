"""Long alternating heap runs and compiler-startup checks after noisy regressions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import struct
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
compiler=ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis');baseline=args.baseline.resolve();count=40_000_000;samples=11
def run(command,expected=None):
    r=subprocess.run(list(map(str,command)),capture_output=True,timeout=120);assert r.returncode==0 and not r.stderr,(command,r.stderr)
    if expected is not None:assert r.stdout==expected,(r.stdout,expected)
    return r.stdout
def runtime_symbols(header):return {4096+int(value,16):name for name,value in re.findall(r'#define RT_(\w+) 0x([a-f0-9]+)',header.read_text())}
def instructions(binary,header):
    data=binary.read_bytes();entry=struct.unpack_from('<Q',data,24)[0]-0x400000;start=data.index(b'\x55\x48\x89\xe5',entry);end=4096+struct.unpack_from('<Q',data,64+56+32)[0];symbols=runtime_symbols(header)
    output=run(['objdump','-D','-b','binary','-m','i386:x86-64','--start-address='+str(start),'--stop-address='+str(end),binary]).decode();result=[]
    for line in output.splitlines():
        match=re.match(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+\s*([a-z][^\n]*)$',line)
        if not match:continue
        text=match[1].strip()
        if re.match(r'^(?:call|j\w+)\s',text):
            target=re.search(r'0x([a-f0-9]+)',text)
            if target:
                address=int(target[1],16);name=symbols.get(address,'user+'+str(address-start));text=text[:target.start()]+name+text[target.end():]
        result.append(re.sub(r'\s+',' ',text))
    return result
report=dict(compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),baselineSha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),iterations=count,samples=samples,heap=[],compilerStartup=[])
with tempfile.TemporaryDirectory(prefix='assis-investigation-') as temp:
    folder=Path(temp);file=folder/'heap.assis';file.write_text('struct Par{let x:int;let y:int;}assis item(n:int):own Par{return new Par(n,n+1);}assis assis_assis():int{let total:int=0;for(let i:int=0;i<'+str(count)+';i+=1){own p:Par=item(i);total+=p.x+p.y;}print(total);return 0;}',encoding='utf-8')
    variants=[('alpha7',baseline),('atual',compiler)]
    paths=[]
    for name,cc in variants:
        binary=folder/(name+('.exe' if os.name=='nt' else ''));run([cc,'build',file,'-o',binary]);paths.append(binary);report['heap'].append(dict(variant=name,samplesMs=[],binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
    expected=f'{count**2}\n'.encode()
    for sample in range(samples+1):
        for i in [(sample+j)%2 for j in range(2)]:
            start=time.perf_counter();run([paths[i]],expected);elapsed=(time.perf_counter()-start)*1000
            if sample:report['heap'][i]['samplesMs'].append(elapsed)
    for record in report['heap']:record['medianMs']=statistics.median(record['samplesMs'])
    for name,cc in variants:report['compilerStartup'].append(dict(variant=name,versionMs=[],checkMs=[]))
    for sample in range(samples):
        for i in [(sample+j)%2 for j in range(2)]:
            for command,key in [('version','versionMs'),('check','checkMs')]:
                start=time.perf_counter()
                for _ in range(5):run([variants[i][1],command,*([file] if command=='check' else [])])
                report['compilerStartup'][i][key].append((time.perf_counter()-start)*200)
    for r in report['compilerStartup']:r['versionMedianMs']=statistics.median(r['versionMs']);r['checkMedianMs']=statistics.median(r['checkMs'])
    if os.name!='nt':
        old=instructions(paths[0],baseline.parent.parent/'src/runtime_blob.h');new=instructions(paths[1],ROOT/'src/runtime_blob.h');report['normalizedUserInstructionsEqual']=old==new
        report['userInstructionCounts']=[len(old),len(new)];report['instructions']={'alpha7':old,'atual':new}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
text='# Investigação alpha.8\n\nOnze pares alternados, 40 milhões de itens por processo, uma rodada de aquecimento. N² é conferido independentemente; os checks continuam ativos.\n\n| Variante | Heap (ms) | Version compilador (ms) | Check compilador (ms) |\n| --- | ---: | ---: | ---: |\n'
for i,r in enumerate(report['heap']):s=report['compilerStartup'][i];text+=f'| {r["variant"]} | {r["medianMs"]:.3f} | {s["versionMedianMs"]:.3f} | {s["checkMedianMs"]:.3f} |\n'
if 'normalizedUserInstructionsEqual' in report:text+=f'\nInstruções de funções do usuário iguais após normalizar endereços de saltos/chamadas: {report["normalizedUserInstructionsEqual"]}. O layout/endereço do código mudou; essa comparação não prova causalidade das diferenças de tempo.\n'
text+='\nVersion/check medem cinco subprocessos por amostra e apresentam média por subprocesso. Frequência, escalonamento Windows/WSL e antivírus não foram controlados. Dados brutos e hashes no JSON; os resultados iniciais permanecem preservados.\n';args.output.with_suffix('.md').write_text(text,encoding='utf-8',newline='\n');print(args.output)

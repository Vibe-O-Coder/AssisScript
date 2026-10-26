"""Equivalent observable workloads: AssisScript, C -O2 and Python.

python tools/benchmark-native.py --cc gcc --samples 5 [--baseline /path/assis]
The compiler and generated programs need no Python/C runtime dependency.
"""
from pathlib import Path
import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', default=os.environ.get('CC', 'gcc'))
parser.add_argument('--samples', type=int, default=5)
parser.add_argument('--baseline', type=Path)
parser.add_argument('--output', type=Path, default=root/'benchmarks/resultados/nativo-3.2.json')
args = parser.parse_args()
if not 3 <= args.samples <= 30:
    parser.error('--samples deve estar entre 3 e 30')
compiler = root/'bin'/('assis.exe' if os.name == 'nt' else 'assis')
def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f'{command[0]}: {result.stderr.decode(errors="replace")} ({result.returncode})')
    return result.stdout

workloads = [
    ('aritmetica',
     'let x:int=1; let soma:int=0; for(let i:int=0;i<10000000;i+=1){x=(x*1664525+1013904223)&0x7fffffff;soma=(soma+x)&0x7fffffff;}print(soma);',
     'int64_t x=1,sum=0; for(int64_t i=0;i<10000000;i++){x=(x*1664525+1013904223)&0x7fffffff;sum=(sum+x)&0x7fffffff;} printf("%lld\\n",(long long)sum);',
     'x=1; total=0\nfor i in range(10000000):\n x=(x*1664525+1013904223)&0x7fffffff\n total=(total+x)&0x7fffffff\nprint(total)\n'),
    ('collatz',
     'let total:int=0;for(let i:int=1;i<200001;i+=1){let n:int=i;while(n!=1){if(n%2==0){n/=2;}else{n=n*3+1;}total+=1;}}print(total);',
     'int64_t total=0;for(int64_t i=1;i<200001;i++){int64_t n=i;while(n!=1){if(n%2==0)n/=2;else n=n*3+1;total++;}}printf("%lld\\n",(long long)total);',
     'total=0\nfor i in range(1,200001):\n n=i\n while n!=1:\n  n=n//2 if n%2==0 else n*3+1\n  total+=1\nprint(total)\n'),
    ('alocacao',
     'let total:int=0;for(let i:int=0;i<1000000;i+=1){let p:P=new P(i);total+=p.x;free(p);}print(total);',
     'int64_t total=0;for(int64_t i=0;i<1000000;i++){struct P *p=malloc(sizeof(*p));if(!p)return 2;p->x=i;observe(p);total+=p->x;free(p);}printf("%lld\\n",(long long)total);',
     'class P:\n __slots__=("x",)\n def __init__(self,x): self.x=x\ntotal=0\nfor i in range(1000000):\n p=P(i)\n total+=p.x\n del p\nprint(total)\n'),
    ('strings-indice',
     'let s:text="'+'a'*30000+'";let total:int=0;for(let i:int=0;i<len(s);i+=1){total+=s[i];}print(total);',
     'char *s=malloc(30001);if(!s)return 2;memset(s,97,30000);s[30000]=0;observe(s);int64_t total=0;size_t n=strlen(s);for(size_t i=0;i<n;i++)total+=(unsigned char)s[i];printf("%lld\\n",(long long)total);free(s);',
     's=b"a"*30000\ntotal=0\nfor i in range(len(s)): total+=s[i]\nprint(total)\n')
]
# A memory barrier makes C allocations/loads observable to the optimizer. It
# emits no instruction, does not add volatile loads, and prevents elision of
# the very allocator being measured. AssisScript does not eliminate allocation.
c_header = '''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct P { int64_t x; };
static inline void observe(void *p){__asm__ __volatile__("" : : "r"(p) : "memory");}
int main(void){
'''
cpu = os.environ.get('PROCESSOR_IDENTIFIER', platform.processor())
if Path('/proc/cpuinfo').exists():
    cpu = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), cpu)
report = dict(generatedAt=datetime.now(timezone.utc).isoformat(), platform=platform.platform(), machine=platform.machine(), cpu=cpu, python=sys.version,
              cCompiler=run([args.cc,'--version']).decode().splitlines()[0], cFlags=['-O2','-std=c11','-static'],
              compiler=run([compiler,'version']).decode().strip(), samples=args.samples,
              includesProcessStartup=True, warmups=1, results=[])
if args.baseline:
    report['baseline'] = run([args.baseline,'version']).decode().strip()
with tempfile.TemporaryDirectory(prefix='assis-native-') as folder:
    folder=Path(folder)
    for name, assis, c, python in workloads:
        # The baseline predates for. Use while in every AssisScript variant.
        if name=='aritmetica': assis=assis.replace('for(let i:int=0;i<10000000;i+=1){','let i:int=0;while(i<10000000){').replace(';}print', ';i+=1;}print')
        elif name=='collatz': assis=assis.replace('for(let i:int=1;i<200001;i+=1){','let i:int=1;while(i<200001){').replace('total+=1;}}','total+=1;}i+=1;}')
        elif name=='alocacao': assis=assis.replace('for(let i:int=0;i<1000000;i+=1){','let i:int=0;while(i<1000000){').replace('free(p);}', 'free(p);i+=1;}')
        elif name=='strings-indice': assis=assis.replace('for(let i:int=0;i<len(s);i+=1){','let i:int=0;while(i<len(s)){').replace('total+=s[i];}', 'total+=s[i];i+=1;}')
        source=folder/(name+'.assis');source.write_text('struct P {let x:int;}\nassis assis_assis():int{'+assis+'return 0;}')
        c_source=folder/(name+'.c'); c_source.write_text(c_header+c+'return 0;}')
        py_source=folder/(name+'.py'); py_source.write_text(python)
        suffix='.exe' if os.name=='nt' else ''
        c_binary=folder/(name+'-c'+suffix)
        run([args.cc,'-O2','-std=c11','-static',c_source,'-o',c_binary])
        variants=[('C -O2',[c_binary]),('Python',[sys.executable,py_source])]
        for label, comp, flags in [('AssisScript',compiler,[]),('AssisScript --no-opt',compiler,['--no-opt'])]+([('AssisScript anterior',args.baseline,[])] if args.baseline else []):
            binary=folder/(name+'-'+str(len(variants))+suffix)
            run([comp,'build',source,'-o',binary,*flags]);variants.append((label,[binary]))
        expected=run([c_binary])
        for label, command in variants:
            assert run(command)==expected,(name,label,'aquecimento')
            samples=[]
            for _ in range(args.samples):
                start=time.perf_counter_ns();actual=run(command);samples.append((time.perf_counter_ns()-start)/1e6)
                assert actual==expected,(name,label,'saída divergente')
            entry=dict(case=name,variant=label,medianMs=statistics.median(samples),minMs=min(samples),maxMs=max(samples),samplesMs=samples,stdout=expected.decode().strip())
            report['results'].append(entry)
            print(f'{name} | {label} | {entry["medianMs"]:.3f} ms',flush=True)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
markdown=f'''# Desempenho nativo — AssisScript 3.2

{report['generatedAt']}; {report['platform']}; {report['cpu']}; {report['cCompiler']}; Python {platform.python_version()}.
{args.samples} amostras após um aquecimento; todas as saídas equivalentes verificadas.
Tempos incluem início de processo. C: `-O2 -std=c11 -static`, sem remover verificações no AssisScript.

| Carga | Variante | Mediana (ms) | Mín–máx (ms) |
| --- | --- | ---: | ---: |
'''
for r in report['results']:
    markdown+=f'| {r["case"]} | {r["variant"]} | {r["medianMs"]:.3f} | {r["minMs"]:.3f}–{r["maxMs"]:.3f} |\n'
markdown+='''
O teste C de alocação contém uma barreira de compilador sem instruções para impedir que malloc/free sejam eliminados; ela não adiciona acessos volatile. Os laços usam os mesmos limites e resultados. O teste de strings mede a indexação pública com limites verificados em AssisScript e acesso por índice em C/Python. O struct de AssisScript inclui metadados adicionais. O teste de objetos Python usa __slots__.

Cargas abaixo de 20 ms sofrem influência relevante do início do processo; proximidade entre medianas não demonstra paridade com C. Estes quatro programas não representam todos os programas C/C++, nem medem pico de RAM. A variante anterior usa o mesmo fonte com while. Dados brutos acompanham este arquivo.
'''
args.output.with_suffix('.md').write_text(markdown,encoding='utf-8')
print(args.output)

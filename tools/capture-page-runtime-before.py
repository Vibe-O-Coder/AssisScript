"""Rebuild exact published base and reproduce the missing page target/SDK."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parent.parent
BASE='1e574736ce33a16e442fb270e9d42c8c884d29f6'
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-runtime-2026-11-02'
folder=ROOT/'build/before-page-runtime';folder.mkdir(parents=True,exist_ok=True)
archive=subprocess.check_output(['git','archive',BASE,'src','stdlib'],cwd=ROOT)
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
compiler=folder/'bin/assis.exe';compiler.parent.mkdir(exist_ok=True)
gcc='C:/msys64/ucrt64/bin/gcc.exe'
environment=dict(os.environ,PATH=str(Path(gcc).parent)+os.pathsep+os.environ['PATH'])
command=[gcc,'-O2','-std=c11','-municode','-static','-static-libgcc','-s',str(folder/'src/assisc.c'),'-o',str(compiler)]
subprocess.run(command,env=environment,check=True)
checks=[]
source=folder/'probe.assis';source.write_text('safe fn main():int{return 42;}',encoding='utf-8')
for case,args in [('target',['build',source,'--target','page-asv2','-o',folder/'out.asv2']),
    ('sdk',['check',folder/'sdk.assis'])]:
    if case=='sdk':(folder/'sdk.assis').write_text('import "std/page.assis";safe fn main():int{return 0;}',encoding='utf-8')
    result=subprocess.run([compiler,*args],cwd=folder,capture_output=True)
    assert result.returncode!=0
    checks.append(dict(case=case,returncode=result.returncode,stderr=result.stderr.decode('utf-8').replace(str(ROOT),'<workspace>')))
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'before.json').write_text(json.dumps(dict(base=BASE,source='git archive exact base; rebuilt C11 compiler',
    compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=checks,execution='not-run: compile/import rejections'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print('Exact published base: page-asv2 target and page SDK absent; no page executed')

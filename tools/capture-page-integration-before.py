"""Rebuild immutable published base and reproduce unavailable worker imports."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parent.parent
BASE='0345d567a7ade632546805fc18eca5ca32749cdb'
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-integration-2026-11-02'
folder=ROOT/'build/before-page-integration';folder.mkdir(parents=True,exist_ok=True)
archive=subprocess.check_output(['git','archive',BASE,'src','stdlib'],cwd=ROOT)
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
compiler=folder/'bin/assis.exe';compiler.parent.mkdir(exist_ok=True)
gcc='C:/msys64/ucrt64/bin/gcc.exe';env=dict(os.environ,PATH=str(Path(gcc).parent)+os.pathsep+os.environ['PATH'])
subprocess.run([gcc,'-O2','-std=c11','-municode','-static','-static-libgcc','-s',str(folder/'src/assisc.c'),'-o',str(compiler)],env=env,check=True)
checks=[]
for library in ['pagereader']:
    file=folder/'probe.assis';file.write_text(f'import "std/{library}.assis";safe fn main():int{{return 0;}}',encoding='utf-8')
    r=subprocess.run([compiler,'check',file],cwd=folder,capture_output=True);assert r.returncode!=0
    checks.append(dict(library=library,returncode=r.returncode,stderr=r.stderr.decode('utf-8').replace(str(ROOT),'<workspace>')))
(OUT/'before.json').write_text(json.dumps(dict(base=BASE,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=checks,execution='not-run: compile/import rejection'),indent=2)+'\n',encoding='utf-8',newline='\n')
print('Exact published base rebuilt; pagereader import unavailable; no execution claimed')

"""Build and execute example 51 with fresh compiler/provider/worker artifacts."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-resource-budget-2026-11-02'
STAGE=ROOT/'build/resource-budget-example';STAGE.mkdir(parents=True,exist_ok=True)
compiler=Path(os.environ['ASSIS_BIN']).resolve();host='windows' if os.name=='nt' else 'linux'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
built=module('resource_worker',ROOT/'tools/build-page-worker.py').build(STAGE,compiler)
if os.name=='nt':module('resource_platform',ROOT/'tools/build-platform.py').build(STAGE/'assis_platform_v1.dll')
binary=STAGE/('compile-page.exe' if os.name=='nt' else 'compile-page')
command=[str(compiler),'build',str(ROOT/'exemplos/51_compile_page.assis'),'-o',str(binary)]
subprocess.run(command,cwd=ROOT,check=True)
env=dict(os.environ,PATH=str(STAGE)+os.pathsep+os.environ.get('PATH',''),LD_LIBRARY_PATH=str(STAGE))
run=[str(binary),str(compiler),built['worker']]+(['--trusted-local'] if os.name=='nt' else [])
r=subprocess.run(run,env=env,cwd=ROOT,capture_output=True,timeout=15)
log=r.stdout+r.stderr;(OUT/f'{host}-example-51.log').write_bytes(log)
report=dict(passed=(r.returncode,r.stdout,r.stderr)==(0,b'PAGE-STATE 42\n',b''),returncode=r.returncode,
    stdout=r.stdout.decode(),stderr=r.stderr.decode(),compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    artifacts={Path(built[k]).name:hashlib.sha256(Path(built[k]).read_bytes()).hexdigest() for k in ['provider','worker']},
    example_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),commands=[command,run])
(OUT/f'{host}-example-51.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Example 51:',r.stdout.decode().strip(),'PASS' if report['passed'] else 'FAIL');raise SystemExit(0 if report['passed'] else 1)

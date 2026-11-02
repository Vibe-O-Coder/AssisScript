"""Isolated distribution for the fresh installer regression; no release promotion."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-integration-2026-11-02'
STAGE=ROOT/'build/page-integration-distribution'
names=[json.loads(line[1:-1]) for line in (ROOT/'src/install_files.inc').read_text().splitlines() if line.startswith('L')]
catalog=json.loads((ROOT/'stdlib/catalogo.json').read_text(encoding='utf-8'))
names += ['stdlib\\'+x['name']+'.assis' for x in catalog['libraries'] if not x['required']]
for name in names:
    source=ROOT/name;dest=STAGE/name;dest.parent.mkdir(parents=True,exist_ok=True)
    if name=='bin\\assis.exe':source=ROOT/'build/assis.exe'
    shutil.copyfile(source,dest)
compiler='C:/msys64/ucrt64/bin/gcc.exe'
candidate=STAGE/'bin/assis-setup.exe'
environment=dict(os.environ,PATH=str(Path(compiler).parent)+os.pathsep+os.environ.get('PATH',''))
command=[compiler,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Wno-misleading-indentation',
    '-municode','-static','-static-libgcc','-s','-Wl,--no-insert-timestamp',
    str(ROOT/'src/windows_setup.c'),'-lshell32','-ladvapi32','-luser32','-o',str(candidate)]
subprocess.run(command,env=environment,cwd=ROOT,check=True)
result=subprocess.run(['node','--test','--test-isolation=none','tests/test-development.js','tests/test-v31.js'],cwd=ROOT,
    env=dict(environment,ASSIS_BIN=str(ROOT/'build/assis.exe'),ASSIS_SETUP_BIN=str(candidate)),
    capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
content=result.stdout+result.stderr;(OUT/'windows-node.log').write_text(content,encoding='utf-8',newline='\n')
count=re.search(r'tests (\d+)',content)
report=dict(passed=result.returncode==0,returncode=result.returncode,tests=int(count[1]) if count else 0,
    log_sha256=hashlib.sha256(content.encode()).hexdigest(),setup_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
    compiler_sha256=hashlib.sha256((STAGE/'bin/assis.exe').read_bytes()).hexdigest(),
    scope='Fresh isolated setup/current distribution/compiler; temporary prefixes; no PATH, associations, release or tracked binary writes')
(OUT/'windows-node.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Node tests:',report['tests'],'PASS' if report['passed'] else 'FAIL');raise SystemExit(result.returncode)

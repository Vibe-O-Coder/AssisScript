"""Reproduce profile boundary, run the example, and capture editor/environment data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path);p.add_argument('--editor',action='store_true');args=p.parse_args()
OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def run(command,input=None):
    r=subprocess.run(list(map(str,command)),input=input,capture_output=True,cwd=ROOT,timeout=90)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))
    return r
records=[]
for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
    command=[compiler,'run',ROOT/'exemplos/52_htdl_catalog.assis','--safe','--debug',*flags]
    r=run(command);assert r.stderr==b'' and r.stdout==b'HTDL-CATALOG 21\nEDITOR-DIAGNOSTICS 2\n'
    log=OUT/f'{host}-example-52-{mode}.log';log.write_bytes(r.stdout)
    records.append(dict(mode=mode,passed=True,log=log.name,log_sha256=sha(log)))
save(f'{host}-example-52.json',dict(passed=True,compiler_sha256=sha(compiler),checks=records))
cc='C:/msys64/ucrt64/bin/gcc.exe' if os.name=='nt' else 'cc'
environment=dict(platform=platform.platform(),machine=platform.machine(),python=sys.version,
    compiler_sha256=sha(compiler),compiler_source_sha256=sha(ROOT/'src/assisc.c'),
    c_compiler=cc,c_compiler_version=run([cc,'--version']).stdout.decode().splitlines()[0])
environment['node_status']='available' if shutil.which('node') else 'not-run/unavailable'
if shutil.which('node'):environment['node_version']=run(['node','--version']).stdout.decode().strip()
save(f'{host}-environment.json',environment)
if args.editor:
    assert shutil.which('node'),'Node is required for --editor'
    command=['node','--test','--test-isolation=none','tests/test-lsp.js','tests/test-htdl-editor.js',
             'vscode-assisscript/test/extension.test.js','vscode-assisscript/test/language.test.js']
    r=run(command);log=OUT/f'{host}-editor.log';log.write_bytes(r.stdout+r.stderr)
    count=re.search(rb'tests (\d+)',log.read_bytes());assert count
    save(f'{host}-editor.json',dict(command=command,passed=True,executed=int(count[1]),returncode=0,
         log_sha256=sha(log),compiler_sha256=sha(compiler)))
if args.baseline:
    baseline=args.baseline.resolve();base_compiler=baseline/'build/assis.exe'
    head=run(['git','-C',baseline,'rev-parse','HEAD']).stdout.decode().strip()
    assert head=='f00d1ff95694dd312f90ec46d563606bda258356'
    assert not run(['git','-C',baseline,'status','--porcelain']).stdout
    source=json.loads((ROOT/'tests/fixtures/htdl-catalog-corpus.json').read_text())['cases'][3]['source'].encode()
    build=ROOT/'build/catalog-before';build.mkdir(parents=True,exist_ok=True);records=[]
    for name,candidate,fixture,expected in [('published-bootstrap',base_compiler,baseline/'tests/fixtures/htdl-driver.assis',203),
            ('current-bootstrap',compiler,ROOT/'tests/fixtures/htdl-driver.assis',203),
            ('current-catalog',compiler,ROOT/'tests/fixtures/htdl-catalog-driver.assis',0)]:
        binary=build/(name+'.exe');run([candidate,'build',fixture,'--safe','--debug','-o',binary])
        r=run([binary],source);code=int(r.stdout.splitlines()[0].split()[0]);assert code==expected and r.stderr==b''
        records.append(dict(profile=name,code=code,compiler_sha256=sha(candidate),fixture_sha256=sha(fixture),binary_sha256=sha(binary),stdout_sha256=hashlib.sha256(r.stdout).hexdigest()))
    save('before.json',dict(base=head,baseline_path=str(baseline),source=source.decode(),checks=records,
        scope='Native observation of the published bootstrap boundary, preserved in current bootstrap; new catalog is an explicit separate API. Baseline binary is used only for this reproduction.'))
print(host,'example/environment/editor/boundary requested checks: PASS')

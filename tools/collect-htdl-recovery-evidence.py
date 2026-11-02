"""Collect fresh HTDL recovery regressions; never count skipped tests as pass."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'docs/ecossistema/evidencias/m3-htdl-recovery-2026-11-02'
BASE = '5fad34e32c444574b4900f6629855cf9a2626cb0'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--editor',action='store_true')
parser.add_argument('--baseline',type=Path)
parser.add_argument('--only',nargs='+')
args = parser.parse_args()
OUT.mkdir(parents=True,exist_ok=True)
host = 'windows' if os.name=='nt' else 'linux'
compiler = Path(os.environ['ASSIS_BIN']).resolve()
records = []
jobs = [(name,[sys.executable,str(ROOT/'tests'/f'test-{name}.py')])
        for name in ['htdl-recovery','htdl-catalog','htdl-parser','reader-transactions','htdl-reader']]
if args.editor:
    jobs.append(('editor',['node','--test','--test-isolation=none','tests/test-htdl-editor.js','tests/test-lsp.js',
                           'vscode-assisscript/test/language.test.js','vscode-assisscript/test/extension.test.js']))
if args.only:
    assert set(args.only) <= {name for name,_ in jobs}
    previous=OUT/f'{host}.json'
    if previous.exists():
        records=[r for r in json.loads(previous.read_text())['checks'] if r['name'] not in args.only]
    jobs=[(name,command) for name,command in jobs if name in args.only]
for name, command in jobs:
    started = time.monotonic()
    r = subprocess.run(command,cwd=ROOT,capture_output=True,timeout=300,
                       env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8'))
    log = r.stdout+r.stderr
    path = OUT/f'{host}-{name}.log'
    path.write_bytes(log)
    if name=='editor':
        total=re.search(rb'(?:# )?tests (\d+)',log)
        skipped=re.search(rb'(?:# )?skipped (\d+)',log)
    else:
        total=re.search(rb'Ran (\d+) tests? in',log)
        skipped=re.search(rb'skipped=(\d+)',log)
    count=int(total[1]) if total else 0
    not_run=int(skipped[1]) if skipped else 0
    records.append(dict(name=name,command=command,returncode=r.returncode,executed=count-not_run,not_run=not_run,
                        log=path.name,sha256=hashlib.sha256(log).hexdigest(),seconds=round(time.monotonic()-started,3)))
    print(f'{host} {name}: rc={r.returncode}, {count-not_run} executed/{not_run} not-run',flush=True)

if args.baseline:
    source = '<div type=document version="0.1" lang=en><div type=head><div type=title>X</div></div><div type=body><div type=paragraph>&bad;</div><div type=paragraph>&also;</div></div></div>'
    observations=[]
    for label, tool in [('before',args.baseline/'tools/htdl-check.assis'),('after',ROOT/'tools/htdl-check.assis')]:
        binary=ROOT/'build'/f'{label}-recovery.exe'
        # Standard-library resolution follows the compiler installation. Using
        # the current compiler for the old tool would silently test the new lib.
        selected=(args.baseline/'build'/('assis.exe' if os.name=='nt' else 'assis-linux')) if label=='before' else compiler
        subprocess.run([str(selected),'build',str(tool),'--safe','--debug','-o',str(binary)],check=True,capture_output=True)
        r=subprocess.run([str(binary)],input=source.encode(),capture_output=True,check=True,timeout=30)
        observations.append(dict(label=label,tool=str(tool),stdout=r.stdout.decode(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),compiler_sha256=hashlib.sha256(selected.read_bytes()).hexdigest()))
    assert observations[0]['stdout'].splitlines()[0]=='1 0',observations
    assert observations[1]['stdout'].splitlines()[0]=='2 0',observations
    (OUT/'before-after.json').write_text(json.dumps(dict(base=BASE,source=source,observations=observations),indent=2)+'\n',encoding='utf-8',newline='\n')

report=dict(schema='htdl-recovery-evidence-v1',base=BASE,platform=platform.platform(),machine=platform.machine(),python=sys.version,
            compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=records,
            passed=all(r['returncode']==0 and r['executed']>0 for r in records))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

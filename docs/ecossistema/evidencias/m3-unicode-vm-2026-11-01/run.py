"""Fresh scoped tests; this runner does not change historical evidence."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
HOST='windows' if os.name=='nt' else 'linux'
COMPILER=Path(os.environ['ASSIS_BIN']).resolve()
suites=['graphemes','pagevm','reader-transactions','htdl-reader','htdl-viewer','htdl-parser',
        'document-memory','document-tree','english-api','ffi','cli','system','packages',
        'optimization','complete-ir','functions','ownership-functions','generic-classes','collections-ast']
if os.name=='nt':suites+=['platform-window','wasm-spike']
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='+',choices=suites);args=parser.parse_args()
previous={}
if args.only:
    report=json.loads((OUT/f'{HOST}.json').read_text())
    assert report['compiler_sha256']==hashlib.sha256(COMPILER.read_bytes()).hexdigest()
    previous={c['name']:c for c in report['checks']}
records=[]
for name in suites:
    if args.only and name not in args.only:records.append(previous[name]);continue
    command=[sys.executable,str(ROOT/f'tests/test-{name}.py')]
    start=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,
        env=dict(os.environ,PYTHONIOENCODING='utf-8',ASSIS_PLATFORM_EVIDENCE=str(OUT/'windows-provider.json')))
    log=f'{HOST}-{name}.log';content=result.stdout+result.stderr
    (OUT/log).write_text(content,encoding='utf-8',newline='\n')
    count=re.search(r'Ran (\d+) tests?',content);skip=re.search(r'skipped=(\d+)',content)
    total=int(count[1]) if count else 0;skipped=int(skip[1]) if skip else 0
    records.append(dict(name=name,returncode=result.returncode,executed=total-skipped,not_run=skipped,
        seconds=time.monotonic()-start,log=log,log_sha256=hashlib.sha256(content.encode()).hexdigest()))
    print(HOST,name,'PASS' if result.returncode==0 and total else 'FAIL',flush=True)
report=dict(platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
    checks=records,passed=all(c['returncode']==0 and c['executed']>0 for c in records),
    native_provider='tested' if os.name=='nt' else 'unsupported',
    wasm='Node/V8 trusted fixtures, coarse process timeout; no general fuel verifier' if os.name=='nt' else 'not-run: Node unavailable',
    targets_generated=['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'],
    other_native_targets='ARM64/macOS not-run; generation is not execution')
(OUT/f'{HOST}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

"""Scoped native evidence. Build ASSIS_BIN freshly; do not infer other targets."""
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
DIRECTORY=Path(__file__).resolve().parent
HOST='windows' if os.name=='nt' else 'linux'
COMPILER=Path(os.environ['ASSIS_BIN']).resolve()
names=['htdl-reader','htdl-viewer','htdl-parser','document-memory','document-tree','ffi','english-api','packages','complete-ir','optimization']
if os.name=='nt':names.insert(1,'platform-window')
arguments=argparse.ArgumentParser(description=__doc__)
arguments.add_argument('--only',nargs='+',choices=names)
arguments=arguments.parse_args()
previous={}
if arguments.only:
    old=json.loads((DIRECTORY/f'{HOST}.json').read_text(encoding='utf-8'))
    assert old['compiler_sha256']==hashlib.sha256(COMPILER.read_bytes()).hexdigest()
    previous={r['name']:r for r in old['checks']}
records=[]
for name in names:
    if arguments.only and name not in arguments.only:
        records.append(previous[name]);continue
    command=[sys.executable,f'tests/test-{name}.py']
    started=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,
        env=dict(os.environ,PYTHONIOENCODING='utf-8',ASSIS_PLATFORM_EVIDENCE=str(DIRECTORY/'windows-provider.json')))
    content=result.stdout+result.stderr;log=f'{HOST}-{name}.log'
    (DIRECTORY/log).write_text(content,encoding='utf-8',newline='\n')
    count=re.search(r'Ran (\d+) tests?',content);skip=re.search(r'skipped=(\d+)',content)
    registered=int(count[1]) if count else 0;not_run=int(skip[1]) if skip else 0
    records.append(dict(name=name,command=['python',command[1]],returncode=result.returncode,registered=registered,
        executed=registered-not_run,not_run=not_run,seconds=time.monotonic()-started,log=log,
        log_sha256=hashlib.sha256(content.encode()).hexdigest()))
    print(name,'PASS' if result.returncode==0 and registered else 'FAIL',flush=True)
report=dict(schema='assisscript-reader-native-v1',platform=platform.platform(),python=sys.version,
    compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),checks=records,
    passed=all(r['returncode']==0 and r['executed']>0 for r in records),
    native_provider='tested' if os.name=='nt' else 'unsupported',
    visual_inspection='not-run: Computer Use app approval timed out',
    accessibility='external MSAA client tested on Windows; real screen reader not-run',scale_200='Windows font zoom and reflow tested; OS DPI/monitors not-run',selection_ime='scalar selection tested; grapheme editing/IME unsupported',
    other_native_targets={'macos-x64':'not-run','macos-arm64':'not-run','linux-arm64':'not-run'})
(DIRECTORY/f'{HOST}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

"""Fresh scoped native evidence; ASSIS_BIN must name a compiler built here."""
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
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
HOST='windows' if os.name=='nt' else 'linux'
COMPILER=Path(os.environ['ASSIS_BIN']).resolve()
names=['reader-transactions','htdl-reader','htdl-viewer','htdl-parser','document-memory','document-tree','ffi','english-api','packages','complete-ir','optimization']
if os.name=='nt':names.insert(3,'platform-window')
arguments=argparse.ArgumentParser(description=__doc__);arguments.add_argument('--only',nargs='+',choices=names);arguments=arguments.parse_args()
previous={}
if arguments.only:
    previous_report=json.loads((OUT/f'{HOST}.json').read_text(encoding='utf-8'))
    assert previous_report['compiler_sha256']==hashlib.sha256(COMPILER.read_bytes()).hexdigest()
    previous={r['name']:r for r in previous_report['checks']}
records=[]
for name in names:
    if arguments.only and name not in arguments.only:records.append(previous[name]);continue
    command=[sys.executable,f'tests/test-{name}.py'];start=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,
        env=dict(os.environ,PYTHONIOENCODING='utf-8',ASSIS_PLATFORM_EVIDENCE=str(OUT/'windows-provider.json')))
    content=result.stdout+result.stderr;log=f'{HOST}-{name}.log'
    (OUT/log).write_text(content,encoding='utf-8',newline='\n')
    count=re.search(r'Ran (\d+) tests?',content);skip=re.search(r'skipped=(\d+)',content)
    total=int(count[1]) if count else 0;not_run=int(skip[1]) if skip else 0
    records.append(dict(name=name,returncode=result.returncode,registered=total,executed=total-not_run,
        not_run=not_run,seconds=time.monotonic()-start,command=['python',command[1]],log=log,
        log_sha256=hashlib.sha256(content.encode()).hexdigest()))
    print(name,'PASS' if result.returncode==0 and total else 'FAIL',flush=True)
report=dict(schema='assisscript-transactions-native-v1',platform=platform.platform(),python=sys.version,
    compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),checks=records,
    passed=all(r['returncode']==0 and r['executed']>0 for r in records),
    native_provider='tested' if os.name=='nt' else 'unsupported',
    targets_generated=['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'],
    other_native_targets='ARM64 and macOS not-run; generation is not execution',
    acceptance='real screen reader, OS DPI/multimonitor, IME and full HTDL/FS/SSC remain open')
(OUT/f'{HOST}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

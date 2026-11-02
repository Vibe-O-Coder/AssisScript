"""Run the page runtime and affected native regressions on the current host."""
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

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-runtime-2026-11-02'
OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux'
compiler=Path(os.environ['ASSIS_BIN']).resolve()
checks=[]
environment=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
names=['page-backend','page-host','pagevm','english-api','safe-default','ffi','system','packages',
    'optimization','complete-ir','functions','ownership-functions','generic-classes','collections-ast',
    'htdl-parser','reader-transactions','htdl-reader','htdl-viewer','graphemes','platform-window']
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='+',choices=names);args=parser.parse_args()
if args.only:
    prior=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))
    checks=[c for c in prior['checks'] if c['name'] not in args.only];names=args.only
for name in names:
    command=[sys.executable,str(ROOT/'tests'/f'test-{name}.py')];started=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,timeout=300)
    log=result.stdout+result.stderr
    path=OUT/f'{host}-{name}.log';path.write_bytes(log)
    count=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log)
    total=int(count[1]) if count else 0;not_run=int(skipped[1]) if skipped else 0
    record=dict(name=name,command=[Path(command[0]).name,f'tests/test-{name}.py'],returncode=result.returncode,
        executed=total-not_run,not_run=not_run,seconds=round(time.monotonic()-started,3),
        log=path.name,log_sha256=hashlib.sha256(log).hexdigest())
    checks.append(record)
    print(f'{host} {name}: code={result.returncode}, executed={total-not_run}, not-run={not_run}',flush=True)
record=dict(platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    checks=checks,passed=all(c['returncode']==0 for c in checks))
(OUT/f'{host}.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if record['passed'] else 1)

"""Collect current-host worker execution and affected regression evidence."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-worker-2026-11-02';OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve()
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker-only',action='store_true');parser.add_argument('--only',nargs='+');args=parser.parse_args()
checks=[]
names=[('page-worker','optimized'),('page-worker','reference')]+[(n,'both') for n in ['page-host','pagevm','page-backend','htdl-parser','process','ffi','safe-default','ownership-functions']]
if args.worker_only or args.only:
    selected=['page-worker'] if args.worker_only else args.only
    assert set(selected)<=set(n for n,m in names)
    checks=[c for c in json.loads((OUT/f'{host}.json').read_text())['checks'] if c['name'] not in selected];names=[(n,m) for n,m in names if n in selected]
for name,mode in names:
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',ASSIS_WORKER_NO_OPT='1' if mode=='reference' else '0')
    command=[sys.executable,str(ROOT/'tests'/f'test-{name}.py')];started=time.monotonic()
    r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);log=r.stdout+r.stderr
    path=OUT/f'{host}-{name}-{mode}.log';path.write_bytes(log)
    count=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log)
    total=int(count[1]) if count else 0;not_run=int(skipped[1]) if skipped else 0
    check=dict(name=name,mode=mode,command=[Path(command[0]).name,f'tests/test-{name}.py'],returncode=r.returncode,executed=total-not_run,not_run=not_run,
        seconds=round(time.monotonic()-started,3),log=path.name,log_sha256=hashlib.sha256(log).hexdigest())
    if name=='page-worker':
        marker=re.search(rb'WORKER_CANDIDATE (\{[^\r\n]+\})',log)
        if marker:check['candidates']=json.loads(marker[1])
    checks.append(check);print(f'{host} {name}/{mode}: {r.returncode}; {total-not_run} executed, {not_run} not-run',flush=True)
report=dict(platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=checks,passed=all(c['returncode']==0 and c['executed']>0 for c in checks))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

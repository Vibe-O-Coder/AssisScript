"""Record fresh native executions; skipped tests are never counted as passes."""
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

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-windows-isolation-2026-11-02';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='+');args=parser.parse_args()
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve()
jobs=[(n,m) for n in ['windows-isolation','page-compiler','page-worker','page-reader'] for m in ['optimized','reference']]
jobs += [(n,'both') for n in ['page-host','page-backend','pagevm','htdl-parser','reader-transactions','safe-default','ownership-functions','functions']]
checks=[]
if args.only:
    assert set(args.only)<=set(n for n,m in jobs)
    previous=OUT/f'{host}.json';checks=[c for c in json.loads(previous.read_text())['checks'] if c['name'] not in args.only] if previous.exists() else []
    jobs=[(n,m) for n,m in jobs if n in args.only]
for name,mode in jobs:
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',ASSIS_WORKER_NO_OPT='1' if mode=='reference' else '0')
    started=time.monotonic();command=[sys.executable,str(ROOT/'tests'/f'test-{name}.py')]
    r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
    log=r.stdout+r.stderr;path=OUT/f'{host}-{name}-{mode}.log';path.write_bytes(log)
    count=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log)
    total=int(count[1]) if count else 0;not_run=int(skipped[1]) if skipped else 0
    item=dict(name=name,mode=mode,command=[Path(command[0]).name,f'tests/test-{name}.py'],returncode=r.returncode,
        executed=total-not_run,not_run=not_run,seconds=round(time.monotonic()-started,3),log=path.name,log_sha256=hashlib.sha256(log).hexdigest())
    marker=re.search(rb'(?:ISOLATION_CANDIDATE|COMPILER_CANDIDATE|PAGE_READER_CANDIDATE|WORKER_CANDIDATE) (\{[^\r\n]+\})',log)
    if marker:item['candidates']=json.loads(marker[1])
    checks.append(item);print(f'{host} {name}/{mode}: {r.returncode}; {total-not_run} executed, {not_run} not-run',flush=True)
report=dict(platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=checks,
    passed=all(c['returncode']==0 and (c['executed']>0 or c['name']=='windows-isolation' and os.name!='nt' and c['not_run']==4) for c in checks))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

"""Run the Frame/worker integration and affected native regressions; checkpoint each result."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m3-frame-worker-2026-11-03'
BASE='52ef3ead2e059395dafb17771214126f578ed19c'
SUITES=[('frame-worker','optimized'),('frame-worker','reference'),('page-worker','optimized'),('page-worker','reference'),('page-reader','optimized'),('page-reader','reference'),('page-compiler','optimized'),('page-host','optimized'),('page-backend','optimized'),('pagevm','optimized'),('windows-isolation','optimized'),('framehost','optimized'),('catalog-frame','optimized'),('install-mask','optimized')]
host='windows' if os.name=='nt' else 'linux'
OUT.mkdir(parents=True,exist_ok=True)
compiler=Path(os.environ['ASSIS_BIN']).resolve();records=[]
if '--resume' in sys.argv:
    previous=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))
    assert previous['compiler_sha256']==hashlib.sha256(compiler.read_bytes()).hexdigest()
    records=[r for r in previous['checks'] if r['returncode']==0]
def checkpoint():
    for record in records:record['status']='executed' if record['executed'] else 'not-run'
    report=dict(schema='frame-worker-host-v1',base=BASE,host=host,platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=records,passed=len(records)==len(SUITES) and all(x['returncode']==0 and x['executed']+x['not_run']>0 for x in records))
    (OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
for suite,mode in SUITES:
    if any(r['suite']==suite and r['worker_mode']==mode for r in records):continue
    start=time.monotonic();command=[sys.executable,str(ROOT/'tests'/f'test-{suite}.py')]
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',ASSIS_WORKER_NO_OPT=str(int(mode=='reference')))
    result=subprocess.run(command,cwd=ROOT,capture_output=True,env=env,timeout=600)
    output=result.stdout+result.stderr;log=OUT/f'{host}-{suite}-{mode}.log';log.write_bytes(output)
    ran=re.search(rb'Ran (\d+) tests? in',output);skipped=re.search(rb'skipped=(\d+)',output);omitted=int(skipped[1]) if skipped else 0
    records.append(dict(suite=suite,worker_mode=mode,command=['python',f'tests/test-{suite}.py'],returncode=result.returncode,executed=int(ran[1])-omitted if ran else 0,not_run=omitted,seconds=round(time.monotonic()-start,3),log=log.name,sha256=hashlib.sha256(output).hexdigest()))
    checkpoint();print(f'{host} {suite} {mode}: rc={result.returncode}, {records[-1]["executed"]} executed/{omitted} not-run',flush=True)
    if result.returncode:
        print(output.decode(errors='replace')[-7000:]);raise SystemExit(1)
checkpoint()

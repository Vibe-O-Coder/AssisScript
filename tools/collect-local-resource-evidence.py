"""Checkpoint exact native resource/UI regressions without promoting skips."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m3-local-resources-2026-11-04'
BASE='33b7431da1e84c8cdc26a8639290e42ba5a14e72'
SUITES=[('page-resources','optimized'),('page-resources','reference'),('frame-responsiveness','optimized'),
    ('frame-worker','optimized'),('frame-worker','reference'),('framehost','optimized'),('framereader','optimized'),
    ('catalog-frame','optimized'),('reader-transactions','optimized'),('motionpage','optimized'),('pagepresent','optimized'),('install-mask','optimized')]
host='windows' if os.name=='nt' else 'linux';OUT.mkdir(parents=True,exist_ok=True)
compiler=Path(os.environ['ASSIS_BIN']).resolve();records=[]
if '--resume' in sys.argv:
    previous=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))
    assert previous['compiler_sha256']==hashlib.sha256(compiler.read_bytes()).hexdigest()
    records=[r for r in previous['checks'] if r['returncode']==0]
def checkpoint():
    report=dict(schema='local-resource-host-v1',base=BASE,host=host,platform=platform.platform(),python=sys.version,
        compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=records,
        passed=len(records)==len(SUITES) and all(r['returncode']==0 and r['executed']+r['not_run']>0 for r in records))
    (OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
for suite,mode in SUITES:
    if any(r['suite']==suite and r['worker_mode']==mode for r in records):continue
    start=time.monotonic();command=[sys.executable,str(ROOT/'tests'/f'test-{suite}.py')]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,
        env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',ASSIS_WORKER_NO_OPT=str(int(mode=='reference'))),timeout=600)
    output=result.stdout+result.stderr;log=OUT/f'{host}-{suite}-{mode}.log';log.write_bytes(output)
    ran=re.search(rb'Ran (\d+) tests? in',output);skipped=re.search(rb'skipped=(\d+)',output);omitted=int(skipped[1]) if skipped else 0
    records.append(dict(suite=suite,worker_mode=mode,command=['python',f'tests/test-{suite}.py'],returncode=result.returncode,
        executed=int(ran[1])-omitted if ran else 0,not_run=omitted,seconds=round(time.monotonic()-start,3),log=log.name,sha256=hashlib.sha256(output).hexdigest()))
    checkpoint();print(f'{host} {suite} {mode}: rc={result.returncode}, {records[-1]["executed"]} executed/{omitted} not-run',flush=True)
    if result.returncode:print(output.decode(errors='replace')[-7000:]);raise SystemExit(1)
checkpoint()

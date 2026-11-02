"""Fresh native HTDL/editor integration matrix. Skips remain not-run."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='+');args=parser.parse_args()
OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve()
jobs=[(name,'both') for name in ['htdl-catalog','htdl-parser','reader-transactions','htdl-reader','page-host']]
jobs += [('page-reader',mode) for mode in ['optimized','reference']]
records=[]
if args.only:
    assert set(args.only)<=set(n for n,_ in jobs)
    previous=OUT/f'{host}.json'
    if previous.exists():records=[r for r in json.loads(previous.read_text())['checks'] if r['name'] not in args.only]
    jobs=[(n,m) for n,m in jobs if n in args.only]
for name,mode in jobs:
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',ASSIS_WORKER_NO_OPT='1' if mode=='reference' else '0')
    started=time.monotonic();command=[sys.executable,str(ROOT/'tests'/f'test-{name}.py')]
    r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
    log=r.stdout+r.stderr;path=OUT/f'{host}-{name}-{mode}.log';path.write_bytes(log)
    total=re.search(rb'Ran (\d+) tests? in',log);skips=re.search(rb'skipped=(\d+)',log)
    count=int(total[1]) if total else 0;not_run=int(skips[1]) if skips else 0
    item=dict(name=name,mode=mode,returncode=r.returncode,executed=count-not_run,not_run=not_run,
              command=['python',f'tests/test-{name}.py'],seconds=round(time.monotonic()-started,3),log=path.name,log_sha256=hashlib.sha256(log).hexdigest())
    records.append(item);print(f'{host} {name}/{mode}: rc={r.returncode}, {count-not_run} executed/{not_run} not-run',flush=True)
report=dict(schema='htdl-catalog-native-v1',platform=platform.platform(),python=sys.version,
            base='f00d1ff95694dd312f90ec46d563606bda258356',compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=records,
            passed=all(r['returncode']==0 and r['executed']>0 for r in records))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

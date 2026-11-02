"""Fresh FS/SSC local-profile and native mask evidence, kept separate by host."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/ecossistema/evidencias/m3-presentation-core-2026-11-02';OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve();records=[]
for name in ['fluxstyle','sanscript','install-mask']:
    command=[sys.executable,str(ROOT/'tests'/f'test-{name}.py')];start=time.monotonic()
    r=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=240,
        env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',SSC_TRACE_OUTPUT=str(OUT/f'{host}-ssc-traces.json')))
    log=r.stdout+r.stderr;path=OUT/f'{host}-{name}.log';path.write_bytes(log)
    ran=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log);not_run=int(skipped[1]) if skipped else 0
    records.append(dict(name=name,command=command,returncode=r.returncode,executed=int(ran[1])-not_run if ran else 0,not_run=not_run,
        seconds=round(time.monotonic()-start,3),log=path.name,sha256=hashlib.sha256(log).hexdigest()))
    print(f'{host} {name}: rc={r.returncode}, {records[-1]["executed"]} executed/{not_run} not-run',flush=True)
for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
    command=[str(compiler),'run',str(ROOT/'exemplos/54_fluxstyle_sanscript.assis'),'--safe','--debug',*flags]
    r=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60);log=r.stdout+r.stderr;path=OUT/f'{host}-example-54-{mode}.log';path.write_bytes(log)
    assert r.returncode==0 and r.stdout==b'FLOW-TARGET -524288\nSSC-REST -524288 true\n' and not r.stderr,(r.returncode,log)
report=dict(schema='presentation-core-evidence-v1',base='6701d1b6d67687144606c03e2431c0f5a6ddf313',base_publication='blocked pending explicit user authorization',platform=platform.platform(),python=sys.version,
    compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),checks=records,passed=all(x['returncode']==0 and x['executed']>0 for x in records))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');raise SystemExit(0 if report['passed'] else 1)

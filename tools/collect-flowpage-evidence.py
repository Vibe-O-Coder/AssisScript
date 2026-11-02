"""Fresh whole-page transaction and affected document/Reader regressions."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m5-page-styles-2026-11-02'
OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux'
compiler=Path(os.environ['ASSIS_BIN']).resolve()
records=[]
for suite in ['flowpage','document-memory','document-tree','htdl-parser','htdl-catalog','fluxstyle','sanscript','reader-transactions','page-reader']:
    command=[sys.executable,str(ROOT/'tests'/f'test-{suite}.py')]
    started=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=420,
        env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',SSC_TRACE_OUTPUT=str(OUT/f'{host}-ssc-traces.json')))
    output=result.stdout+result.stderr
    path=OUT/f'{host}-{suite}.log';path.write_bytes(output)
    ran=re.search(rb'Ran (\d+) tests? in',output);skipped=re.search(rb'skipped=(\d+)',output)
    omitted=int(skipped[1]) if skipped else 0
    records.append(dict(name=suite,command=['python',f'tests/test-{suite}.py'],returncode=result.returncode,
        executed=int(ran[1])-omitted if ran else 0,not_run=omitted,seconds=round(time.monotonic()-started,3),
        log=path.name,sha256=hashlib.sha256(output).hexdigest()))
    print(f'{host} {suite}: rc={result.returncode}, {records[-1]["executed"]} executed/{omitted} not-run',flush=True)
    if result.returncode:break
report=dict(schema='flowpage-host-evidence-v1',base='f274c9f7d4dda1e1d9a7bfe92b172354b89a4203',
    platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    checks=records,passed=len(records)==9 and all(x['returncode']==0 and x['executed']>0 for x in records))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

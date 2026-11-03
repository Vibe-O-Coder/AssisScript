"""Execute catalog reading and the affected native regression matrix."""
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
OUT=ROOT/'docs/ecossistema/evidencias/m3-catalog-frame-2026-11-03'
OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux'
compiler=Path(os.environ['ASSIS_BIN']).resolve();records=[]
suites=['catalog-frame','htdl-catalog','framereader','framehost','motionpage','pageframe','pagepresent','flowpage','fluxstyle','sanscript','document-memory','htdl-parser','htdl-reader','reader-transactions']
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='+',choices=suites);args=parser.parse_args()
if args.only:
    old=json.loads((OUT/f'{host}.json').read_text());assert old['compiler_sha256']==hashlib.sha256(compiler.read_bytes()).hexdigest()
    records=[r for r in old['checks'] if r['name'] not in args.only]
def checkpoint():
    report=dict(schema='catalog-reading-host-evidence-v1',base='6f4398c830fadde4d809bbbac104a1fa4f22c711',
        platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
        checks=records,passed=len(records)==len(suites) and all(x['returncode']==0 and x['executed']>0 for x in records))
    (OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')

for suite in args.only or suites:
    started=time.monotonic();command=[sys.executable,str(ROOT/'tests'/f'test-{suite}.py')]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=600,env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8'))
    output=result.stdout+result.stderr;path=OUT/f'{host}-{suite}.log';path.write_bytes(output)
    ran=re.search(rb'Ran (\d+) tests? in',output);skipped=re.search(rb'skipped=(\d+)',output);omitted=int(skipped[1]) if skipped else 0
    records.append(dict(name=suite,command=['python',f'tests/test-{suite}.py'],returncode=result.returncode,
        executed=int(ran[1])-omitted if ran else 0,not_run=omitted,seconds=round(time.monotonic()-started,3),
        log=path.name,sha256=hashlib.sha256(output).hexdigest()))
    checkpoint()
    print(f'{host} {suite}: rc={result.returncode}, {records[-1]["executed"]} executed/{omitted} not-run',flush=True)
    if result.returncode:print(output.decode(errors='replace')[-8000:]);break
report=dict(schema='catalog-reading-host-evidence-v1',base='6f4398c830fadde4d809bbbac104a1fa4f22c711',
    platform=platform.platform(),python=sys.version,compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    checks=records,passed=len(records)==len(suites) and all(x['returncode']==0 and x['executed']>0 for x in records))
(OUT/f'{host}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

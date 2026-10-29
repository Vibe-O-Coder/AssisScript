"""Run all semantic/native Python suites and preserve exact results."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
suites=['evolution','generics','functions','generic-classes','collections-ast','ownership-functions','values','files','text-bytes','cli','numbers','packages','json','system','tooling','slices','managed-classes','backend-alpha9','optimization','english-api','release-policy','ffi','http','process','applications-bc','safe-default','net','move-enums','closures','usability','backend-evolution','complete-ir','increment','owned-mutation']
records=[];args.output.parent.mkdir(parents=True,exist_ok=True)
environment=os.environ.copy();environment['PYTHONIOENCODING']='utf-8'
for suite in suites:
    started=time.monotonic();result=subprocess.run([sys.executable,ROOT/f'tests/test-{suite}.py'],env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
    log=args.output.parent/(args.output.stem+'-'+suite+'.log');log.write_text(result.stdout+result.stderr,encoding='utf-8')
    match=re.search(r'Ran (\d+) tests?',result.stderr)
    records.append(dict(suite=suite,returnCode=result.returncode,tests=int(match[1]) if match else None,seconds=time.monotonic()-started,log=log.name))
    print(suite, 'PASS' if not result.returncode else 'FAIL',flush=True)
compiler=Path(os.environ.get('ASSIS_BIN',ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis')))
report=dict(platform=sys.platform,compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),testEnvironment=dict(tlsTimeoutMilliseconds=os.environ.get('ASSIS_TLS_TEST_TIMEOUT_MS','native defaults')),passed=all(r['returnCode']==0 for r in records),suites=records)
args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
raise SystemExit(0 if report['passed'] else 1)

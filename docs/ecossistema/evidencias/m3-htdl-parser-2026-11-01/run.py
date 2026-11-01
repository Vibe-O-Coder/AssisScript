"""Scoped native checks for the HTDL parser; requires a fresh ASSIS_BIN."""
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

ROOT = Path(__file__).resolve().parents[4]
DIRECTORY = Path(__file__).resolve().parent
HOST = 'windows' if os.name == 'nt' else 'linux' if sys.platform == 'linux' else 'macos'
COMPILER = Path(os.environ['ASSIS_BIN']).resolve()
commands = [(name, [sys.executable, f'tests/test-{name}.py']) for name in
            ['htdl-parser', 'document-memory', 'document-tree', 'buffer-preallocation',
             'english-api', 'packages', 'complete-ir', 'optimization']]
commands.append(('portability', [sys.executable, 'tools/test-portability.py', '--expect-host', 'x86_64',
                                 '--output', str(DIRECTORY / f'{HOST}-portability.json')]))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', nargs='+', choices=[name for name, command in commands])
args = parser.parse_args()
records = []
digest = hashlib.sha256(COMPILER.read_bytes()).hexdigest()
previous = {}
if args.only:
    report = json.loads((DIRECTORY / f'{HOST}.json').read_text(encoding='utf-8'))
    assert report['compiler_sha256'] == digest, 'Scoped rerun requires the same compiler'
    previous = {record['name']: record for record in report['checks']}
for name, command in commands:
    if args.only and name not in args.only:
        records.append(previous[name])
        continue
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=360,
                            env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    log = f'{HOST}-{name}.log'
    content = result.stdout + result.stderr
    (DIRECTORY / log).write_text(content, encoding='utf-8', newline='\n')
    count = re.search(r'Ran (\d+) tests?', content)
    skipped = re.search(r'skipped=(\d+)', content)
    registered = int(count[1]) if count else None
    not_run = int(skipped[1]) if skipped else 0
    # Avoid user-specific executable paths in this public evidence.
    display = ['python', f'tests/test-{name}.py'] if name != 'portability' else ['python', 'tools/test-portability.py', '--expect-host', 'x86_64', '--output', f'{HOST}-portability.json']
    records.append(dict(name=name, command=display, returncode=result.returncode,
                        registered=registered, not_run=not_run,
                        executed=registered-not_run if registered is not None else None,
                        seconds=time.monotonic()-start, log=log))
    print(name, 'PASS' if result.returncode == 0 else 'FAIL', flush=True)
report = dict(schema='assisscript-htdl-parser-host-v1', platform=platform.platform(),
              python=sys.version, compiler=COMPILER.name,
              compiler_sha256=digest,
              passed=all(r['returncode'] == 0 for r in records), checks=records,
              other_native_targets={'macos-x64': 'not-run', 'linux-arm64': 'not-run', 'macos-arm64': 'not-run'},
              product={'window': 'not-run', 'accessibility': 'not-run', 'remote-page': 'unsupported', 'full-htdl-0.1': 'unsupported'})
(DIRECTORY / f'{HOST}.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
raise SystemExit(0 if report['passed'] else 1)

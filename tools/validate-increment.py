"""Record a rebuilt increment candidate and the affected semantic regressions.

ASSIS_BIN selects the compiler. This runs programs on the current host only;
the increment suite also generates the five native output formats.
"""
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

ROOT = Path(__file__).resolve().parent.parent
SUITES = ['increment', 'evolution', 'numbers', 'ownership-functions',
          'optimization', 'backend-evolution', 'complete-ir']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    compiler = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' /
                    ('assis.exe' if os.name == 'nt' else 'assis'))).resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment['ASSIS_BIN'] = str(compiler)
    environment['PYTHONIOENCODING'] = 'utf-8'
    records = []
    for suite in SUITES:
        command = [sys.executable, str(ROOT / f'tests/test-{suite}.py')]
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=ROOT, env=environment,
                                    capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', timeout=240)
            code, log = result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired as error:
            code = None
            log = (error.stdout or b'').decode('utf-8', errors='replace')
            log += (error.stderr or b'').decode('utf-8', errors='replace')
            log += '\nTIMEOUT after 240 seconds\n'
        path = output.parent / f'{output.stem}-{suite}.log'
        path.write_text(log, encoding='utf-8', newline='\n')
        count = re.search(r'Ran (\d+) tests?', log)
        state = 'pass' if code == 0 and count else 'fail'
        records.append(dict(suite=suite, state=state, return_code=code,
                            tests=int(count[1]) if count else None,
                            seconds=round(time.monotonic() - started, 3),
                            log=path.name, log_sha256=digest(path),
                            command=[Path(sys.executable).name, f'tests/test-{suite}.py']))
        print(f'{suite}: {state}', flush=True)
    inputs = ['src/assisc.c', 'src/frontend.h', 'src/lexer.h',
              'tools/validate-increment.py', 'tests/test-evolution.py']
    inputs += [f'tests/test-{suite}.py' for suite in SUITES if suite != 'evolution']
    report = dict(schema='assisscript-increment-candidate-v1',
                  base_revision='1ed22f5c898f21f06c429774992469177bdfd3d9',
                  platform=sys.platform, host=platform.platform(),
                  architecture=platform.machine(), python=platform.python_version(),
                  compiler_sha256=digest(compiler),
                  inputs={name: digest(ROOT / name) for name in inputs},
                  native_execution='current host only; optimized and reference',
                  foreign_native_execution='not-run',
                  product_integration='not-run',
                  passed=all(record['state'] == 'pass' for record in records),
                  suites=records)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

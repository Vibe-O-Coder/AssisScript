"""Validate a generational arena candidate; retain source identity and native test logs.

ASSIS_BIN selects a freshly built compiler. Foreign output generation in the
tests does not count as native execution. Skipped tests cannot produce pass.
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
SUITES = ['arena', 'owned-mutation', 'move-enums', 'ownership-functions',
          'managed-classes', 'english-api', 'complete-ir']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    compiler = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' /
                    ('assis.exe' if os.name == 'nt' else 'assis'))).resolve()
    environment = dict(os.environ, ASSIS_BIN=str(compiler), PYTHONIOENCODING='utf-8')
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
            log = ''.join(value.decode('utf-8', errors='replace') if isinstance(value, bytes)
                          else value or '' for value in (error.stdout, error.stderr))
            log += '\nTIMEOUT after 240 seconds\n'
        path = output.parent / f'{output.stem}-{suite}.log'
        path.write_text(log, encoding='utf-8', newline='\n')
        count = re.search(r'Ran (\d+) tests?', log)
        skipped = re.search(r'skipped=(\d+)', log)
        not_run = int(skipped[1]) if skipped else 0
        state = 'fail' if code != 0 or not count else 'not-run' if not_run else 'pass'
        records.append(dict(suite=suite, state=state, return_code=code,
                            tests=int(count[1]) if count else None, not_run=not_run,
                            seconds=round(time.monotonic() - started, 3),
                            log=path.name, log_sha256=digest(path),
                            command=[Path(sys.executable).name, f'tests/test-{suite}.py']))
        print(f'{suite}: {state}', flush=True)
    inputs = sorted(list((ROOT / 'src').glob('*')) + list((ROOT / 'stdlib').glob('*.assis')))
    inputs += [ROOT / f'tests/test-{suite}.py' for suite in SUITES]
    inputs += [ROOT / 'tests/test-evolution.py', Path(__file__).resolve(),
               ROOT / 'exemplos/34_generational_arena.assis']
    report = dict(schema='assisscript-arena-candidate-v1',
                  base_revision='ebe5928999d8e01e5b224a2c211ba1b575dee783',
                  platform=sys.platform, host=platform.platform(),
                  architecture=platform.machine(), python=platform.python_version(),
                  compiler_sha256=digest(compiler),
                  inputs={path.relative_to(ROOT).as_posix(): digest(path) for path in inputs if path.is_file()},
                  native_execution='current host only; optimized and reference',
                  foreign_native_execution='not-run', product_integration='not-run',
                  passed=all(record['state'] == 'pass' for record in records), suites=records)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

"""Run boundary and ownership evidence for the trusted Windows platform provider.

Unsupported hosts explicitly report unsupported (exit 2); never count skipped
Windows tests as pass. ASSIS_BIN selects a compiler rebuilt for this candidate.
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
SUITES = ['platform-window', 'ffi', 'ownership-functions', 'managed-classes',
          'english-api', 'arena', 'complete-ir']
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(schema='assisscript-platform-candidate-v1',
                  base_revision='6208ecb5bd5801defcd9c0e6b1809ba731a942db',
                  platform=sys.platform, host=platform.platform(), architecture=platform.machine(),
                  python=platform.python_version(), provider='User32/GDI; Windows 10 1703+ x64',
                  foreign_native_provider_execution='not-run', htdl_integration='not-run',
                  sandbox='not-run', passed=False, suites=[])
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        report['state'] = 'unsupported'
        output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
        print('Windows x64 provider: unsupported on this host')
        return 2
    compiler = Path(os.environ.get('ASSIS_BIN', ROOT/'bin/assis.exe')).resolve()
    report['compiler_sha256'] = digest(compiler)
    environment = dict(os.environ, ASSIS_BIN=str(compiler), PYTHONIOENCODING='utf-8')
    provider_evidence = output.parent/f'{output.stem}-provider.json'
    environment['ASSIS_PLATFORM_EVIDENCE'] = str(provider_evidence)
    for suite in SUITES:
        command = [sys.executable, str(ROOT/f'tests/test-{suite}.py')]
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=240)
            code, log = result.returncode, result.stdout+result.stderr
        except subprocess.TimeoutExpired as error:
            code = None
            log = ''.join(v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v or ''
                          for v in (error.stdout, error.stderr))+'\nTIMEOUT after 240 seconds\n'
        log_file = output.parent/f'{output.stem}-{suite}.log'
        log_file.write_text(log, encoding='utf-8', newline='\n')
        count = re.search(r'Ran (\d+) tests?', log); skipped = re.search(r'skipped=(\d+)', log)
        state = 'fail' if code != 0 or not count else 'not-run' if skipped else 'pass'
        report['suites'].append(dict(suite=suite, state=state, return_code=code,
            tests=int(count[1]) if count else 0, seconds=round(time.monotonic()-started, 3),
            log=log_file.name, log_sha256=digest(log_file), command=[Path(sys.executable).name,f'tests/test-{suite}.py']))
        print(f'{suite}: {state}', flush=True)
    compiler_inputs = [p for p in sorted((ROOT/'src').glob('*'))
                       if p.name not in ('install_files.inc','install_optional.inc','windows_setup.c')]
    paths = [*compiler_inputs, *sorted((ROOT/'stdlib').glob('*.assis')),
             *sorted((ROOT/'providers/platform').glob('*')), ROOT/'tests/platform-oracle.c', ROOT/'tests/platform-version-fixture.c',
             ROOT/'tests/test-evolution.py', ROOT/'tools/build-platform.py', Path(__file__).resolve(),
             ROOT/'exemplos/35_native_window.assis', *[ROOT/f'tests/test-{s}.py' for s in SUITES]]
    report['inputs'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths if p.is_file()}
    if provider_evidence.is_file():
        report['provider_evidence'] = dict(path=provider_evidence.name, sha256=digest(provider_evidence))
    report['passed'] = all(s['state']=='pass' for s in report['suites'])
    report['state'] = 'pass' if report['passed'] else 'fail'
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())

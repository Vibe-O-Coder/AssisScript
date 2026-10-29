"""Run the nested-div probe and preserve hashes; does not certify HTDL."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


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
    command = [sys.executable, 'tests/test-htdl-readiness.py']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=240,
                            env=dict(os.environ, ASSIS_BIN=str(compiler), PYTHONIOENCODING='utf-8'))
    log = output.with_suffix('.log')
    log.write_text(result.stdout + result.stderr, encoding='utf-8', newline='\n')
    count = re.search(r'Ran (\d+) tests?', result.stderr)
    skipped = re.search(r'skipped=(\d+)', result.stderr)
    state = 'fail' if result.returncode or not count else 'not-run' if skipped else 'pass'
    inputs = ['tests/fixtures/htdl-core.assis', 'tests/test-htdl-readiness.py',
              'tests/test-evolution.py', 'stdlib/unicode.assis', 'tools/validate-microformat.py',
              'src/assisc.c', 'src/frontend.h', 'src/lexer.h', 'src/version.h']
    report = dict(schema='assisscript-microformat-candidate-v1', profile='nested-div-probe-v1',
                  base_revision='9c09baf934eb2ae6a73dd7a15df4d8fa3c30717f',
                  state=state, return_code=result.returncode, tests=int(count[1]) if count else None,
                  not_run=int(skipped[1]) if skipped else 0,
                  host=platform.platform(), architecture=platform.machine(), python=platform.python_version(),
                  compiler_sha256=digest(compiler), command=[Path(sys.executable).name, command[1]],
                  inputs={name: digest(ROOT / name) for name in inputs},
                  log=log.name, log_sha256=digest(log),
                  foreign_native_execution='not-run', htdl_conformance='not-run', product_integration='not-run')
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{state}: {report["tests"]} tests; HTDL conformance not-run')
    return 0 if state == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())

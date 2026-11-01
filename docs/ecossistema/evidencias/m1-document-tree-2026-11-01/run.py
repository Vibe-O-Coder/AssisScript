"""Reproduce this unit's scoped native checks; ASSIS_BIN selects a fresh build."""
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
shared = [
    'shared_and_transient_limits_and_return_of_quota',
    'zero_limits_negative_extreme_and_exact_boundaries',
    'stale_forged_cross_instance_reset_and_closed_ids',
    'retirement_and_ten_thousand_recycles',
    'operations_against_independent_bytearray_model',
    'private_storage_and_borrow_conflicts_are_rejected',
    'invalid_access_and_constructor_contracts_trap',
    'example_ir_and_all_five_formats',
]
commands = [
    ('document-tree', [sys.executable, 'tests/test-document-tree.py']),
    ('buffer-preallocation', [sys.executable, 'tests/test-buffer-preallocation.py']),
    ('shared-buffer-budget-selected', [sys.executable, 'tests/test-shared-buffer-budget.py',
        *['SharedBufferBudget.test_' + name for name in shared]]),
    *[(name, [sys.executable, f'tests/test-{name}.py'])
      for name in ['owned-mutation', 'english-api', 'packages']],
    ('portability', [sys.executable, 'tools/test-portability.py', '--expect-host', 'x86_64',
        '--output', str(DIRECTORY / f'{HOST}-portability.json')]),
]
records = []
environment = dict(os.environ, PYTHONIOENCODING='utf-8')
for name, command in commands:
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
        encoding='utf-8', errors='strict', timeout=240, env=environment)
    log = f'{HOST}-{name}.log'
    content = result.stdout + result.stderr
    (DIRECTORY / log).write_text(content, encoding='utf-8', newline='\n')
    tests = re.search(r'Ran (\d+) tests?', content)
    skips = re.search(r'skipped=(\d+)', content)
    registered = int(tests[1]) if tests else None
    not_run = int(skips[1]) if skips else 0
    records.append(dict(name=name, command=command, returncode=result.returncode,
        registered=registered, not_run=not_run,
        executed=registered-not_run if registered is not None else None,
        seconds=time.monotonic()-start, log=log))
    print(name, 'PASS' if result.returncode == 0 else 'FAIL', flush=True)
report = dict(schema='assisscript-document-tree-host-v1', platform=platform.platform(),
    python=sys.version, compiler=str(COMPILER),
    compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
    passed=all(record['returncode'] == 0 for record in records), checks=records)
(DIRECTORY / f'{HOST}.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
raise SystemExit(0 if report['passed'] else 1)

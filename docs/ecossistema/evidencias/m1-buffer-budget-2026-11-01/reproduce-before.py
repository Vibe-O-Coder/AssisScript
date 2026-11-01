"""Reproduce independent ByteBuffer limits; this is not the new pool API."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[3]
compiler = Path(os.environ['ASSIS_BIN']).resolve()
source = DIRECTORY / 'before.assis'
records = []
for flags in [[], ['--no-opt']]:
    command = [str(compiler), 'run', str(source), '--debug', *flags]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
    records.append(dict(command=command, flags=flags, returnCode=result.returncode,
                        stdout=result.stdout, stderr=result.stderr))
    assert (result.returncode, result.stdout, result.stderr) == (0, '16\n', ''), records
report = dict(compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), cases=records)
host = 'windows' if os.name == 'nt' else 'linux' if sys.platform == 'linux' else sys.platform
(DIRECTORY / f'{host}-before.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
print('Before: two independent 12-byte limits permit 16 aggregate payload bytes')

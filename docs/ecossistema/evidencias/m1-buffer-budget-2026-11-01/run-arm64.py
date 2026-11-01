"""Complementary Linux ARM64 emulation; does not certify native ARM64."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[3]
compiler = Path(os.environ['ASSIS_BIN']).resolve()
source = ROOT / 'exemplos/39_shared_buffer_budget.assis'
records = []
for flags in [[], ['--no-opt']]:
    binary = ROOT / 'build' / ('buffer-budget-arm64-reference' if flags else 'buffer-budget-arm64')
    command = [str(compiler), 'build', str(source), '--target', 'linux-arm64', '--debug', '-o', str(binary), *flags]
    built = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert built.returncode == 0, built.stderr
    result = subprocess.run(['qemu-aarch64', str(binary)], capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert (result.returncode, result.stdout, result.stderr) == (0, '8 42\n0 1\n', '')
    records.append(dict(build_command=command, run_command=['qemu-aarch64', str(binary)], flags=flags,
                        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                        returnCode=result.returncode, stdout=result.stdout, stderr=result.stderr))
report = dict(execution='qemu-aarch64', native=False, compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), cases=records)
(DIRECTORY / 'arm64-emulated.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
print('ARM64 emulated: 2/2; native ARM64 remains not-run')

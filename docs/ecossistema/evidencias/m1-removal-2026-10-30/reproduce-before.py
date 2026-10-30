"""Reproduce the old allocating removal under OS refusal; requires ASSIS_BIN."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = '17ac155b8a7e37f413696ab562063e3d71e61e51'
spec = importlib.util.spec_from_file_location('slots', ROOT / 'tests/test-fallible-slots.py')
slots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slots)


def main():
    windows = os.name == 'nt'
    assert platform.machine().lower() in ('amd64', 'x86_64')
    assert windows or platform.system() == 'Linux'
    test = slots.FallibleSlots('test_targets_and_ir')
    test.setUp()
    try:
        cc = str(Path(os.environ.get('ASSIS_TOOLCHAIN_BIN', 'C:/msys64/ucrt64/bin')) / 'gcc.exe') if windows else 'cc'
        library = test.temp / ('fault.dll' if windows else 'fault.so')
        env = dict(os.environ, PATH=str(Path(cc).parent) + os.pathsep + os.environ.get('PATH', ''))
        subprocess.run([cc, '-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-shared', '-fPIC',
            str(ROOT / ('tests/allocation-fault-windows.c' if windows else 'tests/allocation-fault-linux.c')),
            '-o', str(library)], env=env, check=True, capture_output=True)
        baseline = test.temp / 'baseline-arena.assis'
        baseline.write_bytes(subprocess.check_output(['git', 'show', BASE + ':stdlib/arena.assis'], cwd=ROOT))
        text = Path(__file__).with_name('before.assis').read_text(encoding='utf-8')
        text = text.replace('TEST_FIXTURE_PATH', library.as_posix()).replace('BASELINE_ARENA_PATH', baseline.as_posix())
        source = test.source(text)
        results = []
        for flags in [[], ['--no-opt']]:
            binary = test.temp / 'before.exe'
            built = test.invoke('build', source, '--debug', '-o', binary, *flags)
            assert built.returncode == 0, built.stderr
            result = subprocess.run([str(binary)], capture_output=True, text=True, encoding='utf-8', timeout=20)
            assert result.returncode == 70 and 'R001' in result.stderr, result
            results.append(dict(flags=flags, returnCode=result.returncode, stdout=result.stdout, stderr=result.stderr))
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        test.doCleanups()


if __name__ == '__main__':
    main()

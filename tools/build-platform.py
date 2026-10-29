"""Build the optional trusted Windows x64 provider; no package or release promotion."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import platform

ROOT = Path(__file__).resolve().parent.parent

def build(output, testing=False, cc=None):
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('Windows x64 provider: unsupported on this host')
    compiler = cc or os.environ.get('CC') or shutil.which('gcc') or str(
        Path(os.environ.get('ASSIS_TOOLCHAIN_BIN', 'C:/msys64/ucrt64/bin')) / 'gcc.exe')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [compiler, '-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Werror',
               '-shared', '-static-libgcc', '-Wl,--no-insert-timestamp']
    if testing:
        command.append('-DASSISP_TESTING')
    command += [str(ROOT / 'providers/platform/windows.c'), '-o', str(output), '-luser32', '-lgdi32']
    environment = dict(os.environ, PATH=str(Path(compiler).parent) + os.pathsep + os.environ.get('PATH', ''))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    return command

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/platform/assis_platform_v1.dll')
    parser.add_argument('--testing', action='store_true')
    parser.add_argument('--cc')
    args = parser.parse_args()
    build(args.output, args.testing, args.cc)
    print(args.output)

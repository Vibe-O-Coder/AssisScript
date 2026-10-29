"""Rebuild generated runtime headers and the compiler without a build cache.

Copies only source inputs into a temporary tree, never local bin/build/dist.
Runs the native evolution tests against that clean compiler.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', default='gcc')
parser.add_argument('--binutils-dir')
parser.add_argument('--compare-binary',type=Path,help='Candidate binary to reproduce; default is the installed workspace compiler')
suites=['evolution','generics','functions','generic-classes','collections-ast','ownership-functions','values','files','text-bytes','cli','numbers','packages','json','system','tooling','slices','managed-classes','backend-alpha9','optimization','english-api','release-policy','ffi','http','process','applications-bc','safe-default','net','move-enums','closures','usability','backend-evolution','complete-ir']
parser.add_argument('--suite',action='append',choices=suites,help='Limit validation to named suites; default runs the complete matrix')
args = parser.parse_args()
cc = shutil.which(args.cc)
if not cc:
    parser.error('Compilador C não encontrado')
environment = os.environ.copy()
environment['PATH'] = str(Path(cc).parent) + os.pathsep + environment.get('PATH', '')
if args.binutils_dir:
    environment['BINUTILS_DIR'] = args.binutils_dir
with tempfile.TemporaryDirectory(prefix='assis-clean-') as temp:
    folder = Path(temp)
    (folder / 'tools').mkdir()
    (folder / 'bin').mkdir()
    shutil.copytree(ROOT / 'src', folder / 'src')
    shutil.copytree(ROOT / 'assets', folder / 'assets')
    shutil.copytree(ROOT / 'stdlib', folder / 'stdlib')
    shutil.copytree(ROOT / 'exemplos', folder / 'exemplos')
    shutil.copy2(ROOT / 'tools/embed-runtime.py', folder / 'tools/embed-runtime.py')
    # Remove only these generated files from the temporary copy to require their regeneration.
    for name in ['runtime_blob.h', 'runtime_win_blob.h','runtime_macos_blob.h']:
        (folder / 'src' / name).unlink()
    subprocess.run([sys.executable, folder / 'tools/embed-runtime.py'], cwd=folder, env=environment, check=True)
    if os.name!='nt':
        shutil.copy2(ROOT/'tools/embed-arm64.py',folder/'tools/embed-arm64.py')
        for name in ('runtime_arm64_linux.h','runtime_arm64_macos.h'):(folder/'src'/name).unlink()
        subprocess.run([sys.executable,folder/'tools/embed-arm64.py'],cwd=folder,env=environment,check=True)
    binary = folder / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis')
    flags = ['-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Wno-misleading-indentation', '-s']
    if os.name == 'nt':
        flags += ['-static', '-municode', '-static-libgcc', '-Wl,--no-insert-timestamp']
    resources=[]
    if os.name=='nt':
        resource=folder/'icon.o'
        subprocess.run([str(Path(cc).with_name('windres.exe')),'assets/compiler.rc','-O','coff','-o',str(resource)],cwd=folder,env=environment,check=True)
        resources=[str(resource)]
    subprocess.run([cc, *flags, folder / 'src/assisc.c', *resources, '-o', binary], cwd=folder, env=environment, check=True)
    environment['ASSIS_BIN'] = str(binary)
    for suite in args.suite or suites:
        subprocess.run([sys.executable, ROOT / ('tests/test-' + suite + '.py')], env=environment, check=True)
    installed = (args.compare_binary or ROOT / 'bin' / binary.name).resolve()
    record = dict(platform=sys.platform, compiler=cc,
                  cleanBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  workspaceBinarySha256=hashlib.sha256(installed.read_bytes()).hexdigest())
    record['identicalToWorkspaceBinary'] = record['cleanBinarySha256'] == record['workspaceBinarySha256']
    (ROOT / 'build').mkdir(exist_ok=True)
    output = ROOT / 'build' / ('clean-' + sys.platform + '.json')
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2))
    if not record['identicalToWorkspaceBinary']:
        diagnostic = ROOT / 'build' / ('clean-diff-' + sys.platform)
        diagnostic.mkdir(exist_ok=True)
        shutil.copy2(binary, diagnostic / binary.name)
        for name in ['runtime_blob.h', 'runtime_win_blob.h','runtime_macos_blob.h']:
            shutil.copy2(folder / 'src' / name, diagnostic / name)
        raise AssertionError('A reconstrução limpa não reproduziu o binário do workspace')

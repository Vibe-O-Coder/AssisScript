"""Build a matched Windows development bundle; never promote historical bin/.

Default: prepare and verify an isolated install. --prepare-only makes no claim
of installation verification. No user PATH, associations or live prefix change.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent.parent
EVIDENCE=ROOT/'docs/ecossistema/evidencias/m5-page-frame-2026-11-02'
STAGE=ROOT/'build/development-windows-20261102'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    if os.name!='nt':raise SystemExit('This development bundle targets Windows x64')
    candidate=ROOT/'build/assis.exe'
    native=json.loads((EVIDENCE/'windows.json').read_text(encoding='utf-8'))
    if not native['passed'] or native['compiler_sha256']!=sha(candidate):
        raise SystemExit('Fresh candidate does not match the recorded passing native matrix')
    # Refuse a damaged/mixed library closure before copying. The catalog controls
    # names and dependencies, not filenames inferred from a previous release.
    catalog=json.loads((ROOT/'stdlib/catalogo.json').read_text(encoding='utf-8'))
    names={json.loads(line[1:-1]).replace('\\','/') for line in (ROOT/'src/install_files.inc').read_text(encoding='utf-8').splitlines() if line.startswith('L')}
    names.update('stdlib/'+lib['name']+'.assis' for lib in catalog['libraries'])
    names.update(['bin/assis_platform_v1.dll','BUILD-INFO.json'])
    for name in sorted(names-{'bin/assis_platform_v1.dll','BUILD-INFO.json'}):
        source=candidate if name=='bin/assis.exe' else ROOT/name
        target=STAGE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    cc=Path(os.environ.get('ASSIS_TOOLCHAIN_BIN','C:/msys64/ucrt64/bin'))/'gcc.exe'
    environment=dict(os.environ,PATH=str(cc.parent)+os.pathsep+os.environ.get('PATH',''),PYTHONUTF8='1')
    subprocess.run([str(cc),'-O2','-std=c11','-municode','-static','-static-libgcc','-Wl,--no-insert-timestamp',
        'src/assisc.c','-o',str(STAGE/'bin/assis.exe')],cwd=ROOT,env=environment,check=True)
    if sha(STAGE/'bin/assis.exe')!=native['compiler_sha256']:
        raise SystemExit('Rebuilt sources differ from the tested compiler; run the native matrix before packaging')
    provider=[str(cc),'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Werror','-shared','-static-libgcc',
        '-Wl,--no-insert-timestamp',str(ROOT/'providers/platform/windows.c'),'-o',str(STAGE/'bin/assis_platform_v1.dll'),
        '-luser32','-lgdi32','-loleacc','-loleaut32','-lole32','-luuid']
    subprocess.run(provider,cwd=ROOT,env=environment,check=True)
    # Private manifest adds the matching provider and build identity only to this
    # Windows development distribution, preserving the cross-platform release.
    source_dir=ROOT/'build/development-installer-source';source_dir.mkdir(parents=True,exist_ok=True)
    for name in ['windows_setup.c','install_optional.inc','version.h']:
        shutil.copyfile(ROOT/'src'/name,source_dir/name)
    manifest='/* Matched development bundle; not a release manifest. */\n'
    manifest+=''.join('L'+json.dumps(name.replace('/','\\'))+',\n' for name in sorted(names) if not name.startswith('stdlib/') or name in {'stdlib/catalogo.json','stdlib/catalogo.sh'} or any(lib['required'] and name=='stdlib/'+lib['name']+'.assis' for lib in catalog['libraries']))
    (source_dir/'install_files.inc').write_text(manifest,encoding='utf-8',newline='\n')
    setup=[str(cc),'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Wno-misleading-indentation',
        '-municode','-static','-static-libgcc','-s','-Wl,--no-insert-timestamp',str(source_dir/'windows_setup.c'),
        '-lshell32','-ladvapi32','-luser32','-o',str(STAGE/'bin/assis-setup.exe')]
    subprocess.run(setup,cwd=ROOT,env=environment,check=True)
    files=names|{'bin/assis-setup.exe','instalar-windows.cmd','desinstalar-windows.cmd','LEIA-PRIMEIRO.txt'}
    (STAGE/'instalar-windows.cmd').write_text('@echo off\n"%~dp0bin\\assis-setup.exe" install %*\nexit /b %errorlevel%\n',encoding='ascii')
    (STAGE/'desinstalar-windows.cmd').write_text('@echo off\n"%~dp0bin\\assis-setup.exe" uninstall %*\nexit /b %errorlevel%\n',encoding='ascii')
    (STAGE/'LEIA-PRIMEIRO.txt').write_text(
        'AssisScript - pacote de desenvolvimento Windows x64, 02/11/2026.\n'
        'Nao e release estavel nem promessa de suporte a outros sistemas.\n'
        'Compilador, bibliotecas e DLL sao preparados juntos; bin/ historico nao e atualizado.\n'
        'Veja BUILD-INFO.json para hashes e estado dos testes de instalacao.\n'
        'Para instalar: instalar-windows.cmd --no-associations\n'
        'Para teste sem instalar: bin\\assis.exe build exemplos\\57_page_frame_window.assis --safe -o bin\\paineis.exe\n'
        'Depois: bin\\paineis.exe --once (ou sem argumento para interagir).\n'
        'Preserve import "std/..."; -I nao atualiza um compilador antigo.\n',encoding='utf-8')
    info=dict(schema='assisscript-development-bundle-v1',release=False,base=native['base'],
        compiler_sha256=sha(STAGE/'bin/assis.exe'),provider_sha256=sha(STAGE/'bin/assis_platform_v1.dll'),
        setup_sha256=sha(STAGE/'bin/assis-setup.exe'),native_validation=dict(executed=sum(c['executed'] for c in native['checks']),not_run=sum(c['not_run'] for c in native['checks'])),
        installation_validation='not-run',
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','stdlib','providers/platform'] for p in sorted((ROOT/folder).iterdir()) if p.is_file()},
        files_sha256={name:sha(STAGE/name) for name in sorted(files-{'BUILD-INFO.json'})})
    def write_info():
        (STAGE/'BUILD-INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    write_info()
    if not args.prepare_only:
        with tempfile.TemporaryDirectory(prefix='assis-matched-install-') as temp:
            prefix=Path(temp)/'prefix with spaces';installed=prefix/'bin/assis.exe'
            def run(command):
                result=subprocess.run(list(map(str,command)),env=environment,cwd=ROOT,capture_output=True,timeout=120)
                if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
                return result
            run([STAGE/'bin/assis-setup.exe','install','--prefix',prefix,'--no-path','--no-associations','--with','pagepresent'])
            assert sha(installed)==info['compiler_sha256'] and sha(prefix/'bin/assis_platform_v1.dll')==info['provider_sha256']
            for lib in ['pagepresent','pageframe','flowpage','fluxstyle','htdl','reader','viewer','window','owned']:
                assert sha(prefix/'stdlib'/f'{lib}.assis')==sha(ROOT/'stdlib'/f'{lib}.assis')
            headless=run([installed,'run',prefix/'exemplos/56_page_frame.assis','--safe','--debug'])
            assert headless.stdout==b'FRAME 8 4 1 1\nLEFT 8 28 104 16\n'
            run([installed,'build',prefix/'exemplos/57_page_frame_window.assis','--safe','--debug','-o',prefix/'bin/panels.exe'])
            gui=run([prefix/'bin/panels.exe','--once']);assert gui.stdout==b'FRAME 1 10\n'
            personal=prefix/'personal.txt';personal.write_text('preserve')
            run([STAGE/'bin/assis-setup.exe','uninstall','--prefix',prefix,'--no-path','--no-associations'])
            assert personal.read_text()=='preserve' and not installed.exists() and not (prefix/'bin/assis_platform_v1.dll').exists()
        info['installation_validation']='pass';write_info()
    archive=ROOT/'build/AssisScript-development-20261102-windows-x64.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
        for name in sorted(files):output.write(STAGE/name,'AssisScript-development/'+name)
    print(archive);print('Installation validation:',info['installation_validation'])
    (EVIDENCE/'development-bundle.json').write_text(json.dumps(dict(compiler_sha256=info['compiler_sha256'],provider_sha256=info['provider_sha256'],setup_sha256=info['setup_sha256'],zip_sha256=sha(archive),installation_validation=info['installation_validation'],release=False),indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()

"""Install the fresh presentation libraries in an isolated prefix, run and remove."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--confined',action='store_true')
parser.add_argument('--search-forms',action='store_true')
parser.add_argument('--output',type=Path)
args=parser.parse_args()
OUT=args.output or ROOT/'docs/ecossistema/evidencias/m3-local-resources-2026-11-04'
selected=['frameworker','localresources','http','cli'] if args.confined else ['frameworker']
if args.search_forms:selected+=['searchindex','htdlsearch','cli','process']
selected=list(dict.fromkeys(selected))
selection=','.join(selected)
OUT.mkdir(parents=True,exist_ok=True);host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve();records=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='assis-presentation-install-') as temp:
    temp=Path(temp);stage=temp/'distribution';prefix=temp/'prefix with spaces'
    names={json.loads(line[1:-1]).replace('\\','/') for line in (ROOT/'src/install_files.inc').read_text().splitlines() if line.startswith('L')}
    catalog=json.loads((ROOT/'stdlib/catalogo.json').read_text(encoding='utf-8'));names.update('stdlib/'+x['name']+'.assis' for x in catalog['libraries'])
    names.update(['instalar.sh','desinstalar.sh'])
    for name in names:
        source=compiler if name=='bin/assis.exe' and os.name=='nt' else ROOT/name
        dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    environment=dict(os.environ,PYTHONUTF8='1')
    import importlib.util
    spec=importlib.util.spec_from_file_location('installed_worker_builder',ROOT/'tools/build-page-worker.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    runtime=stage/'bin' if os.name=='nt' else temp/'granted runtime'
    built=builder.build(runtime,compiler)
    runtime_hashes={Path(built[k]).name:sha(Path(built[k])) for k in ('worker','provider')}
    if os.name=='nt':
        cc='C:/msys64/ucrt64/bin/gcc.exe';environment['PATH']=str(Path(cc).parent)+os.pathsep+environment.get('PATH','')
        provider=stage/'bin/assis_platform_v1.dll'
        command=[sys.executable,str(ROOT/'tools/build-platform.py'),'--output',str(provider)]
        r=subprocess.run(command,env=environment,capture_output=True,timeout=90);assert r.returncode==0,r.stderr.decode(errors='replace')
        provider_hash=sha(provider)
        source_dir=temp/'installer-source';source_dir.mkdir()
        for name in ['windows_setup.c','install_optional.inc','version.h']:
            shutil.copyfile(ROOT/'src'/name,source_dir/name)
        manifest=(ROOT/'src/install_files.inc').read_text(encoding='utf-8')+'L"bin\\\\assis_platform_v1.dll",\nL"bin\\\\assis_worker_v1.dll",\nL"bin\\\\page-worker.exe",\n'
        (source_dir/'install_files.inc').write_text(manifest,encoding='utf-8',newline='\n')
        setup=stage/'bin/assis-setup.exe'
        command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Wno-misleading-indentation','-municode','-static','-static-libgcc','-s','-Wl,--no-insert-timestamp',str(source_dir/'windows_setup.c'),'-lshell32','-ladvapi32','-luser32','-o',str(setup)]
        r=subprocess.run(command,env=environment,capture_output=True,timeout=90);assert r.returncode==0,r.stderr.decode(errors='replace')
        setup_hash=sha(setup)
        command=[sys.executable,str(ROOT/'tests/test-installer-retry.py')]
        r=subprocess.run(command,cwd=ROOT,env=dict(environment,ASSIS_SETUP_BIN=str(setup)),capture_output=True,timeout=30)
        log=r.stdout+r.stderr;path=OUT/'windows-installer-retry.log';path.write_bytes(log)
        total=re.search(rb'Ran (\d+) tests? in',log);assert r.returncode==0,log.decode(errors='replace')
        records.append(dict(command=['python','tests/test-installer-retry.py'],returncode=r.returncode,
            executed=int(total[1]) if total else 0,log=path.name,sha256=hashlib.sha256(log).hexdigest()))
        install=[setup,'install','--prefix',prefix,'--no-path','--no-associations','--with',selection]
        uninstall=[setup,'uninstall','--prefix',prefix,'--no-path','--no-associations']
        data=prefix;installed=prefix/'bin/assis.exe'
        environment['PATH']=str(prefix/'bin')+os.pathsep+environment['PATH']
    else:
        target=stage/'bin/assis';shutil.copyfile(compiler,target);target.chmod(0o755);setup_hash=None;provider_hash=None
        install=['sh',stage/'instalar.sh','--prefix',prefix,'--no-path','--with',selection]
        uninstall=['sh',stage/'desinstalar.sh','--prefix',prefix];data=prefix/'share/assisscript';installed=prefix/'bin/assis'
    def run(command,input=None,cwd=ROOT):
        r=subprocess.run(list(map(str,command)),env=environment,cwd=cwd,input=input,capture_output=True,timeout=90)
        record=dict(command=[str(x).replace(str(temp),'<TEMP>') for x in command],returncode=r.returncode,
            stdout=r.stdout.decode(errors='replace').replace(str(temp),'<TEMP>'),
            stderr=r.stderr.decode(errors='replace').replace(str(temp),'<TEMP>'));records.append(record)
        assert r.returncode==0,record;return r
    run(install);assert sha(installed)==sha(compiler)
    if os.name=='nt':assert sha(prefix/'bin/assis_platform_v1.dll')==provider_hash
    chosen=set(selected);lookup={x['name']:x for x in catalog['libraries']};pending=list(selected)
    while pending:
        for dep in lookup[pending.pop()].get('dependencies',[]):
            if dep not in chosen:chosen.add(dep);pending.append(dep)
    for lib in catalog['libraries']:
        path=data/'stdlib'/f'{lib["name"]}.assis';expected=lib['required'] or lib['name'] in chosen
        assert path.exists()==expected,(lib['name'],expected)
        if expected:assert sha(path)==sha(ROOT/'stdlib'/f'{lib["name"]}.assis')
    if os.name=='nt':runtime=prefix/'bin'
    environment['PATH']=str(runtime)+os.pathsep+environment.get('PATH','')
    environment['LD_LIBRARY_PATH']=str(runtime)
    worker_path=runtime/('page-worker.exe' if os.name=='nt' else 'page-worker')
    binary=runtime/('installed-example.exe' if os.name=='nt' else 'installed-example')
    root=data/'exemplos/resource-demo'
    if args.confined:
        run([installed,'check',data/'exemplos/27_http_client.assis','--safe'])
        run([installed,'build',data/'exemplos/69_confined_resource_frame.assis','--safe','--debug','-o',binary])
        assert run([binary,installed,worker_path,root]).stdout==b'CONFINED FRAME 4 0 1\n'
    else:
        run([installed,'build',data/'exemplos/66_resource_frame.assis','--safe','--debug','-o',binary])
        paths=[root/name for name in ('index.htdl','main.fxs','main.sscr','main.assis')]
        assert run([binary,installed,worker_path,*paths]).stdout==b'RESOURCE FRAME 4 0 1\n'
    if args.search_forms:
        search=temp/('search-index.exe' if os.name=='nt' else 'search-index')
        sample=temp/'local index';sample.mkdir()
        run([installed,'build',data/'exemplos/71_search_index.assis','--safe','--debug','-o',search])
        run([search,'build'],input=b'1\tlocal index\n2\tindex index\n',cwd=sample)
        assert run([search,'query','phrase','local index'],cwd=sample).stdout.splitlines()==[b'1 1 0']
        if os.name=='nt':
            forms=prefix/'bin/forms.exe'
            run([installed,'build',data/'exemplos/72_local_forms_window.assis','--safe','--debug','-o',forms])
            assert run([forms,'--smoke']).stdout.splitlines()==[b'FORMS WINDOW 3 1']
    user=prefix/'personal.txt';user.write_text('preserve');run(uninstall);assert user.read_text()=='preserve' and not installed.exists()
    if os.name=='nt':
        command=['node','--test','--test-isolation=none','tests/test-development.js','tests/test-v31.js']
        if args.confined:command.append('tests/test-v32.js')
        r=subprocess.run(command,cwd=ROOT,env=dict(environment,ASSIS_BIN=str(compiler),ASSIS_SETUP_BIN=str(setup)),capture_output=True,timeout=240)
        log=r.stdout+r.stderr;(OUT/'windows-distribution-node.log').write_bytes(log)
        total=re.search(rb'(?:# )?tests (\d+)',log);assert r.returncode==0,log.decode(errors='replace')
        records.append(dict(command=command,returncode=r.returncode,executed=int(total[1]) if total else 0,
            log='windows-distribution-node.log',sha256=hashlib.sha256(log).hexdigest()))
report=dict(passed=True,compiler_sha256=sha(compiler),setup_sha256=setup_hash,provider_sha256=provider_hash,runtime_sha256=runtime_hashes,selected_libraries=sorted(chosen),search_forms=args.search_forms,checks=records,
    scope=f'Fresh candidate and isolated offline prefix, transitive closure of {selection}; installed resource Frame/worker demo, uninstall and user file preservation')
(OUT/f'{host}-install.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'{host} isolated resource Frame/worker install/run/uninstall: PASS')

"""Install the fresh presentation libraries in an isolated prefix, run and remove."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/ecossistema/evidencias/m5-frame-reader-2026-11-03'
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
    if os.name=='nt':
        cc='C:/msys64/ucrt64/bin/gcc.exe';environment['PATH']=str(Path(cc).parent)+os.pathsep+environment.get('PATH','')
        setup=stage/'bin/assis-setup.exe'
        command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Wno-misleading-indentation','-municode','-static','-static-libgcc','-s','-Wl,--no-insert-timestamp',str(ROOT/'src/windows_setup.c'),'-lshell32','-ladvapi32','-luser32','-o',str(setup)]
        r=subprocess.run(command,env=environment,capture_output=True,timeout=90);assert r.returncode==0,r.stderr.decode(errors='replace')
        setup_hash=sha(setup)
        command=[sys.executable,str(ROOT/'tests/test-installer-retry.py')]
        r=subprocess.run(command,cwd=ROOT,env=dict(environment,ASSIS_SETUP_BIN=str(setup)),capture_output=True,timeout=30)
        log=r.stdout+r.stderr;path=OUT/'windows-installer-retry.log';path.write_bytes(log)
        total=re.search(rb'Ran (\d+) tests? in',log);assert r.returncode==0,log.decode(errors='replace')
        records.append(dict(command=['python','tests/test-installer-retry.py'],returncode=r.returncode,
            executed=int(total[1]) if total else 0,log=path.name,sha256=hashlib.sha256(log).hexdigest()))
        install=[setup,'install','--prefix',prefix,'--no-path','--no-associations','--with','framehost']
        uninstall=[setup,'uninstall','--prefix',prefix,'--no-path','--no-associations']
        data=prefix;installed=prefix/'bin/assis.exe'
    else:
        target=stage/'bin/assis';shutil.copyfile(compiler,target);target.chmod(0o755);setup_hash=None
        install=['sh',stage/'instalar.sh','--prefix',prefix,'--no-path','--with','framehost']
        uninstall=['sh',stage/'desinstalar.sh','--prefix',prefix];data=prefix/'share/assisscript';installed=prefix/'bin/assis'
    def run(command,input=None):
        r=subprocess.run(list(map(str,command)),env=environment,cwd=ROOT,input=input,capture_output=True,timeout=90)
        record=dict(command=[str(x).replace(str(temp),'<TEMP>') for x in command],returncode=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'));records.append(record)
        assert r.returncode==0,record;return r
    run(install);assert sha(installed)==sha(compiler)
    chosen={'framehost'};lookup={x['name']:x for x in catalog['libraries']};pending=['framehost']
    while pending:
        for dep in lookup[pending.pop()].get('dependencies',[]):
            if dep not in chosen:chosen.add(dep);pending.append(dep)
    for lib in catalog['libraries']:
        path=data/'stdlib'/f'{lib["name"]}.assis';expected=lib['required'] or lib['name'] in chosen
        assert path.exists()==expected,(lib['name'],expected)
        if expected:assert sha(path)==sha(ROOT/'stdlib'/f'{lib["name"]}.assis')
    r=run([installed,'run',data/'exemplos/60_frame_reader.assis','--safe','--debug'])
    assert r.stdout==b'FRAME READER 1 7\n'
    user=prefix/'personal.txt';user.write_text('preserve');run(uninstall);assert user.read_text()=='preserve' and not installed.exists()
    if os.name=='nt':
        command=['node','--test','--test-isolation=none','tests/test-development.js','tests/test-v31.js']
        r=subprocess.run(command,cwd=ROOT,env=dict(environment,ASSIS_BIN=str(compiler),ASSIS_SETUP_BIN=str(setup)),capture_output=True,timeout=240)
        log=r.stdout+r.stderr;(OUT/'windows-distribution-node.log').write_bytes(log)
        total=re.search(rb'(?:# )?tests (\d+)',log);assert r.returncode==0,log.decode(errors='replace')
        records.append(dict(command=command,returncode=r.returncode,executed=int(total[1]) if total else 0,
            log='windows-distribution-node.log',sha256=hashlib.sha256(log).hexdigest()))
report=dict(passed=True,compiler_sha256=sha(compiler),setup_sha256=setup_hash,selected_libraries=sorted(chosen),checks=records,
    scope='Fresh candidate and isolated offline prefix, framehost/framereader transitive dependency closure; installed Frame reading demo, uninstall and user file preservation; no PATH, associations or release changes')
(OUT/f'{host}-install.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'{host} isolated presentation install/run/uninstall: PASS')

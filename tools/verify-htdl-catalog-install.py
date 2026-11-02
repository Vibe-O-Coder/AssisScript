"""Linux offline install of the fresh candidate and native HTDL checker."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02'
assert os.name!='nt','Run this native shell-installer check on Linux'
compiler=Path(os.environ['ASSIS_BIN']).resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
with tempfile.TemporaryDirectory(prefix='assis-htdl-install-') as temp:
    temp=Path(temp);stage=temp/'distribution';prefix=temp/'prefix with spaces'
    names={json.loads(line[1:-1]).replace('\\','/') for line in (ROOT/'src/install_files.inc').read_text().splitlines() if line.startswith('L')}
    names.update('stdlib/'+x['name']+'.assis' for x in json.loads((ROOT/'stdlib/catalogo.json').read_text())['libraries'])
    names.update(['instalar.sh','desinstalar.sh'])
    for name in names:
        destination=stage/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,destination)
    (stage/'bin').mkdir(exist_ok=True);shutil.copyfile(compiler,stage/'bin/assis');(stage/'bin/assis').chmod(0o755)
    def run(command,input=None):
        r=subprocess.run(list(map(str,command)),input=input,capture_output=True,timeout=90)
        records.append(dict(command=[str(x).replace(str(temp),'<TEMP>') for x in command],returncode=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode()))
        assert r.returncode==0,records[-1]
        return r
    run(['sh',stage/'instalar.sh','--prefix',prefix,'--no-path','--with','htdl'])
    data=prefix/'share/assisscript';installed=prefix/'bin/assis'
    assert sha(installed)==sha(compiler)
    for name in ['tools/htdl-check.assis','vscode-assisscript/src/htdl.js','stdlib/htdl.assis']:
        assert sha(data/name)==sha(ROOT/name),name
    binary=temp/'native-checker';run([installed,'build',data/'tools/htdl-check.assis','--safe','--debug','-o',binary])
    corpus=json.loads((ROOT/'tests/fixtures/htdl-catalog-corpus.json').read_text())
    assert run([binary],corpus['cases'][3]['source'].encode()).stdout==b'0 0\n'
    sentinel=data/'docs/user-note.txt';sentinel.write_text('preserve')
    run(['sh',stage/'desinstalar.sh','--prefix',prefix])
    assert sentinel.read_text()=='preserve' and not installed.exists()
    assert not (data/'tools/htdl-check.assis').exists() and not (data/'vscode-assisscript/src/htdl.js').exists()
report=dict(passed=True,compiler_sha256=sha(compiler),checks=records,
            scope='Fresh isolated Linux offline distribution, optional htdl dependency closure, installed native checker, managed-file removal and user-file preservation; no PATH or profile changes')
(OUT/'linux-installed-checker.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Linux installed HTDL checker/uninstall: PASS')

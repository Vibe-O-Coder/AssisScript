"""Build/extract an isolated VSIX and execute its own HTDL editor adapter."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02'
assert os.name=='nt','This packaged native checker is tested on Windows'
stage=ROOT/'build/catalog-distribution';assert stage.is_dir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(ROOT/'vscode-assisscript',stage/'vscode-assisscript',dirs_exist_ok=True)
shutil.copyfile(ROOT/'tools/package-vscode.py',stage/'tools/package-vscode.py')
shutil.copyfile(ROOT/'build/assis-linux',stage/'bin/assis')
assert sha(stage/'bin/assis.exe')==sha(ROOT/'build/assis.exe')
subprocess.run(['python',str(stage/'tools/package-vscode.py')],check=True,capture_output=True)
version=json.loads((ROOT/'stdlib/catalogo.json').read_text())['version'];archive=stage/'dist'/f'assisscript-{version}.vsix'
files=['tools/htdl-check.assis','vscode-assisscript/src/htdl.js','stdlib/htdl.assis',
       'vscode-assisscript/src/extension.js','vscode-assisscript/htdl-configuration.json','vscode-assisscript/syntaxes/htdl.tmLanguage.json']
entries={}
with tempfile.TemporaryDirectory(prefix='assis-htdl-vsix-') as folder:
    folder=Path(folder)
    with zipfile.ZipFile(archive) as package:
        assert len(package.namelist())==len(set(package.namelist()))
        for name in files:
            entry='extension/'+name.replace('vscode-assisscript/','');entries[entry]=hashlib.sha256(package.read(entry)).hexdigest()
            assert entries[entry]==sha(ROOT/name),name
        for name,candidate in [('assis.exe','assis.exe'),('assis','assis-linux')]:
            assert hashlib.sha256(package.read('extension/bin/'+name)).hexdigest()==sha(ROOT/'build'/candidate)
        package.extractall(folder)
    compiler=folder/'extension/bin/assis.exe';tool=folder/'extension/tools/htdl-check.assis';binary=folder/'checker.exe'
    built=subprocess.run([compiler,'build',tool,'--safe','--debug','-o',binary],capture_output=True);assert built.returncode==0,built.stderr
    source=json.loads((ROOT/'tests/fixtures/htdl-catalog-corpus.json').read_text())['cases'][3]['source'].encode()
    ran=subprocess.run([binary],input=source,capture_output=True);assert ran.returncode==0 and ran.stdout==b'0 0\n' and not ran.stderr
    script="const h=require(process.argv[1]);h.check(process.argv[2],require('node:fs').readFileSync(0,'utf8')).then(x=>console.log(JSON.stringify(x))).catch(e=>{console.error(e);process.exitCode=1});"
    adapted=subprocess.run(['node','-e',script,str(folder/'extension/src/htdl.js'),str(compiler)],input=source,capture_output=True,timeout=30)
    assert adapted.returncode==0 and adapted.stdout==b'[]\n' and not adapted.stderr,adapted.stderr
report=json.loads((OUT/'windows-node.json').read_text())
report['vsix']=dict(passed=True,archive_sha256=sha(archive),entries=entries,windows_compiler_sha256=sha(ROOT/'build/assis.exe'),
    linux_compiler_sha256=sha(ROOT/'build/assis-linux'),native_checker_stdout=ran.stdout.decode(),adapter_stdout=adapted.stdout.decode(),
    scope='Isolated VSIX with fresh Windows/Linux compilers; archive contents, extracted native HTDL checker and its own JS adapter executed on Windows. No publication or interactive VS Code acceptance.')
(OUT/'windows-node.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Isolated VSIX/native checker/editor adapter: PASS')

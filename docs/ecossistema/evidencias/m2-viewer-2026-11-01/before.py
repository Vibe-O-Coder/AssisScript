"""Reproduce missing viewer against the exact base standard library."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='ebd3185ae952a85c64cb2a83cd014ac07c0e8c7f'
compiler=Path(os.environ['ASSIS_BIN']).resolve()
folder=ROOT/'build/before';(folder/'bin').mkdir(parents=True,exist_ok=True)
archive=subprocess.run(['git','archive',BASE,'stdlib'],capture_output=True,check=True).stdout
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
binary=folder/'bin/assis.exe';shutil.copyfile(compiler,binary)
source=folder/'probe.assis';source.write_text('import "std/viewer.assis";safe fn main():int{return 0;}',encoding='utf-8')
result=subprocess.run([binary,'check',source,'--safe'],cwd=folder,capture_output=True,text=True,encoding='utf-8')
assert result.returncode==1 and 'viewer' in result.stderr,result.stderr
report=dict(base=BASE,standard_library='git archive of exact base',compiler_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    compiler='current build; compiler sources unchanged from base',command=['assis','check','probe.assis','--safe'],
    returncode=result.returncode,stderr=result.stderr.replace(str(ROOT),'<workspace>'),execution='not-run; frontend rejection')
(OUT/'before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Base standard library: viewer import rejected')

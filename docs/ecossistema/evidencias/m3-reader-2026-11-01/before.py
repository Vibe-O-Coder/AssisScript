"""Reproduce missing reader against the exact base standard library."""
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
BASE='4e7f6b84c2e933bc7b4196f06b4af80d09c289f6'
compiler=Path(os.environ['ASSIS_BIN']).resolve()
folder=ROOT/'build/before-reader';(folder/'bin').mkdir(parents=True,exist_ok=True)
archive=subprocess.run(['git','archive',BASE,'stdlib'],capture_output=True,check=True).stdout
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
binary=folder/'bin/assis.exe';shutil.copyfile(compiler,binary)
source=folder/'probe.assis';source.write_text('import "std/reader.assis";safe fn main():int{return 0;}',encoding='utf-8')
result=subprocess.run([binary,'check',source,'--safe'],cwd=folder,capture_output=True,text=True,encoding='utf-8')
assert result.returncode==1 and 'reader' in result.stderr,result.stderr
report=dict(base=BASE,standard_library='git archive of exact base',compiler_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    compiler='current build; compiler sources unchanged from base',command=['assis','check','probe.assis','--safe'],
    returncode=result.returncode,stderr=result.stderr.replace(str(ROOT),'<workspace>'),execution='not-run; frontend rejection')
(OUT/'before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Base standard library: reader import rejected')

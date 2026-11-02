"""Current compiler against the exact published base standard library."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
BASE='4ba27b3bd91bf7e033f41ba479b96255d4d90566'
folder=ROOT/'build/before-transactions';(folder/'bin').mkdir(parents=True,exist_ok=True)
archive=subprocess.run(['git','archive',BASE,'stdlib'],capture_output=True,check=True).stdout
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
binary=folder/'bin/assis.exe';shutil.copyfile(os.environ['ASSIS_BIN'],binary)
source=folder/'probe.assis';source.write_text('import "std/reader.assis";safe fn main():int{own s:reader::Session=try_new reader::Session(32000000,250000,7);return 0;}',encoding='utf-8')
result=subprocess.run([binary,'check',source,'--safe'],cwd=folder,capture_output=True,text=True,encoding='utf-8')
assert result.returncode==1 and 'Session' in result.stderr,result.stderr
report=dict(base=BASE,standard_library='git archive of exact published base',
    compiler_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    command=['assis','check','probe.assis','--safe'],returncode=result.returncode,
    stderr=result.stderr.replace(str(ROOT),'<workspace>'),execution='not-run: frontend rejection')
(OUT/'before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Published base: reader::Session rejected by current compiler')

"""Current compiler against the exact published base libraries, no execution."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
BASE='a542aff0f6ace008e6558c1cb1553c9ea05cc2eb'
folder=ROOT/'build/before-unicode-vm';(folder/'bin').mkdir(parents=True,exist_ok=True)
archive=subprocess.run(['git','archive',BASE,'stdlib'],capture_output=True,check=True).stdout
tarfile.open(fileobj=io.BytesIO(archive)).extractall(folder,filter='data')
binary=folder/'bin/assis.exe';shutil.copyfile(os.environ['ASSIS_BIN'],binary)
records=[]
for name in ('graphemes','pagevm'):
    source=folder/(name+'.assis');source.write_text(f'import "std/{name}.assis";safe fn main():int{{return 0;}}',encoding='utf-8')
    result=subprocess.run([binary,'check',source,'--safe'],cwd=folder,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==1 and name in result.stderr,result.stderr
    records.append(dict(module=name,returncode=result.returncode,stderr=result.stderr.replace(str(ROOT),'<workspace>')))
report=dict(base=BASE,standard_library='git archive exact published base',
    compiler_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),checks=records,
    execution='not-run: frontend import rejection')
(OUT/'before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Published base rejects both new modules')

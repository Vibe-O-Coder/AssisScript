"""Rebuild the published provider and reproduce its restriction negotiation."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent.parent
BASE='f12a1f2a9a7edf97e829d5f7c6e2f29980961414'
OUT=ROOT/'docs/ecossistema/evidencias/m0-windows-isolation-2026-11-02'
stage=ROOT/'build/isolation-before';stage.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
assert os.name=='nt'
for name in ['providers/worker/worker.c','providers/worker/assis_worker_v1.h','src/page_restrict.h']:
    p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
cc=shutil.which('gcc') or 'C:/msys64/ucrt64/bin/gcc.exe';library=stage/'before.dll'
command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-static-libgcc','-Wl,--no-insert-timestamp',str(stage/'providers/worker/worker.c'),'-o',str(library)]
subprocess.run(command,cwd=ROOT,check=True,env=dict(os.environ,PATH=str(Path(cc).parent)+os.pathsep+os.environ.get('PATH','')))
lib=ctypes.CDLL(str(library));lib.assw_open.restype=ctypes.c_int64
lib.assw_open.argtypes=[ctypes.c_void_p,ctypes.c_int64,ctypes.c_int64,ctypes.POINTER(ctypes.c_int64)]
path=str(Path(os.environ['ASSIS_BIN']).resolve()).encode();token=ctypes.c_int64(99)
result=lib.assw_open(path,len(path),1,ctypes.byref(token));assert (result,token.value)==(-3,0)
report=dict(base=BASE,returncode=result,token=token.value,provider_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),commands=[command],
    reproduction='Published Windows provider rejects restricted=1 before spawning, even with a valid trusted executable')
(OUT/'before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Published baseline reproduced: -3, token 0')

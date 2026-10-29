"""A real GDB remote session against ARM64 code executed by QEMU on x64."""
from pathlib import Path
import json
import os
import socket
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parent.parent
compiler=Path(os.environ.get('ASSIS_BIN',ROOT/'bin/assis'))
record={'execution':'qemu-aarch64 + gdb-multiarch remote','passed':False,'cases':[]}
with tempfile.TemporaryDirectory(prefix='assis-arm-gdb-') as tmp:
    folder=Path(tmp)
    source=folder/'probe.assis';source.write_text('safe fn calc(n:int):int{\nlet x:int=n+2;\nprint(x);\n{let x:int=99;\nn=x;\n}\nreturn x;\n}\nsafe fn main():int{print(calc(40));return 0;}\n')
    for optimize in (True,False):
        binary=folder/'probe'
        subprocess.run([compiler,'build',source,'--target','linux-arm64','--symbols','-o',binary,*([] if optimize else ['--no-opt'])],check=True,capture_output=True)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        child=subprocess.Popen(['qemu-aarch64','-g',str(port),binary],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            time.sleep(.2)
            cmd=['gdb-multiarch','-nx','-nh','-batch','-ex',f'target remote :{port}','-ex',f'break {source}:3','-ex','continue','-ex','print n','-ex','print x','-ex','bt','-ex',f'break {source}:5','-ex','continue','-ex','print x','-ex','quit',binary]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            assert result.returncode==0 and all(v in result.stdout for v in ('= 40','= 42','= 99','main')),result.stdout+result.stderr
            record['cases'].append({'optimized':optimize,'passed':True,'gdb':result.stdout})
        finally:
            if child.poll() is None:child.terminate()
            child.communicate(timeout=10)
record['passed']=True
out=ROOT/'build/arm64-gdb.json';out.write_text(json.dumps(record,indent=2)+'\n');print(out)

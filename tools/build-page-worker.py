"""Build the optional trusted worker and scalar process provider on this host."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent.parent

def build(output,compiler=None,cc=None):
    if platform.machine().lower() not in ('x86_64','amd64') or platform.system() not in ('Windows','Linux'):
        raise RuntimeError('Worker provider supports Windows/Linux x64 only')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    windows=os.name=='nt'
    cc=cc or os.environ.get('CC') or shutil.which('gcc') or 'C:/msys64/ucrt64/bin/gcc.exe'
    compiler=Path(compiler or os.environ.get('ASSIS_BIN',ROOT/'bin'/('assis.exe' if windows else 'assis'))).resolve()
    env=dict(os.environ,PATH=str(Path(cc).parent)+os.pathsep+os.environ.get('PATH',''))
    provider=output/('assis_worker_v1.dll' if windows else 'libassis_worker_v1.so')
    command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared']
    command+=['-static-libgcc','-Wl,--no-insert-timestamp'] if windows else ['-fPIC','-pthread']
    command += [str(ROOT/'providers/worker/worker.c'),'-o',str(provider)]
    subprocess.run(command,env=env,check=True)
    worker=output/('page-worker.exe' if windows else 'page-worker')
    flags=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
    subprocess.run([str(compiler),'build',str(ROOT/'tools/page-worker.assis'),'-o',str(worker),*flags],cwd=ROOT,env=env,check=True)
    return dict(provider=str(provider),worker=str(worker),cc=cc,commands=[command])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'build/worker');parser.add_argument('--compiler');parser.add_argument('--cc');args=parser.parse_args()
    print(json.dumps(build(args.output,args.compiler,args.cc),indent=2))

"""Run isolated native HTTP clients and persistent services for real wall time.

The default duration is 24 hours. Short runs are recorded explicitly and never
qualify as the roadmap's 24-hour gate. Only a loopback server is contacted.
"""
import argparse
import concurrent.futures
import ctypes
import hashlib
import http.server
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--duration',type=float,default=86400)
parser.add_argument('--workers',type=int,default=4)
parser.add_argument('--polling',action='store_true',help='Exercise cooperative net client and cancellation (optional libcurl on Windows)')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--status-output',type=Path,help='Optional checkpoint path; default is beside the final report')
parser.add_argument('--interval',type=float,default=0.0,help='Minimum seconds between rounds per worker; 1.0 is recommended for shared desktop endurance runs')
parser.add_argument('--stop-file',type=Path,help='End gracefully if this file appears; interrupted runs never qualify as 24 hours')
args=parser.parse_args()
assert 1<=args.duration<=172800 and 1<=args.workers<=8
assert 0<=args.interval<=60
compiler=ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis')
compiler_hash=hashlib.sha256(compiler.read_bytes()).hexdigest()
def frozen_hashes():
    paths=[p for directory in ['src','stdlib','exemplos'] for p in sorted((ROOT/directory).glob('*')) if p.is_file()]
    paths.append(Path(__file__).resolve())
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
source_hashes=frozen_hashes()
if args.polling and os.name=='nt':os.environ['PATH']=os.environ.get('ASSIS_CURL_BIN',r'C:\Program Files\Git\mingw64\bin')+os.pathsep+os.environ.get('PATH','')
children=[];children_lock=threading.Lock();stop=threading.Event()
progress={};progress_lock=threading.Lock()
args.output.parent.mkdir(parents=True,exist_ok=True)
status_path=args.status_output or args.output.with_name(args.output.stem+'.status.json')
status_path.parent.mkdir(parents=True,exist_ok=True)

def status(stage,started,**extra):
    with progress_lock:snapshot={str(k):dict(v) for k,v in progress.items()}
    record=dict(stage=stage,pid=os.getpid(),requestedSeconds=args.duration,elapsedSeconds=time.monotonic()-started,
        compilerSha256=compiler_hash,workers=snapshot,intervalSeconds=args.interval,qualifies24Hours=False)
    record.update(extra)
    temporary=status_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    temporary.replace(status_path)

def resources(child):
    if os.name!='nt':
        try:
            rss=next(line for line in Path(f'/proc/{child.pid}/status').read_text().splitlines() if line.startswith('VmRSS:'))
            return dict(rssBytes=int(rss.split()[1])*1024,handles=len(list(Path(f'/proc/{child.pid}/fd').iterdir())))
        except (OSError,StopIteration):return dict(rssBytes=None,handles=None)
    from ctypes import wintypes
    class Memory(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['peak','working','peakPaged','paged','peakNonPaged','nonPaged','pagefile','peakPagefile']]
    counters=Memory();counters.cb=ctypes.sizeof(counters);count=wintypes.DWORD()
    query=ctypes.WinDLL('psapi').GetProcessMemoryInfo;query.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
    handles=ctypes.WinDLL('kernel32').GetProcessHandleCount;handles.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    ok=query(int(child._handle),ctypes.byref(counters),counters.cb);known=handles(int(child._handle),ctypes.byref(count))
    return dict(rssBytes=counters.working if ok else None,handles=count.value if known else None)

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        payload=b'AssisScript\x00'+bytes(range(256))*16
        self.send_response(404 if self.path=='/missing' else 200);self.send_header('Content-Length',str(len(payload)));self.end_headers()
        self.wfile.write(payload)

with tempfile.TemporaryDirectory(prefix='assis-soak-') as temporary:
    folder=Path(temporary);binaries=[]
    for source in ['29_http_polling.assis' if args.polling else '27_http_client.assis','28_persistent_service.assis']:
        binary=folder/(source+'.exe');subprocess.run([compiler,'build',ROOT/'exemplos'/source,'--safe','--debug','-o',binary],check=True,capture_output=True,timeout=30);binaries.append(binary)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    threading.Thread(target=server.serve_forever,daemon=True).start()
    started=time.monotonic();deadline=started+args.duration

    def worker(index):
        state=folder/f'state-{index}';service=subprocess.Popen([binaries[1],state,folder/f'next-{index}',folder/f'lock-{index}'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        with children_lock:children.append(service)
        rounds=0;first=None;final=None;peak_rss=None;peak_handles=None
        try:
            while time.monotonic()<deadline and not stop.is_set() and not (args.stop_file and args.stop_file.exists()):
                round_started=time.monotonic()
                service.stdin.write(b'inc\nget\n');service.stdin.flush();rounds+=1
                assert service.stdout.readline()==f'{rounds}\n'.encode();assert service.stdout.readline()==f'{rounds}\n'.encode()
                sample=resources(service);first=first or sample;final=sample
                if sample['rssBytes'] is not None:peak_rss=max(peak_rss or 0,sample['rssBytes'])
                if sample['handles'] is not None:peak_handles=max(peak_handles or 0,sample['handles'])
                with progress_lock:progress[index]=dict(rounds=rounds,rssBytes=sample['rssBytes'],handles=sample['handles'],peakRssBytes=peak_rss,peakHandles=peak_handles)
                if sample['rssBytes'] is not None:assert sample['rssBytes']<134217728,sample
                if sample['handles'] is not None and first['handles'] is not None:assert sample['handles']<=first['handles']+32,sample
                output=folder/f'output-{index}'
                r=subprocess.run([binaries[0],f'http://127.0.0.1:{server.server_address[1]}/ok',output],capture_output=True,timeout=15)
                assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr)
                assert output.read_bytes()==b'AssisScript\x00'+bytes(range(256))*16
                if rounds%17==0:
                    service.stdin.write(b'bad\n');service.stdin.flush();assert service.stdout.readline()==b'ERR command\n'
                if rounds%31==0:
                    r=subprocess.run([binaries[0],f'http://127.0.0.1:{server.server_address[1]}/missing',output],capture_output=True,timeout=15);assert r.returncode==2
                    assert output.read_bytes()==b'AssisScript\x00'+bytes(range(256))*16
                if args.polling and rounds%29==0:
                    r=subprocess.run([binaries[0],f'http://127.0.0.1:{server.server_address[1]}/ok',output,'0'],capture_output=True,timeout=15)
                    assert r.returncode==1 and r.stdout==b'Transport error -7 0\n' and not r.stderr
                    assert output.read_bytes()==b'AssisScript\x00'+bytes(range(256))*16
                delay=min(args.interval-(time.monotonic()-round_started),deadline-time.monotonic())
                if delay>0:stop.wait(delay)
            service.stdin.write(b'quit\n');service.stdin.flush();out,err=service.communicate(timeout=10)
            assert service.returncode==0 and not out and not err,(service.returncode,out,err)
            restored=subprocess.run([binaries[1],state,folder/f'next-{index}',folder/f'lock-{index}'],input=b'get\nquit\n',capture_output=True,timeout=10)
            assert (restored.returncode,restored.stdout,restored.stderr)==(0,f'{rounds}\n'.encode(),b'')
            return dict(worker=index,rounds=rounds,initial=first,final=final,peakRssBytes=peak_rss,peakHandles=peak_handles)
        finally:
            if service.poll() is None:service.kill();service.communicate(timeout=10)

    failure=None;records=[]
    def checkpoint():
        while not stop.wait(30):status('running',started)
    status('running',started)
    checkpoint_thread=threading.Thread(target=checkpoint,daemon=True);checkpoint_thread.start()
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)
    try:
        futures=[pool.submit(worker,i) for i in range(args.workers)]
        for future in concurrent.futures.as_completed(futures,timeout=args.duration+45):records.append(future.result())
    except BaseException as error:
        failure=repr(error);stop.set()
        with children_lock:
            for child in children:
                if child.poll() is None:child.kill()
    finally:pool.shutdown(wait=True,cancel_futures=True);server.shutdown();server.server_close();stop.set();checkpoint_thread.join(timeout=2)
    elapsed=time.monotonic()-started
    interrupted=bool(args.stop_file and args.stop_file.exists())
    if interrupted:failure=failure or 'Interrupted by stop file; elapsed time does not qualify'
    if hashlib.sha256(compiler.read_bytes()).hexdigest()!=compiler_hash:failure=failure or 'Compiler changed during measurement'
    final_hashes=frozen_hashes()
    if final_hashes!=source_hashes:failure=failure or 'Sources changed during measurement'
    report=dict(platform=platform.platform(),compilerSha256=compiler_hash,applicationSha256={binary.name:hashlib.sha256(binary.read_bytes()).hexdigest() for binary in binaries},sourceHashes=source_hashes,requestedSeconds=args.duration,elapsedSeconds=elapsed,workers=args.workers,passed=failure is None,error=failure,qualifies24Hours=failure is None and args.duration>=86400 and elapsed>=86400,results=sorted(records,key=lambda r:r['worker']))
    report['networkMode']='polling' if args.polling else 'blocking';report['sourceHashes']=source_hashes;report['intervalSeconds']=args.interval
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    status('interrupted' if interrupted else 'passed' if failure is None else 'failed',started,report=args.output.name,error=failure,qualifies24Hours=report['qualifies24Hours'])
    print(json.dumps({key:value for key,value in report.items() if key!='results'},indent=2))
    if failure:raise SystemExit(1)

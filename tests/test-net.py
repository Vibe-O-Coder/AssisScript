"""Cooperative HTTP, cancellation, bounded bodies and isolated TLS trust."""
import http.server
import importlib.util
import os
from pathlib import Path
import ssl
import subprocess
import threading
import time
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/stream':
            self.send_response(200);self.send_header('Content-Length','4096');self.end_headers()
            try:
                for i in range(32):self.wfile.write(b'x'*128);self.wfile.flush();time.sleep(.01)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
            return
        if self.path=='/slow':time.sleep(.5)
        if self.path=='/disconnect':self.connection.close();return
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','file:///etc/passwd');self.send_header('Content-Length','0');self.end_headers();return
        body=b'hello\x00\xc3\xa7' if self.path!='/large' else b'x'*65536
        self.send_response(404 if self.path=='/missing' else 200)
        self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,ssl.SSLError):pass

def buffer(name,text):
    data=os.fsencode(text)
    return f'own {name}:*byte=alloc<byte>({len(data)+1});'+''.join(f'{name}[{i}]=byte({b});' for i,b in enumerate(data))

class Net(base.Evolution):
    def invoke(self,*args,input=None):
        return super().invoke(*args,'--safe',input=input)

    def setUp(self):
        super().setUp()
        # A declared optional native dependency, never copied into the release.
        if os.name=='nt':
            previous=os.environ['PATH'];curl=os.environ.get('ASSIS_CURL_BIN',r'C:\Program Files\Git\mingw64\bin')
            os.environ['PATH']=curl+os.pathsep+previous;self.addCleanup(os.environ.__setitem__,'PATH',previous)
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown);self.port=self.server.server_address[1]

    def source_url(self,path,body,timeout=3000,limit=64,host='127.0.0.1',secure=False,trust=False):
        prefix='import "std/net.assis";\nimport "std/events.assis";\n'
        prefix+='safe fn tick(borrow mut loop:events::Loop,state:int):void{print(state);}\n'
        src=prefix+'safe fn main():int{'+buffer('url',f'{"https" if secure else "http"}://{host}:{self.port}{path}')
        if trust:
            src+=buffer('ca',str(Path(__file__).parent/'fixtures/tls/test-cert.pem'))
            src+=f'own request:net::Request=net::start_trusted(url,ca,{timeout},{limit});'
        else:src+=f'own request:net::Request=net::start(url,{timeout},{limit});'
        return src+body+'return 0;}'

    def test_completion_bounds_errors_and_request_retains_inputs(self):
        self.accepted(self.source_url('/ok','url[7]=byte(88);while(request.poll(10)==0){}print(request.error(),request.status_code(),request.size());{borrow b:slice<byte>=request.body();print(b[5],b[6],b[7]);}assert(!request.cancel());assert(request.poll(0)==1);',limit=8),'0 200 8\n0 195 167\n')
        for path,expected,limit in [('/large','-2 200\n',17),('/missing','0 404\n',64),('/redirect','0 302\n',64),('/disconnect','-4 0\n',64)]:
            self.accepted(self.source_url(path,'while(request.poll(10)==0){}print(request.error(),request.status_code());',limit=limit),expected)

    def test_cancel_before_start_during_io_and_repeated_cancel(self):
        self.accepted(self.source_url('/slow','assert(!request.done());assert(request.error()==1);assert(request.cancel());assert(!request.cancel());assert(request.poll(50)==1);print(request.error(),request.size());'),'-7 0\n')
        body='own loop:events::Loop=events::create(4);assert(events::schedule(loop,0,42,tick)>0);val begun:int=monotonic_ms();let ticks:int=0;while(monotonic_ms()-begun<50){assert(request.poll(0)==0);ticks+=events::run(loop,1);assert(sleep_ms(1)==0);}assert(ticks==1);assert(request.cancel());assert(monotonic_ms()-begun<400);print(request.error());'
        self.accepted(self.source_url('/slow',body),'42\n-7\n')

    def test_timeout_parallel_requests_and_drop_while_pending(self):
        self.accepted(self.source_url('/slow','while(request.poll(10)==0){}print(request.error());',timeout=40),'-3\n')
        prefix='import "std/net.assis";\nsafe fn main():int{'+buffer('url',f'http://127.0.0.1:{self.port}/slow')
        body='own a:net::Request=net::start(url,3000,64);own b:net::Request=net::start(url,3000,64);assert(a.poll(-1)==-1);assert(a.poll(51)==-1);while(!a.done()||!b.done()){let x:int=a.poll(0);let y:int=b.poll(10);}print(a.error(),b.error());{own dropped:net::Request=net::start(url,3000,64);assert(dropped.poll(0)==0);}return 0;}'
        self.accepted(prefix+body,'0 0\n')

    def test_partial_body_stops_changing_after_cancel(self):
        self.accepted(self.source_url('/stream','while(request.size()==0){assert(request.poll(10)==0);}assert(request.cancel());val size:int=request.size();assert(size>0&&size<4096);assert(sleep_ms(50)==0);assert(request.poll(0)==1&&request.size()==size);print(request.error());',limit=8192),'-7\n')

    def test_native_handles_and_buffers_are_released_in_one_live_process(self):
        body='own gate:*byte=alloc<byte>(1);{own warm:net::Request=net::start(url,3000,64);while(warm.poll(10)==0){}}print("READY");assert(read_bytes(gate,1)==1);for(let i:int=0;i<64;i+=1){own next:net::Request=net::start(url,3000,64);if(i%3==0){let cancelled:bool=next.cancel();}else if(i%3==1){while(next.poll(10)==0){}assert(next.error()==0&&next.size()==8);}else{let progress:int=next.poll(0);}}print("DONE");assert(read_bytes(gate,1)==1);'
        source=self.source(self.source_url('/ok',body));binary=self.temp/'lifecycle.exe'
        r=self.invoke('build',source,'--debug','-o',binary);self.assertEqual(r.returncode,0,r.stderr)
        child=subprocess.Popen([binary],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def handles():
            if os.name!='nt':return len(list(Path(f'/proc/{child.pid}/fd').iterdir()))
            import ctypes
            from ctypes import wintypes
            count=wintypes.DWORD();query=ctypes.WinDLL('kernel32').GetProcessHandleCount;query.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
            self.assertTrue(query(int(child._handle),ctypes.byref(count)));return count.value
        try:
            self.assertEqual(child.stdout.readline(),b'READY\n');before=handles();child.stdin.write(b'x');child.stdin.flush()
            self.assertEqual(child.stdout.readline(),b'DONE\n');self.assertLessEqual(handles(),before+8)
            out,err=child.communicate(b'x',timeout=10);self.assertEqual((child.returncode,out,err),(0,b'',b''))
        finally:
            if child.poll() is None:child.kill();child.communicate(timeout=10)

    def test_application_b_polls_and_preserves_output_on_cancel(self):
        binary=self.temp/'application.exe';r=self.invoke('build',base.ROOT/'exemplos/29_http_polling.assis','--debug','-o',binary);self.assertEqual(r.returncode,0,r.stderr)
        output=self.temp/'output.bin';output.write_bytes(b'preserve')
        r=subprocess.run([binary,f'http://127.0.0.1:{self.port}/slow',output,'20'],capture_output=True,timeout=10)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(1,b'Transport error -7 0\n',b''));self.assertEqual(output.read_bytes(),b'preserve')
        r=subprocess.run([binary,f'http://127.0.0.1:{self.port}/ok',output],capture_output=True,timeout=10)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'Downloaded 8 bytes\n',b''));self.assertEqual(output.read_bytes(),b'hello\x00\xc3\xa7')

    def test_tls_positive_untrusted_and_hostname_verification(self):
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);fixtures=Path(__file__).parent/'fixtures/tls'
        context.load_cert_chain(fixtures/'test-cert.pem',fixtures/'test-key.pem')
        self.server.socket=context.wrap_socket(self.server.socket,server_side=True)
        self.accepted(self.source_url('/ok','while(request.poll(10)==0){}print(request.error());',host='localhost',secure=True),'-5\n')
        self.accepted(self.source_url('/ok','while(request.poll(10)==0){}print(request.error(),request.status_code());',host='localhost',secure=True,trust=True),'0 200\n')
        # Fixture has only DNS localhost; numeric host must still fail.
        self.accepted(self.source_url('/ok','while(request.poll(10)==0){}print(request.error());',secure=True,trust=True),'-5\n')

    def test_invalid_input_is_recoverable(self):
        prefix='import "std/net.assis";\nsafe fn main():int{'
        for url in ['file:///etc/passwd','httpsx://host/','http://user:pass@localhost/','http:///bad','http://host\r\nX:yes/']:
            self.accepted(prefix+buffer('url',url)+'own r:net::Request=net::start(url,1000,1);print(r.done(),r.error(),r.size());return 0;}','true -1 0\n')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

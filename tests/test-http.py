"""Loopback HTTP fault injection; no public service dependency."""
import concurrent.futures
import http.server
import importlib.util
import os
from pathlib import Path
import socket
import ssl
import threading
import time
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path=='/slow': time.sleep(.4)
        if self.path=='/disconnect':self.connection.close();return
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','file:///etc/passwd');self.send_header('Content-Length','0');self.end_headers();return
        body=b'hello\x00\xc3\xa7' if self.path!='/large' else b'x'*65536
        self.send_response(404 if self.path=='/missing' else 200)
        self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass

class HTTP(base.Evolution):
    def setUp(self):
        super().setUp();self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.daemon_threads=True;self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.port=self.server.server_address[1]

    def source_url(self,url,body,timeout=5000,limit=64):
        data=url.encode();assign=''.join(f'url[{i}]=byte({c});' for i,c in enumerate(data))
        return 'import "std/http.assis";\nsafe fn main():int{own url:*byte=alloc<byte>('+str(len(data)+1)+');'+assign+f'own response:http::Response=http::get(url,{timeout},{limit});'+body+'return 0;}'

    def test_success_binary_status_and_exact_limit(self):
        src=self.source_url(f'http://localhost:{self.port}/ok','print(response.error(),response.status_code(),response.size());borrow body:slice<byte>=response.body();print(body[5],body[6],body[7]);',limit=8)
        self.accepted(src,'0 200 8\n0 195 167\n')
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/missing','print(response.error(),response.status_code());'),'0 404\n')

    def test_bounds_redirects_and_invalid_urls(self):
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/large','print(response.error());',limit=17),'-2\n')
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/redirect','print(response.error(),response.status_code(),response.size());'),'0 302 0\n')
        for url in ['file:///etc/passwd','http://user:pass@localhost/','httpsx://host/','http://host/\r\nInjected:yes']:
            with self.subTest(url=url):self.accepted(self.source_url(url,'print(response.error());'),'-1\n')

    def test_timeouts_disconnect_and_recovery(self):
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/slow','print(response.error());',timeout=50),'-3\n')
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/disconnect','print(response.error());'),'-4\n')
        self.accepted(self.source_url(f'http://127.0.0.1:{self.port}/ok','print(response.error());'),'0\n')

    def test_independent_process_load_and_released_handles(self):
        source=self.source(self.source_url(f'http://127.0.0.1:{self.port}/ok','print(response.error(),response.size());'))
        binary=self.temp/'client.exe';r=self.invoke('build',source,'--safe','--debug','-o',binary);self.assertEqual(r.returncode,0,r.stderr)
        import subprocess
        def client(_):
            r=subprocess.run([binary],capture_output=True,text=True,timeout=10);return r.returncode,r.stdout,r.stderr
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(client,range(24)))
        self.assertEqual(results,[(0,'0 8\n','')]*24)
        # Keep one native process alive across many requests. Process exit must
        # not hide leaked network handles or allocations.
        body='own gate:*byte=alloc<byte>(1);own client:http::Client=new http::Client();{own warm:http::Response=client.get(url,5000,64);assert(warm.error()==0);}print("READY");assert(read_bytes(gate,1)==1);for(let i:int=0;i<128;i+=1){own next:http::Response=client.get(url,5000,64);assert(next.error()==0&&next.size()==8);}print("DONE");assert(read_bytes(gate,1)==1);'
        source=self.source(self.source_url(f'http://127.0.0.1:{self.port}/ok',body));r=self.invoke('build',source,'--safe','--debug','-o',binary);self.assertEqual(r.returncode,0,r.stderr)
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

    def test_untrusted_tls_certificate_is_rejected(self):
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);fixtures=Path(__file__).parent/'fixtures/tls'
        context.load_cert_chain(fixtures/'test-cert.pem',fixtures/'test-key.pem')
        self.server.socket=context.wrap_socket(self.server.socket,server_side=True)
        self.accepted(self.source_url(f'https://localhost:{self.port}/ok','print(response.error());'),'-5\n')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

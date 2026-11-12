"""Loopback HTTP fault injection; no public service dependency."""
import concurrent.futures
import http.server
import importlib.util
import json
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
    def reply(self,status,body=b'',headers=()):
        self.send_response(status)
        for name,value in headers:self.send_header(name,value)
        self.send_header('Content-Length',str(len(body)));self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length','0')))
        self.server.requests.append((self.command,self.path,self.headers.get('X-Test'),body))
        if self.path=='/post-redirect':
            self.reply(307,headers=(('Location','/post-target'),))
        else:
            self.reply(201,body,(('X-Reply','received'),))
    def do_GET(self):
        self.server.requests.append((self.command,self.path,self.headers.get('X-Test'),b''))
        redirects={'/nested/hop':'../echo?first=1',
                   '/cross':f'http://localhost:{self.server.server_address[1]}/cross-target',
                   '/loop':'/loop','/malformed':'/bad%zz'}
        if self.path in redirects:
            self.reply(302,headers=(('Location',redirects[self.path]),));return
        if self.path=='/duplicate':
            self.reply(302,headers=(('Location','/one'),('Location','/two')));return
        if self.path=='/large-headers':
            self.reply(200,headers=(('X-Large','a'*40000),));return
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
        self.server.requests=[]
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
        binary=self.temp/'resident-client.exe'
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
        timeout=int(os.environ.get('ASSIS_TLS_TEST_TIMEOUT_MS','5000'))
        self.assertTrue(5000<=timeout<=60000)
        self.accepted(self.source_url(f'https://localhost:{self.port}/ok','print(response.error());',timeout=timeout),'-5\n')

    def with_client(self,paths,body):
        code='import "std/http.assis";\nsafe fn main():int{'
        code+='own client:http::Client=new http::Client();own fields:http::Headers=new http::Headers();'
        for name,path in paths.items():
            address=f'http://127.0.0.1:{self.port}{path}'.encode()
            code+=f'own {name}:*byte=alloc<byte>({len(address)+1});'
            code+=''.join(f'{name}[{i}]=byte({c});' for i,c in enumerate(address))
        return code+body+'return 0;}'

    def test_post_binary_empty_body_headers_and_no_method_leak_into_get(self):
        source=self.with_client({'url':'/post','redirect':'/post-redirect'},'''
            assert(fields.add(utf8("X-Test"),utf8("fiel")));
            assert(fields.add(utf8("Content-Type"),utf8("application/octet-stream")));
            assert(!fields.add(utf8("x-test"),utf8("duplicate")));
            assert(!fields.add(utf8("Bad:Name"),utf8("x")));
            assert(!fields.add(utf8("X-Bad"),utf8("ok\r\nHost: evil")));
            assert(!fields.add(utf8("Host"),utf8("evil")));
            assert(!fields.add(utf8("Content-Length"),utf8("7")));
            assert(!fields.add(utf8("Transfer-Encoding"),utf8("chunked")));
            assert(!fields.add(utf8("Authorization"),utf8("Basic xxx")));
            own payload:*byte=alloc<byte>(4);
            payload[0]=byte(65);payload[2]=byte(255);payload[3]=byte(66);
            {
                own res:http::Response=client.post(url,slice_of(payload,0,4),fields,5000,4);
                assert(res.error()==0 && res.status_code()==201 && res.size()==4);
                assert(res.body()[1]==0 && res.body()[2]==255);
                assert(len(res.header(utf8("x-RePlY")))==8 && res.header(utf8("x-reply"))[0]==114);
            }
            {
                own res:http::Response=http::post(url,utf8(""),fields,5000,0);
                assert(res.error()==0 && res.status_code()==201 && res.size()==0);
            }
            {
                own res:http::Response=client.post(redirect,utf8("z"),fields,5000,0);
                assert(res.error()==0 && res.status_code()==307 && len(res.header(utf8("location")))>0);
            }
            {
                own res:http::Response=client.get(url,5000,8);
                assert(res.error()==0 && res.status_code()==200 && len(res.raw_headers())==0);
            }
        ''')
        # Keep CR/LF as literal escapes in the generated AssisScript source.
        self.accepted(source.replace('ok\r\nHost',r'ok\r\nHost'))
        expected=[('POST','/post','fiel',b'A\x00\xffB'),
                  ('POST','/post','fiel',b''),('POST','/post-redirect','fiel',b'z'),
                  ('GET','/post',None,b'')]
        self.assertEqual(self.server.requests,expected*2)

    def test_explicit_same_origin_redirect_and_bounded_header_capture(self):
        self.accepted(self.with_client({'url':'/nested/hop','cross':'/cross','loop':'/loop',
                                       'duplicate':'/duplicate','malformed':'/malformed','large':'/large-headers'},'''
            assert(fields.add(utf8("X-Test"),utf8("sent")));
            {own res:http::Response=client.get_with_headers(url,fields,5000,8);
             assert(res.error()==0 && res.status_code()==302);}
            {own res:http::Response=client.get_following(url,fields,2,5000,8);
             assert(res.error()==0 && res.status_code()==200 && res.size()==8);}
            {own res:http::Response=client.get_following(cross,fields,2,5000,8);
             assert(res.error()==0 && res.status_code()==302);}
            {own res:http::Response=client.get_following(loop,fields,1,5000,8);
             assert(res.error()==0 && res.status_code()==302);}
            {own res:http::Response=client.get_following(duplicate,fields,2,5000,8);
             assert(res.error()==0 && res.status_code()==302 && len(res.header(utf8("Location")))==0);}
            {own res:http::Response=client.get_following(malformed,fields,2,5000,8);
             assert(res.error()==0 && res.status_code()==302);}
            {own res:http::Response=client.get_with_headers(large,fields,5000,0);
             assert(res.error()== -8);}
        '''))
        expected=['/nested/hop','/nested/hop','/echo?first=1','/cross','/loop','/loop',
                  '/duplicate','/malformed','/large-headers']
        self.assertEqual(self.server.requests,[('GET',path,'sent',b'') for path in expected]*2)

    def test_url_resolution_uses_rfc_examples_and_rejects_ambiguous_authority(self):
        def literal(value):
            return 'utf8('+json.dumps(value)+')'
        base_uri='http://a/b/c/d;p?q'
        cases={
            'g':'http://a/b/c/g','./g':'http://a/b/c/g','g/':'http://a/b/c/g/',
            '/g':'http://a/g','//g':'http://g/','?y':'http://a/b/c/d;p?y',
            '#s':'http://a/b/c/d;p?q#s','':'http://a/b/c/d;p?q',
            '../g':'http://a/b/g','../../../g':'http://a/g','./../g':'http://a/b/g',
            'g/./h':'http://a/b/c/g/h','g/../h':'http://a/b/c/h',
            'g?y/../x':'http://a/b/c/g?y/../x','g#s/../x':'http://a/b/c/g#s/../x',
            '/a//b/../':'http://a/a//','%2e%2e/g':'http://a/b/c/%2e%2e/g',
            'https://[2001:db8::1]:444/a/..':'https://[2001:db8::1]:444/',
        }
        src='import "std/httpurl.assis";\nsafe fn main():int{'
        for ref,expected in cases.items():
            src+=f'{{own b:*byte=httpurl::resolve({literal(base_uri)},{literal(ref)});'
            src+=f'assert(b!=null && len(b)=={len(expected)+1});'
            src+=f'borrow want:slice<byte>={literal(expected)};'
            src+='for(let i:int=0;i<len(want);i++){assert(b[i]==want[i]);}assert(b[len(want)]==0);}'
        for invalid in ['http://user@a','http://a\\b','http://%61','http://a:0','http://a:65536',
                        'http://[::1','http://[1:2:3:4:5:6:7:8:9]','http://[::ffff:999.1.1.1]',
                        'http://[fe80::1%25eth0]','http://127.1','http://0177.0.0.1','http://a/%xz']:
            src+=f'assert(httpurl::parse({literal(invalid)}).status== -1);'
        src+='assert(httpurl::same_origin(utf8("HTTPS://Example.org/a"),utf8("https://example.org:443/b")));'
        src+='assert(!httpurl::same_origin(utf8("http://example.org/a"),utf8("https://example.org/a")));'
        src+='assert(httpurl::parse(utf8("http://[::ffff:192.0.2.1]/")).status==0);return 0;}'
        self.accepted(src)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

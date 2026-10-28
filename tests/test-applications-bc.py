"""Real B/C programs: download, persistent IPC, restart and lock failures."""
import http.server
import importlib.util
import os
from pathlib import Path
import subprocess
import threading
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Applications(base.Evolution):
    def build_example(self,name):
        binary=self.temp/(name+'.exe');result=self.invoke('build',base.ROOT/'exemplos'/name,'--safe','--debug','-o',binary)
        self.assertEqual(result.returncode,0,result.stderr);return binary

    def service(self,binary,requests):
        return subprocess.run([binary,self.temp/'state á.bin',self.temp/'next á.bin',self.temp/'lock á.bin'],input=requests,capture_output=True,timeout=15)

    def test_c_persistence_protocol_limits_and_restart(self):
        binary=self.build_example('28_persistent_service.assis')
        r=self.service(binary,b'get\ninc\ninc\ninvalid\n'+b'x'*100+b'\nget\nquit\n')
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'0\n1\n2\nERR command\nERR command\n2\n',b''))
        r=self.service(binary,b'get\ninc\nquit\n');self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'2\n3\n',b''))
        self.assertEqual((self.temp/'state á.bin').stat().st_size,16);self.assertFalse((self.temp/'next á.bin').exists())
        (self.temp/'next á.bin').write_bytes(b'preserve')
        r=self.service(binary,b'inc\nget\nquit\n');self.assertEqual((r.returncode,r.stdout),(0,b'ERR store\n3\n'))
        self.assertEqual((self.temp/'next á.bin').read_bytes(),b'preserve')

    def test_c_lock_contention_crash_release_and_corruption(self):
        binary=self.build_example('28_persistent_service.assis');args=[binary,self.temp/'state á.bin',self.temp/'next á.bin',self.temp/'lock á.bin']
        child=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            child.stdin.write(b'inc\n');child.stdin.flush();self.assertEqual(child.stdout.readline(),b'1\n')
            r=self.service(binary,b'get\n');self.assertEqual((r.returncode,r.stdout),(73,b'ERR locked\n'))
        finally:
            child.kill();child.communicate(timeout=10)
        r=self.service(binary,b'get\nquit\n');self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'1\n',b''))
        before=(self.temp/'state á.bin').read_bytes();damaged=bytearray(before);damaged[4]^=1;(self.temp/'state á.bin').write_bytes(damaged)
        r=self.service(binary,b'inc\n');self.assertEqual((r.returncode,r.stdout),(65,b'ERR corrupt\n'))
        self.assertEqual((self.temp/'state á.bin').read_bytes(),damaged)

    def test_b_download_and_http_failure_preserve_existing_output(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                data=b'A\x00\xc3\xa7';self.send_response(404 if self.path=='/bad' else 200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        binary=self.build_example('27_http_client.assis');output=self.temp/'download á.bin';url=f'http://127.0.0.1:{server.server_address[1]}'
        r=subprocess.run([binary,url+'/ok',output],capture_output=True,timeout=20);self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'Downloaded 4 bytes\n',b''));self.assertEqual(output.read_bytes(),b'A\x00\xc3\xa7')
        r=subprocess.run([binary,url+'/bad',output],capture_output=True,timeout=20);self.assertEqual((r.returncode,r.stdout),(2,b'HTTP status 404\n'));self.assertEqual(output.read_bytes(),b'A\x00\xc3\xa7')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

"""Stream compiler and real OS budgets, with independent binary clients."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('compiler_worker',ROOT/'tests/test-page-worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
base=worker.base

def request(source,reference=False):
    if isinstance(source,str):source=source.encode()
    return b'ASC1'+struct.pack('<II',len(source),int(reference))+source

@unittest.skipUnless(worker.builder.supports_host(), 'Worker provider requires Windows/Linux x64')
class PageCompiler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory(prefix='assis-page-compiler-');cls.out=Path(cls.folder.name)
        built=worker.builder.build(cls.out,base.COMPILER);cls.worker=Path(built['worker']);cls.cc=built['cc']
        if os.name=='nt':
            spec=importlib.util.spec_from_file_location('compile_platform',ROOT/'tools/build-platform.py')
            platform=importlib.util.module_from_spec(spec);spec.loader.exec_module(platform);platform.build(cls.out/'assis_platform_v1.dll',testing=True)
        cls.lib=ctypes.CDLL(built['provider'])
        for name in ('assw_compile_open','assw_open','assw_send','assw_receive','assw_close','assw_usage'):getattr(cls.lib,name).restype=ctypes.c_int64
        cls.lib.assw_compile_open.argtypes=[ctypes.c_void_p,ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,ctypes.POINTER(ctypes.c_int64)]
        cls.lib.assw_send.argtypes=cls.lib.assw_receive.argtypes=[ctypes.c_int64,ctypes.c_void_p,ctypes.c_int64]
        cls.lib.assw_close.argtypes=[ctypes.c_int64]
        cls.lib.assw_usage.argtypes=[ctypes.c_int64,ctypes.POINTER(ctypes.c_int64),ctypes.c_int64]
        cls.env=dict(os.environ,PATH=str(cls.out)+os.pathsep+os.environ.get('PATH',''),LD_LIBRARY_PATH=str(cls.out))
        print('COMPILER_CANDIDATE '+json.dumps(dict(compiler_sha256=hashlib.sha256(base.COMPILER.read_bytes()).hexdigest(),provider_sha256=hashlib.sha256(Path(built['provider']).read_bytes()).hexdigest(),worker_sha256=hashlib.sha256(cls.worker.read_bytes()).hexdigest())),flush=True)
    @classmethod
    def tearDownClass(cls):
        if os.name=='nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.folder.cleanup()
    def setUp(self):
        self.temp=self.out/self._testMethodName;self.temp.mkdir()
    def stream(self,source,reference=False):
        return subprocess.run([str(base.COMPILER),'page-compile-worker'],input=request(source,reference),capture_output=True,timeout=10)
    def native_fixture(self,body):
        source=self.temp/'fixture.c';binary=self.temp/('fixture.exe' if os.name=='nt' else 'fixture')
        source.write_text('#include <stdio.h>\n#include <stdlib.h>\n#include <stdint.h>\nint main(void){'+body+'}',encoding='utf-8')
        subprocess.run([self.cc,'-O2',str(source),'-o',str(binary)],check=True,capture_output=True)
        return binary
    def start(self,path=None,mib=128,seconds=3):
        data=str(path or base.COMPILER).encode();token=ctypes.c_int64()
        self.assertEqual(self.lib.assw_compile_open(data,len(data),mib,seconds,ctypes.byref(token)),0)
        self.addCleanup(lambda:self.lib.assw_close(token.value));return token.value
    def usage(self,token):
        data=(ctypes.c_int64*6)();self.assertEqual(self.lib.assw_usage(token,data,6),0);return list(data)
    def communicate(self,token,data,expect_eof=False,piece=4096,timeout=8):
        at=0;result=bytearray();deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if at<len(data):
                n=self.lib.assw_send(token,data[at:at+piece],min(piece,len(data)-at))
                if n<0:self.assertTrue(expect_eof);return bytes(result)
                at+=n
            chunk=ctypes.create_string_buffer(4096);n=self.lib.assw_receive(token,chunk,4096)
            if n<0:self.assertEqual(n,-5);return bytes(result)
            result.extend(chunk.raw[:n]);time.sleep(.001)
        self.fail('compiler did not terminate within supervision deadline')
    def execute(self,body):
        source=self.temp/'host.assis';binary=self.temp/('host.exe' if os.name=='nt' else 'host')
        source.write_text('import "std/pagecompiler.assis";import "std/pagereader.assis";'
            'safe fn cells(borrow s:slice<byte>):int{return len(s);}'
            'safe fn main():int{'+body+'return 0;}',encoding='utf-8')
        mode=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
        r=subprocess.run([str(base.COMPILER),'build',str(source),'-o',str(binary),*mode],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(r.returncode,0,r.stderr)
        r=subprocess.run([str(binary)],capture_output=True,text=True,env=self.env,timeout=20,cwd=ROOT)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'',''))
    def task(self,source='safe fn main():int{return 42;}',name='t',path=None,timeout=3000):
        literal=worker.HOST.parser.literal
        return ('own '+name+':pagecompiler::Task=try_new pagecompiler::Task('+literal(str(path or base.COMPILER))+','+literal(source)+',false,128,3,monotonic_ms(),'+str(timeout)+');assert('+name+'!=null && '+name+'.status()==0);')
    def test_stream_matches_file_backend_in_both_modes_and_sdk_is_embedded(self):
        for source in ['safe fn main():int{return 42;}',
                'safe fn f(n:int):int{if(n<=1){return 1;}return n*f(n-1);}safe fn main():int{return f(8);}',
                'import "std/page.assis";safe fn main():int{return htdl_v1::state_set(0,htdl_v1::node_count());}']:
            for reference in (False,True):
                with self.subTest(source=source,reference=reference):
                    file=self.temp/'page.assis';file.write_text(source,encoding='utf-8');output=self.temp/'code.asv2'
                    r=subprocess.run([str(base.COMPILER),'build',str(file),'--target','page-asv2','-o',str(output),*(['--no-opt'] if reference else [])],capture_output=True)
                    self.assertEqual(r.returncode,0,r.stderr)
                    r=self.stream(source,reference);self.assertEqual(r.returncode,0,r.stderr)
                    self.assertEqual(r.stdout,struct.pack('<I',len(output.read_bytes()))+output.read_bytes())
    def test_import_paths_never_resolve_project_config_environment_or_aliases(self):
        for path in ['../secret.assis','std/../secret.assis','std\\page.assis','pkg:secret','/etc/passwd','C:/Windows/win.ini']:
            r=self.stream('import '+json.dumps(path)+';safe fn main():int{return 0;}')
            self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,b'');self.assertIn(b'somente std/page.assis',r.stderr)
    def test_source_and_protocol_hostile_bounds(self):
        cases=[b'BAD!'+struct.pack('<II',1,0)+b'x',b'ASC1'+struct.pack('<II',65537,0),b'ASC1'+struct.pack('<II',1,2)+b'x',
            request(b'\0'),request(b'\xff'),request(b'fn main('),request(b'safe fn main():int{return '+b'('*600+b'0'+b')'*600+b';}')]
        for data in cases:
            r=subprocess.run([str(base.COMPILER),'page-compile-worker'],input=data,capture_output=True,timeout=10)
            self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,b'')
    def test_backend_profile_still_denies_native_authority_in_dead_code(self):
        for source in ['safe fn main():int{if(false){print(42);}return 0;}',
                'extern("libc.so.6","KERNEL32.dll","system") fn bad(x:int):int;safe fn main():int{return 0;}',
                'safe fn main():int{return monotonic_ms();}']:
            r=self.stream(source);self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,b'')
    def test_provider_fragmented_stream_and_peak_memory(self):
        token=self.start();usage=self.usage(token);self.assertEqual(usage[:2],[1,128*1024*1024])
        data=self.communicate(token,request('safe fn main():int{return 42;}'),piece=1)
        self.assertEqual(struct.unpack_from('<I',data)[0],len(data)-4);self.assertEqual(data[4:8],b'ASV2')
        deadline=time.monotonic()+2
        while self.usage(token)[5]!=2:
            self.assertLess(time.monotonic(),deadline);time.sleep(.001)
    def test_invalid_quota_stale_and_wrong_thread(self):
        import threading
        for mib,cpu in [(15,1),(513,1),(16,0),(16,11)]:
            token=ctypes.c_int64(99);path=str(base.COMPILER).encode()
            self.assertEqual(self.lib.assw_compile_open(path,len(path),mib,cpu,ctypes.byref(token)),-1);self.assertEqual(token.value,0)
        data=(ctypes.c_int64*6)(*([9]*6));self.assertEqual(self.lib.assw_usage(999999,data,6),-2);self.assertEqual(list(data),[0]*6)
        values=[];t=threading.Thread(target=lambda:values.append(self.lib.assw_usage(999999,data,6)));t.start();t.join();self.assertEqual(values,[-6])
    def test_real_memory_refusal_preserves_neighbor_and_reports_usage(self):
        fixture=self.native_fixture('int n=0;while(n<1024){volatile unsigned char *p=malloc(1048576);if(!p)break;for(int i=0;i<1048576;i+=4096)p[i]=42;n++;}printf("%d\\n",n);fflush(stdout);getchar();return 0;')
        token=self.start(fixture,mib=16);neighbor=self.start();data=bytearray();deadline=time.monotonic()+5
        while b'\n' not in data:
            chunk=ctypes.create_string_buffer(4096);n=self.lib.assw_receive(token,chunk,4096);self.assertGreaterEqual(n,0);data.extend(chunk.raw[:n]);self.assertLess(time.monotonic(),deadline);time.sleep(.001)
        n=int(data);self.assertGreater(n,0);self.assertLess(n,16)
        usage=self.usage(token);self.assertEqual(usage[1],16*1024*1024);self.assertGreater(usage[2],0);self.assertGreaterEqual(usage[3],usage[2]);self.assertLessEqual(usage[4],usage[1])
        result=self.communicate(neighbor,request('safe fn main():int{return 7;}'));self.assertEqual(result[4:8],b'ASV2')
        print('RESOURCE_MEMORY '+json.dumps(dict(allocations_mib=n,usage=usage)),flush=True)
    def test_cpu_budget_terminates_busy_child_during_provider_polling(self):
        fixture=self.native_fixture('volatile uint64_t x=0;for(;;)x++;')
        token=self.start(fixture,seconds=1);started=time.monotonic();self.assertEqual(self.communicate(token,b'',expect_eof=True,timeout=6),b'')
        elapsed=time.monotonic()-started;self.assertLess(elapsed,6)
        deadline=time.monotonic()+2
        while self.usage(token)[5]!=2:
            self.assertLess(time.monotonic(),deadline);time.sleep(.001)
        print('RESOURCE_CPU '+json.dumps(dict(cpu_seconds=1,wall_seconds=round(elapsed,3))),flush=True)
    def test_task_validates_bytes_then_reader_worker_activates_same_result(self):
        literal=worker.HOST.parser.literal;doc=worker.DOC.decode()
        self.execute(self.task('import "std/page.assis";safe fn main():int{return htdl_v1::state_set(0,42);}')+
            'for(let i:int=0;i<5000 && !t.ready();i++){assert(t.poll(monotonic_ms())>=0);sleep_ms(1);}assert(t.ready() && !t.is_open());'
            'own s:pagereader::Session=try_new pagereader::Session(32000000,250000,7,11,19);assert(s!=null && s.is_open());'
            'assert(s.prepare('+literal(str(self.worker))+','+literal(doc)+',t.code(),'+('true')+',300,200,16,cells,new pagereader::Limits(0,16,100000,1000,3000),new pagereader::Grants(true,false),monotonic_ms())==0);'
            'for(let i:int=0;i<5000 && !s.ready();i++){assert(s.advance(monotonic_ms())>=0);sleep_ms(1);}assert(s.ready() && s.commit());'
            'for(let i:int=0;i<5000 && s.result().state!=42;i++){assert(s.advance(monotonic_ms())>=0);sleep_ms(1);}assert(s.result().state==42);s.close();t.close();assert(!t.ready());')
    def test_deadline_cancel_drop_and_failed_source_keep_neighbor_live(self):
        self.execute(self.task(name='a')+self.task(name='b')+
            'assert(a.poll(monotonic_ms()+3000)== -20 && !a.is_open());a.close();assert(a.status()== -9);'
            'for(let i:int=0;i<5000 && !b.ready();i++){assert(b.poll(monotonic_ms())>=0);sleep_ms(1);}assert(b.ready());'+
            self.task('fn main(',name='c')+'let status:int=0;for(let i:int=0;i<5000 && status==0;i++){status=c.poll(monotonic_ms());sleep_ms(1);}assert(status== -21 && !c.ready());assert(b.ready());'
            '{'+self.task(name='d')+'}assert(b.poll(monotonic_ms())==1);')
    def test_task_rejects_forged_response_and_preserves_clock_contract(self):
        fake=self.native_fixture('unsigned char b[]={24,0,0,0,65,83,86,50};fwrite(b,1,sizeof(b),stdout);for(int i=0;i<20;i++)putchar(255);fflush(stdout);getchar();return 0;')
        self.execute(self.task(path=fake)+'assert(t.poll(0)== -1 && t.is_open());let status:int=0;for(let i:int=0;i<5000 && status==0;i++){status=t.poll(monotonic_ms());sleep_ms(1);}assert(status== -22 && !t.ready());')
    def pipeline(self,program,doc=None):
        literal=worker.HOST.parser.literal
        return ('s.prepare_source('+literal(str(base.COMPILER))+','+literal(str(self.worker))+','+literal(doc or worker.DOC.decode())+','+literal(program)+
            ',false,128,3,'+('true')+',300,200,16,cells,new pagereader::Limits(0,16,100000,1000,3000),new pagereader::Grants(true,false),monotonic_ms())')
    def test_source_navigation_compiles_before_activation_and_rolls_back_all_failures(self):
        self.execute('own s:pagereader::Session=try_new pagereader::Session(32000000,250000,7,11,19);assert(s!=null && s.is_open());'
            'assert('+self.pipeline('import "std/page.assis";safe fn main():int{return htdl_v1::state_set(0,42);}')+'==0);'
            'assert(s.has_pending() && !s.has_active() && !s.ready());'
            'for(let i:int=0;i<5000 && !s.ready();i++){assert(s.advance(monotonic_ms())>=0);sleep_ms(1);}assert(s.ready() && s.commit());'
            'for(let i:int=0;i<5000 && s.result().state!=42;i++){assert(s.advance(monotonic_ms())>=0);sleep_ms(1);}assert(s.result().state==42);val id:int=s.document_id();'
            'assert('+self.pipeline('fn main(')+'==0);let status:int=0;for(let i:int=0;i<5000 && status==0;i++){status=s.advance(monotonic_ms());sleep_ms(1);}assert(status== -21 && !s.has_pending() && s.document_id()==id && s.worker_alive());'
            'assert('+self.pipeline('safe fn main():int{return 0;}','invalid HTDL')+'==0);status=0;for(let i:int=0;i<5000 && status==0;i++){status=s.advance(monotonic_ms());sleep_ms(1);}assert(status!=0 && !s.has_pending() && s.document_id()==id && s.worker_alive());'
            'assert('+self.pipeline('safe fn main():int{return 9;}')+'==0);s.abort();assert(!s.has_pending() && s.document_id()==id && s.worker_alive());'
            'assert('+self.pipeline('safe fn main():int{return 7;}')+'==0);s.close();assert(!s.is_open() && !s.has_pending());')

    def test_repeated_compiler_cancel_reclaims_slots_and_os_handles(self):
        count=None
        if os.name=='nt':
            import ctypes.wintypes as w
            kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=w.HANDLE
            kernel.GetProcessHandleCount.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)]
            def count():
                n=w.DWORD();self.assertTrue(kernel.GetProcessHandleCount(kernel.GetCurrentProcess(),ctypes.byref(n)));return n.value
        else:
            def count():return len(list(Path('/proc/self/fd').iterdir()))
        before=count()
        for _ in range(128):
            token=self.start();self.assertEqual(self.lib.assw_close(token),0)
        self.assertEqual(count(),before)

if __name__=='__main__':unittest.main(verbosity=2)

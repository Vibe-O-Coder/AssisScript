"""Independent binary client, real workers, supervision and hostile streams."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import time
import threading
import unittest

ROOT=Path(__file__).resolve().parent.parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('evolution',ROOT/'tests/test-evolution.py')
builder=module('worker_builder',ROOT/'tools/build-page-worker.py')
HOST=module('host',ROOT/'tests/test-page-host.py')
DOC=HOST.parser.document('<div type="paragraph">Olá</div><div type="button">Add</div>').encode()
HEADER=struct.Struct('<4sHHQqqqqqqqq')
def frame(kind,request=1,payload=b'',identity=(7,11,1),args=(0,0,0,0)):
    return HEADER.pack(b'ASIP',1,kind,len(payload),*identity,request,*args)+payload
def load(code,**kw):return frame(1,payload=struct.pack('<I',len(DOC))+DOC+code,args=(0,16,100000,1000),**kw)

@unittest.skipUnless(builder.supports_host(), 'Worker provider requires Windows/Linux x64')
class PageWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory(prefix='assis-worker-');cls.out=Path(cls.folder.name)
        built=builder.build(cls.out,base.COMPILER);cls.worker=Path(built['worker']);cls.cc=built['cc'];cls.provider=Path(built['provider'])
        print('WORKER_CANDIDATE '+json.dumps(dict(worker_sha256=hashlib.sha256(cls.worker.read_bytes()).hexdigest(),provider_sha256=hashlib.sha256(cls.provider.read_bytes()).hexdigest(),mode='reference' if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else 'optimized')),flush=True)
        cls.lib=ctypes.CDLL(str(cls.provider))
        for name in ('assw_version','assw_open','assw_send','assw_receive','assw_close'):getattr(cls.lib,name).restype=ctypes.c_int64
        cls.lib.assw_open.argtypes=[ctypes.c_void_p,ctypes.c_int64,ctypes.c_int64,ctypes.POINTER(ctypes.c_int64)]
        cls.lib.assw_send.argtypes=cls.lib.assw_receive.argtypes=[ctypes.c_int64,ctypes.c_void_p,ctypes.c_int64]
        cls.lib.assw_close.argtypes=[ctypes.c_int64]
        cls.env=dict(os.environ,PATH=str(cls.out)+os.pathsep+os.environ.get('PATH',''),LD_LIBRARY_PATH=str(cls.out),ASSIS_WORKER_SECRET='never inherited')
        cls.code=cls.compile_page('safe fn main():int{return 42;}')

    @classmethod
    def tearDownClass(cls):
        # Windows keeps a ctypes DLL mapped. Unload before deleting own temp.
        if os.name=='nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.folder.cleanup()

    @classmethod
    def compile_page(cls,source):
        file=cls.out/'page.assis';file.write_text(source,encoding='utf-8');output=cls.out/'code.asv2'
        flags=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
        subprocess.run([str(base.COMPILER),'build',str(file),'--target','page-asv2','-o',str(output),*flags],cwd=ROOT,check=True,capture_output=True)
        return output.read_bytes()

    def start(self,path=None,restricted=None):
        path=str(path or self.worker).encode();token=ctypes.c_int64()
        mode=1 if restricted is None else restricted
        result=self.lib.assw_open(path,len(path),mode,ctypes.byref(token));self.assertEqual(result,0)
        self.addCleanup(lambda:self.lib.assw_close(token.value));return token.value

    def send(self,token,data,pieces=None):
        at=0;deadline=time.monotonic()+5
        while at<len(data):
            size=min((pieces or 4096),len(data)-at);n=self.lib.assw_send(token,data[at:at+size],size)
            self.assertGreaterEqual(n,0);at+=n;self.assertLess(time.monotonic(),deadline)
            if not n:time.sleep(.001)

    def receive(self,token):
        data=bytearray();deadline=time.monotonic()+5;target=80
        while len(data)<target:
            chunk=ctypes.create_string_buffer(min(4096,target-len(data)));n=self.lib.assw_receive(token,chunk,len(chunk))
            self.assertGreaterEqual(n,0,bytes(data));data.extend(chunk.raw[:n]);self.assertLess(time.monotonic(),deadline)
            if len(data)>=80:target=80+HEADER.unpack_from(data)[3]
            if not n:time.sleep(.001)
        self.assertEqual(len(data),144);return HEADER.unpack_from(data),struct.unpack_from('<8q',data,80)

    def hello(self,token):
        header,body=self.receive(token);self.assertEqual(header[:4],(b'ASIP',1,128,64));self.assertEqual(header[4:8],(0,0,0,0));self.assertEqual(body[6],1)

    def request(self,token,data):self.send(token,data);return self.receive(token)

    def eof(self,token):
        deadline=time.monotonic()+5;chunk=ctypes.create_string_buffer(4096)
        while True:
            n=self.lib.assw_receive(token,chunk,4096)
            if n<0:self.assertEqual(n,-5);return
            self.assertEqual(n,0);self.assertLess(time.monotonic(),deadline);time.sleep(.001)

    def test_raw_wire_fragmentation_real_page_and_identity(self):
        token=self.start();self.hello(token);self.send(token,load(self.code),pieces=1)
        header,body=self.receive(token);self.assertEqual(header[2],129);self.assertEqual(header[4:8],(7,11,1,1));self.assertEqual(header[8],0)
        _,body=self.request(token,frame(2,2,args=(10000,0,0,0)));self.assertEqual(body[:2],(2,42));self.assertGreater(body[2],0)
        self.request(token,frame(7,3));self.eof(token)

    def test_sdk_state_and_event_model_across_process(self):
        code=self.compile_page('import "std/page.assis";safe fn main():int{return htdl_v1::state_set(0,htdl_v1::state_get(0)+htdl_v1::event_get(0)+htdl_v1::event_get(1));}')
        t=self.start();self.hello(t);self.request(t,load(code));request=1
        def drain():
            nonlocal request
            for _ in range(100):
                request+=1;_,body=self.request(t,frame(2,request,args=(10000,0,0,0)))
                if body[0]==2:return body
            self.fail('event did not complete')
        self.assertEqual(drain()[1],1);expected=1;rng=random.Random(20261102)
        for _ in range(20):
            kind=rng.choice([2,3]);delta=rng.randrange(-40,40);request+=1
            self.request(t,frame(5,request,args=(kind,delta,0,0)));expected+=kind+delta
            body=drain();self.assertEqual((body[1],body[4]),(expected,expected))

    def test_protocol_rejects_version_length_epoch_replay_and_reserved_fields(self):
        mutants=[]
        valid=load(self.code)
        for at,value in [(0,0),(4,2),(5,1),(7,1),(12,1)]:
            data=bytearray(valid);data[at]=value;mutants.append(bytes(data[:80]) if at==12 else bytes(data))
        mutants.append(frame(1,payload=b'',args=(0,16,100,0)))
        for data in mutants:
            with self.subTest(prefix=data[:16].hex()):
                t=self.start();self.hello(t);self.send(t,data);self.eof(t);self.lib.assw_close(t)
        for identity,request in [((8,11,1),2),((7,12,1),2),((7,11,2),2),((7,11,1),1)]:
            t=self.start();self.hello(t);self.request(t,load(self.code));self.send(t,frame(8,request,identity=identity));self.eof(t);self.lib.assw_close(t)
        for args in [(0,0,1,0),(0,0,0,1),(1,0,0,0)]:
            t=self.start();self.hello(t);self.request(t,load(self.code));self.send(t,frame(8,2,args=args));self.eof(t);self.lib.assw_close(t)

    def test_fuel_revocation_and_crash_leave_neighbor_live(self):
        slow=self.compile_page('safe fn main():int{while(true){}return 0;}')
        a=self.start();b=self.start();self.hello(a);self.hello(b)
        self.request(a,load(slow));self.request(b,load(self.code,identity=(8,12,3)))
        header,body=self.request(a,frame(2,2,args=(7,0,0,0)));self.assertEqual((header[8],body[0],body[2]),(1,0,7))
        self.request(a,frame(6,3));_,body=self.request(a,frame(2,4,args=(7,0,0,0)));self.assertEqual(body[0],-2)
        self.send(a,frame(8,5,identity=(9,11,1)));self.eof(a)
        _,body=self.request(b,frame(2,2,identity=(8,12,3),args=(10000,0,0,0)));self.assertEqual(body[1],42)

    def test_catalog_load_is_explicit_and_bootstrap_remains_strict(self):
        source=HOST.parser.document('<div type="main"><div type="list"><div type="item"><div type="paragraph">Text</div></div></div><div type="button">Add</div></div>').encode()
        code=self.compile_page('import "std/page.assis";safe fn main():int{return htdl_v1::node_count();}')
        payload=struct.pack('<I',len(source))+source+code
        old=self.start();self.hello(old)
        header,_=self.request(old,frame(1,payload=payload,args=(0,16,100000,1000)))
        self.assertEqual(header[8],-1203);self.eof(old)
        current=self.start();self.hello(current)
        header,_=self.request(current,frame(9,payload=payload,args=(0,16,100000,1000)))
        self.assertEqual((header[2],header[8]),(137,0))
        self.request(current,frame(4,2))
        for request in range(3,103):
            header,body=self.request(current,frame(2,request,args=(10000,0,0,0)))
            if header[8]==2:break
        else:self.fail('catalog SDK event did not finish')
        # XML element count is independent of the product's query/box encoding.
        import xml.etree.ElementTree as ET
        self.assertEqual(body[1],sum(1 for _ in ET.fromstring(source).iter()))
        self.send(current,frame(9,request+1,payload=payload,args=(0,16,100000,1000)));self.eof(current)
        for damaged in [b'',struct.pack('<I',65537)+code,struct.pack('<I',len(source))+source+bytes(16)]:
            token=self.start();self.hello(token);self.send(token,frame(9,payload=damaged,args=(0,16,100000,1000)))
            if len(damaged)<20 or damaged[:4]==struct.pack('<I',65537):self.eof(token)
            else:
                header,_=self.receive(token);self.assertLess(header[8],0);self.eof(token)

    def test_native_tokens_limits_slots_and_release(self):
        token=ctypes.c_int64(99);self.assertEqual(self.lib.assw_open(b'relative',8,0,ctypes.byref(token)),-1);self.assertEqual(token.value,0)
        self.assertEqual(self.lib.assw_close(9223372036854775807),-2)
        for _ in range(25):
            t=self.start();self.hello(t);self.assertEqual(self.lib.assw_close(t),0);self.assertEqual(self.lib.assw_close(t),-2)
        tokens=[self.start() for _ in range(16)]
        for t in tokens:self.hello(t)
        path=str(self.worker).encode();self.assertEqual(self.lib.assw_open(path,len(path),0,ctypes.byref(token)),-4)
        for t in tokens:self.lib.assw_close(t)
        errors=[];thread=threading.Thread(target=lambda:errors.append(self.lib.assw_close(1)));thread.start();thread.join();self.assertEqual(errors,[-6])

    @unittest.skipUnless(os.name=='nt','Windows native AppContainer negotiation')
    def test_windows_restricted_worker_enters_before_reading_input(self):
        token=self.start(restricted=1);self.hello(token)

    @unittest.skipUnless(os.name=='nt','Windows Job memory and explicit handle/environment inheritance')
    def test_windows_job_memory_and_minimum_inheritance(self):
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        class Attributes(ctypes.Structure):_fields_=[('size',ctypes.c_uint32),('descriptor',ctypes.c_void_p),('inherit',ctypes.c_int32)]
        kernel.CreateEventW.restype=ctypes.c_void_p
        attrs=Attributes(ctypes.sizeof(Attributes),None,1);handle=kernel.CreateEventW(ctypes.byref(attrs),1,0,None);self.assertTrue(handle)
        self.addCleanup(lambda:kernel.CloseHandle(ctypes.c_void_p(handle)))
        source=self.out/'windows-oracle.c';oracle=self.out/'windows-oracle.exe'
        source.write_text('#include <windows.h>\n#include <stdint.h>\nint main(void){DWORD f=0;int mask=0;char value[64];if(!GetEnvironmentVariableA("ASSIS_WORKER_SECRET",value,64))mask|=1;'
            f'if(!GetHandleInformation((HANDLE)(uintptr_t){handle}ULL,&f))mask|=2;'
            'if(!VirtualAlloc(NULL,256*1024*1024,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE))mask|=4;'
            'DWORD count;WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),&mask,4,&count,NULL);return 0;}',encoding='utf-8')
        env=dict(os.environ,PATH=str(Path(self.cc).parent)+os.pathsep+os.environ.get('PATH',''))
        subprocess.run([self.cc,str(source),'-o',str(oracle)],env=env,check=True,capture_output=True)
        original=os.environ.get('ASSIS_WORKER_SECRET');os.environ['ASSIS_WORKER_SECRET']='never inherited'
        try:t=self.start(oracle)
        finally:
            if original is None:os.environ.pop('ASSIS_WORKER_SECRET',None)
            else:os.environ['ASSIS_WORKER_SECRET']=original
        result=bytearray();limit=time.monotonic()+5
        while len(result)<4:
            chunk=ctypes.create_string_buffer(4-len(result));n=self.lib.assw_receive(t,chunk,len(chunk));self.assertGreaterEqual(n,0)
            result.extend(chunk.raw[:n]);self.assertLess(time.monotonic(),limit)
            if not n:time.sleep(.001)
        self.assertEqual(struct.unpack('<I',result)[0],7)

    def compile_host(self,body):
        source=self.out/'supervisor.assis';source.write_text('import "std/pageworker.assis";safe fn wait(borrow mut w:pageworker::Worker):void{let done:bool=false;for(let i:int=0;i<3000;i++){val r:int=w.poll(0);assert(r>=0);if(r==1){done=true;break;}sleep_ms(1);}assert(done);}safe fn main():int{'+body+'return 0;}',encoding='utf-8')
        binary=self.out/('supervisor.exe' if os.name=='nt' else 'supervisor')
        flags=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
        result=subprocess.run([str(base.COMPILER),'build',str(source),'-o',str(binary),*flags],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);return binary

    def hostile(self,data,stall=False):
        source=self.out/'hostile.c';binary=self.out/('hostile.exe' if os.name=='nt' else 'hostile')
        source.write_text('#include <stdio.h>\n#include <stdint.h>\n'+
            ('#include <windows.h>\n#define WAIT Sleep(5000)\n' if os.name=='nt' else '#include <unistd.h>\n#define WAIT sleep(5)\n')+
            'int main(void){unsigned char data[]={'+','.join(map(str,data or b'\0'))+'};'+
            (f'fwrite(data,1,{len(data)},stdout);fflush(stdout);' if data else '')+('WAIT;' if stall else '')+'return 0;}',encoding='utf-8')
        env=dict(os.environ,PATH=str(Path(self.cc).parent)+os.pathsep+os.environ.get('PATH',''))
        subprocess.run([self.cc,str(source),'-o',str(binary)],env=env,check=True,capture_output=True);return binary

    def test_supervisor_rejects_hostile_hello_oversize_trailing_and_eof(self):
        hello=frame(128,0,b'\0'*64,identity=(0,0,0))
        cases=[b'',hello[:17],frame(128,0,b'\0'*64,identity=(7,0,0)),hello+b'x',frame(127,0,b'\0'*64,identity=(0,0,0))]
        data=bytearray(hello);struct.pack_into('<Q',data,8,196629);cases.append(bytes(data[:80]))
        for data in cases:
            with self.subTest(length=len(data)):
                path=json.dumps(str(self.hostile(data)).replace('\\','/'))
                binary=self.compile_host(f'own w:pageworker::Worker=try_new pageworker::Worker(utf8({path}),7,11,1,false,0,1000);assert(w!=null && w.is_open());let failed:bool=false;for(let i:int=0;i<3000;i++){{val r:int=w.poll(0);if(r<0){{assert(r== -21 || r== -22);failed=true;break;}}sleep_ms(1);}}assert(failed && !w.is_open());')
                r=subprocess.run([str(binary)],env=self.env,capture_output=True,timeout=10);self.assertEqual((r.returncode,r.stderr),(0,b''))

    def test_stalled_worker_deadline_and_drop_release_all_slots(self):
        path=json.dumps(str(self.hostile(b'',stall=True)).replace('\\','/'))
        binary=self.compile_host(f'for(let i:int=0;i<24;i++){{own w:pageworker::Worker=try_new pageworker::Worker(utf8({path}),7,11,i+1,false,0,1);assert(w!=null && w.is_open());assert(w.poll(1)== -20 && !w.is_open());}}for(let i:int=0;i<24;i++){{own w:pageworker::Worker=try_new pageworker::Worker(utf8({path}),8,12,i+1,false,0,1000);assert(w!=null && w.is_open());}}')
        started=time.monotonic();r=subprocess.run([str(binary)],env=self.env,capture_output=True,timeout=10)
        self.assertEqual((r.returncode,r.stderr),(0,b''));self.assertLess(time.monotonic()-started,6)

    def test_idle_worker_exit_is_detected_without_new_command(self):
        hello=frame(128,0,b'\0'*64,identity=(0,0,0));path=json.dumps(str(self.hostile(hello)).replace('\\','/'))
        binary=self.compile_host(f'own w:pageworker::Worker=try_new pageworker::Worker(utf8({path}),7,11,1,false,0,1000);assert(w!=null && w.is_open());wait(w);assert(w.ready());let stopped:bool=false;for(let i:int=0;i<3000;i++){{val r:int=w.poll(0);if(r<0){{assert(r== -21);stopped=true;break;}}sleep_ms(1);}}assert(stopped && !w.is_open());')
        r=subprocess.run([str(binary)],env=self.env,capture_output=True,timeout=10);self.assertEqual((r.returncode,r.stderr),(0,b''))

    def test_supervisor_rejects_old_epoch_request_and_response_kind(self):
        hello=frame(128,0,b'\0'*64,identity=(0,0,0))
        for identity,request,kind in [((8,11,1),1,129),((7,12,1),1,129),((7,11,2),1,129),((7,11,1),2,129),((7,11,1),1,130)]:
            source=self.out/'hostile.c';binary=self.out/('hostile.exe' if os.name=='nt' else 'hostile')
            response=frame(kind,request,b'\0'*64,identity=identity)
            source.write_text('#include <stdio.h>\nint main(void){unsigned char hello[]={'+','.join(map(str,hello))+'};unsigned char reply[]={'+','.join(map(str,response))+'};unsigned char input[4096];fwrite(hello,1,sizeof(hello),stdout);fflush(stdout);fread(input,1,1,stdin);fwrite(reply,1,sizeof(reply),stdout);fflush(stdout);return 0;}',encoding='utf-8')
            env=dict(os.environ,PATH=str(Path(self.cc).parent)+os.pathsep+os.environ.get('PATH',''))
            subprocess.run([self.cc,str(source),'-o',str(binary)],env=env,check=True,capture_output=True)
            path=json.dumps(str(binary).replace('\\','/'));body=HOST.data_buffer(self.code)
            body+=f'own w:pageworker::Worker=try_new pageworker::Worker(utf8({path}),7,11,1,false,0,1000);assert(w!=null && w.is_open());wait(w);assert(w.load(utf8({json.dumps(DOC.decode())}),slice_of(code,0,len(code)),0,16,10000,100,0,1000)==0);let failed:bool=false;for(let i:int=0;i<3000;i++){{val r:int=w.poll(0);if(r<0){{assert(r== -22);failed=true;break;}}sleep_ms(1);}}assert(failed && !w.is_open());'
            host=self.compile_host(body);r=subprocess.run([str(host)],env=self.env,capture_output=True,timeout=10);self.assertEqual((r.returncode,r.stderr),(0,b''))

    def test_transactional_navigation_failure_abort_reload_and_close(self):
        path=json.dumps(str(self.worker).replace('\\','/'));restricted='true'
        code84=self.compile_page('safe fn main():int{return 84;}')
        source=HOST.data_buffer(self.code)+HOST.data_buffer(code84,'next')
        source+='own s:pageworker::Session=try_new pageworker::Session();assert(s!=null);'
        source+=f'assert(s.prepare(utf8({path}),7,11,{restricted},0,1000)==0 && !s.commit());wait(s.candidate_mut());'
        source+='assert(!s.commit());assert(s.candidate_mut().load(utf8('+json.dumps(DOC.decode())+'),slice_of(code,0,len(code)),0,16,10000,100,0,1000)==0);wait(s.candidate_mut());assert(s.commit() && s.has_active() && !s.has_pending());'
        source+='assert(s.current_mut().command(2,10000,0,0,1000)==0);wait(s.current_mut());assert(s.current().reply().result==42);'
        source+=f'assert(s.prepare(utf8({path}),7,11,{restricted},0,1000)==0 && s.epoch()==2);wait(s.candidate_mut());'
        source+='assert(s.candidate_mut().load(utf8("invalid"),slice_of(next,0,len(next)),0,16,10000,100,0,1000)==0);wait(s.candidate_mut());assert(!s.candidate_mut().is_open() && !s.commit() && s.current().reply().result==42);s.abort();'
        source+=f'assert(s.prepare(utf8({path}),7,11,{restricted},0,1000)==0 && s.epoch()==3);wait(s.candidate_mut());'
        source+='assert(s.candidate_mut().load(utf8('+json.dumps(DOC.decode())+'),slice_of(next,0,len(next)),0,16,10000,100,0,1000)==0);wait(s.candidate_mut());assert(s.commit());assert(s.current_mut().command(2,10000,0,0,1000)==0);wait(s.current_mut());assert(s.current().reply().result==84);'
        source+='s.close();s.close();assert(!s.has_active() && !s.has_pending() && !s.commit());print(84);'
        binary=self.compile_host(source);r=subprocess.run([str(binary)],env=self.env,capture_output=True,timeout=15)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'84\n',b''))

    def test_background_cpu_and_output_stall_do_not_block_neighbor(self):
        a=self.start(self.hostile(b'',stall=True));b=self.start();self.hello(b);self.request(b,load(self.code,identity=(8,12,1)))
        # A never-responding worker remains alive while the neighbor executes.
        started=time.monotonic();_,body=self.request(b,frame(2,2,identity=(8,12,1),args=(10000,0,0,0)))
        self.assertEqual(body[1],42);self.assertLess(time.monotonic()-started,1)
        self.lib.assw_close(a)
        code=self.compile_page('safe fn main():int{let x:int=0;for(let i:int=0;i<1000000;i++){x+=i;}return x;}')
        a=self.start();self.hello(a);self.request(a,load(code));self.send(a,frame(2,2,args=(10000,0,0,0)))
        _,body=self.request(b,frame(8,3,identity=(8,12,1)));self.assertEqual(body[1],42)
        self.receive(a)

    def test_document_and_counter_default_deny_grants_and_revocation(self):
        code=self.compile_page('import "std/page.assis";safe fn main():int{return htdl_v1::node_count();}')
        t=self.start();self.hello(t);self.request(t,load(code));request=1
        def run():
            nonlocal request
            for _ in range(50):
                request+=1;h,body=self.request(t,frame(2,request,args=(10000,0,0,0)))
                if h[8]==2:return body[1]
            self.fail('SDK did not complete')
        self.assertEqual(run(),-2);request+=1;h,_=self.request(t,frame(4,request));self.assertEqual(h[8],0)
        request+=1;self.request(t,frame(5,request,args=(2,0,0,0)));self.assertEqual(run(),6)
        request+=1;self.request(t,frame(6,request));request+=1;h,_=self.request(t,frame(4,request));self.assertEqual(h[8],-2)
        counter=self.compile_page('import "std/page.assis";safe fn main():int{return htdl_v1::counter_add(1);}')
        for grant,expected in [(False,-2),(True,1)]:
            t=self.start();self.hello(t);self.request(t,load(counter));req=2
            if grant:self.request(t,frame(3,req));req+=1
            h,body=self.request(t,frame(2,req,args=(10000,0,0,0)));self.assertEqual(h[8],2 if grant else expected)
            if grant:self.assertEqual((body[1],body[3]),(1,1))

    def test_shipped_worker_example_requires_isolation_by_default(self):
        code=self.compile_page((ROOT/'exemplos/pages/counter.assis').read_text(encoding='utf-8'));artifact=self.out/'counter.asv2';artifact.write_bytes(code)
        example=self.out/('example.exe' if os.name=='nt' else 'example')
        flags=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
        built=subprocess.run([str(base.COMPILER),'build',str(ROOT/'exemplos/49_page_worker.assis'),'-o',str(example),*flags],capture_output=True)
        self.assertEqual(built.returncode,0,built.stderr)
        args=[str(example),str(self.worker),str(artifact)]
        r=subprocess.run(args,env=self.env,capture_output=True,timeout=10)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'WORKER 2 STATE 2 ISOLATION 1\n',b''))
        if os.name=='nt':
            r=subprocess.run(args+['--trusted-local'],env=self.env,capture_output=True,timeout=10)
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'WORKER 2 STATE 2 ISOLATION 0\n',b''))

    def test_large_frames_backpressure_coalescing_and_fuel_quota(self):
        t=self.start();self.hello(t)
        # A maximum-size HTDL source with whitespace is independently generated.
        source=DOC+b' '*(65536-len(DOC));data=frame(1,payload=struct.pack('<I',len(source))+source+self.code,args=(0,16,1,0))
        self.send(t,data);_,body=self.receive(t);self.assertEqual(body[0],0)
        # Two complete commands in one write exercise decoder reset at frame end.
        self.send(t,frame(2,2,args=(10000,0,0,0))+frame(8,3))
        h,body=self.receive(t);self.assertEqual(h[8],-3);self.assertEqual(body[2],1)
        h,body=self.receive(t);self.assertEqual(h[2],136);self.assertEqual(body[0],-3)
        self.assertEqual(self.lib.assw_close(t),0)
        # Undrained output cannot block the trusted host's nonblocking writes.
        t=self.start();self.hello(t);self.request(t,load(self.code))
        pending=b''.join(frame(8,r) for r in range(2,2002));at=0;blocked=False
        for _ in range(300):
            chunk=pending[at:at+4096]
            if not chunk:break
            count=self.lib.assw_send(t,chunk,len(chunk));self.assertGreaterEqual(count,0)
            if not count:blocked=True;break
            at+=count
        self.assertTrue(blocked);self.lib.assw_close(t)

    @unittest.skipUnless(os.name!='nt','Linux seccomp syscall and process limits')
    def test_linux_default_deny_syscalls_memory_environment_and_descriptors(self):
        oracle=self.out/'isolation-oracle'
        subprocess.run([self.cc,str(ROOT/'tests/worker-isolation-oracle.c'),str(ROOT/'providers/worker/worker.c'),'-pthread','-o',str(oracle)],check=True,capture_output=True)
        original=os.environ.get('ASSIS_WORKER_SECRET');os.environ['ASSIS_WORKER_SECRET']='never inherited'
        try:t=self.start(oracle)
        finally:
            if original is None:os.environ.pop('ASSIS_WORKER_SECRET',None)
            else:os.environ['ASSIS_WORKER_SECRET']=original
        result=bytearray();limit=time.monotonic()+5
        while len(result)<4:
            chunk=ctypes.create_string_buffer(4-len(result));n=self.lib.assw_receive(t,chunk,len(chunk));self.assertGreaterEqual(n,0)
            result.extend(chunk.raw[:n]);self.assertLess(time.monotonic(),limit)
            if not n:time.sleep(.001)
        self.assertEqual(struct.unpack('<I',result)[0],8191)

    @unittest.skipUnless(os.name!='nt','Linux hard CPU lifetime limit')
    def test_linux_cpu_limit_kills_busy_worker_and_preserves_neighbor(self):
        source=self.out/'cpu-oracle.c';oracle=self.out/'cpu-oracle'
        source.write_text('#include "'+str(ROOT/'providers/worker/assis_worker_v1.h')+'"\nint main(void){if(assw_restrict()!=1)return 70;volatile unsigned long x=0;for(;;)x++;}',encoding='utf-8')
        subprocess.run([self.cc,str(source),str(ROOT/'providers/worker/worker.c'),'-pthread','-O2','-o',str(oracle)],check=True,capture_output=True)
        started=time.monotonic();t=self.start(oracle);neighbor=self.start();self.hello(neighbor);self.request(neighbor,load(self.code))
        _,body=self.request(neighbor,frame(2,2,args=(10000,0,0,0)));self.assertEqual(body[1],42)
        self.eof(t);self.assertGreater(time.monotonic()-started,1);self.assertLess(time.monotonic()-started,7)
        _,body=self.request(neighbor,frame(8,3));self.assertEqual(body[1],42)

    def test_assisscript_supervisor_nonblocking_deadline_drop_and_neighbor(self):
        path=json.dumps(str(self.worker).replace('\\','/'));restricted='true'
        buffer=HOST.data_buffer(self.code)
        source='''own w:pageworker::Worker=try_new pageworker::Worker(utf8(PATH),7,11,1,RESTRICTED,0,1000);
          assert(w!=null && w.is_open());let done:bool=false;
          for(let i:int=0;i<2000;i++){val r:int=w.poll(0);assert(r>=0);if(r==1){done=true;break;}sleep_ms(1);}assert(done && w.ready());
          BUFFER
          assert(w.load(utf8(DOC),slice_of(code,0,len(code)),0,16,10000,100,1,1000)==0);
          done=false;for(let i:int=0;i<2000;i++){val r:int=w.poll(1);assert(r>=0);if(r==1){done=true;break;}sleep_ms(1);}assert(done && w.reply().code==0);
          assert(w.command(2,10000,0,2,1000)==0);done=false;
          for(let i:int=0;i<2000;i++){val r:int=w.poll(2);assert(r>=0);if(r==1){done=true;break;}sleep_ms(1);}assert(done && w.reply().result==42);
          assert(w.command(8,0,0,3,1)==0);assert(w.poll(4)== -20 && !w.is_open());w.close();
          own other:pageworker::Worker=try_new pageworker::Worker(utf8(PATH),8,12,2,RESTRICTED,0,1000);
          assert(other!=null && other.is_open());done=false;
          for(let i:int=0;i<2000;i++){val r:int=other.poll(0);assert(r>=0);if(r==1){done=true;break;}sleep_ms(1);}assert(done && other.ready());
          assert(other.poll(-1)== -1 && other.is_open());other.close();print(42);
        '''.replace('PATH',path).replace('RESTRICTED',restricted).replace('BUFFER',buffer).replace('DOC',json.dumps(DOC.decode()))
        binary=self.compile_host(source);r=subprocess.run([str(binary)],cwd=ROOT,env=self.env,capture_output=True,timeout=15)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'42\n',b''))

if __name__=='__main__':unittest.main(verbosity=2)

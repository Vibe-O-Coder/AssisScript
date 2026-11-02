"""Real native authority probes, creation faults and isolated Reader pipeline."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
import uuid

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('isolation_worker',ROOT/'tests/test-page-worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)

@unittest.skipUnless(os.name=='nt','Windows AppContainer/LPAC native execution only')
class WindowsIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory(prefix='assis-isolation-');cls.out=Path(cls.folder.name)
        built=worker.builder.build(cls.out,worker.base.COMPILER,testing=True);cls.worker=Path(built['worker']);cls.cc=built['cc']
        cls.lib=ctypes.CDLL(built['provider'])
        for name in ['assw_open','assw_compile_open','assw_send','assw_receive','assw_close','assw_test_failure','assw_test_status','assw_test_exit']:
            getattr(cls.lib,name).restype=ctypes.c_int64
        cls.lib.assw_open.argtypes=[ctypes.c_void_p,ctypes.c_int64,ctypes.c_int64,ctypes.POINTER(ctypes.c_int64)]
        cls.lib.assw_compile_open.argtypes=[ctypes.c_void_p,ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,ctypes.POINTER(ctypes.c_int64)]
        cls.lib.assw_send.argtypes=cls.lib.assw_receive.argtypes=[ctypes.c_int64,ctypes.c_void_p,ctypes.c_int64]
        cls.lib.assw_close.argtypes=cls.lib.assw_test_exit.argtypes=cls.lib.assw_test_failure.argtypes=[ctypes.c_int64]
        cls.oracle=cls.out/'oracle.exe'
        env=dict(os.environ,PATH=str(Path(cls.cc).parent)+os.pathsep+os.environ.get('PATH',''))
        command=[cls.cc,'-O2','-std=c11','-Wall','-Wextra','-Wno-misleading-indentation',str(ROOT/'tests/windows-isolation-oracle.c'),'-o',str(cls.oracle),'-lws2_32','-ladvapi32','-luser32']
        subprocess.run(command,env=env,check=True,capture_output=True)
        cls.kernel=ctypes.WinDLL('kernel32',use_last_error=True);cls.kernel.GetCurrentProcess.restype=ctypes.c_void_p
        cls.kernel.GetProcessHandleCount.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
        print('ISOLATION_CANDIDATE '+json.dumps(dict(mode='reference' if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else 'optimized',
            compiler_sha256=hashlib.sha256(worker.base.COMPILER.read_bytes()).hexdigest(),worker_sha256=hashlib.sha256(cls.worker.read_bytes()).hexdigest(),
            provider_sha256=hashlib.sha256(Path(built['provider']).read_bytes()).hexdigest(),oracle_sha256=hashlib.sha256(cls.oracle.read_bytes()).hexdigest())),flush=True)
    @classmethod
    def tearDownClass(cls):
        import _ctypes
        _ctypes.FreeLibrary(cls.lib._handle);cls.folder.cleanup()
    def setUp(self):self.streams={};self.lib.assw_test_failure(0)
    def start(self,path=None,compiling=False):
        data=str(path or self.worker).encode();token=ctypes.c_int64(99)
        status=self.lib.assw_compile_open(data,len(data),128,3,ctypes.byref(token)) if compiling else self.lib.assw_open(data,len(data),1,ctypes.byref(token))
        self.assertEqual(status,0,hex(self.lib.assw_test_status()));self.assertGreater(token.value,0)
        self.addCleanup(lambda:self.lib.assw_close(token.value));return token.value
    def send(self,t,data):
        at=0;deadline=time.monotonic()+5
        while at<len(data):
            chunk=data[at:at+4096];n=self.lib.assw_send(t,chunk,len(chunk));self.assertGreaterEqual(n,0);at+=n
            self.assertLess(time.monotonic(),deadline)
            if not n:time.sleep(.001)
    def take(self,t,amount=None):
        content=self.streams.setdefault(t,bytearray());deadline=time.monotonic()+8
        while (amount is not None and len(content)<amount) or (amount is None and b'\n' not in content):
            b=ctypes.create_string_buffer(4096);n=self.lib.assw_receive(t,b,4096);self.assertGreaterEqual(n,0,(self.lib.assw_test_exit(t),bytes(content)))
            content.extend(b.raw[:n]);self.assertLess(time.monotonic(),deadline)
            if not n:time.sleep(.001)
        length=amount if amount is not None else content.index(10)+1;result=bytes(content[:length]);del content[:length];return result
    def hello(self,t):
        parts=self.take(t).decode().strip().split();self.assertEqual(parts[:7],['IDENTITY','1','0','0','1','1','1'])
        self.assertTrue(parts[7].startswith('S-1-15-2-'));path=self.take(t).decode().strip();self.assertTrue(path.startswith('PATH '));return parts[7],path[5:]
    def handles(self):
        n=ctypes.c_uint32();self.assertTrue(self.kernel.GetProcessHandleCount(self.kernel.GetCurrentProcess(),ctypes.byref(n)));return n.value
    def resources(self):
        return ({p.name for p in Path(tempfile.gettempdir()).glob('assis-lpac-*')},
                {p.name for p in (Path(os.environ['LOCALAPPDATA'])/'Packages').glob('assis-lpac-*')})
    def test_native_authority_denials_unique_identities_and_readonly_runtime(self):
        import winreg
        key='Software\\AssisScriptIsolationTest-'+uuid.uuid4().hex
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key) as h:winreg.SetValueEx(h,'sentinel',0,winreg.REG_SZ,'test-only')
        self.addCleanup(lambda:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,key))
        class Attributes(ctypes.Structure):_fields_=[('size',ctypes.c_uint32),('descriptor',ctypes.c_void_p),('inherit',ctypes.c_int32)]
        self.kernel.CreateEventW.restype=ctypes.c_void_p
        attrs=Attributes(ctypes.sizeof(Attributes),None,1);handle=self.kernel.CreateEventW(ctypes.byref(attrs),1,0,None);self.assertTrue(handle)
        self.addCleanup(lambda:self.kernel.CloseHandle(ctypes.c_void_p(handle)))
        sentinel=self.out/'private.txt';sentinel.write_bytes(b'private test sentinel');original=sentinel.read_bytes()
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();listener.settimeout(.1);self.addCleanup(listener.close)
        previous=os.environ.get('ASSIS_WORKER_SECRET');os.environ['ASSIS_WORKER_SECRET']='not inherited'
        try:a=self.start(self.oracle);b=self.start(self.oracle)
        finally:
            if previous is None:os.environ.pop('ASSIS_WORKER_SECRET',None)
            else:os.environ['ASSIS_WORKER_SECRET']=previous
        sid_a,path_a=self.hello(a);sid_b,path_b=self.hello(b);self.assertNotEqual(sid_a,sid_b);self.assertNotEqual(path_a,path_b)
        for token,neighbor in [(a,path_b),(b,path_a)]:
            self.send(token,f'{sentinel}\n{neighbor}\n{key}\n{os.getpid()} {handle} {listener.getsockname()[1]}\n'.encode())
            row=self.take(token).decode().strip().split();self.assertEqual(row[0],'RESULT');values=list(map(int,row[1:]));self.assertEqual(len(values),13)
            own_read,own_write,read,write,other,create,registry,inherited,environment,parent,child,network,executable=values
            self.assertEqual(own_read,0)
            for denied in [own_write,read,write,other,create,registry,parent]:self.assertEqual(denied,5)
            # LPAC can deny provider initialization itself (10107 on Win10),
            # instead of allowing socket() and denying connect() with 10013.
            self.assertEqual((inherited,environment),(0,0));self.assertNotEqual(child,0);self.assertIn(network,{10013,10106,10107,10091});self.assertNotEqual(executable,0)
            clipboard=self.take(token).decode().strip().split();self.assertEqual(clipboard[0],'CLIPBOARD');self.assertNotEqual(int(clipboard[1]),0)
            print('NATIVE_DENIALS '+json.dumps(dict(own_read=own_read,own_write=own_write,private_read=read,private_write=write,neighbor_read=other,
                stage_create=create,registry=registry,inherited=inherited,environment=environment,parent=parent,child=child,network=network,dynamic_code=executable,clipboard=int(clipboard[1]))),flush=True)
        self.assertEqual(sentinel.read_bytes(),original)
        with self.assertRaises(TimeoutError):listener.accept()
        self.assertEqual(self.lib.assw_close(a),0);self.assertEqual(self.lib.assw_close(b),0)
    def test_every_creation_fault_rolls_back_without_unrestricted_fallback(self):
        # Warm system DLL/profile services before measuring process handle count.
        t=self.start();self.take(t,144);self.assertEqual(self.lib.assw_close(t),0)
        before=self.resources();handles=self.handles();data=str(self.worker).encode()
        for fault in range(1,7):
            for _ in range(3):
                self.lib.assw_test_failure(fault);token=ctypes.c_int64(99)
                self.assertEqual(self.lib.assw_open(data,len(data),1,ctypes.byref(token)),-4);self.assertEqual(token.value,0)
                self.assertEqual(self.resources(),before);self.assertEqual(self.handles(),handles)
        self.lib.assw_test_failure(0);t=self.start();self.assertEqual(int.from_bytes(self.take(t,144)[128:136],'little'),1)
    def test_repeated_isolated_close_reclaims_profile_files_handles_and_tokens(self):
        t=self.start();self.take(t,144);self.assertEqual(self.lib.assw_close(t),0)
        before=self.resources();handles=self.handles();seen=set()
        for _ in range(64):
            t=self.start();self.assertNotIn(t,seen);seen.add(t);self.take(t,144)
            self.assertEqual(self.lib.assw_close(t),0);self.assertEqual(self.lib.assw_close(t),-2)
        self.assertEqual(self.resources(),before);self.assertEqual(self.handles(),handles)
        print('ISOLATION_CYCLES 64; unchanged profiles/stage directories/handles',flush=True)
    def test_compiler_launch_is_also_isolated_before_source_input(self):
        t=self.start(self.oracle,compiling=True);self.hello(t);self.assertEqual(self.lib.assw_close(t),0)

if __name__=='__main__':unittest.main(verbosity=2)

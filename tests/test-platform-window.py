"""Windows provider boundary tests. Hidden test windows, real User32/GDI resources.

The Python color oracle and C caller do not use AssisScript code generation.
No production test hooks, callback injection into AssisScript, or remote code.
"""
import ctypes as C
from ctypes import wintypes as W
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct
import threading
import time
import unittest

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

base = module('evolution', Path(__file__).with_name('test-evolution.py'))
builder = module('platform_builder', base.ROOT / 'tools/build-platform.py')
I = C.c_int64
P = C.POINTER(I)
ABI = 65536

@unittest.skipUnless(os.name == 'nt', 'Windows x64 provider unsupported on this host')
class PlatformWindow(base.Evolution):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.folder = tempfile.TemporaryDirectory(prefix='assis-platform-')
        cls.output = Path(cls.folder.name)
        cls.library = cls.output / 'assis_platform_v1.dll'
        cls.command = builder.build(cls.library, testing=True)
        cls.production = cls.output / 'production/assis_platform_v1.dll'
        builder.build(cls.production)
        cls.dll = C.CDLL(str(cls.library))
        signatures = {
            'abi_version': (I, []),
            'open': (C.c_int32, [I, C.c_int32, C.c_int32, C.c_void_p, I, P]),
            'poll': (C.c_int32, [I, C.c_int32, P, I]),
            'clear': (C.c_int32, [I, C.c_uint32]),
            'text_utf8': (C.c_int32, [I, C.c_int32, C.c_int32, C.c_void_p, I, C.c_uint32]),
            'present': (C.c_int32, [I]), 'close': (C.c_int32, [I]),
            'test_control': (I, [I, I]),
            'test_pixel': (I, [I, C.c_int32, C.c_int32]),
        }
        for name, (result, arguments) in signatures.items():
            function = getattr(cls.dll, 'assisp_' + name)
            function.restype, function.argtypes = result, arguments
        cls.instance = 0
        cls.user = C.WinDLL('user32', use_last_error=True)
        cls.user.SendMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        cls.user.SendMessageW.restype = W.LPARAM
        cls.user.GetGuiResources.argtypes = [W.HANDLE, W.DWORD]
        cls.user.GetGuiResources.restype = W.DWORD
        cls.user.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
        cls.user.SetWindowPos.restype = W.BOOL
        cls.kernel = C.WinDLL('kernel32', use_last_error=True)
        cls.kernel.GetCurrentProcess.restype = W.HANDLE
        cls.kernel.GetProcessHandleCount.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]
        cls.kernel.GetProcessHandleCount.restype = W.BOOL
        cls.kernel.FreeLibrary.argtypes = [W.HMODULE]
        cls.kernel.FreeLibrary.restype = W.BOOL
        cls.assertion = cls.dll.assisp_abi_version()
        cls.metrics = {}

    @classmethod
    def tearDownClass(cls):
        evidence = os.environ.get('ASSIS_PLATFORM_EVIDENCE')
        if evidence:
            environment = dict(os.environ, PATH=str(Path(cls.command[0]).parent)+os.pathsep+os.environ.get('PATH',''))
            cc = subprocess.run([cls.command[0],'--version'],env=environment,capture_output=True,text=True,check=True)
            imports = subprocess.run([str(Path(cls.command[0]).parent/'objdump.exe'),'-p',str(cls.production)],
                                     env=environment,capture_output=True,text=True,check=True)
            record = dict(metrics=cls.metrics, toolchain=cc.stdout.splitlines()[0],
                provider_production_sha256=hashlib.sha256(cls.production.read_bytes()).hexdigest(),
                provider_testing_sha256=hashlib.sha256(cls.library.read_bytes()).hexdigest(),
                production_bytes=cls.production.stat().st_size,
                production_imports=[line.split('DLL Name:',1)[1].strip() for line in imports.stdout.splitlines() if 'DLL Name:' in line],
                build_flags=cls.command[1:-5], testing_windows='hidden; real User32/GDI resources',
                visual_inspection='not-run; separate Computer Use attempt timed out waiting for application approval')
            Path(evidence).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
        cls.kernel.FreeLibrary.argtypes = [W.HMODULE]
        cls.kernel.FreeLibrary.restype = W.BOOL
        cls.kernel.FreeLibrary(cls.dll._handle)
        cls.folder.cleanup()

    def setUp(self):
        super().setUp()
        self.handles = []
        self.saved_path = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.temp) + os.pathsep + self.saved_path
        self.addCleanup(os.environ.__setitem__, 'PATH', self.saved_path)
        self.dll.assisp_test_control(0, -1)
        self.dll.assisp_test_control(2, 0)
        self.dll.assisp_test_control(7, 0)

    def tearDown(self):
        self.dll.assisp_test_control(0, -1)
        self.dll.assisp_test_control(7, 0)
        for handle in self.handles:
            self.dll.assisp_close(handle)
        self.assertEqual(self.dll.assisp_test_control(3, 0), 0)

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def opened(self, width=320, height=160):
        type(self).instance += 1
        token = I(0)
        code = self.dll.assisp_open(self.instance, width, height, b'test', 4, C.byref(token))
        self.assertEqual(code, 0)
        self.handles.append(token.value)
        return token.value

    def poll(self, token, timeout=0):
        words = (I * 10)(*([999] * 10))
        code = self.dll.assisp_poll(token, timeout, words, 8)
        self.assertEqual(list(words)[8:], [999, 999])
        if code:
            self.assertEqual(list(words)[:8], [0] * 8)
        return code, list(words)[:8]

    def drain(self, token):
        events = []
        while True:
            code, words = self.poll(token)
            if code:
                self.assertEqual(code, 1)
                return events
            events.append(words)

    def hwnd(self, token):
        return self.dll.assisp_test_control(4, token)

    def test_arguments_buffers_utf8_and_unavailable_provider(self):
        self.assertEqual(self.assertion, ABI)
        token = I(123)
        for width, height, title, size in [(0, 1, b'a', 1), (1, 16385, b'a', 1),
                (1, 1, None, 1), (1, 1, b'a', -1), (1, 1, b'a', 4097),
                (1, 1, b'a\0b', 3), (1, 1, b'\xc0\x80', 2), (1, 1, b'\xed\xa0\x80', 3),
                (1, 1, b'\xf4\x90\x80\x80', 4), (1, 1, b'\xe2\x82', 2)]:
            self.assertEqual(self.dll.assisp_open(100000, width, height, title, size, C.byref(token)), -1)
            self.assertEqual(token.value, 0)
        self.assertEqual(self.dll.assisp_open(1, 1, 1, None, 0, None), -1)
        self.dll.assisp_test_control(2, 1)
        self.assertEqual(self.dll.assisp_open(100000, 1, 1, b'a', 1, C.byref(token)), -3)
        self.assertEqual(token.value, 0)
        self.dll.assisp_test_control(2, 0)
        live = self.opened()
        self.assertEqual(self.poll(live, -1)[0], -1)
        self.assertEqual(self.poll(live, 51)[0], -1)
        small = (I * 7)(*([999] * 7))
        self.assertEqual(self.dll.assisp_poll(live, 0, small, 7), -1)
        self.assertEqual(list(small), [999] * 7)
        self.assertEqual(self.dll.assisp_poll(live, 0, None, 8), -1)

    def test_source_over_and_length_bearing_text_with_independent_color_model(self):
        live = self.opened()
        rgb = [0, 0, 0]
        for rgba in [0x102030ff, 0xd0a07080, 0xffffff00, 0x88776601, 0x000000fe]:
            alpha = rgba & 255
            rgb = [(source * alpha + old * (255-alpha) + 127)//255
                   for source, old in zip([(rgba >> n) & 255 for n in (24, 16, 8)], rgb)]
            self.assertEqual(self.dll.assisp_clear(live, rgba), 0)
            self.assertEqual(self.dll.assisp_test_pixel(live, 0, 0), 0xff000000 | rgb[0] << 16 | rgb[1] << 8 | rgb[2])
        self.assertEqual(self.dll.assisp_clear(live, 0x000000ff), 0)
        text = 'A\0B ç ação'.encode()
        self.assertEqual(self.dll.assisp_text_utf8(live, 0, 0, text, len(text), 0xffffffff), 0)
        # Non-black glyph pixels beyond the first character prove NUL did not terminate the buffer.
        self.assertTrue(any(self.dll.assisp_test_pixel(live, x, y) != 0xff000000
                            for y in range(30) for x in range(24, 90)))
        before = self.dll.assisp_test_pixel(live, 0, 0)
        for data, size in [(None, 1), (b'a', -1), (b'a', 1048577), (b'\x80', 1)]:
            self.assertEqual(self.dll.assisp_text_utf8(live, 0, 0, data, size, 0xffffffff), -1)
        self.assertEqual(self.dll.assisp_test_pixel(live, 0, 0), before)
        self.assertEqual(self.dll.assisp_text_utf8(live, -2147483648, 2147483647, None, 0, 0), 0)
        self.assertEqual(self.dll.assisp_present(live), 0)

    def test_ordered_events_resize_focus_keys_pointer_scale_and_close(self):
        live = self.opened()
        self.drain(live)
        hwnd = self.hwnd(live)
        self.assertTrue(self.user.SetWindowPos(hwnd, None, 0, 0, 500, 260, 0x0016))
        resize = self.drain(live)
        self.assertTrue(any(e[1] == 2 and e[5] > 320 for e in resize))
        for message, wp, lp in [(0x100, 32, 0), (0x101, 32, 0), (0x200, 0, (9 << 16) | 7),
                                (0x7, 0, 0), (0x8, 0, 0), (0x2e0, 192 | (192 << 16), 0), (0x10, 0, 0)]:
            self.user.SendMessageW(hwnd, message, wp, lp)
        events = self.drain(live)
        self.assertEqual([(e[1], e[5], e[6]) for e in events],
                         [(3,32,1), (3,32,0), (4,7,9), (5,1,0), (5,0,0), (6,2000,0), (1,0,0)])
        self.assertTrue(all(e[0] == ABI and e[2] == live and e[3] == self.instance and e[4] > 0 for e in events))
        self.assertEqual([e[7] for e in events], sorted({e[7] for e in events}))

    def test_queue_coalescing_overflow_and_neighbor_isolation(self):
        first, neighbor = self.opened(), self.opened()
        self.drain(first); self.drain(neighbor)
        for i in range(1000):
            self.user.SendMessageW(self.hwnd(first), 0x200, 0, i)
        events = self.drain(first)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][5], 999)
        for _ in range(257):
            self.user.SendMessageW(self.hwnd(first), 0x100, 9, 0)
        self.assertEqual(self.poll(first)[0], -6)
        self.assertEqual(self.dll.assisp_clear(first, 0), -6)
        self.assertEqual(self.dll.assisp_clear(neighbor, 0xffffffff), 0)
        self.assertEqual(self.poll(neighbor)[0], 1)

    def test_tokens_generation_instance_revocation_and_exhaustion(self):
        first = self.opened()
        for forged in [0, -1, first ^ (1 << 56), first ^ (1 << 8), 0x51000000000000ff]:
            self.assertEqual(self.poll(forged)[0], -2)
            self.assertEqual(self.dll.assisp_close(forged), -2)
        instance = self.instance
        self.assertEqual(self.dll.assisp_close(first), 0)
        token = I(123)
        self.assertEqual(self.dll.assisp_open(instance, 1, 1, None, 0, C.byref(token)), -1)
        second = self.opened()
        self.assertNotEqual(first, second)
        self.assertEqual(self.dll.assisp_present(first), -2)
        self.drain(second)
        self.dll.assisp_test_control(5, second)
        self.user.SendMessageW(self.hwnd(second), 0x100, 13, 0)
        self.assertEqual(self.poll(second)[0], -6)
        self.dll.assisp_test_control(6, second)
        self.assertEqual(self.dll.assisp_close(second), 0)
        third = self.opened()
        self.assertNotEqual(third & 255, second & 255)

    def test_wrong_thread_refuses_all_operations(self):
        live = self.opened()
        results = []
        def worker():
            out = I(999); words = (I * 8)(*([999]*8))
            results.extend([self.dll.assisp_abi_version(), self.dll.assisp_open(100000,1,1,None,0,C.byref(out)),
                self.dll.assisp_poll(live,0,words,8), self.dll.assisp_clear(live,0),
                self.dll.assisp_text_utf8(live,0,0,None,0,0), self.dll.assisp_present(live), self.dll.assisp_close(live)])
            results.append(out.value); results.extend(words)
        thread = threading.Thread(target=worker); thread.start(); thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results, [-5]*7 + [0]*9)
        self.assertEqual(self.dll.assisp_present(live), 0)

    def test_injected_oom_every_open_boundary_text_resize_and_neighbor(self):
        neighbor = self.opened(); baseline = self.dll.assisp_test_control(3, 0)
        seen = 0
        for boundary in range(16):
            self.dll.assisp_test_control(0, boundary)
            type(self).instance += 1; token = I(999)
            code = self.dll.assisp_open(self.instance,320,160,b'oom',3,C.byref(token))
            if code == 0:
                self.handles.append(token.value); self.dll.assisp_close(token.value); break
            self.assertEqual((code, token.value), (-4, 0)); seen += 1
            self.assertEqual(self.dll.assisp_test_control(3, 0), baseline)
            self.assertEqual(self.dll.assisp_clear(neighbor, 0x123456ff), 0)
        self.assertEqual(seen, 6)
        self.metrics['open_oom_boundaries'] = seen
        self.dll.assisp_test_control(0, 0)
        self.assertEqual(self.dll.assisp_text_utf8(neighbor,0,0,b'hello',5,0xffffffff), -4)
        self.assertEqual(self.dll.assisp_test_pixel(neighbor,0,0), 0xff123456)
        self.drain(neighbor)
        self.user.SendMessageW(self.hwnd(neighbor), 5, 0, (400 << 16) | 400)
        self.assertEqual(self.poll(neighbor)[0], -4)
        self.assertEqual(self.dll.assisp_test_control(3, 0), baseline)
        self.assertEqual(self.dll.assisp_test_pixel(neighbor,0,0), 0xff123456)

    def test_window_and_surface_quotas_are_recoverable(self):
        type(self).instance += 1; out = I(999)
        self.assertEqual(self.dll.assisp_open(self.instance,16384,16384,None,0,C.byref(out)), -4)
        self.assertEqual(out.value, 0)
        # A retired generation from another test may reduce available slots by one.
        tokens = []
        while len(tokens) < 32:
            type(self).instance += 1
            code = self.dll.assisp_open(self.instance,320,160,None,0,C.byref(out))
            if code == -4: break
            self.assertEqual(code, 0); tokens.append(out.value); self.handles.append(out.value)
        self.assertGreaterEqual(len(tokens), 31)
        self.assertEqual(self.dll.assisp_open(self.instance+1,320,160,None,0,C.byref(out)), -4)
        self.assertEqual(out.value, 0)
        for token in tokens: self.assertEqual(self.dll.assisp_close(token), 0)
        live = self.opened(); self.assertEqual(self.dll.assisp_clear(live, 0), 0)

    def test_wait_is_bounded_and_thousand_cycles_release_native_resources(self):
        live = self.opened(); self.drain(live)
        started = time.monotonic(); self.assertEqual(self.poll(live, 25)[0], 1)
        elapsed = time.monotonic()-started
        self.assertGreaterEqual(elapsed, .015); self.assertLess(elapsed, .5)
        self.dll.assisp_close(live)
        process = self.kernel.GetCurrentProcess()
        def counts():
            handles = W.DWORD()
            self.assertTrue(self.kernel.GetProcessHandleCount(process, C.byref(handles)))
            return (handles.value, self.user.GetGuiResources(process, 0), self.user.GetGuiResources(process, 1))
        before = counts()
        started_cycles = time.monotonic()
        for _ in range(1000):
            token = self.opened(160,80)
            self.assertEqual(self.dll.assisp_close(token), 0)
        after = counts()
        self.assertEqual(after, before)
        self.metrics['resource_cycles'] = dict(count=1000, before=list(before), after=list(after),
            count_order=['process_handles','GDI','USER'], seconds=round(time.monotonic()-started_cycles,3))
        self.metrics['poll_25ms_elapsed_ms'] = round(elapsed*1000,3)

    def test_independent_c_caller_matches_assisscript_both_backends(self):
        cc = self.command[0]
        oracle = self.temp / 'oracle.exe'
        environment = dict(os.environ, PATH=str(Path(cc).parent)+os.pathsep+os.environ.get('PATH',''))
        result = subprocess.run([cc,'-O2','-std=c11','-Wall','-Wextra','-Werror',
            str(base.ROOT/'tests/platform-oracle.c'),'-o',str(oracle)], env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        result = subprocess.run([str(oracle),str(self.library)], capture_output=True, text=True, timeout=20)
        self.assertEqual((result.returncode,result.stderr),(0,''))
        expected = '65536\n0 1\n0 0 0\n1\n0\n-2 -2\n'
        self.assertEqual(result.stdout,expected)
        self.metrics['c_oracle_sha256'] = hashlib.sha256(oracle.read_bytes()).hexdigest()
        path = self.library.as_posix()
        def ext(symbol, parameters, returns='i32'):
            return f'extern("{path}","{path}","assisp_{symbol}") fn p_{symbol}({parameters}):{returns};'
        program = ext('abi_version','','int') + ext('open','instance:int,w:i32,h:i32,borrow data:*byte,n:int,borrow mut out:*int')
        program += ext('poll','token:int,timeout:i32,borrow mut data:*int,n:int') + ext('clear','token:int,color:u32')
        program += ext('text_utf8','token:int,x:i32,y:i32,borrow data:*byte,n:int,color:u32')
        program += ext('present','token:int') + ext('close','token:int')
        program += ('safe fn main():int{own out:*int=alloc<int>(10);own title:*byte=alloc<byte>(1);'
            'own data:*byte=alloc<byte>(6);data[0]=byte(65);data[2]=byte(66);data[3]=byte(32);data[4]=byte(195);data[5]=byte(167);'
            'unsafe{print(p_abi_version());val opened:i32=p_open(1,i32(320),i32(160),title,0,out);val token:int=out[0];'
            'print(opened,int(token!=0));print(p_clear(token,u32(0x244866ff)),p_text_utf8(token,i32(4),i32(4),data,6,u32(0xf0f0f080)),p_present(token));'
            'let status:i32=p_poll(token,i32(0),out,8);while(status==i32(0)){assert(out[0]==65536&&out[2]==token&&out[3]==1&&out[4]>0);status=p_poll(token,i32(0),out,8);}'
            'print(status);print(p_close(token));print(p_close(token),p_clear(token,u32(0)));}return 0;}')
        self.accepted(program, expected)

    def test_owned_wrapper_drop_failures_and_all_output_formats(self):
        shutil.copy2(self.library, self.temp / self.library.name)
        program = ('import "std/window.assis";extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(operation:int,value:int):int;'
            'safe fn main():int{'
            'own view:window::Window=new window::Window(1,320,160,"Ação ç");assert(view.opened());'
            'assert(view.clear(u32(0x182334ff))==0);assert(view.draw_text(4,4,"ação A\\0B",u32(0xffffffff))==0);assert(view.present()==0);'
            'val event:window::Event=view.poll(0);assert(event.status==0||event.status==1);'
            'assert(view.poll(2147483648).status== -1);assert(view.draw_text(2147483648,0,"",u32(0))== -1);'
            'assert(view.close()==0);assert(!view.opened());assert(view.close()==0);assert(view.poll(0).status== -2);'
            'own bad:window::Window=new window::Window(2,0,160,"bad");assert(!bad.opened()&&bad.error()== -1);'
            '{own held:window::Window=new window::Window(3,320,160,"drop");assert(held.opened());}'
            'unsafe{assert(control(3,0)==0);}print(42);return 0;}')
        self.accepted(program, '42\n')
        source = self.source(program)
        ir = self.invoke('ir', source); self.assertEqual(ir.returncode, 0, ir.stderr)
        self.assertEqual(json.loads(ir.stdout)['astFallbacks'], 0)
        hashes = {}
        for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
            for flags in [[],['--no-opt']]:
                output = self.temp/(target+'.exe')
                result = self.invoke('build',source,'--target',target,'-o',output,*flags)
                self.assertEqual(result.returncode,0,(target,flags,result.stderr))
                data = output.read_bytes()
                if target.startswith('linux'):
                    self.assertEqual(data[:6],b'\x7fELF\x02\x01')
                    self.assertEqual(struct.unpack_from('<H',data,18)[0],183 if target.endswith('arm64') else 62)
                elif target.startswith('macos'):
                    self.assertEqual(struct.unpack_from('<II',data),(0xfeedfacf,0x0100000c if target.endswith('arm64') else 0x01000007))
                else:
                    offset = struct.unpack_from('<I',data,0x3c)[0]
                    self.assertEqual(data[:2],b'MZ');self.assertEqual(data[offset:offset+4],b'PE\0\0')
                    self.assertEqual(struct.unpack_from('<H',data,offset+4)[0],0x8664)
                hashes[target+(':reference' if flags else ':optimized')] = hashlib.sha256(data).hexdigest()
        self.metrics['generated_formats'] = hashes
        self.rejected('import "std/window.assis";safe fn main():int{own view:window::Window=new window::Window(1,1,1,"");view.token=1;return 0;}', 'privado')

    def test_exact_input_limits_and_copied_title(self):
        type(self).instance += 1
        out = I(0); title = C.create_string_buffer('Ação'.encode())
        self.assertEqual(self.dll.assisp_open(self.instance,320,160,title,len(title.raw)-1,C.byref(out)),0)
        self.handles.append(out.value)
        title.value = b'gone'
        self.user.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
        buffer = C.create_unicode_buffer(100)
        self.user.GetWindowTextW(self.hwnd(out.value), buffer, 100)
        self.assertEqual(buffer.value, 'Ação')
        maximum = b'a' * 1048576
        self.assertEqual(self.dll.assisp_text_utf8(out.value,0,0,maximum,len(maximum),0xffffffff),0)
        self.assertEqual(self.dll.assisp_text_utf8(out.value,0,0,b'\0',1,0xffffffff),0)
        self.dll.assisp_close(out.value)
        type(self).instance += 1
        self.assertEqual(self.dll.assisp_open(self.instance,320,160,b'a'*4096,4096,C.byref(out)),0)
        self.handles.append(out.value)

    def test_missing_dll_is_a_loader_failure_before_main(self):
        source = self.source('import "std/window.assis";safe fn main():int{print(window::available());return 0;}')
        binary = self.temp/'absent.exe'
        result = self.invoke('build',source,'-o',binary)
        self.assertEqual(result.returncode,0,result.stderr)
        environment = dict(os.environ, PATH=self.saved_path)
        result = subprocess.run([str(binary)],env=environment,capture_output=True,timeout=10)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0xc0000135,b'',b''))

    def test_wrapper_negotiates_abi_before_open_and_reports_optional_unavailable(self):
        cc = self.command[0]
        environment = dict(os.environ, PATH=str(Path(cc).parent)+os.pathsep+os.environ.get('PATH',''))
        for version, calls in [(65537,0),(65536,1)]:
            result = subprocess.run([cc,'-shared','-O2','-std=c11','-Wall','-Wextra','-Werror',f'-DFIXTURE_ABI={version}',
                str(base.ROOT/'tests/platform-version-fixture.c'),'-o',str(self.temp/'assis_platform_v1.dll')],
                env=environment,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            program = ('import "std/window.assis";extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_calls") fn calls():int;'
                'safe fn main():int{own view:window::Window=new window::Window(1,320,160,"fixture");'
                'assert(!view.opened()&&view.error()== -3);unsafe{assert(calls()=='+str(calls)+');}return 0;}')
            self.accepted(program)

    def test_production_exports_exclude_diagnostics(self):
        production = C.CDLL(str(self.production))
        try:
            self.assertEqual(production.assisp_abi_version(), ABI)
            for name in ['assisp_test_control','assisp_test_pixel']:
                with self.assertRaises(AttributeError): getattr(production,name)
        finally:
            self.kernel.FreeLibrary(production._handle)

    def test_failed_native_close_preserves_resources_for_retry(self):
        live = self.opened()
        pixels = self.dll.assisp_test_control(3, 0)
        self.dll.assisp_test_control(7, 1)
        self.assertEqual(self.dll.assisp_close(live), -6)
        self.assertEqual(self.dll.assisp_test_control(3, 0), pixels)
        self.assertEqual(self.dll.assisp_present(live), -6)
        self.dll.assisp_test_control(7, 0)
        self.assertEqual(self.dll.assisp_close(live), 0)
        self.assertEqual(self.dll.assisp_test_control(3, 0), 0)

if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'): delattr(base.Evolution, name)
    unittest.main(verbosity=2)

"""Owned HTDL presentation, independent text wrapping and input/lifecycle checks."""
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import struct
import tempfile
import textwrap
import time
import unittest

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

parser = module('parser_tests', Path(__file__).with_name('test-htdl-parser.py'))
base = parser.base
PREFIX = '''import "std/viewer.assis";
safe fn cells(borrow s:slice<byte>):int{
 let n:int=0;for(let i:int=0;i<len(s);i++){if(s[i]<128 || s[i]>=192){n++;}}return n*8;
}
safe fn fail(borrow s:slice<byte>):int{return -4;}
safe fn event(kind:int,a:int,b:int,request:int):window::Event{return new window::Event(0,kind,7,1,a,b,request);}
'''

def setup(body, width=240, height=160, instance=1):
    return ('own store:documents::Store=try_new documents::Store(32000000,250000,1000);'
            f'assert(htdl::load(store,{instance},' + parser.literal(parser.document(body)) + ').code==0);'
            f'own v:viewer::View=try_new viewer::View(store.active_document(),7,{width},{height},16,cells);'
            'assert(v!=null && v.is_open());')

class HtdlViewer(base.Evolution):
    fault_program = parser.preparation.BufferPreallocation.fault_program

    @classmethod
    def setUpClass(cls):
        cls.provider_temp = tempfile.TemporaryDirectory(prefix='assis-viewer-provider-')
        if os.name == 'nt':
            builder = module('viewer_builder', base.ROOT / 'tools/build-platform.py')
            cls.provider = Path(cls.provider_temp.name) / 'assis_platform_v1.dll'
            builder.build(cls.provider, testing=True)

    @classmethod
    def tearDownClass(cls):
        cls.provider_temp.cleanup()

    def setUp(self):
        super().setUp()
        if os.name == 'nt':
            shutil.copyfile(self.provider, self.temp / 'assis_platform_v1.dll')
            previous = os.environ.get('PATH', '')
            os.environ['PATH'] = str(self.temp) + os.pathsep + previous
            self.addCleanup(os.environ.__setitem__, 'PATH', previous)

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check','build','run','ir'): args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def execute(self, body, expected='', prefix=PREFIX):
        self.accepted(prefix + 'safe fn main():int{' + body + 'return 0;}', expected)

    def test_wrapping_against_python_textwrap_for_atomic_characters(self):
        rng = random.Random(20261101)
        # textwrap counts Python code points; use one-code-point clusters here.
        # Decomposed/ZWJ clusters have explicit byte-boundary tests in graphemes.
        words = ['ação', 'coração', 'café', '😀', 'abcdefghijklmnopqrstuvwx', 'fim']
        content = '  ' + ' \n '.join(rng.choice(words) for _ in range(60)) + '  '
        for width in (96, 120, 240, 780):
            # Python 3.10 and 3.14 differ in trailing spaces after splitting a
            # large word. This profile explicitly trims row-end ASCII spaces.
            expected = [line.rstrip(' ') for line in textwrap.wrap(' '.join(content.split()), width=(width-72)//8,
                break_long_words=True, break_on_hyphens=False)]
            self.execute(setup('<div type=paragraph>'+content+'</div>', width=width) +
                'for(let i:int=0;i<v.line_count();i++){assert(v.line(i).width<='+str(width-72)+');'
                'print(v.line_text(i));}', ''.join(line+'\n' for line in expected))

    def test_hidden_subtrees_inline_collapse_and_label_fallback(self):
        body = ('<div type=container hidden=true><div type=button>Secret</div></div>'
                '<div type=paragraph> A <div type=text> B </div> C </div>'
                '<div type=button a11y-label=Label></div><div type=button disabled=true>Disabled</div>')
        self.execute(setup(body) + 'assert(v.line_count()==3);'
            'for(let i:int=0;i<v.line_count();i++){print(v.line_text(i));}'
            'v.dispatch(1,event(3,9,1,1));assert(viewer::same(v.focus_node(),v.line(1).node));'
            'v.dispatch(1,event(3,9,1,2));assert(viewer::same(v.focus_node(),v.line(1).node));',
            'A B C\nLabel\nDisabled\n')

    def test_focus_reverse_disabled_and_enter_space_repeat(self):
        body = '<div type=button>A</div><div type=button disabled=true>B</div><div type=button>C</div>'
        self.execute(setup(body) +
            'assert(doctree::absent(v.focus_node()));v.dispatch(1,event(3,9,1,1));'
            'assert(viewer::same(v.focus_node(),v.line(0).node));'
            'assert(v.dispatch(1,event(3,13,1,2)).kind==2);'
            'assert(v.dispatch(1,event(3,13,1,3)).kind==0);v.dispatch(1,event(3,13,0,4));'
            'assert(v.dispatch(1,event(3,32,1,5)).kind==1);'
            'assert(v.dispatch(1,event(3,32,1,6)).kind==1);'
            'assert(v.dispatch(1,event(3,32,0,7)).kind==2);'
            'assert(v.dispatch(1,event(3,32,0,8)).kind!=2);'
            'v.dispatch(1,event(3,16,1,9));v.dispatch(1,event(3,9,1,10));'
            'assert(viewer::same(v.focus_node(),v.line(2).node));'
            'v.dispatch(1,event(3,16,0,11));v.dispatch(1,event(3,9,1,12));'
            'assert(viewer::same(v.focus_node(),v.line(0).node));')

    def test_pointer_requires_matching_press_release_and_cancels_keyboard(self):
        self.execute(setup('<div type=button>A</div><div type=button>B</div>') +
            'assert(v.dispatch(1,event(8,30,25,1)).kind!=2);'
            'v.dispatch(1,event(7,30,25,2));assert(v.dispatch(1,event(8,30,65,3)).kind!=2);'
            'v.dispatch(1,event(7,30,25,4));assert(v.dispatch(1,event(8,30,25,5)).kind==2);'
            'v.dispatch(1,event(3,32,1,6));v.dispatch(1,event(7,30,65,7));'
            'assert(v.dispatch(1,event(3,32,0,8)).kind!=2);'
            'v.dispatch(1,event(10,0,0,9));assert(v.dispatch(1,event(8,30,65,10)).kind!=2);'
            'v.dispatch(1,event(3,32,1,11));v.dispatch(1,event(5,0,0,12));'
            'assert(v.dispatch(1,event(3,32,0,13)).kind!=2);')

    def test_scroll_clamping_and_focus_reveals_long_document(self):
        self.execute(setup('<div type=paragraph>'+'words '*100+'</div><div type=button>End</div>') +
            'assert(v.max_scroll()>0);v.scroll_to(9223372036854775807);assert(v.scroll()==v.max_scroll());'
            'v.scroll_to(-9223372036854775808);assert(v.scroll()==0);'
            'v.dispatch(1,event(9,-120,0,1));assert(v.scroll()>0);'
            'v.dispatch(1,event(3,36,1,2));assert(v.scroll()==0);'
            'v.dispatch(1,event(3,9,1,3));assert(v.scroll()>0);'
            'v.dispatch(1,event(3,35,1,4));assert(v.scroll()==v.max_scroll());')

    def test_stale_document_window_sequence_and_close(self):
        self.execute(setup('<div type=button>A</div>') +
            'assert(v.dispatch(2,event(3,9,1,1)).kind==0);'
            'assert(v.dispatch(1,new window::Event(0,3,8,1,9,1,1)).kind==0);'
            'assert(doctree::absent(v.focus_node()));v.dispatch(1,event(3,9,1,1));'
            'assert(v.dispatch(1,event(3,13,1,1)).kind==0);'
            'assert(v.dispatch(1,event(1,0,0,2)).kind==3);assert(!v.is_open());'
            'assert(v.dispatch(1,event(3,13,1,3)).kind==0);v.close();')

    def test_resize_snapshot_is_owned_and_preserves_focus_scroll(self):
        self.execute(setup('<div type=paragraph>'+'text '*100+'</div><div type=button>End</div>') +
            'v.dispatch(1,event(3,9,1,1));'
            'own resized:viewer::View=try_new viewer::View(store.active_document(),7,300,200,16,cells);'
            'assert(resized!=null && resized.is_open());resized.restore(v);'
            'assert(viewer::same(v.focus_node(),resized.focus_node()));'
            'assert(resized.dispatch(1,event(3,13,1,1)).kind==0);'
            'store.close();assert(v.is_open() && resized.is_open());'
            'assert(v.line_text(v.line_count()-1)[0]==69);')

    def test_bad_geometry_metric_failure_and_workspace_limits(self):
        self.execute(setup('<div type=paragraph>abc</div>') +
            'for(let i:int=0;i<4;i++){'
            'own bad:viewer::View=try_new viewer::View(store.active_document(),7,95,160,16,cells);assert(!bad.is_open());}'
            'own bad:viewer::View=try_new viewer::View(store.active_document(),7,240,160,16,fail);'
            'assert(!bad.is_open() && v.is_open());')
        self.execute(setup('<div type=paragraph>'+'a'*5000+'</div>',width=16384) +
            'assert(v.line_count()>1);')

    def test_os_refusal_preserves_existing_snapshot_and_neighbor(self):
        warm, drain, cleanup = parser.preparation.exhaustion()
        source = PREFIX + 'safe fn main():int{' + setup('<div type=button>Keep</div>')
        source += ('val windows:bool=window::available();'
            'own w:window::Window=try_new window::Window(7,240,160,"oom");assert(w!=null);'
            'if(windows){assert(w.opened());}')
        source += ('unsafe{'+warm+drain+
            'own failed:viewer::View=try_new viewer::View(store.active_document(),7,240,160,16,cells);'
            'assert(failed==null || !failed.is_open());assert(v.is_open() && v.line_count()==1);'
            'own failed_window:window::Window=try_new window::Window(8,240,160,"oom");'
            'assert(failed_window==null || !failed_window.opened());'
            'assert(viewer::measure(utf8("x"))== -4);'
            'if(windows){assert(w.draw_text(0,0,utf8("x"),u32(0xffffffff))== -4);'
            'assert(w.clear(u32(0xffffffff))==0 && w.present()==0 && w.close()==0);}'
            'assert(v.line_text(0)[0]==75);v.dispatch(1,event(3,9,1,1));'
            'assert(v.dispatch(1,event(3,13,1,2)).kind==2);'+cleanup+'}return 0;}')
        self.fault_program(source, '')

    def test_viewer_five_output_formats_and_native_execution(self):
        source=self.source(PREFIX+'safe fn main():int{'+setup('<div type=button>One</div>')+
            'assert(v.line_count()==1);return 0;}')
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                binary=self.temp/(mode+'-'+target+'.exe')
                result=self.invoke('build',source,'--target',target,'--debug','-o',binary,*flags)
                self.assertEqual(result.returncode,0,result.stderr)
                data=binary.read_bytes()
                if target.startswith('linux'):
                    self.assertEqual(data[:6],b'\x7fELF\x02\x01')
                    self.assertEqual(struct.unpack_from('<H',data,18)[0],183 if target.endswith('arm64') else 62)
                elif target.startswith('macos'):
                    self.assertEqual(struct.unpack_from('<II',data),
                        (0xfeedfacf,0x0100000c if target.endswith('arm64') else 0x01000007))
                else:
                    self.assertEqual(data[:2],b'MZ');self.assertEqual(struct.unpack_from('<H',data,struct.unpack_from('<I',data,60)[0]+4)[0],0x8664)
                if target==('windows-x64' if os.name=='nt' else 'linux-x64'):
                    result=subprocess.run([binary],capture_output=True,timeout=15)
                    self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    @unittest.skipUnless(os.name == 'nt', 'native Windows painting unsupported')
    def test_native_paint_measure_close_and_pixels(self):
        prefix = PREFIX + '''
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(a:int,b:int):int;
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_pixel") fn pixel(t:int,x:i32,y:i32):int;
'''
        self.execute(setup('<div type=button>Native ação</div>') +
            'assert(viewer::available());val extent:int=viewer::measure(utf8("ação"));assert(extent>0);'
            'own w:window::Window=try_new window::Window(7,240,160,"viewer-test");assert(w!=null && w.opened());'
            'assert(viewer::paint(v,w));v.dispatch(1,event(3,9,1,1));assert(viewer::paint(v,w));'
            'assert(w.close()==0 && w.close()==0);unsafe{assert(control(3,0)==0);}v.close();', prefix=prefix)

    @unittest.skipUnless(os.name == 'nt', 'native Windows application unsupported')
    def test_real_application_native_loop_file_errors_resize_and_input(self):
        import ctypes as C
        from ctypes import wintypes as W
        user=C.WinDLL('user32');kernel=C.WinDLL('kernel32')
        callback_type=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
        user.EnumWindows.argtypes=[callback_type,W.LPARAM]
        user.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
        user.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
        user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
        user.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
        entry=self.temp/'ação 日本.htdl'
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=self.temp/(mode+'.exe')
            built=self.invoke('build',base.ROOT/'exemplos/44_htdl_viewer.assis','--debug','-o',binary,*flags)
            self.assertEqual(built.returncode,0,built.stderr)
            for source,code in [(b'invalid',3),(b'a'*1048577,3),(b'\x80',3)]:
                entry.write_bytes(source)
                result=subprocess.run([binary,entry],capture_output=True,timeout=15)
                self.assertEqual(result.returncode,code,(result.stdout,result.stderr))
            result=subprocess.run([binary,self.temp/'missing.htdl'],capture_output=True,timeout=10)
            self.assertEqual(result.returncode,2)
            entry.write_text(parser.document('<div type=button>A</div><div type=button disabled=true>B</div>'),encoding='utf-8')
            output=self.temp/(mode+'.stdout')
            with output.open('wb') as stream:
                process=subprocess.Popen([binary,entry],stdout=stream,stderr=subprocess.PIPE)
                try:
                    deadline=time.monotonic()+10;target=[]
                    while time.monotonic()<deadline:
                        target.clear()
                        @callback_type
                        def visit(hwnd,unused):
                            pid=W.DWORD();user.GetWindowThreadProcessId(hwnd,C.byref(pid))
                            name=C.create_unicode_buffer(128);user.GetClassNameW(hwnd,name,128)
                            if pid.value==process.pid and name.value=='AssisPlatformV1':target.append(hwnd)
                            return True
                        user.EnumWindows(visit,0)
                        if len(target)==1 and b'VIEW' in output.read_bytes():break
                        time.sleep(.02)
                    self.assertEqual(len(target),1)
                    hwnd=target[0]
                    def post(message,a=0,b=0):self.assertTrue(user.PostMessageW(hwnd,message,a,b))
                    def key(code,down):post(0x100 if down else 0x101,code)
                    key(9,True);key(9,False)
                    key(13,True);key(13,True);key(13,False)
                    key(32,True);key(32,True);key(32,False)
                    post(0x201,1,40|(25<<16));post(0x202,0,40|(25<<16))
                    deadline=time.monotonic()+10
                    while output.read_bytes().count(b'ACTIVATE')<3 and time.monotonic()<deadline:time.sleep(.02)
                    self.assertEqual(output.read_bytes().count(b'ACTIVATE'),3,output.read_bytes())
                    self.assertTrue(user.SetWindowPos(hwnd,None,0,0,650,280,0x16))
                    post(0x20a,(-120 & 65535)<<16)
                    post(0x10)
                    _,errors=process.communicate(timeout=15)
                    self.assertEqual((process.returncode,errors),(0,b''))
                    self.assertEqual(output.read_bytes().count(b'ACTIVATE'),3,output.read_bytes())
                finally:
                    if process.poll() is None:process.kill();process.wait()
                    process.stderr.close()

if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'): delattr(base.Evolution, name)
    unittest.main(verbosity=2)

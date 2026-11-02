"""Reader selection/reflow against a byte model, native MSAA and 200% metrics."""
import ctypes
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import unittest
import importlib.util
import time
import struct

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

viewer=module('reader_viewer_tests',Path(__file__).with_name('test-htdl-viewer.py'))
base=viewer.base
PREFIX=viewer.PREFIX.replace('std/viewer.assis','std/reader.assis')
def setup(body,width=240,height=160):
    return ('own store:documents::Store=try_new documents::Store(32000000,250000,1000);'
        'assert(htdl::load(store,1,'+viewer.parser.literal(viewer.parser.document(body))+').code==0);'
        f'own r:reader::Reader=try_new reader::Reader(store.active_document(),7,{width},{height},16,cells);'
        'assert(r!=null && r.is_open());')

class HtdlReader(base.Evolution):
    @classmethod
    def setUpClass(cls):
        cls.provider_temp=viewer.tempfile.TemporaryDirectory(prefix='assis-reader-provider-')
        if os.name=='nt':
            cls.builder=module('reader_builder',base.ROOT/'tools/build-platform.py')
            cls.provider=Path(cls.provider_temp.name)/'assis_platform_v1.dll'
            cls.builder.build(cls.provider,testing=True)
    @classmethod
    def tearDownClass(cls):cls.provider_temp.cleanup()
    def setUp(self):
        super().setUp()
        if os.name=='nt':
            shutil.copyfile(self.provider,self.temp/'assis_platform_v1.dll')
            old=os.environ.get('PATH','');os.environ['PATH']=str(self.temp)+os.pathsep+old
            self.addCleanup(os.environ.__setitem__,'PATH',old)
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)
    def execute(self,body,expected='',prefix=PREFIX):
        self.accepted(prefix+'safe fn main():int{'+body+'return 0;}',expected)
    def build_oracle(self):
        compiler=self.builder.build(self.temp/'oracle-provider.dll',testing=True)[0]
        oracle=self.temp/'reader-oracle.exe'
        command=[compiler,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',
            str(base.ROOT/'tests/reader_oracle.c'),'-o',str(oracle),'-loleacc','-loleaut32','-lole32','-luuid','-luser32','-lgdi32']
        environment=dict(os.environ,PATH=str(Path(compiler).parent)+os.pathsep+os.environ['PATH'])
        built=subprocess.run(command,capture_output=True,text=True,env=environment)
        self.assertEqual(built.returncode,0,built.stderr)
        return oracle

    def test_selection_against_independent_grapheme_byte_ranges_and_reverse(self):
        content='Ação cafe\u0301 😀 fim'
        model=(content+'\n').encode()
        clusters=['A','ç','ã','o',' ','c','a','f','e\u0301',' ','😀',' ','f','i','m','\n']
        self.assertEqual(''.join(clusters).encode(),model)
        boundaries=[0]
        for cluster in clusters:boundaries.append(boundaries[-1]+len(cluster.encode()))
        rng=random.Random(20261101)
        body=setup('<div type=paragraph>'+content+'</div>',width=120)
        output=''
        for _ in range(24):
            a,b=rng.sample(boundaries,2)
            body+=f'assert(r.select({a},{b}));print(r.selected_text());'
            output+=model[min(a,b):max(a,b)].decode()+'\n'
        for i,b in enumerate(model):
            if 128<=b<192:body+=f'assert(!r.select({i},0));'
        body+='assert(!r.select(-1,0) && !r.select(0,9223372036854775807));'
        self.execute(body,output)

    def test_semantic_boundaries_soft_wraps_hidden_and_owned_accessible_names(self):
        self.execute(setup('<div type=heading level=1>Title</div>'
            '<div type=paragraph>alpha <div type=text> beta </div> gamma</div>'
            '<div type=button a11y-label="Accessible name">Visible</div>'
            '<div type=button disabled=true>Disabled</div>'
            '<div type=container hidden=true><div type=button>SECRET</div></div>',width=120)+
            'assert(r.item_count()==4);r.select(0,r.snapshot().text_size());print(r.selected_text());'
            'assert(r.item(0).role==8 && r.item(3).disabled==1);'
            'print(r.item_name(2));store.close();print(r.item_name(1));',
            'Title\nalpha beta gamma\nVisible\nDisabled\n\nAccessible name\nalpha beta gamma\n')

    def test_pointer_drag_keyboard_scalar_navigation_copy_request_and_cancel(self):
        self.execute(setup('<div type=paragraph>Ação xyz</div><div type=button>Go</div>')+
            'r.dispatch(1,event(7,36,25,1));r.dispatch(1,event(4,60,25,2));'
            'r.dispatch(1,event(8,60,25,3));print(r.selected_text());'
            'r.dispatch(1,event(3,16,1,4));r.dispatch(1,event(3,39,1,5));print(r.selected_text());'
            'r.dispatch(1,event(3,16,0,6));r.dispatch(1,event(3,17,1,7));'
            'assert(r.dispatch(1,event(3,67,1,8)).kind==4);'
            'r.dispatch(1,event(10,0,0,9));assert(r.dispatch(1,event(3,67,1,10)).kind==0);'
            'r.dispatch(1,event(3,9,1,11));assert(r.dispatch(1,event(3,13,1,12)).kind==2);',
            'Açã\nAção\n')

    def test_reflow_keeps_selection_focus_and_rejects_old_events_and_actions(self):
        self.execute(setup('<div type=paragraph>'+'palavra '*35+'</div><div type=button>Go</div>')+
            'r.select(1,20);r.dispatch(1,event(3,9,1,1));'
            'own resized:reader::Reader=try_new reader::Reader(store.active_document(),7,320,180,32,cells);'
            'assert(resized!=null && resized.is_open());resized.restore(r);'
            'assert(resized.selection_start()==1 && resized.selection_end()==20);'
            'assert(viewer::same(r.snapshot().focus_node(),resized.snapshot().focus_node()));'
            'assert(resized.dispatch(1,event(3,13,1,1)).kind==0);'
            'assert(resized.dispatch(1,event(11,2,2,2)).kind==0);'
            'assert(resized.dispatch(1,event(11,1,2,3)).kind==2);'
            'resized.close();assert(resized.dispatch(1,event(11,1,2,4)).kind==0);')

    def test_disabled_invalid_document_and_zoom_requests(self):
        self.execute(setup('<div type=button disabled=true>No</div><div type=button>Yes</div>')+
            'assert(r.dispatch(1,event(11,1,1,1)).kind==0);'
            'assert(r.dispatch(2,event(11,1,2,2)).kind==0);'
            'assert(r.dispatch(1,event(11,1,999999,2)).kind==0);'
            'assert(r.dispatch(1,event(11,1,2,3)).kind==2);'
            'r.dispatch(1,event(3,17,1,4));assert(r.dispatch(1,event(3,187,1,5)).kind==5);'
            'assert(r.dispatch(1,event(3,48,1,6)).kind==6);'
            'r.dispatch(1,event(3,65,1,7));assert(len(r.selected_text())==r.snapshot().text_size());')

    def test_os_refusal_preserves_reader_selection_and_neighbor(self):
        warm,drain,cleanup=viewer.parser.preparation.exhaustion()
        program=PREFIX+'safe fn main():int{'+setup('<div type=paragraph>Keep ação</div>')
        program+='assert(r.select(0,4));unsafe{'+warm+drain
        program+=('own failed:reader::Reader=try_new reader::Reader(store.active_document(),7,240,160,16,cells);'
            'assert(failed==null || !failed.is_open());assert(r.is_open());print(r.selected_text());'+cleanup+'}return 0;}')
        viewer.HtdlViewer.fault_program(self,program,'Keep\n')

    @unittest.skipUnless(os.name=='nt','Windows MSAA/clipboard/font provider unsupported')
    def test_native_msaa_oracle_and_isolated_clipboard(self):
        oracle=self.build_oracle()
        for argument in ([],['--clipboard']):
            run=subprocess.run([oracle,self.temp/'oracle-provider.dll',*argument],capture_output=True,timeout=30)
            self.assertEqual((run.returncode,run.stderr),(0,b''),(run.stdout,run.stderr))
            self.assertIn(b'PASS',run.stdout)

    @unittest.skipUnless(os.name=='nt','Windows integrated paint/accessibility unsupported')
    def test_integrated_reader_publish_paint_200_and_failure_cleanup(self):
        self.execute(setup('<div type=heading level=1>ação</div><div type=button a11y-label=Name>Go</div>')+
            'assert(reader::available());own w:window::Window=try_new window::Window(7,240,160,"reader");'
            'assert(w!=null && w.opened());assert(r.publish(w)==0);assert(r.paint(w,1000));'
            'assert(r.select(0,3));assert(r.paint(w,1000));'
            'r.dispatch(1,event(3,9,1,1));r.select(0,r.snapshot().text_size());assert(r.paint(w,1000));'
            'val button_y:int=r.snapshot().line(r.item(1).first).y;'
            'unsafe{assert(pixel(w.platform_token(),i32(24),i32(button_y-4))==4278218103);}'
            'val metrics:int=reader::measure(utf8("M"),2000);assert(metrics>0);'
            'own zoomed:reader::Reader=try_new reader::Reader(store.active_document(),7,240,160,metrics/4294967296,reader::width_200);'
            'assert(zoomed!=null && zoomed.is_open());zoomed.restore(r);'
            'assert(zoomed.publish(w)==0 && zoomed.paint(w,2000));'
            'assert(w.close()==0 && zoomed.publish(w)== -2);',prefix=PREFIX+
            'extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_pixel") fn pixel(window:int,x:i32,y:i32):int;')

    def test_reader_five_formats_and_native_execution(self):
        source=self.source(PREFIX+'safe fn main():int{'+setup('<div type=button>One</div>')+
            'assert(r.item_count()==1);return 0;}')
        for flags in ([],['--no-opt']):
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                binary=self.temp/(target+'.exe')
                result=self.invoke('build',source,'--target',target,'-o',binary,*flags)
                self.assertEqual(result.returncode,0,result.stderr)
                data=binary.read_bytes();header=data[:6]
                self.assertTrue(header.startswith(b'MZ') if target.startswith('windows') else
                    header==b'\x7fELF\x02\x01' if target.startswith('linux') else header[:4]==b'\xcf\xfa\xed\xfe')
                if target.startswith('linux'):
                    self.assertEqual(struct.unpack_from('<H',data,18)[0],183 if target.endswith('arm64') else 62)
                elif target.startswith('macos'):
                    self.assertEqual(struct.unpack_from('<I',data,4)[0],0x0100000c if target.endswith('arm64') else 0x01000007)
                else:
                    pe=struct.unpack_from('<I',data,0x3c)[0];self.assertEqual(struct.unpack_from('<H',data,pe+4)[0],0x8664)
                if target==('windows-x64' if os.name=='nt' else 'linux-x64'):
                    run=subprocess.run([binary],capture_output=True,timeout=20)
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    @unittest.skipUnless(os.name=='nt','Windows external MSAA application unsupported')
    def test_real_reader_external_accessible_client_zoom_resize_and_close(self):
        from ctypes import wintypes as W
        C=ctypes;user=C.WinDLL('user32');callback=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
        user.EnumWindows.argtypes=[callback,W.LPARAM]
        user.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
        user.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
        user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
        user.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
        oracle=self.build_oracle();entry=self.temp/'ação 日本.htdl'
        entry.write_text(viewer.parser.document('<div type=heading level=1>Título</div>'
            '<div type=paragraph>Ação café</div><div type=button a11y-label=Run>Visible</div>'
            '<div type=button disabled=true>No</div>'),encoding='utf-8')
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=self.temp/(mode+'.exe');built=self.invoke('build',base.ROOT/'exemplos/45_htdl_reader.assis','-o',binary,*flags)
            self.assertEqual(built.returncode,0,built.stderr)
            output=self.temp/(mode+'.stdout')
            with output.open('wb') as stream:
                process=subprocess.Popen([binary,entry],stdout=stream,stderr=subprocess.PIPE)
                try:
                    deadline=time.monotonic()+10;targets=[]
                    while time.monotonic()<deadline:
                        targets.clear()
                        @callback
                        def visit(hwnd,unused):
                            pid=W.DWORD();user.GetWindowThreadProcessId(hwnd,C.byref(pid))
                            name=C.create_unicode_buffer(128);user.GetClassNameW(hwnd,name,128)
                            if pid.value==process.pid and name.value=='AssisPlatformV1':targets.append(hwnd)
                            return True
                        user.EnumWindows(visit,0)
                        if len(targets)==1 and b'READER' in output.read_bytes():break
                        time.sleep(.02)
                    self.assertEqual(len(targets),1,output.read_bytes());hwnd=targets[0]
                    run=subprocess.run([oracle,'--client',str(hwnd)],capture_output=True,timeout=15)
                    self.assertEqual((run.returncode,run.stderr),(0,b''),run.stderr)
                    def key(code,down=True):self.assertTrue(user.PostMessageW(hwnd,0x100 if down else 0x101,code,0))
                    key(17);key(187);key(187,False);key(17,False)
                    deadline=time.monotonic()+10
                    while b'REFLOW 2000' not in output.read_bytes() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertIn(b'REFLOW 2000',output.read_bytes())
                    self.assertEqual(output.read_bytes().count(b'ACTIVATE'),1,output.read_bytes())
                    self.assertTrue(user.SetWindowPos(hwnd,None,0,0,620,320,0x16))
                    key(17);key(48);key(48,False);key(17,False)
                    deadline=time.monotonic()+10
                    while b'REFLOW 1000' not in output.read_bytes() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertIn(b'REFLOW 1000',output.read_bytes())
                    self.assertTrue(user.PostMessageW(hwnd,0x10,0,0));_,errors=process.communicate(timeout=10)
                    self.assertEqual((process.returncode,errors),(0,b''))
                finally:
                    if process.poll() is None:process.kill();process.wait()
                    process.stderr.close()

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

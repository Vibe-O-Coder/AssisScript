"""One snapshot drives raster, interaction and copied MSAA; atomic native failure."""
import ctypes as C
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import unittest

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

frame=module('frame_tests',Path(__file__).with_name('test-pageframe.py'))
reader=module('reader_tests',Path(__file__).with_name('test-htdl-reader.py'))
base=frame.base

class PagePresent(unittest.TestCase):
    setUpClass=classmethod(reader.HtdlReader.setUpClass.__func__)
    tearDownClass=classmethod(reader.HtdlReader.tearDownClass.__func__)
    source=base.Evolution.source
    accepted=base.Evolution.accepted
    def setUp(self):
        base.Evolution.setUp(self)
        if os.name=='nt':
            shutil.copyfile(self.provider,self.temp/'assis_platform_v1.dll')
            old=os.environ.get('PATH','');os.environ['PATH']=str(self.temp)+os.pathsep+old
            self.addCleanup(os.environ.__setitem__,'PATH',old)
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return base.Evolution.invoke(self,*args,**kwargs)
    def execute(self,body):
        self.accepted(frame.PREFIX+'import "std/pagepresent.assis";safe fn main():int{'+body+'return 0;}')

    def test_packet_commands_and_accessibility_share_clipped_frame_bounds(self):
        source='flow B{100px -> layout.width;40px -> layout.height;12px -> target.offsetX;}bind #b to B;'
        self.execute(frame.setup('<div type=button id=b>B</div>',source,width=80,height=30)+
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(frame,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(packet!=null && packet.is_open() && packet.item_count()==2);'
            'val a:pageframe::Rect=packet.item_bounds(1);val b:pageframe::Rect=packet.paint_bounds(0);'
            'assert(a.x==b.x && a.y==b.y && a.width==b.width && a.height==b.height && a.width==68);'
            'assert(packet.item_box(1)==1 && packet.item_box(0)== -1);'
            'assert(doctree::absent(packet.action(frame,store.candidate(),1,1)));')

    def test_focus_order_tracks_semantics_and_disabled_overlay_blocks_underlying_action(self):
        self.execute(frame.setup('<div type=button id=a>A</div><div type=button id=b disabled=true>B</div>',
                'flow B{-16px -> target.offsetY;}bind #b to B;')+
            'val a:doctree::NodeId=frame.box(1).node;'
            'assert(pageframe::same(frame.next_focus(store.candidate(),new doctree::NodeId(),false),a));'
            'assert(pageframe::same(frame.next_focus(store.candidate(),a,true),a));'
            'assert(doctree::absent(frame.hit(store.candidate(),1,2,2)));')

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_native_publish_and_action_revalidate_projection_and_semantic_generation(self):
        self.execute(frame.setup('<div type=button id=b>B</div>')+
            'own w:window::Window=try_new window::Window(7,320,200,utf8("Frame integration"));assert(w!=null && w.opened());'
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(frame,frame.box(1).node,reader::default_preferences(),10000000);'
            'assert(packet!=null && packet.is_open());assert(packet.publish(w,frame,store.candidate())==0);assert(w.present()==0);'
            'assert(pageframe::same(packet.action(frame,store.candidate(),1,1),frame.box(1).node));'
            'assert(doctree::absent(packet.action(frame,store.candidate(),2,1)));'
            'assert(packet.publish(w,frame,store.candidate())==204);'
            'assert(store.candidate().erase_subtree(frame.box(1).node));'
            'assert(doctree::absent(packet.action(frame,store.candidate(),1,1)));assert(w.close()==0);')

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_real_font_metrics_feed_layout_and_native_render_at_two_scales(self):
        body=frame.setup('<div type=paragraph>Ação café</div><div type=button>Go</div>').replace(',metric);',',pagepresent::measure);')
        self.execute(body+
            'own w:window::Window=try_new window::Window(7,320,200,utf8("Native frame font"));assert(w!=null && w.opened());'
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(frame,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(packet!=null && packet.is_open());assert(packet.publish(w,frame,store.candidate())==0);assert(w.present()==0);'
            'own big:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,131072,10000000,pagepresent::measure);'
            'assert(big!=null && big.is_open() && big.run(0).bounds.height>frame.run(0).bounds.height);'
            'own next:pagepresent::Packet=try_new pagepresent::Packet(big,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(next!=null && next.is_open());assert(next.publish(w,big,store.candidate())==0);assert(w.present()==0);'
            'assert(doctree::absent(packet.action(frame,store.candidate(),1,2)));assert(w.close()==0);'
            'assert(doctree::absent(next.action(big,store.candidate(),2,2)));')

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_two_panel_window_presents_and_closes_in_both_modes(self):
        for number,flags in enumerate([[],['--no-opt']]):
            binary=self.temp/f'panels-{number}.exe'
            result=self.invoke('build',base.ROOT/'exemplos/57_page_frame_window.assis','--debug','-o',binary,*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),'--once'],cwd=self.temp,capture_output=True,text=True,timeout=20)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'FRAME 1 10\n',''))

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_all_native_allocation_boundaries_preserve_pixels_accessibility_and_gdi_objects(self):
        dll=C.CDLL(str(self.provider));i64=C.c_int64;i32=C.c_int32;ptr=C.POINTER(i64)
        for name,args,result in [
            ('assisp_open',[i64,i32,i32,C.c_char_p,i64,ptr],i32),
            ('assisp_close',[i64],i32),('assisp_test_control',[i64,i64],i64),
            ('assisp_test_pixel',[i64,i32,i32],i64),
            ('assisp_frame_commit',[i64,i64,C.c_uint32,ptr,i64,C.c_char_p,i64,ptr,i64,C.c_char_p,i64],i32)]:
            fn=getattr(dll,name);fn.argtypes=args;fn.restype=result
        import _ctypes
        self.addCleanup(lambda:_ctypes.FreeLibrary(dll._handle))
        user=C.WinDLL('user32');kernel=C.WinDLL('kernel32')
        user.GetGuiResources.argtypes=[C.c_void_p,C.c_uint];user.GetGuiResources.restype=C.c_uint
        kernel.GetCurrentProcess.restype=C.c_void_p
        resources=lambda:user.GetGuiResources(kernel.GetCurrentProcess(),0)
        token=i64();self.assertEqual(dll.assisp_open(100,96,64,b'Atomic frame',12,C.byref(token)),0)
        self.addCleanup(lambda:dll.assisp_close(token.value))
        access=(i64*16)(1,0,0,0,96,64,0,3,9,0,0,0,96,32,3,2)
        command=(i64*14)(1,0,0,24,20,0,0,24,20,0xffffffff,16,400,0,2)
        def commit(projection,bg=0x123456ff):return dll.assisp_frame_commit(token,projection,bg,command,1,b'Go',2,access,2,b'DocGo',5)
        self.assertEqual(commit(1),0);before=dll.assisp_test_pixel(token,80,50)
        failures=0;gdi_before=resources()
        for checkpoint in range(32):
            self.assertEqual(dll.assisp_test_control(0,checkpoint),0)
            result=commit(2,0xff0000ff);dll.assisp_test_control(0,-1)
            if result==0:break
            self.assertEqual(result,-4,checkpoint);failures+=1
            self.assertEqual(dll.assisp_test_pixel(token,80,50),before,checkpoint)
            self.assertEqual(dll.assisp_test_control(9,0),1,checkpoint)
            self.assertEqual(resources(),gdi_before,checkpoint)
        self.assertGreaterEqual(failures,9);self.assertEqual(result,0)
        self.assertNotEqual(dll.assisp_test_pixel(token,80,50),before)
        self.assertEqual(commit(2),-2)
        # A rejected accessible projection follows successful candidate raster.
        access[8]=99;before=dll.assisp_test_pixel(token,80,50)
        self.assertEqual(commit(3),-1);self.assertEqual(dll.assisp_test_pixel(token,80,50),before)
        access[8]=9;self.assertEqual(commit(3),0)
        # Invalid clip, UTF-8 and work limits never publish partial pixels.
        command[7]=1000;self.assertEqual(commit(4),-1);command[7]=24
        self.assertEqual(dll.assisp_frame_commit(token,4,0,command,1,b'\xffx',2,access,2,b'DocGo',5),-1)
        self.assertEqual(dll.assisp_test_control(9,0),1)

if __name__=='__main__':unittest.main(verbosity=2)

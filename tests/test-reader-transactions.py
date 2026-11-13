"""Semantic transactions, user preferences and a bounded presentation clock."""
import ctypes as C
from ctypes import wintypes as W
import importlib.util
import os
from pathlib import Path
import random
import struct
import subprocess
import time
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('reader_tests',Path(__file__).with_name('test-htdl-reader.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
base=reader.base
literal=reader.viewer.parser.literal
document=reader.viewer.parser.document
PREFIX=reader.PREFIX

def session(body):
    return ('own s:reader::Session=try_new reader::Session(32000000,250000,7);assert(s!=null && s.is_open());'
        'assert(s.prepare(1,'+literal(document(body))+',240,160,16,cells)==0);assert(s.commit());')

class Transactions(unittest.TestCase):
    setUpClass=classmethod(reader.HtdlReader.setUpClass.__func__)
    tearDownClass=classmethod(reader.HtdlReader.tearDownClass.__func__)
    source=base.Evolution.source
    accepted=base.Evolution.accepted
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return base.Evolution.invoke(self,*args,**kwargs)
    execute=reader.HtdlReader.execute
    def setUp(self):
        base.Evolution.setUp(self)
        if os.name=='nt':
            reader.shutil.copyfile(self.provider,self.temp/'assis_platform_v1.dll')
            old=os.environ.get('PATH','');os.environ['PATH']=str(self.temp)+os.pathsep+old
            self.addCleanup(os.environ.__setitem__,'PATH',old)

    def test_staging_is_not_activation_and_busy_does_not_abort_another_candidate(self):
        self.execute('own store:documents::Store=try_new documents::Store(32000000,250000,1000);'
            'assert(htdl::load(store,1,'+literal(document('<div type=paragraph>Old</div>'))+').code==0);'
            'assert(htdl::stage(store,2,'+literal(document('<div type=paragraph>New</div>'))+',0).code==0);'
            'assert(store.active_document().instance()==1 && store.has_candidate());'
            'assert(htdl::stage(store,3,'+literal(document('<div type=paragraph>Other</div>'))+',0).code==401);'
            'assert(store.has_candidate() && store.candidate().instance()==2);assert(store.commit(2));'
            'assert(store.active_document().instance()==2);')

    def test_transaction_maps_focus_by_semantic_id_and_cancels_old_actions(self):
        before='<div type=button id=keep>Old</div><div type=button id=other>Other</div>'
        after='<div type=paragraph>Inserted</div><div type=button id=keep a11y-label=New>Changed</div>'
        self.execute(session(before)+
            's.dispatch(1,event(3,9,1,1));val old:doctree::NodeId=s.active_reader().snapshot().focus_node();'
            'assert(s.prepare(2,'+literal(document(after))+',240,160,16,cells)==0);'
            'assert(s.document().instance()==1);assert(s.dispatch(1,event(3,13,1,2)).kind==0);assert(s.commit());'
            'assert(!s.document().nodes().contains(old));'
            'val focus:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("keep"));'
            'assert(viewer::same(s.active_reader().snapshot().focus_node(),focus));'
            'assert(s.dispatch(1,event(11,1,1,3)).kind==0);'
            'assert(s.dispatch(2,event(11,1,1,4)).kind==0);'
            'assert(s.dispatch(2,event(3,13,1,1)).kind==0);'
            'assert(s.dispatch(2,event(3,13,1,5)).kind==2);'
            'assert(s.active_reader().selection_end()==0);print(s.active_reader().item_name(1));','New\n')

    def test_boolean_mutations_missing_attributes_disabled_hidden_and_stale_patch(self):
        self.execute(session('<div type=button id=a>First</div><div type=button id=b>Second</div>')+
            's.dispatch(1,event(3,9,1,1));'
            'val old:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("a"));'
            'own patch:htdl::Patch=htdl::set_boolean(s.document(),old,8,true);assert(patch!=null && patch.is_open());'
            'assert(s.prepare_patch(2,patch,240,160,16,cells)==0 && s.commit());'
            'assert(doctree::absent(s.active_reader().snapshot().focus_node()));'
            'assert(s.active_reader().item(0).disabled==1 && s.dispatch(2,event(11,2,1,2)).kind==0);'
            'assert(s.prepare_patch(3,patch,240,160,16,cells)== -1);'
            'val a:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("a"));'
            'own hidden:htdl::Patch=htdl::set_boolean(s.document(),a,7,true);'
            'assert(s.prepare_patch(3,hidden,240,160,16,cells)==0 && s.commit());'
            'assert(s.active_reader().item_count()==1);print(s.active_reader().item_name(0));','Second\n')

    def test_ordered_type_class_query_matches_independent_xml(self):
        body='<div type="container"><div type="paragraph" class="cat category">A</div><div type="paragraph" class="cat">B</div></div><div type="button" class="cat">C</div>'
        model=ET.fromstring(document(body))
        expected=''.join((n.text or '')+'\n' for n in model.iter() if n.attrib.get('type')=='paragraph' and 'cat' in n.attrib.get('class','').split())
        self.execute(session(body)+
            'let at:doctree::NodeId=new doctree::NodeId();for(let i:int=0;i<2;i++){'
            'at=htdl::query(s.document().nodes(),6,utf8("cat"),at);assert(!doctree::absent(at));'
            'val child:doctree::NodeId=s.document().nodes().first_child(at);'
            'let n:doctree::NodeId=child;while(s.document().nodes().kind(n)!=2){n=s.document().nodes().next_sibling(n);}'
            'own b:*byte=try_alloc<byte>(htdl::value_size(s.document().nodes(),n));'
            'for(let j:int=0;j<len(b);j++){b[j]=htdl::value_byte(s.document().nodes(),n,j);}print(slice_of(b,0,len(b)));}'
            'assert(doctree::absent(htdl::query(s.document().nodes(),6,utf8("cat"),at)));'
            'assert(doctree::absent(htdl::query(s.document().nodes(),6,utf8("ca"),new doctree::NodeId())));',expected)

    def test_patch_create_remove_and_escaped_text_against_xml(self):
        body='<div type=paragraph id=p>Ação</div><div type=button id=remove>Delete</div>'
        full=document(body);start=full.index('Ação');end=start+len('Ação'.encode())
        self.execute(session(body)+
            f'own edit:htdl::Patch=try_new htdl::Patch(s.document(),{start},{end},utf8("&lt;novo&gt; &amp; café"));'
            'assert(s.prepare_patch(2,edit,240,160,16,cells)==0 && s.commit());print(s.active_reader().item_name(0));'
            'val remove:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("remove"));'
            'own cut:htdl::Patch=try_new htdl::Patch(s.document(),htdl::span_start(s.document().nodes(),remove),htdl::span_end(s.document().nodes(),remove),utf8(""));'
            'assert(s.prepare_patch(3,cut,240,160,16,cells)==0 && s.commit());assert(s.active_reader().item_count()==1);'
            'val p:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("p"));'
            'val position:int=htdl::span_end(s.document().nodes(),p);'
            'own add:htdl::Patch=try_new htdl::Patch(s.document(),position,position,utf8("<div type=button id=new>Created</div>"));'
            'assert(s.prepare_patch(4,add,240,160,16,cells)==0 && s.commit());print(s.active_reader().item_name(1));',
            '<novo> & café\nCreated\n')

    def test_parse_measure_quota_failures_keep_last_document_and_allow_retry(self):
        self.execute(session('<div type=button id=keep>Keep</div>')+
            's.dispatch(1,event(3,9,1,1));val focus:doctree::NodeId=s.active_reader().snapshot().focus_node();'
            'assert(s.prepare(2,'+literal(document('<div type=paragraph>New</div>'))+',240,160,16,fail)== -4);'
            'assert(!s.has_pending() && s.document().instance()==1);'
            'assert(s.prepare(3,utf8("<div>bad"),240,160,16,cells)!=0 && !s.has_pending());'
            'assert(viewer::same(focus,s.active_reader().snapshot().focus_node()));'
            'assert(s.dispatch(1,event(3,13,1,2)).kind==2);'
            'assert(s.prepare(4,'+literal(document('<div type=button id=keep>New</div>'))+',240,160,16,cells)==0);'
            's.abort();assert(!s.has_pending() && s.document().instance()==1);'
            'assert(s.prepare(5,'+literal(document('<div type=paragraph>Final</div>'))+',240,160,16,cells)==0 && s.commit());')

    def test_invalid_ranges_utf8_node_and_semantic_edit_cannot_activate(self):
        self.execute(session('<div type=paragraph id=p>é</div>')+
            'own invalid:htdl::Patch=try_new htdl::Patch(s.document(),-1,0,utf8("x"));assert(!invalid.is_open());'
            'val p:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("p"));'
            'own unsupported:htdl::Patch=htdl::set_boolean(s.document(),p,6,true);assert(!unsupported.is_open());'
            'own wrong_type:htdl::Patch=htdl::set_boolean(s.document(),p,8,true);'
            'assert(s.prepare_patch(2,wrong_type,240,160,16,cells)==203);assert(s.document().instance()==1);'
            'own stale:htdl::Patch=htdl::set_boolean(s.document(),new doctree::NodeId(999,1,1),7,true);assert(!stale.is_open());'
            'own huge:*byte=try_alloc<byte>(1048577);'
            'own rejected:htdl::Patch=try_new htdl::Patch(s.document(),0,0,slice_of(huge,0,len(huge)));assert(!rejected.is_open());')

    def test_quota_and_unicode_cut_preserve_active_and_stale_query_cursor_is_refused(self):
        source=document('<div type=paragraph id=p>é</div>');offset=source.encode().index('é'.encode())
        self.execute(session('<div type=paragraph id=p>é</div>')+
            f'own cut:htdl::Patch=try_new htdl::Patch(s.document(),{offset+1},{offset+2},utf8(""));assert(!cut.is_open());'
            'assert(doctree::absent(htdl::query(s.document().nodes(),0,utf8(""),new doctree::NodeId(999,1,1))));'
            'own limited:reader::Session=try_new reader::Session(12000,100,9);'
            'assert(limited.prepare(1,'+literal(document('<div type=paragraph>Keep</div>'))+',240,160,16,cells)==0 && limited.commit());'
            'own large:*byte=try_alloc<byte>(13000);for(let i:int=0;i<len(large);i++){large[i]=byte(32);}'
            'assert(limited.prepare(2,slice_of(large,0,len(large)),240,160,16,cells)==401);'
            'assert(limited.has_active() && !limited.has_pending() && limited.document().instance()==1);')

    def test_transaction_generation_for_five_formats_and_native_execution(self):
        path=self.source(PREFIX+'safe fn main():int{'+session('<div type=button id=a>Keep</div>')+
            'own clock:reader::Motion=try_new reader::Motion();assert(clock.start(0,350));assert(clock.sample(100,true,false,true)==1000);return 0;}')
        for flags in ([],['--no-opt']):
            for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                output=self.temp/(target+'.exe');built=self.invoke('build',path,'--target',target,'-o',output,*flags)
                self.assertEqual(built.returncode,0,built.stderr);data=output.read_bytes()
                if target.startswith('linux'):
                    self.assertEqual(data[:6],b'\x7fELF\x02\x01');self.assertEqual(struct.unpack_from('<H',data,18)[0],183 if target.endswith('arm64') else 62)
                elif target.startswith('macos'):
                    self.assertEqual(struct.unpack_from('<II',data),(0xfeedfacf,0x0100000c if target.endswith('arm64') else 0x01000007))
                else:
                    self.assertEqual(data[:2],b'MZ');pe=struct.unpack_from('<I',data,0x3c)[0];self.assertEqual(struct.unpack_from('<H',data,pe+4)[0],0x8664)
                if target==base.NATIVE_TARGET:
                    run=subprocess.run([output],capture_output=True,timeout=20);self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_oom_during_candidate_construction_preserves_active_and_neighbor(self):
        warm,drain,cleanup=reader.viewer.parser.preparation.exhaustion()
        code=PREFIX+'safe fn main():int{'+session('<div type=button id=a>Keep</div>')
        code+='unsafe{'+warm+drain+'assert(s.prepare(2,'+literal(document('<div type=paragraph>New</div>'))+',240,160,16,cells)!=0);'
        code+='assert(s.has_active() && !s.has_pending() && s.document().instance()==1);print(s.active_reader().item_name(0));'+cleanup+'}return 0;}'
        reader.viewer.HtdlViewer.fault_program(self,code,'Keep\n')

    def test_motion_hidden_editing_reduced_and_clock_bounds_against_time_model(self):
        rng=random.Random(20261101);now=0;elapsed=0;previous=True;body='own m:reader::Motion=try_new reader::Motion();assert(m.start(0,1000));';expected=''
        for _ in range(50):
            now+=rng.randrange(0,31);visible=rng.choice([True,False]);editing=rng.choice([True,False]);delta=now-(0 if _==0 else old)
            if previous and visible and not editing:elapsed=min(1000,elapsed+delta)
            previous=visible and not editing;old=now
            body+=f'print(m.sample({now},{str(visible).lower()},{str(editing).lower()},false));';expected+=str(elapsed)+'\n'
        body+=f'assert(m.sample({now},true,false,true)==1000);assert(m.sample(9223372036854775807,true,false,false)==1000);'
        body+='assert(!m.start(-1,1) && !m.start(0,0) && !m.start(0,60001));'
        body+='assert(m.start(100,1000));assert(m.sample(200,true,false,false)==100);assert(m.sample(150,true,false,false)==100);'
        self.execute(body,expected)

    @unittest.skipUnless(os.name=='nt','Windows native preferences/MSAA unsupported')
    def test_msaa_publication_failure_is_atomic_then_disabled_is_current(self):
        native='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(op:int,value:int):int;'
        self.execute(session('<div type=button id=a>Keep</div>')+
            'own w:window::Window=try_new window::Window(7,240,160,"transaction");assert(w.opened());'
            'assert(s.prepare(2,'+literal(document('<div type=button id=a>Active</div>'))+',240,160,16,cells)==0 && s.publish(w)==0);'
            'val a:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("a"));'
            'own patch:htdl::Patch=htdl::set_boolean(s.document(),a,8,true);'
            'assert(s.prepare_patch(3,patch,240,160,16,cells)==0);unsafe{control(0,0);}'
            'assert(s.publish(w)== -4 && s.document().instance()==2 && s.has_pending());'
            'assert(s.dispatch(2,event(11,2,1,1)).kind==0);unsafe{control(0,-1);}'
            'assert(s.publish(w)==0 && s.document().instance()==3);assert(s.active_reader().item(0).disabled==1);'
            'assert(s.dispatch(3,event(11,3,1,2)).kind==0);assert(s.paint(w,1000));'
            'assert(w.close()==0);unsafe{assert(control(9,0)==0 && control(3,0)==0);}',prefix=PREFIX+native)

    @unittest.skipUnless(os.name=='nt','Windows high contrast drawing unsupported')
    def test_high_contrast_selection_focus_and_system_query(self):
        native='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_pixel") fn pixel(window:int,x:i32,y:i32):int;'
        self.execute(reader.setup('<div type=button>Selected</div>')+
            'own w:window::Window=try_new window::Window(7,240,160,"contrast");assert(w.opened());'
            'val system:reader::Preferences=reader::preferences(w);assert(system.status==0);'
            'val p:reader::Preferences=new reader::Preferences(0,true,true,u32(0x000000ff),u32(0xffffffff),u32(0x000000ff),'
            'u32(0xffffffff),u32(0xaaaaaaff),u32(0xffff00ff),u32(0x000000ff));'
            'r.dispatch(1,event(3,9,1,1));r.select(0,4);assert(r.paint_with(w,1000,p));'
            'unsafe{assert(pixel(w.platform_token(),i32(0),i32(0))==4278190080);'
            'assert(pixel(w.platform_token(),i32(24),i32(20))==4294967295);'
            'assert(pixel(w.platform_token(),i32(37),i32(24))>=4278190080);}'
            'assert(w.close()==0);assert(reader::preferences(w).status== -2);',prefix=PREFIX+native)

    @unittest.skipUnless(os.name=='nt','Windows preferences event adapter unsupported')
    def test_native_preferences_oracle_subscription_capacity_thread_and_revocation(self):
        dll=C.CDLL(str(self.provider));i64=C.c_int64;p64=C.POINTER(i64)
        import _ctypes
        self.addCleanup(_ctypes.FreeLibrary,dll._handle)
        signatures={'open':(C.c_int32,[i64,C.c_int32,C.c_int32,C.c_void_p,i64,p64]),
            'preferences':(C.c_int32,[i64,p64,i64]),'poll':(C.c_int32,[i64,C.c_int32,p64,i64]),
            'close':(C.c_int32,[i64]),'test_control':(i64,[i64,i64])}
        for n,(result,args) in signatures.items():getattr(dll,'assisp_'+n).restype=result;getattr(dll,'assisp_'+n).argtypes=args
        token=i64();assert dll.assisp_open(100,120,100,b'x',1,C.byref(token))==0
        try:
            user=C.WinDLL('user32');user.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
            hwnd=dll.assisp_test_control(4,token.value);words=(i64*10)(*([-99]*10))
            while dll.assisp_poll(token,0,words,10)==0:pass
            user.SendMessageW(hwnd,0x0015,0,0) # WM_SYSCOLORCHANGE, before subscription
            self.assertEqual(dll.assisp_poll(token,0,words,10),1)
            self.assertEqual(dll.assisp_preferences(token,words,9),-1)
            self.assertEqual(dll.assisp_preferences(token,words,10),0)
            class HC(C.Structure):_fields_=[('size',W.UINT),('flags',W.DWORD),('scheme',W.LPWSTR)]
            hc=HC();hc.size=C.sizeof(hc);animation=W.BOOL()
            self.assertTrue(user.SystemParametersInfoW(0x42,C.sizeof(hc),C.byref(hc),0))
            self.assertTrue(user.SystemParametersInfoW(0x1042,0,C.byref(animation),0))
            self.assertEqual(list(words)[:3],[1,int(bool(hc.flags&1)),int(not animation.value)])
            user.GetSysColor.restype=W.DWORD
            for offset,index in enumerate([5,8,15,18,17,13,14],3):
                color=user.GetSysColor(index);rgba=((color&255)<<24)|(((color>>8)&255)<<16)|(((color>>16)&255)<<8)|255
                self.assertEqual(words[offset],rgba)
            user.SendMessageW(hwnd,0x0015,0,0);self.assertEqual(dll.assisp_poll(token,0,words,10),0);self.assertEqual(words[1],12)
            user.SendMessageW(hwnd,0x0005,1,0);self.assertEqual(dll.assisp_poll(token,0,words,10),0);self.assertEqual((words[1],words[5]),(13,0))
            import threading
            results=[];thread=threading.Thread(target=lambda:results.append(dll.assisp_preferences(token,words,10)));thread.start();thread.join()
            self.assertEqual(results,[-5])
        finally:self.assertEqual(dll.assisp_close(token),0)
        self.assertEqual(dll.assisp_preferences(token,words,10),-2)
        self.assertEqual(list(words),[0]*10)

    @unittest.skipUnless(os.name=='nt','Windows integrated application unsupported')
    def test_integrated_example_toggle_preferences_visibility_resize_and_close(self):
        user=C.WinDLL('user32');callback=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
        user.EnumWindows.argtypes=[callback,W.LPARAM];user.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
        user.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
        user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
        user.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            output=self.temp/(mode+'.stdout');binary=self.temp/(mode+'.exe')
            built=self.invoke('build',base.ROOT/'exemplos/46_reader_transactions.assis','-o',binary,*flags)
            self.assertEqual(built.returncode,0,built.stderr)
            with output.open('wb') as stream:
                process=subprocess.Popen([binary],stdout=stream,stderr=subprocess.PIPE)
                try:
                    targets=[];deadline=time.monotonic()+10
                    @callback
                    def visit(hwnd,unused):
                        pid=W.DWORD();user.GetWindowThreadProcessId(hwnd,C.byref(pid))
                        name=C.create_unicode_buffer(128);user.GetClassNameW(hwnd,name,128)
                        if pid.value==process.pid and name.value=='AssisPlatformV1':targets.append(hwnd)
                        return True
                    while time.monotonic()<deadline:
                        targets.clear();user.EnumWindows(visit,0)
                        if len(targets)==1 and b'TRANSACTION 1 3' in output.read_bytes():break
                        time.sleep(.02)
                    self.assertEqual(len(targets),1,output.read_bytes());hwnd=targets[0]
                    oracle=reader.HtdlReader.build_oracle(self)
                    external=subprocess.run([oracle,'--transaction-client',str(hwnd)],capture_output=True,timeout=15)
                    self.assertEqual((external.returncode,external.stderr),(0,b''),external.stderr)
                    self.assertIn(b'TRANSACTION 3 3',output.read_bytes())
                    for key in (9,13):self.assertTrue(user.PostMessageW(hwnd,0x100,key,0));self.assertTrue(user.PostMessageW(hwnd,0x101,key,0))
                    deadline=time.monotonic()+10
                    while b'TRANSACTION 4 4' not in output.read_bytes() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertIn(b'TRANSACTION 4 4',output.read_bytes())
                    self.assertTrue(user.PostMessageW(hwnd,0x0015,0,0))
                    self.assertTrue(user.PostMessageW(hwnd,0x0005,1,0))
                    self.assertTrue(user.PostMessageW(hwnd,0x0005,0,(520<<16)|780))
                    self.assertTrue(user.SetWindowPos(hwnd,None,0,0,680,420,0x16))
                    self.assertTrue(user.PostMessageW(hwnd,0x100,13,0));self.assertTrue(user.PostMessageW(hwnd,0x101,13,0))
                    deadline=time.monotonic()+10
                    while b'TRANSACTION 5 3' not in output.read_bytes() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertIn(b'TRANSACTION 5 3',output.read_bytes())
                    self.assertTrue(user.PostMessageW(hwnd,0x10,0,0));_,errors=process.communicate(timeout=10)
                    self.assertEqual((process.returncode,errors),(0,b''))
                finally:
                    if process.poll() is None:process.kill();process.wait()
                    process.stderr.close()

if __name__=='__main__':unittest.main(verbosity=2)

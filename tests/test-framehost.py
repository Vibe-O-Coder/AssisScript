"""Atomic local HTDL/FS/SSC/reading bundle; no implicit resource authority."""
import importlib.util
import os
import subprocess
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('fr',Path(__file__).with_name('test-framereader.py'))
fr=importlib.util.module_from_spec(spec);spec.loader.exec_module(fr)
frame=fr.frame;base=fr.base
DOC=frame.fs.literal(frame.fs.catalog.document('<div type=paragraph>abcd</div><div type=button id=b>Go</div>'))
FS=frame.fs.literal('flow B{8px -> target.offsetX;}bind #b to B;')
SSC=frame.fs.literal('motion B{spring(target:fs.target.offsetX,frequency:4Hz,dampingRatio:0.8)->presentation.offsetX;}bind #b to B;')

def setup():return 'own s:framehost::Session=try_new framehost::Session(8000000,4000,7);assert(s!=null && s.is_open());'
def prepare(instance=1,request=1,doc=DOC,fs=FS,ssc=SSC,version='framehost::versions()',metric='metric',width=320):
    return f's.prepare({instance},{request},{version},{doc},{fs},{ssc},{width},200,65536,reader::default_preferences(),{metric})'

class FrameHost(unittest.TestCase):
    setUpClass=classmethod(fr.FrameReader.setUpClass.__func__)
    tearDownClass=classmethod(fr.FrameReader.tearDownClass.__func__)
    setUp=fr.FrameReader.setUp
    invoke=fr.FrameReader.invoke
    source=base.Evolution.source
    accepted=base.Evolution.accepted
    fault_program=frame.PageFrame.fault_program
    def execute(self,body,prefix=''):
        self.accepted(frame.PREFIX+'import "std/framehost.assis";'+fr.EVENT+prefix+'safe fn main():int{'+body+'return 0;}')

    def test_bundle_commit_and_headless_reading_share_one_revision(self):
        self.execute(setup()+f'assert({prepare()}==0 && s.has_pending() && !s.has_active());'
            'assert(!s.commit(2));assert(s.commit(1));assert(!s.has_pending() && s.has_active());'
            'assert(s.snapshot().frame.version()==1 && s.snapshot().reading.version()==1);'
            'assert(s.snapshot().frame.box(2).bounds.x==8);'
            'assert(s.dispatch(1,ev(3,17,1,1)).kind==0);assert(s.dispatch(1,ev(3,65,1,2)).kind==1);'
            'assert(len(s.snapshot().reading.selected_text())==7);s.close();assert(!s.is_open());')

    def test_htdl_fs_ssc_version_and_frame_failures_preserve_active(self):
        body=setup()+f'assert({prepare()}==0);assert(s.commit(1));'
        cases=[(frame.fs.literal('bad'),FS,SSC,'framehost::versions()','metric',102),
               (DOC,frame.fs.literal('bad'),SSC,'framehost::versions()','metric',102),
               (DOC,FS,frame.fs.literal('bad'),'framehost::versions()','metric',101),
               (DOC,FS,SSC,'new framehost::Versions(1,2,1)','metric',200),
               (DOC,FS,SSC,'framehost::versions()','bad_metric',304)]
        for i,(doc,fs,ssc,version,metric,code) in enumerate(cases,2):
            body+=f'assert({prepare(i,i,doc,fs,ssc,version,metric)}=={code});assert(!s.has_pending() && s.document().instance()==1 && s.snapshot().frame.version()==1);'
        self.execute(body)

    def test_busy_abort_old_request_and_instance_are_not_reused(self):
        self.execute(setup()+f'assert({prepare()}==0);assert({prepare(2,2)}==407);'
            'assert(!s.abort(2) && s.abort(1));'+f'assert({prepare(2,1)}==204);'
            f'assert({prepare(1,2)}!=0);assert({prepare(3,3)}==0);assert(s.commit(3));'
            'assert(s.document().instance()==3 && s.snapshot().frame.version()==1);')

    def test_pending_navigation_freezes_events_abort_restores_previous(self):
        self.execute(setup()+f'assert({prepare()}==0);assert(s.commit(1));assert({prepare(2,2)}==0);'
            'assert(s.dispatch(1,ev(3,17,1,1)).kind==0);assert(s.dispatch(1,ev(3,65,1,2)).kind==0);'
            'assert(s.abort(2));assert(s.dispatch(1,ev(3,17,1,1)).kind==0);assert(s.dispatch(1,ev(3,65,1,2)).kind==1);')

    def test_reflow_selection_zoom_scroll_abort_and_stale_frame(self):
        self.execute(setup()+f'assert({prepare()}==0);assert(s.commit(1));'
            's.dispatch(1,ev(3,17,1,1));s.dispatch(1,ev(3,65,1,2));'
            'assert(s.reflow(100,40,12,131072,25,true,reader::default_preferences(),metric)==0);'
            'assert(s.snapshot().frame.version()==1);s.abort_reflow();'
            'assert(s.reflow(100,40,12,131072,25,true,reader::default_preferences(),metric)==0);'
            'assert(s.commit_reflow());assert(s.snapshot().frame.version()==2 && len(s.snapshot().reading.selected_text())==7);'
            'assert(s.dispatch(1,ev(3,65,1,3)).kind==0);'
            'assert(s.dispatch(2,ev(3,67,1,3)).kind==4);')

    def test_gesture_freezes_timer_until_explicit_cancel_or_release(self):
        self.execute(setup()+f'assert({prepare()}==0);assert(s.commit(1));'
            's.dispatch(1,ev(7,0,2,1));assert(s.snapshot().reading.gesture_active());'
            'assert(s.reflow(320,200,0,65536,25,true,reader::default_preferences(),metric)==407);'
            's.cancel_gesture();assert(s.reflow(320,200,0,65536,25,true,reader::default_preferences(),metric)==0);'
            'assert(s.commit_reflow() && !s.snapshot().reading.gesture_active());')

    def test_navigation_never_carries_selection_or_old_semantic_handles(self):
        self.execute(setup()+f'assert({prepare()}==0);assert(s.commit(1));'
            'val old:doctree::NodeId=s.snapshot().frame.box(2).node;'
            's.dispatch(1,ev(3,17,1,1));s.dispatch(1,ev(3,65,1,2));'+f'assert({prepare(2,2)}==0);assert(s.commit(2));'
            'assert(len(s.snapshot().reading.selected_text())==0 && !s.document().nodes().contains(old));'
            'assert(s.dispatch(1,ev(3,65,1,3)).kind==0);')

    def test_repaint_retains_held_control_for_subsequent_explicit_copy(self):
        self.execute(setup()+f'assert({prepare()}==0);assert(s.commit(1));'
            's.dispatch(1,ev(3,17,1,1));s.dispatch(1,ev(3,65,1,2));'
            'assert(s.reflow(320,200,0,65536,0,true,reader::default_preferences(),metric)==0);assert(s.commit_reflow());'
            'assert(s.dispatch(2,ev(3,67,1,3)).kind==4);')

    def test_reading_example_and_five_generated_formats_are_separate_from_execution(self):
        source=base.ROOT/'exemplos/60_frame_reader.assis'
        for flags in ([],['--no-opt']):
            r=self.invoke('run',source,'--debug',*flags);self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'FRAME READER 1 7\n',''))
            for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                r=self.invoke('build',source,'--target',target,'-o',self.temp/target,*flags);self.assertEqual(r.returncode,0,r.stderr)

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_real_font_window_selects_reflows_presents_and_closes(self):
        for index,flags in enumerate(([],['--no-opt'])):
            binary=self.temp/f'reading-{index}.exe'
            r=self.invoke('build',base.ROOT/'exemplos/61_frame_reader_window.assis','--debug','-o',binary,*flags);self.assertEqual(r.returncode,0,r.stderr)
            for option,revision in (('--once',1),('--smoke',2)):
                r=subprocess.run([binary,option],cwd=self.temp,capture_output=True,text=True,timeout=30)
                self.assertEqual((r.returncode,r.stdout,r.stderr),(0,f'READING FRAME {revision} 6\n',''))

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_native_bundle_failure_and_accessibility_replay(self):
        self.execute(setup()+f'assert({prepare()}==0);'
            'own w:window::Window=try_new window::Window(7,320,200,utf8("Local bundle"));assert(w!=null && w.opened());'
            'assert(s.publish(1,w)==0);assert(s.dispatch(1,ev(11,1,2,1)).kind==2);'
            'assert(s.dispatch(1,ev(11,1,2,1)).kind==0);'
            'assert(s.dispatch(1,new window::Event(0,11,7,2,1,2,2)).kind==0);'+f'assert({prepare(2,2)}==0);'
            'unsafe{control(0,0);}assert(s.publish(2,w)== -4);unsafe{control(0,-1);}'
            'assert(s.document().instance()==1 && s.snapshot().frame.version()==1);assert(s.abort(2));'
            'assert(s.dispatch(1,ev(11,1,2,2)).kind==2);'+f'assert({prepare(3,3)}==0);assert(s.publish(3,w)==0);'
            'assert(s.dispatch(1,ev(11,1,2,3)).kind==0);assert(w.close()==0);',
            prefix='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(op:int,arg:int):int;')

    def test_os_refusal_during_bundle_preparation_conserves_active_and_neighbor(self):
        for allowance in (0,1,2,4,8):
            warm,drain,cleanup=frame.fs.bootstrap.preparation.exhaustion(allowance)
            body=setup()+f'assert({prepare()}==0);assert(s.commit(1));'
            body+='own neighbor:documents::Store=try_new documents::Store(100000,1000,10);'+f'assert(htdl::load(neighbor,7,{DOC}).code==0);'
            body+='unsafe{'+warm+drain+f'val code:int={prepare(2,2)};'
            body+='if(code==0){assert(s.abort(2));}else{assert(code==401 || code==403);}'
            body+='assert(s.document().instance()==1 && s.snapshot().frame.version()==1 && !s.has_pending());'
            body+='assert(neighbor.active_document().is_open());'+cleanup+'}'
            self.fault_program(frame.PREFIX+'import "std/framehost.assis";safe fn main():int{'+body+'return 0;}','')

if __name__=='__main__':unittest.main(verbosity=2)

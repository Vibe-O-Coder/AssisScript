"""Composed reading geometry, independent byte ranges, stale events and rollback."""
import importlib.util
import os
from pathlib import Path
import random
import re
import unittest

spec=importlib.util.spec_from_file_location('present',Path(__file__).with_name('test-pagepresent.py'))
present=importlib.util.module_from_spec(spec);spec.loader.exec_module(present)
frame=present.frame;base=present.base

def reading():
    return ('own r:framereader::Reader=try_new framereader::Reader(frame,store.candidate(),7,20000000,metric);'
            'assert(r!=null && r.is_open() && r.status()==0);')

class FrameReader(unittest.TestCase):
    setUpClass=classmethod(present.PagePresent.setUpClass.__func__)
    tearDownClass=classmethod(present.PagePresent.tearDownClass.__func__)
    setUp=present.PagePresent.setUp
    invoke=present.PagePresent.invoke
    source=base.Evolution.source
    accepted=base.Evolution.accepted
    fault_program=frame.PageFrame.fault_program
    def execute(self,body,prefix=''):
        code=frame.PREFIX+'import "std/pagepresent.assis";'+prefix+'safe fn main():int{'+body+'return 0;}'
        # Statement lines locate failed assertions without changing literals.
        code=re.sub(r'("(?:\\.|[^"\\])*")|;',lambda m:m[0] if m[1] else ';\n',code)
        self.accepted(code)

    def test_reading_order_soft_wraps_labels_hidden_and_copied_text(self):
        body=(frame.setup('<div type=heading level=1>Título</div>'
            '<div type=paragraph>abcdefghi</div><div type=button a11y-label=Label>Go</div>'
            '<div type=paragraph hidden=true>SECRET</div>',width=48)+reading()+
            'print(r.text_bytes());assert(r.select(frame,store.candidate(),0,len(r.text_bytes())));'
            'print(r.selected_text());store.close();print(r.text_bytes());')
        self.accepted(frame.PREFIX+'import "std/framereader.assis";safe fn main():int{'+body+'return 0;}',
            'Título\nabcdefghi\nGo\n'*3)

    def test_unicode_selection_against_independent_grapheme_ranges(self):
        clusters=['A','ç','ã','o',' ','c','a','f','e\u0301',' ','👩\u200d💻',' ','🇧🇷']
        text=''.join(clusters);model=text.encode();bounds=[0]
        for c in clusters:bounds.append(bounds[-1]+len(c.encode()))
        rng=random.Random(20261103);body=frame.setup('<div type=paragraph>'+text+'</div>',width=160)+reading();output=''
        for _ in range(30):
            a,b=rng.sample(bounds,2);body+=f'assert(r.select(frame,store.candidate(),{a},{b}));print(r.selected_text());'
            output+=model[min(a,b):max(a,b)].decode()+'\n'
        for i in range(len(model)+1):
            if i not in bounds:body+=f'assert(!r.select(frame,store.candidate(),{i},0));'
        body+='assert(!r.select(frame,store.candidate(),-1,0) && !r.select(frame,store.candidate(),0,9223372036854775807));'
        self.accepted(frame.PREFIX+'import "std/framereader.assis";safe fn main():int{'+body+'return 0;}',output)

    def test_selection_rectangle_uses_aligned_composed_clipped_run(self):
        source='flow P{64px -> layout.width;24px -> layout.height;center -> text.align;12px -> target.offsetX;clip -> layout.overflow;}bind #p to P;'
        self.execute(frame.setup('<div type=paragraph id=p>abcd</div>',source,width=60)+reading()+
            'assert(r.select(frame,store.candidate(),1,4));val h:pageframe::Rect=r.highlight(frame,0);'
            'assert(h.x==36 && h.y==0 && h.width==24 && h.height==16);'
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(frame,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'val count:int=packet.command_count();assert(packet.highlight(frame,store.candidate(),r,reader::default_preferences())==0);'
            'assert(packet.command_count()==count+2 && packet.highlight(frame,store.candidate(),r,reader::default_preferences())==204);')

    def test_soft_wrap_terminal_width_is_distinct_from_next_run_zero(self):
        self.execute(frame.setup('<div type=paragraph>abcdef</div>',width=16)+reading()+
            'assert(frame.run_count()==3);assert(r.select(frame,store.candidate(),0,6));'
            'assert(r.highlight(frame,0).width==16 && r.highlight(frame,1).width==16 && r.highlight(frame,2).width==16);'
            'r.dispatch(frame,store.candidate(),1,ev(7,15,2,1));assert(r.selection_end()==2);'
            'r.dispatch(frame,store.candidate(),1,ev(8,0,18,2));assert(r.selection_start()==2 && r.selection_end()==2);',prefix=EVENT)

    def test_pointer_keyboard_focus_press_release_copy_zoom_and_capture_loss(self):
        self.execute(frame.setup('<div type=paragraph>abcd</div><div type=button id=b>Go</div>')+reading()+
            'assert(r.dispatch(frame,store.candidate(),1,ev(7,0,2,1)).kind==1);'
            'r.dispatch(frame,store.candidate(),1,ev(4,24,2,2));r.dispatch(frame,store.candidate(),1,ev(8,24,2,3));'
            'assert(len(r.selected_text())==3 && !r.gesture_active());'
            'r.dispatch(frame,store.candidate(),1,ev(3,16,1,4));r.dispatch(frame,store.candidate(),1,ev(3,39,1,5));'
            'assert(len(r.selected_text())==4);r.dispatch(frame,store.candidate(),1,ev(3,16,0,6));'
            'r.dispatch(frame,store.candidate(),1,ev(3,17,1,7));assert(r.dispatch(frame,store.candidate(),1,ev(3,67,1,8)).kind==4);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,187,1,9)).kind==5);'
            'r.dispatch(frame,store.candidate(),1,ev(10,0,0,10));assert(r.dispatch(frame,store.candidate(),1,ev(3,67,1,11)).kind==0);'
            'r.dispatch(frame,store.candidate(),1,ev(3,9,1,12));assert(pageframe::same(r.focus_node(),frame.box(2).node));'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,13,1,13)).kind==2);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,13,0,14)).kind==0);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(7,1,17,15)).kind==1);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(8,1,17,16)).kind==2);',prefix=EVENT)

    def test_stale_projection_generation_request_and_semantic_mutation_are_refused(self):
        self.execute(frame.setup('<div type=paragraph>abcd</div><div type=button id=b>Go</div>')+reading()+
            'assert(r.dispatch(frame,store.candidate(),2,ev(3,17,1,100)).kind==0);'
            'r.dispatch(frame,store.candidate(),1,ev(3,17,1,1));'
            'assert(r.dispatch(frame,store.candidate(),1,new window::Event(0,3,7,2,65,1,2)).kind==0);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,65,1,1)).kind==0);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,65,1,2)).kind==1 && len(r.selected_text())==7);'
            'assert(store.candidate().erase_subtree(frame.box(2).node));'
            'assert(!r.current(frame,store.candidate()) && !r.select(frame,store.candidate(),0,1));'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,67,1,3)).kind==0);',prefix=EVENT)

    def test_reflow_restores_reading_offsets_but_cancels_gestures_and_modifiers(self):
        self.execute(frame.setup('<div type=paragraph>abcdefghijkl</div><div type=button>Go</div>',width=48)+reading()+
            'r.select(frame,store.candidate(),2,10);r.dispatch(frame,store.candidate(),1,ev(3,17,1,1));'
            'own next:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,160,200,0,131072,10000000,metric);'
            'own next_r:framereader::Reader=try_new framereader::Reader(next,store.candidate(),7,20000000,metric);'
            'assert(next_r!=null && next_r.is_open());assert(next_r.restore(next,store.candidate(),r));'
            'assert(next_r.selection_start()==2 && next_r.selection_end()==10 && !next_r.gesture_active());'
            'assert(next_r.dispatch(next,store.candidate(),2,ev(3,67,1,2)).kind==0);'
            'assert(next_r.dispatch(next,store.candidate(),2,ev(3,17,1,1)).kind==0);',prefix=EVENT)

    def test_overlapping_disabled_button_occludes_text_selection_and_activation(self):
        self.execute(frame.setup('<div type=paragraph>abcd</div><div type=button id=b disabled=true>Block</div>',
            'flow B{-16px -> target.offsetY;}bind #b to B;')+reading()+
            'assert(r.dispatch(frame,store.candidate(),1,ev(7,8,2,1)).kind==0);'
            'assert(!r.gesture_active() && len(r.selected_text())==0);'
            'assert(r.dispatch(frame,store.candidate(),1,ev(8,8,2,2)).kind==0);',prefix=EVENT)

    def test_metric_failure_and_budget_keep_previous_reader_usable(self):
        self.execute(frame.setup('<div type=paragraph>abcd</div>')+reading()+
            'assert(r.select(frame,store.candidate(),1,3));'
            'own bad:framereader::Reader=try_new framereader::Reader(frame,store.candidate(),7,20000000,bad_metric);'
            'assert(bad!=null && !bad.is_open() && bad.status()==304);'
            'own small:framereader::Reader=try_new framereader::Reader(frame,store.candidate(),7,1,metric);'
            'assert(small!=null && !small.is_open() && small.status()==401);'
            'assert(r.current(frame,store.candidate()) && len(r.selected_text())==2);')

    def test_empty_document_and_empty_buttons_have_valid_zero_length_selection(self):
        for body in ('','<div type=button a11y-label=Empty></div>'):
            self.execute(frame.setup(body)+reading()+'assert(len(r.text_bytes())==0);assert(r.select(frame,store.candidate(),0,0));')

    def test_command_ceiling_rejects_large_selection_without_modifying_packet(self):
        source='flow Body{row(gap:0px) -> layout.children;}bind #body to Body;flow P{8px -> layout.width;}bind .p to P;'
        self.execute(frame.setup(('<div type=paragraph class=p>'+'x'*100+'</div>')*120,source,width=960,height=1600)+reading()+
            'assert(frame.run_count()==12000);assert(r.select(frame,store.candidate(),0,len(r.text_bytes())));'
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(frame,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(packet!=null && packet.is_open());val count:int=packet.command_count();'
            'assert(packet.highlight(frame,store.candidate(),r,reader::default_preferences())==401 && packet.command_count()==count);')

    def test_os_refusal_during_reader_preparation_conserves_selection(self):
        for allowance in (0,1,2,4,8):
            warm,drain,cleanup=frame.fs.bootstrap.preparation.exhaustion(allowance)
            body=frame.setup('<div type=paragraph>abcd</div>')+reading()+'assert(r.select(frame,store.candidate(),1,3));'
            body+='unsafe{'+warm+drain+'own next:framereader::Reader=try_new framereader::Reader(frame,store.candidate(),7,20000000,metric);'
            if allowance==0:body+='assert(next==null || !next.is_open());'
            body+='assert(r.current(frame,store.candidate()) && len(r.selected_text())==2);'+cleanup+'}'
            self.fault_program(frame.PREFIX+'import "std/framereader.assis";safe fn main():int{'+body+'return 0;}','')

    @unittest.skipUnless(os.name=='nt','Windows native frame provider unavailable')
    def test_native_highlight_failure_keeps_previous_projection_then_retries(self):
        self.execute(frame.setup('<div type=paragraph>abcd</div><div type=button>Go</div>')+reading()+
            'own w:window::Window=try_new window::Window(7,320,200,utf8("Frame reading"));assert(w!=null && w.opened());'
            'own old:pagepresent::Packet=try_new pagepresent::Packet(frame,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(old.publish(w,frame,store.candidate())==0);'
            'own next:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'own next_r:framereader::Reader=try_new framereader::Reader(next,store.candidate(),7,20000000,metric);'
            'assert(next_r.select(next,store.candidate(),1,3));'
            'own packet:pagepresent::Packet=try_new pagepresent::Packet(next,new doctree::NodeId(),reader::default_preferences(),10000000);'
            'assert(packet.highlight(next,store.candidate(),next_r,reader::default_preferences())==0);'
            'unsafe{control(0,0);}assert(packet.publish(w,next,store.candidate())== -4);unsafe{control(0,-1);}'
            'assert(pageframe::same(old.action(frame,store.candidate(),1,2),frame.box(2).node));'
            'assert(packet.publish(w,next,store.candidate())==0 && w.present()==0);'
            'assert(doctree::absent(old.action(frame,store.candidate(),1,2)));assert(w.close()==0);',
            prefix='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(op:int,arg:int):int;')

    def test_ssc_displacement_is_applied_once_to_selection_and_packet(self):
        motion=present.module('motion',Path(__file__).with_name('test-motionpage.py'))
        body=motion.setup()+motion.prepare()+motion.commit()+motion.target(8*65536)+motion.prepare(25)
        body+='own next:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);assert(next.compose(store.candidate(),motion)==0);'
        body+='own r:framereader::Reader=try_new framereader::Reader(next,store.candidate(),7,20000000,metric);assert(r!=null && r.is_open());'
        body+='assert(r.select(next,store.candidate(),0,1));val h:pageframe::Rect=r.highlight(next,0);'
        body+='assert(h.x==next.run(0).bounds.x && h.x>0 && h.y==next.run(0).bounds.y);'
        body+='assert(next.compose(store.candidate(),motion)==204);motion.abort();'
        self.execute(body)

EVENT='safe fn ev(kind:int,a:int,b:int,request:int):window::Event{return new window::Event(0,kind,7,1,a,b,request);}'
if __name__=='__main__':unittest.main(verbosity=2)

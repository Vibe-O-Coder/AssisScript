"""Reading catalog, independent list/fragment models and native ABI boundaries."""
import importlib.util
import os
from pathlib import Path
import random
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('host',Path(__file__).with_name('test-framehost.py'))
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
frame=host.frame;literal=frame.fs.literal;document=frame.fs.catalog.document;base=host.base

def prepare(body,fs='',instance=1,request=1,width=320,height=200,head=None,version='framehost::reading_versions()'):
    return (f's.prepare({instance},{request},{version},{literal(document(body,head))},{literal(fs)},utf8(""),'
            f'{width},{height},65536,reader::default_preferences(),metric)')

def start(body,fs='',**kwargs):return host.setup()+f'assert({prepare(body,fs,**kwargs)}==0);assert(s.commit(1));'

class CatalogFrame(unittest.TestCase):
    setUpClass=classmethod(host.FrameHost.setUpClass.__func__)
    tearDownClass=classmethod(host.FrameHost.tearDownClass.__func__)
    setUp=host.FrameHost.setUp
    invoke=host.FrameHost.invoke
    source=base.Evolution.source
    accepted=base.Evolution.accepted
    fault_program=host.FrameHost.fault_program
    execute=host.FrameHost.execute

    def test_explicit_reading_profile_and_arbitrary_valid_head_order(self):
        body='<div type=main><div type=section a11y-label=Region><div type=paragraph>Text</div></div></div>'
        code=host.setup()+f'assert({prepare(body,version="framehost::versions()")}==203);'
        head='<div type=meta name=description content=Info></div><div type=title>Right title</div>'
        code+=f'assert({prepare(body,instance=2,request=2,head=head)}==0);assert(s.commit(2));'
        code+='assert(len(s.snapshot().frame.title())==11 && s.snapshot().frame.title()[0]==82 && s.snapshot().frame.size()==4);'
        self.execute(code)

    def test_all_structural_reading_types_keep_semantic_order(self):
        body=('<div type=header><div type=paragraph>Header</div></div>'
              '<div type=nav a11y-label=Contents><div type=link href="#end">Jump</div></div>'
              '<div type=main><div type=section><div type=list><div type=item><div type=paragraph>Item</div></div></div></div></div>'
              '<div type=footer id=end><div type=paragraph>Footer</div></div>')
        self.execute(start(body)+'assert(s.snapshot().frame.size()==12);'
            'assert(s.snapshot().packet.item_count()==12);assert(len(s.snapshot().reading.text_bytes())==23);'
            'assert(s.snapshot().frame.box(3).kind==16 && s.snapshot().frame.box(4).kind==17);'
            'assert(s.snapshot().frame.box(8).kind==19 && s.snapshot().frame.marker(8)[0]==226);')

    def test_numbered_markers_and_geometry_against_independent_stack_model(self):
        body='<div type=list ordered=true>'+''.join(f'<div type=item><div type=paragraph>{i}</div></div>' for i in range(1,105))+'</div>'
        code=start(body,height=16384)
        for i in range(1,105):
            item=2+2*(i-1);mark=str(i)+'.';indent=len(mark)*8+8
            code+=f'assert(len(s.snapshot().frame.marker({item}))=={len(mark)});'
            for j,b in enumerate(mark.encode()):code+=f'assert(s.snapshot().frame.marker({item})[{j}]=={b});'
            code+=f'assert(s.snapshot().frame.box({item}).bounds.y=={(i-1)*16} && s.snapshot().frame.box({item+1}).bounds.x=={indent});'
        code+='assert(s.snapshot().frame.box(0).bounds.height==1664);'
        self.execute(code)

    def test_hidden_items_do_not_consume_ordinal_or_copy_marker_bytes(self):
        body=('<div type=list ordered=true><div type=item><div type=paragraph>A</div></div>'
              '<div type=item hidden=true><div type=paragraph>SECRET</div></div>'
              '<div type=item><div type=paragraph>B</div><div type=list><div type=item><div type=paragraph>C</div></div></div></div></div>')
        self.execute(start(body)+'assert(s.snapshot().frame.marker(4)[0]==50 && s.snapshot().frame.marker(7)[0]==226);'
            'assert(len(s.snapshot().reading.text_bytes())==5 && s.snapshot().reading.text_bytes()[2]==66);'
            'assert(s.snapshot().frame.box(8).bounds.x==56);')

    def test_fragment_target_can_be_offscreen_inline_or_structural(self):
        body=('<div type=link id=l href="#target">Jump</div><div type=container id=spacer></div>'
              '<div type=section><div type=paragraph>A<div type=text id=target>B</div></div></div>')
        self.execute(start(body,'flow Gap{400px -> layout.height;}bind #spacer to Gap;')+
            'val link:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("l"));'
            'assert(s.fragment_scroll(1,link)==232 && s.fragment_scroll(2,link)== -1);'
            'assert(s.reflow(320,200,232,65536,0,true,reader::default_preferences(),metric)==0);assert(s.commit_reflow());'
            'assert(s.fragment_scroll(2,link)==232 && s.snapshot().frame.scroll_y()==232);')

    def test_hidden_fragment_target_is_valid_but_never_scrolled_or_focused(self):
        body='<div type=link id=l href="#x">Jump</div><div type=section hidden=true id=x><div type=paragraph>Secret</div></div>'
        self.execute(start(body)+'val link:doctree::NodeId=s.snapshot().frame.box(1).node;'
            'assert(s.fragment_scroll(1,link)== -1);assert(s.snapshot().frame.size()==2);')

    def test_unsupported_resources_live_hints_and_missing_fragments_preserve_active(self):
        cases=[('<div type=link href="other.htdl">Open</div>',None,203),
               ('<div type=link href="https://example.test/">Open</div>',None,203),
               ('<div type=link href="#missing">Open</div>',None,207),
               ('<div type=section hidden=true><div type=image src="image.png" alt=Picture></div></div>',None,203),
               ('<div type=input a11y-label=Input></div>',None,203),
               ('<div type=form><div type=input a11y-label=Input></div></div>',None,203),
               ('<div type=paragraph a11y-live=polite>Live</div>',None,203),
               ('<div type=paragraph>Static</div>','<div type=title>Title</div><div type=script src="x.assis" format=source></div>',203)]
        code=start('<div type=paragraph>Active</div>')
        for i,(body,head,status) in enumerate(cases,2):
            code+=f'assert({prepare(body,instance=i,request=i,head=head)}=={status});'
            code+='assert(!s.has_pending() && s.document().instance()==1 && s.snapshot().frame.version()==1);'
        self.execute(code)

    def test_link_enter_once_space_scrolls_and_button_space_releases_once(self):
        body='<div type=link href="#tail">Jump</div><div type=button>Button</div><div type=container id=tail></div>'
        code=start(body,'flow Tall{600px -> layout.height;}bind #tail to Tall;')
        events=[(9,1,1),(13,1,8),(13,1,0),(13,0,0),(32,1,7),(32,1,0),(32,0,0),
                (9,1,1),(13,1,2),(13,1,0),(13,0,0),(32,1,0),(32,1,0),(32,0,2),(32,0,0)]
        for req,(key,down,result) in enumerate(events,1):code+=f'assert(s.dispatch(1,ev(3,{key},{down},{req})).kind=={result});'
        code+='assert(s.snapshot().reading.scroll_target()==100 && !s.snapshot().reading.gesture_active());'
        self.execute(code)

    def test_repaint_while_enter_is_held_does_not_repeat_activation(self):
        body='<div type=link href="#tail">Jump</div><div type=paragraph id=tail>Tail</div>'
        self.execute(start(body)+'s.dispatch(1,ev(3,9,1,1));assert(s.dispatch(1,ev(3,13,1,2)).kind==8);'
            'assert(s.reflow(320,200,0,65536,0,true,reader::default_preferences(),metric)==0);assert(s.commit_reflow());'
            'assert(s.dispatch(2,ev(3,13,1,3)).kind==0);assert(s.dispatch(2,ev(3,13,0,4)).kind==0);'
            'assert(s.dispatch(2,ev(3,13,1,5)).kind==8);')

    def test_pointer_link_activation_and_requests_revalidate_snapshot(self):
        body='<div type=link href="#tail">Jump</div><div type=paragraph id=tail>Tail</div>'
        self.execute(start(body)+'assert(s.dispatch(1,ev(7,1,1,1)).kind==1);'
            'assert(s.dispatch(1,ev(8,1,1,2)).kind==8);assert(s.dispatch(1,ev(8,1,1,2)).kind==0);'
            'assert(s.dispatch(2,ev(7,1,1,3)).kind==0);'
            'val link:doctree::NodeId=s.snapshot().frame.box(1).node;'+
            f'assert({prepare(body,instance=2,request=2)}==0);assert(s.commit(2));'
            'assert(s.fragment_scroll(2,link)== -1 && s.dispatch(1,ev(7,1,1,3)).kind==0);')

    def test_tree_mutation_revokes_fragment_focus_and_old_reading_projection(self):
        body='<div type=link id=jump href="#target">Jump</div><div type=paragraph id=target>Target</div>'
        self.execute(frame.setup(body)+host.fr.reading()+
            'val link:doctree::NodeId=frame.box(1).node;val target:doctree::NodeId=frame.box(2).node;'
            'assert(frame.fragment_scroll(store.candidate(),link)==0);assert(store.candidate().erase_subtree(target));'
            'assert(!frame.current(store.candidate()) && !r.current(frame,store.candidate()));'
            'assert(frame.fragment_scroll(store.candidate(),link)== -1);'
            'assert(doctree::absent(frame.next_focus(store.candidate(),link,false)));'
            'assert(doctree::absent(frame.hit(store.candidate(),1,1,1)));'
            'assert(r.dispatch(frame,store.candidate(),1,ev(3,13,1,1)).kind==0);')

    def test_keyboard_and_pointer_gestures_do_not_complete_each_other(self):
        self.execute(start('<div type=button id=a>A</div><div type=button id=b>B</div>')+
            's.dispatch(1,ev(3,9,1,1));s.dispatch(1,ev(3,32,1,2));'
            'assert(s.dispatch(1,ev(8,1,1,3)).kind==0);'
            'assert(s.dispatch(1,ev(3,32,0,4)).kind==2);'
            's.dispatch(1,ev(3,32,1,5));s.dispatch(1,ev(7,1,17,6));'
            'assert(s.dispatch(1,ev(3,32,0,7)).kind==0);'
            'assert(s.dispatch(1,ev(8,1,17,8)).kind==2);')

    def test_list_wrapping_indents_before_text_measurement_and_zoom(self):
        body='<div type=list ordered=true><div type=item><div type=paragraph>abcdefgh</div></div></div>'
        self.execute(start(body,width=56)+'assert(s.snapshot().frame.run_count()==2 && s.snapshot().frame.box(3).bounds.width==32);'
            'assert(s.reflow(112,200,0,131072,0,true,reader::default_preferences(),metric)==0);assert(s.commit_reflow());'
            'assert(s.snapshot().frame.box(3).bounds.x==48 && s.snapshot().frame.run_count()==2);')

    def test_item_clip_keeps_marker_and_child_content_in_one_inner_rectangle(self):
        body='<div type=list ordered=true><div type=item id=entry><div type=paragraph>abcdefgh</div></div></div>'
        self.execute(frame.setup(body,'flow Item{56px -> layout.width;clip -> layout.overflow;}bind #entry to Item;')+
            'assert(frame.box(3).bounds.x==24 && frame.box(3).bounds.width==32);'
            'assert(frame.box(3).clip.x==0 && frame.box(3).clip.width==56);'
            'assert(frame.accessible_bounds(3).width==32 && frame.content_clip(2).width==56);')

    def test_native_catalog_actions_and_failure_keep_previous_frame(self):
        if os.name!='nt':self.skipTest('Windows catalog provider unavailable')
        body='<div type=nav><div type=link href="#tail">Jump</div></div><div type=paragraph id=tail>Tail</div>'
        self.execute(host.setup()+f'assert({prepare(body)}==0);'
            'own w:window::Window=try_new window::Window(7,320,200,utf8("Catalog"));assert(w!=null && w.opened());'
            'assert(pagepresent::catalog_available() && s.publish(1,w)==0);'
            'assert(s.dispatch(1,ev(11,1,2,1)).kind==8);assert(s.dispatch(1,ev(11,1,1,2)).kind==0);'+
            f'assert({prepare(body,instance=2,request=2)}==0);'
            'unsafe{control(0,0);}assert(s.publish(2,w)== -4);unsafe{control(0,-1);}'
            'assert(s.document().instance()==1 && s.snapshot().frame.version()==1);assert(s.abort(2));'
            'assert(s.dispatch(1,ev(11,1,2,3)).kind==8);assert(w.close()==0);',
            prefix='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(op:int,arg:int):int;')

    def test_os_refusal_of_catalog_candidate_preserves_neighbor(self):
        body='<div type=link href="#tail">Jump</div><div type=list ordered=true><div type=item><div type=paragraph id=tail>Tail</div></div></div>'
        for allowance in (0,1,2,4,8):
            warm,drain,cleanup=frame.fs.bootstrap.preparation.exhaustion(allowance)
            code=start('<div type=paragraph>Old</div>')
            code+='own neighbor:documents::Store=try_new documents::Store(100000,1000,10);'
            code+=f'assert(htdl::load(neighbor,9,{literal(document("<div type=paragraph>Neighbor</div>"))}).code==0);'
            code+='unsafe{'+warm+drain+f'val code:int={prepare(body,instance=2,request=2)};'
            code+='if(code==0){assert(s.abort(2));}else{assert(code==401 || code==403);}'
            code+='assert(s.document().instance()==1 && s.snapshot().frame.version()==1 && neighbor.active_document().is_open());'+cleanup+'}'
            self.fault_program(frame.PREFIX+'import "std/framehost.assis";safe fn main():int{'+code+'return 0;}','')

    def test_seeded_hidden_list_matches_plain_text_and_ordinal_model(self):
        rng=random.Random(2026110309);body='<div type=list ordered=true>';visible=[]
        for i in range(36):
            hidden=rng.randrange(4)==0;value='Item'+str(i)
            body+=f'<div type=item'+(' hidden=true' if hidden else '')+f'><div type=paragraph>{value}</div></div>'
            if not hidden:visible.append(value)
        body+='</div>';code=start(body,width=320,height=1200)
        expected='\n'.join(visible).encode();code+=f'assert(len(s.snapshot().reading.text_bytes())=={len(expected)});'
        for i,b in enumerate(expected):code+=f'assert(s.snapshot().reading.text_bytes()[{i}]=={b});'
        for ordinal in range(1,len(visible)+1):
            item=2+(ordinal-1)*2;mark=str(ordinal)+'.'
            for i,b in enumerate(mark.encode()):code+=f'assert(s.snapshot().frame.marker({item})[{i}]=={b});'
            code+=f'assert(s.snapshot().frame.box({item}).bounds.y=={16*(ordinal-1)});'
        self.execute(code)

    def test_box_and_fragment_work_limits_preserve_previous_document(self):
        code=start('<div type=paragraph>Previous</div>')
        large='<div type=section></div>'*256
        code+=f'assert({prepare(large,instance=2,request=2)}==401);'
        # Nine scans of a near-1MiB document exceed the declared eight-million
        # source-byte charge, independently of how early a matching ID occurs.
        large='<div type=paragraph id=x>'+('a'*900000)+'</div>'+'<div type=link href="#x">X</div>'*9
        code+=f'assert({prepare(large,instance=3,request=3)}==401);'
        code+='assert(s.document().instance()==1 && !s.has_pending());'
        self.execute(code)

    def test_examples_use_both_modes_and_generate_all_five_formats(self):
        for flags in ([],['--no-opt']):
            r=self.invoke('run',base.ROOT/'exemplos/62_catalog_reader.assis','--debug',*flags)
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'CATALOG FRAME 1 10\n',''))
            for name in ('62_catalog_reader.assis','63_catalog_reader_window.assis'):
                for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                    r=self.invoke('build',base.ROOT/'exemplos'/name,'--target',target,'-o',self.temp/target,*flags)
                    self.assertEqual(r.returncode,0,r.stderr)

    @unittest.skipUnless(os.name=='nt','Windows catalog provider unavailable')
    def test_real_font_catalog_window_selects_reflows_and_closes(self):
        for index,flags in enumerate(([],['--no-opt'])):
            binary=self.temp/f'catalog-{index}.exe'
            r=self.invoke('build',base.ROOT/'exemplos/63_catalog_reader_window.assis','--debug','-o',binary,*flags)
            self.assertEqual(r.returncode,0,r.stderr)
            for option,revision in (('--once',1),('--smoke',2)):
                r=subprocess.run([binary,option],cwd=self.temp,capture_output=True,text=True,timeout=30)
                self.assertEqual((r.returncode,r.stdout,r.stderr),(0,f'CATALOG WINDOW {revision} 10\n',''))

    @unittest.skipUnless(os.name=='nt','Windows catalog provider unavailable')
    def test_independent_native_com_roles_actions_hits_revocation_and_allocation_rollback(self):
        cc='C:/msys64/ucrt64/bin/gcc.exe';binary=self.temp/'catalog-oracle.exe'
        command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Werror',str(base.ROOT/'tests/catalog_frame_oracle.c'),
                 '-o',str(binary),'-loleacc','-loleaut32','-lole32','-luuid','-luser32','-lgdi32']
        r=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,PATH=str(Path(cc).parent)+os.pathsep+os.environ['PATH']))
        self.assertEqual(r.returncode,0,r.stderr)
        r=subprocess.run([binary,self.provider],capture_output=True,text=True,timeout=30)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'PASS catalog roles actions hits revocation allocation rollback\n',''))

if __name__=='__main__':unittest.main(verbosity=2)

"""Independent rectangle/constraint models and transactional frame failures."""
import importlib.util
import json
import random
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('flowpage',Path(__file__).with_name('test-flowpage.py'))
flowpage=importlib.util.module_from_spec(spec);spec.loader.exec_module(flowpage)
fs=flowpage.fs;base=fs.base;literal=fs.literal
PREFIX='''import "std/pageframe.assis";
safe fn metric(borrow content:slice<byte>,size:int,weight:int):int{
    return (pageframe::pixels(size)<<32)+len(content)*pageframe::pixels(size)/2;
}
safe fn bad_metric(borrow content:slice<byte>,size:int,weight:int):int{return -4;}
'''

def setup(body,source='',width=320,height=200,scale=65536,scroll=0):
    doc=fs.catalog.document(body).replace('<div type="body">','<div type="body" id="body">')
    return (f'own store:documents::Store=try_new documents::Store(4000000,4000,100);assert(store!=null);'
            f'assert(htdl::stage_catalog(store,1,{literal(doc)},0).code==0);'
            f'own page:flowpage::Page=try_new flowpage::Page({literal(source)},256,2048,40000000);'
            'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);assert(page!=null && page.is_open() && input!=null);'
            'assert(page.refresh(store.candidate(),input)==0);'
            f'own frame:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,1,{width},{height},{scroll},{scale},10000000,metric);'
            'assert(frame!=null && frame.is_open());')

def rect(index,x,y,w,h):
    return (f'assert(frame.box({index}).bounds.x=={x} && frame.box({index}).bounds.y=={y} && '
            f'frame.box({index}).bounds.width=={w} && frame.box({index}).bounds.height=={h});')

class PageFrame(base.Evolution):
    fault_program=flowpage.FlowPage.fault_program
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)
    def execute(self,body):self.accepted(PREFIX+'safe fn main():int{'+body+'return 0;}')

    def test_column_padding_gaps_and_transforms_do_not_change_flow(self):
        source=('flow Body{10px -> layout.padding;column(gap:6px) -> layout.children;}bind #body to Body;'
                'flow First{100px -> layout.width;20px -> layout.height;8px -> target.offsetY;}bind #a to First;'
                'flow Second{80px -> layout.width;30px -> layout.height;}bind #b to Second;')
        body='<div type=container id=a></div><div type=container id=b></div>'
        # Add body id without changing the authoritative corpus generator.
        code=setup(body,source).replace('<div type=body>','<div type=body id=body>')
        self.execute(code+rect(0,0,0,320,76)+rect(1,10,18,100,20)+rect(2,10,36,80,30)+
            'assert(frame.style_version()==1 && frame.semantic_version()==store.candidate().semantic_version() && frame.version()==1);')

    def test_seeded_rows_and_columns_against_independent_stack_model(self):
        rng=random.Random(2026110205)
        for row in (False,True):
            widths=[rng.randrange(20,60) for _ in range(8)]
            heights=[rng.randrange(8,40) for _ in range(8)]
            gap=7;pad=4
            source=f'flow Root{{{pad}px -> layout.padding;'+('row' if row else 'column')+f'(gap:{gap}px) -> layout.children;}}bind #body to Root;'
            body=''
            for i,(w,h) in enumerate(zip(widths,heights)):
                source+=f'flow N{i}{{{w}px -> layout.width;{h}px -> layout.height;}}bind #n{i} to N{i};'
                body+=f'<div type=container id=n{i}></div>'
            checks='';cursor=pad
            for i,(w,h) in enumerate(zip(widths,heights),1):
                checks+=rect(i,cursor if row else pad,pad if row else cursor,w,h)
                cursor+=(w if row else h)+gap
            total=2*pad+(max(heights) if row else sum(heights)+(len(heights)-1)*gap)
            self.execute(setup(body,source,width=600,height=600).replace('<div type=body>','<div type=body id=body>')+checks+rect(0,0,0,600,total))

    def test_nested_widths_and_bottom_up_heights_do_not_feed_back(self):
        body='<div type=container id=a><div type=paragraph>abcdefghijkl</div></div><div type=button id=b>B</div>'
        source='flow A{64px -> layout.width;8px -> layout.padding;}bind #a to A;'
        self.execute(setup(body,source)+rect(1,0,0,64,48)+rect(2,8,8,48,32)+rect(3,0,48,320,16)+
            'assert(frame.run_count()==3 && len(frame.run_text(0))==6 && len(frame.run_text(1))==6);')

    def test_clip_hit_and_accessible_bounds_use_the_same_final_rectangle(self):
        source=('flow A{64px -> layout.width;24px -> layout.height;clip -> layout.overflow;}bind #a to A;'
                'flow B{100px -> layout.width;40px -> layout.height;12px -> target.offsetX;}bind #b to B;')
        body='<div type=container id=a><div type=button id=b>B</div></div>'
        self.execute(setup(body,source)+rect(2,12,0,100,40)+
            'val b:doctree::NodeId=frame.box(2).node;val bounds:pageframe::Rect=frame.accessible_bounds(2);'
            'assert(bounds.x==12 && bounds.width==52 && bounds.height==24);'
            'assert(pageframe::same(frame.hit(store.candidate(),1,63,23),b));'
            'assert(doctree::absent(frame.hit(store.candidate(),1,64,23)) && doctree::absent(frame.hit(store.candidate(),1,63,24)));'
            'assert(doctree::absent(frame.hit(store.candidate(),2,20,10)));')

    def test_semantic_order_is_independent_of_visual_overlap(self):
        body='<div type=button id=a>A</div><div type=button id=b>B</div>'
        source='flow B{-16px -> target.offsetY;}bind #b to B;'
        self.execute(setup(body,source)+
            'assert(pageframe::same(frame.hit(store.candidate(),1,2,2),frame.box(2).node));'
            'assert(frame.eligible(store.candidate(),1) && frame.eligible(store.candidate(),2));')

    def test_current_semantics_disabled_hidden_and_removal_override_failed_fs(self):
        source='flow B{input off:bool=self.disabled;choose(off,1px/0,8px) -> target.offsetX;}bind #b to B;'
        self.execute(setup('<div type=button id=b>B</div>',source)+
            'val b:doctree::NodeId=frame.box(1).node;'
            'match(store.candidate().try_append(b,108,utf8("0000000000000000true"))){Appended(id){}Rejected(code){assert(false);}}'
            'assert(!frame.current(store.candidate()) && doctree::absent(frame.hit(store.candidate(),1,12,2)));'
            'assert(page.refresh(store.candidate(),input)==402);'
            'own next:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(next!=null && next.is_open() && next.box(1).disabled && next.box(1).bounds.x==8 && next.style_version()==1);'
            'assert(!next.eligible(store.candidate(),1));'
            'assert(store.candidate().erase_subtree(b));assert(!next.current(store.candidate()));'
            'own removed:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,3,320,200,0,65536,10000000,metric);'
            'assert(removed!=null && removed.is_open() && removed.size()==1);')

    def test_hidden_subtree_is_absent_and_never_clickable(self):
        self.execute(setup('<div type=container hidden=true><div type=button>B</div></div><div type=button>C</div>')+
            'assert(frame.size()==2 && frame.run_count()==1 && frame.name(1)[0]==67);')

    def test_zoom_is_applied_once_and_text_align_uses_measured_run(self):
        source='flow P{16px -> text.size;center -> text.align;}bind #p to P;'
        self.execute(setup('<div type=paragraph id=p>abcd</div>',source,width=100,scale=131072)+
            'assert(frame.run(0).bounds.x==18 && frame.run(0).bounds.width==64 && frame.run(0).bounds.height==32);'
            'own next:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,100,200,0,131072,10000000,metric);'
            'assert(next!=null && next.is_open() && next.run(0).bounds.width==64);')

    def test_accessible_label_and_text_are_owned_after_document_close(self):
        self.execute(setup('<div type=button a11y-label="Execute">Go</div>')+
            'assert(len(frame.name(1))==7 && len(frame.run_text(0))==2);store.candidate().close();assert(!frame.current(store.candidate()));store.close();'
            'assert(frame.is_open() && frame.name(1)[0]==69 && frame.run_text(0)[0]==71);'
            'frame.close();frame.close();assert(!frame.is_open());')

    def test_unrepresentable_metric_row_width_and_unsupported_types_reject_candidate(self):
        self.execute(setup('<div type=button>B</div>')+
            'own failed:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,bad_metric);'
            'assert(failed!=null && !failed.is_open() && failed.status()==304 && frame.is_open());')
        for body,source,status in [
            ('<div type=container id=r><div type=button>B</div></div>','flow R{row(gap:0px) -> layout.children;}bind #r to R;',303),
            ('<div type=link href="https://example.org">L</div>','',203),
            ('<div type=paragraph><div type=text id=t>T</div></div>','flow T{20px -> text.size;}bind #t to T;',203),
            ('<div type=button id=b>B</div>','flow B{4px -> paint.radius;}bind #b to B;',203)]:
            code=setup(body,source).replace('assert(frame!=null && frame.is_open());',f'assert(frame!=null && !frame.is_open() && frame.status()=={status});')
            self.execute(code)

    def test_scroll_is_clamped_and_does_not_modify_flow_extent(self):
        source='flow B{600px -> layout.height;}bind #b to B;'
        self.execute(setup('<div type=button id=b>B</div>',source,scroll=900)+
            'assert(frame.scroll_y()==400 && frame.max_scroll()==400);'+rect(1,0,-400,320,600)+
            'assert(frame.accessible_bounds(1).height==200);')

    def test_reservation_and_oom_preserve_previous_snapshot_and_neighbor(self):
        self.execute(setup('<div type=button>B</div>')+
            'own failed:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,0,metric);'
            'assert(failed!=null && !failed.is_open() && failed.status()==401 && frame.is_open() && frame.run_count()==1);')

    def test_real_allocator_refusal_preserves_owned_frame_and_neighbor(self):
        warm,drain,cleanup=fs.bootstrap.preparation.exhaustion()
        body=setup('<div type=button>B</div>')
        self.fault_program(PREFIX+'safe fn main():int{'+body+'unsafe{'+warm+drain+
            'own refused:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(refused==null || (!refused.is_open() && refused.status()==401));'
            'assert(frame.is_open() && frame.run_text(0)[0]==66 && page.is_open());'+cleanup+'}return 0;}','')

    def test_graphemes_are_never_split_and_oversized_cluster_is_diagnosed(self):
        self.execute(setup('<div type=paragraph>éé</div>',width=24)+
            'assert(frame.run_count()==2 && len(frame.run_text(0))==3 && len(frame.run_text(1))==3);')
        self.execute(setup('<div type=paragraph>é</div>',width=16).replace(
            'assert(frame!=null && frame.is_open());','assert(frame!=null && !frame.is_open() && frame.status()==303);'))

    def test_new_document_uses_defaults_and_never_inherits_previous_style_version(self):
        self.execute(setup('<div type=button id=b>B</div>','flow B{64px -> layout.width;}bind #b to B;')+
            'own other:documents::Store=try_new documents::Store(4000000,4000,100);'
            f'assert(htdl::stage_catalog(other,2,{literal(fs.catalog.document("<div type=button id=b>C</div>"))},0).code==0);'
            'own next:pageframe::Frame=try_new pageframe::Frame(other.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(next!=null && next.is_open() && next.style_version()==0 && next.box(1).bounds.width==320);'
            'assert(doctree::absent(frame.hit(other.candidate(),1,2,2)));')

    def test_row_cross_axis_alignment_and_reserved_scroll_gutter(self):
        source=('flow R{row(gap:4px) -> layout.children;center -> layout.align;40px -> layout.height;}bind #r to R;'
                'flow A{20px -> layout.width;10px -> layout.height;}bind #a to A;'
                'flow B{30px -> layout.width;20px -> layout.height;}bind #b to B;')
        self.execute(setup('<div type=container id=r><div type=container id=a></div><div type=container id=b></div></div>',source)+
            rect(2,0,15,20,10)+rect(3,24,10,30,20))
        self.execute(setup('<div type=container id=r><div type=button>B</div></div>',
            'flow R{100px -> layout.width;scroll -> layout.overflow;}bind #r to R;')+rect(2,0,0,88,16))

    def test_examples_generate_all_five_formats_and_use_ir_in_both_modes(self):
        for example in ['56_page_frame.assis','57_page_frame_window.assis']:
            source=base.ROOT/'exemplos'/example
            for flags in [[],['--no-opt']]:
                ir=self.invoke('ir',source,*flags);self.assertEqual(ir.returncode,0,ir.stderr)
                self.assertEqual(json.loads(ir.stdout)['astFallbacks'],0)
                for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                    result=self.invoke('build',source,'--target',target,'-o',self.temp/target,*flags)
                    self.assertEqual(result.returncode,0,(target,result.stderr))
        for flags in [[],['--no-opt']]:
            result=self.invoke('run',base.ROOT/'exemplos/56_page_frame.assis','--debug',*flags)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'FRAME 8 4 1 1\nLEFT 8 28 104 16\n',''))

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

"""Whole-page SSC: pinned independent traces, transactional time and shared geometry."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest

def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

frame=module('frame_tests',Path(__file__).with_name('test-pageframe.py'))
ssc=module('ssc_tests',Path(__file__).with_name('test-sanscript.py'))
base=frame.base;literal=frame.literal;fs=frame.fs;ROOT=base.ROOT
PREFIX=frame.PREFIX+'import "std/motionpage.assis";'
NONE='new doctree::NodeId()'
FS=('flow Card{input n:number=state("n",0);80px -> layout.width;24px -> layout.height;'
    'n*1px -> target.offsetX;n*1px -> target.offsetY;}bind .card to Card;')
SSC='motion Card{'+ssc.channel(axis='X')+ssc.channel()+'}bind .card to Card;'
BODY='<div type=button id=a class=card>A</div><div type=button id=b class=card>B</div>'

def setup(body=BODY, source=FS, motion=SSC):
    return (frame.setup(body,source)+
        f'own motion:motionpage::Page=try_new motionpage::Page({literal(motion)},1000000);'
        'assert(motion!=null && motion.is_open());'
        'val a:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("a"));'
        'val b:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("b"));'
        'val n:int=page.input_index(utf8("Card"),utf8("n"));')

def prepare(ms=0, visible='true', focus=NONE, edit=NONE, reduced='false', expected=0):
    return f'assert(motion.prepare(store.candidate(),page,{ms},{visible},{focus},{edit},{reduced})=={expected});'

def commit():return 'assert(motion.commit(store.candidate(),page)==0);'
def target(value):return f'assert(input.set(n,2,{value}));assert(page.refresh(store.candidate(),input)==0);'
def value(node='a', axis=1):return f'motion.value(store.candidate(),{node},{axis}).value'

class MotionPage(base.Evolution):
    fault_program=frame.PageFrame.fault_program
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)
    def execute(self,body,stdout=''):self.accepted(PREFIX+'safe fn main():int{'+body+'return 0;}',stdout)

    def test_committed_moving_query_stops_idle_hidden_protected_and_aborted_timers(self):
        self.execute(setup(body='<div type=button id=a class=card>A</div>')+prepare()+commit()+'assert(!motion.moving());'+
            target(32*65536)+prepare()+'assert(!motion.moving());motion.abort();assert(!motion.moving());'+
            prepare()+commit()+'assert(motion.moving());'+prepare(9,focus='a')+commit()+'assert(!motion.moving());'+
            prepare(9)+commit()+'assert(motion.moving());'+prepare(9,visible='false')+commit()+'assert(!motion.moving());'+
            prepare(9)+commit()+'assert(motion.moving());'+prepare(9,reduced='true')+commit()+'assert(!motion.moving());')

    def test_multinode_trajectory_and_retarget_against_pinned_integer_oracle(self):
        events=[(1,8),(17,-5),(41,12),(70,0)]
        code=setup()+prepare()+commit()
        for tick in range(1,101):
            if any(t==tick for t,_ in events):code+=target(next(p for t,p in events if t==tick)*65536)
            # Exact 1/120 step by repeating the 9,8,8ms pattern.
            code+=prepare(9 if tick%3==1 else 8)
            code+=f'print({value()},{value("b",2)});'+commit()
        file=self.source(PREFIX+'safe fn main():int{'+code+'return 0;}')
        outputs=[]
        # Use the pinned Q16 matrix as an independent scalar recurrence, with
        # Python unbounded integers; do not import production implementation.
        row=next(r for r in json.loads((ROOT/'tests/fixtures/ssc-coefficients.json').read_text())['rows'] if r['frequency']=='4' and r['damping']=='0.8')
        m11,m12,m21,m22=row['matrix'];position=velocity=destination=0;calm=0;expected=[]
        for tick in range(1,101):
            for at,to in events:
                if tick==at:destination=to*65536;calm=0
            x=position-destination
            x2=((m11*x+32768)>>16)+((m12*velocity+32768)>>16)
            velocity=((m21*x+32768)>>16)+((m22*velocity+32768)>>16)
            position=destination+x2
            calm=calm+1 if abs(x2)<1024 and abs(velocity)<32768 else 0
            if calm>=3:position=destination;velocity=0
            expected.append(f'{position} {position}')
        for flags in ([],['--no-opt']):
            r=self.invoke('run',file,'--debug',*flags);self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(r.stdout.strip().splitlines(),expected);outputs.append(r.stdout)
        self.assertEqual(*outputs)

    def test_abort_preserves_active_dynamics_and_candidate_time(self):
        self.execute(setup()+prepare()+commit()+target(8*65536)+prepare(25)+
            f'val x:int={value()};assert(x>0 && x<8*65536);motion.abort();assert(motion.version()==1);'+
            prepare(25)+f'assert({value()}==x);'+commit()+prepare(0)+f'assert({value()}==x);'+
            'assert(motion.prepare(store.candidate(),page,9,true,new doctree::NodeId(),new doctree::NodeId(),false)==403);'
            f'assert({value()}==x);motion.abort();'+prepare(60001,expected=401)+'assert(motion.version()==2);')

    def test_protects_focus_and_editing_ancestors_without_freezing_other_panel(self):
        body='<div type=container id=a class=card><div type=button id=focus>F</div></div><div type=container id=b class=card></div>'
        self.execute(setup(body)+prepare()+commit()+target(8*65536)+
            'val focus:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("focus"));'+prepare(25,focus='focus')+
            f'assert({value()}==0 && {value("b")}>0);'+commit()+prepare(25,edit='focus')+
            f'assert({value()}==0 && {value("b")}>0);'+commit()+prepare(25)+f'assert({value()}==0);'+commit()+
            prepare(25)+f'assert({value()}>0);')

    def test_hidden_tab_reduced_motion_and_long_frames_have_no_backlog(self):
        self.execute(setup()+prepare()+commit()+target(8*65536)+prepare(60000)+f'val x:int={value()};motion.abort();'+
            prepare(67)+f'assert({value()}==x);'+commit()+prepare(0)+f'assert({value()}==x);'+commit()+
            prepare(1000,visible='false')+f'assert({value()}==x);'+commit()+prepare(1000)+f'assert({value()}==x);'+commit()+
            prepare(1000,reduced='true')+f'assert({value()}==8*65536 && {value("b",2)}==8*65536);')
        hidden=BODY.replace('id=a class=card','id=a class=card hidden=true')
        self.execute(setup(hidden)+prepare()+commit()+target(8*65536)+prepare(25)+
            f'assert({value()}==0 && {value("b")}>0 && motion.candidate_channels()==4);')

    def test_page_quota_counts_hidden_channels_and_rejects_257th_atomically(self):
        body=''.join(f'<div type=container id=n{i} class=card hidden=true></div>' for i in range(128))
        motion=SSC+'motion Single{'+ssc.channel(axis='X')+'}bind .single to Single;'
        source=FS+'bind .single to Card;'
        self.execute(setup(body,source,motion)+prepare()+'assert(motion.candidate_channels()==256);'+commit()+
            'assert(motion.channels()==256 && motion.version()==1);'
            'assert(store.abort(1));'
            # Immutable bootstrap attributes: an extra channel-bearing element is
            # supplied by a new document, without mutating the active bank.
            f'assert(htdl::stage_catalog(store,2,{literal(fs.catalog.document(body+"<div type=container class=single></div>"))},0).code==0);'+
            'assert(page.refresh(store.candidate(),input)==0);'+prepare(expected=403)+
            'assert(motion.channels()==256 && motion.version()==1 && motion.candidate_version()==0);')

    def test_missing_producer_conflict_and_closed_program_are_reported(self):
        self.execute(setup(source='')+prepare(expected=302)+'assert(motion.version()==0);')
        conflict='motion Other{'+ssc.channel()+'}'+SSC+'bind .card to Other;'
        self.execute(setup(motion=conflict)+prepare(expected=301)+'assert(motion.version()==0);')
        self.execute('assert(motionpage::reservation(-1)== -1);'
            'own low:motionpage::Page=try_new motionpage::Page(utf8(""),599999);assert(low!=null && !low.is_open());'
            'own bad:motionpage::Page=try_new motionpage::Page(utf8("bad"),1000000);assert(bad!=null && !bad.is_open() && bad.status()==101);')

    def test_removal_navigation_and_recycled_id_do_not_transfer_motion(self):
        self.execute(setup()+prepare()+commit()+target(8*65536)+prepare(25)+commit()+
            'val parent:doctree::NodeId=store.candidate().nodes().parent(a);'
            'assert(store.candidate().erase_subtree(a));'+prepare()+
            'assert(motion.value(store.candidate(),a,1).code==403 && motion.candidate_channels()==2);'+commit()+
            'let fresh:doctree::NodeId=new doctree::NodeId();'
            'match(store.candidate().try_append(parent,1,utf8("0000000000000000"))){Appended(id){fresh=id;}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,101,utf8("0000000000000000container"))){Appended(id){}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,105,utf8("0000000000000000a"))){Appended(id){}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,106,utf8("0000000000000000card"))){Appended(id){}Rejected(code){assert(false);}}'
            'assert(fresh.slot==a.slot && fresh.generation!=a.generation);assert(page.refresh(store.candidate(),input)==0);'+prepare()+
            'assert(motion.value(store.candidate(),fresh,1).value==8*65536 && motion.value(store.candidate(),a,1).code==403);motion.abort();'
            'assert(store.abort(1));'+f'assert(htdl::stage_catalog(store,2,{literal(fs.catalog.document(BODY))},0).code==0);'+
            'assert(page.refresh(store.candidate(),input)==0);'+prepare()+
            'assert(motion.value(store.candidate(),a,1).code==403);'
            'val current:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("a"));'
            'assert(motion.value(store.candidate(),current,1).value==8*65536);motion.close();motion.close();'
            'assert(motion.channels()==0 && motion.value(store.candidate(),current,1).code==403);')

    def test_semantic_or_fs_change_invalidates_pending_commit(self):
        self.execute(setup()+prepare()+'assert(page.refresh(store.candidate(),input)==0);'
            'assert(motion.commit(store.candidate(),page)==403 && motion.version()==0);'+prepare()+
            'assert(store.candidate().erase_subtree(a));'
            'assert(!motion.ready(store.candidate()) && motion.value(store.candidate(),b,1).code==403);'
            'assert(motion.commit(store.candidate(),page)==403 && motion.version()==0);')

    def test_composition_shifts_descendants_clips_runs_and_hit_but_not_flow(self):
        body='<div type=container id=a class=card><div type=button id=button>B</div></div><div type=container id=b></div>'
        source=FS+'flow Clip{clip -> layout.overflow;}bind #a to Clip;'
        self.execute(setup(body,source)+prepare()+commit()+target(8*65536)+prepare(25)+
            'own animated:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(animated!=null && animated.is_open());val before:pageframe::Rect=animated.box(3).bounds;'
            'assert(animated.compose(store.candidate(),motion)==0);'
            f'val dx:int=pageframe::pixels({value()});'
            'assert(animated.box(1).bounds.x==dx && animated.box(2).bounds.x==dx && animated.run(0).bounds.x==dx);'
            'assert(animated.box(2).clip.x==dx && animated.box(2).clip.width==80);'
            'assert(animated.box(3).bounds.x==before.x && animated.box(3).bounds.y==before.y);'
            'assert(pageframe::same(animated.hit(store.candidate(),2,dx+1,dx+1),animated.box(2).node));'
            'assert(doctree::absent(animated.hit(store.candidate(),1,dx+1,dx+1)));'
            'assert(animated.motion_version()==motion.candidate_version());assert(animated.compose(store.candidate(),motion)==204);')

    def test_sealed_frame_refuses_late_composition(self):
        # Packet generation is provider independent. Windows native publication
        # and stale MSAA actions are also exercised by test-pagepresent.py.
        self.execute(setup()+prepare()+commit()+target(8*65536)+prepare(25)+
            'assert(frame.compose(store.candidate(),motion)==204);'
            'own animated:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(animated.compose(store.candidate(),motion)==0);animated.seal();'
            'assert(animated.compose(store.candidate(),motion)==204);')

    def test_real_allocator_refusal_leaves_active_bank_and_neighbor(self):
        body=setup()+prepare()+commit()+target(8*65536)
        for allowance in (0,1,2,4,8):
            warm,drain,cleanup=fs.bootstrap.preparation.exhaustion(allowance)
            self.fault_program(PREFIX+'safe fn main():int{'+body+'unsafe{'+warm+drain+
                'val result:int=motion.prepare(store.candidate(),page,25,true,new doctree::NodeId(),new doctree::NodeId(),false);'
                'assert(motion.version()==1 && motion.channels()==4);'
                'if(result==0){assert(motion.value(store.candidate(),a,1).value>0);motion.abort();}'
                'else{assert(result==403 && motion.candidate_version()==0);}'
                'assert(frame.is_open() && frame.box(1).bounds.width==80 && page.is_open());'+cleanup+'}return 0;}','')

    def test_fs_error_keeps_last_targets_with_current_disabled_semantics(self):
        source=FS.replace('n*1px','8px/n').replace('state("n",0)','state("n",1)')
        self.execute(setup(source=source)+prepare()+commit()+
            'match(store.candidate().try_append(a,108,utf8("0000000000000000true"))){Appended(id){}Rejected(code){assert(false);}}'
            'assert(input.set(n,2,0));assert(page.refresh(store.candidate(),input)==402);'+prepare(25)+
            'assert(motion.value(store.candidate(),a,1).value==8*65536);'
            'own current:pageframe::Frame=try_new pageframe::Frame(store.candidate(),page,2,320,200,0,65536,10000000,metric);'
            'assert(current!=null && current.is_open());assert(current.compose(store.candidate(),motion)==0);'
            'assert(current.box(1).disabled && doctree::absent(current.hit(store.candidate(),2,9,9)));')

    def test_outside_physical_range_has_explicit_safe_fallback(self):
        self.execute(setup()+prepare()+commit()+target(5000*65536)+prepare(25)+
            'assert(motion.fallback()==401 && motion.value(store.candidate(),a,1).value==5000*65536);')

    def test_demo_and_five_formats_are_generation_separate_from_native(self):
        file=ROOT/'exemplos/58_page_motion.assis'
        for flags in ([],['--no-opt']):
            r=self.invoke('run',file,'--debug',*flags);self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(r.stdout,'MOTION 1 11 1\nMOTION 2 32 1\nMOTION 3 51 1\nMOTION 4 65 1\n')
            for target_name in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                r=self.invoke('build',file,'--target',target_name,'-o',self.temp/'output.bin',*flags)
                self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

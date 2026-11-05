"""Immutable local resource batches: independent path oracle and real workers."""
import importlib.util
import os
from pathlib import Path
import random
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('frame_worker_resources',ROOT/'tests/test-frame-worker.py')
fw=importlib.util.module_from_spec(spec);spec.loader.exec_module(fw)
base=fw.base;literal=fw.literal

class ResourceBatch(unittest.TestCase):
    setUp=base.Evolution.setUp
    tearDown=base.Evolution.tearDown
    source=base.Evolution.source
    def invoke(self,*args,**kwargs):
        if args and args[0] in ("check","build","run","ir"): args=(*args,"--safe")
        return base.Evolution.invoke(self,*args,**kwargs)
    accepted=base.Evolution.accepted

    def execute(self,body):
        self.accepted('import "std/pageresources.assis";safe fn main():int{'+body+'return 0;}')

    def test_paths_against_independent_segment_stack_and_invalid_authority(self):
        rng=random.Random(20261104);code=''
        for _ in range(80):
            parent=['app','pages','nested'][:rng.randrange(4)]
            parts=[rng.choice(['assets','a-b','C_2','.','..']) for _ in range(rng.randrange(1,8))]+['item.bin']
            stack=parent.copy();valid=True
            for part in parts:
                if part=='..':
                    if not stack:valid=False;break
                    stack.pop()
                elif part!='.':stack.append(part)
            code+='{own p:pageresources::Path=try_new pageresources::Path('+literal('/'.join(parent+['index.htdl']))+','+literal('/'.join(parts))+');assert(p!=null);'
            code+=('assert(p.status()==0 && pageresources::equal(p.content(),'+literal('/'.join(stack))+'));' if valid else 'assert(p.status()== -1);')+'}'
        for path in ['','/root','//host/x','C:/root','file:x','https://a/x','a\\b','a%2fb','a?b','a#b','a//b','a/','../a','a/../../b','NUL','con.txt','a/COM1.log','LPT9','a.','ÃƒÆ’Ã‚Â¡.txt','a\x00b']:
            code+='{own p:pageresources::Path=try_new pageresources::Path(utf8(""),'+literal(path)+');assert(p!=null && p.status()== -1);}'
        self.execute(code)

    def test_paths_exact_length_and_local_keys_preserve_case(self):
        self.execute('{own p:pageresources::Path=try_new pageresources::Path(utf8(""),'+literal('a'*1024)+');assert(p!=null && p.status()==0 && len(p.content())==1024);}'
            '{own p:pageresources::Path=try_new pageresources::Path(utf8(""),'+literal('a'*1025)+');assert(p!=null && p.status()== -1);}'
            'assert(!pageresources::equal(utf8("App/a"),utf8("app/a")));')

    def test_plan_deduplicates_exact_keys_versions_and_single_role_roots(self):
        self.execute('own b:pageresources::Batch=try_new pageresources::Batch(1,2,3,3,1000,100);assert(b!=null && b.is_open());'
            'assert(b.add(1,2,utf8("app/index.htdl"),utf8("./index.htdl"))==1);'
            'assert(b.add(1,2,utf8(""),utf8("app/index.htdl"))==1 && b.size()==1);'
            'assert(b.add(1,1,utf8(""),utf8("app/index.htdl"))== -16);'
            'assert(b.add(1,2,utf8(""),utf8("other.htdl"))== -16);'
            'assert(b.add(9,1,utf8(""),utf8("x"))== -16 && b.add(2,2,utf8(""),utf8("x"))== -16);'
            'assert(b.add(4,1,utf8(""),utf8("app.assis"))==2);'
            'assert(b.add(5,1,utf8(""),utf8("app.asv2"))== -16);'
            'assert(b.add(6,1,utf8(""),utf8("a.bin"))==3 && b.add(6,1,utf8(""),utf8("b.bin"))== -3);'
            'assert(b.seal(1)==0 && b.add(6,1,utf8(""),utf8("b"))== -12 && !b.complete());')

    def test_out_of_order_envelopes_replay_copy_and_immutable_completion(self):
        self.execute('own b:pageresources::Batch=try_new pageresources::Batch(11,12,13,3,6,100);assert(b!=null);'
            'assert(b.add(6,1,utf8(""),utf8("a"))==1 && b.add(6,1,utf8(""),utf8("b"))==2);assert(b.seal(1)==0);'
            'val q:pageresources::Request=b.envelope(0);'
            'assert(b.deliver(new pageresources::Request(10,12,13,1,6,1),utf8("x"),2)== -2);'
            'assert(b.deliver(new pageresources::Request(11,10,13,1,6,1),utf8("x"),2)== -2);'
            'assert(b.deliver(new pageresources::Request(11,12,10,1,6,1),utf8("x"),2)== -2);'
            'assert(b.deliver(new pageresources::Request(11,12,13,0,6,1),utf8("x"),2)== -2);'
            'assert(b.deliver(new pageresources::Request(11,12,13,3,6,1),utf8("x"),2)== -2);'
            'assert(b.deliver(new pageresources::Request(11,12,13,1,2,1),utf8("x"),2)== -16);'
            'assert(b.deliver(new pageresources::Request(11,12,13,1,6,2),utf8("x"),2)== -16);'
            'own raw:*byte=try_alloc<byte>(3);assert(raw!=null);raw[0]=byte(0);raw[1]=byte(65);raw[2]=byte(255);'
            'assert(b.deliver(b.envelope(1),slice_of(raw,0,3),2)==0);raw[1]=byte(66);'
            'assert(b.deliver(b.envelope(1),utf8("bad"),3)== -2 && !b.complete());'
            'assert(b.deliver(q,utf8("1234"),3)== -3 && b.used_bytes()==3);'
            'assert(b.deliver(q,utf8("123"),3)==0 && b.complete() && b.used_bytes()==6);'
            'assert(b.content(1)[0]==0 && b.content(1)[1]==65 && b.content(1)[2]==255);'
            'assert(b.deliver(q,utf8("bad"),4)== -12 && b.poll(1000)==1);'
            'assert(b.role(6)==0 && b.role(1)== -1);b.cancel();assert(!b.complete() && b.used_bytes()==0 && b.role(6)== -1 && b.deliver(q,utf8("x"),4)== -12);')

    def test_deadline_empty_payload_exact_budget_and_independent_neighbor(self):
        self.execute('own b:pageresources::Batch=try_new pageresources::Batch(1,1,1,1,0,10);'
            'own n:pageresources::Batch=try_new pageresources::Batch(2,2,2,1,0,10);assert(b!=null && n!=null);'
            'assert(b.seal(1)== -1 && b.add(6,1,utf8(""),utf8("a"))==1 && b.seal(1)==0);'
            'assert(n.add(6,1,utf8(""),utf8("a"))==1 && n.seal(1)==0);'
            'assert(b.deliver(b.envelope(0),utf8(""),10)== -8 && b.status()== -8 && !b.is_open());'
            'assert(n.deliver(n.envelope(0),utf8(""),9)==0 && n.complete() );{assert(len(n.content(0))==0);}'
            'own late:pageresources::Batch=try_new pageresources::Batch(1,1,2,1,10,10);assert(late!=null);val expired:int=late.poll(10);assert(expired== -8 && late.status()== -8);')

    def test_per_kind_limits_and_retained_quota_after_failure(self):
        self.execute('own raw:*byte=try_alloc<byte>(65537);assert(raw!=null);'
            'own b:pageresources::Batch=try_new pageresources::Batch(1,1,1,2,100000,100);assert(b!=null);'
            'assert(b.add(1,2,utf8(""),utf8("index.htdl"))==1 && b.seal(1)==0);'
            'assert(b.deliver(b.envelope(0),slice_of(raw,0,65537),2)== -3 && b.used_bytes()==0);'
            'assert(b.deliver(b.envelope(0),slice_of(raw,0,65536),2)==0 && b.used_bytes()==65536);')

class ResourceIntegration(unittest.TestCase):
    setUpClass=classmethod(fw.FrameWorker.setUpClass.__func__)
    tearDownClass=classmethod(fw.FrameWorker.tearDownClass.__func__)
    setUp=fw.FrameWorker.setUp
    binary=fw.FrameWorker.binary
    compile_page=classmethod(fw.FrameWorker.compile_page.__func__)
    execute=fw.FrameWorker.execute
    setup=fw.FrameWorker.setup
    prepare=fw.FrameWorker.prepare
    source=base.Evolution.source
    invoke=base.Evolution.invoke
    fault_program=fw.FrameWorker.fault_program

    def bundle(self,generation=1,program=None,fs='flow B{12px -> target.offsetX;}bind #add to B;',origin=23):
        values=[(1,2,'index.htdl',literal(fw.document('<div type=button id=add>Add</div>'))),(2,1,'styles/main.fxs',literal(fs)),(3,1,'styles/main.sscr',literal('')),
                (5 if program is None else 4,1,'code/main.asv2' if program is None else 'code/main.assis',self.binary(self.code) if program is None else literal(program)),(6,1,'data/note.bin',literal('resource-v1'))]
        code=f'own bundle:pageresources::Batch=try_new pageresources::Batch(19,{origin},{generation},8,300000,monotonic_ms()+10000);assert(bundle!=null);'
        code+=''.join(f'assert(bundle.add({k},{v},utf8(""),{literal(path)})=={i+1});' for i,(k,v,path,payload) in enumerate(values))
        code+='assert(bundle.seal(monotonic_ms())==0);'
        code+=''.join(f'assert(bundle.deliver(bundle.envelope({i}),{values[i][3]},monotonic_ms())==0);' for i in reversed(range(len(values))))
        return code+'assert(bundle.complete());'

    def activate(self):
        return 's.prepare_bundle(move(bundle),'+literal(str(base.COMPILER))+','+literal(str(self.worker))+',false,128,3,true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(true,false),monotonic_ms())'

    def test_asv2_bundle_commit_reflow_host_data_and_legacy_navigation(self):
        self.execute(self.setup()+self.bundle()+f'assert({self.activate()}==0);ready(s);assert(!s.has_resources());assert(s.commit() && s.has_resources());'
            'drain(s,0);assert(s.resources().complete() && s.resources().size()==5 && s.snapshot().frame.box(1).bounds.x==12);'
            'assert(pageresources::equal(s.resources().content(4),utf8("resource-v1")));'
            'assert(s.reflow(200,160,0,131072,25,true,reader::default_preferences(),metric)==0 && s.commit_reflow() && s.has_resources());'
            's.dispatch(s.document_id(),s.snapshot().frame.version(),ev(3,9,1,1));s.dispatch(s.document_id(),s.snapshot().frame.version(),ev(3,13,1,2));drain(s,1);'
            f'assert({self.prepare()}==0);ready(s);assert(s.commit() && !s.has_resources());s.close();assert(!s.has_resources());')

    def test_source_bundle_compile_abort_failure_and_generation_authority(self):
        program='import "std/page.assis";safe fn main():int{return 42;}'
        code=self.setup()+self.bundle(program=program)+f'assert({self.activate()}==0);ready(s);assert(s.commit());drain(s,42);'
        code+='{'+self.bundle(generation=1)+f'assert({self.activate()}== -2 && s.has_resources() && s.document_id()==2);'+'}'
        code+='{'+self.bundle(generation=2,origin=24)+f'assert({self.activate()}== -2 && s.has_resources());'+'}'
        code+='{'+self.bundle(generation=2,fs='bad')+f'assert({self.activate()}!=0 && !s.has_pending() && s.has_resources());'+'}'
        code+='{'+self.bundle(generation=2)+f'assert({self.activate()}== -2);'+'}'
        code+='{'+self.bundle(generation=3,program=program)+f'assert({self.activate()}==0);s.abort();assert(!s.has_pending() && s.has_resources());'+'}'
        code+='{'+self.bundle(generation=4,program='not a program')+f'assert({self.activate()}==0);let failed:bool=false;for(let i:int=0;i<5000;i++)'+'{if(s.advance(monotonic_ms())<0){failed=true;break;}sleep_ms(1);}assert(failed && s.has_resources() && s.document_id()==2);}'
        code+='s.close();assert(!s.has_resources());'
        self.execute(code)

    def test_held_control_shortcuts_survive_zoom_and_focus_loss_cancels_them(self):
        self.execute(self.setup()+
            's.dispatch(1,1,ev(3,17,1,1));assert(s.dispatch(1,1,ev(3,187,1,2)).change.kind==5);'
            'assert(s.reflow(320,220,0,131072,0,true,reader::default_preferences(),metric)==0 && s.commit_reflow());'
            'assert(s.dispatch(1,2,ev(3,189,1,3)).change.kind==6);'
            'assert(s.dispatch(1,2,ev(3,65,1,4)).change.kind==1);'
            'assert(s.dispatch(1,2,ev(3,67,1,5)).change.kind==4);'
            's.dispatch(1,2,ev(5,0,0,6));assert(s.dispatch(1,2,ev(3,187,1,7)).change.kind==0);')

    def test_external_file_examples_load_the_exact_grants_and_reject_missing_files(self):
        paths=[ROOT/'exemplos/resource-demo'/name for name in ('index.htdl','main.fxs','main.sscr','main.assis')]
        for flags in ([],['--no-opt']):
            binary=self.temp/('resources.exe' if os.name=='nt' else 'resources')
            result=subprocess.run([base.COMPILER,'build',ROOT/'exemplos/66_resource_frame.assis','--safe','--debug','-o',binary,*flags],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([binary,base.COMPILER,self.worker,*paths],env=self.env,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'RESOURCE FRAME 4 0 1\n',''))
            result=subprocess.run([binary,base.COMPILER,self.worker,self.temp/'missing.htdl',*paths[1:]],env=self.env,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(6,'',''))

    @unittest.skipUnless(os.name=='nt','Windows native resource window unavailable')
    def test_external_resource_window_native_once_and_zoom_smoke(self):
        paths=[ROOT/'exemplos/resource-demo'/name for name in ('index.htdl','main.fxs','main.sscr','main.assis')]
        for flags in ([],['--no-opt']):
            binary=self.temp/'resource-window.exe'
            result=subprocess.run([base.COMPILER,'build',ROOT/'exemplos/67_resource_frame_window.assis','--safe','--debug','-o',binary,*flags],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for option in ('--once','--smoke'):
                result=subprocess.run([binary,base.COMPILER,self.worker,*paths,option],env=self.env,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'FRAME WORKER WINDOW '+('1 11' if option=='--once' else '2 11')+'\n',''))

    def test_os_allocation_refusal_keeps_a_delivered_resource_and_retryable_slot(self):
        for allowance in (0,1,2,4,8):
            warm,deny,cleanup=fw.fr.frame.fs.bootstrap.preparation.exhaustion(allowance)
            body=('own b:pageresources::Batch=try_new pageresources::Batch(1,2,3,2,2000000,100);assert(b!=null);'
                'assert(b.add(6,1,utf8(""),utf8("a"))==1 && b.add(6,1,utf8(""),utf8("b"))==2 && b.seal(1)==0);'
                'assert(b.deliver(b.envelope(0),utf8("keep"),2)==0);own payload:*byte=try_alloc<byte>(1048576);assert(payload!=null);'
                'unsafe{'+warm+deny+'val code:int=b.deliver(b.envelope(1),slice_of(payload,0,len(payload)),3);'
                'assert(code==0 || code== -4);assert(b.is_open() && b.size()==2 && b.used_bytes()>=4);'+cleanup+'}'
                'if(!b.complete()){assert(b.deliver(b.envelope(1),utf8("retry"),4)==0);}assert(b.complete() && pageresources::equal(b.content(0),utf8("keep")));')
            self.fault_program('import "std/pageresources.assis";safe fn main():int{'+body+'return 0;}','')

    def test_resource_example_emits_five_formats_without_claiming_their_execution(self):
        for flags in ([],['--no-opt']):
            for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                result=subprocess.run([base.COMPILER,'build',ROOT/'exemplos/66_resource_frame.assis','--safe','--target',target,'-o',self.temp/target,*flags],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,(target,result.stderr))

    @unittest.skipUnless(os.name=='nt','Windows atomic resource/raster/MSAA publication')
    def test_native_resource_publish_failure_retry_and_abort_preserve_active_owners(self):
        self.execute(self.setup()+
            'own w:window::Window=try_new window::Window(7,320,220,utf8("Resource owners"));assert(w!=null && w.opened());'+
            self.bundle()+f'assert({self.activate()}==0);ready(s);'
            'own closed:window::Window=try_new window::Window(8,320,220,utf8("Closed"));assert(closed!=null);closed.close();'
            'assert(s.publish(closed)== -2 && !s.has_resources() && s.has_pending());'
            'assert(s.publish(w)==0 && s.has_resources());drain(s,0);'+
            '{'+self.bundle(generation=2)+f'assert({self.activate()}==0);ready(s);s.abort();'
            'assert(s.has_resources() && s.document_id()==2 && s.resources().envelope(0).generation==1);}'
            's.close();w.close();assert(!s.has_resources());')

if __name__=='__main__':unittest.main(verbosity=2)

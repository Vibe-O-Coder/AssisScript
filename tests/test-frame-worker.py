"""Frame/FS/SSC and real restricted ASV2 workers share a transaction.

SDK order is asserted from literal HTDL preorders, independent of the Frame's
boxes (which omit head, inline and hidden nodes). Native runs use both modes.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parent.parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
pr=module('worker_reader',ROOT/'tests/test-page-reader.py')
fr=module('composed_reader',ROOT/'tests/test-framereader.py')
base=pr.base;literal=pr.literal;document=pr.document
PREFIX=fr.frame.PREFIX+'import "std/frameworker.assis";'+fr.EVENT+'''
safe fn ready(borrow mut s:frameworker::Session):void{
 for(let i:int=0;i<5000;i++){assert(s.advance(monotonic_ms())>=0);if(s.ready()){return;}sleep_ms(1);}assert(false);
}
safe fn drain(borrow mut s:frameworker::Session,expected:int):void{
 for(let i:int=0;i<5000;i++){assert(s.advance(monotonic_ms())>=0);
 if(s.result().code==2 && s.result().result==expected && s.queued()==0){return;}sleep_ms(1);}assert(false);
}
'''
FS=literal('flow B{8px -> target.offsetX;}bind #add to B;')
SSC=literal('motion B{spring(target:fs.target.offsetX,frequency:4Hz,dampingRatio:0.8)->presentation.offsetX;}bind #add to B;')

class FrameWorkerFormats(unittest.TestCase):
    setUp=base.Evolution.setUp
    invoke=base.Evolution.invoke

    def test_worker_example_generates_five_target_formats(self):
        for flags in ([],['--no-opt']):
            for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                result=self.invoke('build',ROOT/'exemplos/64_frame_worker.assis','--safe','--target',target,'-o',self.temp/target,*flags)
                self.assertEqual(result.returncode,0,(target,result.stderr))

@unittest.skipUnless(pr.worker.builder.supports_host(), 'Worker provider requires Windows/Linux x64')
class FrameWorker(unittest.TestCase):
    setUpClass=classmethod(pr.PageReader.setUpClass.__func__)
    tearDownClass=classmethod(pr.PageReader.tearDownClass.__func__)
    setUp=pr.PageReader.setUp
    binary=pr.PageReader.binary
    compile_page=classmethod(pr.PageReader.compile_page.__func__)
    source=base.Evolution.source
    invoke=base.Evolution.invoke
    fault_program=fr.frame.PageFrame.fault_program
    def execute(self,body,imports=''):
        prelude=''.join(f'own {key}:*byte=try_alloc<byte>({len(data)});assert({key}!=null);'+''.join(f'{key}[{i}]=byte({b});' for i,b in enumerate(data)) for key,data in self.data.items())
        source=self.temp/'host.assis'
        code=imports+PREFIX+'safe fn main():int{'+prelude+body+'return 0;}'
        code=re.sub(r'("(?:\\.|[^"\\])*")|;',lambda m:m[0] if m[1] else ';\n',code)
        source.write_text(code,encoding='utf-8')
        for flags in ([],['--no-opt']):
            binary=self.temp/('host.exe' if os.name=='nt' else 'host')
            r=subprocess.run([str(base.COMPILER),'build',str(source),'--safe','--debug','-o',str(binary),*flags],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(binary)],env=self.env,capture_output=True,text=True,timeout=30,cwd=ROOT)
            match=re.search(r'host\.assis:(\d+)',r.stderr)
            context=source.read_text(encoding='utf-8').splitlines()[int(match[1])-1] if match else r.stderr
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'',''),context)
    def prepare(self,body='<div type=button id=add>Add</div>',code=None,fs=FS,ssc=SSC,profile='framehost::reading_versions()',metric='metric',path=None):
        return ('s.prepare('+literal(str(self.worker) if path is None else path)+','+literal(document(body))+','+fs+','+ssc+','+profile+','+self.binary(self.code if code is None else code)+',true,320,220,65536,reader::default_preferences(),'+metric+',limits,new frameworker::Grants(true,false),monotonic_ms())')
    def setup(self,body='<div type=button id=add>Add</div>',commit=True,**kw):
        return ('own s:frameworker::Session=try_new frameworker::Session(32000000,250000,7,19,23);assert(s!=null && s.is_open());'
            'val limits:frameworker::Limits=new frameworker::Limits(0,16,100000,1000,3000);assert('+self.prepare(body,**kw)+'==0);ready(s);'+('assert(s.commit());' if commit else ''))
    def test_composed_frame_sdk_keyboard_and_reflow_use_distinct_identities(self):
        self.execute(self.setup()+'drain(s,0);assert(s.snapshot().frame.box(1).bounds.x==8);'
            's.dispatch(1,1,ev(3,9,1,1));assert(s.dispatch(1,1,ev(3,13,1,2)).change.kind==2);drain(s,1);'
            'assert(s.reflow(200,160,0,131072,25,true,reader::default_preferences(),metric)==0);assert(s.commit_reflow());'
            'assert(s.document_id()==1 && s.snapshot().frame.version()==2);'
            'assert(s.dispatch(1,1,ev(3,13,1,3)).change.kind==0);s.dispatch(1,2,ev(3,13,0,3));'
            'assert(s.dispatch(1,2,ev(3,13,1,4)).change.kind==2);drain(s,2);')
    def test_catalog_sdk_preorder_includes_nonvisual_inline_and_hidden_nodes(self):
        # document,head,title,body,main,list,item,paragraph,text,hidden button,button
        program='import "std/page.assis";safe fn main():int{if(htdl_v1::event_get(0)==2){return htdl_v1::event_get(1);}return htdl_v1::node_count();}'
        self.execute(self.setup('<div type=main><div type=list><div type=item><div type=paragraph>A<div type=text>B</div></div></div></div><div type=button hidden=true>Hidden</div><div type=button id=add>Add</div></div>',code=self.compile_page(program))+
            'drain(s,11);s.dispatch(1,1,ev(3,9,1,1));s.dispatch(1,1,ev(3,13,1,2));drain(s,10);assert(s.result().isolation==1);')
    def test_parse_style_motion_metric_worker_failures_and_abort_preserve_active(self):
        body=self.setup()+'drain(s,0);'
        for kw in [dict(body='<div>bad'),dict(fs=literal('bad')),dict(ssc=literal('bad')),dict(metric='bad_metric'),dict(path='relative-worker'),dict(profile='new framehost::Versions(2,2,1)')]:
            body+='assert('+self.prepare(**kw)+'!=0 && !s.has_pending() && s.document_id()==1 && s.worker_alive());'
        body+='assert('+self.prepare(profile='framehost::forms_versions()')+'==200 && !s.has_pending() && s.document_id()==1);'
        body+=('assert(s.prepare_source(utf8("invalid-compiler"),utf8("invalid-worker"),'+literal(document('<div type=paragraph>Read</div>'))+
            ',utf8("safe fn main():int{return 0;}"),utf8(""),utf8(""),framehost::forms_versions(),false,128,3,true,'
            '320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(false,false),monotonic_ms())==200 && !s.has_pending());')
        body+='assert('+self.prepare(code=bytes(20))+'==0);let rejected:bool=false;for(let i:int=0;i<5000;i++){if(s.advance(monotonic_ms())<0){rejected=true;break;}sleep_ms(1);}assert(rejected && s.document_id()==1 && s.worker_alive());'
        body+='assert('+self.prepare()+'==0);ready(s);val used:int=s.candidate_id();s.abort();assert(!s.has_pending());'
        body+='assert('+self.prepare()+'==0);ready(s);assert(s.candidate_id()>used && s.commit());drain(s,0);'
        self.execute(body)
    def test_navigation_freezes_actions_and_discards_old_queue_selection_and_frame(self):
        self.execute(self.setup()+'drain(s,0);s.dispatch(1,1,ev(3,9,1,1));s.dispatch(1,1,ev(3,13,1,2));assert(s.queued()==1);'
            's.dispatch(1,1,ev(3,17,1,3));s.dispatch(1,1,ev(3,65,1,4));assert(len(s.snapshot().reading.selected_text())>0);'
            'assert('+self.prepare()+'==0);assert(s.dispatch(1,1,ev(3,13,1,5)).status== -2);ready(s);assert(s.commit());'
            'assert(s.document_id()==2 && s.queued()==0 && len(s.snapshot().reading.selected_text())==0);drain(s,0);'
            'assert(s.dispatch(1,2,ev(3,13,1,6)).status== -2);assert(s.dispatch(2,1,ev(3,13,1,6)).change.kind==0);')
    def test_fifo_backpressure_enter_repeat_hidden_disabled_and_close(self):
        self.execute(self.setup('<div type=button hidden=true>Hidden</div><div type=button disabled=true>Disabled</div><div type=button id=add>Add</div>')+
            'drain(s,0);s.dispatch(1,1,ev(3,9,1,1));'
            'for(let i:int=0;i<32;i++){assert(s.dispatch(1,1,ev(3,13,1,2+3*i)).status==0);assert(s.dispatch(1,1,ev(3,13,1,3+3*i)).change.kind==0);s.dispatch(1,1,ev(3,13,0,4+3*i));}'
            'assert(s.queued()==32);assert(s.dispatch(1,1,ev(3,13,1,100)).status==1);drain(s,32);'
            'assert('+self.prepare()+'==0);s.close();assert(!s.worker_alive() && !s.has_active() && !s.has_pending() && s.queued()==0);')
    def test_links_remain_local_host_actions_and_never_post_sdk_button_events(self):
        self.execute(self.setup('<div type=link href="#end">End</div><div type=paragraph id=end>Target</div>')+
            'drain(s,0);s.dispatch(1,1,ev(3,9,1,1));val a:frameworker::Action=s.dispatch(1,1,ev(3,13,1,2));'
            'assert(a.status==0 && a.change.kind==8 && s.queued()==0 && s.fragment_scroll(1,a.change.node)>=0);'
            'assert('+self.prepare(body='<div type=link href="https://example.test/">No</div>')+'==203 && s.document_id()==1);')
    def test_transformed_pointer_targets_the_same_sdk_node_and_rejects_forged_events(self):
        self.execute(self.setup()+'drain(s,0);'
            'assert(s.dispatch(1,1,new window::Event(0,7,8,1,9,1,1)).change.kind==0);'
            'assert(s.dispatch(1,1,ev(7,1,1,1)).change.kind==0);'
            'assert(s.dispatch(1,1,ev(7,9,1,2)).change.kind==1);assert(s.dispatch(1,1,ev(8,9,1,3)).change.kind==2);drain(s,1);'
            'assert(s.dispatch(1,1,ev(8,9,1,3)).change.kind==0 && s.queued()==0);')
    def test_worker_fuel_failure_keeps_reading_and_independent_neighbor_and_recovers(self):
        hostile=self.compile_page('safe fn main():int{while(true){}return 0;}')
        self.execute(self.setup(code=hostile)+
            'own n:frameworker::Session=try_new frameworker::Session(32000000,250000,8,20,24);assert(n!=null && n.is_open());'
            'assert(n.prepare('+literal(str(self.worker))+','+literal(document('<div type=paragraph>Neighbor</div>'))+',utf8(""),utf8(""),framehost::reading_versions(),'+self.binary(self.compile_page('safe fn main():int{return 42;}'))+',true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(false,false),monotonic_ms())==0);ready(n);assert(n.commit());'
            'let stopped:bool=false;for(let i:int=0;i<5000;i++){assert(n.advance(monotonic_ms())>=0);if(s.advance(monotonic_ms())<0){stopped=true;break;}sleep_ms(1);}assert(stopped && s.has_active() && !s.worker_alive());drain(n,42);assert(n.worker_alive());'
            's.dispatch(1,1,ev(3,9,1,1));assert(s.dispatch(1,1,ev(3,13,1,2)).status== -9);'
            'assert(s.reflow(200,160,0,65536,0,true,reader::default_preferences(),metric)==0 && s.commit_reflow());'
            'assert('+self.prepare()+'==0);ready(s);assert(s.commit());drain(s,0);')
    def test_mutable_source_code_style_and_motion_are_copied_before_return(self):
        source=self.binary(document('<div type=button id=add>Add</div>').encode());code=self.binary(self.code)
        fs=self.binary(b'flow B{8px -> target.offsetX;}bind #add to B;');ssc=self.binary(b'motion B{spring(target:fs.target.offsetX,frequency:4Hz,dampingRatio:0.8)->presentation.offsetX;}bind #add to B;')
        mutate=''.join(x.split('(')[1].split(',')[0]+'[0]=byte(0);' for x in (source,code,fs,ssc))
        self.execute('own s:frameworker::Session=try_new frameworker::Session(32000000,250000,7,19,23);assert(s!=null);'
            'val limits:frameworker::Limits=new frameworker::Limits(0,16,100000,1000,3000);'
            'assert(s.prepare('+literal(str(self.worker))+','+source+','+fs+','+ssc+',framehost::reading_versions(),'+code+',true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(true,false),monotonic_ms())==0);'+mutate+
            'ready(s);assert(s.commit());drain(s,0);assert(s.snapshot().frame.box(1).bounds.x==8);s.dispatch(1,1,ev(3,9,1,1));s.dispatch(1,1,ev(3,13,1,2));drain(s,1);')
    def test_real_os_allocation_refusal_preserves_active_worker_and_frame(self):
        # Allocation denial is confined to this host process; the worker keeps
        # its separate heap. Existing buffers suffice to poll it after refusal.
        original={key:os.environ.get(key) for key in ('PATH','LD_LIBRARY_PATH')}
        for key in original:os.environ[key]=self.env[key]
        try:
            for allowance in (0,1,2,4,8):
                warm,deny,cleanup=fr.frame.fs.bootstrap.preparation.exhaustion(allowance)
                body=self.setup()+'drain(s,0);unsafe{'+warm+deny+'val rejected:int='+self.prepare()+';'
                body+='assert(rejected==0 || rejected==401 || rejected== -4);if(rejected==0){s.abort();}'
                body+='assert(s.document_id()==1 && s.worker_alive() && s.snapshot().frame.version()==1 && !s.has_pending());'+cleanup+'}s.close();'
                self.fault_program(PREFIX+'safe fn main():int{'+''.join(f'own {k}:*byte=try_alloc<byte>({len(v)});'+''.join(f'{k}[{i}]=byte({b});' for i,b in enumerate(v)) for k,v in self.data.items())+body+'return 0;}','')
        finally:
            for key,value in original.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value
    def test_worker_example_runs_with_the_native_provider(self):
        for flags in ([],['--no-opt']):
            binary=self.temp/('example.exe' if os.name=='nt' else 'example')
            r=subprocess.run([base.COMPILER,'build',ROOT/'exemplos/64_frame_worker.assis','--safe','-o',binary,*flags],capture_output=True,text=True,cwd=ROOT);self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([binary,base.COMPILER,self.worker],env=self.env,capture_output=True,text=True,timeout=20,cwd=ROOT)
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'FRAME WORKER 42 1 1\n',''))
    @unittest.skipUnless(os.name=='nt','Windows graphical example')
    def test_interactive_example_native_once_and_smoke(self):
        for flags in ([],['--no-opt']):
            binary=self.temp/'window.exe'
            r=subprocess.run([base.COMPILER,'build',ROOT/'exemplos/65_frame_worker_window.assis','--safe','-o',binary,*flags],capture_output=True,text=True,cwd=ROOT);self.assertEqual(r.returncode,0,r.stderr)
            for option,revision in (('--once',1),('--smoke',2)):
                r=subprocess.run([binary,base.COMPILER,self.worker,option],env=self.env,capture_output=True,text=True,timeout=20,cwd=ROOT)
                self.assertEqual((r.returncode,r.stdout,r.stderr),(0,f'FRAME WORKER WINDOW {revision} 11\n',''))
    def test_source_compilation_copies_bundle_and_abort_preserves_previous(self):
        self.execute(self.setup()+'drain(s,0);'
            'assert(s.prepare_source('+literal(str(base.COMPILER))+','+literal(str(self.worker))+','+literal(document('<div type=button id=add>Compiled</div>'))+','+literal('safe fn main():int{return 42;}')+','+FS+','+SSC+',framehost::reading_versions(),false,128,3,true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(false,false),monotonic_ms())==0);'
            'assert(s.dispatch(1,1,ev(3,9,1,1)).status== -2);s.abort();assert(s.document_id()==1 && s.worker_alive());'
            'assert(s.prepare_source('+literal(str(base.COMPILER))+','+literal(str(self.worker))+','+literal(document('<div type=button id=add>Compiled</div>'))+','+literal('safe fn main():int{return 42;}')+','+FS+','+SSC+',framehost::reading_versions(),true,128,3,true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(false,false),monotonic_ms())==0);ready(s);assert(s.commit());drain(s,42);')
    @unittest.skipUnless(os.name=='nt','Windows atomic raster/MSAA publication')
    def test_native_publication_failure_retry_reflow_and_accessible_activation(self):
        self.execute(self.setup(commit=False)+'own w:window::Window=try_new window::Window(7,320,220,"Frame worker");assert(w!=null && w.opened());assert(s.publish(w)==0 && w.present()==0);drain(s,0);'
            'assert(s.dispatch(1,1,ev(11,1,1,1)).change.kind==2);drain(s,1);'
            'assert('+self.prepare(body='<div type=main><div type=button id=add>New</div></div>')+'==0);ready(s);'
            'own closed:window::Window=try_new window::Window(8,320,220,"Closed");assert(closed!=null);closed.close();'
            'assert(s.publish(closed)== -2 && s.document_id()==1 && s.has_pending() && s.worker_alive());assert(s.publish(w)==0 && s.document_id()==2);drain(s,0);'
            'assert(s.reflow(200,160,0,131072,25,true,reader::default_preferences(),metric)==0 && s.publish_reflow(w)==0);'
            'assert(s.snapshot().frame.version()==3 && s.document_id()==2);s.close();w.close();')

if __name__=='__main__':unittest.main(verbosity=2)

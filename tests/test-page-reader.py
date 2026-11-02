"""One HTDL source -> Reader + isolated SDK worker; transactional activation."""
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
worker=module('tab_worker',ROOT/'tests/test-page-worker.py')
reader=module('tab_reader',ROOT/'tests/test-htdl-reader.py')
base=worker.base
literal=reader.viewer.parser.literal
document=reader.viewer.parser.document
PREFIX=reader.PREFIX.replace('std/reader.assis','std/pagereader.assis')+'''
safe fn ready(borrow mut s:pagereader::Session):void{
 for(let i:int=0;i<5000;i++){assert(s.advance(monotonic_ms())>=0);if(s.ready()){return;}sleep_ms(1);}assert(false);
}
safe fn drain(borrow mut s:pagereader::Session,expected:int):void{
 for(let i:int=0;i<5000;i++){assert(s.advance(monotonic_ms())>=0);
 if(s.result().code==2 && s.result().result==expected && s.queued()==0){return;}sleep_ms(1);}assert(false);
}
'''

class PageReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory(prefix='assis-page-reader-');cls.out=Path(cls.folder.name)
        built=worker.builder.build(cls.out,base.COMPILER);cls.worker=Path(built['worker'])
        if os.name=='nt': reader.module('tab_platform_builder',ROOT/'tools/build-platform.py').build(cls.out/'assis_platform_v1.dll',testing=True)
        cls.env=dict(os.environ,PATH=str(cls.out)+os.pathsep+os.environ.get('PATH',''),LD_LIBRARY_PATH=str(cls.out))
        cls.code=cls.compile_page('import "std/page.assis";safe fn main():int{'
            'if(htdl_v1::event_get(0)==2){let n:int=htdl_v1::node_at(htdl_v1::event_get(1));'
            'if(htdl_v1::node_kind(n)==9){return htdl_v1::state_set(0,htdl_v1::state_get(0)+1);}}return htdl_v1::state_get(0);}')
        print('PAGE_READER_CANDIDATE '+json.dumps(dict(worker_sha256=hashlib.sha256(cls.worker.read_bytes()).hexdigest(),mode='reference' if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else 'optimized')),flush=True)
    @classmethod
    def tearDownClass(cls): cls.folder.cleanup()
    compile_page=classmethod(worker.PageWorker.compile_page.__func__)
    def setUp(self):
        self.temp=self.out/self._testMethodName;self.temp.mkdir();self.data={}
    def binary(self,data):
        key='code_'+hashlib.sha256(data).hexdigest()[:12];self.data[key]=data
        return f'slice_of({key},0,{len(data)})'
    def execute(self,body):
        prelude=''.join(f'own {key}:*byte=try_alloc<byte>({len(data)});assert({key}!=null);'+''.join(f'{key}[{i}]=byte({b});' for i,b in enumerate(data)) for key,data in self.data.items())
        source=self.temp/'host.assis';source.write_text(PREFIX+'safe fn main():int{'+prelude+body.replace('assert(','\nassert(')+'return 0;}',encoding='utf-8')
        binary=self.temp/('host.exe' if os.name=='nt' else 'host')
        flags=['--no-opt'] if os.environ.get('ASSIS_WORKER_NO_OPT')=='1' else []
        r=subprocess.run([str(base.COMPILER),'build',str(source),'-o',str(binary),*flags],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        run=subprocess.run([str(binary)],env=self.env,capture_output=True,text=True,timeout=30,cwd=ROOT)
        match=re.search(r'host\.assis:(\d+)',run.stderr)
        context=source.read_text(encoding='utf-8').splitlines()[int(match[1])-1] if match else ''
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'',''),context)
    def setup(self,content='<div type=button id=add>Add</div>',code=None,grants='new pagereader::Grants(true,false)',commit=True):
        return ('own s:pagereader::Session=try_new pagereader::Session(32000000,250000,7,19,23);assert(s!=null && s.is_open());'
            'val limits:pagereader::Limits=new pagereader::Limits(0,16,100000,1000,3000);'
            'assert(s.prepare('+literal(str(self.worker))+','+literal(document(content))+','+self.binary(self.code if code is None else code)+','+
            ('false' if os.name=='nt' else 'true')+',300,220,16,cells,limits,'+grants+',monotonic_ms())==0);ready(s);'+('assert(s.commit());' if commit else ''))
    def prepare(self,content,code=None,metric='cells',path=None):
        return ('s.prepare('+literal(str(self.worker) if path is None else path)+','+literal(document(content))+','+self.binary(self.code if code is None else code)+','+
            ('false' if os.name=='nt' else 'true')+',300,220,16,'+metric+',limits,new pagereader::Grants(true,false),monotonic_ms())')
    def test_keyboard_accessible_and_pointer_actions_use_same_sdk_projection(self):
        self.execute(self.setup()+
            'drain(s,0);assert(s.dispatch(1,event(3,9,1,1)).status==0);'
            'val a:pagereader::Action=s.dispatch(1,event(3,13,1,2));assert(a.status==0 && a.change.kind==2);drain(s,1);'
            'assert(s.dispatch(1,event(11,1,1,3)).status==0);drain(s,2);'
            's.dispatch(1,event(7,40,22,4));s.dispatch(1,event(8,40,22,5));drain(s,3);s.close();assert(!s.worker_alive());')
    def test_hidden_disabled_stale_document_request_and_forged_window_do_not_post(self):
        self.execute(self.setup('<div type=button disabled=true>Disabled</div><div type=button hidden=true>Hidden</div><div type=button>Active</div>')+
            'drain(s,0);assert(s.dispatch(1,event(11,1,1,1)).change.kind==0);'
            'assert(s.dispatch(2,event(11,1,2,2)).status== -2);'
            'assert(s.dispatch(1,new window::Event(0,11,8,1,1,2,3)).change.kind==0);'
            'assert(s.dispatch(1,event(3,9,1,4)).change.kind==1);s.dispatch(1,event(3,13,1,5));'
            'assert(s.dispatch(1,event(3,13,1,5)).change.kind==0);drain(s,1);assert(s.result().state==1);')
    def test_failed_parse_layout_worker_load_and_abort_keep_active_and_fresh_ids(self):
        self.execute(self.setup()+'drain(s,0);'
            'assert('+self.prepare('<div>bad')+'!=0 && s.document_id()==1 && !s.has_pending());'
            'assert('+self.prepare('<div type=button>Unavailable</div>',path='relative-worker')+'== -1 && s.document_id()==1 && !s.has_pending());'
            'assert('+self.prepare('<div type=button>Other</div>',metric='fail')+'== -4 && s.document_id()==1);'
            'assert('+self.prepare('<div type=button>Other</div>',code=b'bad'+bytes(16))+'==0);'
            'let rejected:bool=false;for(let i:int=0;i<5000;i++){if(s.advance(monotonic_ms())<0){rejected=true;break;}sleep_ms(1);}'
            'assert(rejected && !s.has_pending() && s.document_id()==1 && s.worker_alive());'
            'assert('+self.prepare('<div type=button>Other</div>')+'==0);ready(s);val used:int=s.candidate_id();s.abort();'
            'assert(s.document_id()==1 && s.worker_alive());s.dispatch(1,event(3,9,1,1));s.dispatch(1,event(3,13,1,2));drain(s,1);'
            'assert('+self.prepare('<div type=button>Final</div>')+'==0);ready(s);assert(s.candidate_id()>used && s.commit());assert(s.document_id()>1);drain(s,0);')
    def test_navigation_freezes_actions_and_drops_queued_old_events(self):
        self.execute(self.setup()+'drain(s,0);s.dispatch(1,event(3,9,1,1));s.dispatch(1,event(3,13,1,2));assert(s.queued()==1);'
            'assert('+self.prepare('<div type=button id=add>New</div>')+'==0);assert(s.dispatch(1,event(3,13,1,3)).status== -2);'
            'ready(s);assert(s.document_id()==1);assert(s.commit() && s.document_id()==2 && s.queued()==0);drain(s,0);'
            'assert(s.dispatch(1,event(3,13,1,4)).status== -2 && s.queued()==0);'
            's.dispatch(2,event(3,9,1,5));s.dispatch(2,event(3,13,1,6));drain(s,1);')
    def test_queue_backpressure_is_explicit_and_close_cancels_both_generations(self):
        self.execute(self.setup()+'drain(s,0);s.dispatch(1,event(3,9,1,1));'
            'for(let i:int=0;i<32;i++){assert(s.dispatch(1,event(3,13,1,i*2+2)).status==0);s.dispatch(1,event(3,13,0,i*2+3));}assert(s.queued()==32);'
            'assert(s.dispatch(1,event(3,13,1,66)).status==1 && s.queued()==32);'
            'drain(s,32);assert(s.result().state==32);'
            'assert('+self.prepare('<div type=button>Candidate</div>')+'==0);s.close();s.close();'
            'assert(!s.is_open() && !s.has_pending() && !s.worker_alive() && s.queued()==0 && s.advance(monotonic_ms())== -9);')
    def test_denied_document_grant_never_becomes_authority_from_source(self):
        code=self.compile_page('import "std/page.assis";safe fn main():int{htdl_v1::node_count();return htdl_v1::last_error();}')
        self.execute(self.setup(code=code,grants='new pagereader::Grants(false,false)')+'drain(s,-2);assert(s.result().state==0);')
    def test_worker_fuel_failure_preserves_reader_and_independent_neighbor(self):
        hostile=self.compile_page('safe fn main():int{while(true){}return 0;}')
        neighbor=self.compile_page('safe fn main():int{return 42;}')
        self.execute(self.setup(code=hostile)+
            'own n:pagereader::Session=try_new pagereader::Session(32000000,250000,8,20,24);assert(n!=null);'
            'assert(n.prepare('+literal(str(self.worker))+','+literal(document('<div type=paragraph>Neighbor</div>'))+','+self.binary(neighbor)+','+
            ('false' if os.name=='nt' else 'true')+',300,220,16,cells,limits,new pagereader::Grants(false,false),monotonic_ms())==0);ready(n);assert(n.commit());'
            'let stopped:bool=false;for(let i:int=0;i<5000;i++){assert(n.advance(monotonic_ms())>=0);if(s.advance(monotonic_ms())<0){stopped=true;break;}sleep_ms(1);}'
            'assert(stopped && s.has_active() && !s.worker_alive() && s.active_reader().item_count()==1);'
            'drain(n,42);assert(n.worker_alive());'
            'assert(s.dispatch(1,event(3,9,1,1)).status==0);assert(s.dispatch(1,event(3,13,1,2)).status== -9);'
            'assert('+self.prepare('<div type=button>Recovered</div>')+'==0);ready(s);assert(s.commit());drain(s,0);')
    def test_counter_grant_is_explicit_and_both_grant_steps_can_complete(self):
        code=self.compile_page('import "std/page.assis";safe fn main():int{return htdl_v1::counter_add(1);}')
        self.execute(self.setup(code=code,grants='new pagereader::Grants(true,true)')+'drain(s,1);assert(s.result().counter==1);')
    def test_prepare_copies_mutable_input_before_async_load(self):
        source=document('<div type=button>Add</div>').encode()
        src=self.binary(source);code=self.binary(self.code)
        source_name=src.split('(')[1].split(',')[0];code_name=code.split('(')[1].split(',')[0]
        self.execute('own s:pagereader::Session=try_new pagereader::Session(32000000,250000,7,19,23);assert(s!=null);'
            'assert(s.prepare('+literal(str(self.worker))+','+src+','+code+','+('false' if os.name=='nt' else 'true')+
            ',300,220,16,cells,new pagereader::Limits(0,16,100000,1000,3000),new pagereader::Grants(true,false),monotonic_ms())==0);'
            +source_name+'[0]=byte(0);'+code_name+'[0]=byte(0);ready(s);assert(s.commit());drain(s,0);'
            's.dispatch(1,event(3,9,1,1));s.dispatch(1,event(3,13,1,2));drain(s,1);')
    @unittest.skipUnless(os.name=='nt','Windows accessible publication')
    def test_native_accessibility_publication_failure_keeps_both_active(self):
        self.execute(self.setup(commit=False)+'own w:window::Window=try_new window::Window(7,300,220,"Page Reader");assert(w!=null && w.opened());'
            'assert(s.publish(w)==0);drain(s,0);assert('+self.prepare('<div type=button disabled=true>New</div>')+'==0);ready(s);'
            'own closed:window::Window=try_new window::Window(9,300,220,"Closed");assert(closed!=null);closed.close();'
            'assert(s.publish(closed)== -2 && s.document_id()==1 && s.has_pending() && s.worker_alive());'
            'assert(s.publish(w)==0 && s.document_id()==2);drain(s,0);s.close();w.close();')

if __name__=='__main__': unittest.main(verbosity=2)

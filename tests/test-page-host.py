"""Real SDK pages, HTDL snapshots, independent event model and hostile lifetimes."""
import importlib.util
import random
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('backend',Path(__file__).with_name('test-page-backend.py'))
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
vm=backend.vm;base=backend.base
spec=importlib.util.spec_from_file_location('parser',Path(__file__).with_name('test-htdl-parser.py'))
parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
SDK='import "std/page.assis";'
PREFIX='''import "std/pagehost.assis";
safe fn drain(borrow mut p:pagehost::Page):void{
 let done:bool=false;for(let i:int=0;i<10000;i++){val r:int=p.tick(7);if(r!=1){assert(r==2);done=true;break;}}assert(done);
}
'''

def data_buffer(data,name='code'):
    return f'own {name}:*byte=try_alloc<byte>({len(data)});assert({name}!=null);'+''.join(f'{name}[{i}]=byte({b});' for i,b in enumerate(data))

def store(body='<div type="paragraph" hidden="true">Text</div><div type="button" disabled="true">Button</div>'):
    return ('own store:documents::Store=try_new documents::Store(32000000,250000,1000);assert(store!=null);'
        'assert(htdl::load(store,1,'+parser.literal(parser.document(body))+').code==0);')

def page(data,name='p',instance=7,origin=11,fuel=100000,calls=1000):
    return data_buffer(data,name+'_code')+f'own {name}:pagehost::Page=try_new pagehost::Page({instance},{origin});assert({name}!=null && {name}.is_open());'+f'assert({name}.prepare(store.active_document(),slice_of({name}_code,0,len({name}_code)),0,16,{fuel},{calls})==0 && {name}.commit());'

class PageHost(backend.PageBackend):
    def execute_host(self,body,expected=''):
        self.accepted(PREFIX+'safe fn main():int{'+body+'return 0;}',expected)

    def test_sdk_events_state_and_queue_against_independent_model(self):
        code=self.compile_page(SDK+'safe fn main():int{val old:int=htdl_v1::state_get(0);'
            'val delta:int=htdl_v1::event_get(0)+htdl_v1::event_get(1);return htdl_v1::state_set(0,old+delta);}')
        body=store()+page(code)+'drain(p);assert(p.result()==1 && p.state_get(0)==1);'
        rng=random.Random(20261102);answer=1
        for request in range(2,82):
            kind,value=rng.choice([2,3]),rng.randrange(-30,30);answer+=kind+value
            body+=f'assert(p.post(7,11,p.generation(),1,{request},{kind},{value})==0);drain(p);assert(p.result()=={answer} && p.state_get(0)=={answer});'
        self.execute_host(body+'assert(p.tick(7)==0);')

    def test_document_projection_matches_xml_semantics_and_default_deny(self):
        code=self.compile_page(SDK+'safe fn main():int{val count:int=htdl_v1::node_count();if(count<0){return count;}'
            'let sum:int=0;for(let i:int=0;i<count;i++){val node:int=htdl_v1::node_at(i);'
            'sum+=10*htdl_v1::node_kind(node)+htdl_v1::node_flags(node);}return sum;}')
        # Independent XML corpus, not the host traversal or tree encoding.
        import xml.etree.ElementTree as ET
        body='<div type="paragraph" hidden="true">Text</div><div type="button" disabled="true">Button</div>'
        kinds={'document':1,'head':2,'title':3,'body':4,'paragraph':6,'button':9}
        expected=sum(10*kinds[n.attrib['type']]+int(n.attrib.get('hidden')=='true')+2*int(n.attrib.get('disabled')=='true') for n in ET.fromstring(parser.document(body)).iter())
        self.execute_host(store(body)+page(code)+'drain(p);assert(p.result()== -2);'
            'assert(!p.grant_document(8,11,p.generation(),1) && !p.grant_document(7,12,p.generation(),1));'
            'assert(!p.grant_document(7,11,p.generation()+1,1) && !p.grant_document(7,11,p.generation(),2));'
            'assert(p.grant_document(7,11,p.generation(),1));assert(p.post(7,11,p.generation(),1,2,2,0)==0);drain(p);'
            f'assert(p.result()=={expected});p.revoke_document();assert(!p.grant_document(7,11,p.generation(),1));'
            'assert(p.post(7,11,p.generation(),1,3,2,0)==0);drain(p);assert(p.result()== -2);')

    def test_four_arguments_left_to_right_nested_calls_and_counter_authority(self):
        code=self.compile_page(SDK+'safe fn combine(a:int,b:int,c:int,d:int):int{return a*1000+b*100+c*10+d;}'
            'safe fn add(x:int):int{return htdl_v1::counter_add(x);}'
            'safe fn main():int{return combine(add(1),add(1),add(1),add(1));}')
        self.execute_host(store()+page(code)+'assert(!p.grant_counter(7,12,p.generation()));'
            'assert(p.grant_counter(7,11,p.generation()));drain(p);assert(p.result()==1234 && p.counter()==4);'
            +page(code,'denied',instance=8)+'assert(denied.tick(10000)== -2 && denied.counter()==0);')

    def test_pending_reply_requires_full_identity_event_call_and_no_replay(self):
        ops=[vm.instruction(1,immediate=42),vm.instruction(12,1,0,immediate=2),vm.instruction(0,1)]
        data=b'ASV2'+vm.program(ops)[4:]
        self.execute(vm.load(data)+'assert(v.begin_event(1,7,1,1));assert(v.run(10)==3);'
            'assert(v.waiting_import()==2 && v.waiting_argument()==42 && v.waiting_call()==1);'
            'assert(!v.reply(2,7,1,1,1,99) && !v.reply(1,8,1,1,1,99) && !v.reply(1,7,2,1,1,99));'
            'assert(!v.reply(1,7,1,2,1,99) && !v.reply(1,7,1,1,2,99));assert(v.run(10)==3);'
            'assert(v.reply(1,7,1,1,1,99) && !v.reply(1,7,1,1,1,0));assert(v.run(10)==2 && v.result()==99);'
            'assert(!v.begin_event(1,7,1,1));assert(v.begin_event(1,7,1,2));assert(v.run(10)==3);'
            'assert(!v.reply(1,7,1,1,1,0));v.close();assert(!v.reply(1,7,1,2,2,0) && !v.begin_event(1,7,1,3));')

    def test_queue_backpressure_request_replay_and_navigation_epoch(self):
        code=self.compile_page('safe fn main():int{return 42;}')
        body=store()+page(code)
        body+='assert(p.post(7,11,1,1,1,2,0)== -2);assert(p.post(7,11,1,1,2,0,0)== -1);'
        body+='for(let r:int=2;r<=32;r++){assert(p.post(7,11,1,1,r,2,r)==0);}assert(p.queue_size()==32);'
        body+='assert(p.post(7,11,1,1,33,2,0)==1);drain(p);assert(p.post(7,11,1,1,33,2,0)==0);'
        body+='assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,10000,100)==0);'
        body+='val old:int=p.generation();assert(p.commit() && p.generation()>old && p.queue_size()==1);'
        body+='assert(p.post(7,11,old,1,100,2,0)== -2);drain(p);assert(p.tick(100)==0 && p.result()==42);'
        body+='p.close();p.close();assert(p.post(7,11,p.generation(),1,200,2,0)== -9 && p.tick(1)== -9);'
        self.execute_host(body)

    def test_old_node_tokens_fail_after_reload_and_revocation(self):
        code=self.compile_page(SDK+'safe fn main():int{return htdl_v1::node_kind(2049);}')
        self.execute_host(store()+page(code)+'assert(p.grant_document(7,11,1,1));drain(p);assert(p.result()==1);'
            'assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,10000,100)==0 && p.commit());'
            'assert(p.grant_document(7,11,2,1));drain(p);assert(p.result()== -2);')

    def test_loop_fuel_and_revocation_do_not_starve_neighbor(self):
        loop=self.compile_page('safe fn main():int{while(true){}return 0;}')
        fast=self.compile_page('safe fn main():int{return 42;}')
        self.execute_host(store()+page(loop,fuel=90)+page(fast,'neighbor',instance=8)+
            'for(let i:int=0;i<9;i++){assert(p.tick(3)==1);neighbor.tick(3);}assert(neighbor.result()==42);'
            'assert(p.steps()==27);p.revoke();assert(p.tick(10)== -2 && p.queue_size()==0);'
            'assert(neighbor.post(8,11,1,1,2,2,0)==0);drain(neighbor);assert(neighbor.result()==42);'
            +page(loop,'exhausted',instance=9,fuel=5)+'assert(exhausted.tick(10)== -3 && neighbor.tick(1)==0);')

    def test_invalid_sdk_ranges_host_quota_and_abort_preserve_live_instance(self):
        code=self.compile_page(SDK+'safe fn main():int{return htdl_v1::state_get(32)+htdl_v1::state_set(-1,7)+htdl_v1::event_get(7);}')
        self.execute_host(store()+page(code)+'drain(p);assert(p.result()== -3);'
            'own bad:*byte=try_alloc<byte>(1);assert(p.prepare(store.active_document(),slice_of(bad,0,1),0,16,100,100)== -1);'
            'assert(p.generation()==1 && !p.has_pending() && p.result()== -3);'
            'assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,100,100)==0);'
            'assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,100,100)== -12);'
            'p.abort();assert(!p.has_pending() && p.generation()==1);'
            +page(code,'quota',instance=8,calls=1)+'for(let i:int=0;i<100;i++){if(quota.tick(100)<0){break;}}assert(quota.status()== -8);')

    def test_oom_prepare_rollback_and_allocation_free_commit(self):
        code=self.compile_page('safe fn main():int{return 42;}')
        setup,drain,cleanup=parser.preparation.exhaustion()
        body=store()+page(code)+'drain(p);unsafe{'+setup+drain
        body+='assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,100,100)== -4);'
        body+='assert(!p.has_pending() && p.generation()==1 && p.result()==42);'+cleanup+'}'
        parser.preparation.BufferPreallocation.fault_program(self,PREFIX+'safe fn main():int{'+body+'return 0;}','')
        body=store()+page(code)+'drain(p);assert(p.prepare(store.active_document(),slice_of(p_code,0,len(p_code)),0,16,100,100)==0);unsafe{'+setup+drain
        body+='assert(p.commit() && p.generation()==2);drain(p);assert(p.result()==42);'+cleanup+'}'
        parser.preparation.BufferPreallocation.fault_program(self,PREFIX+'safe fn main():int{'+body+'return 0;}','')

    def test_group_round_robin_deadlines_and_non_reused_slots(self):
        loop=self.compile_page('safe fn main():int{while(true){}return 0;}')
        fast=self.compile_page('safe fn main():int{return 42;}')
        self.execute_host(store()+page(loop)+page(fast,'neighbor',instance=8)+
            'own g:pagehost::Group=try_new pagehost::Group();assert(g!=null && g.is_open());'
            'assert(g.add(move(p),10)==0 && g.add(move(neighbor),0)==1);'
            'assert(g.poll(-1,1,1).visited== -1 && g.poll(0,0,1).visited== -1);'
            'assert(g.poll(0,1,1).yielded==1 && g.page(0).steps()==1 && g.page(1).steps()==0);'
            'for(let i:int=0;i<7;i++){g.poll(0,1,1);}assert(g.page(1).result()==42 && g.page(0).steps()==4);'
            'val expired:pagehost::Poll=g.poll(10,2,1);assert(expired.expired==1 && expired.failed==1);'
            'assert(g.page(0).status()== -2 && g.page(1).result()==42);assert(g.poll(9,1,1).visited== -1);'
            'assert(g.close_page(0));own third:pagehost::Page=try_new pagehost::Page(9,11);'
            'assert(g.add(move(third),0)==2 && g.size()==3 && !g.page(0).is_open());g.close();assert(g.poll(11,1,1).visited== -1);')

    def test_sdk_error_channel_distinguishes_negative_values_and_invalid_slots(self):
        code=self.compile_page(SDK+'safe fn main():int{htdl_v1::state_set(0,-1);val value:int=htdl_v1::state_get(0);'
            'if(htdl_v1::last_error()!=0){return 99;}htdl_v1::state_get(32);val bad:int=htdl_v1::last_error();'
            'val again:int=htdl_v1::last_error();htdl_v1::state_get(0);return value+bad+again+htdl_v1::last_error();}')
        self.execute_host(store()+page(code)+'drain(p);assert(p.result()== -3 && p.state_get(0)== -1);')

    def test_projection_is_immutable_and_never_addresses_another_page(self):
        code=self.compile_page(SDK+'safe fn main():int{val last:int=htdl_v1::node_count()-1;return htdl_v1::node_kind(htdl_v1::node_at(last));}')
        self.execute_host(store('<div type="button">A</div>')+page(code)+
            'assert(p.grant_document(7,11,1,1));drain(p);assert(p.result()==9);'
            'assert(htdl::load(store,2,'+parser.literal(parser.document('<div type="paragraph">B</div>'))+').code==0);'
            +page(code,'other',instance=8,origin=12)+
            'assert(other.grant_document(8,12,1,2));drain(other);assert(other.result()==6);'
            'assert(!p.grant_document(7,11,1,2));assert(p.post(7,11,1,1,2,2,0)==0);drain(p);assert(p.result()==9);')

    def test_shipped_page_and_local_native_host(self):
        import subprocess
        code=self.compile_page((base.ROOT/'exemplos/pages/counter.assis').read_text(encoding='utf-8'))
        artifact=self.temp/'counter.asv2';artifact.write_bytes(code)
        for flags in ((),('--no-opt',)):
            binary=self.temp/'host.exe'
            result=self.invoke('build',base.ROOT/'exemplos/48_page_runtime.assis','-o',binary,*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([binary,artifact],capture_output=True,text=True,timeout=10)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'PAGE 2 STATE 2\n',''))

if __name__=='__main__':
    for cls in (base.Evolution,vm.PageVM,backend.PageBackend):
        for name in list(vars(cls)):
            if name.startswith('test_'):delattr(cls,name)
    unittest.main(verbosity=2)

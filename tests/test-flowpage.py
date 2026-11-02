"""Whole-page FS transactions, exact dirtiness and live semantic identities."""
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('fs_tests',Path(__file__).with_name('test-fluxstyle.py'))
fs=importlib.util.module_from_spec(spec);spec.loader.exec_module(fs)
base=fs.base;literal=fs.literal;ROOT=base.ROOT
PREFIX='import "std/flowpage.assis";'
SOURCE='flow Card { input n: number = state("n", 1, scope: node); 8px / n -> target.offsetY; } bind .card to Card;'
DOC=fs.catalog.document('<div type=container id=a class=card></div><div type=button id=b class=card>B</div>')

def setup(source=SOURCE,doc=DOC,capacity=8):
    return (f'own page:flowpage::Page=try_new flowpage::Page({literal(source)},{capacity},2048,10000000);'
        'assert(page!=null && page.is_open());own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);'
        'assert(input!=null && input.is_ready());own store:documents::Store=try_new documents::Store(4000000,4000,100);'
        f'assert(store!=null);assert(htdl::load_catalog(store,1,{literal(doc)}).code==0);'
        'val a:doctree::NodeId=htdl::find_id(store.active_document().nodes(),utf8("a"));'
        'val b:doctree::NodeId=htdl::find_id(store.active_document().nodes(),utf8("b"));'
        'val n:int=page.input_index(utf8("Card"),utf8("n"));')

def value(node,expected):
    return f'assert(page.value(store.active_document(),{node},15).code==0 && page.value(store.active_document(),{node},15).value=={expected});'

class FlowPage(base.Evolution):
    fault_program=fs.FluxStyle.fault_program
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)
    def execute(self,body):self.accepted(PREFIX+'safe fn main():int{'+body+'return 0;}')

    def test_commit_is_complete_and_private_until_success(self):
        self.execute(setup()+'assert(page.refresh(store.active_document(),input)==0 && page.size()==3 && page.version()==1);'
            'assert(page.begin(store.active_document())==0);assert(input.set(n,2,2*65536));'
            'assert(page.stage(store.active_document(),a,input)==0);'+value('a',8*65536)+
            'assert(page.commit(store.active_document())==204 && page.version()==1);'+value('a',8*65536)+
            'page.abort();assert(page.refresh(store.active_document(),input)==0 && page.version()==2);'+value('a',4*65536)+value('b',4*65536))

    def test_failure_in_last_node_discards_every_candidate_output_and_retry_works(self):
        self.execute(setup()+'assert(page.refresh(store.active_document(),input)==0);'
            'assert(page.begin(store.active_document())==0);assert(input.set(n,2,2*65536));'
            'assert(page.stage(store.active_document(),a,input)==0);assert(input.set(n,2,0));'
            'assert(page.stage(store.active_document(),b,input)==402 && page.diagnostic().code==402);'
            'assert(page.diagnostic_node().slot==b.slot && page.commit(store.active_document())==402 && page.version()==1);'+
            value('a',8*65536)+value('b',8*65536)+
            'assert(page.diagnostic().end>page.diagnostic().start);page.abort();input.clear();'
            'assert(page.refresh(store.active_document(),input)==0 && page.version()==2);'+value('a',8*65536))

    def test_exact_node_context_cache_and_independent_equal_input_objects(self):
        self.execute(setup()+'assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==3 && page.cache_hits()==0);'
            'assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==0 && page.cache_hits()==3);'
            'own other:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);assert(other!=null && other.is_ready());'
            'assert(page.refresh(store.active_document(),other)==0 && page.evaluations()==0 && page.cache_hits()==3);'
            'assert(page.begin(store.active_document())==0);'
            'for(let i:int=page.size()-1;i>=0;i--){val node:doctree::NodeId=page.node_at(i);input.clear();'
            'if(node.slot==a.slot){assert(input.set(n,2,2*65536));}assert(page.stage(store.active_document(),node,input)==0);}'
            'assert(page.commit(store.active_document())==0 && page.evaluations()==1 && page.cache_hits()==2);'+value('a',4*65536)+value('b',8*65536))

    def test_absence_is_distinct_from_explicit_zero_and_abort_does_not_poison_cache(self):
        source='flow Card { input n: bool = state("n", true, scope: node); choose(n,8px,0px) -> target.offsetY; } bind .card to Card;'
        self.execute(setup(source)+'assert(page.refresh(store.active_document(),input)==0);'
            'assert(input.set(n,1,0));assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==3);'+value('a',0)+
            'assert(page.begin(store.active_document())==0);input.clear();assert(page.stage(store.active_document(),a,input)==0);page.abort();'+value('a',0)+
            'assert(input.set(n,1,0));assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==0 && page.cache_hits()==3);'
            'input.clear();assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==3);'+value('a',8*65536))

    def test_shared_page_cells_require_one_effective_value_across_nodes(self):
        source=SOURCE.replace(', scope: node','')
        self.execute(setup(source)+'assert(page.refresh(store.active_document(),input)==0);assert(page.begin(store.active_document())==0);'
            'assert(input.set(n,2,2*65536));assert(page.stage(store.active_document(),a,input)==0);input.clear();'
            'assert(page.stage(store.active_document(),b,input)==304 && page.commit(store.active_document())==304 && page.version()==1);'
            'page.abort();assert(input.set(n,2,2*65536));assert(page.refresh(store.active_document(),input)==0);'+value('a',4*65536)+value('b',4*65536))

    def test_page_cell_aliases_compare_effective_values_instead_of_presence(self):
        source=('flow Card { input n: number = state("n", 1); 8px/n -> target.offsetY; } '
                'flow Other { input alias: number = state("n", 1); } bind .card to Card;')
        self.execute(setup(source)+'val alias:int=page.input_index(utf8("Other"),utf8("alias"));'
            'assert(page.begin(store.active_document())==0);'
            'page.abort();assert(page.refresh(store.active_document(),input)==0);'
            'assert(page.begin(store.active_document())==0);for(let i:int=0;i<page.size();i++){'
            'input.clear();if(i==1){assert(input.set(alias,2,2*65536));}else{assert(input.set(n,2,2*65536));}val node:doctree::NodeId=page.node_at(i);'
            'assert(page.stage(store.active_document(),node,input)==0);}assert(page.commit(store.active_document())==0);'+value('a',4*65536))

    def test_live_semantic_mutation_invalidates_candidate_without_rolling_back_disabled(self):
        # Mutating the Document is legal on Store.candidate; Page does not own it.
        source='flow Card { input off: bool=self.disabled; choose(off,1px/0,8px) -> target.offsetY; } bind #b to Card;'
        self.execute(setup(source)+
            f'assert(htdl::stage(store,2,{literal(DOC)},0).code==0);'
            'assert(page.refresh(store.candidate(),input)==0);val button:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("b"));'
            'val before:int=store.candidate().semantic_version();assert(page.begin(store.candidate())==0);'
            'match(store.candidate().try_append(button,108,utf8("0000000000000000true"))){Appended(id){}Rejected(code){assert(false);}}'
            'assert(store.candidate().semantic_version()>before);assert(page.commit(store.candidate())==204);page.abort();'
            'assert(page.refresh(store.candidate(),input)==402 && page.version()==1);'
            'val disabled:doctree::NodeId=htdl::attribute(store.candidate().nodes(),button,8);'
            'assert(htdl::value_equals(store.candidate().nodes(),disabled,utf8("true")));'
            'assert(page.value(store.candidate(),button,15).value==8*65536);')

    def test_document_mutation_clock_success_failure_and_no_layout_growth(self):
        self.execute('assert(documents::document_bytes()==256);own d:documents::Document=try_new documents::Document(1,1000000,100,100,utf8(""));'
            'assert(d!=null && d.is_open() && d.semantic_version()==0);let root:doctree::NodeId=new doctree::NodeId();'
            'match(d.try_append(new doctree::NodeId(),1,utf8(""))){Appended(id){root=id;}Rejected(code){assert(false);}}'
            'assert(d.semantic_version()==1);assert(!d.try_set_text(new doctree::NodeId(),utf8("bad")) && d.semantic_version()==1);'
            'assert(d.try_set_text(root,utf8("ok")) && d.semantic_version()==2);let child:doctree::NodeId=new doctree::NodeId();'
            'match(d.try_append(root,1,utf8(""))){Appended(id){child=id;}Rejected(code){assert(false);}}'
            'assert(d.semantic_version()==3);assert(!d.try_reparent(root,child) && d.semantic_version()==3);'
            'assert(d.try_reparent(child,root) && d.semantic_version()==4);assert(d.erase_subtree(child) && d.semantic_version()==5);'
            'assert(!d.erase_subtree(child) && d.semantic_version()==5);')

    def test_semantic_edits_conservatively_dirty_all_nodes_and_removed_ids_expire(self):
        self.execute(setup()+f'assert(htdl::stage(store,2,{literal(DOC)},0).code==0);'
            'assert(page.refresh(store.candidate(),input)==0);val node:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("a"));'
            'assert(store.candidate().try_set_text(node,utf8("")));assert(page.refresh(store.candidate(),input)==0 && page.evaluations()==3);'
            'assert(store.candidate().erase_subtree(node));assert(!page.has(store.candidate(),node,15));'
            'assert(page.refresh(store.candidate(),input)==0 && page.size()==2 && page.evaluations()==2);'
            'assert(!page.has(store.active_document(),a,15));assert(page.value(store.candidate(),node,15).code==204);')

    def test_duplicate_forged_stale_busy_and_closed_calls_are_rejected(self):
        self.execute(setup()+'assert(page.refresh(store.active_document(),input)==0);assert(page.begin(store.active_document())==0);'
            'assert(page.refresh(store.active_document(),input)==204);assert(page.stage(store.active_document(),a,input)==0);'
            'assert(page.stage(store.active_document(),a,input)==204 && page.commit(store.active_document())==204);page.abort();'
            'assert(page.begin(store.active_document())==0);assert(page.stage(store.active_document(),new doctree::NodeId(99,a.slot,a.generation),input)==204);page.abort();'
            'assert(page.refresh(store.active_document(),input)==0 && page.version()==2);'
            f'assert(htdl::load_catalog(store,2,{literal(DOC)}).code==0);'
            'assert(!page.has(store.active_document(),a,15));assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==3);'
            'page.close();assert(!page.is_open() && page.size()==0 && !page.has(store.active_document(),a,15));'
            'assert(page.begin(store.active_document())==204);page.close();')

    def test_recycled_slot_and_textual_id_never_inherit_old_outputs(self):
        self.execute(setup()+f'assert(htdl::stage(store,2,{literal(DOC)},0).code==0);'
            'assert(page.refresh(store.candidate(),input)==0);val old:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("a"));'
            'val parent:doctree::NodeId=store.candidate().nodes().parent(old);assert(store.candidate().erase_subtree(old));'
            'let fresh:doctree::NodeId=new doctree::NodeId();'
            'match(store.candidate().try_append(parent,1,utf8("0000000000000000"))){Appended(id){fresh=id;}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,101,utf8("0000000000000000container"))){Appended(id){}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,105,utf8("0000000000000000a"))){Appended(id){}Rejected(code){assert(false);}}'
            'match(store.candidate().try_append(fresh,106,utf8("0000000000000000card"))){Appended(id){}Rejected(code){assert(false);}}'
            'assert(old.slot==fresh.slot && old.generation!=fresh.generation);'
            'assert(!page.has(store.candidate(),old,15) && !page.has(store.candidate(),fresh,15));'
            'assert(page.refresh(store.candidate(),input)==0);assert(page.value(store.candidate(),fresh,15).value==8*65536);')

    def test_changed_selector_removes_old_producer_only_on_successful_commit(self):
        self.execute(setup()+f'assert(htdl::stage(store,2,{literal(DOC)},0).code==0);'
            'assert(page.refresh(store.candidate(),input)==0);val node:doctree::NodeId=htdl::find_id(store.candidate().nodes(),utf8("a"));'
            'val classes:doctree::NodeId=htdl::attribute(store.candidate().nodes(),node,6);'
            'assert(store.candidate().try_set_text(classes,utf8("0000000000000000other")));'
            'assert(page.has(store.candidate(),node,15));assert(page.refresh(store.candidate(),input)==0);'
            'assert(!page.has(store.candidate(),node,15) && page.value(store.candidate(),node,15).code==204);')

    def test_capacity_and_reservation_boundaries_and_wrong_input_shape(self):
        self.execute(setup(capacity=2)+'assert(page.refresh(store.active_document(),input)==401 && page.version()==0);'
            'assert(flowpage::reservation(0,0,1)==-1 && flowpage::reservation(65537,1,1)==-1);'
            'assert(flowpage::reservation(0,257,1)==-1 && flowpage::reservation(0,1,2049)==-1);'
            f'val budget:int=flowpage::reservation(len({literal(SOURCE)}),8,2048);'
            f'own short:flowpage::Page=try_new flowpage::Page({literal(SOURCE)},8,2048,budget-1);'
            'assert(short!=null && !short.is_open() && short.diagnostic().code==401);'
            f'own exact:flowpage::Page=try_new flowpage::Page({literal(SOURCE)},8,2048,budget);'
            'assert(exact!=null && exact.is_open() && exact.storage_reservation()==budget);'
            'own wrong:fluxstyle::Inputs=try_new fluxstyle::Inputs(1);assert(exact.refresh(store.active_document(),wrong)==204 && exact.version()==0);')

    def test_hidden_nodes_are_evaluated_and_conflicting_producers_reject_whole_page(self):
        doc=fs.catalog.document('<div type=container id=a class=card hidden=true></div><div type=container id=b class="card conflict"></div>')
        source=SOURCE+'flow Other { 1px -> target.offsetY; } bind .conflict to Other;'
        self.execute(setup(source,doc)+'assert(page.refresh(store.active_document(),input)==302 && page.version()==0);'
            'assert(page.diagnostic_node().slot==b.slot);')

    def test_randomized_per_node_transactions_against_rational_model(self):
        rng=random.Random(2026110204)
        body=setup()+'assert(page.refresh(store.active_document(),input)==0);'
        current=[8*65536,8*65536];version=1
        for _ in range(48):
            denominators=[rng.choice([0,1,2,3,4,7,8]),rng.choice([0,1,2,3,4,7,8])]
            body+='assert(page.begin(store.active_document())==0);'
            # Body has no producer; its input is separate from either node cell.
            body+='{input.clear();val body:doctree::NodeId=page.node_at(0);assert(page.stage(store.active_document(),body,input)==0);}'
            failed=False
            for index,node in enumerate(['a','b']):
                body+=f'input.clear();assert(input.set(n,2,{denominators[index]}*65536));'
                expected=402 if denominators[index]==0 else 0
                body+=f'assert(page.stage(store.active_document(),{node},input)=={expected});'
                if expected:failed=True;break
            if failed:body+='assert(page.commit(store.active_document())==402);page.abort();'
            else:
                body+='assert(page.commit(store.active_document())==0);';version+=1
                current=[fs.nearest_positive(Fraction(8*65536,d)) for d in denominators]
            body+=f'assert(page.version()=={version});'+value('a',current[0])+value('b',current[1])
        self.execute(body)

    def test_real_allocator_denial_preserves_bank_and_cache_hits_need_no_allocation(self):
        before=setup()+'assert(page.refresh(store.active_document(),input)==0);'
        init,drain,cleanup=fs.bootstrap.preparation.exhaustion()
        self.fault_program(PREFIX+'safe fn main():int{'+before+'unsafe{'+init+drain+
            'assert(page.refresh(store.active_document(),input)==0 && page.evaluations()==0 && page.cache_hits()==3);'
            'assert(input.set(n,2,2*65536));assert(page.refresh(store.active_document(),input)==401 && page.version()==2);'+value('a',8*65536)+
            f'own refused:flowpage::Page=try_new flowpage::Page({literal(SOURCE)},8,2048,10000000);'
            'assert(refused==null || !refused.is_open());'+cleanup+'}'
            'assert(page.refresh(store.active_document(),input)==0 && page.version()==3);'+value('a',4*65536)+'return 0;}','')

    def test_all_five_formats_generate_without_ast_fallback_and_example_executes(self):
        path=ROOT/'exemplos/55_page_styles.assis'
        for flags in [[],['--no-opt']]:
            result=self.invoke('ir',path,*flags);self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['astFallbacks'],0)
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                result=self.invoke('build',path,'--target',target,'-o',self.temp/target,*flags)
                self.assertEqual(result.returncode,0,(target,result.stderr))
            result=self.invoke('run',path,'--debug',*flags)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'PANELS -524288 0\nWORK 1 2\n',''))

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

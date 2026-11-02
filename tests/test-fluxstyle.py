"""FS local profile: Fraction oracle, source corpus and transactional HTDL binding."""
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('catalog',Path(__file__).with_name('test-htdl-catalog.py'))
catalog=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalog)
base=catalog.base;bootstrap=catalog.bootstrap;ROOT=base.ROOT

def flow(expression,property='target.offsetY',prefix=''):
    return f'flow Card {{ {prefix} {expression} -> {property}; }} bind .card to Card;'

def nearest_positive(x):
    x=Fraction(x)+Fraction(1,2)
    return x.numerator//x.denominator

def literal(x):return bootstrap.literal(x)

class FluxStyle(base.Evolution):
    fault_program=bootstrap.HTDLParser.fault_program
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)

    @classmethod
    def setUpClass(cls):
        cls.shared=tempfile.TemporaryDirectory(prefix='assis-fs-');cls.drivers=[]
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=Path(cls.shared.name)/(mode+'.exe')
            r=subprocess.run([str(base.COMPILER),'build',str(ROOT/'tests/fixtures/fluxstyle-driver.assis'),'--safe','--debug','-o',str(binary),*flags],capture_output=True,timeout=60)
            if r.returncode:raise AssertionError(r.stderr.decode(errors='replace'))
            cls.drivers.append((mode,binary))

    @classmethod
    def tearDownClass(cls):cls.shared.cleanup()

    def parse(self,source,code=0,runtime=0):
        data=source.encode() if isinstance(source,str) else source;outputs=[]
        for mode,binary in self.drivers:
            r=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
            self.assertEqual((r.returncode,r.stderr),(0,b''),(mode,source[:300],r.stderr));outputs.append(r.stdout)
            lines=r.stdout.decode().splitlines();diagnostic=list(map(int,lines[0].split()))
            self.assertEqual(diagnostic[0],code,(mode,source[:500],r.stdout))
            checked=[diagnostic]
            if not code:
                error=list(map(int,lines[1].split()));self.assertEqual(error[0],runtime,(source[:500],r.stdout))
                checked.append(error)
                version=int(lines[2]);self.assertEqual(version,0 if runtime else 1)
                values=dict(map(lambda s:map(int,s.split()),lines[3:]))
            if isinstance(source,str):
                for d in checked:
                    for offset,actual in [(d[1],d[3:5]),(d[2],d[5:7])]:
                        prefix=data[:offset].decode().replace('\r\n','\n').replace('\r','\n')
                        self.assertEqual(actual,[prefix.count('\n')+1,len(prefix.split('\n')[-1].encode('utf-16-le'))//2+1])
        self.assertEqual(outputs[0],outputs[1]);return {} if code else values

    def test_reference_card_and_all_fifteen_property_domains(self):
        values=self.parse('''flow Card {
            input expanded: bool = state("expanded", false);
            let lift = choose(expanded, -8px, 0px);
            200px -> layout.width; 40px -> layout.height; 12px -> layout.padding;
            row(gap: 8px) -> layout.children; center -> layout.align; clip -> layout.overflow;
            #7454d8 -> paint.background; #fff -> paint.text; 4px -> paint.radius;
            50% -> paint.opacity; 16px -> text.size; 400 -> text.weight;
            start -> text.align; 2px -> target.offsetX; lift -> target.offsetY;
        } bind .card to Card;''')
        self.assertEqual(values,{1:200*65536,2:40*65536,3:12*65536,4:8*65536*4+1,5:1,6:1,
                                 7:0x7454d8ff,8:0xffffffff,9:4*65536,10:32768,11:16*65536,12:400*65536,13:0,14:2*65536,15:0})

    def test_forward_references_resolution_and_cycle_in_unselected_branch(self):
        self.assertEqual(self.parse(flow('a',prefix='let a=b+1px; let b=2px;'))[15],3*65536)
        for source in [flow('a',prefix='let a=b; let b=a;'),flow('a',prefix='let a=choose(false,b,1px); let b=a;')]:self.parse(source,301)
        self.parse(flow('missing'),205)
        self.parse(flow('a',prefix='let a=1px; let a=2px;'),206)
        for name in ['true','flow','choose','state']:self.parse(flow('1px',prefix=f'let {name}=1px;'),206)

    def test_no_cascade_disjoint_producers_and_idempotent_binding(self):
        source='flow A { 1px -> target.offsetY; } flow B { 2px -> target.offsetX; } bind .card to A; bind #card to A; bind .featured to B;'
        self.assertEqual(self.parse(source),{14:2*65536,15:65536})
        self.parse(source.replace('target.offsetX','target.offsetY'),runtime=302)
        self.parse('flow A { 1px -> target.offsetY; 2px -> target.offsetY; }',302)
        self.parse('bind .card to Missing;',205)
        self.assertEqual(self.parse('flow A { 1px -> target.offsetY; } bind .no-match to A;'),{})

    def test_short_circuit_still_checks_unselected_types_and_names(self):
        self.assertEqual(self.parse(flow('choose(false, 1px / 0, 8px)'))[15],8*65536)
        self.assertEqual(self.parse(flow('choose(false && (1/0==0), 1px, 2px)'))[15],2*65536)
        self.assertEqual(self.parse(flow('choose(true || (1/0==0), 1px, 2px)'))[15],65536)
        self.parse(flow('choose(false, unknown, 8px)'),205)
        self.parse(flow('choose(false, 1, 8px)'),203)
        self.parse(flow('choose(1, 1px, 2px)'),201)
        self.parse(flow('1px / 0'),runtime=402)
        self.parse(flow('clamp(1px, 2px, 0px)'),runtime=403)
        self.parse(flow('abs(-32768px)'),runtime=401)

    def test_dimensional_arithmetic_and_closed_types(self):
        self.assertEqual(self.parse(flow('(4Hz * 0.5s) * 1px'))[15],2*65536)
        self.assertEqual(self.parse(flow('(4Hz * 500ms) * 1px'))[15],2*65536)
        self.assertEqual(self.parse(flow('max(1px, min(4px, 3px))'))[15],3*65536)
        self.assertEqual(self.parse(flow('clamp(-2px, -1px, 2px)'))[15],-65536)
        for expr in ['1px+1','1px*1px','1px/1Hz','1s+1px','#fff*1','true+false']:
            self.parse(flow(expr),201)
        self.parse(flow('1px','paint.background'),201)
        self.parse(flow('1px','paint.focusRing'),202)
        self.parse(flow('row(8px)','layout.children'),102)
        self.parse(flow('choose(true,1px)','layout.width'),207)
        self.parse(flow('1px < 2px < 3px'),102)

    def test_property_domain_failures_do_not_publish(self):
        for expr,prop in [('-1px','layout.width'),('-1px','paint.radius'),('1.1','paint.opacity'),('0px','text.size'),
                          ('99','text.weight'),('400.5','text.weight'),('stretch','text.align'),('row(gap:-1px)','layout.children')]:
            self.parse(flow(expr,prop),runtime=404)

    def test_decimal_conversion_against_fraction_oracle(self):
        rng=random.Random(2026110202)
        for _ in range(65):
            value=Fraction(rng.randrange(-2000000,2000000),1000000)
            text=f'{float(value):.6f}'
            expected=nearest_positive(abs(value)*65536)*(1 if value>=0 else -1)
            self.assertEqual(self.parse(flow(text+'px'))[15],expected)
        self.assertEqual(self.parse(flow('-32768px'))[15],-2147483648)
        self.parse(flow('32768px'),runtime=401)
        self.assertEqual(self.parse(flow('50% * 8px'))[15],4*65536)

    def test_numeric_operations_against_unbounded_rational_oracle(self):
        rng=random.Random(2026110203);lines=[];expected=[]
        for op in ['add','subtract','multiply','divide']:
            pairs=[(-2147483648,-2147483648),(2147483647,2147483647),(-1,32768),(1,32768),(1,-32768),(0,0)]
            pairs += [(rng.randrange(-2147483648,2147483648),rng.randrange(-2147483648,2147483648)) for _ in range(55)]
            for a,b in pairs:
                if op=='divide' and b==0:code,value=402,0
                else:
                    result={'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:nearest_positive(Fraction(a*b,65536)),
                            'divide':lambda:nearest_positive(Fraction(a*65536,b))}[op]()
                    code,value=(0,result) if -2147483648<=result<=2147483647 else (401,0)
                lines.append(f'{{val r:fluxstyle::Number=fluxstyle::{op}({a},{b});print(r.code,r.value);}}')
                expected.append(f'{code} {value}\n')
        self.accepted('import "std/fluxstyle.assis";safe fn main():int{'+''.join(lines)+'return 0;}',''.join(expected))

    def test_lexical_grammar_nested_comments_colors_and_unicode_positions(self):
        source='\ufeff// 🙂 é\r\n/* outer /* inner */ done */\r'+flow('#1234abcd','paint.background')
        self.assertEqual(self.parse(source)[7],0x1234abcd)
        for color in ['#12','#12345','#1234567','#123456789','#abcg']:self.parse(flow(color,'paint.background'),101)
        for number in ['1.','.5','1e3','0x1','50%px']:self.parse(flow(number+'px'),101 if number!='.5' else 102)
        self.parse(flow('1qu'),201)
        self.parse(b'\xff',101)
        self.parse('/* unfinished',102)
        self.parse('/*'*33+'*/'*33,401)
        self.parse(flow('1px').replace('1px','"unterminated'),101)

    def test_state_schema_and_host_source_catalog(self):
        self.assertEqual(self.parse(flow('choose(v,1px,0px)',prefix='input v:bool=self.checked;'))[15],65536)
        self.assertEqual(self.parse(flow('choose(v,1px,0px)',prefix='input v:bool=self.disabled;'))[15],65536)
        self.parse(flow('v',prefix='input v:length=parent.availableWidth;'),runtime=303)
        self.parse(flow('v',prefix='input v:length=self.finalWidth;'),204)
        self.parse(flow('v',prefix='input v:length=env.textScale;'),201)
        self.parse(flow('1px',prefix='input v:number=state("a",0.5);'),201)
        self.parse(flow('1px',prefix='input v:bool=state("A",false);'),204)
        self.parse('flow A {input a:bool=state("k",false);} flow B {input b:number=state("k",0);}',304)
        self.parse('flow A {input a:bool=state("k",false);} flow B {input b:bool=state("k",true);}',306)

    def test_pinned_fs_corpus_and_reference_card_with_host_constraint(self):
        frozen=ROOT/'docs/ecossistema/referencias/htdl-drafts-2026-10-29/exemplos'
        for name,code in [('branch-types',203),('dimension',201),('state-defaults',306)]:
            self.parse((frozen/f'conformidade/invalid/{name}.fxs').read_text(),code)
        card=(frozen/'fluxstyle/card.fxs').read_text()
        self.parse(card,runtime=303)
        self.parse((frozen/'conformidade/valid/lazy-branch.fxs').read_text())
        doc=literal(catalog.document(catalog.element('container','','id=card class=card')))
        self.accepted('import "std/fluxstyle.assis";safe fn main():int{'
            f'own p:fluxstyle::Program=try_new fluxstyle::Program({literal(card)},1000000);'
            'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);own style:fluxstyle::Style=try_new fluxstyle::Style();'
            'own s:documents::Store=try_new documents::Store(1000000,1000,100);'
            f'assert(htdl::load_catalog(s,1,{doc}).code==0);'
            'val node:doctree::NodeId=htdl::find_id(s.active_document().nodes(),utf8("card"));'
            'val f:int=p.flow_index(utf8("CardVisuals"));assert(input.set(p.input_index(f,utf8("available")),3,500*65536));'
            'assert(p.evaluate(s.active_document(),node,input,1,style).code==0 && style.value(1)==320*65536 && style.value(15)==0);'
            'assert(input.set(p.input_index(f,utf8("expanded")),1,1));'
            'assert(p.evaluate(s.active_document(),node,input,2,style).code==0 && style.value(1)==500*65536 && style.value(15)==-8*65536);return 0;}')

    def test_shared_state_uses_one_value_and_rejects_host_conflict(self):
        source='flow A{input a:number=state("k",1); a*1px -> target.offsetX;} flow B{input b:number=state("k",1); b*1px -> target.offsetY;} bind .card to A; bind .card to B;'
        doc=literal(catalog.document(catalog.element('container','','id=card class=card')))
        self.accepted('import "std/fluxstyle.assis";safe fn main():int{'
            f'own p:fluxstyle::Program=try_new fluxstyle::Program({literal(source)},1000000);'
            'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);own style:fluxstyle::Style=try_new fluxstyle::Style();'
            'own s:documents::Store=try_new documents::Store(1000000,1000,100);'
            f'assert(htdl::load_catalog(s,1,{doc}).code==0);'
            'val node:doctree::NodeId=htdl::find_id(s.active_document().nodes(),utf8("card"));'
            'val a:int=p.input_index(p.flow_index(utf8("A")),utf8("a"));val b:int=p.input_index(p.flow_index(utf8("B")),utf8("b"));'
            'assert(input.set(a,2,3*65536));assert(p.evaluate(s.active_document(),node,input,1,style).code==0 && style.value(14)==3*65536 && style.value(15)==3*65536);'
            'assert(input.set(b,2,4*65536));assert(p.evaluate(s.active_document(),node,input,2,style).code==304 && style.version()==1);'
            'input.clear();assert(input.set(a,2,1));assert(p.evaluate(s.active_document(),node,input,2,style).code==201 && style.version()==1);return 0;}')

    def test_real_allocation_denial_preserves_neighbor_and_last_style(self):
        source=literal(flow('8px'))
        setup,drain,cleanup=bootstrap.preparation.exhaustion()
        self.fault_program('import "std/fluxstyle.assis";safe fn main():int{'
            f'own neighbor:fluxstyle::Program=try_new fluxstyle::Program({source},1000000);assert(neighbor!=null && neighbor.is_open());'
            'unsafe{'+setup+drain+
            f'own refused:fluxstyle::Program=try_new fluxstyle::Program({source},1000000);'
            'assert(refused==null || (!refused.is_open() && refused.diagnostic().code==401));'
            'assert(neighbor.is_open());'+cleanup+'}return 0;}','')

    def test_host_context_and_semantic_control_applicability(self):
        doc=literal(catalog.document(catalog.element('container','','id=card class=card')))
        for prefix,expr in [('input v:bool=self.checked;','choose(v,1px,0px)'),('input v:bool=self.disabled;','choose(v,1px,0px)')]:
            source=literal(flow(expr,prefix=prefix))
            self.accepted('import "std/fluxstyle.assis";safe fn main():int{'
                f'own p:fluxstyle::Program=try_new fluxstyle::Program({source},1000000);'
                'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);own style:fluxstyle::Style=try_new fluxstyle::Style();'
                'own s:documents::Store=try_new documents::Store(1000000,1000,100);'
                f'assert(htdl::load_catalog(s,1,{doc}).code==0);'
                'val node:doctree::NodeId=htdl::find_id(s.active_document().nodes(),utf8("card"));'
                'assert(p.evaluate(s.active_document(),node,input,1,style).code==204 && style.version()==0);return 0;}')

    def test_transaction_failure_retry_stale_node_and_shared_state(self):
        source='flow Card {input n:number=state("n",1); n*1px -> layout.width; 0.5 -> paint.opacity;} bind .card to Card;'
        doc=literal(catalog.document(catalog.element('container','','id=card class=card')))
        self.accepted('import "std/fluxstyle.assis";safe fn main():int{'
            f'own p:fluxstyle::Program=try_new fluxstyle::Program({literal(source)},1000000);'
            'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);own style:fluxstyle::Style=try_new fluxstyle::Style();'
            'own s:documents::Store=try_new documents::Store(1000000,1000,100);'
            f'assert(htdl::load_catalog(s,1,{doc}).code==0);'
            'val node:doctree::NodeId=htdl::find_id(s.active_document().nodes(),utf8("card"));'
            'assert(p.evaluate(s.active_document(),node,input,1,style).code==0 && style.value(1)==65536 && style.value(10)==32768);'
            'val index:int=p.input_index(p.flow_index(utf8("Card")),utf8("n"));assert(input.set(index,2,-65536));'
            'assert(p.evaluate(s.active_document(),node,input,2,style).code==404 && style.version()==1 && style.value(1)==65536 && style.value(10)==32768);'
            'assert(input.set(index,2,3*65536));assert(p.evaluate(s.active_document(),node,input,2,style).code==0 && style.version()==2 && style.value(1)==3*65536);'
            'assert(p.evaluate(s.active_document(),node,input,2,style).code==204 && style.version()==2);'
            f'assert(htdl::load_catalog(s,2,{doc}).code==0);'
            'assert(p.evaluate(s.active_document(),node,input,3,style).code==204 && style.version()==2);return 0;}')

    def test_budget_and_depth_are_explicit_refusals(self):
        self.parse(b'x'*65537,401)
        self.parse(flow('('*66+'1px'+')'*66),401)
        self.parse(''.join(f'flow F{i}{{}}' for i in range(33)),401)
        self.parse('flow F{}'+'bind .card to F;'*129,401)
        self.parse(flow('0.1234567890px'),401)
        self.accepted('import "std/fluxstyle.assis";safe fn main():int{'
            'own p:fluxstyle::Program=try_new fluxstyle::Program(utf8("flow F{}"),399999);'
            'assert(p!=null && !p.is_open() && p.diagnostic().code==401);return 0;}')

    def test_all_native_formats_generated_without_ast_fallback(self):
        for flags in [[],['--no-opt']]:
            result=self.invoke('ir',ROOT/'tests/fixtures/fluxstyle-driver.assis',*flags)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['astFallbacks'],0)
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                result=self.invoke('build',ROOT/'tests/fixtures/fluxstyle-driver.assis','--target',target,'-o',self.temp/target,*flags)
                self.assertEqual(result.returncode,0,(target,result.stderr))

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

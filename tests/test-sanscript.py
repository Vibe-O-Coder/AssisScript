"""Finite SSC profile: pinned spring vectors, analytic comparison and lifecycle."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('fs',Path(__file__).with_name('test-fluxstyle.py'));fs=importlib.util.module_from_spec(spec);spec.loader.exec_module(fs)
base=fs.base;ROOT=base.ROOT;literal=fs.literal
spec=importlib.util.spec_from_file_location('spring',ROOT/'docs/ecossistema/referencias/htdl-drafts-2026-10-29/exemplos/fluxstyle/spring_reference.py');spring=importlib.util.module_from_spec(spec);spec.loader.exec_module(spring)
def channel(f='4',z='0.8',axis='Y'):
    return f'spring(target:fs.target.offset{axis},frequency:{f}Hz,dampingRatio:{z})->presentation.offset{axis};'
def program(body=None):return 'motion Card{'+(channel() if body is None else body)+'}bind .card to Card;'

DOC=literal(fs.catalog.document(fs.catalog.element('container','','id=card class=card')))
PREFIX='import "std/sanscript.assis";safe fn main():int{'
SETUP=('own store:documents::Store=try_new documents::Store(1000000,1000,100);own style:fluxstyle::Style=try_new fluxstyle::Style();own data:*int=try_alloc<int>(15);'
       f'assert(htdl::load_catalog(store,1,{DOC}).code==0);'
       'val node:doctree::NodeId=htdl::find_id(store.active_document().nodes(),utf8("card"));assert(style.commit(node,1,24576,slice_of(data,0,15)));')

class SanScript(base.Evolution):
    fault_program=fs.bootstrap.HTDLParser.fault_program
    def invoke(self,*args,**kwargs):
        if args and args[0] in ('check','build','run','ir'):args=(*args,'--safe')
        return super().invoke(*args,**kwargs)
    @classmethod
    def setUpClass(cls):
        cls.shared=tempfile.TemporaryDirectory(prefix='assis-ssc-');cls.drivers=[]
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=Path(cls.shared.name)/(mode+'.exe');r=subprocess.run([str(base.COMPILER),'build',str(ROOT/'tests/fixtures/sanscript-driver.assis'),'--safe','--debug','-o',str(binary),*flags],capture_output=True,timeout=60)
            if r.returncode:raise AssertionError(r.stderr.decode(errors='replace'))
            cls.drivers.append((mode,binary))
    @classmethod
    def tearDownClass(cls):cls.shared.cleanup()
    def parse(self,source,code=0,binding=0):
        data=source.encode() if isinstance(source,str) else source;outputs=[]
        for mode,binary in self.drivers:
            r=subprocess.run([str(binary)],input=data,capture_output=True,timeout=15)
            self.assertEqual((r.returncode,r.stderr),(0,b''),(source[:300],r.stderr));outputs.append(r.stdout)
            lines=r.stdout.decode().splitlines();d=list(map(int,lines[0].split()));self.assertEqual(d[0],code,(mode,source[:300],r.stdout[:300]))
            if isinstance(source,str):
                for offset,actual in [(d[1],d[3:5]),(d[2],d[5:7])]:
                    prefix=data[:offset].decode().replace('\r\n','\n').replace('\r','\n');self.assertEqual(actual,[prefix.count('\n')+1,len(prefix.split('\n')[-1].encode('utf-16-le'))//2+1])
            if not code:self.assertEqual(int(lines[1]),binding)
        self.assertEqual(outputs[0],outputs[1]);return outputs[0]

    def test_all_42_matrices_and_trajectories_against_pinned_and_analytic_oracles(self):
        corpus=json.loads((ROOT/'tests/fixtures/ssc-coefficients.json').read_text());observations=[];worst=0
        for row in corpus['rows']:
            raw=self.parse(program(channel(row['frequency'],row['damping'])))
            records=[line.split() for line in raw.decode().splitlines()[2:]]
            f,z=float(row['frequency']),float(row['damping']);trace,matrix=spring.trace(f,z,[(1,-8)],360)
            self.assertEqual(matrix,row['matrix']);self.assertEqual(len(records),360)
            errors=[]
            for step,record in enumerate(records,1):
                status,position,speed,asleep,code=record
                self.assertEqual((int(status),int(code)),(0,0))
                self.assertEqual(int(position),round(trace[step][0]*65536),(row,step))
                self.assertEqual(asleep=='true',trace[step][1])
                errors.append(abs((int(position)/65536+8)-spring.analytic(f,z,8,step/120)))
            maximum=max(errors);worst=max(worst,maximum);self.assertLess(maximum,1/16)
            observations.append(dict(frequency=row['frequency'],damping=row['damping'],trace_sha256=hashlib.sha256(raw).hexdigest(),max_error_8px=maximum))
        if os.environ.get('SSC_TRACE_OUTPUT'):
            Path(os.environ['SSC_TRACE_OUTPUT']).write_text(json.dumps(dict(rows=observations,max_error_8px=worst,scope='Only 8px steps over 3 seconds; not a global tolerance proof'),indent=2)+'\n',encoding='utf-8',newline='\n')

    def test_arguments_types_ranges_and_finite_profile_rejection(self):
        self.parse(program(channel(z='80%')))
        for text,code in [('spring(target:fs.target.offsetY,frequency:4Hz)->presentation.offsetY;',201),
                          ('spring(target:fs.target.offsetY,target:fs.target.offsetY,dampingRatio:0.8)->presentation.offsetY;',201),
                          ('spring(target:fs.target.offsetX,frequency:4Hz,dampingRatio:0.8)->presentation.offsetY;',203),
                          (channel(f='12'),202),(channel(z='0.05'),202),(channel(f='3'),402),
                          (channel().replace('4Hz','4px'),204),(channel().replace('0.8','0.8Hz'),204)]:self.parse(program(text),code)
        self.parse(program(channel()+channel()),301)
        self.parse('motion Card{}motion Card{}',205)
        self.parse('bind .card to Missing;',205)
        self.parse('motion A{'+channel()+'}motion B{'+channel()+'}bind .card to A;bind #card to B;',binding=301)
        self.parse(program().replace('bind .card','bind .other'))

    def test_grammar_unicode_limits_and_reordered_arguments(self):
        self.parse('\ufeff// 🙂 é\r\n/* a /* b */ c */'+program('spring(dampingRatio:0.8,target:fs.target.offsetY,frequency:4Hz)->presentation.offsetY;'))
        self.parse(b'\xff',101);self.parse(b'x'*65537,403);self.parse('/*'*33+'*/'*33,403)
        self.parse(program().replace('4Hz','1e3Hz'),101)
        self.parse(''.join(f'motion M{i}{{}}' for i in range(33)),403)
        self.parse('motion A{}'+'bind .card to A;'*129,403)
        self.parse('// valid\n\x00',101)

    def test_first_presentation_continuity_and_retarget(self):
        self.accepted(PREFIX+SETUP+f'own p:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'own motion:sanscript::Motion=p.attach(store.active_document(),node,style);assert(motion.is_open() && motion.at(2).value==0 && motion.asleep());'
            'data[14]=-8*65536;assert(style.commit(node,2,24576,slice_of(data,0,15)));assert(motion.update(store.active_document(),style)==0);'
            'for(let i:int=0;i<10;i++){let delta:int=8;if(i%3==0){delta=9;}assert(motion.advance(store.active_document(),delta,true,true,false,false)==0);}'
            'val position:int=motion.at(2).value;val velocity:int=motion.speed(2).value;data[14]=0;'
            'assert(style.commit(node,3,24576,slice_of(data,0,15)) && motion.update(store.active_document(),style)==0);'
            'assert(motion.at(2).value==position && motion.speed(2).value==velocity);'
            'assert(motion.advance(store.active_document(),25,true,true,false,true)==0 && motion.at(2).value==0 && motion.asleep());return 0;}')

    def test_time_budget_pause_focus_hidden_and_no_backlog(self):
        self.accepted(PREFIX+SETUP+f'own p:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'own m:sanscript::Motion=p.attach(store.active_document(),node,style);data[14]=-8*65536;assert(style.commit(node,2,24576,slice_of(data,0,15)) && m.update(store.active_document(),style)==0);'
            'assert(m.advance(store.active_document(),1000,true,true,false,false)==0);val after:int=m.at(2).value;'
            'assert(m.advance(store.active_document(),0,true,true,false,false)==0 && m.at(2).value==after);'
            'assert(m.advance(store.active_document(),1000,false,true,false,false)==0 && m.at(2).value==after);'
            'assert(m.advance(store.active_document(),1000,true,true,false,false)==0 && m.at(2).value==after);'
            'assert(m.advance(store.active_document(),25,true,true,true,false)==0 && m.at(2).value==after && m.speed(2).value==0);'
            'data[14]=0;assert(style.commit(node,3,24576,slice_of(data,0,15)) && m.update(store.active_document(),style)==0);'
            'assert(m.advance(store.active_document(),1000,true,true,true,false)==0 && m.at(2).value==after);'
            'assert(m.advance(store.active_document(),1000,true,true,false,false)==0 && m.at(2).value==after);'
            'assert(m.advance(store.active_document(),1000,true,false,false,false)==0);'
            'assert(m.advance(store.active_document(),1000,true,true,false,false)==0 && m.at(2).value==0 && m.asleep());'
            'assert(m.advance(store.active_document(),60001,true,true,false,false)==401);return 0;}')

    def test_fs_pipeline_stale_handles_close_and_missing_producer(self):
        fs_source=fs.flow('choose(expanded,-8px,0px)',prefix='input expanded:bool=state("expanded",false);')
        self.accepted(PREFIX+SETUP+f'own p:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'own empty:fluxstyle::Style=try_new fluxstyle::Style();assert(empty.commit(node,1,0,slice_of(data,0,15)));'
            'own refused:sanscript::Motion=p.attach(store.active_document(),node,empty);assert(!refused.is_open() && refused.status()==302);'
            f'own fs:fluxstyle::Program=try_new fluxstyle::Program({literal(fs_source)},1000000);'
            'own input:fluxstyle::Inputs=try_new fluxstyle::Inputs(2048);own visual:fluxstyle::Style=try_new fluxstyle::Style();'
            'assert(fs.evaluate(store.active_document(),node,input,1,visual).code==0);own m:sanscript::Motion=p.attach(store.active_document(),node,visual);assert(m.is_open());'
            'assert(input.set(fs.input_index(0,utf8("expanded")),1,1));assert(fs.evaluate(store.active_document(),node,input,2,visual).code==0 && m.update(store.active_document(),visual)==0);'
            'assert(m.advance(store.active_document(),9,true,true,false,false)==0 && m.at(2).value<0);'
            'assert(m.update(store.active_document(),visual)==403);'
            f'assert(htdl::load_catalog(store,2,{DOC}).code==0);'
            'assert(m.advance(store.active_document(),9,true,true,false,false)==403 && !m.is_open() && m.at(2).code==403);m.close();return 0;}')

    def test_checked_product_outside_physical_range_and_safe_fallback(self):
        self.accepted(PREFIX+SETUP+f'own p:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'own m:sanscript::Motion=p.attach(store.active_document(),node,style);data[14]=5000*65536;'
            'assert(style.commit(node,2,24576,slice_of(data,0,15)));assert(m.update(store.active_document(),style)==401 && m.at(2).value==5000*65536 && m.asleep());'
            'assert(sanscript::product(9223372036854775807,2).code==401);'
            'assert(sanscript::product(-1,32768).value==0 && sanscript::product(1,32768).value==1);return 0;}')

    def test_real_allocation_denial_and_allocation_free_advancement(self):
        setup,drain,cleanup=fs.bootstrap.preparation.exhaustion()
        self.fault_program(PREFIX+SETUP+f'own p:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'own m:sanscript::Motion=p.attach(store.active_document(),node,style);assert(m.is_open());unsafe{'+setup+drain+
            f'own refused:sanscript::Program=try_new sanscript::Program({literal(program())},1000000);'
            'assert(refused==null || (!refused.is_open() && refused.diagnostic().code==403));'
            'data[14]=-8*65536;assert(style.commit(node,2,24576,slice_of(data,0,15)));'
            'assert(m.update(store.active_document(),style)==0 && m.advance(store.active_document(),9,true,true,false,false)==0 && m.at(2).value<0);'
            'm.close();assert(m.at(2).code==403);'+cleanup+'}return 0;}','')

    def test_coefficient_generation_and_five_native_formats(self):
        r=subprocess.run([os.sys.executable,str(ROOT/'tools/generate-ssc-coefficients.py'),'--check'],capture_output=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr)
        for flags in [[],['--no-opt']]:
            result=self.invoke('ir',ROOT/'tests/fixtures/sanscript-driver.assis',*flags);self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['astFallbacks'],0)
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                result=self.invoke('build',ROOT/'tests/fixtures/sanscript-driver.assis','--target',target,'-o',self.temp/target,*flags);self.assertEqual(result.returncode,0,(target,result.stderr))

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

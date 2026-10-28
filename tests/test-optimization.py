"""Differential arithmetic, allocator zeroing and adversarial map regressions."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
main=base.main

class Optimization(base.Evolution):
    def test_range_proof_and_mutation_call_unsafe_fallbacks(self):
        cases=[
            ('for(let i:int=0;i<len(a);i+=1){a[i]=i;}',1),
            ('for(let i:int=-1;i<len(a);i+=1){a[i]=i;}',0),
            ('for(let i:int=0;i<len(a);i+=1){i+=1;a[i]=i;}',0),
            ('for(let i:int=0;i<len(a);i+=1){print(id(i));a[i]=i;}',1),
            ('for(let i:int=0;i<len(a);i+=1){unsafe{a[i]=i;}}',0),
        ]
        for body,expected in cases:
            source=self.source('pure fn id(n:int):int{return n;}'+main('own a:*int=alloc<int>(3);'+body))
            result=self.invoke('ir',source);self.assertEqual(result.returncode,0,result.stderr)
            function=next(f for f in json.loads(result.stdout)['functions'] if f['name']=='main')
            self.assertEqual(function['provenBounds'],expected,body)
        self.accepted(main('own a:*int=alloc<int>(16);for(let i:int=0;i<len(a);i+=1){a[i]=i;}assert(a[15]==15);'))
        self.accepted(main('own a:Array<int>=[0,0,0];for(let i:int=0;i<len(a);i+=1){a[i]=i;}assert(a[2]==2);'))
        for source in ['own a:*int=alloc<int>(3);for(let i:int=0;i<len(a);i+=1){i+=1;print(a[i]);}',
                       'own a:Array<int>=[1,2];for(let i:int=0;i<len(a);i+=1){a.clear();print(a[i]);}']:
            file=self.source(main(source))
            for flags in [[],['--no-opt']]:self.assertEqual(self.invoke('run',file,*flags).returncode,70)

    def test_strided_negative_extreme_keys_and_tombstones(self):
        for stride in [1,64,4096,65536]:
            body=f'own m:HashMap<int,int>=new HashMap<int,int>();let i:int=0;while(i<3000){{m.set((i-1500)*{stride},i);i+=1;}}'
            body+=f'i=0;while(i<3000){{assert(m.get((i-1500)*{stride})==i);if(i%2==0){{assert(m.remove((i-1500)*{stride}));}}i+=1;}}'
            body+=f'i=0;while(i<3000){{m.set((i-1500)*{stride},i+1);i+=1;}}i=0;while(i<3000){{assert(m.get((i-1500)*{stride})==i+1);i+=1;}}'
            body+='m.set(-0x8000_0000_0000_0000,41);m.set(0x7fff_ffff_ffff_ffff,42);assert(m.get(-0x8000_0000_0000_0000)==41);assert(m.get(0x7fff_ffff_ffff_ffff)==42);'
            self.accepted(main(body))

    def test_zeroed_fresh_and_reused_allocations(self):
        for size in [0,1,31,32,33,255,32736,32737,1048576,8388608]:
            body=f'for(let i:int=0;i<8;i+=1){{own p:*byte=alloc<byte>({size});assert(len(p)=={size});'
            if size:
                body+=f'assert(p[0]==0&&p[{size//2}]==0&&p[{size-1}]==0);p[0]=byte(123);p[{size-1}]=byte(255);'
            self.accepted(main(body+'}'))

    def test_immediates_scaled_addresses_and_leaf_calls(self):
        rng=random.Random(611)
        values=[-2**63,-2**31-1,-2**31,-1,0,1,2**31-1,2**31,2**63-1]+[rng.randrange(-2**63,2**63) for _ in range(15)]
        wrap=lambda n:(n+2**63)%2**64-2**63
        body=''
        for n in values:
            for c in [-2**31-1,-2**31,-1,0,3,5,9,2**31-1,2**31]:
                literal=lambda v:hex(v) if v>=0 else '-'+hex(-v)
                body+=f'{{let x:int={literal(n)};assert(add(x,{literal(c)})=={literal(wrap(n+c))});assert(mul(x,{literal(c)})=={literal(wrap(n*c))});assert((x<{literal(c)})=='+('true' if n<c else 'false')+');}'
        helpers='pure fn add(x:int,y:int):int{return x+y;}pure fn mul(x:int,y:int):int{return x*y;}'
        self.accepted(helpers+main(body))
        for ty in ['byte','i16','i32','int']:
            self.accepted(main(f'own p:*{ty}=alloc<{ty}>(5);for(let i:int=0;i<5;i+=1){{p[i]={ty}(i+1);}}assert(int(p[4])==5);'))

    def test_inline_preserves_effects_and_argument_order(self):
        self.accepted('pure fn swap(a:int,b:int):int{return b-a+a;}fn effect(n:int):int{print(n);return n;}'+main('print(swap(effect(1),effect(2)));'),'1\n2\n2\n')
        self.accepted('pure fn duplicate(a:int):int{return a+a;}'+main('let a:int=21;print(duplicate(a));'),'42\n')
        self.accepted('pure fn choose(a:bool,b:bool):bool{return a&&b;}'+main('assert(choose(true,true));assert(!choose(true,false));'))

    def test_optimized_bounds_and_traps_are_retained(self):
        source=self.source(main('own p:*int=alloc<int>(1);print(p[1]);'))
        for flags in [[],['--no-opt']]:
            result=self.invoke('run',source,*flags)
            self.assertEqual(result.returncode,70,result.stderr)
            self.assertIn('ndice',result.stderr)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

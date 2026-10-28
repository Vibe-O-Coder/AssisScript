"""Scalar IR, CFG liveness and nonwrapping induction proofs against independent results."""
import importlib.util
import json
import random
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
main = base.main


class BackendEvolution(base.Evolution):
    def inspect(self, source, function='main'):
        result = self.invoke('ir', self.source(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        return data, next(f for f in data['functions'] if f['name'] == function)

    def test_scalar_values_have_types_effects_and_dominating_operands(self):
        source = 'pure fn calc(x:int,y:int):int{return (x+y)/(y|1);}' + main(
            'let x:int=40;let y:int=2;print(calc(x,y));let n:f64=f64(x)+0.5;print(int(n));')
        data, _ = self.inspect(source)
        self.assertEqual(data['valueFormat'], 'AssisScript-ScalarIR-v1')
        kinds = {v['opcode'] for v in data['values']}
        self.assertTrue({'constant', 'local', 'binary', 'cast', 'call'} <= kinds)
        self.assertTrue(any(v['effects'] & 32 for v in data['values']))
        for value in data['values']:
            self.assertIsInstance(value['type'], str)
            self.assertTrue(all(0 <= operand < value['id'] for operand in value['inputs']))
            self.assertNotIn('node', value)
        self.accepted(source, '14\n40\n')

    def test_scalar_emission_matches_independent_modular_reference(self):
        rng = random.Random(3315)
        values = [-2**63, 2**63-1, -1, 0, 1] + [rng.randrange(-2**63, 2**63) for _ in range(35)]
        wrap = lambda n: (n + 2**63) % 2**64 - 2**63
        checks = []
        for a in values:
            b = rng.randrange(-2**63, 2**63) or 1
            div = abs(a)//abs(b) * (-1 if (a < 0) != (b < 0) else 1)
            for op, expected in [('+', wrap(a+b)), ('-', wrap(a-b)), ('*', wrap(a*b)),
                                 ('/', wrap(div)), ('%', a-div*b), ('^', wrap(a^b))]:
                checks.append(f'{{let a:int={a};let b:int={b};assert((a{op}b)=={expected});}}')
        self.accepted(main(''.join(checks)))

    def test_short_circuit_call_order_and_traps_remain_observable(self):
        helper = 'fn effect(n:int):int{print(n);return n;}pure fn div(a:int,b:int):int{return a/b;}'
        self.accepted(helper + main('let no:bool=false;let yes:bool=true;'
            'assert(!(no&&bool(div(1,0))));assert(yes||bool(div(1,0)));'
            'print(effect(1)+effect(2)*effect(3));'), '1\n2\n3\n7\n')
        for expression in ['div(1,0)', '(1<<effect(64))']:
            source = self.source(helper + main('print('+expression+');'))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('assis: erro', result.stderr)

    def test_registers_reused_across_scopes_and_dead_writes(self):
        body = 'let total:int=0;'
        for i in range(24):
            body += f'{{let x{i}:int={i};let dead{i}:int=99;total+=x{i};}}'
        body += 'print(total);'
        source = main(body)
        _, function = self.inspect(source)
        self.assertTrue(function['liveness'])
        self.assertGreater(function['registerVariables'], 4)
        self.assertGreater(function['registerReuses'], 4)
        self.accepted(source, '276\n')
        self.accepted(main('let keep:int=42;{let unused:int=99;unused=2;}print(keep);'), '42\n')

    def test_register_liveness_through_backedges_branches_and_parameters(self):
        helper = ('pure fn rotate(n:int,a:int,b:int,c:int,d:int,e:int):int{'
                  'if(n==0){return a+2*b+3*c+4*d+5*e;}'
                  'return rotate(n-1,b,c,d,e,a);}')
        self.accepted(helper + main('let sum:int=0;'
            'for(let i:int=0;i<100;i+=1){if(i%2==0){continue;}'
            'let x:int=i*2;if(i==99){sum+=x;break;}sum+=x;}'
            'print(sum,rotate(100,1,2,3,4,5));'), '5000 55\n')
        source = self.source(helper + main('print(rotate(100000,1,2,3,4,5));'))
        result = self.invoke('run', source, '--debug')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '55\n', ''))
        self.accepted('fn f(a:int,b:int,c:int,d:int,e:int):int{'
            'let keep:int=a+b+c+d+e;let i:int=0;while(i<10){let tmp:int=i+1;'
            'if(i<5){keep+=tmp;}else{keep-=tmp;}i+=1;}return keep;}' + main('print(f(1,2,3,4,5));'), '-10\n')

    def test_addressed_locals_and_effectful_aliases_stay_in_memory(self):
        self.accepted('fn change(p:*int):void{*p=42;}' + main(
            'let x:int=1;let y:int=2;change(&x);print(x,y);'), '42 2\n')
        self.accepted('class Counter{let value:int;fn add(borrow mut self,n:int):int{self.value+=n;return self.value;}}' + main(
            'own c:Counter=new Counter();let a:int=10;let b:int=20;print(c.add(a),c.add(b),a,b);'), '10 30 10 20\n')

    def test_match_definitions_nested_loops_and_owned_cleanup(self):
        source = ('enum E{A(int,int);B(int);}' + main(
            'let keep:int=7;let sum:int=0;for(let i:int=0;i<9;i+=1){'
            'val e:E=new E.A(i,2);match(e){A(x,y){sum+=x+y;}B(z){sum+=z;}}'
            'for(let j:int=0;j<3;j+=1){own p:*int=alloc<int>(1);p[0]=j;sum+=p[0];}}print(sum,keep);'))
        self.accepted(source, '81 7\n')

    def test_forward_reverse_offset_and_pure_call_induction(self):
        loops = [
            ('for(let i:int=1;i<len(a)-1;i+=1){sum+=a[i-1]+a[i]+a[i+1];}', 3, 27),
            ('for(let i:int=len(a)-1;i>=0;i-=1){sum+=a[i];}', 1, 15),
            ('for(let i:int=len(a)-2;i>=1;i-=1){sum+=a[i-1]+a[i+1];}', 2, 18),
            ('for(let i:int=0;i<len(a);i+=1){sum+=id(a[i]);}', 1, 15),
        ]
        for loop, bounds, expected in loops:
            source = 'pure fn id(n:int):int{return n;}' + main('own a:Array<int>=[1,2,3,4,5];let sum:int=0;'+loop+'print(sum);')
            _, f = self.inspect(source)
            self.assertEqual(f['provenBounds'], bounds, loop)
            self.accepted(source, str(expected)+'\n')
        self.accepted(main('own a:Array<int>=[];for(let i:int=len(a)-1;i>=0;i-=1){print(a[i]);}'))
        self.accepted(main('own a:*int=alloc<int>(0);for(let i:int=1;i<len(a)-1;i+=1){print(a[i-1]);}'))

    def test_unproven_offsets_mutation_and_overflow_keep_checks(self):
        for loop in [
            'for(let i:int=0;i<len(a);i+=1){print(a[i-1]);}',
            'for(let i:int=len(a)-1;i>=0;i-=1){print(a[i+1]);}',
            'for(let i:int=0;i<len(a);i+=2){print(a[i+3]);}',
            'for(let i:int=0;i<len(a);i+=1){i+=1;print(a[i]);}',
            'for(let i:int=0;i<len(a);i+=1){a.clear();print(a[i]);}',
        ]:
            source = main('own a:Array<int>=[1];'+loop)
            _, f = self.inspect(source)
            self.assertEqual(f['provenBounds'], 0, loop)
            file = self.source(source)
            for flags in [[], ['--no-opt']]:
                self.assertEqual(self.invoke('run', file, *flags).returncode, 70, loop)
        _, f = self.inspect(main('own a:Array<int>=[1];for(let i:int=0;i<len(a);i+=1){print(a[i-(-9223372036854775808)]);}'))
        self.assertEqual(f['provenBounds'], 0)

    def test_liveness_limit_falls_back_without_rejecting_program(self):
        body = ''.join(f'let n{i}:int={i};' for i in range(257))
        body += 'print(' + '+'.join(f'n{i}' for i in range(257)) + ');'
        source = main(body)
        _, f = self.inspect(source)
        self.assertFalse(f['liveness'])
        self.accepted(source, '32896\n')


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

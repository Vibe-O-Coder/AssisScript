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

    def test_scalar_stores_and_compound_assignments_have_explicit_ir(self):
        source = 'fn tick(n:int):int{print(n);return n;}' + main(
            'let x:int=2;x+=3;x*=4;x=x-2;tick(x);print(x);')
        data, function = self.inspect(source)
        operations = [op for block in function['blocks'] for op in block['operations']]
        stores = [op for op in operations if op['opcode'] == 'store-local']
        self.assertEqual(len(stores), 4)
        self.assertTrue(all(op['local'] == 'x' and op['type'] == 'int' and op['effects'] & 2 for op in stores))
        for op, operator in zip(stores[1:3], ['+', '*']):
            value = data['values'][op['value']]
            self.assertEqual((value['opcode'], value['operator']), ('binary', ord(operator)))
            self.assertTrue(all(operand < value['id'] for operand in value['inputs']))
        self.assertTrue(any(op['opcode'] == 'eval' for op in operations))
        self.accepted(source, '18\n18\n')

    def test_branch_short_circuit_negation_and_effect_order(self):
        helper = 'fn mark(n:int):bool{print(n);return n>0;}fn value(n:int):int{print(n);return n;}'
        self.accepted(helper + main('let yes:bool=true;let no:bool=false;'
            'if((no&&mark(1))||(!no&&mark(2))){print(10);}'
            'if(!(yes||mark(3))&&mark(4)){print(99);}'
            'while(yes&&mark(5)){yes=false;}'
            'if(value(7)<value(8)){print(1);}'), '2\n10\n5\n7\n8\n1\n')

    def test_all_integer_branch_relations_against_python(self):
        rng = random.Random(3316)
        checks = []
        relations = [('==', lambda a,b:a==b), ('!=', lambda a,b:a!=b), ('<', lambda a,b:a<b),
                     ('<=', lambda a,b:a<=b), ('>', lambda a,b:a>b), ('>=', lambda a,b:a>=b)]
        for ty, bits, signed in [('i8',8,True),('i16',16,True),('i32',32,True),
                                 ('u16',16,False),('u32',32,False),('u64',64,False),('int',64,True),('byte',8,False)]:
            values = [0, 1, (1 << bits)-1, 1 << (bits-1)] + [rng.randrange(1 << bits) for _ in range(6)]
            norm = lambda n: n-(1 << bits) if signed and n >= 1 << (bits-1) else n
            for a, b in zip(values, reversed(values)):
                for op, reference in relations:
                    expected = '1' if reference(norm(a), norm(b)) else '0'
                    # Test the branch itself, including its inverse, rather than print(bool).
                    checks.append(f'{{let a:{ty}={ty}(0x{a:x});let b:{ty}={ty}(0x{b:x});'
                                  f'let r:int=0;if(a{op}b){{r=1;}}assert(r=={expected});'
                                  f'if(!(a{op}b)){{assert(r==0);}}else{{assert(r==1);}}}}')
        self.accepted(main(''.join(checks)))

    def test_modulo_branch_extremes_and_zero_divisor(self):
        checks = []
        for a in [-2**63, -17, -1, 0, 1, 17, 2**63-1]:
            for b in [-2**63, -8, -1, 1, 2, 8, 3]:
                expected = int(a % b == 0)
                checks.append(f'{{let a:int={a};let yes:int=0;if(a%({b})==0){{yes=1;}}'
                              f'assert(yes=={expected});if(a%({b})!=0){{assert(yes==0);}}}}')
        self.accepted(main(''.join(checks)))
        file = self.source(main('let z:int=0;if(1%z==0){print(1);}'))
        for flags in [[], ['--no-opt']]:
            self.assertEqual(self.invoke('run', file, *flags).returncode, 70)

    def test_scalar_stores_keep_width_rounding_and_aliased_reads(self):
        self.accepted('fn change(p:*int):int{*p=10;return 3;}' + main(
            'let x:int=2;x+=change(&x);print(x);'
            'let a:i8=i8(127);a+=i8(1);a*=i8(3);a/=i8(-1);'
            'let u:u64=u64(0xffffffffffffffff);u>>=63;u<<=63;'
            'let f:f32=f32(16777216.0);f+=f32(1.0);f-=f32(16777216.0);'
            'print(a,u,f);'), '5\n-128 9223372036854775808 0x0.0000000000000p+0\n')

    def test_ieee_branches_and_owned_cleanup_at_loop_exits(self):
        self.accepted(main('let z:f64=0.0;let nan:f64=z/z;let score:int=0;'
            'if(nan==nan){score+=100;}if(nan!=nan){score+=1;}'
            'if(nan<z||nan<=z||nan>z||nan>=z){score+=100;}if(z==-z){score+=2;}'
            'for(let i:int=0;i<5;i+=1){own p:*int=alloc<int>(1);p[0]=i;'
            'if(i==1){continue;}if(i==4){break;}score+=p[0];}print(score);'), '8\n')

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

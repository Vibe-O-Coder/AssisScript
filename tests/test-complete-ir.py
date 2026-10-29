"""Complete typed emission: memory, cleanup edges, dispatch and independent results."""
import importlib.util
import json
import random
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
main = base.main


class CompleteIR(base.Evolution):
    def inspect(self, source):
        result = self.invoke('ir', self.source(source))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['backendFormat'], 'AssisScript-TypedIR-v1')
        self.assertEqual(data['astFallbacks'], 0)
        for value in data['backendValues']:
            self.assertTrue(all(0 <= operand < value['id'] for operand in value['inputs']), value)
            self.assertIsInstance(value['type'], str)
        for function in data['emission']:
            for block in function['blocks']:
                self.assertTrue(all(0 <= successor < len(function['blocks']) for successor in block['successors']))
                self.assertTrue(all(op['opcode'] != 'ast' for op in block['operations']))
        return data

    def test_typed_addresses_resources_runtime_and_dispatch_are_complete(self):
        source = ('class Counter{let value:int;fn add(borrow mut self,n:int):int{self.value+=n;return self.value;}}'
                  'fn consume(own p:*int):int{return p[0];}' + main(
                  'own c:Counter=new Counter();assert(c.add(2)==2);'
                  'let x:int=1;let raw:*int=&x;*raw=3;assert(x==3);'
                  'own a:Array<int>=[1,2];own buffer:*int=alloc<int>(2);buffer[0]=a[1];'
                  '{borrow s:slice<int>=slice_of(buffer,0,1);assert(s[0]==2);}'
                  'assert(c is Counter);{borrow down:Counter=c as Counter;assert(down!=null);}'
                  'own transferred:*int=alloc<int>(1);transferred[0]=7;assert(consume(move(transferred))==7);'
                  'assert(sleep_ms(0)==0);print(utf8("ok"));'))
        data = self.inspect(source)
        kinds = {value['opcode'] for value in data['backendValues']}
        self.assertTrue({'address-local','address-field','address-index','address-deref','load','take',
                         'call','construct','slice','allocate','runtime','utf8-slice','type-test','downcast'} <= kinds, kinds)
        self.accepted(source, 'ok\n')

    def test_owned_cleanup_is_present_before_returns_and_loop_exits(self):
        source = ('enum E{None;Some(own *int);}'
                  'fn read(own p:*int,n:int):int{own extra:*byte=alloc<byte>(3);if(n==0){return p[0];}return n;}' + main(
                  'let sum:int=0;for(let i:int=0;i<6;i+=1){'
                  'own e:E=new E.Some(alloc<int>(1));match(move(e)){None{}Some(p){'
                  'p[0]=i;if(i==1){continue;}if(i==4){break;}sum+=read(move(p),0);}}}print(sum);'))
        data = self.inspect(source)
        read = next(function for function in data['emission'] if function['name'] == 'read')
        returns = [block for block in read['blocks'] if block['terminator'] == 'return']
        self.assertEqual(len(returns), 2)
        for block in returns:
            operations = block['operations']
            saved = next(i for i, op in enumerate(operations) if op['opcode'] == 'save-return')
            drops = [op['local'] for op in operations[saved+1:] if op['opcode'] == 'drop-local']
            self.assertEqual(drops, ['extra','p'])
        entry = next(function for function in data['emission'] if function['name'] == 'main')
        self.assertTrue(any(block['terminator'] == 'match' for block in entry['blocks']))
        self.assertTrue(any(block['terminator'] == 'jump' and any(op['opcode'] == 'drop-local' for op in block['operations']) for block in entry['blocks']))
        self.accepted(source, '5\n')

    def test_own_replacement_and_compound_memory_evaluate_in_source_order(self):
        source = ('fn replacement(n:int):own *int{own p:*int=alloc<int>(1);p[0]=n+1;return move(p);}'
                  'struct Box{own p:*int;}fn change(p:*int):int{p[0]=100;return 3;}' + main(
                  'own box:Box=new Box(alloc<int>(1));box.p[0]=41;box.p=replacement(box.p[0]);print(box.p[0]);'
                  'let raw:*int=alloc<int>(1);raw[0]=2;raw[0]+=change(raw);print(raw[0]);free(raw);'))
        data = self.inspect(source)
        self.assertTrue(any(op['opcode'] == 'store-memory' for f in data['emission'] for b in f['blocks'] for op in b['operations']))
        self.accepted(source, '42\n5\n')

    def test_indirect_callee_is_saved_before_effectful_arguments(self):
        source = ('fn plus(n:int):int{return n+1;}fn twice(n:int):int{return n*2;}'
                  'struct Box{let call:fn(int):int;}'
                  'fn mutate(box:Box):int{box.call=twice;return 5;}' + main(
                  'let box:Box=new Box(plus);print(box.call(mutate(box)),box.call(5));free(box);'))
        self.inspect(source)
        self.accepted(source, '6 10\n')

    def test_aggregate_argument_and_return_survive_later_memory_effects(self):
        source = ('value struct P{let x:int;let y:int;}'
                  'fn mutate(p:*P):int{p[0]=new P(90,9);return 2;}'
                  'fn combine(p:P,n:int):P{return new P(p.x+n,p.y);}' + main(
                  'let buffer:*P=alloc<P>(1);buffer[0]=new P(40,7);'
                  'val result:P=combine(buffer[0],mutate(buffer));print(result.x,result.y,buffer[0].x);free(buffer);'))
        data = self.inspect(source)
        self.assertIn('materialize', {value['opcode'] for value in data['backendValues']})
        self.accepted(source, '42 7 90\n')

    def test_nested_memory_loops_match_independent_python_reference(self):
        rng = random.Random(5316)
        bodies, expected = [], []
        for _ in range(18):
            size = rng.randrange(1, 12)
            values = [rng.randrange(-100, 100) for _ in range(size)]
            skip = rng.randrange(size)
            stop = rng.randrange(skip+1, size+1)
            bodies.append('{own a:*int=alloc<int>('+str(size)+');'+''.join(f'a[{i}]={n};' for i,n in enumerate(values))+
                          f'let sum:int=0;for(let i:int=0;i<len(a);i+=1){{own scratch:*int=alloc<int>(1);'
                          f'if(i=={skip}){{continue;}}if(i=={stop}){{break;}}scratch[0]=a[i];'
                          'for(let j:int=0;j<3;j+=1){sum+=scratch[0]+j;}}print(sum);}')
            expected.append(str(sum(3*n+3 for i,n in enumerate(values[:stop]) if i != skip))+'\n')
        self.accepted(main(''.join(bodies)), ''.join(expected))

    def test_owned_closure_and_inline_variant_returns_with_symbols(self):
        source = ('value struct P{let x:int;let y:int;}enum E{None;Some(P);}'
                  'safe fn make(n:int):own closure():E{return closure[val x:int=n]():E{return new E.Some(new P(x,2));};}'
                  'safe fn main():int{own f:closure():E=make(40);match(f()){None{print(0);}Some(p){print(p.x+p.y);}}return 0;}')
        self.inspect(source)
        self.accepted(source, '42\n')
        binary = self.temp / 'with-symbols.exe'
        result = self.invoke('build', self.source(source), '--symbols', '-o', binary)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Execution and heap validation also exercise aggregate hidden results.
        result = self.invoke('run', self.source(source), '--debug')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '42\n', ''))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

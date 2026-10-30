"""Allocation-free resource removal, checked against logical ownership models."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('slots', Path(__file__).with_name('test-fallible-slots.py'))
slots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slots)
base = slots.base
PREFIX = slots.PREFIX
main = slots.main

ADD = '''safe fn add(borrow mut a:arena::Arena<Item>,n:int):arena::Handle{
 val s:arena::InsertStatus=a.try_insert(new Item(n,alloc<byte>(1)));
 match(s){Inserted(h){return h;}Rejected(code){assert(false);return new arena::Handle();}}
}'''
ARENA = 'own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,1024,0x7fff_ffff_ffff_ffff);'
DRAIN = '''unsafe{
 let keep:**byte=alloc<*byte>(8193);let wide:**byte=alloc<*byte>(8193);let n:int=0;let m:int=0;
 FAULT_ENABLE
 while(true){let p:*byte=try_alloc<byte>(1);if(p==null){break;}keep[n]=p;n++;assert(n<8193);}
 while(true){let p:*byte=try_alloc<byte>(33);if(p==null){break;}wide[m]=p;m++;assert(m<8193);}
'''
CLEAN = '''FAULT_CHECK
 for(let i:int=0;i<n;i++){free(keep[i]);}for(let i:int=0;i<m;i++){free(wide[i]);}
 free(keep);free(wide);}'''


class ArenaRemoval(base.Evolution):
    fault_program = slots.FallibleSlots.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_take_transfers_nested_resources_and_survives_close(self):
        self.accepted(PREFIX + ADD + main(ARENA +
            'val h:arena::Handle=add(a,42);val other:arena::Handle=add(a,7);'
            'own value:Item=a.take(h);assert(!a.contains(h) && a.contains(other) && a.size()==1);'
            'a.close();value.data[0]=byte(9);print(value.n,int(value.data[0]));'), '42 9\n')
        self.accepted('import "std/arena.assis";' + main(
            'own a:arena::Arena<*int>=new arena::Arena<*int>(1,1,2,8);'
            'let h:arena::Handle=new arena::Handle();'
            'own empty:*int=try_alloc<int>(-1);assert(empty==null);'
            'val s:arena::InsertStatus=a.try_insert(move(empty));'
            'match(s){Inserted(id){h=id;}Rejected(code){assert(false);}}'
            'assert(a.contains(h));own value:*int=a.take(h);'
            'assert(value==null && !a.contains(h) && a.size()==0);'))

    def test_erase_rejects_stale_forged_closed_and_previous_instances(self):
        self.accepted(PREFIX + ADD + main(ARENA + 'val h:arena::Handle=add(a,42);'
            'assert(!a.erase(new arena::Handle()));'
            'assert(!a.erase(new arena::Handle(8,1,h.slot,h.generation)));'
            'assert(!a.erase(new arena::Handle(7,2,h.slot,h.generation)));'
            'assert(!a.erase(new arena::Handle(7,1,-1,h.generation)));'
            'assert(!a.erase(new arena::Handle(7,1,0x7fff_ffff_ffff_ffff,1)));'
            'assert(!a.erase(new arena::Handle(7,1,h.slot,0)));'
            'assert(!a.erase(new arena::Handle(7,1,h.slot,-1)));'
            'assert(!a.erase(new arena::Handle(7,1,h.slot,0x7fff_ffff_ffff_ffff)));'
            'assert(a.size()==1 && a.get(h).n==42);assert(a.erase(h));assert(!a.erase(h));'
            'val recycled:arena::Handle=add(a,7);assert(recycled.slot==h.slot && recycled.generation>h.generation);'
            'assert(!a.erase(h) && a.contains(recycled));a.close();assert(!a.erase(recycled));'
            'assert(a.reset(2));val fresh:arena::Handle=add(a,9);'
            'assert(!a.erase(recycled) && a.contains(fresh) && a.size()==1);'))

    def test_retirement_generation_max_and_many_reuses(self):
        self.accepted(PREFIX + ADD + main(
            'own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,1,2);'
            'val h:arena::Handle=add(a,1);{own value:Item=a.take(h);}'
            'val next:arena::Handle=add(a,2);assert(next.generation==2);assert(a.erase(next));'
            'val rejected:arena::InsertStatus=a.try_insert(new Item());'
            'match(rejected){Inserted(id){assert(false);}Rejected(code){assert(code==2);}}'
            'assert(a.size()==0 && a.slots_used()==1 && !a.erase(h) && !a.erase(next));'
            'assert(a.reset(2));val fresh:arena::Handle=add(a,3);assert(fresh.generation==1);'))
        self.accepted(PREFIX + ADD + main(ARENA + 'for(let i:int=0;i<10000;i++){'
            'val current:arena::Handle=add(a,i);assert(current.slot==0 && current.generation==i+1);'
            'if(i%2==0){assert(a.erase(current));}else{own value:Item=a.take(current);assert(value.n==i);}'
            'assert(!a.erase(current));}assert(a.size()==0 && a.slots_used()==1);'))

    def test_operations_against_independent_logical_document_model(self):
        rng = random.Random(20261030)
        live, stale, body, expected = {}, [], ARENA, ''
        sequence, instance = 0, 1
        for step in range(220):
            op = rng.choice(['insert', 'insert', 'take', 'erase', 'stale', 'reset']) if live else 'insert'
            if op == 'insert':
                name = f'h{sequence}'
                sequence += 1
                live[name] = step * 13 - 17
                body += f'val {name}:arena::Handle=add(a,{live[name]});'
            elif op in ('take', 'erase'):
                name = rng.choice(list(live))
                value = live.pop(name)
                stale.append(name)
                if op == 'take':
                    body += f'{{own value:Item=a.take({name});print(value.n);}}'
                    expected += f'{value}\n'
                else:
                    body += f'assert(a.erase({name}));'
            elif op == 'reset':
                stale.extend(live)
                live.clear()
                instance += 1
                body += f'assert(a.reset({instance}));'
            if stale:
                body += f'assert(!a.erase({rng.choice(stale)}));'
            body += 'print(a.size());'
            expected += f'{len(live)}\n'
            for name, value in live.items():
                body += f'assert(a.contains({name}) && a.get({name}).n=={value});'
        self.accepted(PREFIX + ADD + main(body), expected)

    def test_destructors_once_and_transfer_order(self):
        self.accepted('import "std/arena.assis";'
            'final class R{let id:int;own data:*byte;fn init(borrow mut self,id:int):void{'
            'self.id=id;self.data=alloc<byte>(3);}fn drop(borrow mut self):void{print(self.id);}}'
            'safe fn add(borrow mut a:arena::Arena<R>,n:int):arena::Handle{'
            'val s:arena::InsertStatus=a.try_insert(new R(n));'
            'match(s){Inserted(h){return h;}Rejected(code){assert(false);return new arena::Handle();}}}' + main(
            'own a:arena::Arena<R>=new arena::Arena<R>(1,1,8,8);'
            'val first:arena::Handle=add(a,1);val second:arena::Handle=add(a,2);val third:arena::Handle=add(a,3);'
            '{own value:R=a.take(first);assert(a.erase(second));assert(!a.erase(second));'
            'a.close();assert(!a.erase(third));print(value.id+10);}a.close();'), '2\n3\n11\n1\n')

    def test_loans_and_unconsumed_owned_results_are_rejected(self):
        for loan in ['borrow value:Item=a.get(h);', 'borrow mut value:Item=a.get_mut(h);']:
            for op in ['own result:Item=a.take(h);', 'a.erase(h);']:
                with self.subTest(loan=loan, op=op):
                    self.rejected(PREFIX + ADD + main(ARENA + 'val h:arena::Handle=add(a,1);' + loan + op),
                        'borrow mut ativo' if 'borrow mut' in loan else 'exclusivo')
        self.rejected(PREFIX + ADD + main(ARENA + 'val h:arena::Handle=add(a,1);a.take(h);'), 'own')

    def test_invalid_take_has_explicit_contract_trap(self):
        for setup, handle in [('', 'new arena::Handle()'),
                              ('val h:arena::Handle=add(a,1);assert(a.erase(h));', 'h'),
                              ('val h:arena::Handle=add(a,1);a.close();', 'h')]:
            source = self.source(PREFIX + ADD + main(ARENA + setup + f'own value:Item=a.take({handle});'))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, '--debug', *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('R001', result.stderr)

    def test_os_refusal_take_erase_reuse_and_neighbor(self):
        body = (ARENA + 'own neighbor:arena::Arena<Item>=new arena::Arena<Item>(2,7,1,8);'
            'val other:arena::Handle=add(neighbor,77);'
            'val first:arena::Handle=add(a,42);val second:arena::Handle=add(a,7);'
            'own pending:Item=new Item(99,alloc<byte>(1));' + DRAIN +
            'assert(!a.erase(new arena::Handle()));'
            '{own value:Item=a.take(first);assert(value.n==42 && !a.contains(first));'
            'assert(a.erase(second) && !a.erase(second));assert(a.size()==0);'
            'val s:arena::InsertStatus=a.try_insert(move(pending));'
            'match(s){Inserted(h){assert(!a.contains(first) && !a.contains(second) && a.get(h).n==99);'
            'assert(a.erase(h));}Rejected(code){assert(false);}}'
            'assert(neighbor.contains(other) && neighbor.get(other).n==77);'
            'a.close();assert(value.n==42 && len(value.data)==1);}' + CLEAN + 'print(42);')
        self.fault_program(PREFIX + ADD + main(body), '42\n')

    def test_os_refusal_swap_remove_at_sparse_tree_boundaries(self):
        for size, index in [(2, 0), (3, 0), (4, 1), (5, 0), (8, 3), (9, 7), (17, 0), (17, 16)]:
            with self.subTest(size=size, index=index):
                body = ('own a:owned::OwnedArray<Item>=new owned::OwnedArray<Item>();'
                    f'for(let i:int=0;i<{size};i++){{a.push(new Item(i,alloc<byte>(1)));}}' + DRAIN +
                    f'{{own removed:Item=a.swap_remove({index});assert(removed.n=={index});'
                    f'assert(a.size()=={size-1});for(let i:int=0;i<a.size();i++){{'
                    f'if(i=={index}){{assert(a.get(i).n=={size-1});}}else{{assert(a.get(i).n==i);}}}}}}' + CLEAN + 'print(42);')
                self.fault_program(PREFIX + main(body), '42\n')

    def test_typed_ir_all_targets_and_example(self):
        source = base.ROOT / 'exemplos/38_allocation_free_removal.assis'
        self.accepted(source.read_text(encoding='utf-8'), '42 0\n')
        result = self.invoke('ir', source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', source, '--target', target, '-o', self.temp / (target + '.exe'), *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

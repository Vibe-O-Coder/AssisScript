"""Generational identities: independent logical model, reuse, retirement and drops."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

PREFIX = '''import "std/arena.assis";struct Item{let n:int;own data:*byte;}
safe fn add(borrow mut a:arena::Arena<Item>,n:int):arena::Handle{
 own result:arena::Insertion<Item>=a.insert(new Item(n,alloc<byte>(2)));
 match(move(result)){Inserted(h){return h;}Rejected(code,value){assert(false);return new arena::Handle();}}
}
safe fn take(borrow mut a:arena::Arena<Item>,h:arena::Handle):own Item{
 own result:arena::Removal<Item>=a.remove(h);
 match(move(result)){Missing{assert(false);return new Item();}Removed(value){return move(value);}}
}
'''
ARENA = 'own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,1024,0x7fff_ffff_ffff_ffff);'


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


class Arena(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_recycling_preserves_other_identities_and_nested_mutation(self):
        self.accepted(PREFIX + main(ARENA +
            'val h:arena::Handle=add(a,10);val stable:arena::Handle=add(a,20);'
            '{borrow mut item:Item=a.get_mut(stable);item.n=42;item.data[1]=byte(7);}'
            'own removed:Item=take(a,h);val recycled:arena::Handle=add(a,30);'
            'assert(recycled.slot==h.slot && recycled.generation!=h.generation);'
            'assert(!a.contains(h) && a.contains(stable) && a.contains(recycled));'
            '{borrow item:Item=a.get(stable);print(removed.n,item.n,int(item.data[1]));}'
            'a.close();assert(removed.n==10);'), '10 42 7\n')

    def test_forged_domains_generations_and_indices_are_rejected_before_lookup(self):
        self.accepted(PREFIX + main(ARENA + 'val h:arena::Handle=add(a,42);'
            'own invalid:Array<arena::Handle>=[new arena::Handle(),'
            'new arena::Handle(8,1,h.slot,h.generation),new arena::Handle(7,2,h.slot,h.generation),'
            'new arena::Handle(7,1,-1,1),new arena::Handle(7,1,0x7fff_ffff_ffff_ffff,1),'
            'new arena::Handle(7,1,h.slot,0),new arena::Handle(7,1,h.slot,-1),'
            'new arena::Handle(7,1,h.slot,0x7fff_ffff_ffff_ffff)];'
            'for(let i:int=0;i<len(invalid);i++){assert(!a.contains(invalid[i]));'
            'own result:arena::Removal<Item>=a.remove(invalid[i]);'
            'match(move(result)){Missing{}Removed(value){assert(false);}}}'
            'assert(a.size()==1 && a.contains(h));'
            'own other:arena::Arena<Item>=new arena::Arena<Item>(2,7,1,2);assert(!other.contains(h));'))

    def test_exhausted_generation_retires_slot_without_wrap_and_returns_ownership(self):
        self.accepted(PREFIX + main(
            'own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,1,2);'
            'val first:arena::Handle=add(a,1);{own old:Item=take(a,first);}'
            'val second:arena::Handle=add(a,2);assert(second.generation==2);'
            '{own old:Item=take(a,second);}assert(a.size()==0 && a.slots_used()==1);'
            'own result:arena::Insertion<Item>=a.insert(new Item(42,alloc<byte>(2)));'
            'match(move(result)){Inserted(h){assert(false);}Rejected(code,value){assert(code==2);print(value.n);}}'
            'assert(!a.contains(first) && !a.contains(second));assert(a.reset(2));'
            'val fresh:arena::Handle=add(a,3);assert(fresh.instance==2 && fresh.generation==1);'
            'assert(!a.contains(first) && !a.contains(second));'), '42\n')

    def test_close_reset_and_instance_exhaustion(self):
        self.accepted(PREFIX + main(ARENA + 'val h:arena::Handle=add(a,1);a.close();a.close();'
            'assert(!a.contains(h) && a.size()==0 && a.slots_used()==0);'
            'assert(!a.reset(1) && !a.reset(0) && !a.reset(-1));'
            'own rejected:arena::Insertion<Item>=a.insert(new Item(42,alloc<byte>(1)));'
            'match(move(rejected)){Inserted(x){assert(false);}Rejected(code,value){assert(code==1 && value.n==42);}}'
            'assert(a.reset(0x7fff_ffff_ffff_ffff));val last:arena::Handle=add(a,2);'
            'assert(!a.reset(1) && !a.reset(0x7fff_ffff_ffff_ffff));assert(a.contains(last));'
            'a.close();assert(!a.contains(last));'))

    def test_random_operations_against_independent_logical_object_model(self):
        # Model object identity only; do not predict the arena's storage/free list.
        rng = random.Random(20261101)
        live, allocated, instance = {}, 0, 1
        body = ARENA + 'own handles:Array<arena::Handle>=[];'
        for step in range(180):
            action = rng.choice(['insert', 'insert', 'mutate', 'remove', 'reset']) if live else 'insert'
            value = step * 13 - 31
            if action == 'insert':
                live[allocated] = value
                allocated += 1
                body += f'handles.push(add(a,{value}));'
            elif action == 'mutate':
                identity = rng.choice(list(live))
                live[identity] = value
                body += f'{{borrow mut item:Item=a.get_mut(handles[{identity}]);item.n={value};}}'
            elif action == 'remove':
                identity = rng.choice(list(live))
                previous = live.pop(identity)
                body += f'{{own old:Item=take(a,handles[{identity}]);assert(old.n=={previous});}}'
            else:
                live.clear()
                instance += 1
                body += f'assert(a.reset({instance}));'
            body += f'assert(a.size()=={len(live)});'
            for identity in range(allocated):
                expected = 'true' if identity in live else 'false'
                body += f'assert(a.contains(handles[{identity}])=={expected});'
                if identity in live:
                    body += f'{{borrow item:Item=a.get(handles[{identity}]);assert(item.n=={live[identity]});}}'
        self.accepted(PREFIX + main(body))

    def test_drop_once_after_rejection_removal_reset_and_close(self):
        code = 'import "std/arena.assis";final class R{let id:int;own data:*byte;'
        code += 'fn init(borrow mut self,id:int):void{self.id=id;self.data=alloc<byte>(1);}'
        code += 'fn drop(borrow mut self):void{print(self.id);}}'
        source = self.source(code + main(
            'own a:arena::Arena<R>=new arena::Arena<R>(1,1,2,2);'
            'let first:arena::Handle=new arena::Handle();'
            '{own r:arena::Insertion<R>=a.insert(new R(1));match(move(r)){Inserted(h){first=h;}Rejected(c,v){assert(false);}}}'
            '{own r:arena::Insertion<R>=a.insert(new R(2));}'
            'own held:arena::Removal<R>=a.remove(first);'
            '{own r:arena::Insertion<R>=a.insert(new R(3));}'
            '{own r:arena::Insertion<R>=a.insert(new R(4));match(move(r)){Inserted(h){assert(false);}Rejected(c,v){assert(v.id==4);}}}'
            'assert(a.reset(2));a.close();a.close();'
            '{own r:arena::Insertion<R>=a.insert(new R(5));}'
            'match(held){Missing{assert(false);}Removed(v){assert(v.id==1);}}'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, '--debug', *flags)
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            ids = [int(x) for x in result.stdout.splitlines()]
            self.assertCountEqual(ids, [1, 2, 3, 4, 5])
            self.assertEqual(ids[-1], 1)

    def test_loans_block_mutation_close_reset_and_owner_destruction(self):
        start = PREFIX + 'safe fn main():int{' + ARENA + 'val h:arena::Handle=add(a,1);'
        for loan in ['borrow item:Item=a.get(h);', 'borrow mut item:Item=a.get_mut(h);']:
            for operation in ['a.close();', 'a.reset(2);', 'own r:arena::Removal<Item>=a.remove(h);',
                              'own r:arena::Insertion<Item>=a.insert(new Item());', 'free(a);']:
                with self.subTest(loan=loan, operation=operation):
                    self.rejected(start + loan + operation + 'return 0;}', 'borrow')
        self.rejected(start + 'borrow item:Item=a.get(h);item.n=2;return 0;}', 'exclusivo')

    def test_local_loans_cannot_escape(self):
        self.rejected(PREFIX +
            'safe fn bad(borrow owner:arena::Arena<Item>):borrow(owner) Item{' + ARENA +
            'val h:arena::Handle=add(a,1);return a.get(h);}' + main(''), 'local')

    def test_invalid_get_is_contract_error_and_init_cannot_replay_old_instance(self):
        for operation in ['borrow item:Item=a.get(new arena::Handle());',
                          'borrow mut item:Item=a.get_mut(new arena::Handle());']:
            source = self.source(PREFIX + main(ARENA + operation))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, '--debug', *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('assis: erro', result.stderr)
        for operation in ['a.init(1,7,1024,2);', 'a.close();a.init(1,7,1024,2);']:
            self.rejected(PREFIX + main(ARENA + operation), 'só pode ser chamado por new')

    def test_constructor_preconditions_and_zero_slot_limit(self):
        for arguments in ['0,7,1,2', '-1,7,1,2', '1,0,1,2', '1,7,-1,2', '1,7,1,0']:
            source = self.source(PREFIX + main('own a:arena::Arena<Item>=new arena::Arena<Item>(' + arguments + ');'))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, '--debug', *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
        self.accepted(PREFIX + main('own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,0,1);'
            'own result:arena::Insertion<Item>=a.insert(new Item(42,alloc<byte>(1)));'
            'match(move(result)){Inserted(h){assert(false);}Rejected(code,value){assert(code==2 && value.n==42);}}'
            'assert(a.size()==0 && a.slots_used()==0);'))

    def test_repeated_recycling_stays_within_slot_quota(self):
        self.accepted(PREFIX + main('own a:arena::Arena<Item>=new arena::Arena<Item>(1,7,1,0x7fff_ffff_ffff_ffff);'
            'for(let i:int=0;i<10000;i++){val h:arena::Handle=add(a,i);'
            '{own old:Item=take(a,h);assert(old.n==i);}assert(!a.contains(h));}'
            'assert(a.size()==0 && a.slots_used()==1);'))

    def test_buffers_preserve_owned_payload(self):
        self.accepted('import "std/arena.assis";' + main(
            'own a:arena::Arena<*int>=new arena::Arena<*int>(1,1,2,2);'
            'let h:arena::Handle=new arena::Handle();'
            '{own r:arena::Insertion<*int>=a.insert(alloc<int>(1));match(move(r)){Inserted(x){h=x;}Rejected(c,v){assert(false);}}}'
            '{borrow mut value:*int=a.get_mut(h);value[0]=42;}'
            '{own r:arena::Removal<*int>=a.remove(h);match(move(r)){Missing{assert(false);}Removed(v){print(v[0]);}}}'
            'assert(!a.contains(h));'), '42\n')

    def test_typed_ir_output_formats_and_example(self):
        source = base.ROOT / 'exemplos/34_generational_arena.assis'
        self.accepted(source.read_text(encoding='utf-8'), '42\n')
        ir = self.invoke('ir', source)
        self.assertEqual(ir.returncode, 0, ir.stderr)
        self.assertEqual(json.loads(ir.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', source, '--target', target, '-o', self.temp / (target + '.exe'), *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

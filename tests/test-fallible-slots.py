"""Fallible construction/insertion: independent models and OS refusal at each path.

The Windows fixture denies only this test executable's slab mappings. Linux
uses seccomp in the child. Neither adds a hook to the production allocator.
"""
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import unittest

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

base = module('evolution', Path(__file__).with_name('test-evolution.py'))
PREFIX = 'import "std/arena.assis";struct Item{let n:int;own data:*byte;}'
ARRAY = 'own a:owned::OwnedArray<Item>=new owned::OwnedArray<Item>();'

def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'

def item(n):
    return f'new Item({n},alloc<byte>(1))'

class FallibleSlots(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_record_generic_class_inheritance_and_owned_enum(self):
        self.accepted('value struct Pair{let x:int;let y:int;}'
            'struct S<T>{let n:T;let p:Pair;own data:*byte;}'
            'class Base{let n:int;fn init(borrow mut self,n:int):void{self.n=n;}'
            'fn read(borrow self):int{return self.n;}}'
            'class Child extends Base{fn read(borrow self):int{return self.n+1;}}'
            'enum E{None;Some(own *int,Pair);}' + main(
            'own s:S<int>=try_new S<int>(42,new Pair(2,3),alloc<byte>(2));'
            'assert(s!=null && s.n==42 && s.p.y==3 && len(s.data)==2);'
            'own zero:S<int>=try_new S<int>();assert(zero.n==0 && zero.data==null);'
            'own c:Base=try_new Child(41);assert(c.read()==42);'
            'own e:E=try_new E.Some(alloc<int>(1),new Pair(4,5));'
            'assert(e!=null);match(move(e)){None{}Some(data,p){data[0]=42;print(data[0],p.x);}}'), '42 4\n')

    def test_argument_order_constructor_and_cleanup(self):
        self.accepted('final class R{let n:int;fn init(borrow mut self,n:int):void{self.n=n;}'
            'fn drop(borrow mut self):void{print(self.n);}}'
            'safe fn arg(n:int):own R{print(n+10);return new R(n);}'
            'final class C{own first:R;own second:R;fn init(borrow mut self,own a:R,own b:R):void{'
            'print(30);self.first=move(a);self.second=move(b);}}' + main(
            '{own c:C=try_new C(arg(1),arg(2));assert(c!=null);}print(40);'), '11\n12\n30\n2\n1\n40\n')

    def test_safe_ownership_effects_value_types_and_borrows(self):
        for source, message in [
            ('struct S{let n:int;}' + main('let s:S=try_new S();'), 'own'),
            ('value struct S{let n:int;}' + main('val s:S=try_new S();'), 'value'),
            ('enum E{None;Some(int);}' + main('val e:E=try_new E.None();'), 'value'),
            ('struct S{let n:int;}pure fn bad():int{own s:S=try_new S();return 0;}' + main(''), 'pure'),
            ('value struct S{let n:int;}pure fn unused<T>():int{val s:S=try_new S(1);return 0;}' + main(''), 'pure'),
            (PREFIX + main(ARRAY + 'own x:Item=try_new Item(1,alloc<byte>(1));'
                'a.try_push(move(x));print(x.n);'), 'movido'),
            (PREFIX + main(ARRAY + 'a.push(' + item(1) + ');borrow x:Item=a.get(0);a.try_push(' + item(2) + ');'), 'exclusivo'),
            (PREFIX + main('own a:arena::Arena<Item>=new arena::Arena<Item>(1,2,4,8);'
                'val s:arena::InsertStatus=a.try_insert(' + item(1) + ');'
                'match(s){Inserted(h){borrow x:Item=a.get(h);a.try_insert(' + item(2) + ');}Rejected(code){}}'), 'exclusivo'),
        ]:
            with self.subTest(source=source):
                self.rejected(source, message)

    def test_array_against_independent_list_model(self):
        rng = random.Random(20261030)
        model, body, expected = [], ARRAY, ''
        for step in range(240):
            operation = rng.choice(['push', 'push', 'pop', 'remove', 'clear']) if model else 'push'
            if operation == 'push':
                model.append(step)
                body += 'assert(a.try_push(' + item(step) + '));'
            elif operation == 'pop':
                expected += str(model.pop()) + '\n'
                body += '{own x:Item=a.pop();print(x.n);}'
            elif operation == 'remove':
                index = rng.randrange(len(model))
                expected += str(model[index]) + '\n'
                model[index] = model[-1]
                model.pop()
                body += '{own x:Item=a.swap_remove(' + str(index) + ');print(x.n);}'
            else:
                model.clear()
                body += 'a.clear();'
            body += 'print(a.size());for(let i:int=0;i<a.size();i++){print(a.get(i).n);}'
            expected += str(len(model)) + '\n' + ''.join(f'{n}\n' for n in model)
        self.accepted(PREFIX + main(body), expected)

    def test_arena_limits_recycling_generation_and_closed_rejection(self):
        self.accepted(PREFIX + main(
            'own a:arena::Arena<Item>=new arena::Arena<Item>(1,2,1,2);'
            'let old:arena::Handle=new arena::Handle();'
            'val first:arena::InsertStatus=a.try_insert(' + item(1) + ');'
            'match(first){Inserted(h){old=h;}Rejected(code){assert(false);}}'
            'assert(a.contains(old));'
            'val full:arena::InsertStatus=a.try_insert(' + item(2) + ');'
            'match(full){Inserted(h){assert(false);}Rejected(code){assert(code==2);}}'
            '{own removed:arena::Removal<Item>=a.remove(old);}'
            'val next:arena::InsertStatus=a.try_insert(' + item(3) + ');'
            'match(next){Inserted(h){assert(h.slot==old.slot && h.generation==2 && !a.contains(old));'
            'own removed:arena::Removal<Item>=a.remove(h);}Rejected(code){assert(false);}}'
            'val retired:arena::InsertStatus=a.try_insert(' + item(4) + ');'
            'match(retired){Inserted(h){assert(false);}Rejected(code){assert(code==2);}}'
            'a.close();val closed:arena::InsertStatus=a.try_insert(' + item(5) + ');'
            'match(closed){Inserted(h){assert(false);}Rejected(code){assert(code==1);}}'
            'assert(a.reset(2));val fresh:arena::InsertStatus=a.try_insert(' + item(6) + ');'
            'match(fresh){Inserted(h){assert(h.instance==2 && !a.contains(old));}Rejected(code){assert(false);}}'))

    def fault_program(self, text, expected):
        is_windows = os.name == 'nt' and platform.machine().lower() in ('amd64', 'x86_64')
        is_linux = platform.system() == 'Linux' and platform.machine() == 'x86_64'
        if not (is_windows or is_linux):
            self.skipTest('OS slab refusal requires Windows/Linux x64')
        cc = str(Path(os.environ.get('ASSIS_TOOLCHAIN_BIN', 'C:/msys64/ucrt64/bin')) / 'gcc.exe') if is_windows else 'cc'
        library = self.temp / ('allocation_fault.dll' if is_windows else 'allocation_fault.so')
        environment = dict(os.environ, PATH=str(Path(cc).parent) + os.pathsep + os.environ.get('PATH', ''))
        if not library.exists():
            subprocess.run([cc, '-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Werror',
                '-shared', '-fPIC', str(base.ROOT / ('tests/allocation-fault-windows.c' if is_windows else 'tests/allocation-fault-linux.c')),
                '-o', str(library)], env=environment, check=True, capture_output=True)
        path = json.dumps(library.as_posix())
        header = f'extern({path},{path},"fault_enable") fn fault_enable():i32;'
        if is_windows:
            header += f'extern({path},{path},"fault_hits") fn fault_hits():i32;'
        text = header + text.replace('FAULT_ENABLE', 'unsafe{assert(fault_enable()==i32(0));}')
        text = text.replace('FAULT_CHECK', 'unsafe{assert(fault_hits()>i32(0));}' if is_windows else '')
        source = self.source(text)
        for flags in [[], ['--no-opt']]:
            binary = self.temp / ('fault-reference.exe' if flags else 'fault.exe')
            result = self.invoke('build', source, '--debug', '-o', binary, *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], cwd=self.temp, capture_output=True,
                text=True, encoding='utf-8', timeout=20)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, ''), flags)

    def test_os_refusal_does_not_skip_argument_effects_and_drops_in_reverse(self):
        prefix = ('final class R{let id:int;fn init(borrow mut self,n:int):void{self.id=n;}'
            'fn drop(borrow mut self):void{print(self.id);}}'
            'safe fn take(own r:R):own R{print(r.id+10);return move(r);}')
        # R/C/1-byte fillers all occupy the smallest class. No owned resources
        # are created after denial; argument calls only transfer existing ones.
        for definition, construction in [
            ('final class C{own a:R;own b:R;fn init(borrow mut self,own a:R,own b:R):void{assert(false);}}', 'C'),
            ('struct C{own a:R;own b:R;}', 'C'),
            ('enum C{None;Some(own R,own R);}', 'C.Some'),
        ]:
            with self.subTest(construction=construction):
                body = ('own a:R=new R(1);own b:R=new R(2);'
                    'unsafe{let keep:**byte=alloc<*byte>(8193);let n:int=0;FAULT_ENABLE'
                    'while(true){let p:*byte=try_alloc<byte>(1);if(p==null){break;}keep[n]=p;n++;assert(n<8193);}'
                    'own c:C=try_new ' + construction + '(take(move(a)),take(move(b)));assert(c==null);'
                    'FAULT_CHECK for(let i:int=0;i<n;i++){free(keep[i]);}free(keep);}print(42);')
                self.fault_program(prefix + definition + main(body), '11\n12\n2\n1\n42\n')

    def test_os_refusal_rolls_back_each_array_insertion_path(self):
        for existing, allocations in [(0, 1), (1, 2), (2, 3), (3, 1), (4, 4), (5, 1), (6, 2), (7, 1), (8, 5)]:
            for available in range(allocations+1):
                with self.subTest(existing=existing, available=available):
                    success = available == allocations
                    body = (ARRAY + 'for(let i:int=0;i<' + str(existing) + ';i++){a.push(new Item(i,alloc<byte>(1)));}'
                        'own value:Item=' + item(99) + ';'
                        'unsafe{let keep:**byte=alloc<*byte>(8193);let n:int=0;FAULT_ENABLE'
                        'while(true){let p:*byte=try_alloc<byte>(1);if(p==null){break;}keep[n]=p;n++;assert(n<8193);}'
                        'for(let i:int=0;i<' + str(available) + ';i++){n--;free(keep[n]);}'
                        'assert(a.try_push(move(value))==' + str(success).lower() + ');assert(a.size()==' + str(existing+int(success)) + ');'
                        'for(let i:int=0;i<' + str(existing) + ';i++){assert(a.get(i).n==i && len(a.get(i).data)==1);}'
                        + ('assert(a.get(' + str(existing) + ').n==99);' if success else '') +
                        'FAULT_CHECK for(let i:int=0;i<n;i++){free(keep[i]);}free(keep);}print(42);')
                    self.fault_program(PREFIX + main(body), '42\n')

    def test_os_refusal_preserves_arena_slots_handles_and_neighbor(self):
        for existing, path in [(0, 1), (4, 4)]:
            # One slot object (128-byte class), then path nodes (64-byte class).
            for small, slots in [(0, 0), *[(n, 1) for n in range(path+1)]]:
                with self.subTest(existing=existing, small=small, slots=slots):
                    success = slots == 1 and small == path
                    body = ('own a:arena::Arena<Item>=new arena::Arena<Item>(1,2,32,16);'
                        'own neighbor:arena::Arena<Item>=new arena::Arena<Item>(2,2,2,16);'
                        'val other:arena::InsertStatus=neighbor.try_insert(' + item(77) + ');'
                        'own handles:*arena::Handle=alloc<arena::Handle>(16);'
                        'for(let i:int=0;i<' + str(existing) + ';i++){'
                        'val s:arena::InsertStatus=a.try_insert(new Item(i,alloc<byte>(1)));'
                        'match(s){Inserted(h){handles[i]=h;}Rejected(code){assert(false);}}}'
                        'own value:Item=' + item(99) + ';unsafe{'
                        'let keep:**byte=alloc<*byte>(8193);let wide:**byte=alloc<*byte>(8193);let n:int=0;let m:int=0;FAULT_ENABLE'
                        'while(true){let p:*byte=try_alloc<byte>(1);if(p==null){break;}keep[n]=p;n++;assert(n<8193);}'
                        'while(true){let p:*byte=try_alloc<byte>(33);if(p==null){break;}wide[m]=p;m++;assert(m<8193);}'
                        'for(let i:int=0;i<' + str(small) + ';i++){n--;free(keep[n]);}'
                        'for(let i:int=0;i<' + str(slots) + ';i++){m--;free(wide[m]);}'
                        'val s:arena::InsertStatus=a.try_insert(move(value));'
                        'match(s){Inserted(h){assert(' + str(success).lower() + ' && h.slot==' + str(existing) + ');'
                        'assert(a.get(h).n==99);}Rejected(code){assert(' + str(not success).lower() + ' && code==3);}}'
                        'assert(a.size()==' + str(existing+int(success)) + ' && a.slots_used()==' + str(existing+int(success)) + ');'
                        'for(let i:int=0;i<' + str(existing) + ';i++){assert(a.contains(handles[i]) && a.get(handles[i]).n==i);}'
                        'match(other){Inserted(h){assert(neighbor.contains(h) && neighbor.get(h).n==77);}Rejected(code){assert(false);}}'
                        'FAULT_CHECK for(let i:int=0;i<n;i++){free(keep[i]);}for(let i:int=0;i<m;i++){free(wide[i]);}'
                        'free(keep);free(wide);}print(42);')
                    self.fault_program(PREFIX + main(body), '42\n')

    def test_targets_and_ir(self):
        source = self.source(PREFIX + main(ARRAY + 'assert(a.try_push(try_new Item(42,try_alloc<byte>(1))));'))
        result = self.invoke('ir', source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', source, '--target', target, '-o', self.temp / (target + '.exe'), *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))

    def test_arena_free_slot_reuse_needs_no_allocation_under_os_refusal(self):
        body = ('own a:arena::Arena<Item>=new arena::Arena<Item>(1,2,1,8);'
            'let old:arena::Handle=new arena::Handle();'
            'val first:arena::InsertStatus=a.try_insert(' + item(1) + ');'
            'match(first){Inserted(h){old=h;}Rejected(code){assert(false);}}'
            '{own removed:arena::Removal<Item>=a.remove(old);}'
            'own value:Item=' + item(99) + ';unsafe{'
            'let keep:**byte=alloc<*byte>(8193);let wide:**byte=alloc<*byte>(8193);let n:int=0;let m:int=0;FAULT_ENABLE'
            'while(true){let p:*byte=try_alloc<byte>(1);if(p==null){break;}keep[n]=p;n++;assert(n<8193);}'
            'while(true){let p:*byte=try_alloc<byte>(33);if(p==null){break;}wide[m]=p;m++;assert(m<8193);}'
            'val s:arena::InsertStatus=a.try_insert(move(value));'
            'match(s){Inserted(h){assert(h.slot==old.slot && h.generation==old.generation+1);'
            'assert(!a.contains(old) && a.contains(h) && a.get(h).n==99);}Rejected(code){assert(false);}}'
            'FAULT_CHECK for(let i:int=0;i<n;i++){free(keep[i]);}for(let i:int=0;i<m;i++){free(wide[i]);}'
            'free(keep);free(wide);}print(42);')
        self.fault_program(PREFIX + main(body), '42\n')

    def test_example_and_large_regrowth(self):
        self.accepted((base.ROOT / 'exemplos/37_fallible_slots.assis').read_text(encoding='utf-8'), '42 1\n')
        self.accepted((base.ROOT / 'tests/fixtures/fallible-construct.assis').read_text(encoding='utf-8'), '11\n12\n42 7\n2\n1\n')
        self.accepted(PREFIX + main(ARRAY +
            'for(let i:int=0;i<4097;i++){assert(a.try_push(new Item(i,alloc<byte>(1))));}'
            'for(let i:int=4096;i>=0;i--){own x:Item=a.pop();assert(x.n==i);}'
            'for(let i:int=0;i<2049;i++){assert(a.try_push(new Item(i,alloc<byte>(1))));}'
            'for(let i:int=0;i<2049;i++){assert(a.get(i).n==i);}a.clear();'))

if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

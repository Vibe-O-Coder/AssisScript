"""Owned resources for document trees: mutation, transfer, cleanup and loan safety."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

PREFIX = 'import "std/owned.assis";struct Item{let n:int;own data:*byte;}'
ARRAY = 'own items:owned::OwnedArray<Item>=new owned::OwnedArray<Item>();'


def item(value):
    return f'new Item({value},alloc<byte>(3))'


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


class OwnedMutation(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_exclusive_loans_mutate_nested_resources_and_polymorphic_items(self):
        self.accepted(PREFIX +
            'safe fn first(borrow mut items:owned::OwnedArray<Item>):borrow mut(items) Item{return items.get_mut(0);}' +
            main(ARRAY + 'items.push(' + item(1) + ');'
            '{borrow mut value:Item=first(items);value.n=42;value.data[2]=byte(7);}'
            '{borrow value:Item=items.get(0);print(value.n,int(value.data[2]));}'), '42 7\n')
        self.accepted('import "std/owned.assis";'
            'class Base{own data:*int;fn init(borrow mut self,n:int):void{self.data=alloc<int>(1);self.data[0]=n;}'
            'fn read(borrow self):int{return self.data[0];}fn set(borrow mut self,n:int):void{self.data[0]=n;}}'
            'class Child extends Base{fn read(borrow self):int{return self.data[0]+1;}}' + main(
            'own items:owned::OwnedArray<Base>=new owned::OwnedArray<Base>();items.push(new Child(40));'
            '{borrow mut value:Base=items.get_mut(0);value.set(41);}'
            '{borrow value:Base=items.get(0);print(value.read());}'), '42\n')
        self.accepted('import "std/owned.assis";' + main(
            'own items:owned::OwnedArray<*int>=new owned::OwnedArray<*int>();items.push(alloc<int>(2));'
            '{borrow mut data:*int=items.get_mut(0);data[1]=42;}'
            'own old:*int=items.replace(0,alloc<int>(1));print(old[1]);'), '42\n')

    def test_mixed_operations_against_independent_python_model(self):
        rng = random.Random(20261029)
        model = []
        body = ARRAY
        output = ''
        for step in range(180):
            operation = rng.choice(['push', 'push', 'mutate', 'replace', 'remove', 'pop', 'clear'])
            if not model:
                operation = 'push'
            value = step * 17 - 31
            index = rng.randrange(len(model)) if model else 0
            if operation == 'push':
                model.append(value)
                body += 'items.push(' + item(value) + ');'
            elif operation == 'mutate':
                model[index] = value
                body += f'{{borrow mut entry:Item=items.get_mut({index});entry.n={value};}}'
            elif operation == 'replace':
                previous = model[index]
                model[index] = value
                body += f'{{own old:Item=items.replace({index},' + item(value) + ');print(old.n);}'
                output += f'{previous}\n'
            elif operation == 'remove':
                previous = model[index]
                model[index] = model[-1]
                model.pop()
                body += f'{{own removed:Item=items.swap_remove({index});print(removed.n);}}'
                output += f'{previous}\n'
            elif operation == 'pop':
                previous = model.pop()
                body += '{own removed:Item=items.pop();print(removed.n);}'
                output += f'{previous}\n'
            else:
                model.clear()
                body += 'items.clear();'
            body += 'print(items.size());for(let i:int=0;i<items.size();i++){borrow entry:Item=items.get(i);print(entry.n);}'
            output += f'{len(model)}\n' + ''.join(f'{entry}\n' for entry in model)
        self.accepted(PREFIX + main(body), output)

    def test_sparse_paths_after_large_removal_and_regrowth(self):
        self.accepted(PREFIX + main(ARRAY +
            'for(let i:int=0;i<8193;i++){items.push(new Item(i,alloc<byte>(3)));}'
            'for(let i:int=8192;i>=0;i--){own removed:Item=items.pop();assert(removed.n==i);}'
            'assert(items.size()==0);'
            'for(let i:int=0;i<4097;i++){items.push(new Item(i,alloc<byte>(3)));}'
            'for(let i:int=0;i<2048;i++){{own removed:Item=items.swap_remove(0);}}'
            '{borrow mut entry:Item=items.get_mut(2048);entry.n=42;}'
            '{own old:Item=items.replace(2048,new Item(99,alloc<byte>(3)));assert(old.n==42);}'
            'print(items.size());items.clear();items.clear();items.push(' + item(7) + ');'
            '{borrow entry:Item=items.get(0);print(entry.n);}'), '2049\n7\n')

    def test_every_removal_position_across_tree_boundaries(self):
        # Model the public unordered-remove contract, independently of tree paths.
        body, output = ARRAY, ''
        for size in [1, 2, 3, 7, 8, 9, 15, 16, 17, 31, 32, 33]:
            for index in range(size):
                values = list(range(size))
                previous = values[index]
                values[index] = values[-1]
                values.pop()
                body += 'items.clear();'
                body += f'for(let n:int=0;n<{size};n++){{items.push(new Item(n,alloc<byte>(1)));}}'
                body += f'{{own removed:Item=items.swap_remove({index});print(removed.n);}}'
                body += 'for(let n:int=0;n<items.size();n++){borrow entry:Item=items.get(n);print(entry.n);}'
                output += f'{previous}\n' + ''.join(f'{n}\n' for n in values)
        self.accepted(PREFIX + main(body), output)

    def test_random_resource_destruction_against_allocation_ledger(self):
        rng = random.Random(20261030)
        values, allocated, body = [], [], ''
        for step in range(240):
            operation = rng.choice(['push', 'push', 'push', 'replace', 'remove', 'pop']) if values else 'push'
            index = rng.randrange(len(values)) if values else 0
            if operation in ('push', 'replace'):
                allocated.append(step)
                if operation == 'push':
                    values.append(step)
                    body += f'items.push(new Resource({step}));'
                else:
                    previous = values[index]
                    values[index] = step
                    body += f'{{own old:Resource=items.replace({index},new Resource({step}));assert(old.id=={previous});}}'
            else:
                previous = values[index] if operation == 'remove' else values[-1]
                if operation == 'remove':
                    values[index] = values[-1]
                values.pop()
                call = f'items.swap_remove({index})' if operation == 'remove' else 'items.pop()'
                body += f'{{own old:Resource={call};assert(old.id=={previous});}}'
            if step % 47 == 46:
                values.clear()
                body += 'items.clear();items.clear();'
            body += f'assert(items.size()=={len(values)});'
            for position, value in enumerate(values):
                body += f'{{borrow entry:Resource=items.get({position});assert(entry.id=={value});}}'
        source = self.source('import "std/owned.assis";final class Resource{let id:int;own data:*byte;'
            'fn init(borrow mut self,id:int):void{self.id=id;self.data=alloc<byte>(2);}'
            'fn drop(borrow mut self):void{print(self.id);}}' + main(
            'own items:owned::OwnedArray<Resource>=new owned::OwnedArray<Resource>();' + body))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, '--debug', *flags)
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            self.assertCountEqual([int(line) for line in result.stdout.splitlines()], allocated)

    def test_transferred_resources_survive_clear_and_drop_exactly_once(self):
        source = self.source('import "std/owned.assis";'
            'final class Resource{let id:int;own data:*byte;'
            'fn init(borrow mut self,id:int):void{self.id=id;self.data=alloc<byte>(1);}'
            'fn drop(borrow mut self):void{print(self.id);}}' + main(
            'own items:owned::OwnedArray<Resource>=new owned::OwnedArray<Resource>();'
            'items.push(new Resource(1));items.push(new Resource(2));items.push(new Resource(3));'
            'own old:Resource=items.replace(1,new Resource(4));'
            'own removed:Resource=items.swap_remove(0);print("held");'
            'items.clear();print("cleared");assert(old.id==2 && removed.id==1);'
            'items.push(new Resource(5));items.clear();items.clear();print("end");'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, '--debug', *flags)
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            lines = result.stdout.splitlines()
            self.assertEqual(lines[0], 'held')
            self.assertCountEqual(lines[1:3], ['3', '4'])
            self.assertEqual(lines[3:6], ['cleared', '5', 'end'])
            self.assertCountEqual(lines[6:], ['1', '2'])

    def test_cleanup_on_break_continue_and_early_return(self):
        self.accepted(PREFIX + 'safe fn early():own Item{' + ARRAY +
            'items.push(' + item(42) + ');items.push(' + item(9) + ');'
            'return items.swap_remove(0);}' + main(
            'for(let i:int=0;i<100;i++){' + ARRAY + 'items.push(' + item(1) + ');'
            'own removed:Item=items.replace(0,' + item(2) + ');'
            'if(i%2==0){continue;}if(i==51){break;}}'
            'own result:Item=early();print(result.n);'), '42\n')

    def test_shared_and_exclusive_loans_block_conflicting_access(self):
        start = PREFIX + 'safe fn main():int{' + ARRAY + 'items.push(' + item(1) + ');'
        for operation in ['borrow mut other:Item=items.get_mut(0);', 'own other:Item=items.replace(0,' + item(2) + ');',
                          'own other:Item=items.swap_remove(0);', 'items.clear();']:
            with self.subTest(shared=operation):
                self.rejected(start + 'borrow entry:Item=items.get(0);' + operation + 'return 0;}', 'exclusivo')
        for operation in ['borrow other:Item=items.get(0);', 'borrow mut other:Item=items.get_mut(0);', 'items.size();',
                          'items.push(' + item(2) + ');', 'own other:Item=items.replace(0,' + item(2) + ');',
                          'own other:Item=items.swap_remove(0);', 'own other:Item=items.pop();', 'items.clear();']:
            with self.subTest(exclusive=operation):
                self.rejected(start + 'borrow mut entry:Item=items.get_mut(0);' + operation + 'return 0;}', 'borrow incompatível')
        self.rejected(start + 'borrow mut entry:Item=items.get_mut(0);free(items);return 0;}', 'borrow ativo')
        self.rejected(start + 'borrow entry:Item=items.get(0);entry.n=2;return 0;}', 'exclusivo')

    def test_loans_cannot_escape_or_be_promoted_to_ownership(self):
        self.rejected(PREFIX + 'safe fn bad(borrow source:owned::OwnedArray<Item>):borrow(source) Item{' + ARRAY +
            'items.push(' + item(1) + ');return items.get_mut(0);}' + main(''), 'local')
        for binding, message in [('own entry:Item=items.get_mut(0);', 'own'),
                                 ('borrow mut entry:Item=items.get(0);', 'compartilhada')]:
            self.rejected(PREFIX + main(ARRAY + 'items.push(' + item(1) + ');' + binding), message)

    def test_invalid_indices_are_runtime_contract_errors(self):
        for method, arguments in [('get_mut', ''), ('replace', ',' + item(9)), ('swap_remove', '')]:
            for size, index in [(0, 0), (1, -1), (1, 1), (1, 9223372036854775807)]:
                body = ARRAY + ('items.push(' + item(1) + ');' if size else '')
                binding = 'borrow mut result:Item=' if method == 'get_mut' else 'own result:Item='
                source = self.source(PREFIX + main(body + binding + f'items.{method}({index}{arguments});'))
                for flags in [[], ['--no-opt']]:
                    with self.subTest(method=method, size=size, index=index, flags=flags):
                        result = self.invoke('run', source, '--debug', *flags)
                        self.assertEqual(result.returncode, 70, result.stderr)
                        self.assertIn('assis: erro', result.stderr)

    def test_all_output_targets_and_typed_ir(self):
        source = self.source(PREFIX + main(ARRAY + 'items.push(' + item(1) + ');'
            '{borrow mut entry:Item=items.get_mut(0);entry.n=42;}'
            'own old:Item=items.replace(0,' + item(9) + ');'
            'own removed:Item=items.swap_remove(0);items.clear();'))
        result = self.invoke('ir', source)
        self.assertEqual(result.returncode, 0, result.stderr)
        ir = json.loads(result.stdout)
        self.assertEqual(ir['backendFormat'], 'AssisScript-TypedIR-v1')
        self.assertEqual(ir['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', source, '--target', target, '-o', self.temp / (target + '.exe'), *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))

    def test_document_resource_example(self):
        example = base.ROOT / 'exemplos/32_document_resources.assis'
        self.accepted(example.read_text(encoding='utf-8'), '11 42\n12 Pronto\n')


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

"""Document payload budget, ordered-tree model and bounded child-local OOM."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('preparation', Path(__file__).with_name('test-buffer-preallocation.py'))
preparation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)
base = preparation.base
main = preparation.main
PREFIX = '''import "std/doctree.assis";
safe fn append(borrow mut t:doctree::Tree,p:doctree::NodeId,k:int,borrow data:slice<byte>):doctree::NodeId{
 val r:doctree::Append=t.try_append(p,k,data);
 match(r){Appended(h){return h;}Rejected(c){assert(false);return new doctree::NodeId();}}
}
safe fn rejected(r:doctree::Append,code:int):void{
 match(r){Appended(h){assert(false);}Rejected(c){assert(c==code);}}
}
pure fn eq(a:doctree::NodeId,b:doctree::NodeId):bool{
 return a.instance==b.instance && a.slot==b.slot && a.generation==b.generation;
}'''
EMPTY = 'new doctree::NodeId()'
TREE = 'own t:doctree::Tree=try_new doctree::Tree(1,4096,64,100000);assert(t!=null && t.is_open());'


def data(value):
    return 'utf8(' + json.dumps(value, ensure_ascii=False).replace('\\u0000', '\\0') + ')'


class DocumentTree(base.Evolution):
    fault_program = preparation.BufferPreallocation.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_shared_record_text_budget_and_transient_growth(self):
        self.accepted(PREFIX + main(
            'own t:doctree::Tree=try_new doctree::Tree(1,400,8,100);'
            'val r:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));'
            'val a:doctree::NodeId=append(t,r,2,utf8("a"));'
            'assert(t.used_bytes()==257 && t.node_capacity(a)==129);'
            'rejected(t.try_append(r,3,utf8("0123456789012345")),4);'
            'assert(t.size()==2 && doctree::absent(t.next_sibling(a)));'
            'assert(!t.try_set_text(a,utf8("0123456789012345")));'
            'assert(t.text_size(a)==1 && t.text_byte(a,0)==byte(97) && t.used_bytes()==257);'
            'assert(t.try_set_text(a,utf8("012345678901234")));'
            'assert(t.used_bytes()==271 && t.node_capacity(a)==143 && t.text_size(a)==15);'
            'assert(t.try_set_text(a,utf8("")) && t.used_bytes()==271 && t.text_size(a)==0);'
            'assert(t.erase_subtree(a) && t.used_bytes()==128);'
            'val b:doctree::NodeId=append(t,r,3,utf8(""));'
            'assert(b.slot==a.slot && b.generation>a.generation && !t.contains(a));'
            'assert(t.erase_subtree(r) && t.size()==0 && t.used_bytes()==0 && doctree::absent(t.root()));'))

    def test_links_reparent_cycles_and_subtree_deletion(self):
        self.accepted(PREFIX + main(TREE +
            'val r:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));'
            'val a:doctree::NodeId=append(t,r,2,utf8(""));'
            'val b:doctree::NodeId=append(t,r,3,utf8(""));'
            'val c:doctree::NodeId=append(t,r,4,utf8(""));'
            'val d:doctree::NodeId=append(t,b,5,utf8(""));'
            'assert(!t.try_reparent(r,d) && !t.try_reparent(b,d) && !t.try_reparent(b,b));'
            'assert(eq(t.first_child(r),a) && eq(t.last_child(r),c));'
            'assert(t.try_reparent(b,r) && eq(t.next_sibling(a),b));'
            'assert(t.try_reparent(b,a));'
            'assert(eq(t.next_sibling(a),c) && eq(t.previous_sibling(c),a));'
            'assert(eq(t.parent(b),a) && eq(t.first_child(a),b) && eq(t.last_child(a),b));'
            'assert(t.erase_subtree(a));'
            'assert(!t.contains(a) && !t.contains(b) && !t.contains(d));'
            'assert(t.size()==2 && eq(t.first_child(r),c) && eq(t.last_child(r),c));'
            'assert(doctree::absent(t.previous_sibling(c)) && doctree::absent(t.next_sibling(c)));'
            'assert(!t.erase_subtree(a) && t.erase_subtree(c));'
            'assert(doctree::absent(t.first_child(r)) && doctree::absent(t.last_child(r)));'))

    def test_unicode_copy_validation_and_embedded_nul(self):
        body = TREE + 'val r:doctree::NodeId=append(t,' + EMPTY + ',9223372036854775807,' + data('Olá\0🙂') + ');'
        expected = 'Olá\0🙂'.encode()
        body += f'assert(t.kind(r)==9223372036854775807 && t.text_size(r)=={len(expected)});'
        for i, byte in enumerate(expected):
            body += f'assert(t.text_byte(r,{i})==byte({byte}));'
        for invalid in [[0x80], [0xC0, 0xAF], [0xED, 0xA0, 0x80], [0xF4, 0x90, 0x80, 0x80], [0xE2, 0x82]]:
            body += ('{own input:*byte=alloc<byte>(' + str(len(invalid)) + ');')
            body += ''.join(f'input[{i}]=byte({n});' for i, n in enumerate(invalid))
            body += ('rejected(t.try_append(r,2,slice_of(input,0,' + str(len(invalid)) + ')),6);'
                     'assert(!t.try_set_text(r,slice_of(input,0,' + str(len(invalid)) + ')));}')
        body += f'assert(t.size()==1 && t.used_bytes()=={128+len(expected)} && t.text_size(r)=={len(expected)});'
        body += 'assert(t.try_set_text(r,utf8("x")) && t.text_size(r)==1 && t.text_byte(r,0)==byte(120));'
        self.accepted(PREFIX + main(body))

    def test_ordered_tree_against_independent_dictionary_model(self):
        # The oracle stores Python parent/children lists and byte strings. It has
        # no packed fields, arena slots, linked siblings or free-list algorithm.
        rng = random.Random(20261103)
        live, stale, sequence, root = {}, [], 0, None
        body = TREE
        for step in range(180):
            used = sum(n['capacity'] for n in live.values())
            op = rng.choice(['append', 'append', 'text', 'move', 'erase']) if live else 'append'
            if op == 'append':
                parent = rng.choice(list(live)) if live else None
                value = rng.choice(['', 'ação', 'abc', '🙂', 'x' * 50])
                size = 128 + len(value.encode())
                if used + size > 4096:
                    body += f'rejected(t.try_append({parent or EMPTY},1,{data(value)}),4);'
                else:
                    name = f'n{sequence}'
                    sequence += 1
                    body += f'val {name}:doctree::NodeId=append(t,{parent or EMPTY},{step+1},{data(value)});'
                    live[name] = dict(parent=parent, children=[], value=value.encode(), capacity=size, kind=step+1)
                    if parent:
                        live[parent]['children'].append(name)
                    else:
                        root = name
            elif op == 'text':
                name = rng.choice(list(live))
                value = rng.choice(['', 'á', 'xyz', '🙂' * 8, 'z' * 120])
                size = 128 + len(value.encode())
                ok = size <= live[name]['capacity'] or used + size <= 4096
                body += f'assert(t.try_set_text({name},{data(value)})=={str(ok).lower()});'
                if ok:
                    live[name]['value'] = value.encode()
                    live[name]['capacity'] = max(live[name]['capacity'], size)
            elif op == 'move':
                name, parent = rng.choice(list(live)), rng.choice(list(live))
                ancestors, cursor = [], parent
                while cursor:
                    ancestors.append(cursor)
                    cursor = live[cursor]['parent']
                ok = name != root and name not in ancestors
                body += f'assert(t.try_reparent({name},{parent})=={str(ok).lower()});'
                if ok and live[name]['parent'] != parent:
                    live[live[name]['parent']]['children'].remove(name)
                    live[parent]['children'].append(name)
                    live[name]['parent'] = parent
            else:
                name = rng.choice(list(live))
                body += f'assert(t.erase_subtree({name}));'
                parent = live[name]['parent']
                if parent:
                    live[parent]['children'].remove(name)
                else:
                    root = None
                stack = [name]
                while stack:
                    removed = stack.pop()
                    stack.extend(live.pop(removed)['children'])
                    stale.append(removed)
            body += f'assert(t.size()=={len(live)} && t.used_bytes()=={sum(n["capacity"] for n in live.values())});'
            body += f'assert(eq(t.root(),{root or EMPTY}));'
            for name, record in live.items():
                children = record['children']
                siblings = live[record['parent']]['children'] if record['parent'] else [name]
                index = siblings.index(name)
                previous = siblings[index-1] if index else EMPTY
                following = siblings[index+1] if index+1 < len(siblings) else EMPTY
                body += (f'assert(t.contains({name}) && t.kind({name})=={record["kind"]} && '
                         f't.node_capacity({name})=={record["capacity"]} && t.text_size({name})=={len(record["value"])});'
                         f'assert(eq(t.parent({name}),{record["parent"] or EMPTY}) && '
                         f'eq(t.first_child({name}),{children[0] if children else EMPTY}) && '
                         f'eq(t.last_child({name}),{children[-1] if children else EMPTY}));'
                         f'assert(eq(t.previous_sibling({name}),{previous}) && eq(t.next_sibling({name}),{following}));')
                for i, byte in enumerate(record['value']):
                    body += f'assert(t.text_byte({name},{i})==byte({byte}));'
            for name in stale[-3:]:
                body += f'assert(!t.contains({name}));'
        self.accepted(PREFIX + main(body))

    def test_limits_stale_cross_document_retirement_and_reset(self):
        self.accepted(PREFIX + main(
            'own t:doctree::Tree=try_new doctree::Tree(1,128,1,2);'
            'rejected(t.try_append(' + EMPTY + ',0,utf8("")),5);'
            'val a:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));'
            'rejected(t.try_append(' + EMPTY + ',1,utf8("")),5);'
            'assert(t.erase_subtree(a));val b:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));'
            'assert(!t.contains(a) && b.slot==a.slot && b.generation==2 && t.erase_subtree(b));'
            'rejected(t.try_append(' + EMPTY + ',1,utf8("")),2);'
            'assert(t.slots_used()==1 && t.size()==0 && !t.reset(1) && t.reset(2));'
            'val c:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));'
            'assert(!t.contains(b) && !t.contains(new doctree::NodeId(2,-1,1)));'
            'assert(!t.contains(new doctree::NodeId(2,0,0)));'
            'own other:doctree::Tree=try_new doctree::Tree(3,256,2,10);'
            'val d:doctree::NodeId=append(other,' + EMPTY + ',1,utf8(""));'
            'assert(!other.contains(c) && !t.contains(d) && !t.try_reparent(c,d));'
            'assert(!t.try_set_text(a,utf8("x")));t.close();t.close();'
            'assert(!t.contains(c) && t.used_bytes()==0 && t.slots_used()==0);'
            'rejected(t.try_append(' + EMPTY + ',1,utf8("")),1);'
            'assert(t.reset(4) && doctree::absent(t.root()));'
            'own tiny:doctree::Tree=try_new doctree::Tree(5,127,1,10);'
            'rejected(tiny.try_append(' + EMPTY + ',1,utf8("")),4);'
            'own zero:doctree::Tree=try_new doctree::Tree(6,9223372036854775807,0,10);'
            'rejected(zero.try_append(' + EMPTY + ',1,utf8("")),2);'))

    def test_deep_tree_has_iterative_subtree_cleanup(self):
        self.accepted(PREFIX + main(
            'own t:doctree::Tree=try_new doctree::Tree(1,384000,3000,100);'
            'let parent:doctree::NodeId=' + EMPTY + ';'
            'for(let i:int=0;i<3000;i++){parent=append(t,parent,1,utf8(""));}'
            'assert(t.size()==3000 && t.used_bytes()==384000);'
            'assert(t.erase_subtree(t.root()) && t.size()==0 && t.used_bytes()==0);'))

    def test_os_refusal_rolls_back_and_keeps_neighbor(self):
        setup, drain, cleanup = preparation.exhaustion()
        self.fault_program(PREFIX + main(TREE +
            'val r:doctree::NodeId=append(t,' + EMPTY + ',1,utf8("root"));'
            'val a:doctree::NodeId=append(t,r,2,utf8("a"));'
            'val b:doctree::NodeId=append(t,r,3,utf8("b"));'
            'own other:doctree::Tree=try_new doctree::Tree(2,1024,8,100);'
            'val n:doctree::NodeId=append(other,' + EMPTY + ',4,utf8("ok"));'
            'val prepared:buffers::Preparation=t.prepare_nodes(4);'
            'match(prepared){Ready(n){assert(n==4);}Incomplete(c,n){assert(false);}}'
            'unsafe{' + setup + drain +
            'rejected(t.try_append(r,4,utf8("")),3);assert(!t.try_set_text(a,utf8("longer")));'
            'assert(t.size()==3 && t.used_bytes()==390 && eq(t.first_child(r),a) && eq(t.last_child(r),b));'
            'assert(t.text_size(a)==1 && t.text_byte(a,0)==byte(97));'
            'assert(other.contains(n) && other.text_size(n)==2 && other.text_byte(n,0)==byte(111));'
            'assert(t.try_reparent(b,a) && t.try_set_text(a,utf8("z")));'
            'assert(t.erase_subtree(a) && t.size()==1 && t.used_bytes()==132);'
            'own missing:doctree::Tree=try_new doctree::Tree(3,1024,4,8);assert(missing==null);'
            't.close();other.close();' + cleanup + '}'), '')

    def test_privacy_borrows_and_access_contracts(self):
        self.rejected(PREFIX + main(TREE + 'print(t.pool);'), 'privado')
        self.rejected(PREFIX + main(TREE + 'borrow view:doctree::Tree=t;t.close();'), 'borrow')
        self.rejected(PREFIX + main(TREE + 'borrow mut view:doctree::Tree=t;t.size();'), 'borrow')
        self.rejected(PREFIX + main(TREE + 't.init(2,128,1,1);'), 'inicializador')
        for body in [TREE + 't.parent(' + EMPTY + ');',
                     TREE + 'val r:doctree::NodeId=append(t,' + EMPTY + ',1,utf8(""));t.text_byte(r,0);',
                     'own t:doctree::Tree=try_new doctree::Tree(0,128,1,1);']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', self.source(PREFIX + main(body)), *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('R001', result.stderr)

    def test_example_ir_and_five_formats(self):
        example = base.ROOT / 'exemplos/41_document_tree_budget.assis'
        self.accepted(example.read_text(encoding='utf-8'), '3 393 4\n3 394 5\n1 128\n')
        result = self.invoke('ir', example)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', example, '--target', target, '-o', self.temp / target, *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

"""Storage accounting, independent models and whole-candidate rollback."""
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
PREFIX = '''import "std/documents.assis";
safe fn put(borrow mut d:documents::Document,p:doctree::NodeId,borrow input:slice<byte>):doctree::NodeId{
 val r:doctree::Append=d.try_append(p,1,input);
 match(r){Appended(id){return id;}Rejected(code){assert(false);return new doctree::NodeId();}}
}
safe fn create(borrow mut p:buffers::BufferPool,n:int):buffers::BufferId{
 val r:buffers::Creation=p.try_create(n);
 match(r){Created(id){return id;}Rejected(code){assert(false);return new buffers::BufferId();}}
}
safe fn reject(r:buffers::Creation,c:int):void{
 match(r){Created(id){assert(false);}Rejected(code){assert(c==code);}}
}'''
EMPTY = 'new doctree::NodeId()'


def metadata(slots):
    # Independent oracle: count the union of intervals covering contiguous leaves.
    # It does not model insertion paths, power-of-two tests or a free list.
    capacity = 1
    while capacity < slots:
        capacity *= 2

    def intervals(start, end):
        if start >= slots:
            return 0
        if end - start == 1:
            return 1
        middle = (start + end) // 2
        return 1 + intervals(start, middle) + intervals(middle, end)

    return 144 + 56 * slots + 32 * intervals(0, capacity)


class DocumentMemory(base.Evolution):
    fault_program = preparation.BufferPreallocation.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_metadata_admission_exact_limit_preparation_and_retirement(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,1000,16,1);'
            'assert(p.storage_bytes()==144 && !p.try_limit_storage(143));'
            'assert(p.try_limit_storage(232));reject(p.try_create(1),4);'
            'assert(p.storage_bytes()==144 && p.slots_used()==0);'
            'val a:buffers::BufferId=create(p,0);assert(p.storage_bytes()==232);'
            'assert(!p.try_limit_storage(1000));reject(p.try_create(0),4);'
            'assert(p.erase(a) && p.storage_bytes()==232 && !p.contains(a));'
            'reject(p.try_create(0),4);p.close();assert(p.storage_bytes()==144);'
            'assert(p.reset(2) && p.try_limit_storage(352));'
            'val ready:buffers::Preparation=p.prepare_slots(3);'
            'match(ready){Ready(n){assert(false);}Incomplete(c,n){assert(c==4 && n==2);}}'
            'assert(p.storage_bytes()==352 && p.size()==0);'
            'val b:buffers::BufferId=create(p,0);val c:buffers::BufferId=create(p,0);'
            'assert(p.storage_bytes()==352 && p.erase(b) && p.erase(c));'
            'assert(p.storage_bytes()==352);p.close();assert(p.storage_bytes()==144);'))

    def test_growth_counts_metadata_old_payload_and_entire_candidate(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,10000,8,100);'
            'assert(p.try_limit_storage(242));val a:buffers::BufferId=create(p,4);'
            'p.set(a,0,byte(42));assert(p.storage_bytes()==236);'
            'assert(!p.try_reserve(a,7) && p.capacity(a)==4 && p.storage_bytes()==236);'
            'assert(p.try_reserve(a,6) && p.storage_bytes()==238 && p.get(a,0)==byte(42));'
            'assert(p.release(a) && p.storage_bytes()==232);'
            'assert(p.try_resize(a,10) && p.storage_bytes()==242);'
            'assert(p.try_resize(a,0) && p.storage_bytes()==242);'
            'assert(p.erase(a) && p.storage_bytes()==232);'
            'val b:buffers::BufferId=create(p,10);assert(b.generation==2 && p.storage_bytes()==242);'))

    def test_accounting_against_interval_tree_and_bytearray_model(self):
        rng = random.Random(20261104)
        body = ('own p:buffers::BufferPool=try_new buffers::BufferPool(1,5000,80,10000);'
                'assert(p.try_limit_storage(5000));')
        live, spares, slots, sequence = {}, [], 0, 0
        for step in range(200):
            used = sum(len(v) for v in live.values())
            charge = metadata(slots) + used
            op = rng.choice(['create', 'create', 'grow', 'erase', 'prepare', 'close'])
            if op == 'create':
                size = rng.choice([0, 1, 13, 80, 211])
                new_slots = slots if spares else slots + 1
                ok = new_slots <= 80 and metadata(new_slots) + used + size <= 5000
                if ok:
                    name = f'h{sequence}'
                    sequence += 1
                    body += f'val {name}:buffers::BufferId=create(p,{size});'
                    live[name] = bytearray(size)
                    if spares:
                        spares.pop()
                    slots = new_slots
                else:
                    body += f'reject(p.try_create({size}),4);'
            elif op == 'grow' and live:
                name = rng.choice(list(live))
                size = rng.choice([0, 1, 32, 144, 333])
                old = len(live[name])
                ok = size <= old or charge + size <= 5000
                body += f'assert(p.try_reserve({name},{size})=={str(ok).lower()});'
                if ok and size > old:
                    live[name].extend(b'\0' * (size - old))
            elif op == 'erase' and live:
                name = rng.choice(list(live))
                live.pop(name)
                spares.append(name)
                body += f'assert(p.erase({name}) && !p.contains({name}));'
            elif op == 'prepare':
                wanted = rng.randrange(0, 15)
                while len(spares) < wanted and slots < 80 and metadata(slots + 1) + used <= 5000:
                    slots += 1
                    spares.append(None)
                body += f'{{val result:buffers::Preparation=p.prepare_slots({wanted});'
                if len(spares) >= wanted:
                    body += f'match(result){{Ready(n){{assert(n=={len(spares)});}}Incomplete(c,n){{assert(false);}}}}}}'
                else:
                    body += f'match(result){{Ready(n){{assert(false);}}Incomplete(c,n){{assert(c==4 && n=={len(spares)});}}}}}}'
            elif op == 'close':
                body += f'p.close();assert(p.storage_bytes()==144);assert(p.reset({step+2}));'
                live, spares, slots = {}, [], 0
            body += f'assert(p.storage_bytes()=={metadata(slots)+sum(len(v) for v in live.values())});'
            body += f'assert(p.size()=={len(live)} && p.ready_slots()=={len(spares)});'
            for name, value in live.items():
                body += f'assert(p.contains({name}) && p.capacity({name})=={len(value)});'
        self.accepted(PREFIX + main(body))

    def test_source_copy_utf8_exact_budget_and_tree_metadata(self):
        self.accepted(PREFIX + main(
            'own input:*byte=alloc<byte>(3);input[0]=byte(97);input[1]=byte(0);input[2]=byte(98);'
            'own d:documents::Document=try_new documents::Document(1,475,16,100,slice_of(input,0,3));'
            'assert(d!=null && d.is_open() && d.storage_bytes()==259);input[0]=byte(99);'
            'assert(d.source_size()==3 && d.source_byte(0)==byte(97) && d.source_byte(1)==byte(0));'
            'val root:doctree::NodeId=put(d,' + EMPTY + ',utf8(""));'
            'assert(d.storage_bytes()==475 && d.nodes().contains(root));'
            'val refused:doctree::Append=d.try_append(root,1,utf8(""));'
            'match(refused){Appended(id){assert(false);}Rejected(c){assert(c==4);}}'
            'assert(!d.try_set_text(root,utf8("x")) && d.storage_bytes()==475);'
            'assert(d.erase_subtree(root) && d.storage_bytes()==347);d.close();assert(d.storage_bytes()==64);'
            'assert(!d.is_open() && !d.has_root());'
            'own small:documents::Document=try_new documents::Document(2,255,1,1,utf8(""));'
            'assert(small!=null && !small.is_open() && small.storage_bytes()==64);'
            'input[0]=byte(128);own bad:documents::Document=try_new documents::Document(3,1000,1,1,slice_of(input,0,1));'
            'assert(bad!=null && !bad.is_open() && bad.storage_bytes()==64);'))

    def test_complete_candidate_abort_commit_and_stale_instances(self):
        example = base.ROOT / 'exemplos/42_document_candidate.assis'
        self.accepted(example.read_text(encoding='utf-8'), '3 1\n')
        self.accepted(PREFIX + main(
            'own s:documents::Store=try_new documents::Store(1400,8,100);'
            'assert(s.storage_bytes()==72 && s.begin(0,utf8(""))==5);'
            'assert(s.begin(1,utf8(""))==0 && !s.commit(1));'
            'assert(s.begin(2,utf8(""))==7 && !s.abort(2));'
            '{borrow mut d:documents::Document=s.candidate();put(d,' + EMPTY + ',utf8("old"));}'
            'assert(s.commit(1) && !s.has_candidate());'
            'val old:doctree::NodeId=s.active_document().nodes().root();val before:int=s.storage_bytes();'
            'assert(s.begin(1,utf8(""))==5 && s.begin(2,utf8("x"))==0);'
            '{borrow mut d:documents::Document=s.candidate();val h:doctree::NodeId=put(d,' + EMPTY + ',utf8("new"));'
            'assert(!d.nodes().contains(old));}'
            'assert(s.storage_bytes()<=1400 && s.active_document().nodes().contains(old));'
            'assert(!s.commit(1) && s.abort(2) && s.storage_bytes()==before);'
            'assert(s.begin(2,utf8(""))==5 && s.begin(3,utf8(""))==0);'
            '{borrow mut d:documents::Document=s.candidate();d.close();}'
            'assert(!s.commit(3) && s.abort(3) && s.storage_bytes()==before);'
            's.close();s.close();assert(s.storage_bytes()==72 && !s.is_open());'
            'assert(s.begin(4,utf8(""))==1 && !s.commit(1) && !s.abort(1));'))

    def test_active_candidate_combined_limit_and_invalid_source(self):
        self.accepted(PREFIX + main(
            'own s:documents::Store=try_new documents::Store(800,8,100);'
            'assert(s.begin(1,utf8(""))==0);'
            '{borrow mut d:documents::Document=s.candidate();put(d,' + EMPTY + ',utf8(""));}'
            'assert(s.commit(1) && s.storage_bytes()==544);'
            'assert(s.begin(2,utf8("x"))==4 && s.storage_bytes()==544 && !s.has_candidate());'
            'assert(s.begin(2,utf8(""))==0 && s.storage_bytes()==800);'
            '{borrow mut d:documents::Document=s.candidate();val r:doctree::Append=d.try_append(' + EMPTY + ',1,utf8(""));'
            'match(r){Appended(id){assert(false);}Rejected(c){assert(c==4);}}}'
            'assert(!s.commit(2) && s.abort(2) && s.storage_bytes()==544);'
            'own b:*byte=alloc<byte>(1);b[0]=byte(128);'
            'assert(s.begin(3,slice_of(b,0,1))==4);'  # size wins over UTF-8
            'own large:documents::Store=try_new documents::Store(10000,4,100);'
            'assert(large.begin(1,slice_of(b,0,1))==6 && large.storage_bytes()==72);'
            'assert(large.begin(9223372036854775807,utf8(""))==0 && large.abort(9223372036854775807));'
            'assert(large.begin(9223372036854775807,utf8(""))==5);'))

    def test_document_versions_against_independent_snapshot_model(self):
        rng = random.Random(20261105)
        current, pending, last, sequence = None, None, 0, 0
        body = 'own s:documents::Store=try_new documents::Store(2048,64,10000);'

        def charge(doc):
            return 0 if doc is None else 256 + len(doc['source']) + (88 + doc['capacity'] if doc['capacity'] else 0)

        for _ in range(180):
            op = rng.choice(['begin', 'root', 'text', 'commit', 'abort']) if pending else 'begin'
            if op == 'begin':
                sequence += 1
                source = 's' * rng.choice([0, 3, 40, 150, 1900])
                code = 7 if pending else 4 if 72 + charge(current) + 256 + len(source) > 2048 else 0
                body += f'assert(s.begin({sequence},utf8({json.dumps(source)}))=={code});'
                if code == 0:
                    last = sequence
                    pending = dict(instance=last, source=source.encode(), capacity=0, value=b'', id=None)
            elif op in ('root', 'text'):
                value = rng.choice(['', 'Olá', '🙂', 'x' * 200, 'y' * 1000])
                record = 128 + len(value.encode())
                delta = 88 + record if not pending['capacity'] else record if record > pending['capacity'] else 0
                ok = 72 + charge(current) + charge(pending) + delta <= 2048
                encoded = json.dumps(value, ensure_ascii=False)
                if not pending['capacity']:
                    name = f'root{sequence}'
                    if ok:
                        body += f'let {name}:doctree::NodeId=new doctree::NodeId();'
                        body += f'{{borrow mut d:documents::Document=s.candidate();{name}=put(d,{EMPTY},utf8({encoded}));}}'
                        pending['id'] = name
                    else:
                        body += f'{{borrow mut d:documents::Document=s.candidate();val r:doctree::Append=d.try_append({EMPTY},1,utf8({encoded}));'
                        body += 'match(r){Appended(id){assert(false);}Rejected(c){assert(c==4);}}}'
                else:
                    body += f'{{borrow mut d:documents::Document=s.candidate();assert(d.try_set_text({pending["id"]},utf8({encoded}))=={str(ok).lower()});}}'
                if ok:
                    pending['capacity'] = max(pending['capacity'], record)
                    pending['value'] = value.encode()
            elif op == 'commit':
                ok = bool(pending['capacity'])
                body += f'assert(s.commit({pending["instance"]})=={str(ok).lower()});'
                if ok:
                    current, pending = pending, None
            elif op == 'abort':
                body += f'assert(s.abort({pending["instance"]}));'
                pending = None
            body += (f'assert(s.storage_bytes()=={72+charge(current)+charge(pending)} && '
                     f's.has_active()=={str(current is not None).lower()} && s.has_candidate()=={str(pending is not None).lower()});')
            if current:
                body += f'assert(s.active_document().instance()=={current["instance"]} && s.active_document().source_size()=={len(current["source"])});'
                body += f'assert(s.active_document().nodes().text_size({current["id"]})=={len(current["value"])});'
                if current['value']:
                    for index in sorted({0, len(current['value']) // 2, len(current['value']) - 1}):
                        body += f'assert(s.active_document().nodes().text_byte({current["id"]},{index})==byte({current["value"][index]}));'
        self.accepted(PREFIX + main(body))

    def test_os_refusal_rolls_back_source_and_each_construction_stage(self):
        # Supplies for the 64/128/256-byte slab classes: refuse the Document,
        # Tree, BufferPool and OwnedArray in turn, then permit construction.
        stages = [({}, ''), ({1: 1}, ''), ({1: 2}, ''), ({1: 2, 2: 1}, ''),
                  ({0: 1, 1: 2, 2: 1}, ''), ({0: 4, 1: 4, 2: 4}, 'x' * 20000)]
        for supply, source in stages:
            with self.subTest(supply=supply, source_size=len(source)):
                setup, drain, cleanup = preparation.exhaustion()
                for index, count in supply.items():
                    drain += f'for(let i:int=0;i<{count} && n{index}>0;i++){{n{index}--;free(keep{index}[n{index}]);}}'
                body = ('own s:documents::Store=try_new documents::Store(100000,32,1000);'
                        'assert(s.begin(1,utf8("live"))==0);'
                        '{borrow mut d:documents::Document=s.candidate();put(d,' + EMPTY + ',utf8("old"));}'
                        'assert(s.commit(1));val old:doctree::NodeId=s.active_document().nodes().root();'
                        'val before:int=s.storage_bytes();'
                        'own neighbor:documents::Store=try_new documents::Store(100000,4,1000);'
                        'assert(neighbor.begin(100,utf8("neighbor"))==0);'
                        'unsafe{' + setup + drain +
                        'val result:int=s.begin(2,utf8(' + json.dumps(source) + '));')
                if supply != {0: 1, 1: 2, 2: 1} or source:
                    body += 'assert(result==3 && !s.has_candidate() && s.storage_bytes()==before);'
                else:
                    body += ('assert(result==0 && s.has_candidate());'
                             '{borrow mut d:documents::Document=s.candidate();val r:doctree::Append=d.try_append(' + EMPTY + ',1,utf8(""));'
                             'match(r){Appended(id){assert(false);}Rejected(c){assert(c==3);}}assert(d.storage_bytes()==256);}'
                             'assert(s.abort(2) && s.storage_bytes()==before);')
                body += ('assert(s.active_document().nodes().contains(old));'
                         'assert(s.active_document().source_size()==4 && neighbor.has_candidate());'
                         's.close();neighbor.close();assert(s.storage_bytes()==72);' + cleanup + '}')
                self.fault_program(PREFIX + main(body), '')

    def test_commit_abort_and_close_allocate_nothing_under_os_refusal(self):
        setup, drain, cleanup = preparation.exhaustion()
        self.fault_program(PREFIX + main(
            'own s:documents::Store=try_new documents::Store(100000,32,1000);'
            'assert(s.begin(1,utf8("first"))==0);'
            '{borrow mut d:documents::Document=s.candidate();put(d,' + EMPTY + ',utf8("old"));}'
            'assert(s.commit(1));val old:doctree::NodeId=s.active_document().nodes().root();'
            'assert(s.begin(2,utf8("second"))==0);'
            '{borrow mut d:documents::Document=s.candidate();put(d,' + EMPTY + ',utf8("new"));}'
            'own other:documents::Store=try_new documents::Store(10000,4,100);assert(other.begin(10,utf8("discard"))==0);'
            'unsafe{' + setup + drain +
            'assert(s.commit(2) && !s.active_document().nodes().contains(old));'
            'assert(s.active_document().instance()==2 && s.active_document().source_size()==6);'
            'assert(other.abort(10) && other.storage_bytes()==72);'
            's.close();other.close();' + cleanup + '}'), '')

    def test_private_storage_and_borrows_block_mutation_and_navigation(self):
        init = ('own s:documents::Store=try_new documents::Store(10000,8,100);'
                'assert(s.begin(1,utf8(""))==0);')
        self.rejected(PREFIX + main(init + 'borrow mut d:documents::Document=s.candidate();s.commit(1);'), 'borrow')
        self.rejected(PREFIX + main(init + 'borrow mut d:documents::Document=s.candidate();'
                                   'borrow view:doctree::Tree=d.nodes();d.close();'), 'borrow')
        self.rejected(PREFIX + main(init + 'print(s.pending);'), 'privado')
        self.rejected(PREFIX + main(init + 'borrow mut d:documents::Document=s.candidate();d.nodes().close();'), 'mut')
        self.rejected(PREFIX + main('own s:documents::Store=try_new documents::Store(72,1,1);s.init(72,1,1);'), 'inicializador')

    def test_invalid_constructor_and_access_contracts_trap(self):
        bodies = [
            'own s:documents::Store=try_new documents::Store(71,1,1);',
            'own s:documents::Store=try_new documents::Store(72,-1,1);',
            'own s:documents::Store=try_new documents::Store(72,1,0);',
            'own d:documents::Document=try_new documents::Document(0,1000,1,1,utf8(""));',
            'own s:documents::Store=try_new documents::Store(72,1,1);borrow mut d:documents::Document=s.candidate();',
            'own s:documents::Store=try_new documents::Store(72,1,1);borrow d:documents::Document=s.active_document();',
            'own d:documents::Document=try_new documents::Document(1,1000,1,1,utf8(""));d.source_byte(0);',
        ]
        for body in bodies:
            with self.subTest(body=body):
                file = self.source(PREFIX + main(body))
                for flags in [[], ['--no-opt']]:
                    result = self.invoke('run', file, '--debug', *flags)
                    self.assertEqual(result.returncode, 70, result.stderr)
                    self.assertIn('R001', result.stderr)

    def test_ir_allocation_layouts_and_all_five_formats(self):
        example = base.ROOT / 'exemplos/42_document_candidate.assis'
        for flags in [[], ['--no-opt']]:
            result = self.invoke('ir', example, *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            ir = json.loads(result.stdout)
            self.assertEqual(ir['astFallbacks'], 0)
            allocations = {v['type']: v['allocationBytes'] for v in ir['backendValues'] if 'allocationBytes' in v}
            # Actual allocation arguments selected by the emitter, independent
            # of the accounting constants in the AssisScript libraries.
            for name, size in [('buffers::Slot', 56), ('buffers::BufferPool', 112),
                               ('doctree::Tree', 48), ('documents::Document', 64), ('documents::Store', 72)]:
                self.assertEqual(allocations[name], size, (flags, name))
            arrays = [(n, s) for n, s in allocations.items() if 'OwnedArray' in n or 'ArrayNode' in n]
            self.assertTrue(arrays, allocations)
            self.assertTrue(all(s == 32 for n, s in arrays), arrays)
            for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
                result = self.invoke('build', example, '--target', target, '-o', self.temp / target, *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

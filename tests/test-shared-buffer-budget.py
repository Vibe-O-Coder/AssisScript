"""Shared payload limits: independent logical model, identities and OS refusal."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('slots', Path(__file__).with_name('test-fallible-slots.py'))
slots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slots)
base = slots.base
main = slots.main
PREFIX = '''import "std/buffers.assis";
safe fn create(borrow mut p:buffers::BufferPool,n:int):buffers::BufferId{
 val r:buffers::Creation=p.try_create(n);
 match(r){Created(h){return h;}Rejected(c){assert(false);return new buffers::BufferId();}}
}
safe fn rejected(r:buffers::Creation,code:int):void{
 match(r){Created(h){assert(false);}Rejected(c){assert(c==code);}}
}'''
POOL = 'own p:buffers::BufferPool=try_new buffers::BufferPool(1,64,512,100000);assert(p!=null && p.is_open());'


class SharedBufferBudget(base.Evolution):
    fault_program = slots.FallibleSlots.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_shared_and_transient_limits_and_return_of_quota(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,16,8,8);assert(p!=null && p.is_open());'
            'val a:buffers::BufferId=create(p,4);val b:buffers::BufferId=create(p,8);p.set(a,3,byte(42));'
            'assert(p.used_bytes()==12 && !p.try_reserve(a,8));rejected(p.try_create(5),4);'
            'assert(p.try_resize(b,0) && p.used_bytes()==12 && p.capacity(b)==8);'
            'assert(p.release(b) && p.release(b) && p.used_bytes()==4);'
            'assert(p.try_reserve(a,12) && p.used_bytes()==12 && p.byte_size(a)==4 && p.get(a,3)==byte(42));'
            'assert(!p.try_reserve(a,13) && p.capacity(a)==12);'
            'assert(p.try_resize(a,2) && p.try_resize(a,4) && p.get(a,3)==byte(0));'
            'assert(p.erase(a) && p.used_bytes()==0 && !p.erase(a));'
            'assert(p.try_resize(b,16) && p.used_bytes()==16);p.close();p.close();assert(p.used_bytes()==0);'))

    def test_zero_limits_negative_extreme_and_exact_boundaries(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,0,1,8);'
            'val h:buffers::BufferId=create(p,0);assert(p.used_bytes()==0 && p.capacity(h)==0);'
            'assert(p.try_reserve(h,0) && !p.try_resize(h,1));rejected(p.try_create(0),2);'
            'rejected(p.try_create(-1),4);rejected(p.try_create(9223372036854775807),4);'
            'assert(!p.try_resize(h,-1) && !p.try_reserve(h,9223372036854775807));'
            'assert(p.erase(h));p.close();rejected(p.try_create(0),1);'
            'own empty:buffers::BufferPool=try_new buffers::BufferPool(2,32,0,8);rejected(empty.try_create(0),2);'
            'own huge:buffers::BufferPool=try_new buffers::BufferPool(3,9223372036854775807,2,8);'
            'rejected(huge.try_create(9223372036854775807),3);assert(huge.used_bytes()==0 && huge.slots_used()==0);'))

    def test_stale_forged_cross_instance_reset_and_closed_ids(self):
        body = POOL + 'val h:buffers::BufferId=create(p,8);p.set(h,0,byte(42));'
        for forged in ['new buffers::BufferId()', 'new buffers::BufferId(2,h.slot,h.generation)',
                       'new buffers::BufferId(1,-1,1)', 'new buffers::BufferId(1,9223372036854775807,1)',
                       'new buffers::BufferId(1,h.slot,0)', 'new buffers::BufferId(1,h.slot,-1)',
                       'new buffers::BufferId(1,h.slot,9223372036854775807)']:
            body += ('{val bad:buffers::BufferId=' + forged + ';assert(!p.contains(bad) && !p.erase(bad) && '
                     '!p.release(bad) && !p.try_resize(bad,0) && !p.try_reserve(bad,0));}')
        body += ('assert(p.used_bytes()==8 && p.get(h,0)==byte(42) && p.erase(h));'
                 'val next:buffers::BufferId=create(p,8);assert(next.slot==h.slot && next.generation>h.generation);'
                 'assert(!p.contains(h) && !p.reset(1) && p.contains(next));assert(p.reset(2));'
                 'val fresh:buffers::BufferId=create(p,1);assert(!p.contains(next) && fresh.instance==2);'
                 'p.close();assert(!p.contains(fresh));rejected(p.try_create(0),1);assert(p.reset(3));')
        self.accepted(PREFIX + main(body))

    def test_retirement_and_ten_thousand_recycles(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,8,1,2);'
            'val h:buffers::BufferId=create(p,4);assert(p.erase(h));'
            'val next:buffers::BufferId=create(p,8);assert(next.generation==2 && p.erase(next));'
            'rejected(p.try_create(0),2);assert(p.slots_used()==1 && p.used_bytes()==0);'
            'assert(p.reset(2));val fresh:buffers::BufferId=create(p,0);assert(fresh.generation==1);'))
        self.accepted(PREFIX + main(POOL +
            'for(let i:int=0;i<10000;i++){val h:buffers::BufferId=create(p,8);'
            'assert(h.slot==0 && h.generation==i+1 && p.used_bytes()==8 && p.erase(h));'
            'assert(!p.contains(h) && p.used_bytes()==0);}assert(p.slots_used()==1 && p.size()==0);'))

    def test_operations_against_independent_bytearray_model(self):
        rng = random.Random(20261101)
        live, stale, body, sequence, instance = {}, [], POOL, 0, 1
        for step in range(260):
            used = sum(capacity for data, capacity in live.values())
            operation = rng.choice(['create', 'create', 'resize', 'reserve', 'set', 'release', 'erase', 'reset']) if live else 'create'
            if operation == 'create':
                size = rng.choice([0, 1, 3, 8, 13, 31, 65, -1])
                if 0 <= size <= 64 - used:
                    name = f'h{sequence}'
                    sequence += 1
                    live[name] = (bytearray(size), size)
                    body += f'val {name}:buffers::BufferId=create(p,{size});'
                else:
                    body += f'rejected(p.try_create({size}),4);'
            elif operation == 'reset':
                instance += 1
                stale.extend(live)
                live.clear()
                body += f'assert(p.reset({instance}));'
            else:
                name = rng.choice(list(live))
                data, capacity = live[name]
                if operation in ('reserve', 'resize'):
                    size = rng.choice([-1, 0, 1, 4, 17, 33, 64, 65, 9223372036854775807])
                    success = size >= 0 and (size <= capacity or used + size <= 64)
                    body += f'assert({"" if success else "!"}p.try_{operation}({name},{size}));'
                    if success:
                        if operation == 'resize':
                            data = data[:size] + bytearray(max(0, size - len(data)))
                        live[name] = (data, max(capacity, size))
                elif operation == 'set' and data:
                    index, value = rng.randrange(len(data)), rng.randrange(256)
                    data[index] = value
                    body += f'p.set({name},{index},byte({value}));'
                elif operation == 'release':
                    live[name] = (bytearray(), 0)
                    body += f'assert(p.release({name}));'
                elif operation == 'erase':
                    del live[name]
                    stale.append(name)
                    body += f'assert(p.erase({name}));'
            body += f'assert(p.size()=={len(live)} && p.used_bytes()=={sum(c for d, c in live.values())});'
            for name, (data, capacity) in live.items():
                body += f'assert(p.contains({name}) && p.byte_size({name})=={len(data)} && p.capacity({name})=={capacity});'
                for index, value in enumerate(data):
                    body += f'assert(p.get({name},{index})==byte({value}));'
            if stale:
                body += f'assert(!p.erase({rng.choice(stale)}));'
        self.accepted(PREFIX + main(body))

    def test_private_storage_and_borrow_conflicts_are_rejected(self):
        for field in ['used', 'limit', 'slots', 'free_head']:
            self.rejected(PREFIX + main(POOL + f'print(p.{field});'), 'privado')
        self.rejected(PREFIX + main(POOL + 'borrow view:buffers::BufferPool=p;p.try_create(0);'), 'borrow')
        self.rejected(PREFIX + main(POOL + 'borrow mut view:buffers::BufferPool=p;p.used_bytes();'), 'borrow')

    def test_invalid_access_and_constructor_contracts_trap(self):
        for call in ['p.get(h,0);', 'p.set(h,-1,byte(0));', 'p.byte_size(new buffers::BufferId());',
                     'p.capacity(new buffers::BufferId());']:
            source = self.source(PREFIX + main(POOL + 'val h:buffers::BufferId=create(p,0);' + call))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, '--debug', *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('R001', result.stderr)
        for args in ['0,8,1,8', '1,-1,1,8', '1,8,-1,8', '1,8,1,0']:
            source = self.source(PREFIX + main(f'own p:buffers::BufferPool=try_new buffers::BufferPool({args});'))
            result = self.invoke('run', source, '--debug')
            self.assertEqual(result.returncode, 70, result.stderr)

    def test_os_refusal_preserves_quota_data_slots_and_neighbour(self):
        # Exhaust every cached small class; the OS fixture denies new slabs.
        sizes = [1, 33, 97, 225, 481, 993, 2017, 4065, 8161, 16353]
        setup, drain, cleanup = '', '', ''
        for i, size in enumerate(sizes):
            setup += f'let keep{i}:**byte=alloc<*byte>(8193);let n{i}:int=0;'
            drain += f'while(true){{let v:*byte=try_alloc<byte>({size});if(v==null){{break;}}keep{i}[n{i}]=v;n{i}++;assert(n{i}<8193);}}'
            cleanup += f'for(let i:int=0;i<n{i};i++){{free(keep{i}[i]);}}free(keep{i});'
        self.fault_program(PREFIX + main(POOL +
            'val h:buffers::BufferId=create(p,4);p.set(h,3,byte(42));'
            'own neighbour:buffers::BufferPool=try_new buffers::BufferPool(2,64,4,8);'
            'val other:buffers::BufferId=create(neighbour,8);neighbour.set(other,0,byte(7));'
            'unsafe{' + setup + 'FAULT_ENABLE' + drain +
            'assert(!p.try_reserve(h,8) && p.capacity(h)==4 && p.used_bytes()==4 && p.get(h,3)==byte(42));'
            'rejected(p.try_create(1),3);rejected(p.try_create(0),3);'
            'assert(p.size()==1 && p.slots_used()==1 && p.used_bytes()==4);'
            'own failed:buffers::BufferPool=try_new buffers::BufferPool(3,8,1,8);assert(failed==null);'
            'assert(p.release(h) && p.used_bytes()==0 && p.erase(h));'
            'val reused:buffers::BufferId=create(p,0);assert(reused.generation==2 && p.erase(reused));'
            'assert(neighbour.used_bytes()==8 && neighbour.get(other,0)==byte(7));'
            'p.close();neighbour.close();FAULT_CHECK' + cleanup + '}'), '')

    def test_controller_metadata_refusal_is_explicit_and_allocation_free(self):
        # try_new reserves the controller BEFORE evaluating its arguments. The
        # argument below drains caches and denies slabs before init allocates
        # the index controller. All retained raw blocks belong to this child.
        drain, cleanup = '', ''
        for i, size in enumerate([1, 33, 97, 225, 481, 993, 2017, 4065, 8161, 16353]):
            drain += f'while(true){{let v:*byte=try_alloc<byte>({size});if(v==null){{break;}}'
            drain += f'assert(counts[{i}]<8193);keep[{i}*8193+counts[{i}]]=v;counts[{i}]+=1;}}'
            cleanup += f'for(let i:int=0;i<counts[{i}];i++){{free(keep[{i}*8193+i]);}}'
        helper = ('fn deny(keep:**byte,counts:*int):int{unsafe{FAULT_ENABLE' + drain + '}return 64;}')
        self.fault_program(PREFIX + helper + main('unsafe{'
            'let keep:**byte=alloc<*byte>(81930);let counts:*int=alloc<int>(10);'
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,deny(keep,counts),8,8);'
            'assert(p!=null && !p.is_open() && p.size()==0 && p.used_bytes()==0 && p.slots_used()==0);'
            'rejected(p.try_create(0),1);assert(!p.reset(2));p.close();p.close();FAULT_CHECK'
            + cleanup + 'free(keep);free(counts);}'), '')

    def test_partial_metadata_reservations_roll_back_before_publication(self):
        sizes = [1, 33, 97, 225, 481, 993, 2017, 4065, 8161, 16353]
        for allowance in range(5):
            setup, drain, restore, cleanup = '', '', '', ''
            for i, size in enumerate(sizes):
                setup += f'let keep{i}:**byte=alloc<*byte>(8193);let n{i}:int=0;'
                drain += f'while(true){{let v:*byte=try_alloc<byte>({size});if(v==null){{break;}}keep{i}[n{i}]=v;n{i}++;assert(n{i}<8193);}}'
                restore += f'for(let i:int=0;i<{allowance} && n{i}>0;i++){{n{i}--;free(keep{i}[n{i}]);}}'
                cleanup += f'for(let i:int=0;i<n{i};i++){{free(keep{i}[i]);}}free(keep{i});'
            self.fault_program(PREFIX + main(POOL +
                'val h:buffers::BufferId=create(p,4);p.set(h,0,byte(42));unsafe{'
                + setup + 'FAULT_ENABLE' + drain + restore +
                'let success:bool=false;val r:buffers::Creation=p.try_create(1);'
                'match(r){Created(id){success=true;assert(p.size()==2 && p.used_bytes()==5 && p.byte_size(id)==1);'
                'assert(p.get(id,0)==byte(0) && p.erase(id));}'
                'Rejected(code){assert(code==3 && p.size()==1 && p.used_bytes()==4 && p.slots_used()==1);}}'
                + ('assert(!success);' if allowance == 0 else 'assert(success);' if allowance == 4 else '') +
                'assert(p.contains(h) && p.get(h,0)==byte(42) && p.used_bytes()==4);'
                'p.close();FAULT_CHECK' + cleanup + '}'), '')

    def test_example_ir_and_all_five_formats(self):
        example = base.ROOT / 'exemplos/39_shared_buffer_budget.assis'
        self.accepted(example.read_text(encoding='utf-8'), '8 42\n0 1\n')
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

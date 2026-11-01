"""Prepared metadata: logical inventory model and allocation-free consumption."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('budget', Path(__file__).with_name('test-shared-buffer-budget.py'))
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)
base = budget.base
main = budget.main
PREFIX = budget.PREFIX + '''
safe fn prepared(r:buffers::Preparation,n:int):void{
 match(r){Ready(ready){assert(ready==n);}Incomplete(code,ready){assert(false);}}
}
safe fn incomplete(r:buffers::Preparation,c:int,n:int):void{
 match(r){Ready(ready){assert(false);}Incomplete(code,ready){assert(code==c && ready==n);}}
}'''


def exhaustion(allowance=0):
    # Denial is installed before draining cached blocks. Even if it malfunctions,
    # these ten loops retain at most 2048 * 32426 = 66,408,448 payload bytes,
    # plus ten 16 KiB ledgers. There is no system-OOM stress loop.
    setup, drain, restore, cleanup = '', '', '', ''
    for i, size in enumerate([1, 33, 97, 225, 481, 993, 2017, 4065, 8161, 16353]):
        # Supply must not depend on which classes library controllers happened
        # to warm. Their layouts can legitimately move to another slab class.
        setup += f'{{let warm:*byte=alloc<byte>({size});free(warm);}}'
        setup += f'let keep{i}:**byte=alloc<*byte>(2048);let n{i}:int=0;'
        drain += (f'for(let attempt:int=0;attempt<2048;attempt++){{'
                  f'let v:*byte=try_alloc<byte>({size});if(v==null){{break;}}'
                  f'keep{i}[n{i}]=v;n{i}++;}}assert(n{i}<2048);')
        restore += f'for(let i:int=0;i<{allowance} && n{i}>0;i++){{n{i}--;free(keep{i}[n{i}]);}}'
        cleanup += f'for(let i:int=0;i<n{i};i++){{free(keep{i}[i]);}}free(keep{i});'
    return setup, 'FAULT_ENABLE' + drain + restore, 'FAULT_CHECK' + cleanup


class BufferPreallocation(base.Evolution):
    fault_program = budget.slots.FallibleSlots.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_inventory_limits_and_lifecycle(self):
        self.accepted(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,16,4,2);'
            'prepared(p.prepare_slots(0),0);prepared(p.prepare_slots(3),3);'
            'assert(p.size()==0 && p.used_bytes()==0 && p.slots_used()==3 && p.ready_slots()==3);'
            'assert(!p.contains(new buffers::BufferId(1,0,1)));'
            'val a:buffers::BufferId=create(p,4);val b:buffers::BufferId=create(p,0);'
            'assert(p.ready_slots()==1);prepared(p.prepare_slots(1),1);'
            'incomplete(p.prepare_slots(-1),4,1);incomplete(p.prepare_slots(9223372036854775807),4,1);'
            'incomplete(p.prepare_slots(4),2,2);assert(p.slots_used()==4 && p.used_bytes()==4);'
            'assert(p.release(a) && p.ready_slots()==2 && p.erase(a) && p.ready_slots()==3);'
            'val c:buffers::BufferId=create(p,0);assert(c.slot==a.slot && c.generation==2);'
            'assert(p.erase(c) && p.ready_slots()==2);incomplete(p.prepare_slots(3),2,2);'
            'assert(p.contains(b));p.close();assert(p.ready_slots()==0 && p.slots_used()==0);'
            'incomplete(p.prepare_slots(-1),1,0);assert(p.reset(2));prepared(p.prepare_slots(4),4);'
            'assert(!p.contains(b) && p.size()==0 && p.used_bytes()==0);'))

    def test_ready_inventory_against_independent_resource_model(self):
        # Logical inventory only: no model of tree shape, slot indices or free-list order.
        rng = random.Random(20261102)
        body = 'own p:buffers::BufferPool=try_new buffers::BufferPool(1,0,23,10000);'
        live, reserved, sequence, instance = [], 0, 0, 1
        for _ in range(220):
            op = rng.choice(['prepare', 'prepare', 'create', 'erase', 'reset'])
            if op == 'prepare':
                count = rng.choice([-1, 0, 1, 7, 16, 23, 24])
                ready = reserved - len(live)
                if count < 0 or count > 23:
                    body += f'incomplete(p.prepare_slots({count}),4,{ready});'
                else:
                    reserved = max(reserved, min(23, len(live) + count))
                    ready = reserved - len(live)
                    if ready >= count:
                        body += f'prepared(p.prepare_slots({count}),{ready});'
                    else:
                        body += f'incomplete(p.prepare_slots({count}),2,{ready});'
            elif op == 'create':
                if len(live) < 23:
                    reserved = max(reserved, len(live) + 1)
                    name = f'h{sequence}'
                    sequence += 1
                    body += f'val {name}:buffers::BufferId=create(p,0);'
                    live.append(name)
                else:
                    body += 'rejected(p.try_create(0),2);'
            elif op == 'erase' and live:
                name = live.pop(rng.randrange(len(live)))
                body += f'assert(p.erase({name}) && !p.contains({name}));'
            elif op == 'reset':
                instance += 1
                body += f'assert(p.reset({instance}));'
                for name in live:
                    body += f'assert(!p.contains({name}));'
                live, reserved = [], 0
            body += (f'assert(p.size()=={len(live)} && p.slots_used()=={reserved} && '
                     f'p.ready_slots()=={reserved-len(live)} && p.used_bytes()==0);')
            for name in live:
                body += f'assert(p.contains({name}));'
        self.accepted(PREFIX + main(body))

    def test_prepared_slots_are_consumed_and_recycled_under_os_refusal(self):
        setup, drain, cleanup = exhaustion()
        self.fault_program(PREFIX + main(
            'own p:buffers::BufferPool=try_new buffers::BufferPool(1,64,64,100);'
            'val h:buffers::BufferId=create(p,4);p.set(h,3,byte(42));prepared(p.prepare_slots(16),16);'
            'own neighbour:buffers::BufferPool=try_new buffers::BufferPool(2,64,4,8);'
            'val other:buffers::BufferId=create(neighbour,8);neighbour.set(other,0,byte(7));'
            'own ids:*buffers::BufferId=alloc<buffers::BufferId>(16);unsafe{' + setup + drain +
            'incomplete(p.prepare_slots(32),3,16);rejected(p.try_create(1),3);'
            'assert(p.size()==1 && p.slots_used()==17 && p.ready_slots()==16 && p.used_bytes()==4);'
            'for(let i:int=0;i<16;i++){ids[i]=create(p,0);}assert(p.ready_slots()==0);'
            'rejected(p.try_create(0),3);'
            'for(let i:int=0;i<16;i++){assert(p.erase(ids[i]));}'
            'prepared(p.prepare_slots(16),16);'
            'for(let i:int=0;i<16;i++){val fresh:buffers::BufferId=create(p,0);'
            'assert(!p.contains(ids[i]) && p.erase(fresh));}'
            'assert(p.contains(h) && p.get(h,3)==byte(42) && p.used_bytes()==4);'
            'assert(neighbour.contains(other) && neighbour.get(other,0)==byte(7));'
            'p.close();neighbour.close();' + cleanup + '}'), '')

    def test_partial_os_refusal_retains_exactly_reported_spares(self):
        for allowance in [0, 1, 3, 8]:
            setup, drain, cleanup = exhaustion(allowance)
            self.fault_program(PREFIX + main(
                'own p:buffers::BufferPool=try_new buffers::BufferPool(1,0,64,100);unsafe{' + setup + drain +
                'val result:buffers::Preparation=p.prepare_slots(64);'
                'let ready:int=0;match(result){Ready(n){assert(false);}'
                'Incomplete(code,n){assert(code==3);ready=n;}}'
                'assert(ready>=0 && ready<64 && p.ready_slots()==ready && p.slots_used()==ready);'
                + ('assert(ready==0);' if allowance == 0 else 'assert(ready>0);') +
                'assert(p.size()==0 && p.used_bytes()==0);'
                'for(let i:int=0;i<ready;i++){val id:buffers::BufferId=create(p,0);assert(p.contains(id));}'
                'assert(p.ready_slots()==0 && p.size()==ready);p.close();' + cleanup + '}'), '')

    def test_borrow_conflicts_and_private_inventory_are_rejected(self):
        init = 'own p:buffers::BufferPool=try_new buffers::BufferPool(1,0,4,8);'
        self.rejected(PREFIX + main(init + 'borrow view:buffers::BufferPool=p;p.prepare_slots(1);'), 'borrow')
        self.rejected(PREFIX + main(init + 'borrow mut view:buffers::BufferPool=p;p.ready_slots();'), 'borrow')
        self.rejected(PREFIX + main(init + 'print(p.ready);'), 'privado')

    def test_example_ir_and_five_output_formats(self):
        example = base.ROOT / 'exemplos/40_prepared_buffer_slots.assis'
        self.accepted(example.read_text(encoding='utf-8'), '0 4\n1 3 4\n0 4\n')
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

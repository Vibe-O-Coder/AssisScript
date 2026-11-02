"""Experimental ASV1 against independent arithmetic and authority/lifetime cases."""
import importlib.util
import random
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('vm_base', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PREFIX = 'import "std/pagevm.assis";\n'

def instruction(op, a=0, b=0, c=0, immediate=0):
    return struct.pack('<BBBBi', op, a, b, c, immediate)

def program(ops, entry=0, memory=0):
    return b'ASV1' + struct.pack('<III', len(ops), entry, memory) + b''.join(ops)

def load(data, name='v', instance=1, origin=7, generation=1, memory=65536, frames=16, fuel=10000, calls=100):
    return ('own ' + name + '_data:*byte=try_alloc<byte>(' + str(len(data)) + ');' +
        ''.join(f'{name}_data[{i}]=byte({b});' for i, b in enumerate(data)) +
        f'own {name}:pagevm::Instance=try_new pagevm::Instance({instance},{origin},{generation},'
        f'slice_of({name}_data,0,len({name}_data)),{memory},{frames},{fuel},{calls});assert({name}!=null);')

def wrapped(value):
    return (value + 2**63) % 2**64 - 2**63

class PageVM(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def execute(self, body, expected=''):
        self.accepted(PREFIX + 'safe fn main():int{' + body + 'return 0;}', expected)

    def test_integer_boolean_division_and_overflow_against_expression_model(self):
        rng = random.Random(170001)
        ops = [instruction(1, i, immediate=rng.randrange(-2**31, 2**31)) for i in range(16)]
        values = [struct.unpack('<i', op[4:])[0] for op in ops]
        for _ in range(160):
            op = rng.randrange(2, 8)
            a, b, c = (rng.randrange(16) for _ in range(3))
            left, right = values[b], values[c]
            if op == 5 and right == 0:
                op = 2
            if op == 2:value = left + right
            elif op == 3:value = left - right
            elif op == 4:value = left * right
            elif op == 5:value = (abs(left)//abs(right)) * (-1 if (left<0)!=(right<0) else 1)
            elif op == 6:value = int(left == right)
            else:value = int(left < right)
            values[a] = wrapped(value)
            ops.append(instruction(op, a, b, c))
        # Each final register is observed independently, including signed values.
        body = ''
        for i, value in enumerate(values):
            body += '{' + load(program(ops + [instruction(0, i)]))
            body += f'assert(v.status()==0 && v.run(1000)==2);print(v.result());}}'
        self.execute(body, ''.join(str(n)+'\n' for n in values))

    def test_calls_isolate_registers_order_effects_and_copy_code(self):
        ops = [instruction(1,0,immediate=6),instruction(10,1,0,immediate=5),
            instruction(12,2,1,immediate=1),instruction(2,3,0,2),instruction(0,3),
            instruction(1,1,immediate=7),instruction(4,0,0,1),instruction(11,0)]
        self.execute(load(program(ops)) +
            'assert(v.grant_counter(1,7,1));v_data[16]=byte(255);'
            'assert(v.run(3)==1 && v.status()==0 && v.host_calls()==0);'
            'assert(v.run(10)==2 && v.result()==48 && v.counter()==42 && v.host_calls()==1);'
            'assert(v.run(10)==2 && v.steps()==8);')

    def test_fuel_yield_recursion_cancel_and_neighbor(self):
        loop=program([instruction(8,immediate=0)])
        recursive=program([instruction(10,immediate=0)])
        self.execute(load(loop,fuel=11)+load(program([instruction(1,immediate=42),instruction(0)]),'neighbor',instance=2)+
            'assert(v.run(4)==1 && v.steps()==4);assert(v.run(4)==1 && v.steps()==8);'
            'assert(v.run(4)== -3 && v.steps()==11 && v.run(1)== -3);'
            'assert(neighbor.run(4)==2 && neighbor.result()==42);'
            '{'+load(recursive,frames=3)+'assert(v.run(100)== -6 && v.steps()==3);}'
            '{'+load(loop)+'assert(v.run(1)==1);v.revoke();assert(v.run(100)== -2 && !v.grant_counter(1,7,1));v.close();assert(v.run(1)== -9);}')

    def test_capability_default_deny_origin_instance_generation_revocation_and_call_limit(self):
        ops=[instruction(1,immediate=3),instruction(12,1,0,immediate=1),instruction(12,2,0,immediate=1),instruction(0,2)]
        self.execute('{'+load(program(ops))+'assert(v.run(100)== -2 && v.counter()==0);}'
            '{'+load(program(ops),calls=1)+
            'assert(!v.grant_counter(2,7,1) && !v.grant_counter(1,8,1) && !v.grant_counter(1,7,2));'
            'assert(v.grant_counter(1,7,1));assert(v.run(100)== -8 && v.counter()==3 && v.host_calls()==1);}'
            '{'+load(program(ops))+'assert(v.grant_counter(1,7,1));assert(v.run(1)==1);v.revoke();assert(v.run(100)== -2 && v.counter()==0);}')

    def test_memory_bounds_zero_initialization_and_modular_store(self):
        ops=[instruction(1,0,immediate=1),instruction(1,1,immediate=511),instruction(14,0,1),instruction(13,2,0),instruction(0,2)]
        self.execute(load(program(ops,memory=2))+'assert(v.run(100)==2 && v.result()==255);'
            '{'+load(program([instruction(13,1,0),instruction(0,1)],memory=1))+'assert(v.run(100)==2 && v.result()==0);}'
            '{'+load(program(ops,memory=1))+'assert(v.run(100)== -5);}'
            '{'+load(program([instruction(1,immediate=-1),instruction(13,1,0)],memory=1))+'assert(v.run(100)== -5);}')

    def test_division_trap_fallthrough_and_bounded_host_argument(self):
        self.execute('{'+load(program([instruction(5,0,1,2)]))+'assert(v.run(10)== -7);}'
            '{'+load(program([instruction(1,immediate=1)]))+'assert(v.run(10)== -5);}'
            '{'+load(program([instruction(1,immediate=1000001),instruction(12,1,0,immediate=1)]))+
            'assert(v.grant_counter(1,7,1));assert(v.run(10)== -10 && v.counter()==0 && v.host_calls()==0);}')

    def test_minimum_division_preserves_native_modular_contract(self):
        ops=[instruction(1,0,immediate=-2147483648),instruction(4,0,0,0),
             instruction(1,1,immediate=-2),instruction(4,0,0,1),
             instruction(1,1,immediate=-1),instruction(5,2,0,1),instruction(0,2)]
        self.execute(load(program(ops))+'assert(v.run(10)==2 && v.result()== -9223372036854775808);')

    def test_five_target_formats_and_native_execution(self):
        import os
        import subprocess
        code=PREFIX+'safe fn main():int{'+load(program([instruction(1,immediate=42),instruction(0)]))+'assert(v.run(10)==2 && v.result()==42);return 0;}'
        source=self.source(code)
        for flags in ([],['--no-opt']):
            for target in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):
                output=self.temp/(target+'.exe')
                built=self.invoke('build',source,'--target',target,'-o',output,*flags)
                self.assertEqual(built.returncode,0,built.stderr)
                data=output.read_bytes()
                if target.startswith('linux'):
                    self.assertEqual(data[:6],b'\x7fELF\x02\x01')
                    self.assertEqual(struct.unpack_from('<H',data,18)[0],183 if target.endswith('arm64') else 62)
                elif target.startswith('macos'):
                    self.assertEqual(struct.unpack_from('<II',data),(0xfeedfacf,0x0100000c if target.endswith('arm64') else 0x01000007))
                else:
                    self.assertEqual(data[:2],b'MZ');pe=struct.unpack_from('<I',data,0x3c)[0]
                    self.assertEqual(struct.unpack_from('<H',data,pe+4)[0],0x8664)
                if target==('windows-x64' if os.name=='nt' else 'linux-x64'):
                    result=subprocess.run([output],capture_output=True,timeout=20)
                    self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_malformed_unknown_import_register_branch_size_and_limits_fail_before_run(self):
        valid=program([instruction(0)])
        bad=[b'',valid[:15],b'ASV2'+valid[4:],valid+b'\0',program([instruction(255)]),
            program([instruction(0,16)]),program([instruction(0,b=1)]),
            program([instruction(8,immediate=1)]),program([instruction(8,immediate=-1)]),
            program([instruction(12,immediate=2)]),program([instruction(12,c=1,immediate=1)]),
            program([instruction(1,b=1)]),program([instruction(2,c=16)]),
            program([instruction(0)],entry=1),program([instruction(0)],memory=65537)]
        rng=random.Random(20261101)
        bad += [bytes(rng.randrange(256) for _ in range(rng.randrange(0,40))) for _ in range(50)]
        self.execute(''.join('{'+load(data)+'assert(v.status()== -1 && v.run(10)== -1 && v.steps()==0);}' for data in bad)+
            '{'+load(valid,instance=0)+'assert(v.status()== -1);}'
            '{'+load(valid,frames=0)+'assert(v.status()== -1);}'
            '{'+load(valid,fuel=0)+'assert(v.status()== -1);}')

    def test_oom_constructor_and_instance_boundaries_preserve_other_state(self):
        parser_spec=importlib.util.spec_from_file_location('vm_parser',Path(__file__).with_name('test-htdl-parser.py'))
        parser=importlib.util.module_from_spec(parser_spec);parser_spec.loader.exec_module(parser)
        warm,drain,cleanup=parser.preparation.exhaustion()
        data=program([instruction(0)])
        # Reserve the source before fault injection; only VM construction fails.
        before=load(data,'neighbor',instance=2)
        fault=load(data)
        start=fault.index('own v:pagevm::Instance')
        body=before+fault[:start]+'unsafe{'+warm+drain+fault[start:].replace('assert(v!=null);','')
        body+='assert(v==null || v.status()== -4);assert(neighbor.run(1)==2);'+cleanup+'}'
        parser.preparation.BufferPreallocation.fault_program(self,PREFIX+'safe fn main():int{'+body+'return 0;}','')

if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)

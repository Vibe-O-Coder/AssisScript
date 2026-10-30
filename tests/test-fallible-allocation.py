"""Recoverable managed buffers: independent models, real OOM and ownership.

Linux additionally denies mmap selectively in the child with seccomp. This
does not change the compiler/runtime under test or add a production test hook.
"""
import ctypes
import importlib.util
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


def deny_pool_maps():
    # Linux x86_64 seccomp_data: nr at 0; args[1] (mmap length) at 24.
    # Deny only 64 KiB allocator slabs; permit initialization and large maps.
    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                    ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]

    class Program(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]

    code = (Filter * 6)(Filter(0x20, 0, 0, 0), Filter(0x15, 0, 3, 9),
                        Filter(0x20, 0, 0, 24), Filter(0x15, 0, 1, 65536),
                        Filter(0x06, 0, 0, 0x0005000c), Filter(0x06, 0, 0, 0x7fff0000))
    program = Program(len(code), code)
    libc = ctypes.CDLL(None, use_errno=True)
    # no_new_privs; filter inherited across exec of our static ELF test binary.
    if libc.prctl(38, 1, 0, 0, 0) or libc.prctl(22, 2, ctypes.byref(program), 0, 0):
        raise OSError(ctypes.get_errno(), 'seccomp failure injection unavailable')


class FallibleAllocation(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_typed_sizes_zero_initialization_and_zero_length(self):
        body = ''
        for ty in ['byte', 'i8', 'u16', 'i32', 'u64', 'f32', 'f64', 'bool']:
            zero = 'false' if ty == 'bool' else f'{ty}(0)'
            body += ('{own data:*' + ty + '=try_alloc<' + ty + '>(17);'
                     'assert(data!=null && len(data)==17);'
                     'for(let i:int=0;i<17;i++){assert(data[i]==' + zero + ');}}')
        self.accepted('value struct Pair{let a:int;let b:int;}' + main(body +
            'own pairs:*Pair=try_alloc<Pair>(3);assert(pairs!=null && len(pairs)==3);'
            'assert(pairs[2].a==0 && pairs[2].b==0);'
            'own empty:*int=try_alloc<int>(0);assert(empty!=null && len(empty)==0);'
            'assert(len(slice_of(empty,0,0))==0);'))

    def test_negative_unsigned_and_byte_size_overflow_return_null(self):
        body = ''
        for ty in ['byte', 'u16', 'u32', 'int']:
            for count in ['-1', '-9223372036854775807-1', '9223372036854775807',
                          'u64(0xffffffffffffffff)', 'u64(0x8000000000000000)']:
                body += '{own p:*' + ty + '=try_alloc<' + ty + '>(' + count + ');assert(p==null);}'
        # Header overflow must also be rejected when element multiplication fits.
        body += 'own p:*byte=try_alloc<byte>(9223372036854775776);assert(p==null);'
        self.accepted(main(body))

    def test_all_size_classes_reuse_zero_and_cleanup(self):
        body = ''
        for size in [0, 1, 32, 33, 96, 97, 224, 225, 480, 481, 992, 993,
                     2016, 2017, 4064, 4065, 8160, 8161, 16352, 16353, 32736, 32737, 65537]:
            body += ('for(let n:int=0;n<3;n++){own p:*byte=try_alloc<byte>(' + str(size) + ');'
                     'assert(p!=null && len(p)==' + str(size) + ');'
                     'for(let i:int=0;i<len(p);i++){assert(p[i]==byte(0));p[i]=byte(255);}}')
        self.accepted(main(body))

    def test_evaluation_once_generic_returns_and_move(self):
        self.accepted('safe fn next(borrow mut p:*int):int{p[0]+=1;return p[0];}'
            'safe fn create<T>(n:int):own *T{return try_alloc<T>(n);}' + main(
            'own count:*int=alloc<int>(1);'
            'own data:*u16=try_alloc<u16>(next(count));assert(count[0]==1 && len(data)==1);'
            'own other:*u16=create::<u16>(4);other[3]=u16(42);'
            'own moved:*u16=move(other);print(moved[3]);'), '42\n')

    def test_existing_alloc_still_traps_on_invalid_size(self):
        for body, message in [
            ('own p:*byte=alloc<byte>(-1);', 'tamanho de alocação inválido'),
            ('own p:*int=alloc<int>(9223372036854775807);', 'tamanho de alocação inválido'),
            ('own p:*byte=alloc<byte>(0x1fff_ffff_ffff_ffff);', 'memória insuficiente')]:
            source = self.source(main(body))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn(message, result.stderr)

    def test_ownership_effects_and_diagnostics(self):
        for text, message in [
            (main('let p:*byte=try_alloc<byte>(4);'), 'own'),
            ('pure fn bad():int{own p:*byte=try_alloc<byte>(4);return 0;}' + main(''), 'pure'),
            (main('own p:*byte=try_alloc<byte>(1.5);'), 'inteira'),
            (main('own p:*byte=try_alloc<byte>();'), 'um argumento'),
            (main('own p:*byte=try_alloc<byte>(1,2);'), 'um argumento'),
            (main('own p:*byte=try_alloc<byte>(2);borrow q:*byte=p;free(p);'), 'borrow ativo'),
        ]:
            self.rejected(text, message)
        self.rejected('import "std/memory.assis";' + main(
            'own b:ByteBuffer=new ByteBuffer(10);print(b.data);'), 'privado')
        self.rejected('import "std/memory.assis";' + main(
            'own b:ByteBuffer=new ByteBuffer(10);b.init(1);'), 'só pode ser chamado')

    def test_bounded_buffer_against_independent_python_model(self):
        rng = random.Random(20261029)
        limit, capacity, model = 127, 0, bytearray()
        body = 'own b:ByteBuffer=new ByteBuffer(127);'
        output = ''
        for _ in range(220):
            op = rng.choice(['reserve', 'resize', 'resize', 'clear', 'release', 'set'])
            n = rng.randrange(-2, 150)
            if op in ('reserve', 'resize'):
                success = n >= 0 and (n <= capacity or n + capacity <= limit)
                body += f'print(b.try_{op}({n}));'
                output += str(success).lower() + '\n'
                if success:
                    capacity = max(capacity, n)
                    if op == 'resize':
                        model = model[:n] + bytearray(max(0, n - len(model)))
            elif op == 'clear':
                body += 'b.clear();'
                model.clear()
            elif op == 'release':
                body += 'b.release();'
                model.clear()
                capacity = 0
            elif model:
                index, value = rng.randrange(len(model)), rng.randrange(256)
                body += f'b.set({index},byte({value}));'
                model[index] = value
            body += 'print(b.size(),b.capacity());for(let i:int=0;i<b.size();i++){print(int(b.get(i)));}'
            output += f'{len(model)} {capacity}\n' + ''.join(f'{byte}\n' for byte in model)
        self.accepted('import "std/memory.assis";' + main(body), output)

    def test_quota_peak_boundary_and_independent_instances(self):
        self.accepted('import "std/memory.assis";' + main(
            'own a:ByteBuffer=new ByteBuffer(12);own b:ByteBuffer=new ByteBuffer(0);'
            'assert(a.try_resize(4));a.set(3,byte(42));'
            'assert(!a.try_reserve(9));assert(a.size()==4 && a.capacity()==4 && a.get(3)==byte(42));'
            'assert(a.try_reserve(8));assert(a.get(3)==byte(42));'
            'assert(b.try_resize(0) && !b.try_resize(1));'
            'a.release();assert(a.try_resize(12));assert(a.get(3)==byte(0));'
            'assert(a.try_resize(3));assert(a.try_resize(9));assert(a.get(8)==byte(0));'
            'assert(a.max_bytes()==12 && b.max_bytes()==0);'))

    def test_os_denial_preserves_old_data_and_neighbor(self):
        # Valid 2 EiB request exceeds the virtual address space of these targets.
        # No huge allocation is touched or relied on for a successful result.
        self.accepted('import "std/memory.assis";' + main(
            'own a:ByteBuffer=new ByteBuffer(9223372036854775775);'
            'own b:ByteBuffer=new ByteBuffer(32);'
            'assert(a.try_resize(8));a.set(7,byte(91));'
            'assert(!a.try_reserve(0x1fff_ffff_ffff_ffff));'
            'assert(a.size()==8 && a.capacity()==8 && a.get(7)==byte(91));'
            'assert(b.try_resize(16));b.set(15,byte(42));'
            'assert(a.try_resize(16));assert(a.get(7)==byte(91) && b.get(15)==byte(42));'))

    if sys.platform == 'linux' and platform.machine().lower() in ('x86_64', 'amd64'):
        def test_injected_pool_mapping_failures_and_large_neighbor(self):
            body = 'own neighbor:*byte=try_alloc<byte>(65537);assert(neighbor!=null);neighbor[0]=byte(42);'
            for size in [1, 33, 97, 225, 481, 993, 2017, 4065, 8161, 16353]:
                body += '{own p:*byte=try_alloc<byte>(' + str(size) + ');assert(p==null);}'
            body += 'assert(neighbor[0]==byte(42));print("recovered");'
            source = self.source(main(body))
            for flags in [[], ['--no-opt']]:
                binary = self.temp / 'injected'
                built = self.invoke('build', source, '--debug', '-o', binary, *flags)
                self.assertEqual(built.returncode, 0, built.stderr)
                result = subprocess.run([str(binary)], preexec_fn=deny_pool_maps,
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, 'recovered\n', ''))

    def test_failure_and_index_contracts_trap_only_on_invalid_access(self):
        for body in ['own p:*int=try_alloc<int>(-1);print(len(p));',
                     'own p:*int=try_alloc<int>(-1);print(p[0]);',
                     'own b:ByteBuffer=new ByteBuffer(10);print(b.get(0));',
                     'own b:ByteBuffer=new ByteBuffer(10);assert(b.try_resize(2));b.set(2,byte(1));',
                     'own b:ByteBuffer=new ByteBuffer(-1);']:
            source = self.source('import "std/memory.assis";' + main(body))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('assis: erro', result.stderr)

    def test_ir_all_targets_and_example(self):
        source = self.source('import "std/memory.assis";' + main(
            'own b:ByteBuffer=new ByteBuffer(16);assert(b.try_resize(8));'
            'own p:*int=try_alloc<int>(9223372036854775807);assert(p==null);'))
        ir = self.invoke('ir', source)
        self.assertEqual(ir.returncode, 0, ir.stderr)
        self.assertEqual(json.loads(ir.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                result = self.invoke('build', source, '--target', target, '-o', self.temp / target, *flags)
                self.assertEqual(result.returncode, 0, (target, result.stderr))
        self.accepted((base.ROOT / 'exemplos/36_fallible_buffers.assis').read_text(encoding='utf-8'),
                      '32 64 42\n64 0\n')


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

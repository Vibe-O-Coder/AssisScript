"""Statement-only increment/decrement: typing, borrowing, evaluation and targets."""
import importlib.util
import json
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


class Increment(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir', 'tokens') and '--legacy' not in args:
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_prefix_postfix_and_for_continue(self):
        self.accepted(main('let x:int=4;x++;print(x);++x;print(x);x--;print(x);--x;print(x);'
            'let sum:int=0;for(let i:int=0;i<6;i++){if(i==2){continue;}sum+=i;}'
            'for(let i:int=3;i>0;--i){sum+=i;}print(sum);'), '5\n6\n5\n4\n19\n')

    def test_all_integer_widths_wrap_in_both_directions(self):
        body = ''
        for ty, lo, hi in [('i8', -128, 127), ('i16', -32768, 32767),
                           ('i32', -2147483648, 2147483647), ('int', -9223372036854775808, 9223372036854775807),
                           ('i64', -9223372036854775808, 9223372036854775807), ('byte', 0, 255),
                           ('u8', 0, 255), ('u16', 0, 65535), ('u32', 0, 4294967295),
                           ('u64', 0, '0xffffffffffffffff')]:
            body += ('{let n:' + ty + '=' + ty + '(' + str(hi) + ');n++;'
                     'assert(n==' + ty + '(' + str(lo) + '));--n;assert(n==' + ty + '(' + str(hi) + '));}')
        self.accepted(main(body))

    def test_floating_point_and_generic_specializations(self):
        self.accepted('pure fn next<T>(x:T):T{let n:T=x;++n;return n;}' + main(
            'let a:f32=f32(1.5);a++;assert(a==f32(2.5));--a;assert(a==f32(1.5));'
            'let b:f64=-1.5;b--;assert(b== -2.5);++b;assert(b== -1.5);'
            'assert(next::<i16>(i16(41))==i16(42));assert(next::<f64>(41.0)==42.0);'))

    def test_integer_sequences_against_python_model(self):
        rng = random.Random(20261029)
        body, expected = '', []
        for ty, bits, signed in [('i8', 8, True), ('u8', 8, False),
                                 ('i16', 16, True), ('u16', 16, False),
                                 ('i32', 32, True), ('u32', 32, False),
                                 ('i64', 64, True), ('u64', 64, False)]:
            mask = (1 << bits) - 1
            value = (1 << (bits - int(signed))) - 1
            body += '{let n:' + ty + '=' + ty + '(0x' + format(value, 'x') + ');'
            for step in [1, 1, -1, -1] + [rng.choice([-1, 1]) for _ in range(28)]:
                op = '++' if step == 1 else '--'
                body += (op + 'n' if rng.choice([False, True]) else 'n' + op) + ';print(n);'
                value = (value + step) & mask
                expected.append(str(value - (1 << bits) if signed and value >= (1 << (bits - 1)) else value))
            body += '}'
        self.accepted(main(body), '\n'.join(expected) + '\n')

    def test_float_special_values_preserve_ieee_contract(self):
        self.accepted(main('let z:f64=0.0;let n:f64=z/z;n++;--n;assert(n!=n);'
            'let inf:f64=1.0/z;inf++;--inf;assert(inf>1.0 && inf==inf);'
            'let rounded:f32=f32(16777216.0);rounded++;assert(rounded==f32(16777216.0));'))

    def test_index_and_receiver_evaluated_once(self):
        self.accepted('safe fn index(borrow mut count:*int):int{count[0]+=1;return 0;}'
            'class C{let n:int;fn add(borrow mut self):void{++self.n;self.n--;self.n++;}}' + main(
            'own count:*int=alloc<int>(1);own data:*i16=alloc<i16>(1);data[0]=i16(8);'
            'data[index(count)]++;--data[index(count)];assert(count[0]==2 && data[0]==i16(8));'
            'own c:C=new C();c.add();assert(c.n==1);'
            'own values:Array<int>=[8];values[index(count)]++;assert(values[0]==9 && count[0]==3);'))

    def test_immutable_and_non_numeric_targets_are_rejected(self):
        for body, message in [
            ('val n:int=1;n++;', 'imutável'),
            ('let n:bool=false;n++;', 'posição numérica'),
            ('own n:*int=alloc<int>(1);n++;', 'posição numérica'),
            ('let n:int=1;(n+1)++;', 'posição gravável'),
            ('own a:*int=alloc<int>(1);borrow s:slice<int>=slice_of(a,0,1);s[0]++;', 'exclusivo'),
        ]:
            with self.subTest(body=body):
                self.rejected(main(body), message)
        self.rejected('const N:int=1;' + main('N++;'), 'posição gravável')
        self.rejected('pure fn bad(n:int):int{n++;return n;}' + main(''), 'imutável')

    def test_borrow_conflicts_and_private_members_are_rejected(self):
        self.rejected(main('own a:*int=alloc<int>(1);borrow view:slice<int>=slice_of(a,0,1);a[0]++;'), 'borrow')
        self.rejected('class C{private let n:int;}' + main('own c:C=new C();c.n++;'), 'privado')
        self.rejected('class C{let n:int;fn bad(borrow self):void{self.n++;}}' + main(''), 'exclusivo')

    def test_updates_do_not_produce_expression_values(self):
        for body in ['let n:int=1;print(++n);', 'let n:int=1;print(--n);',
                     'let n:int=1;let x:int=++n;', 'let n:int=1;print(n++);',
                     'let n:int=1;n++++;', 'let n:int=1;++n++;',
                     'let n:int=1;n++ + 2;', 'for(let n:int=0;n<2;print(n)){}']:
            source = self.source(main(body))
            for flags in [[], ['--no-opt']]:
                r = self.invoke('check', source, '--diagnostics=json', *flags)
                self.assertEqual(r.returncode, 1, body)
                self.assertEqual(json.loads(r.stderr)['code'], 'A001')
        self.accepted(main('let n:int=4;print(+ +n,- -n);'), '4 4\n')

    def test_typed_ir_and_every_output_target(self):
        source = self.source(main('own a:*int=alloc<int>(1);for(let i:int=0;i<3;++i){a[0]++;}print(a[0]);'))
        r = self.invoke('ir', source)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['astFallbacks'], 0)
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                binary = self.temp / (target + ('-reference' if flags else '') + '.exe')
                r = self.invoke('build', source, '--target', target, '-o', binary, *flags)
                self.assertEqual(r.returncode, 0, (target, flags, r.stderr))
                self.assertTrue(binary.is_file())


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)

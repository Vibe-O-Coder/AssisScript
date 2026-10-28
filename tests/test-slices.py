"""Borrowed fat descriptors: bounds, lifetime, ABI and alias regressions."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
main = base.main


class Slices(base.Evolution):
    def test_mutable_nested_slice_and_empty_end(self):
        self.accepted('safe ' + main('own b:*int=alloc<int>(4);b[1]=40;'
            '{borrow mut s:slice<int>=slice_of(b,1,2);s[0]+=2;'
            '{borrow t:slice<int>=slice_of(s,0,1);print(len(t),t[0]);}}'
            'borrow z:slice<int>=slice_of(b,4,0);print(len(z),b[1]);'), '1 42\n0 42\n')

    def test_returned_generic_and_indirect_borrow(self):
        prefix = 'safe fn sub<T>(borrow b:slice<T>):borrow(b) slice<T>{return slice_of(b,1,len(b)-1);}'
        prefix += 'safe fn view(borrow b:*int):borrow(b) slice<int>{return slice_of(b,0,len(b));}'
        self.accepted(prefix + 'safe ' + main('own b:*int=alloc<int>(3);b[2]=42;'
            'val f:safe fn(borrow *int):borrow(0) slice<int>=view;'
            'borrow a:slice<int>=f(b);borrow c:slice<int>=sub::<int>(a);print(len(c),c[1]);'), '2 42\n')

    def test_copy_elements_and_narrow_widths(self):
        self.accepted('value struct V{let n:int;let f:f64;}' + 'safe ' + main(
            'own b:*V=alloc<V>(2);b[1]=new V(42,1.5);borrow s:slice<V>=slice_of(b,1,1);print(s[0].n,s[0].f);'
            'own w:*u16=alloc<u16>(3);w[2]=u16(65535);borrow q:slice<u16>=slice_of(w,2,1);print(int(q[0]));'),
            '42 0x1.8000000000000p+0\n65535\n')

    def test_lifetime_and_exclusivity_rejections(self):
        for body, message in [
            ('own b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);free(b);', 'borrow ativo'),
            ('own b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);s[0]=1;', 'exclusivo'),
            ('own b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);borrow mut t:slice<int>=slice_of(s,0,1);', 'compartilhada'),
            ('own b:*int=alloc<int>(2);borrow mut s:slice<int>=slice_of(b,0,1);print(b[0]);', 'borrow incompatível'),
            ('own b:*int=alloc<int>(2);let s:slice<int>=slice_of(b,0,1);', 'vínculo borrow'),
            ('let b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);', 'gerenciado'),
            ('own b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);print(s==s);', 'comparação'),
        ]:
            with self.subTest(body=body): self.rejected(main(body), message)
        self.rejected('fn bad(borrow b:*int):borrow(b) slice<int>{own local:*int=alloc<int>(1);return slice_of(local,0,1);}' + main(''), 'não pode escapar')
        self.rejected('struct Bad{let s:slice<int>;}' + main(''), 'contrato de vida')
        self.rejected('fn bad(s:slice<int>):int{return len(s);}' + main(''), 'parâmetro borrow')

    def test_bounds_at_creation_and_index(self):
        for operation in ['slice_of(b,-1,0)', 'slice_of(b,0,-1)', 'slice_of(b,3,0)', 'slice_of(b,1,2)', 'slice_of(b,0,9223372036854775807)']:
            source = self.source('safe ' + main(f'own b:*int=alloc<int>(2);borrow s:slice<int>={operation};'))
            for flags in [[], ['--no-opt']]:
                r = self.invoke('run', source, *flags)
                self.assertEqual(r.returncode,70,r.stderr)
                self.assertIn('limite',r.stderr)
        for index in ['-1', '1']:
            r = self.invoke('run', self.source('safe ' + main(f'own b:*int=alloc<int>(2);borrow s:slice<int>=slice_of(b,0,1);print(s[{index}]);')))
            self.assertEqual(r.returncode,70,r.stderr)


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'): delattr(base.Evolution,name)
    unittest.main(verbosity=2)

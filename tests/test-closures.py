"""Explicit closure captures, affine environments and lexical borrowing."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


class Closures(base.Evolution):
    def invoke(self, *args, input=None):
        return subprocess.run([str(base.COMPILER), *map(str, args)], input=input,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_value_capture_is_a_snapshot(self):
        self.accepted(main('let x:int=40;own f:closure(int):int=closure[val x:int=x](v:int):int{return x+v;};'
                           'x=100;print(f(2),x);'), '42 100\n')

    def test_owned_capture_and_mutable_receiver(self):
        self.accepted(main('own b:*int=alloc<int>(1);b[0]=40;'
                           'own f:closure mut(int):int=closure mut[own b:*int=move(b)](x:int):int{b[0]+=x;return b[0];};'
                           'print(f(1),f(1));'), '41 42\n')

    def test_copy_record_and_function_capture(self):
        code = 'value struct P{let a:int;let b:int;}pure fn twice(x:int):int{return x*2;}'
        self.accepted(code + main('own f:closure():int=closure[val p:P=new P(20,1),val f:pure fn(int):int=twice]():int{return f(p.a+p.b);};print(f());'), '42\n')

    def test_shared_borrow_capture_and_end_of_scope(self):
        self.accepted(main('own b:*int=alloc<int>(1);b[0]=42;{'
                           'own f:closure():int=closure[borrow a:*int=b]():int{return a[0];};'
                           'print(f());}b[0]=7;print(b[0]);'), '42\n7\n')

    def test_borrowed_callback_parameter(self):
        code = 'safe fn apply(borrow f:closure(int):int,x:int):int{return f(x);}'
        self.accepted(code + main('own a:*int=alloc<int>(1);a[0]=40;'
                           'own f:closure(int):int=closure[borrow b:*int=a](v:int):int{return b[0]+v;};print(apply(f,2));'), '42\n')

    def test_owned_return_move_and_nested_environments(self):
        code = 'safe fn make(x:int):own closure(int):int{return closure[val k:int=x](v:int):int{return k+v;};}'
        self.accepted(code + main('own f:closure(int):int=make(40);'
                           'own g:closure(int):int=closure[own f:closure(int):int=move(f)](v:int):int{return f(v);};'
                           'own h:closure(int):int=move(g);print(h(2));'), '42\n')
        self.accepted('struct Box{own f:closure(int):int;}' + main(
                      'own box:Box=new Box(closure[val k:int=40](x:int):int{return x+k;});print(box.f(2));'), '42\n')
        self.accepted('import "std/owned.assis";\n' + main(
                      'own list:owned::OwnedList<closure(int):int>=new owned::OwnedList<closure(int):int>();'
                      'list.push_front(closure[val k:int=40](x:int):int{return x+k;});'
                      '{borrow f:closure(int):int=list.get(0);print(f(2));}'
                      'own f:closure(int):int=list.pop_front();print(f(3));'), '42\n43\n')

    def test_generic_closure_factory(self):
        code = 'safe fn constant<T>(v:T):own closure():T{return closure[val v:T=v]():T{return v;};}'
        self.accepted(code + main('own a:closure():int=constant::<int>(42);'
                           'own b:closure():bool=constant::<bool>(true);print(a(),b());'), '42 true\n')

    def test_inline_return_abi_and_argument_order(self):
        code = 'value struct P{let x:int;let y:int;}'
        self.accepted(code + main('own f:closure(P,int):P=closure[val k:int=2](p:P,v:int):P{return new P(p.x+k,p.y+v);};'
                           'val p:P=f(new P(20,1),19);print(p.x+p.y);'), '42\n')

    def test_borrowed_slice_capture(self):
        self.accepted(main('own b:*int=alloc<int>(3);b[1]=42;borrow s:slice<int>=slice_of(b,1,2);'
                           'own f:closure():int=closure[borrow s:slice<int>=s]():int{return s[0];};print(f());'), '42\n')

    def test_borrow_return_lifetime_is_tied_to_environment(self):
        self.accepted(main('own f:closure():borrow(self) *int=closure[own b:*int=alloc<int>(2)]():borrow(self) *int{return b;};'
                           'borrow b:*int=f();print(len(b));'), '2\n')

    def test_standard_library_pipeline_and_owned_results(self):
        text = (base.ROOT / 'exemplos/30_closures_and_owned_results.assis').read_text(encoding='utf-8')
        self.accepted(text, '42\n5\n')
        self.accepted('import "std/errors.assis";\n' + main('own o:OwnedOption<*int>=new OwnedOption<*int>.None();print(owned_option_is_some::<*int>(o));'
                      'own f:closure(own *int):own *int=closure[](own v:*int):own *int{return move(v);};'
                      'own e:OwnedResult<*int,int>=owned_result_map::<*int,*int,int>(new OwnedResult<*int,int>.Err(7),f);'
                      'match(e){Ok(v){print(len(v));}Err(code){print(code);}}'), 'false\n7\n')

    def test_capture_destruction_order_and_single_drop(self):
        code = 'final class R{let id:int;fn init(borrow mut self,id:int):void{self.id=id;}fn drop(borrow mut self):void{print(self.id);}}'
        self.accepted(code + main('{own f:closure():int=closure[own a:R=new R(1),own b:R=new R(2)]():int{return 0;};'
                      'own g:closure():int=move(f);print(g());}'), '0\n2\n1\n')

    def test_mutable_call_requires_exclusive_access(self):
        code = 'safe fn apply(borrow mut f:closure mut():int):int{return f();}'
        self.accepted(code + main('own f:closure mut():int=closure mut[own b:*int=alloc<int>(1)]():int{b[0]+=1;return b[0];};print(apply(f),apply(f));'), '1 2\n')
        self.rejected(main('own f:closure mut():int=closure mut[]():int{return 1;};borrow g:closure mut():int=f;print(g());'), 'borrow mut incompatível')
        self.rejected(main('own b:*int=alloc<int>(1);own f:closure mut():int=closure mut[borrow b:*int=b]():int{b[0]=1;return b[0];};'), 'exclusivo')
        self.rejected(main('own f:closure():borrow(self) *int=closure[own b:*int=alloc<int>(2)]():borrow(self) *int{return b;};borrow b:*int=f();free(f);'), 'borrow ativo')

    def test_reject_escaped_borrow_and_active_loans(self):
        cases = [
            ('own b:*int=alloc<int>(1);own f:closure():int=closure[borrow b:*int=b]():int{return b[0];};own g:closure():int=move(f);', 'captura borrow'),
            ('own b:*int=alloc<int>(1);own f:closure():int=closure[borrow b:*int=b]():int{return b[0];};free(b);', 'borrow ativo'),
            ('own b:*int=alloc<int>(1);own f:closure():int=closure[borrow b:*int=b]():int{return b[0];};b[0]=1;', 'exclusivo'),
            ('own b:*int=alloc<int>(1);own f:closure():int=closure[own b:*int=move(b)]():int{return b[0];};free(b);', 'movido'),
        ]
        for body, message in cases:
            with self.subTest(body=body):
                self.rejected(main(body), message)
        self.rejected('safe fn bad():own closure():int{own b:*int=alloc<int>(1);return closure[borrow b:*int=b]():int{return b[0];};}' + main(''), 'captura borrow')
        self.rejected(main('own b:*int=alloc<int>(1);own f:closure():int=closure[own inner:closure():int=closure[borrow b:*int=b]():int{return b[0];}]():int{return inner();};'), 'captura borrow')

    def test_reject_implicit_copies_mutation_and_unsafe_callbacks(self):
        for body, message in [
            ('own f:closure():int=closure[]():int{return 1;};own g:closure():int=f;', 'own exige'),
            ('own f:closure():int=closure[val x:int=1]():int{x=2;return x;};', 'gravável'),
            ('own f:closure():int=closure[own b:*int=alloc<int>(1)]():int{b[0]=1;return b[0];};', 'exclusivo'),
            ('own f:closure mut():int=closure mut[borrow b:*int=alloc<int>(1)]():int{return 1;};', 'borrow exige'),
            ('own f:closure():int=closure[]():int{return 1;};val g:safe fn():int=f;', 'não é possível usar'),
            ('own f:closure():int=closure[]():int{return legacy();};', 'chamada legada'),
        ]:
            with self.subTest(body=body):
                self.rejected('fn legacy():int{return 0;}' + main(body), message)
        self.rejected(main('own f:closure mut():own *int=closure mut[own b:*int=alloc<int>(1)]():own *int{return move(b);};'), 'captura de closure')


if __name__ == '__main__':
    suite = unittest.TestSuite(Closures(name) for name in Closures.__dict__ if name.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())

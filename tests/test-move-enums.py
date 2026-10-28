"""Affine sum types: active drops, borrowing, extraction and control flow."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


OPTION = 'enum O<T>{None;Some(own T);}'


class MoveEnums(base.Evolution):
    def invoke(self, *args, input=None):
        return subprocess.run([str(base.COMPILER), *map(str, args)], input=input,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_borrow_then_consume(self):
        self.accepted(OPTION + main('own b:*int=alloc<int>(1);b[0]=42;own o:O<*int>=new O<*int>.Some(move(b));'
                      'match(o){None{}Some(v){print(v[0]);}}'
                      'match(move(o)){None{}Some(v){v[0]+=1;print(v[0]);}}'), '42\n43\n')

    def test_active_variant_only_and_nested_drop(self):
        self.accepted('enum E{A(own *int);B(int,own *byte);C;}'
                      'enum N{Nested(own E);Empty;}' + main(
                      'own n:N=new N.Nested(new E.B(99,alloc<byte>(256)));'
                      'own e:E=new E.C();own a:E=new E.A(alloc<int>(32));'), '')

    def test_generic_return_and_consuming_parameter(self):
        code = OPTION + 'safe fn wrap<T>(own v:T):own O<T>{return new O<T>.Some(move(v));}'
        code += 'safe fn read(own o:O<*int>):int{match(move(o)){None{return 0;}Some(v){return v[0];}}}'
        self.accepted(code + main('own b:*int=alloc<int>(1);b[0]=42;print(read(wrap::<*int>(move(b))));'), '42\n')

    def test_move_payload_out_and_cleanup_on_return(self):
        code = OPTION + 'safe fn unwrap(own o:O<*int>):own *int{'
        code += 'match(move(o)){None{return alloc<int>(1);}Some(v){return move(v);}}}'
        self.accepted(code + main('own o:O<*int>=new O<*int>.Some(alloc<int>(2));'
                      'own b:*int=unwrap(move(o));print(len(b));'), '2\n')

    def test_copy_payload_with_inline_aggregate(self):
        self.accepted('value struct P{let x:int;let y:int;}enum E{A(P,own *int);B;}' + main(
                      'own e:E=new E.A(new P(20,22),alloc<int>(2));'
                      'match(e){A(p,b){print(p.x+p.y,len(b));}B{}}'
                      'match(move(e)){A(p,b){print(p.x+p.y,len(b));}B{}}'), '42 2\n42 2\n')

    def test_recursive_owned_variants(self):
        self.accepted('enum List{End;Next(int,own List);}' + main(
                      'own l:List=new List.Next(42,new List.Next(7,new List.End()));'
                      'match(l){End{}Next(v,tail){print(v);match(tail){End{}Next(x,t){print(x);}}}}'), '42\n7\n')

    def test_loops_break_and_continue_cleanup(self):
        self.accepted(OPTION + main('let i:int=0;while(i<10){i+=1;'
                      'own o:O<*int>=new O<*int>.Some(alloc<int>(10));'
                      'match(move(o)){None{}Some(v){if(i<5){continue;}break;}}}print(i);'), '5\n')

    def test_borrowed_payload_can_return_from_borrowed_parameter(self):
        code = OPTION + 'safe fn get(borrow o:O<*int>):borrow(o) *int{'
        code += 'match(o){None{return get(o);}Some(v){return v;}}}'
        self.accepted(code + main('own o:O<*int>=new O<*int>.Some(alloc<int>(2));'
                      'borrow b:*int=get(o);print(len(b));'), '2\n')

    def test_reject_implicit_copies_and_reuse(self):
        for body, message in [
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));own p:O<*int>=o;', 'own exige'),
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));match(move(o)){None{}Some(v){}}free(o);', 'movido'),
            ('own b:*int=alloc<int>(1);own o:O<*int>=new O<*int>.Some(b);', 'own exige'),
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));match(o){None{}Some(v){free(v);}}', 'somente own'),
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));match(o){None{}Some(v){v[0]=1;}}', 'exclusivo'),
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));match(o){None{}Some(v){free(o);}}', 'borrow ativo'),
            ('own o:O<*int>=new O<*int>.Some(alloc<int>(1));borrow p:O<*int>=o;match(move(o)){None{}Some(v){}}', 'borrow ativo'),
        ]:
            with self.subTest(body=body):
                self.rejected(OPTION + main(body), message)

    def test_exhaustiveness_type_and_safe_boundary(self):
        self.rejected(OPTION + main('own o:O<*int>=new O<*int>.None();match(o){Some(v){}}'), 'não exaustivo')
        self.rejected('enum E{A(own int);}' + main(''), 'own aceita')
        self.rejected('enum E{A(*int);}' + main(''), 'valor Copy')
        self.rejected(OPTION + 'pure fn f():O<*int>{return new O<*int>.None();}' + main(''), 'pure exige')
        self.rejected(OPTION + main('match(new O<*int>.Some(alloc<int>(1))){None{}Some(v){}}'), 'match emprestado')


if __name__ == '__main__':
    suite = unittest.TestSuite(MoveEnums(name) for name in MoveEnums.__dict__ if name.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())

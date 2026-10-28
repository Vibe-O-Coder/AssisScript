"""Portable acceptance tests for AST-based user specialization (alpha.2)."""
import importlib
import json
import unittest

evolution = importlib.import_module('test-evolution')
main = evolution.main


class Generics(unittest.TestCase):
    setUp = evolution.Evolution.setUp
    source = evolution.Evolution.source
    invoke = evolution.Evolution.invoke
    accepted = evolution.Evolution.accepted
    rejected = evolution.Evolution.rejected

    def test_identity_scalar_specializations_and_pure(self):
        self.accepted('pure fn identidade<T>(v:T):T{return v;}' + main(
            'print(identidade::<int>(42),identidade::<byte>(byte(255)),identidade::<bool>(true));'),
            '42 255 true\n')
        self.accepted('fn identidade<T>(v:T):T{return v;}' + main(
            'val t:text=identidade::<text>("ação");print(t);'), 'ação\n')

    def test_structs_multiple_parameters_and_scoped_type_variables(self):
        self.accepted('struct Caixa<T>{let value:T;}struct Par<A,B>{let a:A;let b:B;}'
                      'fn primeiro<T,U>(a:T,b:U):T{return a;}' + main(
            'own a:Caixa<int>=new Caixa<int>(42);own b:Caixa<text>=new Caixa<text>("oi");'
            'own p:Par<byte,bool>=new Par<byte,bool>(byte(7),true);'
            'print(a.value,b.value,p.a,p.b,primeiro::<int,bool>(9,false));'), '42 oi 7 true 9\n')

    def test_transitive_queue_recursion_and_repeated_instances(self):
        self.accepted('pure fn par<T>(v:T,n:int):bool{if(n==0){return true;}return impar::<T>(v,n-1);}'
                      'pure fn impar<U>(v:U,n:int):bool{if(n==0){return false;}return par::<U>(v,n-1);}'
                      'pure fn fat<T>(v:T,n:int):int{if(n<2){return 1;}return n*fat::<T>(v,n-1);}' + main(
            'print(par::<byte>(byte(1),20),par::<byte>(byte(2),21),fat::<bool>(true,10));'),
            'true false 3628800\n')

    def test_nested_types_arrays_maps_and_contextual_literals(self):
        self.accepted('struct Caixa<T>{let value:T;}'
                      'fn create<T>(v:T):Caixa<T>{return new Caixa<T>(v);}'
                      'fn lista<T>(v:T):Array<T>{return [v,v];}' + main(
            'let c:Caixa<Array<int>>=create::<Array<int>>([3,4]);'
            'let a:Array<Caixa<Array<int>>>=lista::<Caixa<Array<int>>>(c);'
            'let m:HashMap<int,Caixa<Array<int>>>=new HashMap<int,Caixa<Array<int>>>();'
            'm.set(1,c);print(m.get(1).value[1],len(a));free(m);free(a);free(c.value);free(c);'), '4 2\n')

    def test_pointer_substitution_and_finite_recursive_struct(self):
        self.accepted('struct Elo<T>{let value:T;let next:Elo<T>;}'
                      'fn load<T>(p:*T):T{return *p;}' + main(
            'let x:int=17;print(load::<int>(&x));'
            'let a:Elo<int>=new Elo<int>(1,null);let b:Elo<int>=new Elo<int>(2,a);'
            'print(b.next.value);free(b);free(a);'), '17\n1\n')

    def test_nominal_identity_and_no_conflation_of_type_parameters(self):
        for code in [
            'struct Caixa<T>{let value:T;}' + main('let a:Caixa<int>=new Caixa<int>(1);let b:Caixa<byte>=a;'),
            'struct A<T>{let value:T;}struct B<T>{let value:T;}' + main('let a:A<int>=new B<int>(1);'),
            'fn escolher<T,U>(a:T,b:U):T{return b;}' + main('print(escolher::<int,bool>(1,true));'),
        ]:
            self.rejected(code, 'não é possível usar')

    def test_arity_explicit_arguments_and_invalid_declarations(self):
        for code, message in [
            ('fn f<T>(v:T):T{return v;}' + main('print(f(1));'), 'explícitos'),
            ('fn f<T>(v:T):T{return v;}' + main('print(f::<int,bool>(1));'), 'argumentos de tipo'),
            ('fn f(v:int):int{return v;}' + main('print(f::<int>(1));'), 'não genérica'),
            ('struct C<T>{let v:T;}' + main('let c:C=new C<int>(1);'), 'exige argumentos de tipo'),
            ('struct C<T>{let v:T;}' + main('let c:C<int,bool>=new C<int,bool>();'), 'argumentos de tipo'),
            ('struct C{let v:int;}' + main('let c:C<int>=new C<int>();'), 'não genérico'),
            ('fn f<T,T>(v:T):T{return v;}' + main(''), 'tipo declarado duas vezes'),
            ('fn f<T>(v:T):T{return v;}' + main('f::<void>(1);'), 'não pode ser void'),
            ('fn f<T>():int{return 0;}fn f():int{return 0;}' + main(''), 'duas vezes'),
            ('fn main<T>():int{return 0;}', 'não pode ser genérica'),
            ('class C{fn f<T>(v:T):T{return v;}}' + main(''), 'métodos genéricos'),
        ]:
            with self.subTest(code=code):
                self.rejected(code, message)

    def test_private_access_does_not_gain_callers_authority(self):
        self.rejected('class Segredo{private let value:int;fn ler():int{return espiar::<Segredo>(self);}}'
                      'fn espiar<T>(v:T):int{return v.value;}' + main(''), 'campo privado')
        self.rejected('struct Caixa<T>{private let value:T;}' + main('let c:Caixa<int>=new Caixa<int>(1);'), 'campo privado')
        self.rejected('struct Caixa<T>{private let value:T;}'
                      'fn espiar<T>(v:Caixa<T>):T{return v.value;}' + main(
            'let c:Caixa<int>=new Caixa<int>();print(espiar::<int>(c));'), 'campo privado')
        self.rejected('fn espiar<T>(v:Array<T>):int{return v._length;}' + main(
            'let a:Array<int>=[1];print(espiar::<int>(a));'), 'campo privado')

    def test_pure_templates_reject_effects_even_when_unused(self):
        for body in ['print(v);return v;', 'if(false){print(1);}return v;',
                     'let n:int=monotonic_ms();return v;', 'return comum::<T>(v);',
                     'let p:*T=alloc<T>(1);return v;', 'let s:text="a";return v;']:
            self.rejected('fn comum<T>(v:T):T{return v;}pure fn f<T>(v:T):T{' + body + '}' + main(''), 'pure')
        self.rejected('pure fn f<T>(v:T):T{return v;}' + main('print(f::<text>("x"));'), 'pure')
        self.rejected('pure fn f<T>(v:T):T{v=v;return v;}' + main('print(f::<int>(1));'), 'imutável')

    def test_ownership_is_checked_on_each_concrete_instance(self):
        self.accepted('struct Caixa<T>{let value:T;}'
                      'fn local<T>(v:T):int{own c:Caixa<T>=new Caixa<T>(v);return 1;}' + main(
            'print(local::<int>(42),local::<text>("oi"));'), '1 1\n')
        self.rejected('fn id<T>(v:T):T{return v;}' + main(
            'own a:Array<int>=[1];let b:Array<int>=id::<Array<int>>(a);'), 'não pode escapar')
        self.rejected('struct Caixa<T>{let value:T;}'
                      'fn local<T>(v:T):int{own c:Caixa<T>=new Caixa<T>(v);return 1;}' + main(
            'let a:Array<int>=[1];print(local::<Array<int>>(a));'), 'own struct exige campos')

    def test_expanding_function_and_struct_rejected_deterministically(self):
        self.rejected('fn crescer<T>():int{return crescer::<*T>();}' + main('print(crescer::<int>());'), 'limite de expansão')
        self.rejected('struct Crescer<T>{let campo:Crescer<Array<T>>;}' + main('let c:Crescer<int>=new Crescer<int>();'), 'limite de expansão')

    def test_cache_reuses_types_and_limits_distinct_specializations(self):
        function = 'fn marca<T>():int{return 1;}'
        self.accepted(function + main('marca::<int>();' * 258))
        declarations = ''.join(f'struct Tipo{i}{{let v:int;}}' for i in range(257))
        calls = ''.join(f'marca::<Tipo{i}>();' for i in range(257))
        self.rejected(declarations + function + main(calls), 'limite de 256 especializações')

    def test_modules_diagnostics_and_lazy_body_validation(self):
        library = self.source('struct Caixa<T>{let v:T;}\nfn falhar<T>(v:T):T{\nreturn v+true;\n}', 'lib.assis')
        file = self.source('import "lib.assis";\n' + main('print(falhar::<int>(1));'))
        result = self.invoke('check', file, '--diagnostics=json')
        diagnostic = json.loads(result.stderr)
        self.assertEqual((result.returncode, diagnostic['file'], diagnostic['line']), (1, str(library), 3))
        self.assertIn('instância de falhar', diagnostic['message'])
        self.assertIn(str(file), diagnostic['message'])
        result = self.invoke('check', library, '--library')
        self.assertEqual(result.returncode, 0, result.stderr)
        library.write_text('struct Caixa<T>{\nlet v:void;\n}', encoding='utf-8')
        file.write_text('import "lib.assis";\n' + main('let c:Caixa<int>=new Caixa<int>();'), encoding='utf-8')
        result = self.invoke('check', file, '--diagnostics=json')
        diagnostic = json.loads(result.stderr)
        self.assertEqual((result.returncode, diagnostic['file'], diagnostic['line']), (1, str(library), 2))
        self.assertIn('instância de Caixa', diagnostic['message'])
        self.assertIn(str(file), diagnostic['message'])
        library.write_text('struct Caixa<T>{let v:T;}fn id<T>(v:T):T{return v;}', encoding='utf-8')
        self.accepted('import "lib.assis";\n' + main(
            'own c:Caixa<int>=new Caixa<int>(id::<int>(42));print(c.v);'), '42\n')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS generics: {evolution.INVOCATIONS} invocações; {evolution.COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())

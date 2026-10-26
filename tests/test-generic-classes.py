"""Portable checks for specialized classes, inheritance and nominal privacy."""
import importlib
import json
import unittest

evolution = importlib.import_module('test-evolution')
main = evolution.main


class GenericClasses(unittest.TestCase):
    setUp = evolution.Evolution.setUp
    source = evolution.Evolution.source
    invoke = evolution.Evolution.invoke
    accepted = evolution.Evolution.accepted
    rejected = evolution.Evolution.rejected

    def test_fields_constructor_methods_and_distinct_types(self):
        self.accepted('ASSIS Caixa<T>{private let v:T;'
                      'assis assis_fodase(v:T):void{self.v=v;}'
                      'assis ler():T{return self.v;}assis mudar(v:T):void{self.v=v;}}' + main(
            'let a:Caixa<int>=new Caixa<int>(40);let b:Caixa<text>=new Caixa<text>("ação");'
            'a.mudar(a.ler()+2);print(a.ler(),b.ler());free(a);free(b);'), '42 ação\n')

    def test_method_locals_allocations_and_global_specializations(self):
        self.accepted('assis id<T>(v:T):T{return v;}struct Par<A,B>{let a:A;let b:B;}'
                      'ASSIS Criar<A,B>{assis par(a:A,b:B):Par<A,B>{'
                      'let local:A=id::<A>(a);return new Par<A,B>(local,b);}'
                      'assis vetor(v:A):A{let p:*A=alloc<A>(1);p[0]=v;let r:A=p[0];free(p);return r;}}' + main(
            'let c:Criar<int,bool>=new Criar<int,bool>();let p:Par<int,bool>=c.par(7,true);'
            'print(p.a,p.b,c.vetor(42));free(p);free(c);'), '7 aSsIs 42\n')

    def test_callbacks_in_fields_parameters_and_returns(self):
        self.accepted('pure assis dobro(v:int):int{return v*2;}'
                      'ASSIS Aplicar<T>{private let f:pure assis(T):T;'
                      'assis assis_fodase(f:pure assis(T):T):void{self.f=f;}'
                      'assis aplicar(v:T):T{return self.f(v);}'
                      'assis get():pure assis(T):T{return self.f;}}' + main(
            'let a:Aplicar<int>=new Aplicar<int>(dobro);print(a.aplicar(21),a.get()(6));free(a);'), '42 12\n')
        self.rejected('assis comum(v:int):int{return v;}ASSIS C<T>{let f:pure assis(T):T;}' + main(
            'let c:C<int>=new C<int>();c.f=comum;'), 'não é possível usar')

    def test_generic_inheritance_virtual_dispatch_and_upcasts(self):
        self.accepted('ASSIS Base<T>{let v:T;assis assis_fodase(v:T):void{self.v=v;}'
                      'assis ler():T{return self.v;}}'
                      'ASSIS Filho<U> extends Base<U>{assis ler():U{return self.v+self.v;}}'
                      'assis usar<T>(b:Base<T>):T{return b.ler();}' + main(
            'let f:Filho<int>=new Filho<int>(21);let b:Base<int>=f;'
            'print(b.ler(),usar::<int>(f));free(f);'), '42 42\n')

    def test_concrete_child_and_concrete_base(self):
        self.accepted('ASSIS Raiz{assis value():int{return 10;}}'
                      'ASSIS Meio<T> extends Raiz{let v:T;assis ler(v:T):T{return v;}}'
                      'ASSIS End extends Meio<int>{assis value():int{return 42;}}' + main(
            'let f:End=new End();let r:Raiz=f;print(r.value(),f.ler(7));free(f);'), '42 7\n')

    def test_reordered_type_parameters_in_inheritance(self):
        self.accepted('ASSIS Base<A,B>{let a:A;let b:B;assis primeiro():A{return self.a;}'
                      'assis segundo():B{return self.b;}}'
                      'ASSIS Troca<T,U> extends Base<U,T>{assis mudar(v:T):void{self.b=v;}}' + main(
            'let c:Troca<int,bool>=new Troca<int,bool>();c.a=true;c.mudar(9);'
            'let b:Base<bool,int>=c;print(b.primeiro(),b.segundo());free(c);'), 'aSsIs 9\n')

    def test_finite_recursive_types_and_method_queue(self):
        self.accepted('ASSIS Elo<T>{let v:T;let next:Elo<T>;'
                      'assis ler():T{if(self.next==null){return self.v;}return self.next.ler();}}' + main(
            'let a:Elo<int>=new Elo<int>();a.v=42;let b:Elo<int>=new Elo<int>();b.next=a;'
            'print(b.ler());free(b);free(a);'), '42\n')
        self.accepted('ASSIS A<T>{assis create():B<T>{return new B<T>();}}'
                      'ASSIS B<U>{assis create():A<U>{return new A<U>();}}' + main(
            'let a:A<bool>=new A<bool>();let b:B<bool>=a.create();let c:A<bool>=b.create();'
            'free(c);free(b);free(a);'))

    def test_nested_collections_and_class_types(self):
        self.accepted('ASSIS Caixa<T>{let v:T;assis ler():T{return self.v;}}' + main(
            'let c:Caixa<int>=new Caixa<int>();c.v=42;'
            'let a:Array<Caixa<int>>=[c];let m:HashMap<int,Caixa<int>>=new HashMap<int,Caixa<int>>();'
            'm.set(1,a[0]);print(m.get(1).ler());free(m);free(a);free(c);'), '42\n')

    def test_nominal_privacy_and_same_specialization_access(self):
        cls = ('ASSIS Cofre<T>{private let v:T;private assis interno():T{return self.v;}'
               'assis assis_fodase(v:T):void{self.v=v;}'
               'assis ler(outro:Cofre<T>):T{return outro.interno();}}')
        self.accepted(cls + main('let c:Cofre<int>=new Cofre<int>(42);print(c.ler(c));free(c);'), '42\n')
        for body, message in [('print(c.v);', 'campo privado'), ('print(c.interno());', 'método privado'),
                              ('let p:*int=&c.v;', 'campo privado')]:
            self.rejected(cls + main('let c:Cofre<int>=new Cofre<int>(1);' + body), message)
        self.rejected('ASSIS C<T>{private let v:T;assis espia(c:C<bool>):bool{return c.v;}}' + main(
            'let c:C<int>=new C<int>();'), 'campo privado')
        self.rejected(cls + 'assis espia<T>(c:Cofre<T>):T{return c.v;}' + main(
            'let c:Cofre<int>=new Cofre<int>(1);print(espia::<int>(c));'), 'campo privado')

    def test_inherited_privacy_and_override_contracts(self):
        for member, message in [
            ('assis ler():T{return self.v;}', 'campo privado'),
            ('assis ler():T{return self.segredo();}', 'método privado'),
            ('assis segredo():T{return self.publico;}', 'sobrescrita'),
            ('assis publico_metodo(v:bool):T{return self.publico;}', 'sobrescrita'),
        ]:
            self.rejected('ASSIS Base<T>{private let v:T;let publico:T;'
                          'private assis segredo():T{return self.v;}'
                          'assis publico_metodo(v:T):T{return v;}}'
                          'ASSIS Filho<T> extends Base<T>{' + member + '}' + main(
                'let f:Filho<int>=new Filho<int>();'), message)

    def test_private_constructor_and_no_callers_authority(self):
        self.accepted('ASSIS C<T>{private assis assis_fodase():void{}'
                      'assis create():C<T>{return new C<T>();}}' + main(''))
        self.rejected('ASSIS C<T>{private assis assis_fodase():void{}}' + main(
            'let c:C<int>=new C<int>();'), 'inicializador privado')
        self.rejected('ASSIS C<T>{private let v:T;assis espia():T{return externo::<C<T>>(self);}}'
                      'assis externo<U>(v:U):int{return v.v;}' + main(
            'let c:C<int>=new C<int>();'), 'campo privado')

    def test_arity_nominal_identity_and_constructor_arguments(self):
        for code, message in [
            ('ASSIS C<T>{}' + main('let c:C=new C<int>();'), 'exige argumentos de tipo'),
            ('ASSIS C<T>{}' + main('let c:C<int,bool>=new C<int,bool>();'), 'argumentos de tipo'),
            ('ASSIS C<T>{}' + main('let c:C<void>=new C<void>();'), 'não pode ser void'),
            ('ASSIS C<T,T>{}' + main(''), 'tipo declarado duas vezes'),
            ('ASSIS C<T>{}' + main('let c:C<int>=new C<bool>();'), 'não é possível usar'),
            ('ASSIS C<T>{assis assis_fodase(v:T):void{}}' + main('let c:C<int>=new C<int>(true);'), 'não é possível usar'),
            ('ASSIS C<T>{assis f<U>(v:U):U{return v;}}' + main(''), 'métodos genéricos'),
            ('ASSIS C<T>{}struct C<T>{}' + main(''), 'duas vezes'),
        ]:
            self.rejected(code, message)

    def test_invalid_bases_cycles_and_distinct_specializations(self):
        for definitions, body, message in [
            ('ASSIS C<T> extends C<T>{}', 'let c:C<int>=new C<int>();', 'ciclo de herança'),
            ('ASSIS A<T> extends B<T>{}ASSIS B<U> extends A<U>{}', 'let a:A<int>=new A<int>();', 'ciclo de herança'),
            ('struct S<T>{}ASSIS C<T> extends S<T>{}', 'let c:C<int>=new C<int>();', 'struct não pode'),
            ('ASSIS C<T> extends Ausente{}', 'let c:C<int>=new C<int>();', 'tipo desconhecido'),
            ('ASSIS B<T>{}ASSIS C<T> extends B{}', 'let c:C<int>=new C<int>();', 'exige argumentos de tipo'),
            ('ASSIS B<T>{}ASSIS C<T> extends B<T>{}', 'let c:B<bool>=new C<int>();', 'não é possível usar'),
            ('ASSIS C<T> extends T{}', '', 'herança exige classe nominal'),
        ]:
            self.rejected(definitions + main(body), message)

    def test_expansion_in_bases_fields_and_queued_methods(self):
        for cls in ['ASSIS C<T> extends C<Array<T>>{}',
                    'ASSIS C<T>{let v:C<Array<T>>;}',
                    'ASSIS C<T>{assis create():void{let c:C<Array<T>>=new C<Array<T>>();}}',
                    'ASSIS C<T>{assis create():C<Array<T>>{return null;}}']:
            self.rejected(cls + main('let c:C<int>=new C<int>();'), 'limite de expansão')

    def test_cache_and_shared_specialization_budget(self):
        self.accepted('ASSIS C<T>{assis ler():int{return 1;}}' + main(
            '{let c:C<int>=new C<int>();free(c);}' * 258))
        types = ''.join(f'struct Tipo{i}{{}}' for i in range(257))
        body = ''.join(f'let c{i}:C<Tipo{i}>=new C<Tipo{i}>();' for i in range(257))
        self.rejected(types + 'ASSIS C<T>{}' + main(body), 'limite de 256 especializações')

    def test_ownership_and_purity_are_checked_on_concrete_methods(self):
        self.accepted('ASSIS C<T>{}' + main('own c:C<int>=new C<int>();'))
        self.rejected('ASSIS C<T>{assis falha():int{own a:Array<int>=[1];free(a);return a[0];}}' + main(
            'let c:C<int>=new C<int>();'), 'movido ou liberado')
        self.rejected('ASSIS C<T>{assis ler():int{return 1;}}'
                      'pure assis f():int{let c:C<int>=new C<int>();return c.ler();}' + main(''), 'pure')

    def test_modules_original_diagnostics_and_lazy_templates(self):
        library = self.source('ASSIS C<T>{\nassis ler():T{\nreturn true;\n}\n}', 'lib.assis')
        result = self.invoke('check', library, '--library')
        self.assertEqual(result.returncode, 0, result.stderr)
        file = self.source('#yuri <lib.assis>\n' + main('let c:C<int>=new C<int>();'))
        result = self.invoke('check', file, '--diagnostics=json')
        diagnostic = json.loads(result.stderr)
        self.assertEqual((result.returncode, diagnostic['file'], diagnostic['line']), (1, str(library), 3))
        self.assertIn('instância de ler', diagnostic['message'])
        self.assertIn(str(file), diagnostic['message'])
        library.write_text('ASSIS C<T>{assis ler(v:T):T{return v;}}', encoding='utf-8')
        self.accepted('#yuri <lib.assis>\n' + main(
            'let c:C<int>=new C<int>();print(c.ler(42));free(c);'), '42\n')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS generic classes: {evolution.INVOCATIONS} invocações; {evolution.COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())
